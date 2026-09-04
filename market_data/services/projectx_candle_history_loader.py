from datetime import date, datetime, timedelta, timezone

from market_data.providers.futures_provider import FuturesProvider
from market_data.repository.candle_repository import CandleRepository
from market_data.repository.contract_repository import ContractRepository


class ProjectxCandlesHistoryLoader:

    def __init__(
        self,
        provider: FuturesProvider,
        contract_repo: ContractRepository,
        candle_repo: CandleRepository,
    ):
        self.provider = provider
        self.contract_repo = contract_repo
        self.candle_repo = candle_repo

    def sync_candles(
        self,
        instrument: str,
    ) -> int:

        # ----------------------------------------------------------
        # 1. Determine current active contract
        # ----------------------------------------------------------

        current_contract = self.contract_repo.get_front_month(
            instrument=instrument,
            as_of_date=date.today(),
        )

        if current_contract is None:
            raise RuntimeError(
                f"No active contract found for {instrument}"
            )

        print(
            f"{instrument} active contract: "
            f"{current_contract.contract}"
        )

        # ----------------------------------------------------------
        # 2. Resolve ProjectX contract mapping
        # ----------------------------------------------------------

        projectx_contract_id = (
            self.provider.resolve_contract(
                current_contract.contract
            )
        )

        print(
            f"ProjectX mapping: "
            f"{current_contract.contract} → "
            f"{projectx_contract_id}"
        )

        # ----------------------------------------------------------
        # 3. Get latest candle in our DB
        # ----------------------------------------------------------

        latest = (
            self.candle_repo.latest_timestamp_by_contract(
                contract=current_contract.contract,
                timeframe=1,
            )
        )

        # ----------------------------------------------------------
        # 4. Determine retrieval window
        # ----------------------------------------------------------

        if latest is None:
            raise RuntimeError(
                f"No existing 1m candles found for "
                f"{current_contract.contract}"
            )

        start = latest + timedelta(minutes=1)
        end = datetime.now(timezone.utc)

        print(
            f"Retrieving {instrument} {current_contract.contract}: "
            f"{start} → {end}"
        )

        # ----------------------------------------------------------
        # 5. Nothing to retrieve
        # ----------------------------------------------------------

        if start >= end:
            print("Database is already up to date")
            return 0

        # ----------------------------------------------------------
        # 6. Retrieve missing candles from ProjectX
        # ----------------------------------------------------------

        candles = self.provider.get_history(
            instrument=instrument,
            contract=current_contract.contract,
            timeframe=1,
            start=start,
            end=end,
        )

        # ----------------------------------------------------------
        # 7. Safety filter
        # ----------------------------------------------------------

        candles = [
            candle
            for candle in candles
            if candle.timestamp > latest
            and candle.timestamp <= end
        ]

        # ----------------------------------------------------------
        # 8. Save
        # ----------------------------------------------------------

        if not candles:
            print("No new candles received")
            return 0

        self.candle_repo.save(candles)

        print(
            f"Saved {len(candles)} new "
            f"{instrument} 1m candles"
        )

        return len(candles)
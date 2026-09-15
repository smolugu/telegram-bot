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
    
    def reconcile_recent_candles_new(
        self,
        instrument: str,
        lookback_minutes: int = 60,
    ) -> int:
        current_contract = self.contract_repo.get_front_month(
            instrument,
            date.today(),
        )

        if current_contract is None:
            raise RuntimeError(
                f"No front-month contract found for {instrument}"
            )

        contract = current_contract.contract

        now = datetime.now(timezone.utc)

        # Current minute is still forming.
        # Reconcile only through the previous completed minute.
        end = now.replace(
            second=0,
            microsecond=0,
        )

        start = end - timedelta(minutes=lookback_minutes)

        if start >= end:
            return 0

        candles = self.provider.get_history(
            instrument=instrument,
            contract=contract,
            timeframe=1,
            start=start,
            end=end,
        )

        if not candles:
            print(
                f"No reconciliation candles received "
                f"for {instrument}"
            )
            return 0

        # Never save the currently forming minute.
        candles = [
            candle
            for candle in candles
            if candle.timestamp < end
        ]

        if not candles:
            return 0

        self.candle_repo.save(candles)

        print(
            f"Reconciled {len(candles)} candles "
            f"for {instrument} {contract} "
            f"from {start} to {end}"
        )

        return len(candles)

    def reconcile_recent_candles(
        self,
        instrument: str,
        lookback_minutes: int = 60,
    ) -> int:

        current_contract = self.contract_repo.get_front_month(
            instrument,
            date.today(),
        )

        if current_contract is None:
            raise RuntimeError(
                f"No front month contract found for {instrument}"
            )

        contract = current_contract.contract

        latest = self.candle_repo.latest_timestamp_by_contract(
            contract,
            timeframe=1,
        )

        if latest is None:
            raise RuntimeError(
                f"No existing 1m candles found for {contract}"
            )

        end = datetime.now(timezone.utc)

        start = end - timedelta(minutes=lookback_minutes)

        # Don't request future/current partial minute.
        end = end.replace(
            second=0,
            microsecond=0,
        )

        if start >= end:
            return 0

        candles = self.provider.get_history(
            instrument=instrument,
            contract=contract,
            timeframe=1,
            start=start,
            end=end,
        )

        if not candles:
            print(
                f"No reconciliation candles returned "
                f"for {instrument} {contract}"
            )
            return 0

        # Only save completed candles.
        current_minute = datetime.now(timezone.utc).replace(
            second=0,
            microsecond=0,
        )

        candles = [
            candle
            for candle in candles
            if candle.timestamp < current_minute
        ]

        if not candles:
            return 0

        self.candle_repo.save(candles)

        print(
            f"Reconciled {len(candles)} candles "
            f"for {instrument} {contract}"
        )

        return len(candles)
    
    def sync_candle_range(
        self,
        instrument: str,
        contract: str,
        start_utc: datetime,
        end_utc: datetime,
    ) -> int:

        if start_utc >= end_utc:
            return 0

        print(
            f"Syncing 1m range: "
            f"{instrument} {contract} "
            f"{start_utc} → {end_utc}"
        )

        candles = self.provider.get_history(
            instrument=instrument,
            contract=contract,
            timeframe=1,
            start=start_utc,
            end=end_utc,
        )

        if not candles:
            print(
                f"No 1m candles returned for "
                f"{instrument} {contract}"
            )
            return 0

        # Only keep candles belonging to the requested range.
        candles = [
            candle
            for candle in candles
            if start_utc <= candle.timestamp < end_utc
        ]

        if not candles:
            return 0

        self.candle_repo.save(candles)

        print(
            f"Synced {len(candles)} 1m candles for "
            f"{instrument} {contract}"
        )

        return len(candles)

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
        # latest = datetime(
        #             2026, 9, 10, 7, 0,
        #             tzinfo=timezone.utc,
        #         ) 
        # start = datetime(
        #             2026, 9, 10, 7, 0,
        #             tzinfo=timezone.utc,
        #         )
        # end = datetime(
        #             2026, 9, 10, 8, 0,
        #             tzinfo=timezone.utc,
        #         )
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
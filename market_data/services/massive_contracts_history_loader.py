# Responsibilities
# HistoryLoader should answer four questions:

# Which contract should I download?
# Where does my local history end?
# Which candles are missing?
# Save the missing candles.
# Flow of History Loader
# ===============================
# Determine front contract
#         │
#         ▼
# Repository.latest_timestamp()
#         │
#         ▼
# Download missing candles
#         │
#         ▼
# Repository.save()

# market_data/services/history_loader.py

from datetime import datetime, time, timedelta, timezone, date
import time as time_module
import time
from datetime import datetime, time as dt_time, timezone, timedelta

from config.settings import LIVE_HISTORY_DAYS, SUPPORTED_TIMEFRAMES
from data.models.contract import Contract
from market_data.htf.htf_candle_builder import HTFCandleBuilder
from market_data.providers.massive_futures_provider import FuturesProvider
from market_data.repository.candle_repository import CandleRepository
from market_data.repository.contract_repository import ContractRepository


class MassiveContractsHistoryLoader:

    def __init__(
        self,
        provider: FuturesProvider,
        contract_repo: ContractRepository,
        candle_repo: CandleRepository,
    ):
        self.provider = provider
        self.contract_repo = contract_repo
        self.candle_repo = candle_repo

    def sync_contracts(
        self,
        instrument: str,
    ) -> int:

        # ----------------------------------------------------------
        # 1. Get current contracts from Massive
        # ----------------------------------------------------------

        current_contracts = self.provider.get_contracts(
            instrument=instrument,
            snapshot_date=date.today(),
        )

        print(
            f"Retrieved {len(current_contracts)} current "
            f"{instrument} contracts from Massive"
        )

        # ----------------------------------------------------------
        # 2. Get existing contracts from our database
        # ----------------------------------------------------------

        existing_contracts = [
            c
            for c in self.contract_repo.get_all(instrument)
            if c.contract_type == "single"
            and "-" not in c.contract
        ]

        # ----------------------------------------------------------
        # 3. Merge current Massive data with existing contracts
        # ----------------------------------------------------------

        contracts_by_ticker = {
            c.contract: c
            for c in existing_contracts
        }

        for contract in current_contracts:

            existing = contracts_by_ticker.get(
                contract.contract
            )

            if existing is not None:
                # Preserve the existing rollover date for now.
                contract = Contract(
                    contract=contract.contract,
                    instrument=contract.instrument,
                    contract_type=contract.contract_type,
                    first_trade_date=contract.first_trade_date,
                    rollover_date=existing.rollover_date,
                    last_trade_date=contract.last_trade_date,
                    settlement_date=contract.settlement_date,
                    days_to_maturity=contract.days_to_maturity,
                    active=contract.active,
                )

            contracts_by_ticker[contract.contract] = contract

        contracts = list(contracts_by_ticker.values())

        # ----------------------------------------------------------
        # 4. Sort complete contract chain by expiry
        # ----------------------------------------------------------

        contracts.sort(
            key=lambda c: (
                c.last_trade_date
                if c.last_trade_date is not None
                else date.max
            )
        )

        # ----------------------------------------------------------
        # 5. Recalculate rollover dates
        # ----------------------------------------------------------

        updated_contracts = []

        previous = None

        for contract in contracts:

            rollover_date = (
                previous.last_trade_date
                if previous is not None
                else None
            )

            updated_contracts.append(
                Contract(
                    contract=contract.contract,
                    instrument=contract.instrument,
                    contract_type=contract.contract_type,
                    first_trade_date=contract.first_trade_date,
                    rollover_date=rollover_date,
                    last_trade_date=contract.last_trade_date,
                    settlement_date=contract.settlement_date,
                    days_to_maturity=contract.days_to_maturity,
                    active=contract.active,
                )
            )

            previous = contract

        # ----------------------------------------------------------
        # 6. Save complete contract chain
        # ----------------------------------------------------------

        self.contract_repo.save(updated_contracts)

        print(
            f"Saved {len(updated_contracts)} {instrument} contracts"
        )

        return len(updated_contracts)
    

    def download_historical_candles(
        self,
        instrument: str,
        history_start: date,
        pause_seconds: int = 15,
    ) -> None:

        contracts = self.contract_repo.get_all(
            instrument
        )

        today = datetime.now(timezone.utc).date()

        # --------------------------------------------------------------
        # Only contracts relevant to the requested history
        # --------------------------------------------------------------

        contracts = [
            c
            for c in contracts
            if c.last_trade_date is not None
            and c.last_trade_date >= history_start
            and c.last_trade_date <= today
        ]

        contracts.sort(
            key=lambda c: c.last_trade_date
        )

        print(
            f"\n{instrument}: "
            f"{len(contracts)} contracts"
        )

        for index, contract in enumerate(contracts):

            print(
                f"\n{'=' * 60}"
            )

            print(
                f"[{index + 1}/{len(contracts)}] "
                f"{contract.contract}"
            )

            # ----------------------------------------------------------
            # Start = rollover date
            # ----------------------------------------------------------

            if contract.rollover_date is not None:

                start_date = max(
                    contract.rollover_date,
                    history_start,
                )

            else:

                start_date = max(
                    contract.first_trade_date,
                    history_start,
                )

            end_date = contract.last_trade_date

            start = datetime.combine(
                start_date,
                dt_time.min,
                tzinfo=timezone.utc,
            )

            end = datetime.combine(
                end_date,
                dt_time.max,
                tzinfo=timezone.utc,
            )

            print(
                f"Downloading:"
            )
            print(
                f"  {start} → {end}"
            )

            # ----------------------------------------------------------
            # Download 1m candles
            # ----------------------------------------------------------

            candles = self.provider.get_history(
                instrument=instrument,
                contract=contract.contract,
                timeframe=1,
                start=start,
                end=end,
            )

            print(
                f"Received {len(candles)} candles"
            )
            # ----------------------------------------------------------
            # Deduplicate
            # ----------------------------------------------------------

            unique_candles = {}

            for candle in candles:

                key = (
                    candle.contract,
                    candle.timeframe,
                    candle.timestamp,
                )

                unique_candles[key] = candle

            candles = list(
                unique_candles.values()
            )

            candles.sort(
                key=lambda c: c.timestamp
            )

            print(
                f"Unique candles: {len(candles)}"
            )

            # ----------------------------------------------------------
            # Save
            # ----------------------------------------------------------

            if candles:

                self.candle_repo.save(candles)

                print(
                    f"Saved {len(candles)} candles"
                )

            else:

                print(
                    f"WARNING: No candles returned "
                    f"for {contract.contract}"
                )

            # ----------------------------------------------------------
            # Wait before next contract
            # ----------------------------------------------------------

            if index < len(contracts) - 1:

                print(
                    f"Waiting {pause_seconds}s "
                    f"before next contract..."
                )

                time.sleep(pause_seconds)

        print(
            f"\nFinished historical download for {instrument}"
        )

    
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


class HistoryLoader:

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

        contracts = self.provider.get_contracts(
            instrument=instrument,
            snapshot_date=date.today(),
        )
        print(f"Retrieved {len(contracts)} contracts")

        for c in contracts[:5]:
            print(c)

        self.contract_repo.save(contracts)

        return len(contracts)
    
    
    # def download_contract_history(
    #     self,
    #     instrument: str,
    #     contract: Contract,
    #     history_start: date | None = None,
    # ) -> None:

    #     # --------------------------------------------------------------
    #     # Determine candle start
    #     # --------------------------------------------------------------

    #     if contract.rollover_date is not None:

    #         start = datetime.combine(
    #             contract.rollover_date,
    #             dt_time.min,
    #             tzinfo=timezone.utc,
    #         )

    #     else:

    #         # First contract in the historical chain
    #         start_date = contract.first_trade_date

    #         if history_start is not None:
    #             start_date = max(
    #                 start_date,
    #                 history_start,
    #             )

    #         start = datetime.combine(
    #             start_date,
    #             dt_time.min,
    #             tzinfo=timezone.utc,
    #         )

    #     # --------------------------------------------------------------
    #     # Candle end
    #     # --------------------------------------------------------------

    #     end = datetime.combine(
    #         contract.last_trade_date,
    #         dt_time.max,
    #         tzinfo=timezone.utc,
    #     )

    #     print(
    #         f"\nDownloading {contract.contract}"
    #     )
    #     print(
    #         f"  {start} → {end}"
    #     )

    #     candles = self.provider.get_history(
    #         instrument=instrument,
    #         contract=contract.contract,
    #         timeframe=1,
    #         start=start,
    #         end=end,
    #     )

    #     print(
    #         f"  Received {len(candles)} candles"
    #     )

    #     if not candles:
    #         print(
    #             f"  WARNING: No candles for "
    #             f"{contract.contract}"
    #         )
    #         return

    #     self.candle_repo.save(candles)

    #     print(
    #         f"  Saved {len(candles)} candles"
    #     )

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
    def sync_history(
        self,
        instrument: str,
        timeframe: int = 1,
    ) -> None:

        print(f"\nSynchronizing {instrument} ({timeframe}m)")

        # Current front-month contract
        current_contract = self.contract_repo.get_front_month(
            instrument,
        )

        if current_contract is None:
            raise Exception(f"No active contract found for {instrument}")

        print(f"Current contract: {current_contract.contract}")
        
        # Latest candle stored for this instrument
        latest_candle = self.candle_repo.get_latest_by_instrument(
            instrument=instrument,
            timeframe=timeframe,
        )

        now = datetime.now(timezone.utc)

        # ------------------------------------------------------------------
        # First synchronization
        # ------------------------------------------------------------------
        if latest_candle is None:

            print("Initial history download")

            start = now - timedelta(days=60)

            candles = self.provider.get_history(
                instrument=instrument,
                contract=current_contract.contract,
                timeframe=timeframe,
                start=start,
                end=now,
            )

            self.candle_repo.save(candles)

            print(f"Saved {len(candles)} candles")
            # save candles for all timeframes
            self.sync_all_timeframes(
                instrument,
                current_contract.contract,
            )

            return

        # ------------------------------------------------------------------
        # Contract rollover
        # ------------------------------------------------------------------
        if latest_candle.contract != current_contract.contract:

            print(
                f"Contract rollover detected: "
                f"{latest_candle.contract} -> {current_contract.contract}"
            )

            #
            # Finish downloading the previous contract
            #
            previous_contract = self.contract_repo.get(
                latest_candle.contract,
            )

            previous_start = (
                latest_candle.timestamp +
                timedelta(minutes=timeframe)
            )

            previous_end = datetime.combine(
                previous_contract.last_trade_date,
                time.max,
                tzinfo=timezone.utc,
            )

            remaining = self.provider.get_history(
                instrument=instrument,
                contract=previous_contract.contract,
                timeframe=timeframe,
                start=previous_start,
                end=previous_end,
            )

            self.candle_repo.save(remaining)

            print(
                f"Completed {previous_contract.contract}: "
                f"{len(remaining)} candles"
            )
            # update htf for previous contract
            self.sync_all_timeframes(
                instrument,
                previous_contract.contract,
            )
            # get candles for new contract from start of new contract or from 
            retention_start = now - timedelta(
                days=LIVE_HISTORY_DAYS
            )
    
            contract_start = datetime.combine(
                current_contract.first_trade_date,
                time.min,
                tzinfo=timezone.utc,
            )
    
            current_start = max(
                contract_start,
                retention_start,
            )

        else:

            #
            # Normal incremental synchronization
            #
            current_start = (
                latest_candle.timestamp +
                timedelta(minutes=timeframe)
            )

        # ------------------------------------------------------------------
        # Synchronize current contract
        # ------------------------------------------------------------------
        candles = self.provider.get_history(
            instrument=instrument,
            contract=current_contract.contract,
            timeframe=timeframe,
            start=current_start,
            end=now,
        )

        self.candle_repo.save(candles)

        print(
            f"{current_contract.contract}: "
            f"{len(candles)} new candles"
        )
        # update htf for current contract
        self.sync_all_timeframes(
            instrument,
            current_contract.contract,
        )
        
    def rebuild_timeframes(
        self,
        instrument: str,
        contract: str,
    ) -> None:

        print(
            f"\nRebuilding HTF candles "
            f"for {instrument} / {contract}"
        )

        # --------------------------------------------------------------
        # Get all 1-minute candles for this contract
        # --------------------------------------------------------------
        candles_1m = self.candle_repo.get_history(
            contract=contract,
            timeframe=1,
        )

        if not candles_1m:
            print(
                f"No 1m candles found for {contract}"
            )
            return

        print(
            f"Found {len(candles_1m)} 1m candles"
        )

        builder = HTFCandleBuilder()

        # --------------------------------------------------------------
        # Build each HTF
        # --------------------------------------------------------------
        timeframes = [3, 30, 60, 240, 420]

        for timeframe in timeframes:

            print(
                f"\nBuilding {timeframe}m candles..."
            )

            candles_htf = builder.build(
                candles=candles_1m,
                timeframe=timeframe,
            )

            print(
                f"Built {len(candles_htf)} "
                f"{timeframe}m candles"
            )

            if candles_htf:
                self.candle_repo.save(candles_htf)

                print(
                    f"Saved {len(candles_htf)} "
                    f"{timeframe}m candles"
                )

        print(
            f"\nFinished rebuilding "
            f"{contract}"
        )
    def sync_timeframe(
        self,
        instrument: str,
        contract: str,
        timeframe: int,
    ) -> None:
        
        print("synching {} timeframe: {} for contract: {}".format(instrument, timeframe, contract))
        latest = self.candle_repo.latest_timestamp(
            contract=contract,
            timeframe=timeframe,
        )

        if latest is None:
            candles_1m = self.candle_repo.get_history(
                contract=contract,
                timeframe=1,
            )
        else:
            candles_1m = self.candle_repo.get_history(
                contract=contract,
                timeframe=1,
                start=latest - timedelta(minutes=timeframe * 2),
            )

        builder = HTFCandleBuilder()

        candles_htf = builder.build(
            candles=candles_1m,
            timeframe=timeframe,
        )

        self.candle_repo.save(candles_htf)

        print(
            f"{instrument} - {contract} - {timeframe}m synchronized "
            f"({len(candles_htf)} candles)"
        )

    def sync_all_timeframes(
        self,
        instrument: str,
        contract: str,
    ):
        for tf in SUPPORTED_TIMEFRAMES:
            self.sync_timeframe(
                instrument=instrument,
                contract=contract,
                timeframe=tf,
            )
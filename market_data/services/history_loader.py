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

from config.settings import LIVE_HISTORY_DAYS, SUPPORTED_TIMEFRAMES
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
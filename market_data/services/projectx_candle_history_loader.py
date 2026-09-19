from datetime import date, datetime, timedelta, timezone, time as dt_time

import time

from data.models.candle import NY_TZ
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
    
    def sync_30m_range(
        self,
        instrument: str,
        contract: str,
        start_utc: datetime,
        end_utc: datetime,
    ) -> int:

        if start_utc >= end_utc:
            return 0

        print(
            f"Syncing 30m range: "
            f"{instrument} {contract} "
            f"{start_utc} → {end_utc}"
        )

        candles = self.provider.get_history(
            instrument=instrument,
            contract=contract,
            timeframe=30,
            start=start_utc,
            end=end_utc,
        )

        if not candles:
            print(
                f"No 30m candles returned for "
                f"{instrument} {contract}"
            )
            return 0

        # ProjectX uses an exclusive end.
        # Keep only candles inside [start_utc, end_utc).
        candles = [
            candle
            for candle in candles
            if start_utc <= candle.timestamp < end_utc
        ]

        if not candles:
            return 0

        self.candle_repo.save(candles)

        print(
            f"Synced {len(candles)} 30m candles for "
            f"{instrument} {contract}"
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
        print("===========")
        for candle in candles:
            print(candle)
        print("===========")

        if not candles:
            return 0

        self.candle_repo.save(candles)

        print(
            f"Synced {len(candles)} 1m candles for "
            f"{instrument} {contract}"
        )

        return len(candles)


    def _sync_contract_range(
        self,
        instrument: str,
        contract: str,
        start: datetime,
        end: datetime,
    ) -> int:

        if start >= end:
            return 0

        print(
            f"Retrieving {instrument} {contract}: "
            f"{start} → {end}"
        )

        candles = self.provider.get_history(
            instrument=instrument,
            contract=contract,
            timeframe=1,
            start=start,
            end=end,
        )

        # Safety filter
        candles = [
            candle
            for candle in candles
            if candle.timestamp >= start
            and candle.timestamp <= end
        ]
        
        if not candles:
            print(
                f"No new candles received for "
                f"{instrument} {contract}"
            )
            return 0

        self.candle_repo.save(candles)

        print(
            f"Saved {len(candles)} new "
            f"{instrument} {contract} 1m candles"
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
        # 3. Get latest candle for current contract
        # ----------------------------------------------------------

        latest_current = (
            self.candle_repo.latest_timestamp_by_contract(
                contract=current_contract.contract,
                timeframe=1,
            )
        )

        # ----------------------------------------------------------
        # 4. Get latest candle for instrument
        #    regardless of contract
        # ----------------------------------------------------------

        latest_instrument = (
            self.candle_repo.latest_candle_by_instrument(
                instrument=instrument,
                timeframe=1,
            )
        )

        end = datetime.now(timezone.utc)

        total_synced = 0

        # ----------------------------------------------------------
        # 5. Current contract already exists in DB
        # ----------------------------------------------------------

        if latest_current is not None:

            start = latest_current + timedelta(minutes=1)

            print(
                f"{instrument} {current_contract.contract} "
                f"normal sync: {start} → {end}"
            )

            total_synced += self._sync_contract_range(
                instrument=instrument,
                contract=current_contract.contract,
                start=start,
                end=end,
            )

            return total_synced

        # ----------------------------------------------------------
        # 6. Current contract doesn't exist
        # ----------------------------------------------------------

        if latest_instrument is None:
            raise RuntimeError(
                f"No existing 1m candles found for {instrument}"
            )

        # ----------------------------------------------------------
        # 7. Contract rollover detected
        # ----------------------------------------------------------

        previous_contract = self.contract_repo.get_previous_contract(
            instrument=instrument,
            contract=current_contract.contract,
        )

        if previous_contract is None:
            raise RuntimeError(
                f"Could not resolve previous contract "
                f"{latest_instrument.contract}"
            )

        print(
            f"{instrument} contract rollover detected: "
            f"{previous_contract.contract} → "
            f"{current_contract.contract}"
        )

        latest_previous = (
            self.candle_repo.latest_timestamp_by_contract(
                contract=previous_contract.contract,
                timeframe=1,
            )
        )

        if latest_previous is None:
            raise RuntimeError(
                f"No 1m candles found for previous contract "
                f"{previous_contract.contract}"
            )

        # ----------------------------------------------------------
        # Contract rollover timestamp
        # ----------------------------------------------------------

        rollover_start_ny = datetime.combine(
            current_contract.rollover_date,
            dt_time(18, 0),
            tzinfo=NY_TZ,
        )

        rollover_start_utc = rollover_start_ny.astimezone(
            timezone.utc
        )

        print(
            f"Rollover: {previous_contract.contract} → "
            f"{current_contract.contract} at "
            f"{rollover_start_ny}"
        )

        # ----------------------------------------------------------
        # Sync missing candles for previous contract
        # ----------------------------------------------------------

        previous_start = latest_previous + timedelta(minutes=1)

        # Last 1m candle belonging to previous contract
        previous_end = rollover_start_utc - timedelta(minutes=1)

        if previous_start <= previous_end:

            print(
                f"Filling {previous_contract.contract}: "
                f"{previous_start} → {previous_end}"
            )

            total_synced += self._sync_contract_range(
                instrument=instrument,
                contract=previous_contract.contract,
                start=previous_start,
                end=previous_end,
            )

        else:
            print(
                f"No missing {previous_contract.contract} "
                f"candles before rollover"
            )
        # ----------------------------------------------------------
        # Sync current contract from rollover
        # ----------------------------------------------------------

        new_start = rollover_start_utc

        if new_start < end:

            print(
                f"Starting {current_contract.contract}: "
                f"{new_start} → {end}"
            )

            total_synced += self._sync_contract_range(
                instrument=instrument,
                contract=current_contract.contract,
                start=new_start,
                end=end,
            )

        return total_synced
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable
from zoneinfo import ZoneInfo

from data.models.candle import Candle

# HTF_NY_TZ = ZoneInfo("America/New_York")
NY_TZ = ZoneInfo("America/New_York")
UTC_TZ = ZoneInfo("UTC")


@dataclass(frozen=True, slots=True)
class HTFDefinition:
    timeframe: int
    name: str


HTF_3M = HTFDefinition(
    timeframe=3,
    name="3m",
)

HTF_30M = HTFDefinition(
    timeframe=30,
    name="30m",
)

HTF_1H = HTFDefinition(
    timeframe=60,
    name="1h",
)

HTF_4H = HTFDefinition(
    timeframe=240,
    name="4h",
)

HTF_7H = HTFDefinition(
    timeframe=420,
    name="7h",
)

HTF_D = HTFDefinition(
    timeframe=1440,
    name="D",
)
HTF_4H_BOUNDARIES = [(18, 0),(22, 0),(2, 0),(6, 0),(10, 0),(14, 0),]
HTF_7H_BOUNDARIES = [(18, 0),(1, 0),(8, 0),(15, 0),]

HTF_7H_PERIODS = [
    (18, 0, 1, 0),
    (1, 0, 8, 0),
    (8, 0, 15, 0),
    (15, 0, 17, 0),
]

HTF_4H_PERIODS = [
    (18, 0, 22, 0),
    (22, 0, 2, 0),
    (2, 0, 6, 0),
    (6, 0, 10, 0),
    (10, 0, 14, 0),
    (14, 0, 17, 0),
]

class HTFCandleBuilder:
    def __init__(
        self,
        candle_repo,
        history_loader,
        on_candle: Callable[[Candle], None],
    ):
        self._candle_repo = candle_repo
        self.history_loader = history_loader
        self._on_candle = on_candle

    def _is_weekend(self, timestamp_utc: datetime) -> bool:
        timestamp_ny = timestamp_utc.astimezone(NY_TZ)
        return timestamp_ny.weekday() >= 5
    def build(
        self,
        instrument: str,
        contract: str,
        timeframe: HTFDefinition,
        end: datetime,
    ) -> Candle | None:

        end = end.astimezone(timezone.utc).replace(
            second=0,
            microsecond=0,
        )

        start = self._get_start(
            end=end,
            timeframe=timeframe,
        )

        last_1m = end - timedelta(minutes=1)

        one_minute_candles = (
            self._candle_repo.get_between(
                contract=contract,
                timeframe=1,
                start=start,
                end=last_1m,
            )
        )

        expected_minutes = int(
            (end - start).total_seconds() / 60
        )

        if len(one_minute_candles) != expected_minutes:
            print(
                f"Cannot build {timeframe.name} candle for "
                f"{instrument} {contract}: "
                f"expected {expected_minutes} 1m candles, "
                f"found {len(one_minute_candles)} "
                f"for {start} → {last_1m}"
            )
            return None

        one_minute_candles.sort(
            key=lambda c: c.timestamp
        )

        for i, candle in enumerate(one_minute_candles):
            expected_timestamp = (
                start + timedelta(minutes=i)
            )

            if candle.timestamp != expected_timestamp:
                print(
                    f"Cannot build {timeframe.name} candle for "
                    f"{instrument} {contract}: "
                    f"missing 1m candle at "
                    f"{expected_timestamp}"
                )
                return None

        first = one_minute_candles[0]
        last = one_minute_candles[-1]

        htf_candle = Candle(
            instrument=instrument,
            timeframe=timeframe.timeframe,
            timestamp=start,
            contract=contract,
            open=first.open,
            high=max(
                c.high for c in one_minute_candles
            ),
            low=min(
                c.low for c in one_minute_candles
            ),
            close=last.close,
            volume=sum(
                c.volume for c in one_minute_candles
            ),
        )

        self._on_candle(htf_candle)

        return htf_candle

    def _get_session_period_start(
        self,
        timestamp_ny: datetime,
        boundaries: list[tuple[int, int]],
    ) -> datetime:
        """Return the start of the custom NY session period containing timestamp."""

        candidates = []

        for hour, minute in boundaries:
            boundary = timestamp_ny.replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0,
            )

            # If this boundary is later than the timestamp,
            # it belongs to the previous NY calendar day.
            if boundary > timestamp_ny:
                boundary -= timedelta(days=1)

            candidates.append(boundary)

        return max(candidates)

    def _get_next_session_boundary(
        self,
        start_ny: datetime,
        boundaries: list[tuple[int, int]],
    ) -> datetime:
        """Return the next custom NY session boundary after start_ny."""

        candidates = []

        for hour, minute in boundaries:
            boundary = start_ny.replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0,
            )

            if boundary <= start_ny:
                boundary += timedelta(days=1)

            candidates.append(boundary)

        return min(candidates)

    def _get_explicit_period(
        self,
        timestamp_ny: datetime,
        periods: list[tuple[int, int, int, int]],
    ) -> tuple[datetime, datetime]:
        """Return the NY start/end of the custom period containing timestamp."""

        for start_hour, start_minute, end_hour, end_minute in periods:

            start_ny = timestamp_ny.replace(
                hour=start_hour,
                minute=start_minute,
                second=0,
                microsecond=0,
            )

            end_ny = timestamp_ny.replace(
                hour=end_hour,
                minute=end_minute,
                second=0,
                microsecond=0,
            )

            # Period crosses midnight.
            if end_ny <= start_ny:
                end_ny += timedelta(days=1)

            # If this period's start is after the timestamp,
            # move the entire period to the previous NY date.
            if start_ny > timestamp_ny:
                start_ny -= timedelta(days=1)
                end_ny -= timedelta(days=1)

            if start_ny <= timestamp_ny < end_ny:
                return start_ny, end_ny

        raise ValueError(
            f"Timestamp {timestamp_ny} falls outside all defined HTF periods"
        )

    def _get_completed_period(
        self,
        end_utc: datetime,
        definition: HTFDefinition,
    ) -> tuple[datetime, datetime]:

        end_ny = end_utc.astimezone(NY_TZ)

        if definition.timeframe == 420:
            periods = HTF_7H_PERIODS

        elif definition.timeframe == 240:
            periods = HTF_4H_PERIODS

        else:
            # Standard timeframes can continue using the
            # period-containing logic.
            return self._get_period_boundaries(
                end_utc - timedelta(microseconds=1),
                definition,
            )

        candidates = []

        for start_hour, start_minute, end_hour, end_minute in periods:

            start_ny = end_ny.replace(
                hour=start_hour,
                minute=start_minute,
                second=0,
                microsecond=0,
            )

            end_ny_period = end_ny.replace(
                hour=end_hour,
                minute=end_minute,
                second=0,
                microsecond=0,
            )

            # Cross-midnight period
            if end_ny_period <= start_ny:
                end_ny_period += timedelta(days=1)

            # We need to consider yesterday's instance too.
            for day_offset in (-1, 0, 1):
                candidate_start = start_ny + timedelta(days=day_offset)
                candidate_end = end_ny_period + timedelta(days=day_offset)

                if candidate_end <= end_ny:
                    candidates.append(
                        (candidate_start, candidate_end)
                    )

        if not candidates:
            raise ValueError(
                f"No completed HTF period found before {end_ny}"
            )

        # Pick the most recent period that has completely ended.
        start_ny, completed_end_ny = max(
            candidates,
            key=lambda period: period[1],
        )

        return (
            start_ny.astimezone(UTC_TZ),
            completed_end_ny.astimezone(UTC_TZ),
        )
    def _get_period_boundaries(
        self,
        timestamp_utc: datetime,
        definition: HTFDefinition,
    ) -> tuple[datetime, datetime]:
        """
        Return the NY-defined start and exclusive end of the HTF
        period containing timestamp_utc.

        All session boundaries are calculated in America/New_York,
        then converted back to UTC for DB queries.
        """

        timestamp_ny = timestamp_utc.astimezone(NY_TZ)
        # ---------------------------------------------------------
        # 3m
        # ---------------------------------------------------------
        if definition.timeframe == 3:
            minute = (timestamp_ny.minute // 3) * 3

            start_ny = timestamp_ny.replace(
                minute=minute,
                second=0,
                microsecond=0,
            )
            end_ny = start_ny + timedelta(minutes=3)

            if 17 <= start_ny.hour < 18:
                raise ValueError(
                    f"3m candle falls inside maintenance window: "
                    f"{start_ny} -> {end_ny}"
                )
        # ---------------------------------------------------------
        # 30m
        # ---------------------------------------------------------
        elif definition.timeframe == 30:
            minute = (timestamp_ny.minute // 30) * 30

            start_ny = timestamp_ny.replace(
                minute=minute,
                second=0,
                microsecond=0,
            )

            end_ny = start_ny + timedelta(minutes=30)

        # ---------------------------------------------------------
        # 1h
        # ---------------------------------------------------------
        elif definition.timeframe == 60:
            start_ny = timestamp_ny.replace(
                minute=0,
                second=0,
                microsecond=0,
            )

            end_ny = start_ny + timedelta(hours=1)

        # ---------------------------------------------------------
        # 4h — Ping custom boundaries
        # ---------------------------------------------------------
        elif definition.timeframe == 240:
            start_ny, end_ny = self._get_explicit_period(
                timestamp_ny,
                HTF_4H_PERIODS,
            )

        # ---------------------------------------------------------
        # 7h — Ping custom boundaries
        # ---------------------------------------------------------
        elif definition.timeframe == 420:
            start_ny, end_ny = self._get_explicit_period(
                timestamp_ny,
                HTF_7H_PERIODS,
            )

        # ---------------------------------------------------------
        # Daily
        # ---------------------------------------------------------
        elif definition.timeframe == 1440:
            start_ny = timestamp_ny.replace(
                hour=18,
                minute=0,
                second=0,
                microsecond=0,
            )

            if timestamp_ny < start_ny:
                start_ny -= timedelta(days=1)

            end_ny = start_ny + timedelta(days=1)

        else:
            raise ValueError(
                f"Unsupported timeframe: {definition.timeframe}"
            )

        return (
            start_ny.astimezone(UTC_TZ),
            end_ny.astimezone(UTC_TZ),
        )

    def _expected_1m_count(
        self,
        start_utc: datetime,
        end_utc: datetime,
        definition: HTFDefinition,
    ) -> int:

        duration_minutes = int(
            (end_utc - start_utc).total_seconds() / 60
        )

        # Daily candle contains a 17:00–18:00 NY
        # maintenance period with no 1m candles.
        if definition.timeframe == 1440:
            return duration_minutes - 60

        return duration_minutes

    def build_completed_candle(
        self,
        instrument: str,
        contract: str,
        end_utc: datetime,
        definition: HTFDefinition,
    ) -> Candle | None:

        start_utc, end_utc = self._get_completed_period(
            end_utc,
            definition,
        )

        return self._build_candle_for_period(
            instrument=instrument,
            contract=contract,
            start_utc=start_utc,
            end_utc=end_utc,
            definition=definition,
        )
    def build_completed_candle_old(
        self,
        instrument: str,
        contract: str,
        end_utc: datetime,
        definition: HTFDefinition,
        ) -> Candle | None:
            """
            Build one completed HTF candle from 1m candles in the DB.

            `end_utc` is the exclusive completion boundary.
            """

            start_utc, end_utc = self._get_completed_period(
                end_utc,
                definition,
            )

            candles_1m = self._candle_repo.get_between(
                contract=contract,
                timeframe=1,
                start=start_utc,
                end=end_utc - timedelta(minutes=1),
            )

            if not candles_1m:
                print(
                    f"No 1m candles found for "
                    f"{instrument} {contract} "
                    f"{start_utc} → {end_utc}"
                )
                return None

            # Make sure every 1m candle belongs to the requested period.
            candles_1m = [
                candle
                for candle in candles_1m
                if start_utc <= candle.timestamp < end_utc
            ]

            # Verify contiguous 1m candles.
            expected_count = self._expected_1m_count(
                start_utc=start_utc,
                end_utc=end_utc,
                definition=definition,
            )

            if len(candles_1m) != expected_count:
                print(
                    f"Incomplete 1m data for "
                    f"{instrument} {contract}: "
                    f"expected={expected_count}, "
                    f"actual={len(candles_1m)} "
                    f"for {start_utc} → {end_utc}"
                )
                return None

            for previous, current in zip(
                candles_1m,
                candles_1m[1:],
            ):
                if current.timestamp != (
                    previous.timestamp + timedelta(minutes=1)
                ):
                    print(
                        f"Gap in 1m data for "
                        f"{instrument} {contract}: "
                        f"{previous.timestamp} → "
                        f"{current.timestamp}"
                    )
                    return None

            first = candles_1m[0]
            last = candles_1m[-1]

            htf_candle = Candle(
                instrument=instrument,
                timeframe=definition.timeframe,
                timestamp=start_utc,
                contract=contract,
                open=first.open,
                high=max(c.high for c in candles_1m),
                low=min(c.low for c in candles_1m),
                close=last.close,
                volume=sum(c.volume for c in candles_1m),
            )

            self._candle_repo.save([htf_candle])

            return htf_candle

    def backfill_contract_htf_history(
        self,
        instrument: str,
        contract: str,
    ) -> dict[str, int]:
        """
        Backfill all Ping HTF timeframes for a contract
        using existing 1m candles.
        """
        first_1m, last_1m = self._candle_repo.get_time_range(
            contract=contract,
            timeframe=1,
        )

        if first_1m is None or last_1m is None:
            print(
                f"No 1m history found for "
                f"{instrument} {contract}"
            )
            return {}

        start_utc = first_1m
        end_utc = last_1m + timedelta(minutes=1)
        
        # start_utc=datetime(
        #     2026, 9, 9, 21, 0,
        #     tzinfo=UTC_TZ,
        # )
        # end_utc=datetime(
        #     2026, 9, 11, 0, 0,
        #     tzinfo=UTC_TZ,
        # )

        print(
            f"1m history range: "
            f"{start_utc} → {end_utc}"
        )
        
        definitions = [
            HTFDefinition(timeframe=3, name="3m"),
            HTFDefinition(timeframe=30, name="30m"),
            HTFDefinition(timeframe=60, name="1h"),
            HTFDefinition(timeframe=240, name="4h"),
            HTFDefinition(timeframe=420, name="7h"),
            HTFDefinition(timeframe=1440, name="D"),
        ]

        results: dict[str, int] = {}
        
        print(
            f"\n=== HTF BACKFILL START ===\n"
            f"Instrument: {instrument}\n"
            f"Contract:   {contract}\n"
            f"Start:      {start_utc}\n"
            f"End:        {end_utc}\n"
        )

        for definition in definitions:
            print(
                f"\n--- Backfilling {definition.name} ---"
            )

            count = self.backfill_htf(
                instrument=instrument,
                contract=contract,
                start_utc=start_utc,
                end_utc=end_utc,
                definition=definition,
            )

            results[definition.name] = count

        print("\n=== HTF BACKFILL COMPLETE ===")

        for timeframe, count in results.items():
            print(f"{timeframe}: {count}")

        return results
    
    def backfill_htf(
        self,
        instrument: str,
        contract: str,
        start_utc: datetime,
        end_utc: datetime,
        definition: HTFDefinition,
    ) -> int:
        """
        Backfill completed HTF candles from existing 1m candles.
        """
        current = start_utc.replace(second=0, microsecond=0)

        built = 0
        skipped = 0

        while current < end_utc:

            current_ny = current.astimezone(NY_TZ)

            weekday = current_ny.weekday()

            # Friday after 18:00 NY → Sunday before 18:00 NY
            if (
                (weekday == 4 and current_ny.hour >= 18)
                or weekday == 5
                or (weekday == 6 and current_ny.hour < 18)
            ):
                # Find next Sunday 18:00 NY
                days_until_sunday = (6 - weekday) % 7

                next_sunday_ny = (
                    current_ny.replace(
                        hour=18,
                        minute=0,
                        second=0,
                        microsecond=0,
                    )
                    + timedelta(days=days_until_sunday)
                )

                # If we're already on Sunday after midnight,
                # this gives Sunday 18:00.
                if weekday == 4:
                    next_sunday_ny = (
                        current_ny.replace(
                            hour=18,
                            minute=0,
                            second=0,
                            microsecond=0,
                        )
                        + timedelta(days=2)
                    )

                elif weekday == 5:
                    next_sunday_ny = (
                        current_ny.replace(
                            hour=18,
                            minute=0,
                            second=0,
                            microsecond=0,
                        )
                        + timedelta(days=1)
                    )

                current = next_sunday_ny.astimezone(UTC_TZ)
                continue

            # Daily maintenance: 17:00–18:00 NY
            if 17 <= current_ny.hour < 18:
                next_session_ny = current_ny.replace(
                    hour=18,
                    minute=0,
                    second=0,
                    microsecond=0,
                )

                current = next_session_ny.astimezone(UTC_TZ)
                continue

            # Get the HTF period containing current.
            start_period, end_period = self._get_period_boundaries(
                current,
                definition,
            )

            # If this period starts before our requested range,
            # move directly to the next period.
            if start_period < start_utc:
                current = end_period
                continue

            # Don't build a period that extends beyond our requested range.
            if end_period > end_utc:
                break
            
            if self._candle_repo.exists(
                contract=contract,
                timeframe=definition.timeframe,
                timestamp=start_period,
            ):
                current = end_period
                # print("candle exists: not merging")
                continue

            # print(
            #     f"BACKFILL: building "
            #     f"{start_period} → {end_period}"
            # )

            # We already know the exact period, so retrieve its 1m candles
            # directly rather than calling build_completed_candle(), which
            # would recalculate the period.
            candles_1m = self._candle_repo.get_between(
                contract=contract,
                timeframe=1,
                start=start_period,
                end=end_period - timedelta(minutes=1),
            )

            candles_1m = [
                c for c in candles_1m
                if start_period <= c.timestamp < end_period
            ]

            expected_count = self._expected_1m_count(
                start_utc=start_period,
                end_utc=end_period,
                definition=definition,
            )

            if len(candles_1m) != expected_count:
                print(
                    f"{definition.name} incomplete: "
                    f"{start_period} → {end_period} "
                    f"({len(candles_1m)}/{expected_count} 1m candles)"
                )

                # Attempt to repair the missing 1m data.
                synced = self.history_loader.sync_candle_range(
                    instrument=instrument,
                    contract=contract,
                    start_utc=start_period,
                    end_utc=end_period,
                )

                print(
                    f"1m sync returned {synced} candles for "
                    f"{definition.name} period"
                )

                # Read the DB again after synchronization.
                candles_1m = self._candle_repo.get_between(
                    contract=contract,
                    timeframe=1,
                    start=start_period,
                    end=end_period - timedelta(minutes=1),
                )

                candles_1m = [
                    c
                    for c in candles_1m
                    if start_period <= c.timestamp < end_period
                ]

                if len(candles_1m) != expected_count:
                    print(
                        f"{definition.name} still incomplete after "
                        f"1m sync: {start_period} → {end_period} "
                        f"({len(candles_1m)}/{expected_count})"
                    )

                    skipped += 1
                    current = end_period
                    continue

                print(
                    f"{definition.name} repaired successfully: "
                    f"{start_period} → {end_period}"
                )

            # Verify continuity.
            continuous = all(
                current_candle.timestamp
                == previous_candle.timestamp + timedelta(minutes=1)
                for previous_candle, current_candle
                in zip(candles_1m, candles_1m[1:])
            )

            if not continuous:
                print(
                    f"BACKFILL: gap detected "
                    f"{start_period} → {end_period}"
                )
                skipped += 1
                current = end_period
                continue

            first = candles_1m[0]
            last = candles_1m[-1]

            htf_candle = Candle(
                instrument=instrument,
                timeframe=definition.timeframe,
                timestamp=start_period,
                contract=contract,
                open=first.open,
                high=max(c.high for c in candles_1m),
                low=min(c.low for c in candles_1m),
                close=last.close,
                volume=sum(c.volume for c in candles_1m),
            )

            self._candle_repo.save([htf_candle])

            built += 1

            current = end_period

        print(
            f"{definition.name} backfill complete: "
            f"{instrument} {contract} → "
            f"{built} candles built, "
            f"{skipped} incomplete/missing"
        )

        return built

    def backfill_3m(
        self,
        instrument: str,
        contract: str,
        start_utc: datetime,
        end_utc: datetime,
    ) -> int:
        """
        Build all complete 3m candles from existing 1m candles
        between start_utc and end_utc.
        """

        current = start_utc.replace(second=0, microsecond=0)

        # Align to the next 3-minute boundary.
        remainder = current.minute % 3
        if remainder != 0:
            current += timedelta(minutes=3 - remainder)

        built = 0

        while current + timedelta(minutes=3) <= end_utc:

            current_ny = current.astimezone(NY_TZ)

            # Skip the 17:00–18:00 NY maintenance window.
            if 17 <= current_ny.hour < 18:
                next_session_ny = current_ny.replace(
                    hour=18,
                    minute=0,
                    second=0,
                    microsecond=0,
                )

                if current_ny >= next_session_ny:
                    next_session_ny += timedelta(days=1)

                current = next_session_ny.astimezone(UTC_TZ)
                continue

            candle = self.build_completed_candle(
                instrument=instrument,
                contract=contract,
                end_utc=current + timedelta(minutes=3),
                definition=HTFDefinition(
                    timeframe=3,
                    name="3m",
                ),
            )

            if candle is not None:
                built += 1

            current += timedelta(minutes=3)

        print(
            f"3m backfill complete: "
            f"{instrument} {contract} → {built} candles"
        )

        return built

    def _build_candle_for_period(
        self,
        instrument: str,
        contract: str,
        start_utc: datetime,
        end_utc: datetime,
        definition: HTFDefinition,
    ) -> Candle | None:

        candles_1m = self._candle_repo.get_between(
            contract=contract,
            timeframe=1,
            start=start_utc,
            end=end_utc - timedelta(minutes=1),
        )

        candles_1m = [
            c for c in candles_1m
            if start_utc <= c.timestamp < end_utc
        ]

        expected_count = self._expected_1m_count(
            start_utc=start_utc,
            end_utc=end_utc,
            definition=definition,
        )

        # if len(candles_1m) != expected_count:
        #     print(
        #         f"No complete {definition.name} candle: "
        #         f"{start_utc} → {end_utc} "
        #         f"({len(candles_1m)}/{expected_count} 1m candles)"
        #     )
        #     return None
        if len(candles_1m) != expected_count:

            print(
                f"{definition.name} incomplete: "
                f"{start_utc} → {end_utc} "
                f"({len(candles_1m)}/{expected_count} 1m candles)"
            )

            # Attempt to repair the missing 1m data.
            synced = self.history_loader.sync_candle_range(
                instrument=instrument,
                contract=contract,
                start_utc=start_utc,
                end_utc=end_utc,
            )

            print(
                f"1m sync returned {synced} candles for "
                f"{definition.name} period"
            )

            # Read the DB again after synchronization.
            candles_1m = self._candle_repo.get_between(
                contract=contract,
                timeframe=1,
                start=start_utc,
                end=end_utc - timedelta(minutes=1),
            )

            candles_1m = [
                c
                for c in candles_1m
                if start_utc <= c.timestamp < end_utc
            ]

            if len(candles_1m) != expected_count:
                print(
                    f"{definition.name} still incomplete after "
                    f"1m sync: {start_utc} → {end_utc} "
                    f"({len(candles_1m)}/{expected_count})"
                )
                return None

            print(
                f"{definition.name} repaired successfully: "
                f"{start_utc} → {end_utc}"
            )

        for previous, current in zip(
            candles_1m,
            candles_1m[1:],
        ):
            if current.timestamp != (
                previous.timestamp + timedelta(minutes=1)
            ):
                print(
                    f"Gap in {definition.name} candle: "
                    f"{start_utc} → {end_utc}"
                )
                return None

        first = candles_1m[0]
        last = candles_1m[-1]

        htf_candle = Candle(
            instrument=instrument,
            timeframe=definition.timeframe,
            timestamp=start_utc,
            contract=contract,
            open=first.open,
            high=max(c.high for c in candles_1m),
            low=min(c.low for c in candles_1m),
            close=last.close,
            volume=sum(c.volume for c in candles_1m),
        )

        self._candle_repo.save([htf_candle])

        return htf_candle

    # def process_realtime_htf(
    #     self,
    #     instrument: str,
    #     contract: str,
    #     boundary_utc: datetime,
    #     definition: HTFDefinition,
    # ) -> int:
    #     """
    #     Rebuild the current and previous completed HTF candles
    #     at a realtime boundary.

    #     This intentionally rebuilds existing candles so that any
    #     corrections made by REST reconciliation are reflected.
    #     """

    #     built = 0

    #     # Find the HTF period that has just completed.
    #     current_start, current_end = self._get_completed_period(
    #         boundary_utc,
    #         definition,
    #     )

    #     periods = [
    #         (current_start, current_end),
    #     ]

    #     # Find the immediately previous HTF period.
    #     previous_start, previous_end = self._get_completed_period(
    #         current_start - timedelta(microseconds=1),
    #         definition,
    #     )

    #     periods.insert(
    #         0,
    #         (previous_start, previous_end),
    #     )

    #     for start_period, end_period in periods:

    #         candle = self._build_candle_for_period(
    #             instrument=instrument,
    #             contract=contract,
    #             start_utc=start_period,
    #             end_utc=end_period,
    #             definition=definition,
    #         )

    #         if candle is not None:
    #             built += 1

    #     return built

    def get_realtime_htf_periods(
        self,
        instrument: str,
        contract: str,
        boundary_utc: datetime,
        definition: HTFDefinition,
    ) -> list[tuple[datetime, datetime]]:
        """
        Determine which completed HTF periods should be processed
        at the current scheduler boundary.
        """

        current_start, current_end = self._get_completed_period(
            boundary_utc,
            definition,
        )

        latest = self.candle_repo.get_last(
            contract=contract,
            timeframe=definition.timeframe,
        )

        # No HTF candles exist yet.
        if latest is None:
            return [(current_start, current_end)]

        latest_start = latest.timestamp

        # If the latest DB candle is within the previous two
        # completed periods, rebuild previous + current.
        previous_start, previous_end = self._get_completed_period(
            current_start - timedelta(microseconds=1),
            definition,
        )

        if latest_start >= previous_start:
            return [
                (previous_start, previous_end),
                (current_start, current_end),
            ]

        # DB is behind. Build every period from the period
        # immediately after the latest DB candle through current.
        periods = []

        current_period_start = latest_start

        while current_period_start < current_start:
            period_start, period_end = self._get_period_boundaries(
                current_period_start,
                definition,
            )

            if period_start < latest_start:
                current_period_start = period_end
                continue

            if period_end > current_end:
                break

            periods.append((period_start, period_end))
            current_period_start = period_end

        # Include the current completed period.
        periods.append((current_start, current_end))

        return periods

    def process_realtime_htf(
        self,
        instrument: str,
        contract: str,
        boundary_utc: datetime,
        definition: HTFDefinition,
    ) -> int:

        periods = self.get_realtime_htf_periods(
            instrument=instrument,
            contract=contract,
            boundary_utc=boundary_utc,
            definition=definition,
        )

        print(
            f"{definition.name} realtime processing: "
            f"{len(periods)} period(s)"
        )

        built = 0

        for start_period, end_period in periods:

            print(
                f"Processing {definition.name}: "
                f"{start_period} → {end_period}"
            )

            candle = self._build_candle_for_period(
                instrument=instrument,
                contract=contract,
                start_period=start_period,
                end_period=end_period,
                definition=definition,
            )

            if candle is not None:
                built += 1

        return built

    def is_htf_boundary(
        self,
        timestamp_utc: datetime,
        definition: HTFDefinition,
    ) -> bool:
        """
        Return True when timestamp_utc is an HTF period boundary.
        """

        timestamp_ny = timestamp_utc.astimezone(NY_TZ)

        if definition.timeframe == 3:
            return timestamp_ny.minute % 3 == 0

        if definition.timeframe == 30:
            return timestamp_ny.minute in (0, 30)

        if definition.timeframe == 60:
            return timestamp_ny.minute == 0

        if definition.timeframe == 240:
            return (
                timestamp_ny.minute == 0
                and timestamp_ny.hour in (2, 6, 10, 14, 18, 22)
            )

        if definition.timeframe == 420:
            return (
                timestamp_ny.minute == 0
                and timestamp_ny.hour in (1, 8, 15, 17)
            )

        if definition.timeframe == 1440:
            return (
                timestamp_ny.hour == 18
                and timestamp_ny.minute == 0
            )

        raise ValueError(
            f"Unsupported HTF timeframe: {definition.timeframe}"
        )
    @staticmethod
    def _regular_start(
        end: datetime,
        minutes: int,
    ) -> datetime:

        total_minutes = (
            end.hour * 60
            + end.minute
        )

        start_minutes = (
            total_minutes // minutes
        ) * minutes

        return end.replace(
            hour=start_minutes // 60,
            minute=start_minutes % 60,
            second=0,
            microsecond=0,
        )

    @staticmethod
    def _session_start(
        end: datetime,
        start_hours: list[int],
    ) -> datetime:

        candidates = []

        for hour in start_hours:

            candidate = end.replace(
                hour=hour,
                minute=0,
                second=0,
                microsecond=0,
            )

            if candidate > end:
                candidate -= timedelta(days=1)

            candidates.append(candidate)

        return max(candidates)

    @staticmethod
    def _daily_start(
        end: datetime,
    ) -> datetime:

        if end.hour >= 18:
            return end.replace(
                hour=18,
                minute=0,
                second=0,
                microsecond=0,
            )

        return (
            end.replace(
                hour=18,
                minute=0,
                second=0,
                microsecond=0,
            )
            - timedelta(days=1)
        )
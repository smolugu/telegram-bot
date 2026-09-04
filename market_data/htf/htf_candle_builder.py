from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from data.models.candle import Candle


from collections import Counter
from datetime import timedelta


def inspect_1m_gaps(candles):
    candles = sorted(
        candles,
        key=lambda c: c.timestamp,
    )

    print(f"Total candles: {len(candles)}")

    if not candles:
        return

    print(f"First: {candles[0].timestamp}")
    print(f"Last:  {candles[-1].timestamp}")

    gaps = []

    for previous, current in zip(candles, candles[1:]):

        delta = current.timestamp - previous.timestamp

        # Ignore normal gaps larger than 1 minute for now,
        # just record them.
        if delta > timedelta(minutes=1):
            gaps.append(
                (
                    previous.timestamp,
                    current.timestamp,
                    delta,
                )
            )

    print(f"\nGaps > 1 minute: {len(gaps)}")

    print("\nLargest gaps:")

    for previous, current, delta in sorted(
        gaps,
        key=lambda x: x[2],
        reverse=True,
    )[:30]:

        print(
            f"{previous} → {current} "
            f"({delta})"
        )

class HTFCandleBuilder:
    NY_TZ = ZoneInfo("America/New_York")
    UTC_TZ = timezone.utc

    def build(
        self,
        candles: list[Candle],
        timeframe: int,
    ) -> list[Candle]:
        """
        Build 1-minute candles into a higher timeframe.

        Example:
            timeframe=30 -> 30-minute candles
            timeframe=60 -> 1-hour candles
            timeframe=240 -> 4-hour candles
        """

        if not candles:
            return []

        buckets: dict[datetime, list[Candle]] = defaultdict(list)
        
        for candle in candles:
            if timeframe == 420:
                bucket = self._get_7h_bucket_start(
                    candle.timestamp
                )
            elif timeframe == 240:
                bucket = self._get_4h_bucket_start(candle.timestamp)
            else:
                bucket = self._get_bucket_start(
                    candle.timestamp,
                    timeframe,
                )
            if bucket is None:
                continue
            buckets[bucket].append(candle)

        result: list[Candle] = []

        # return result
        for bucket_start in sorted(buckets.keys()):

            bucket = buckets[bucket_start]

        
            if timeframe not in (240, 420):

                if len(bucket) != timeframe:
                    continue

            result.append(
                Candle(
                    instrument=bucket[0].instrument,
                    contract=bucket[0].contract,
                    timeframe=timeframe,
                    timestamp=bucket_start,

                    open=bucket[0].open,
                    high=max(c.high for c in bucket),
                    low=min(c.low for c in bucket),
                    close=bucket[-1].close,
                    volume=sum(c.volume for c in bucket),
                )
            )
            if timeframe == 420:
                print(
                    f"timeframe={timeframe}, "
                    f"bucket={bucket_start}, "
                    f"candles={len(bucket)}"
                )

        return result

    @classmethod
    def _get_4h_bucket_start(
        cls,
        timestamp: datetime,
    ) -> datetime | None:
        """
        Return the Ping 4H bucket start.

        NY session structure:

            18:00 → 22:00
            22:00 → 02:00
            02:00 → 06:00
            06:00 → 10:00
            10:00 → 14:00
            14:00 → EOD

        17:00 → 18:00 is excluded.

        Timestamp is stored in UTC.
        """

        ny_timestamp = timestamp.astimezone(cls.NY_TZ)

        hour = ny_timestamp.hour

        # --------------------------------------------------------------
        # 18:00 → 22:00
        # --------------------------------------------------------------
        if hour >= 18:

            bucket_ny = ny_timestamp.replace(
                hour=18,
                minute=0,
                second=0,
                microsecond=0,
            )

        # --------------------------------------------------------------
        # 00:00 → 02:00
        #
        # This belongs to the previous day's 22:00 bucket.
        # --------------------------------------------------------------
        elif hour < 2:

            previous_day = (
                ny_timestamp - timedelta(days=1)
            )

            bucket_ny = previous_day.replace(
                hour=22,
                minute=0,
                second=0,
                microsecond=0,
            )

        # --------------------------------------------------------------
        # 02:00 → 06:00
        # --------------------------------------------------------------
        elif hour < 6:

            bucket_ny = ny_timestamp.replace(
                hour=2,
                minute=0,
                second=0,
                microsecond=0,
            )

        # --------------------------------------------------------------
        # 06:00 → 10:00
        # --------------------------------------------------------------
        elif hour < 10:

            bucket_ny = ny_timestamp.replace(
                hour=6,
                minute=0,
                second=0,
                microsecond=0,
            )

        # --------------------------------------------------------------
        # 10:00 → 14:00
        # --------------------------------------------------------------
        elif hour < 14:

            bucket_ny = ny_timestamp.replace(
                hour=10,
                minute=0,
                second=0,
                microsecond=0,
            )

        # --------------------------------------------------------------
        # 14:00 → 17:00
        #
        # EOD candle.
        # --------------------------------------------------------------
        elif hour < 17:

            bucket_ny = ny_timestamp.replace(
                hour=14,
                minute=0,
                second=0,
                microsecond=0,
            )

        # --------------------------------------------------------------
        # 17:00 → 18:00
        #
        # Excluded.
        # --------------------------------------------------------------
        else:

            return None

        return bucket_ny.astimezone(timezone.utc)
    @classmethod
    def _get_7h_bucket_start(
        cls,
        timestamp: datetime,
    ) -> datetime | None:

        ny_timestamp = timestamp.astimezone(cls.NY_TZ)

        hour = ny_timestamp.hour

        # 18:00 → 01:00
        if hour >= 18 or hour < 1:

            if hour < 1:
                previous_day = ny_timestamp - timedelta(days=1)

                bucket_ny = previous_day.replace(
                    hour=18,
                    minute=0,
                    second=0,
                    microsecond=0,
                )
            else:
                bucket_ny = ny_timestamp.replace(
                    hour=18,
                    minute=0,
                    second=0,
                    microsecond=0,
                )

        # 01:00 → 08:00
        elif hour < 8:

            bucket_ny = ny_timestamp.replace(
                hour=1,
                minute=0,
                second=0,
                microsecond=0,
            )

        # 08:00 → 15:00
        elif hour < 15:

            bucket_ny = ny_timestamp.replace(
                hour=8,
                minute=0,
                second=0,
                microsecond=0,
            )

        # 15:00 → EOD
        elif hour < 17:

            bucket_ny = ny_timestamp.replace(
                hour=15,
                minute=0,
                second=0,
                microsecond=0,
            )

        # 17:00 → 18:00 excluded
        else:

            return None

        return bucket_ny.astimezone(timezone.utc)
    
    @staticmethod
    def _get_bucket_start(
        timestamp: datetime,
        timeframe: int,
    ) -> datetime:
        """
        Returns the start of the timeframe bucket.

        Examples

        30m

        09:30 -> 09:30
        09:44 -> 09:30
        09:59 -> 09:30

        1h

        10:12 -> 10:00

        4h

        13:15 -> 12:00
        """

        total_minutes = (
            timestamp.hour * 60
            + timestamp.minute
        )

        bucket_minutes = (
            total_minutes // timeframe
        ) * timeframe

        return timestamp.replace(
            hour=bucket_minutes // 60,
            minute=bucket_minutes % 60,
            second=0,
            microsecond=0,
        )
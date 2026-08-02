from collections import defaultdict
from datetime import datetime

from data.models.candle import Candle


class HTFCandleBuilder:

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
            bucket = self._get_bucket_start(
                candle.timestamp,
                timeframe,
            )
            buckets[bucket].append(candle)

        result: list[Candle] = []

        for bucket_start in sorted(buckets.keys()):
            bucket = buckets[bucket_start]

            # ignore incomplete buckets
            expected = timeframe
            if len(bucket) != expected:
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

        return result

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
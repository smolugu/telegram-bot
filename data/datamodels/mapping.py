from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from massive.rest.models.futures import FuturesAgg
from typing import Protocol

from data.datamodels.candle import Candle
from data.utils.timezone_refactor import unix_to_est_timestamp

# class AggregateBar(Protocol):
#     window_start: int
#     open: float
#     high: float
#     low: float
#     close: float
#     volume: int

# type checking without improting FuturesAgg
# def to_candle(agg: AggregateBar) -> Candle:
def to_candle(agg: FuturesAgg) -> Candle:
    # dt = (
    #     datetime.fromtimestamp(
    #         agg.window_start / 1_000_000_000,
    #         tz=UTC,
    #     )
    #     .astimezone(ZoneInfo("America/New_York"))
    # )
    dt = unix_to_est_timestamp(agg.window_start)

    return Candle(
        timestamp=dt,
        open=agg.open,
        high=agg.high,
        low=agg.low,
        close=agg.close,
        volume=agg.volume,
    )
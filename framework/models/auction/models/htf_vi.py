from dataclasses import dataclass
from datetime import datetime

from framework.models.auction.models.base_model import LevelType, LiquidityType, VIStatus


# @dataclass
# class HTFVolumeImbalance(HTFLevel):
#     top: float
#     bottom: float
#     bullish: bool

@dataclass(slots=True)
class HTFVolumeImbalance:
    timeframe: str
    timestamp: datetime
    is_bullish: bool
    is_swept: bool

    upper: float
    lower: float

    status: VIStatus = VIStatus.OPEN
    liquidity_type = LiquidityType.INTERNAL
    level_type = LevelType.VI
    mitigation_time: datetime | None = None
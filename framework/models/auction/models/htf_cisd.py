from dataclasses import dataclass
from datetime import datetime
from framework.models.auction.models.base_model import CISDStatus, HTFLevel, LevelType, LiquidityType

# @dataclass
# class HTFCISD(HTFLevel):
#     price: float
#     bullish: bool

@dataclass(slots=True)
class HTFCISD:
    timeframe: str
    timestamp: datetime
    is_bullish: bool
    is_swept: bool

    upper_body: float
    lower_body: float
    upper_wick: float
    lower_wick: float

    status: CISDStatus = CISDStatus.OPEN
    liquidity_type = LiquidityType.INTERNAL
    level_type = LevelType.CISD
    mitigation_time: datetime | None = None
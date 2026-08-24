from dataclasses import dataclass
from datetime import datetime

from framework.models.auction.models.enums import  HTFFvgStatus, LevelType, LiquidityType

@dataclass(slots=True)
class HTFFVG:
    timeframe: str
    timestamp: datetime
    is_bullish: bool
    is_buy_side: bool
    is_touched: bool
    
    price: float
    upper: float
    lower: float
    is_swept: bool = False
    status: HTFFvgStatus = HTFFvgStatus.OPEN
    liquidity_type = LiquidityType.INTERNAL
    level_type = LevelType.FVG
    mitigation_time: datetime | None = None
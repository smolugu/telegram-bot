from dataclasses import dataclass
from datetime import datetime

from framework.models.auction.models.enums import HTFViStatus, LevelType, LiquidityType


@dataclass(slots=True)
class HTFVolumeImbalance:
    timeframe: str
    timestamp: datetime
    is_bullish: bool
    is_buy_side: bool
    
    upper: float
    lower: float
    price: float
    is_swept: bool = False
    is_touched: bool = False
    is_mitigated: bool = False
    status: HTFViStatus = HTFViStatus.OPEN
    liquidity_type = LiquidityType.INTERNAL
    level_type = LevelType.VI
    mitigation_time: datetime | None = None
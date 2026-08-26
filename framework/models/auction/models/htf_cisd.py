from dataclasses import dataclass
from datetime import datetime
from framework.models.auction.models.enums import HTFCisdStatus, LevelType, LiquidityType

@dataclass(slots=True)
class HTFCISD:
    timeframe: str
    timestamp: datetime
    is_bullish: bool
    is_buy_side: bool
    
    upper: float
    lower: float
    upper_wick: float
    lower_wick: float
    price: float

    is_swept: bool = False
    is_touched: bool = False
    is_mitigated: bool = False
    status: HTFCisdStatus = HTFCisdStatus.OPEN
    liquidity_type = LiquidityType.INTERNAL
    level_type = LevelType.CISD
    mitigation_time: datetime | None = None
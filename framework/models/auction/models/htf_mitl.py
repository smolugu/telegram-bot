from dataclasses import dataclass
from datetime import datetime

from framework.models.auction.models.enums import HTFMitlStatus, LevelType, LiquidityType


@dataclass(slots=True)
class HTFMITL:
    timeframe: str
    timestamp: datetime
    confirmation_time: datetime
    price: float
    is_bullish: bool
    is_buy_side: bool

    is_swept: bool = False
    is_touched: bool = False
    is_mitigated: bool = False
    status: HTFMitlStatus = HTFMitlStatus.OPEN
    liquidity_type = LiquidityType.EXTERNAL
    level_type = LevelType.MITL
    mitigation_time: datetime | None = None
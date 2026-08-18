from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

from framework.models.auction.models.enums import HTFSwingStatus, LevelType, LiquidityType, SwingType




@dataclass
class HTFSwing:
    timeframe: str              # WEEKLY, DAILY, H7
    swing_type: SwingType       # BUY_SIDE = swing high
                                # SELL_SIDE = swing low

    price: float
    index: int

    timestamp: datetime
    is_swept: bool = False
    is_bullish: bool = False
    status: HTFSwingStatus = HTFSwingStatus.OPEN
    liquidity_type: LiquidityType = LiquidityType.EXTERNAL
    level_type: LevelType = LevelType.SWING
    mitigated_index: Optional[int] = None

    mitigation_time: Optional[datetime] = None
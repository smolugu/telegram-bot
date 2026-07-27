from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from data.models.auction.models.base_model import HTFSwingStatus

# from data.models.auction.models.base_model import HTFLevelStatus

# SwingType = Literal["BUY_SIDE", "SELL_SIDE"]
# SwingStatus = Literal["OPEN", "MITIGATED"]

class SwingType(str, Enum):
    BUY_SIDE = "BUY_SIDE"
    SELL_SIDE = "SELL_SIDE"

    @property
    def opposite(self):
        return (
            SwingType.SELL_SIDE
            if self == SwingType.BUY_SIDE
            else SwingType.BUY_SIDE
        )

@dataclass
class HTFSwing:
    timeframe: str              # WEEKLY, DAILY, H7

    swing_type: SwingType       # BUY_SIDE = swing high
                                # SELL_SIDE = swing low

    price: float

    index: int

    timestamp: datetime

    status: HTFSwingStatus = "OPEN"

    mitigated_index: Optional[int] = None

    mitigated_time: Optional[datetime] = None
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

SwingType = Literal["BUY_SIDE", "SELL_SIDE"]
SwingStatus = Literal["OPEN", "MITIGATED"]


@dataclass
class HTFSwing:
    timeframe: str              # WEEKLY, DAILY, H7

    swing_type: SwingType       # BUY_SIDE = swing high
                                # SELL_SIDE = swing low

    price: float

    index: int

    timestamp: datetime

    status: SwingStatus = "OPEN"

    mitigated_index: Optional[int] = None

    mitigated_time: Optional[datetime] = None
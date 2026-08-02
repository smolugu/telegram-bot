from dataclasses import dataclass
from datetime import datetime

from framework.models.auction.models.base_model import FVGStatus

# @dataclass
# class HTFFVG(HTFLevel):
#     top: float
#     bottom: float
#     bullish: bool

@dataclass(slots=True)
class HTFFVG:
    timeframe: str
    timestamp: datetime
    is_bullish: bool

    upper: float
    lower: float

    status: FVGStatus = FVGStatus.OPEN
    mitigation_time: datetime | None = None
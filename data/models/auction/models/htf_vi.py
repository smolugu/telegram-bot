from dataclasses import dataclass
from datetime import datetime

from data.models.auction.models.base_model import VIStatus


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

    upper: float
    lower: float

    status: VIStatus = VIStatus.OPEN
    mitigation_time: datetime | None = None
from dataclasses import dataclass
from datetime import datetime
from data.models.auction.models.base_model import CISDStatus, HTFLevel

# @dataclass
# class HTFCISD(HTFLevel):
#     price: float
#     bullish: bool

@dataclass(slots=True)
class HTFCISD:
    timeframe: str
    timestamp: datetime
    is_bullish: bool

    upper_body: float
    lower_body: float
    upper_wick: float
    lower_wick: float

    status: CISDStatus = CISDStatus.OPEN
    mitigation_time: datetime | None = None
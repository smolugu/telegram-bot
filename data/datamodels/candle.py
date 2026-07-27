from dataclasses import dataclass
from datetime import datetime

@dataclass(slots=True)
class Candle:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


#     @dataclass(slots=True)
# class Candle:
#     timestamp: datetime      # America/New_York
#     open: float
#     high: float
#     low: float
#     close: float
#     volume: int
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

NY_TZ = ZoneInfo("America/New_York")

@dataclass(slots=True, frozen=True)
class Candle:
    instrument: str
    timeframe: int
    timestamp: datetime
    contract: str
    open: float
    high: float
    low: float
    close: float
    volume: int

    @property
    def timestamp_ny(self) -> datetime:
        return self.timestamp.astimezone(NY_TZ)
    @property
    def hour_ny(self) -> int:
        return self.timestamp_ny.hour

    @property
    def minute_ny(self) -> int:
        return self.timestamp_ny.minute

    @property
    def date_ny(self):
        return self.timestamp_ny.date()

    @property
    def weekday_ny(self) -> int:
        return self.timestamp_ny.weekday()


#     @dataclass(slots=True)
# class Candle:
#     timestamp: datetime      # America/New_York
#     open: float
#     high: float
#     low: float
#     close: float
#     volume: int
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo


NY_TZ = ZoneInfo("America/New_York")


@dataclass(slots=True, frozen=True)
class Trade:
    instrument: str
    contract: str
    timestamp: datetime
    price: float
    volume: int
    side: int

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
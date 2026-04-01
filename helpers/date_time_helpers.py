from datetime import datetime
from zoneinfo import ZoneInfo


def to_ny_datetime(ts):
    tz = ZoneInfo("America/New_York")

    if isinstance(ts, str):
        return datetime.fromisoformat(ts).astimezone(tz)
    return ts.astimezone(tz)
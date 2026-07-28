from datetime import datetime, UTC
from zoneinfo import ZoneInfo

# ts_ns = time stamp in nanoseconds (example: ts_ns = 1784156400000000000)
def unix_to_est_timestamp(ts_ns):
    dt_utc = datetime.fromtimestamp(ts_ns / 1_000_000_000, tz=UTC)
    dt_est = dt_utc.astimezone(ZoneInfo("America/New_York"))
    return dt_est
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

def get_cme_session_date(timestamp):
    dt = datetime.fromisoformat(timestamp)
    if dt.hour >= 18:
        return dt.date()
    return (dt-timedelta(days=1)).date()

def build_session_ranges(candles_30m):
    sessions = {}

    for c in candles_30m:
        session = get_cme_session_date(c["timestamp"])
        high = c["high"]
        low = c["low"]
        if session not in sessions:
            sessions[session] = {"high": high, "low": low}
        else:
            sessions[session]["high"] = max(sessions[session]["high"], high)
            sessions[session]["low"] = min(sessions[session["low"]], low)
    
    return sessions




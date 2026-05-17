from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

def in_session(ts, start_h, start_m, end_h, end_m):
    tz = ZoneInfo("America/New_York")
    if isinstance(ts, str):
        dt = datetime.fromisoformat(ts).astimezone(tz)
    else:
        dt = ts.astimezone(tz)
    start = time(start_h, start_m)
    end = time(end_h, end_m)
    return start <= dt.time() < end 

def get_max_high_low_with_time(candles):

    high_candle = max(candles, key=lambda c: c["high"])
    low_candle = min(candles, key=lambda c: c["low"])

    return {
        "high": high_candle["high"],
        "high_ts": high_candle["timestamp"],
        "low": low_candle["low"],
        "low_ts": low_candle["timestamp"]
    }

def get_futures_session(candles, test_date):

    test_dt = datetime.strptime(test_date, "%Y-%m-%d")

    session_start = test_dt - timedelta(hours=6)
    session_end = test_dt + timedelta(hours=16)
    filtered = []
    # print("candles all: ", candles)

    for c in candles:
        ts = datetime.fromisoformat(c["timestamp"]).replace(tzinfo=None)
        # print("ts before: ", ts)
        if session_start <= ts <= session_end:
            # print("ts session: ", ts)
            filtered.append(c)

    print("start, end: ", session_start, session_end)

    return filtered





def get_session_high_low(
    candles,
    start_hr,
    start_min,
    end_hr,
    end_min,
    current_start,
    name=None
):

    tz = ZoneInfo("America/New_York")

    # last_closed_dt = datetime.fromisoformat(last_closed_candle_ts).astimezone(tz)
    last_closed_dt = datetime.fromisoformat(current_start).astimezone(tz)
    

    # -------------------------
    # Determine session date
    # -------------------------
    if name == "Asia":
        session_date = last_closed_dt.date() - timedelta(days=1)
    else:
        session_date = last_closed_dt.date()
    
    # Detect cross-midnight session
    cross_midnight = (end_hr, end_min) <= (start_hr, start_min)
    if cross_midnight:
        session_start = datetime.combine(
            last_closed_dt.date() - timedelta(days=1),
            time(start_hr, start_min),
            tz
        )
        session_end = datetime.combine(
            last_closed_dt.date(),
            time(end_hr, end_min),
            tz
        )
    else:
        session_start = datetime.combine(
            last_closed_dt.date(),
            time(start_hr, start_min),
            tz
        )
        session_end = datetime.combine(
            last_closed_dt.date(),
            time(end_hr, end_min),
            tz
        )

    # -------------------------
    # KEY FIX: Only proceed AFTER session ends
    # -------------------------
    if last_closed_dt < session_end:
        return {
            "high": None,
            "high_ts": None,
            "low": None,
            "low_ts": None
        }

    # -------------------------
    # Collect session candles
    # -------------------------
    session = []

    for c in candles:
        dt = datetime.fromisoformat(c["timestamp"]).astimezone(tz)

        if session_start <= dt < session_end:
            session.append(c)

    if not session:
        return {
            "high": None,
            "high_ts": None,
            "low": None,
            "low_ts": None
        }

    # -------------------------
    # Get high + timestamp
    # -------------------------
    high_candle = max(session, key=lambda c: c["high"])
    low_candle = min(session, key=lambda c: c["low"])

    return {
        "high": high_candle["high"],
        "high_ts": high_candle["timestamp"],
        "low": low_candle["low"],
        "low_ts": low_candle["timestamp"]
    }
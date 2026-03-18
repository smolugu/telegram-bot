from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo


def get_futures_session(candles, test_date):

    test_dt = datetime.strptime(test_date, "%Y-%m-%d")

    session_start = test_dt - timedelta(hours=6)
    session_end = test_dt + timedelta(hours=16)
    filtered = []

    for c in candles:
        ts = datetime.fromisoformat(c["timestamp"]).replace(tzinfo=None)
        if session_start <= ts <= session_end:
            filtered.append(c)

    print("start, end: ", session_start, session_end)

    return filtered


def get_session_high_low(candles, start_hr, start_min, end_hr, end_min, last_closed_candle_ts, name=None):

    # Always work in NY time (CME reference)
    tz = ZoneInfo("America/New_York")

    last_closed_dt = datetime.fromisoformat(last_closed_candle_ts).astimezone(tz)
    # print("last_closed_hour:", last_closed_dt.hour)

    # Asia session must be completed (ends at 00:00)
    if last_closed_dt.hour < 0:  # effectively always false, but keeping structure clear
        return None, None

    # Do not use after reset (post 16:00)
    if last_closed_dt.hour >= 16:
        return None, None

    # Determine session date (Asia belongs to previous day evening)
    if name == "Asia":
        session_date = last_closed_dt.date() - timedelta(days=1)
    else:
        session_date = last_closed_dt.date()

    session_start = datetime.combine(session_date, time(start_hr, start_min), tz)
    session_end   = datetime.combine(last_closed_dt.date(), time(end_hr, end_min), tz)
    print("session_start: ", session_start)
    print("session_end: ", session_end)

    session = []

    for c in candles:

        dt = datetime.fromisoformat(c["timestamp"]).astimezone(tz)

        # Proper time window check
        if session_start <= dt < session_end:
            print("appending:", c["timestamp"], c["high"], c["low"])
            session.append(c)

    if not session:
        return None, None

    high = max(c["high"] for c in session)
    low = min(c["low"] for c in session)

    return high, low


# def session_high_low(candles, start_hour, end_hour, last_closed_candle_ts):

#     session = []
#     last_closed_dt = datetime.fromisoformat(last_closed_candle_ts)
#     hour_last_closed = last_closed_dt.hour
#     if hour_last_closed < end_hour:
#         return None, None
#     # do not return session highs and lows after 18:00 reset
#     if hour_last_closed >= 16:
#         return None, None
#     for c in candles:

#         dt = datetime.fromisoformat(c["timestamp"])
#         hour = dt.hour

#         if start_hour <= hour < end_hour:
#             session.append(c)

#     if not session:
#         return None, None

#     high = max(c["high"] for c in session)
#     low = min(c["low"] for c in session)

#     return high, low

# def session_high_low_london(candles, start_hour, end_hour, last_closed_candle_ts):

#     session = []
#     last_closed_dt = datetime.fromisoformat(last_closed_candle_ts)
#     hour_last_closed = last_closed_dt.hour
#     # print("last_closed_candle_ts: ", last_closed_candle_ts)
#     # print("last_closed_dt: ", last_closed_dt)
#     # print("start_hour: ", start_hour)
#     # print("end_hour: ", end_hour)
#     # print("hour_last_closed: ", hour_last_closed)
#     if hour_last_closed < end_hour:
#         print("returning none error")
#         return None, None
#     # do not return session highs and lows after 18:00 reset
#     if hour_last_closed >= 16:
#         print("returning none error 16")
#         return None, None
    
#     for c in candles:

#         dt = datetime.fromisoformat(c["timestamp"])
#         hour = dt.hour

#         if start_hour <= hour < end_hour:
#             session.append(c)

#     if not session:
#         print("not session error")
#         return None, None

#     high = max(c["high"] for c in session)
#     low = min(c["low"] for c in session)
#     print("london high low: ", high, low)

#     return high, low
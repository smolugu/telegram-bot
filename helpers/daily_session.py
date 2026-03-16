from datetime import datetime, timedelta

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



# def get_pdh_pdl(current_timestamp, sessions):

#     session = get_cme_session_date(current_timestamp)

#     prev_session = sorted(sessions.keys())

#     idx = prev_session.index(session)

#     if idx == 0:
#         return None, None

#     prev_day = prev_session[idx - 1]

#     pdh = sessions[prev_day]["high"]
#     pdl = sessions[prev_day]["low"]

#     return pdh, pdl



def get_pdh_pdl(candles, test_date):

    test_dt = datetime.strptime(test_date, "%Y-%m-%d")

    prev_session_start = test_dt - timedelta(days=1, hours=6)   # previous day 18:00
    prev_session_end = test_dt - timedelta(hours=8)             # test_date-1 16:00

    pdh = float("-inf")
    pdl = float("inf")

    for c in candles:

        ts = datetime.fromisoformat(c["timestamp"]).replace(tzinfo=None)

        if prev_session_start <= ts <= prev_session_end:

            if c["high"] > pdh:
                pdh = c["high"]

            if c["low"] < pdl:
                pdl = c["low"]

    return pdh, pdl
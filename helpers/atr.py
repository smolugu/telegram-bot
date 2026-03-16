from datetime import datetime, timedelta

def calculate_atr(candles, period=14):

    if len(candles) < period + 1:
        return None

    trs = []

    for i in range(1, len(candles)):

        high = candles[i]["high"]
        low = candles[i]["low"]
        prev_close = candles[i-1]["close"]

        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )

        trs.append(tr)

    atr = sum(trs[-period:]) / period

    return atr


# ---------------------------
# if 10:30 range > ATR
# → high probability trend day

def calculate_daily_atr(candles, period=5):

    sessions = {}

    # -------- group candles into futures sessions --------
    for c in candles:

        ts = datetime.fromisoformat(c["timestamp"])

        # skip Saturday completely
        if ts.weekday() == 5:
            continue

        # Sunday before 18:00 is still closed
        if ts.weekday() == 6 and ts.hour < 18:
            continue

        # futures session assignment
        if ts.hour >= 18:
            session_date = (ts + timedelta(days=1)).date()
        else:
            session_date = ts.date()

        if session_date not in sessions:
            sessions[session_date] = {
                "high": float("-inf"),
                "low": float("inf"),
                "close": None
            }

        sessions[session_date]["high"] = max(
            sessions[session_date]["high"], c["high"]
        )

        sessions[session_date]["low"] = min(
            sessions[session_date]["low"], c["low"]
        )

        sessions[session_date]["close"] = c["close"]

    # -------- sort sessions --------
    ordered_sessions = sorted(sessions.items())

    trs = []
    prev_close = None

    for date, data in ordered_sessions:

        high = data["high"]
        low = data["low"]
        close = data["close"]

        if prev_close is None:
            tr = high - low
        else:
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )

        trs.append(tr)

        prev_close = close

    # -------- ATR --------
    atr = sum(trs[-period:]) / min(period, len(trs))

    return atr
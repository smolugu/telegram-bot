from datetime import timedelta

from data.models.candle import Candle



def calculate_atr(daily_candles: list[Candle]) -> float:
    if len(daily_candles) < 5:
        raise ValueError("At least 5 daily candles are required")

    last_5 = daily_candles[-5:]

    ranges = [
        candle.high - candle.low
        for candle in last_5
    ]

    return sum(ranges) / len(ranges)

def calculate_daily_atr(candles, period=5):

    sessions = {}

    # -------- group candles into futures sessions --------
    for c in candles:

        ts = c.timestamp

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
            sessions[session_date]["high"], c.high
        )

        sessions[session_date]["low"] = min(
            sessions[session_date]["low"], c.low
        )

        sessions[session_date]["close"] = c.close

    # -------- sort sessions --------
    ordered_sessions = sorted(sessions.items())

    # -------- use last `period` sessions --------
    ordered_sessions = ordered_sessions[-period:]

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
    atr = sum(trs) / min(period, len(trs))

    return atr
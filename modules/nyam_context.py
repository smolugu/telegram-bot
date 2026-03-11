from datetime import datetime


from datetime import datetime

def get_1am_7h_bias(candles_1h):

    session = []

    for c in candles_1h:

        dt = datetime.fromisoformat(c["timestamp"])

        if 1 <= dt.hour < 8:
            session.append(c)

    if len(session) < 7:
        return None

    open_price = session[0]["open"]
    close_price = session[-1]["close"]

    high_price = max(c["high"] for c in session)
    low_price = min(c["low"] for c in session)

    body = abs(close_price - open_price)

    upper_wick = high_price - max(open_price, close_price)
    lower_wick = min(open_price, close_price) - low_price

    # Require body dominance
    if body <= upper_wick or body <= lower_wick:
        return "neutral"

    if close_price > open_price:
        return "bullish"

    if close_price < open_price:
        return "bearish"

    return "neutral"

def get_morning_context(candles_1h, candles_30m):

    bias_1am = None
    ib_high = None
    ib_low = None
    swing_high_9am = None
    swing_low_9am = None

    # -------------------------
    # 1️⃣ 1AM 7H Candle Bias
    # -------------------------

    bias_1am_7hr_candle = get_1am_7h_bias(candles_1h)
    
    # -------------------------
    # 2️⃣ 8AM Initial Balance
    # -------------------------
    for c in candles_1h:

        dt = datetime.fromisoformat(c["timestamp"])

        if dt.hour == 8:

            ib_high = c["high"]
            ib_low = c["low"]
            break

    # -------------------------
    # 3️⃣ 30m swings by 9:00
    # -------------------------
    swings = []

    for i in range(1, len(candles_30m) - 1):

        c1 = candles_30m[i - 1]
        c2 = candles_30m[i]
        c3 = candles_30m[i + 1]

        dt = datetime.fromisoformat(c2["timestamp"])

        if dt.hour > 9:
            break

        if c2["high"] > c1["high"] and c2["high"] > c3["high"]:
            swings.append(("high", c2["high"]))

        if c2["low"] < c1["low"] and c2["low"] < c3["low"]:
            swings.append(("low", c2["low"]))

    highs = [s[1] for s in swings if s[0] == "high"]
    lows = [s[1] for s in swings if s[0] == "low"]

    if highs:
        swing_high_9am = max(highs)

    if lows:
        swing_low_9am = min(lows)

    return {
        "bias_1am": bias_1am_7hr_candle,
        "ib_high": ib_high,
        "ib_low": ib_low,
        "swing_high_9am": swing_high_9am,
        "swing_low_9am": swing_low_9am
    }
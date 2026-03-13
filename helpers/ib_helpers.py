# IB Model - ideal sequence
# IB level
# ↓
# 3m compression near IB
# ↓
# strong displacement
# ↓
# retest IB
# ↓
# 3m imbalance entry

# example
# 8:00 IB formed
# 9:30 open
# 9:33–9:45 compression near IB
# 9:48 breakout
# 9:55 retest IB
# 10:00 entry


# compression = detect_ib_compression(recent_3m_candles, ib_high, atr)

# if compression and detect_ib_displacement(candle, ib_high, ib_low, atr):

#     ib_candidate.active = True

def is_liquidity_raid(candle, ib_high, ib_low, atr):

    open_ = candle["open"]
    close = candle["close"]
    high = candle["high"]
    low = candle["low"]

    rng = high - low
    body = abs(close - open_)

    if rng == 0:
        return True

    # bullish raid
    if high > ib_high and close <= ib_high:
        return True

    if close > ib_high:

        if (close - ib_high) < atr * 0.1:
            return True

        if body / rng < 0.4:
            return True

    # bearish raid
    if low < ib_low and close >= ib_low:
        return True

    if close < ib_low:

        if (ib_low - close) < atr * 0.1:
            return True

        if body / rng < 0.4:
            return True

    return False


# candles (recent_3m)  = candles_3m[-5:]
def detect_ib_compression(candles, ib_level, atr):

    if len(candles) < 4:
        return False

    recent = candles[-4:]

    highs = [c["high"] for c in recent]
    lows = [c["low"] for c in recent]

    compression_range = max(highs) - min(lows)

    # range must be small
    if compression_range > atr * 0.2:
        return False

    # price must stay close to IB
    distance = abs(max(highs) - ib_level)

    if distance > atr * 0.15:
        return False

    return True
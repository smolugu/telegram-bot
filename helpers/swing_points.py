# -------------------------------------------------------
# Swing helpers
# -------------------------------------------------------

def find_swing_highs(candles):
    swings = []
    # print("Last 30m candle timestamp:",
    #   candles[-1]["timestamp"])

    for i in range(1, len(candles) - 1):
        if (
            candles[i]["high"] > candles[i - 1]["high"]
            and candles[i]["high"] > candles[i + 1]["high"]
        ):
            swings.append(candles[i])
    # for s in swings:
    #     print(s["timestamp"], s["high"])
    return swings


def find_swing_lows(candles):
    swings = []

    for i in range(1, len(candles) - 1):
        if (
            candles[i]["low"] < candles[i - 1]["low"]
            and candles[i]["low"] < candles[i + 1]["low"]
        ):
            swings.append(candles[i])
    # for s in swings:
    #     print(s["timestamp"], s["low"])
    return swings


# ---------------------
# valid swing points
# ---------------------

def filter_valid_swing_lows(swings):

    valid = []

    for swing in swings:

        swing_low = swing["low"]

        # Remove previous lows that are higher than the current swing
        valid = [v for v in valid if v["low"] < swing_low]

        # Add the current swing
        valid.append(swing)

    return valid

def filter_valid_swing_highs(swings):

    valid = []

    for swing in swings:

        swing_high = swing["high"]

        # Remove previous highs that are lower than the current swing
        valid = [v for v in valid if v["high"] > swing_high]

        # Add the current swing
        valid.append(swing)

    return valid


def get_valid_swings(historical_candles):

    swing_lows = find_swing_lows(historical_candles)
    swing_highs = find_swing_highs(historical_candles)
    valid_swing_lows = filter_valid_swing_lows(swing_lows)
    valid_swing_highs = filter_valid_swing_highs(swing_highs)
    
    return valid_swing_lows, valid_swing_highs


def debug_print_30m_swings(nq_30m, test_date):

    # Filter only that day
    day_30m = [c for c in nq_30m if test_date in c["timestamp"]]

    swings_high = find_swing_highs(day_30m)
    swings_low = find_swing_lows(day_30m)

    print("\n--- 30M SWING HIGHS ---")
    for s in swings_high:
        print(s["timestamp"], s["high"])

    print("\n--- 30M SWING LOWS ---")
    for s in swings_low:
        print(s["timestamp"], s["low"])
    #  print only relevant swings for the day
    print("\n--- FILTERED PROGRESSIVE SWING HIGHS ---")
    progressive_highs = filter_valid_swing_highs(swings_high)
    
    for s in progressive_highs:
        print(s["timestamp"], s["high"])
    progressive_lows = filter_valid_swing_lows(swings_low)
    print("\n--- FILTERED PROGRESSIVE SWING LOWS ---")
    for s in progressive_lows:
        print(s["timestamp"], s["low"])


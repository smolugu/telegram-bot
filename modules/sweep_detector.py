# from datetime import datetime
from helpers.time_windows import (
    get_reversal_windows,
    is_in_reversal_window
)

def filter_valid_swing_highs(swings):

    if not swings:
        return []

    valid = []

    for swing in swings:
        # Remove any existing swings lower than this one
        valid = [s for s in valid if s["high"] > swing["high"]]

        valid.append(swing)

    return valid

def filter_valid_swing_lows(swings):

    if not swings:
        return []

    valid = []

    for swing in swings:
        # Remove any existing swings higher than this one
        valid = [s for s in valid if s["low"] < swing["low"]]

        valid.append(swing)

    return valid

def detect_dual_sweep(
    nq_30m,
    nq_3m,
    es_30m,
    current_7h_open_iso,
    wick_window_minutes
):

    windows = get_reversal_windows(
        current_7h_open_iso,
        wick_window_minutes
    )
    print("Last 30m candle timestamp:",
      nq_30m[-1]["timestamp"])
    print("Last 3m candle timestamp:",
      nq_3m[-1]["timestamp"])

    nq_result = detect_swing_sweep(nq_30m, windows)
    # print("NQ sweep result:", nq_result)
    es_result = detect_swing_sweep(es_30m, windows)
    # print("ES sweep result:", es_result)

    return {
        "sweep_exists": nq_result["sweep_detected"] or es_result["sweep_detected"],
        "NQ": nq_result,
        "ES": es_result
    }


# -------------------------------------------------------
# Session-based liquidity levels
# -------------------------------------------------------
def detect_key_liquidity_sweep(last_candle, liquidity, tolerance=0):

    sweep_at_key_level = False
    swept_levels = []

    high = last_candle["high"]
    low = last_candle["low"]
    close = last_candle["close"]
    

    for level_type, level_data in liquidity.items():

        price = level_data["price"]
        swept = level_data["swept"]

        if price is None or swept:
            continue

        # Buy-side liquidity (price above level)
        if level_type.endswith("high") or level_type == "pdh":
            # Check if high touches or exceeds the level (potential sweep) and set swept to True
            if high >= price - tolerance:
                liquidity[level_type]["swept"] = True
            # check for valid sweep (rejection off level)
            if high >= price - tolerance and close < price:

                sweep_at_key_level = True
                liquidity[level_type]["swept"] = True

                swept_levels.append({
                    "level_name": level_type,
                    "price": price,
                    "side": "buy_side",
                    "type": "rejection"
                })
            elif high >= price - tolerance and close >= price:
                # potential sweep but no rejection, still mark as swept
                liquidity[level_type]["swept"] = True
                swept_levels.append({
                    "level_name": level_type,
                    "price": price,
                    "side": "buy_side",
                    "type": "displacement"
                })


        # Sell-side liquidity (price below level)
        elif level_type.endswith("low") or level_type == "pdl":
            # Check if low touches or goes below the level (potential sweep) and set swept to True
            if low <= price + tolerance:
                liquidity[level_type]["swept"] = True
            #  check for valid sweep (rejection off level)
            if low <= price + tolerance and close > price:

                sweep_at_key_level = True
                liquidity[level_type]["swept"] = True

                swept_levels.append({
                    "level_name": level_type,
                    "price": price,
                    "side": "sell_side",
                    "type": "rejection"
                })
            elif low <= price + tolerance and close <= price:
                # potential sweep but no rejection, still mark as swept
                liquidity[level_type]["swept"] = True
                swept_levels.append({
                    "level_name": level_type,
                    "price": price,
                    "side": "sell_side",
                    "type": "displacement"
                })

    return sweep_at_key_level, swept_levels


# -------------------------------------------------------
# Swing-based sweep logic
# -------------------------------------------------------

def detect_swing_sweep(candles, windows):

    if len(candles) < 5:
        return _no_sweep()

    raw_swings_high = find_swing_highs(candles[:-1])
    raw_swings_low = find_swing_lows(candles[:-1])
    valid_swings_high = filter_valid_swing_highs(raw_swings_high)
    valid_swings_low = filter_valid_swing_lows(raw_swings_low)
    print(f"Raw swings high: {raw_swings_high}")
    print(f"Raw swings low: {raw_swings_low}")
    print(f"Valid swings high: {valid_swings_high}")
    print(f"Valid swings low: {valid_swings_low}")

    # Last closed 30m candle (just completed)
    last_closed = candles[-1]

    valid, window_name = is_in_reversal_window(
        last_closed["timestamp"],
        windows
    )
    print(f"valid: {valid}, window_name: {window_name} for timestamp {last_closed['timestamp']} in windows {windows}")
    if not valid:
        return _no_sweep()
    
    # -------------------------
    # Bearish sweep (buy-side taken)
    # -------------------------
    # print(f"Valid swings high: {valid_swings_high}")
    if not valid_swings_high:
        return _no_sweep()

    # -----------------------------------------
    # 3️⃣ Check if last_closed swept ≥ 1
    # -----------------------------------------
    swept_levels = []

    for swing in valid_swings_high:
        print(f"Comparing last closed high {last_closed['high']} with swing high {swing['high']}")
        if last_closed["high"] > swing["high"]:
            swept_levels.append(swing)
    print(f"Swept levels: {swept_levels}")
    # print("---------------------------")
    if swept_levels:
        print("Swept highs:", swept_levels)
        return {
            "sweep_detected": True,
            "side": "buy_side",   # buy-side liquidity taken
            "timestamp": last_closed["timestamp"],
            "window": window_name,
            "swept_levels": swept_levels
        }

    # -------------------------
    # Bullish sweep (sell-side taken)
    # -------------------------
    # print(f"Valid swings low: {valid_swings_low}")
    
    if not valid_swings_low:
        return _no_sweep()
    swept_levels_low = []
    for swing in valid_swings_low:
        if last_closed["low"] < swing["low"]:
            swept_levels_low.append(swing)

    if swept_levels_low:
        # print("Swept lows:", swept_levels_low)
        return {
            "sweep_detected": True,
            "side": "sell_side",
            "timestamp": last_closed["timestamp"],
            "window": window_name,
            "swept_levels": swept_levels_low
        }

    return _no_sweep()


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


def _no_sweep():
    return {
        "sweep_detected": False,
        "side": None,
        "timestamp": None,
        "window": None
    }

# from datetime import datetime
from helpers.time_windows import (
    get_reversal_windows,
    is_in_reversal_window
)


def detect_dual_sweep(
    nq_30m,
    es_30m,
    current_7h_open_iso,
    wick_window_minutes
):

    windows = get_reversal_windows(
        current_7h_open_iso,
        wick_window_minutes
    )

    nq_result = detect_swing_sweep(nq_30m, windows)
    es_result = detect_swing_sweep(es_30m, windows)

    return {
        "sweep_exists": nq_result["sweep_detected"] or es_result["sweep_detected"],
        "NQ": nq_result,
        "ES": es_result
    }


# -------------------------------------------------------
# Swing-based sweep logic
# -------------------------------------------------------

def detect_swing_sweep(candles, windows):

    if len(candles) < 5:
        return _no_sweep()

    swings_high = find_swing_highs(candles[:-1])
    swings_low = find_swing_lows(candles[:-1])

    current = candles[-1]

    valid, window_name = is_in_reversal_window(
        current["timestamp"],
        windows
    )

    if not valid:
        return _no_sweep()

    # -------------------------
    # Bearish sweep (buy-side taken)
    # -------------------------
    if swings_high:
        last_high = swings_high[-1]

        if current["high"] > last_high["high"]:
            return {
                "sweep_detected": True,
                "side": "buy_side",
                "timestamp": current["timestamp"],
                "window": window_name
            }

    # -------------------------
    # Bullish sweep (sell-side taken)
    # -------------------------
    if swings_low:
        last_low = swings_low[-1]

        if current["low"] < last_low["low"]:
            return {
                "sweep_detected": True,
                "side": "sell_side",
                "timestamp": current["timestamp"],
                "window": window_name
            }

    return _no_sweep()


# -------------------------------------------------------
# Swing helpers
# -------------------------------------------------------

def find_swing_highs(candles):
    swings = []

    for i in range(1, len(candles) - 1):
        if (
            candles[i]["high"] > candles[i - 1]["high"]
            and candles[i]["high"] > candles[i + 1]["high"]
        ):
            swings.append(candles[i])

    return swings


def find_swing_lows(candles):
    swings = []

    for i in range(1, len(candles) - 1):
        if (
            candles[i]["low"] < candles[i - 1]["low"]
            and candles[i]["low"] < candles[i + 1]["low"]
        ):
            swings.append(candles[i])

    return swings


def _no_sweep():
    return {
        "sweep_detected": False,
        "side": None,
        "timestamp": None,
        "window": None
    }

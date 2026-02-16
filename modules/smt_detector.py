from helpers.time_windows import (
    get_reversal_windows,
    is_in_reversal_window
)

def detect_smt_dual(
    nq_30m,
    es_30m,
    nq_1h,
    es_1h,
    current_7h_open_iso,
    wick_window_minutes
):
    print("SMT module called")
    windows = get_reversal_windows(
        current_7h_open_iso,
        wick_window_minutes
    )

    result = _check_tf(nq_30m, es_30m, windows, "30m")
    if result["smt_confirmed"]:
        return result

    result = _check_tf(nq_1h, es_1h, windows, "1h")
    return result


def _check_tf(nq, es, windows, tf_name):

    nq_highs = _find_swing_highs(nq)
    nq_lows = _find_swing_lows(nq)
    es_highs = _find_swing_highs(es)
    es_lows = _find_swing_lows(es)
    # print("Swing High Count NQ:", len(nq_highs))
    # print("Swing High Count ES:", len(es_highs))


    # -------- Bearish SMT (High divergence) --------
    for nq_h in nq_highs:
        valid, window_name = is_in_reversal_window(
            nq_h["timestamp"],
            windows
        )
        if not valid:
            continue

        for es_h in es_highs:

            if nq_h["high"] > es_h["high"]:
                # print("Bearish SMT FOUND at", nq_h["timestamp"])
                return {
                    "smt_confirmed": True,
                    "type": "bearish",
                    "sweeper": "NQ",
                    "trade_symbol": "NQ",
                    "trade_direction": "SHORT",
                    "tf": tf_name,
                    "window": window_name,
                    "timestamp": nq_h["timestamp"]
                }

            if es_h["high"] > nq_h["high"]:
                return {
                    "smt_confirmed": True,
                    "type": "bearish",
                    "sweeper": "ES",
                    "trade_symbol": "ES",
                    "trade_direction": "SHORT",
                    "tf": tf_name,
                    "window": window_name,
                    "timestamp": nq_h["timestamp"]
                }

    # -------- Bullish SMT (Low divergence) --------
    for nq_l in nq_lows:
        valid, window_name = is_in_reversal_window(
            nq_l["timestamp"],
            windows
        )
        if not valid:
            continue

        for es_l in es_lows:

            if nq_l["low"] < es_l["low"]:
                return {
                    "smt_confirmed": True,
                    "type": "bullish",
                    "sweeper": "NQ",
                    "trade_symbol": "ES",
                    "trade_direction": "LONG",
                    "tf": tf_name,
                    "window": window_name,
                    "timestamp": nq_l["timestamp"]
                }

            if es_l["low"] < nq_l["low"]:
                return {
                    "smt_confirmed": True,
                    "type": "bullish",
                    "sweeper": "ES",
                    "trade_symbol": "NQ",
                    "trade_direction": "LONG",
                    "tf": tf_name,
                    "window": window_name,
                    "timestamp": nq_l["timestamp"]
                }

    return {"smt_confirmed": False}


def _find_swing_highs(candles):
    swings = []
    for i in range(1, len(candles) - 1):
        if candles[i]["high"] > candles[i-1]["high"] and candles[i]["high"] > candles[i+1]["high"]:
            swings.append(candles[i])
    return swings


def _find_swing_lows(candles):
    swings = []
    for i in range(1, len(candles) - 1):
        if candles[i]["low"] < candles[i-1]["low"] and candles[i]["low"] < candles[i+1]["low"]:
            swings.append(candles[i])
    return swings

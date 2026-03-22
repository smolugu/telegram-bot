from helpers.time_windows import (
    get_reversal_windows,
    is_in_reversal_window
)

from datetime import datetime, timedelta

def detect_smt_key_levels(nq_swept, es_swept):

    nq_swept = nq_swept or []
    es_swept = es_swept or []

    # Convert to dict for fast lookup
    nq_map = {lvl["level_name"]: lvl for lvl in nq_swept}
    es_map = {lvl["level_name"]: lvl for lvl in es_swept}

    all_levels = set(nq_map.keys()) | set(es_map.keys())

    results = []

    for level in all_levels:

        nq_lvl = nq_map.get(level)
        es_lvl = es_map.get(level)

        # -------------------------
        # Only NQ swept this level
        # -------------------------
        if nq_lvl and not es_lvl:

            if nq_lvl["side"] == "sell_side":
                results.append({
                    "type": "bullish_smt",
                    "sweeper": "nq",
                    "level": level,
                    "details": nq_lvl
                })

            elif nq_lvl["side"] == "buy_side":
                results.append({
                    "type": "bearish_smt",
                    "sweeper": "nq",
                    "level": level,
                    "details": nq_lvl
                })

        # -------------------------
        # Only ES swept this level
        # -------------------------
        elif es_lvl and not nq_lvl:

            if es_lvl["side"] == "sell_side":
                results.append({
                    "type": "bullish_smt",
                    "sweeper": "es",
                    "level": level,
                    "details": es_lvl
                })

            elif es_lvl["side"] == "buy_side":
                results.append({
                    "type": "bearish_smt",
                    "sweeper": "es",
                    "level": level,
                    "details": es_lvl
                })

        # -------------------------
        # Both swept → NO SMT
        # -------------------------
        else:
            continue

    return results if results else None


def detect_30m_swing_smt(
    nq_swings_high,
    nq_swings_low,
    es_swings_high,
    es_swings_low,
    current_nq_candle,
    current_es_candle,
    time_tolerance=timedelta(minutes=5)
):

    def find_matching_swing(target_ts, swings):
        for s in swings:
            dt_target = datetime.fromisoformat(target_ts)
            dt = datetime.fromisoformat(s["timestamp"])
            # if abs(s["timestamp"] - target_ts) <= time_tolerance:
            if dt_target.hour == dt.hour and dt_target.minute == dt.minute:
                return s
        return None

    # -------------------------
    # Bullish SMT (lows)
    # -------------------------
    for nq_swing in nq_swings_low:

        es_swing = find_matching_swing(nq_swing["timestamp"], es_swings_low)
        if es_swing is None:
            continue

        nq_swept = current_nq_candle["low"] < nq_swing["low"]
        es_swept = current_es_candle["low"] < es_swing["low"]

        # XOR condition → only one sweeps
        if nq_swept != es_swept:

            return {
                "type": "bullish_smt",
                "sweeper": "nq" if nq_swept else "es",
                "nq_swing": nq_swing,
                "es_swing": es_swing
            }

    # -------------------------
    # Bearish SMT (highs)
    # -------------------------
    for nq_swing in nq_swings_high:

        es_swing = find_matching_swing(nq_swing["timestamp"], es_swings_high)
        if es_swing is None:
            continue

        nq_swept = current_nq_candle["high"] > nq_swing["high"]
        es_swept = current_es_candle["high"] > es_swing["high"]

        if nq_swept != es_swept:

            return {
                "type": "bearish_smt",
                "sweeper": "nq" if nq_swept else "es",
                "nq_swing": nq_swing,
                "es_swing": es_swing
            }

    return None

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

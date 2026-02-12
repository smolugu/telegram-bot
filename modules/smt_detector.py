# Important Note (Next Refinement Needed)
# This version:
# Compares last swing highs/lows
# Does NOT yet restrict strictly to wick window timestamps
# Does NOT check invalidation
# We should tighten that next.

from datetime import datetime, timedelta


def detect_smt_dual(
    nq_30m,
    es_30m,
    nq_1h,
    es_1h,
    seven_hour_open_ts: str,
    wick_window_minutes: int
):

    seven_open = datetime.fromisoformat(seven_hour_open_ts)
    prev_close = seven_open
    prev_wick_start = prev_close - timedelta(minutes=wick_window_minutes)
    curr_wick_end = seven_open + timedelta(minutes=wick_window_minutes)

    # Check 30m first
    result = _check_tf(
        nq_30m,
        es_30m,
        prev_wick_start,
        prev_close,
        seven_open,
        curr_wick_end,
        "30m"
    )

    if result["smt_confirmed"]:
        return result

    # Then 1H
    result = _check_tf(
        nq_1h,
        es_1h,
        prev_wick_start,
        prev_close,
        seven_open,
        curr_wick_end,
        "1h"
    )

    return result


def _check_tf(nq, es, prev_wick_start, prev_close, curr_open, curr_wick_end, tf_name):

    nq_swings_high = _find_swing_highs(nq)
    nq_swings_low = _find_swing_lows(nq)

    es_swings_high = _find_swing_highs(es)
    es_swings_low = _find_swing_lows(es)

    # Bearish SMT (high sweep divergence)
    for nq_h in nq_swings_high:
        ts = datetime.fromisoformat(nq_h["timestamp"])
        if not _in_wick(ts, prev_wick_start, prev_close, curr_open, curr_wick_end):
            continue

        for es_h in es_swings_high:
            if nq_h["high"] > es_h["high"]:
                return {
                    "smt_confirmed": True,
                    "type": "bearish",
                    "sweeper": "NQ",
                    "trade_symbol": "NQ",
                    "trade_direction": "SHORT",
                    "tf": tf_name,
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
                    "timestamp": nq_h["timestamp"]
                }

    # Bullish SMT (low sweep divergence)
    for nq_l in nq_swings_low:
        ts = datetime.fromisoformat(nq_l["timestamp"])
        if not _in_wick(ts, prev_wick_start, prev_close, curr_open, curr_wick_end):
            continue

        for es_l in es_swings_low:
            if nq_l["low"] < es_l["low"]:
                return {
                    "smt_confirmed": True,
                    "type": "bullish",
                    "sweeper": "NQ",
                    "trade_symbol": "ES",
                    "trade_direction": "LONG",
                    "tf": tf_name,
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
                    "timestamp": nq_l["timestamp"]
                }

    return {
        "smt_confirmed": False
    }


def _in_wick(ts, prev_wick_start, prev_close, curr_open, curr_wick_end):
    return (
        prev_wick_start <= ts <= prev_close
        or
        curr_open <= ts <= curr_wick_end
    )


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

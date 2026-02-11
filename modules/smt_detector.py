# Important Note (Next Refinement Needed)
# This version:
# Compares last swing highs/lows
# Does NOT yet restrict strictly to wick window timestamps
# Does NOT check invalidation
# We should tighten that next.
from datetime import datetime


def detect_smt_dual(
    nq_30m: list[dict],
    es_30m: list[dict],
    nq_1h: list[dict],
    es_1h: list[dict],
    seven_hour_open_ts: str,
    window_minutes: int = 60
) -> dict:
    """
    Detect SMT on 30m OR 1H.
    At least one timeframe must confirm.
    """

    # 30m first
    result_30m = _check_tf(nq_30m, es_30m, "30m")
    if result_30m["smt_confirmed"]:
        return result_30m

    # Then 1H
    result_1h = _check_tf(nq_1h, es_1h, "1h")
    if result_1h["smt_confirmed"]:
        return result_1h

    return _no_smt()


def _check_tf(nq, es, tf_name):
    nq_highs = _find_swing_highs(nq)
    nq_lows = _find_swing_lows(nq)

    es_highs = _find_swing_highs(es)
    es_lows = _find_swing_lows(es)

    if not nq_highs or not es_highs or not nq_lows or not es_lows:
        return _no_smt()

    last_nq_high = nq_highs[-1]
    last_es_high = es_highs[-1]
    last_nq_low = nq_lows[-1]
    last_es_low = es_lows[-1]

    # ------------------------
    # Bearish SMT (High sweep)
    # ------------------------
    if last_nq_high["high"] > last_es_high["high"]:
        return {
            "smt_confirmed": True,
            "type": "bearish",
            "sweeper": "NQ",
            "non_sweeper": "ES",
            "trade_symbol": "NQ",
            "trade_direction": "SHORT",
            "tf": tf_name
        }

    if last_es_high["high"] > last_nq_high["high"]:
        return {
            "smt_confirmed": True,
            "type": "bearish",
            "sweeper": "ES",
            "non_sweeper": "NQ",
            "trade_symbol": "ES",
            "trade_direction": "SHORT",
            "tf": tf_name
        }

    # ------------------------
    # Bullish SMT (Low sweep)
    # ------------------------
    if last_nq_low["low"] < last_es_low["low"]:
        return {
            "smt_confirmed": True,
            "type": "bullish",
            "sweeper": "NQ",
            "non_sweeper": "ES",
            "trade_symbol": "ES",
            "trade_direction": "LONG",
            "tf": tf_name
        }

    if last_es_low["low"] < last_nq_low["low"]:
        return {
            "smt_confirmed": True,
            "type": "bullish",
            "sweeper": "ES",
            "non_sweeper": "NQ",
            "trade_symbol": "NQ",
            "trade_direction": "LONG",
            "tf": tf_name
        }

    return _no_smt()


def _find_swing_highs(candles):
    swings = []
    for i in range(1, len(candles) - 1):
        if (
            candles[i]["high"] > candles[i - 1]["high"]
            and candles[i]["high"] > candles[i + 1]["high"]
        ):
            swings.append(candles[i])
    return swings


def _find_swing_lows(candles):
    swings = []
    for i in range(1, len(candles) - 1):
        if (
            candles[i]["low"] < candles[i - 1]["low"]
            and candles[i]["low"] < candles[i + 1]["low"]
        ):
            swings.append(candles[i])
    return swings


def _no_smt():
    return {
        "smt_confirmed": False,
        "type": None,
        "sweeper": None,
        "non_sweeper": None,
        "trade_symbol": None,
        "trade_direction": None,
        "tf": None
    }

from datetime import datetime
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

    nq_sweep = _detect_single_sweep(nq_30m, windows)
    es_sweep = _detect_single_sweep(es_30m, windows)

    return {
        "sweep_exists": nq_sweep["sweep_detected"] or es_sweep["sweep_detected"],
        "NQ": nq_sweep,
        "ES": es_sweep
    }


def _detect_single_sweep(candles, windows):

    if len(candles) < 4:
        return _no_sweep()

    prior_high = max(c["high"] for c in candles[:-1])
    prior_low = min(c["low"] for c in candles[:-1])

    for candle in candles:
        ts = candle["timestamp"]

        valid, window_name = is_in_reversal_window(ts, windows)

        if not valid:
            continue

        if candle["high"] > prior_high:
            return {
                "sweep_detected": True,
                "side": "buy_side",
                "timestamp": ts,
                "window": window_name
            }

        if candle["low"] < prior_low:
            return {
                "sweep_detected": True,
                "side": "sell_side",
                "timestamp": ts,
                "window": window_name
            }

    return _no_sweep()


def _no_sweep():
    return {
        "sweep_detected": False,
        "side": None,
        "timestamp": None,
        "window": None
    }

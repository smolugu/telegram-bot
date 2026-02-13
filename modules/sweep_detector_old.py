from datetime import datetime, timedelta


def detect_dual_sweep(
    nq_30m: list[dict],
    es_30m: list[dict],
    seven_hour_open_ts: str,
    wick_window_minutes: int
) -> dict:

    seven_open = datetime.fromisoformat(seven_hour_open_ts)
    seven_close = seven_open + timedelta(hours=7)
    prev_close = seven_open

    prev_wick_start = prev_close - timedelta(minutes=wick_window_minutes)
    curr_wick_end = seven_open + timedelta(minutes=wick_window_minutes)

    nq_sweep = _detect_single_sweep(
        nq_30m,
        prev_wick_start,
        prev_close,
        seven_open,
        curr_wick_end
    )

    es_sweep = _detect_single_sweep(
        es_30m,
        prev_wick_start,
        prev_close,
        seven_open,
        curr_wick_end
    )

    return {
        "sweep_exists": nq_sweep["sweep_detected"] or es_sweep["sweep_detected"],
        "NQ": nq_sweep,
        "ES": es_sweep
    }


def _detect_single_sweep(
    candles,
    prev_wick_start,
    prev_close,
    curr_open,
    curr_wick_end
):

    if len(candles) < 4:
        return _no_sweep()

    # Prior candles before current 7H open
    prior = [
        c for c in candles
        if datetime.fromisoformat(c["timestamp"]) < curr_open
    ]

    if not prior:
        return _no_sweep()

    prior_high = max(c["high"] for c in prior)
    prior_low = min(c["low"] for c in prior)

    for candle in candles:
        ts = datetime.fromisoformat(candle["timestamp"])

        in_prev_wick = prev_wick_start <= ts <= prev_close
        in_curr_wick = curr_open <= ts <= curr_wick_end

        if not (in_prev_wick or in_curr_wick):
            continue

        if candle["high"] > prior_high:
            return {
                "sweep_detected": True,
                "side": "buy_side",
                "timestamp": candle["timestamp"]
            }

        if candle["low"] < prior_low:
            return {
                "sweep_detected": True,
                "side": "sell_side",
                "timestamp": candle["timestamp"]
            }

    return _no_sweep()


def _no_sweep():
    return {
        "sweep_detected": False,
        "side": None,
        "timestamp": None
    }

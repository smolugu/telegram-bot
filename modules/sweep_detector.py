from datetime import datetime, timedelta


def detect_dual_sweep(
    nq_30m: list[dict],
    es_30m: list[dict],
    seven_hour_open_ts: str,
    window_minutes: int = 60
) -> dict:
    """
    Detect sweep on BOTH NQ and ES during 7H wick window.
    """

    nq_sweep = _detect_single_sweep(
        nq_30m,
        seven_hour_open_ts,
        window_minutes
    )

    es_sweep = _detect_single_sweep(
        es_30m,
        seven_hour_open_ts,
        window_minutes
    )

    at_least_one = nq_sweep["sweep_detected"] or es_sweep["sweep_detected"]

    return {
        "sweep_exists": at_least_one,
        "NQ": nq_sweep,
        "ES": es_sweep
    }


def _detect_single_sweep(
    candles_30m: list[dict],
    seven_hour_open_ts: str,
    window_minutes: int
) -> dict:
    """
    Detect sweep for a single market.
    """

    if len(candles_30m) < 4:
        return _no_sweep()

    seven_open = datetime.fromisoformat(seven_hour_open_ts)
    seven_close = seven_open + timedelta(hours=7)

    early_end = seven_open + timedelta(minutes=window_minutes)
    late_start = seven_close - timedelta(minutes=window_minutes)

    # Prior candles before 7H open
    prior = [
        c for c in candles_30m
        if datetime.fromisoformat(c["timestamp"]) < seven_open
    ]

    if not prior:
        return _no_sweep()

    prior_high = max(c["high"] for c in prior)
    prior_low = min(c["low"] for c in prior)

    # Check wick windows
    for candle in candles_30m:
        ts = datetime.fromisoformat(candle["timestamp"])

        in_early = seven_open <= ts < early_end
        in_late = late_start <= ts < seven_close

        if not (in_early or in_late):
            continue

        # Buy-side sweep
        if candle["high"] > prior_high:
            return {
                "sweep_detected": True,
                "side": "buy_side",
                "level": prior_high,
                "window": "early" if in_early else "late",
                "timestamp": candle["timestamp"]
            }

        # Sell-side sweep
        if candle["low"] < prior_low:
            return {
                "sweep_detected": True,
                "side": "sell_side",
                "level": prior_low,
                "window": "early" if in_early else "late",
                "timestamp": candle["timestamp"]
            }

    return _no_sweep()


def _no_sweep():
    return {
        "sweep_detected": False,
        "side": None,
        "level": None,
        "window": None,
        "timestamp": None
    }

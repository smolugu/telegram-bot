from datetime import datetime, timedelta


def detect_7h_wick_sweep(
    candles_30m: list[dict],
    seven_hour_open_ts: str,
    window_minutes: int = 60
) -> dict:
    """
    Detects liquidity sweep during the WICK of a 7H candle.
    Looks ONLY at 30m candles.

    Sweep windows:
    - Early wick: first `window_minutes` of 7H candle
    - Late wick: last `window_minutes` of 7H candle

    candles_30m: list of 30m candles (oldest -> newest)
    """

    if len(candles_30m) < 4:
        return _no_sweep()

    seven_open = datetime.fromisoformat(seven_hour_open_ts)
    seven_close = seven_open + timedelta(hours=7)

    early_end = seven_open + timedelta(minutes=window_minutes)
    late_start = seven_close - timedelta(minutes=window_minutes)

    # Prior liquidity levels (exclude current 7H candles)
    prior_candles = [
        c for c in candles_30m
        if datetime.fromisoformat(c["timestamp"]) < seven_open
    ]

    if not prior_candles:
        return _no_sweep()

    prior_high = max(c["high"] for c in prior_candles)
    prior_low = min(c["low"] for c in prior_candles)

    # Check 30m candles inside wick windows
    for candle in candles_30m:
        ts = datetime.fromisoformat(candle["timestamp"])

        in_early_wick = seven_open <= ts < early_end
        in_late_wick = late_start <= ts < seven_close

        if not (in_early_wick or in_late_wick):
            continue

        # Buy-side sweep
        if candle["high"] > prior_high:
            return {
                "sweep_detected": True,
                "side": "buy_side",
                "level": prior_high,
                "window": "early" if in_early_wick else "late",
                "timestamp": candle["timestamp"]
            }

        # Sell-side sweep
        if candle["low"] < prior_low:
            return {
                "sweep_detected": True,
                "side": "sell_side",
                "level": prior_low,
                "window": "early" if in_early_wick else "late",
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

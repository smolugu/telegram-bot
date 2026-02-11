# 🔧 Easy Future Improvements (Later)
# Without changing the signature, you can later add:
# Weekly bias filter
# EQ (50%) logic
# Displacement threshold tuning
# Fair Value Gap context
# Killzone awareness

def get_daily_bias(
    daily_candles: list[dict],
    current_price: float
) -> dict:
    """
    Daily bias is determined by comparing
    yesterday's candle to the candle from two days ago (PDH/PDL).

    daily_candles: list of daily candles (oldest -> newest)
    Each candle:
    {
        "open": float,
        "high": float,
        "low": float,
        "close": float,
        "timestamp": str
    }
    """

    if len(daily_candles) < 3:
        return {
            "bias": "NEUTRAL",
            "pd_high": None,
            "pd_low": None,
            "reason": "insufficient_data"
        }

    # Day before yesterday (PDH / PDL)
    ref_day = daily_candles[-3]
    pd_high = ref_day["high"]
    pd_low = ref_day["low"]

    # Yesterday candle
    yday = daily_candles[-2]

    y_open = yday["open"]
    y_high = yday["high"]
    y_low = yday["low"]
    y_close = yday["close"]

    candle_range = y_high - y_low
    body_size = abs(y_close - y_open)

    # Avoid divide-by-zero edge case
    displacement = (
        body_size / candle_range
        if candle_range > 0 else 0
    )

    # --- RULE 1: Expansion outside PD range ---
    if y_close > pd_high and displacement >= 0.5:
        return {
            "bias": "BULLISH",
            "pd_high": pd_high,
            "pd_low": pd_low,
            "reason": "bullish_displacement_above_PDH"
        }

    if y_close < pd_low and displacement >= 0.5:
        return {
            "bias": "BEARISH",
            "pd_high": pd_high,
            "pd_low": pd_low,
            "reason": "bearish_displacement_below_PDL"
        }

    # --- RULE 2: Rejection logic ---
    if y_high > pd_high and y_close < pd_high:
        return {
            "bias": "BEARISH",
            "pd_high": pd_high,
            "pd_low": pd_low,
            "reason": "rejection_from_PDH"
        }

    if y_low < pd_low and y_close > pd_low:
        return {
            "bias": "BULLISH",
            "pd_high": pd_high,
            "pd_low": pd_low,
            "reason": "rejection_from_PDL"
        }

    # --- RULE 3: Neutral ---
    return {
        "bias": "NEUTRAL",
        "pd_high": pd_high,
        "pd_low": pd_low,
        "reason": "inside_range_no_displacement"
    }

def classify_volatility(ny_range, atr):

    if ny_range < 0.5 * atr:
        return "low_vol"

    if ny_range > 1.5 * atr:
        return "high_vol"

    return "normal_vol"
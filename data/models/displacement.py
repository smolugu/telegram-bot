def is_displacement_candle(
    candle,
    atr,
    direction,              # "bullish" or "bearish"
    sweep_price=None,       # optional but recommended
    min_body_ratio=0.6,
    min_atr_ratio=0.25
):
    """
    Checks if a 30m candle (OB candle) is a displacement candle
    """

    open_ = float(candle["open"])
    close = float(candle["close"])
    high = float(candle["high"])
    low = float(candle["low"])

    body = abs(close - open_)
    range_ = high - low

    if range_ == 0:
        return False

    # -------------------------
    # 1️⃣ Strong body
    # -------------------------
    body_ratio = body / range_
    strong_body = body_ratio >= min_body_ratio

    # -------------------------
    # 2️⃣ Directional close
    # -------------------------
    if direction == "bearish":
        directional = close < open_
    else:
        directional = close > open_

    # -------------------------
    # 3️⃣ ATR expansion
    # -------------------------
    atr_expansion = body >= min_atr_ratio * atr

    # -------------------------
    # 4️⃣ Move away from sweep (VERY IMPORTANT)
    # -------------------------
    move_away = True

    if sweep_price is not None:
        if direction == "bearish":
            move_away = close < sweep_price
        else:
            move_away = close > sweep_price

    # -------------------------
    # FINAL
    # -------------------------
    print("final:")
    print("strong_body: ", strong_body)
    print("directional: ", directional)
    print("atr_expansion: ", atr_expansion, min_atr_ratio * atr, body)
    print("move_away: ", move_away)
    return strong_body and directional and atr_expansion and move_away
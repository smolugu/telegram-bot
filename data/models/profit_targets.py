def get_tp2_from_liquidity(tp1, direction, liquidity_map):
    """
    Select TP2 from liquidity map

    liquidity_map = {
        "asia_low": {"price": ..., "swept": False},
        "pdl": {...},
        ...
    }
    """

    valid_levels = []
    buy_side_valid_levels = []
    sell_side_valid_levels = []

    # -------------------------
    # 1. Filter unswept levels
    # -------------------------
    for name, lvl in liquidity_map.items():

        price = lvl.get("price")
        swept = lvl.get("swept")
        side = lvl.get("side")

        if price is None or swept:
            continue
        if side == "buy_side":
            buy_side_valid_levels.append(price)
        elif side == "sell_side":
            sell_side_valid_levels.append(price)    
        valid_levels.append(price)

    if not valid_levels:
        return None

    # -------------------------
    # 2. Apply direction filter
    # -------------------------
    if direction == "bearish":
        # TP2 must be BELOW TP1
        candidates = [p for p in sell_side_valid_levels if p < tp1]

        if not candidates:
            return None

        # pick closest BELOW TP1
        tp2 = max(candidates)

    else:  # bullish
        # TP2 must be ABOVE TP1
        candidates = [p for p in buy_side_valid_levels if p > tp1]

        if not candidates:
            return None

        # pick closest ABOVE TP1
        tp2 = min(candidates)

    return tp2

def get_tp_levels(entry, stop, direction, liquidity_map, daily_atr, tp1=None):

    risk = abs(entry - stop)

    # # TP1: fixed RR
    # tp1 = entry - 1.5 * risk if direction == "bearish" else entry + 1.5 * risk

    # TP2: liquidity
    tp2 = get_tp2_from_liquidity(tp1, direction, liquidity_map)
    print("tp2 from function: ", tp2)

     # if no valid TP2 from liquidity, set TP2 to 2RR

    # if tp2 is None:
        # tp2 = entry - 2 * risk if direction == "bearish" else entry + 2 * risk


    # TP3: ATR expansion
    tp3 = entry - 0.7 * daily_atr if direction == "bearish" else entry + 0.7 * daily_atr
    
    return tp1, tp2, tp3
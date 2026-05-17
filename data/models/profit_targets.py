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

def get_tp_levels_from_liquidity(tp1, direction, liquidity_map, entry_price):

    buy_levels = []
    sell_levels = []

    # -------------------------
    # 1. Filter unswept levels
    # -------------------------
    for lvl in liquidity_map.values():

        price = lvl.get("price")
        swept = lvl.get("swept")
        side = lvl.get("side")

        if price is None or swept:
            continue

        if side == "buy_side":
            buy_levels.append(price)

        elif side == "sell_side":
            sell_levels.append(price)

    # -------------------------
    # 2. Direction logic
    # -------------------------
    if direction == "bearish":

        candidates = sorted([p for p in sell_levels if p < entry_price], reverse=True)

    else:  # bullish

        candidates = sorted([p for p in buy_levels if p > entry_price])

    if not candidates:
        return tp1, None
    print("candidates: ", candidates)
    # -------------------------
    # 3. Find closest liquidity
    # -------------------------
    closest = candidates[0]
    print("closest: ", closest)

    # -------------------------
    # 4. Replace TP1 if needed
    # -------------------------
    if abs(entry_price - closest) < abs(entry_price - tp1):
        print("level closest to entry")
        new_tp1 = closest
    else:
        print("tp1 is closest")
        new_tp1 = tp1

    # -------------------------
    # 5. Find TP1 index PROPERLY
    # -------------------------
    tp1_index = None

    for i, p in enumerate(candidates):
        if p == new_tp1:
            tp1_index = i
            break

    # If TP1 is not exactly in list, find correct insertion point
    if tp1_index is None:

        if direction == "bearish":
            # find first level BELOW tp1
            for i, p in enumerate(candidates):
                if p < new_tp1:
                    tp1_index = i
                    break

        else:  # bullish
            # find first level ABOVE tp1
            for i, p in enumerate(candidates):
                if p > new_tp1:
                    tp1_index = i
                    break

    # Safety fallback
    if tp1_index is None:
        tp1_index = 0

    # -------------------------
    # 6. TP2 = next level ONLY
    # -------------------------
    tp2 = None

    if tp1_index + 1 < len(candidates):
        tp2 = candidates[tp1_index + 1]

    # Prevent duplicate TP1/TP2
    if tp2 == new_tp1:
        tp2 = candidates[tp1_index + 2] if tp1_index + 2 < len(candidates) else None

    return new_tp1, tp2

def get_tp_levels(entry, stop, direction, liquidity_map, daily_atr, tp1=None):

    risk = abs(entry - stop)

    # # TP1: fixed RR
    # tp1 = entry - 1.5 * risk if direction == "bearish" else entry + 1.5 * risk

    # TP2: liquidity
    tp1, tp2 = get_tp_levels_from_liquidity(tp1, direction, liquidity_map, entry)
    print("tp2 from function: ", tp2)

     # if no valid TP2 from liquidity, set TP2 to 2RR

    # if tp2 is None:
        # tp2 = entry - 2 * risk if direction == "bearish" else entry + 2 * risk


    # TP3: ATR expansion
    tp3 = entry - 0.7 * daily_atr if direction == "bearish" else entry + 0.7 * daily_atr
    if tp2 is None:
        if direction == "bearish":
            tp2 = tp1 - (tp1 - tp3) / 2
        else:
            tp2 = tp1 + (tp3 - tp1) / 2
    else:
        if direction == "bearish":
            tp2 = tp2+2
        else:
            tp2 = tp2-2

    
    return tp1, tp2, tp3
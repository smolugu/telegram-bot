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

def get_tp_levels_from_liquidity_v2(tp1, direction, liquidity_map, entry_price, min_liquidity_distance, min_tp2_spacing):

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
            # print("level name, price, swept, side: ", lvl)
            buy_levels.append(price)

        elif side == "sell_side":
            # print("level name, price, swept, side: ", lvl)
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

     # ---------------------------------------------------------
    # 3. Find KEY liquidity
    #
    #    Only liquidity >= minimum distance from entry
    #    qualifies to replace TP1.
    # ---------------------------------------------------------

    key_candidates = [
        p for p in candidates
        if abs(entry_price - p) >= min_liquidity_distance
    ]

    # ---------------------------------------------------------
    # 4. TP1
    #
    #    Prefer closest qualifying key liquidity.
    #    Otherwise retain original TP1.
    # ---------------------------------------------------------

    if key_candidates:

        # candidates are already ordered closest -> farthest
        new_tp1 = key_candidates[0]

    else:
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
    # tp2 = None

    # if tp1_index + 1 < len(candidates):
    #     tp2 = candidates[tp1_index + 1]

    # # Prevent duplicate TP1/TP2
    # if tp2 == new_tp1:
    #     tp2 = candidates[tp1_index + 2] if tp1_index + 2 < len(candidates) else None
    tp2 = None

    for p in candidates[tp1_index + 1:]:
        if abs(p - new_tp1) >= min_tp2_spacing:
            tp2 = p
            break

    return new_tp1, tp2



def get_tp_levels_from_liquidity(
    tp1,
    direction,
    liquidity_map,
    entry_price,
    min_liquidity_distance,
    min_tp2_spacing,
    max_liquidity_distance=None,
):
    buy_levels = []
    sell_levels = []

    # 1. Collect unswept liquidity levels
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

    # 2. Keep liquidity in the trade direction
    if direction == "bearish":
        # Closest levels below entry first
        candidates = sorted(
            [p for p in sell_levels if p < entry_price],
            reverse=True,
        )
    else:
        # Closest levels above entry first
        candidates = sorted(
            [p for p in buy_levels if p > entry_price]
        )

    # 3. Select eligible TP1 liquidity
    if max_liquidity_distance is not None:
        key_candidates = [
            p for p in candidates
            if min_liquidity_distance
            <= abs(entry_price - p)
            <= max_liquidity_distance
        ]
    else:
        key_candidates = [
            p for p in candidates
            if abs(entry_price - p) >= min_liquidity_distance
        ]

    # Candidates are sorted closest to farthest
    new_tp1 = key_candidates[0] if key_candidates else tp1

    # 4. Identify levels beyond TP1.
    # If TP1 is a liquidity level, use levels after it.
    # If TP1 is a fallback, use levels farther from entry
    # than that fallback in the trade direction.
    if new_tp1 in candidates:
        tp1_index = candidates.index(new_tp1)
        next_candidates = candidates[tp1_index + 1:]

    elif direction == "bearish":
        next_candidates = [
            p for p in candidates if p < new_tp1
        ]

    else:
        next_candidates = [
            p for p in candidates if p > new_tp1
        ]

    # 5. TP2 = next level satisfying minimum spacing
    tp2 = next(
        (
            p for p in next_candidates
            if abs(p - new_tp1) >= min_tp2_spacing
        ),
        None,
    )

    return new_tp1, tp2


def get_tp_levels(
    entry,
    stop,
    direction,
    liquidity_map,
    daily_atr,
    tp1=None,
    instrument=None,
):
    risk = abs(entry - stop)

    # 1. Instrument-specific liquidity thresholds
    if instrument == "NQ":
        min_liquidity_distance = 75
        max_liquidity_distance = None
        min_tp2_spacing = 40

    elif instrument == "ES":
        min_liquidity_distance = 20
        max_liquidity_distance = 40
        min_tp2_spacing = 10

    else:
        min_liquidity_distance = 75
        max_liquidity_distance = None
        min_tp2_spacing = 40

    # TP1: eligible liquidity, otherwise retain caller's fallback
    # TP2: next qualifying liquidity level
    tp1, tp2 = get_tp_levels_from_liquidity(
        tp1=tp1,
        direction=direction,
        liquidity_map=liquidity_map,
        entry_price=entry,
        min_liquidity_distance=min_liquidity_distance,
        min_tp2_spacing=min_tp2_spacing,
        max_liquidity_distance=max_liquidity_distance,
    )

    print("TP1 from function:", tp1)
    print("TP2 from function:", tp2)

    # TP3: ATR expansion
    tp3 = (
        entry - 0.7 * daily_atr
        if direction == "bearish"
        else entry + 0.7 * daily_atr
    )

    print("Daily ATR:", daily_atr, daily_atr * 0.7)

    # Preserve existing TP2/TP3 midpoint adjustment
    if tp2 is not None:
        tp2_tp3_distance = abs(tp3 - tp2)
        tp1_tp3_distance = abs(tp3 - tp1)

        if tp2_tp3_distance < 0.2 * tp1_tp3_distance:
            tp2 = (tp1 + tp3) / 2

    if tp2 is None:
        if direction == "bearish":
            tp2 = tp1 - (tp1 - tp3) / 2
        else:
            tp2 = tp1 + (tp3 - tp1) / 2
    else:
        if direction == "bearish":
            tp2 = tp2 + 2
        else:
            tp2 = tp2 - 2

    return tp1, tp2, tp3


def get_tp_levels_v2(entry, stop, direction, liquidity_map, daily_atr, tp1=None, instrument=None):

    risk = abs(entry - stop)

    # # TP1: fixed RR
    # tp1 = entry - 1.5 * risk if direction == "bearish" else entry + 1.5 * risk
    # ---------------------------------------------------------
    # 2. Key liquidity threshold
    # ---------------------------------------------------------

    if instrument == "NQ":
        min_liquidity_distance = 75
        min_tp2_spacing = 40

    elif instrument == "ES":
        min_liquidity_distance = 25
        min_tp2_spacing = 10

    else:
        min_liquidity_distance = 75
        min_tp2_spacing = 40

    # TP2: liquidity
    tp1, tp2 = get_tp_levels_from_liquidity(tp1, direction, liquidity_map, entry, min_liquidity_distance, min_tp2_spacing)
    print("tp2 from function: ", tp2)

     # if no valid TP2 from liquidity, set TP2 to 2RR

    # if tp2 is None:
        # tp2 = entry - 2 * risk if direction == "bearish" else entry + 2 * risk


    # TP3: ATR expansion

    tp3 = entry - 0.7 * daily_atr if direction == "bearish" else entry + 0.7 * daily_atr
    print("daily atr xx: ", daily_atr, daily_atr * 0.7)

    if tp2 is not None:
        # If TP2 and TP3 are too close,
        # move TP2 to midpoint between TP1 and TP3
        tp2_tp3_distance = abs(tp3 - tp2)
        tp1_tp3_distance = abs(tp3 - tp1)
        # Example threshold:
        # TP2 and TP3 considered "too close"
        # if distance is less than 20% of full TP1→TP3 range

        if tp2_tp3_distance < 0.2 * tp1_tp3_distance:
            tp2 = (tp1 + tp3) / 2


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
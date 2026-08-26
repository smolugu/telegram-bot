def _refresh_level_lists(context):

    context.bullish_levels = context.bullish_swings + context.bearish_fvgs + context.bearish_vis + context.bearish_cisds
    context.bearish_levels = context.bearish_swings + context.bullish_fvgs + context.bullish_vis + context.bullish_cisds


def _nearest_above(levels, candle_30m):

    candidates = [
        level
        for level in levels
        if not level.is_swept
        and level.price > candle_30m.high
    ]

    if not candidates:
        return None

    return min(
        candidates,
        key=lambda x: x.price,
    )


def _nearest_below(levels, candle_30m):

    candidates = [
        level
        for level in levels
        if not level.is_swept
        and level.price < candle_30m.low
    ]

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda x: x.price,
    )

def _refresh_nearest_levels(
    context,
    candle_30m,
):

    # ---------------------------------------------------------
    # Reset
    # ---------------------------------------------------------
    # print("***********************")
    # print("nearest levels")
    # print("nearest bullish level before: ", context.nearest_bullish_level)
    # print("nearest bearish level before: ", context.nearest_bearish_level)

    context.nearest_bullish_level = None
    context.nearest_bearish_level = None

    context.nearest_bullish_swing = None
    context.nearest_bearish_swing = None

    context.nearest_bullish_fvg = None
    context.nearest_bearish_fvg = None

    context.nearest_bullish_vi = None
    context.nearest_bearish_vi = None

    context.nearest_bullish_cisd = None
    context.nearest_bearish_cisd = None
    

    # ---------------------------------------------------------
    # Bullish levels
    # ---------------------------------------------------------

    bullish_open = [
        level
        for level in context.bullish_levels
        if not level.is_swept
        and level.price > candle_30m.high
    ]

    if bullish_open:

        context.nearest_bullish_level = min(
            bullish_open,
            key=lambda x: x.price,
        )
    # print("nearest bullish level after: ", context.nearest_bullish_level)
    # ---------------------------------------------------------
    # Bearish levels
    # ---------------------------------------------------------
    
    bearish_open = [
        level
        for level in context.bearish_levels
        if not level.is_swept
        and level.price < candle_30m.low
    ]

    if bearish_open:

        context.nearest_bearish_level = max(
            bearish_open,
            key=lambda x: x.price,
        )
    # print("nearest bearish level after: ", context.nearest_bearish_level)
    # print("***********************")
    # ---------------------------------------------------------
    # Type-specific nearest levels
    # ---------------------------------------------------------

    context.nearest_bullish_swing = _nearest_above(
        context.bullish_swings,
        candle_30m,
    )

    context.nearest_bearish_swing = _nearest_below(
        context.bearish_swings,
        candle_30m,
    )

    context.nearest_bullish_fvg = _nearest_above(
        context.bullish_fvgs,
        candle_30m,
    )

    context.nearest_bearish_fvg = _nearest_below(
        context.bearish_fvgs,
        candle_30m,
    )

    context.nearest_bullish_vi = _nearest_above(
        context.bullish_vis,
        candle_30m,
    )

    context.nearest_bearish_vi = _nearest_below(
        context.bearish_vis,
        candle_30m,
    )

    context.nearest_bullish_cisd = _nearest_above(
        context.bullish_cisds,
        candle_30m,
    )

    context.nearest_bearish_cisd = _nearest_below(
        context.bearish_cisds,
        candle_30m,
    )    

def _refresh_level_statistics(context):

    context.open_bullish_levels = sum(
        1
        for level in context.bullish_levels
        if not level.is_swept
    )

    context.open_bearish_levels = sum(
        1
        for level in context.bearish_levels
        if not level.is_swept
    )

    context.swept_bullish_levels = sum(
        1
        for level in context.bullish_levels
        if level.is_swept
    )

    context.swept_bearish_levels = sum(
        1
        for level in context.bearish_levels
        if level.is_swept
    )


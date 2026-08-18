from framework.models.auction.detector.detect_cisd import detect_htf_cisd
from framework.models.auction.detector.detect_fvg import detect_htf_fvg
from framework.models.auction.detector.detect_swings import detect_htf_swings
from framework.models.auction.detector.detect_vi import detect_htf_vi
from framework.models.auction.engine.auction_progress import update_auction_progress
from framework.models.auction.engine.auction_status import build_auction_status
from framework.models.auction.engine.add_update_levels import _add_htf_level, update_current_level_status


def _refresh_level_statistics(context):

    context.open_bullish_levels = sum(
        1
        for level in context.bullish_levels
        if level.status == "OPEN"
    )

    context.open_bearish_levels = sum(
        1
        for level in context.bearish_levels
        if level.status == "OPEN"
    )

    context.swept_bullish_levels = sum(
        1
        for level in context.bullish_levels
        if level.status == "SWEPT"
    )

    context.swept_bearish_levels = sum(
        1
        for level in context.bearish_levels
        if level.status == "SWEPT"
    )

def _refresh_level_lists(context):

    context.bullish_levels = context.bullish_swings + context.bullish_fvgs + context.bullish_vis + context.bullish_cisds
    context.bearish_levels = context.bearish_swings + context.bearish_fvgs + context.bearish_vis + context.bearish_cisds


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

    # ---------------------------------------------------------
    # Bearish levels
    # ---------------------------------------------------------

    bearish_open = [
        level
        for level in context.bearish_levels
        if level.is_swept
        and level.price < candle_30m.low
    ]

    if bearish_open:

        context.nearest_bearish_level = max(
            bearish_open,
            key=lambda x: x.price,
        )

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


def update_new_htf_levels(
    context,
    candles,
    timeframe,
):
    """
    Detect and add newly formed HTF levels.

    `candles` should contain the last 3 completed candles
    for the requested timeframe.

    Example:
        candles = h4_candles[-3:]
        timeframe = "4h"
    """

    if not candles or len(candles) < 3:
        return

    # ---------------------------------------------------------
    # Latest candle
    # ---------------------------------------------------------

    latest_candle = candles[-1]

    latest_timestamp = latest_candle.timestamp

    # ---------------------------------------------------------
    # Detect levels using the last 3 candles
    # ---------------------------------------------------------

    swings = detect_htf_swings(candles, timeframe)
    fvgs = detect_htf_fvg(candles, timeframe)
    vis = detect_htf_vi(candles, timeframe)
    cisds = detect_htf_cisd(candles, timeframe)

    # ---------------------------------------------------------
    # Add levels to context
    # ---------------------------------------------------------

    for level in swings:
        _add_htf_level(
            context,
            level,
        )

    for level in fvgs:

        _add_htf_level(
            context,
            level,
        )

    for level in vis:
        _add_htf_level(
            context,
            level,
        )

    for level in cisds:
        _add_htf_level(
            context,
            level,
        )


def refresh_auction_engine(auction_engine, candle_30m, last_3_4h_candles, last_3_7h_candles):

    # ---------------------------------------------------------
    # 1. Detect newly formed HTF levels
    # ---------------------------------------------------------

    print("last_3_4h_candles: ", last_3_4h_candles)
    print("last_3_7h_candles: ", last_3_7h_candles)
    if last_3_4h_candles:
        update_new_htf_levels(
            auction_engine.context,
            last_3_4h_candles,
            "4h",
        )

    if last_3_7h_candles:
        update_new_htf_levels(
            auction_engine.context,
            last_3_7h_candles,
            "7h",
        )

    # levels = update_level_state(levels, candles_for_auction)
    # build auction context
    # auction_engine.auction_context = build_auction_context(levels)
    # 1. update level status with candle_30m

    update_current_level_status(
        auction_engine.context,
        candle_30m,
    )

    # 
    _refresh_level_lists(auction_engine.context)

    # ---------------------------------------------------------
    # 3. Refresh nearest OPEN levels
    # ---------------------------------------------------------

    _refresh_nearest_levels(
        auction_engine.context,
        candle_30m,
    )

    # ---------------------------------------------------------
    # 4. Refresh statistics
    # ---------------------------------------------------------

    _refresh_level_statistics(auction_engine.context)

    update_auction_progress(
        auction_engine.context,
        candle_30m,
    )

    auction_engine.status = build_auction_status(
        auction_engine.context,
    )

    return auction_engine


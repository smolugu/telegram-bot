from framework.models.auction.detector.detect_cisd import detect_htf_cisd
from framework.models.auction.detector.detect_fvg import detect_htf_fvg
from framework.models.auction.detector.detect_swings import detect_htf_swings
from framework.models.auction.detector.detect_vi import detect_htf_vi
from framework.models.auction.engine.auction_progress import update_auction_progress
from framework.models.auction.engine.auction_status import build_auction_status
from framework.models.auction.engine.add_update_levels import _add_htf_level, update_current_level_status
from framework.models.auction.engine.refresh_auction_helpers.helpers import _refresh_level_lists, _refresh_level_statistics, _refresh_nearest_levels


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


def refresh_auction_engine(auction_engine, candle_30m, ltf_candles, last_3_4h_candles, last_3_7h_candles):

    # ---------------------------------------------------------
    # 1. Detect newly formed HTF levels
    # ---------------------------------------------------------
    print("auction updates for: ", candle_30m.timestamp)
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
        ltf_candles,
        last_3_4h_candles,
        last_3_7h_candles
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


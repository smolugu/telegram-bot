
from framework.models.auction.models.enums import LevelType
from framework.models.auction.models.htf_cisd import HTFCISD
from framework.models.auction.models.htf_fvg import HTFFVG
from framework.models.auction.models.htf_swing import HTFSwing
from framework.models.auction.models.htf_vi import HTFVolumeImbalance
from framework.models.auction.tracker.update_cisd_status import update_cisd_status
from framework.models.auction.tracker.update_fvg_status import update_fvg_status
from framework.models.auction.tracker.update_swing_status import update_swing_status
from framework.models.auction.tracker.update_vi_status import update_vi_status


def _add_htf_level(
    context,
    level,
):
    """
    Add an HTF level to the overall directional list
    and its type-specific list.
    """

    # ---------------------------------------------------------
    # Prevent duplicate levels
    # ---------------------------------------------------------

    all_levels = (
        context.bullish_levels
        + context.bearish_levels
    )

    for existing in all_levels:

        if (
            existing.timeframe == level.timeframe
            and existing.level_type == level.level_type
            and existing.timestamp == level.timestamp
            and existing.price == level.price
        ):
            return

    # ---------------------------------------------------------
    # Overall directional list
    # ---------------------------------------------------------

    if level.is_buy_side:
        context.bullish_levels.append(level)
    else:
        context.bearish_levels.append(level)

    # ---------------------------------------------------------
    # Type-specific list
    # ---------------------------------------------------------
    if isinstance(level, HTFSwing):
        if level.is_bullish:
            context.bullish_swings.append(level)
        else:
            context.bearish_swings.append(level)
    #
    # FVG
    #
    elif isinstance(level, HTFFVG):
        if level.is_bullish:
            context.bullish_fvgs.append(level)
        else:
            context.bearish_fvgs.append(level)
            
    #
    # VI
    #
    elif isinstance(level, HTFVolumeImbalance):
        if level.is_bullish:
            context.bullish_vis.append(level)
        else:
            context.bearish_vis.append(level)

    #
    # CISD
    #
    elif isinstance(level, HTFCISD):
        if level.is_bullish:
            context.bullish_cisds.append(level)
        else:
            context.bearish_cisds.append(level)
            


def update_current_level_status(auction_context, candle_30m):
    """
    Update all HTF level states using the completed 30m candle.
    """
    candles = [candle_30m]

    # Swings
    update_swing_status(
        auction_context.bullish_swings,
        candles,
    )

    update_swing_status(
        auction_context.bearish_swings,
        candles,
    )

    # FVGs
    update_fvg_status(
        auction_context.bullish_fvgs,
        candles,
    )

    update_fvg_status(
        auction_context.bearish_fvgs,
        candles,
    )

    # Volume Imbalances
    update_vi_status(
        auction_context.bullish_vis,
        candles,
    )

    update_vi_status(
        auction_context.bearish_vis,
        candles,
    )

    # CISDs
    update_cisd_status(
        auction_context.bullish_cisds,
        candles,
    )

    update_cisd_status(
        auction_context.bearish_cisds,
        candles,
    )

def update_historical_level_state(levels, historical_candles):
    """
    Update the state of all HTF levels using historical candles.

    Args:
        levels: Flat list containing Swing, FVG, VI and CISD levels.
        historical_candles: Dict containing candles by timeframe.

    Returns:
        Updated levels list.
    """

    for level in levels:

        candles = historical_candles.get(level.timeframe, [])

        if not candles:
            continue

        if level.level_type == LevelType.SWING:

            update_swing_status(
                [level],
                candles,
            )

        elif level.level_type == LevelType.FVG:

            update_fvg_status(
                [level],
                candles,
            )

        elif level.level_type == LevelType.VI:

            update_vi_status(
                [level],
                candles,
            )

        elif level.level_type == LevelType.CISD:

            update_cisd_status(
                [level],
                candles,
            )

    return levels


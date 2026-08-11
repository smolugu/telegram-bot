
from framework.models.auction.models.base_model import LevelType
from framework.models.auction.tracker import update_cisd_status, update_fvg_status, update_swing_status, update_vi_status


def update_current_level_state(auction_context, candle_30m):
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
                level,
                candles,
            )

        elif level.level_type == LevelType.FVG:

            update_fvg_status(
                level,
                candles,
            )

        elif level.level_type == LevelType.VI:

            update_vi_status(
                level,
                candles,
            )

        elif level.level_type == LevelType.CISD:

            update_cisd_status(
                level,
                candles,
            )

    return levels
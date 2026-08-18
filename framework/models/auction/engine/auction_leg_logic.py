from framework.models.auction.engine.auction_progress import _candle_interacts_with_level
from framework.models.auction.models.auction_leg import AuctionLeg
from framework.models.auction.models.enums import AuctionDirection, LevelType, LiquidityType

def _level_event_time(level):
    return getattr(
        level,
        "sweep_time",
        level.timestamp,
    )

def _same_level(a, b):

    if a is b:
        return True

    if (
        a.timeframe != b.timeframe
        or a.level_type != b.level_type
    ):
        return False

    if a.level_type == LevelType.SWING:
        return a.price == b.price

    return (
        a.upper == b.upper
        and a.lower == b.lower
    )

def _is_intermediate_level(
    leg,
    level,
):
    """
    Determine whether a level is simply part of the path
    rather than the current auction objective.
    """

    if leg.objective is None:
        return False

    # Current objective itself
    if _same_level(
        level,
        leg.objective,
    ):
        return False

    # ---------------------------------------------------------
    # Same-direction intermediate liquidity does not replace
    # the objective.
    # ---------------------------------------------------------

    if level.is_bullish and (
        leg.direction
        == AuctionDirection.BULLISH
    ):
        return True

    if (
        not level.is_bullish
        and leg.direction
        == AuctionDirection.BEARISH
    ):
        return True

    return False

def _closest_objective(
    levels,
    reference,
    direction,
):
    if direction == AuctionDirection.BULLISH:
        return min(
            levels,
            key=lambda level: level.price,
        )

    return max(
        levels,
        key=lambda level: level.price,
    )

def _level_is_in_direction(
    level,
    reference,
    direction,
):
    if direction == AuctionDirection.BULLISH:
        return level.price > reference.price

    if direction == AuctionDirection.BEARISH:
        return level.price < reference.price

    return False

def _find_new_auction_leg(
    tf_levels,
    current_price,
):
    swept_levels = [
        level
        for level in tf_levels
        if level.is_swept
    ]

    if not swept_levels:
        return None

    swept_levels = sorted(
        swept_levels,
        key=_level_event_time,
    )

    latest = swept_levels[-1]

    # ---------------------------------------------------------
    # Latest swept level establishes the current direction
    #
    # Bullish level:
    #     auction is moving upward
    #
    # Bearish level:
    #     auction is moving downward
    # ---------------------------------------------------------

    direction = (
        AuctionDirection.BULLISH
        if latest.is_bullish
        else AuctionDirection.BEARISH
    )

    # ---------------------------------------------------------
    # Find the last opposing liquidity.
    # This becomes the anchor for measuring progress.
    # ---------------------------------------------------------

    opposing = [
        level
        for level in swept_levels
        if (
            level.is_bullish
            != latest.is_bullish
        )
    ]

    if not opposing:
        return None

    opposing = sorted(
        opposing,
        key=_level_event_time,
    )

    origin = opposing[-1]

    # ---------------------------------------------------------
    # Find the next objective in the direction of travel.
    #
    # Prefer internal liquidity first.
    # If no internal liquidity exists, use external liquidity.
    # ---------------------------------------------------------

    candidates = [
        level
        for level in tf_levels
        if (
            not level.is_swept
            and _level_is_in_direction(
                level,
                latest,
                direction,
            )
        )
    ]

    if not candidates:
        return None

    internal = [
        level
        for level in candidates
        if level.liquidity_type
        == LiquidityType.INTERNAL
    ]

    if internal:
        objective = _closest_objective(
            internal,
            latest,
            direction,
        )
    else:
        external = [
            level
            for level in candidates
            if level.liquidity_type
            == LiquidityType.EXTERNAL
        ]

        if not external:
            return None

        objective = _closest_objective(
            external,
            latest,
            direction,
        )

    return AuctionLeg(
        direction=direction,
        origin=origin,
        objective=objective,
        opposing_liquidity=origin,
        progress=0.0,
        confirmed=False,
        completed=False,
        is_sub_leg=False,
    )

def _update_timeframe_progress_auction_leg(
    auction_progress,
    levels,
    candle_30m,
):
    """
    Update the auction state for one HTF timeframe.

    Rules:

    1. Auction is represented by an AuctionLeg.
    2. A potential leg becomes confirmed only after 40% progress.
    3. Before confirmation, a newer meaningful swept level can
       replace the current provisional leg.
    4. Intermediate swings do not automatically replace the
       current objective.
    5. Reaching the current objective completes the leg.
    6. If the objective is an HTF level, at_htf is preserved.
    """

    current_price = candle_30m["Close"]

    tf_levels = [
        level
        for level in levels
        if level.timeframe == auction_progress.timeframe
    ]

    if not tf_levels:
        return

    # ---------------------------------------------------------
    # Reset transient HTF state for this update
    # ---------------------------------------------------------

    auction_progress.at_htf = False
    auction_progress.at_htf_level = None

    # ---------------------------------------------------------
    # 1. Check whether price is currently interacting with
    #    an HTF level.
    #
    #    Level status has already been updated using candle_30m,
    #    so do NOT filter on is_swept here.
    # ---------------------------------------------------------

    candle_high = candle_30m["High"]
    candle_low = candle_30m["Low"]

    interacting_levels = [
        level
        for level in tf_levels
        if _candle_interacts_with_level(
            level,
            candle_high,
            candle_low,
        )
    ]

    current_level = None

    if interacting_levels:
        current_level = min(
            interacting_levels,
            key=lambda level: abs(
                current_price - level.price
            ),
        )

    # ---------------------------------------------------------
    # 2. If we are interacting with an HTF level, determine
    #    whether this is the current auction objective.
    # ---------------------------------------------------------

    if current_level is not None:

        leg = auction_progress.current_leg

        if (
            leg.objective is not None
            and _same_level(
                current_level,
                leg.objective,
            )
        ):
            # -------------------------------------------------
            # Current auction objective has been reached.
            # -------------------------------------------------

            leg.completed = True
            leg.progress = 1.0

            auction_progress.progress = 1.0

            auction_progress.at_htf = True
            auction_progress.at_htf_level = current_level

            # Preserve the direction of the auction that
            # brought price to this HTF.
            auction_progress.previous_direction = (
                leg.direction
            )

            auction_progress.previous_leg = leg

            auction_progress.confirmed = leg.confirmed
            auction_progress.confirmed_direction = (
                leg.direction
                if leg.confirmed
                else AuctionDirection.NEUTRAL
            )

            auction_progress.completed = True

            return

        # -----------------------------------------------------
        # Current level is NOT necessarily the objective.
        #
        # It may simply be an intermediate swing.
        # Do not reset the auction.
        # -----------------------------------------------------

        if leg.objective is not None:

            if _is_intermediate_level(
                leg,
                current_level,
            ):
                return

    # ---------------------------------------------------------
    # 3. No active leg yet.
    #
    #    Try to establish a new provisional leg from the
    #    swept liquidity sequence.
    # ---------------------------------------------------------

    if (
        auction_progress.current_leg.origin is None
        or auction_progress.current_leg.objective is None
    ):

        new_leg = _find_new_auction_leg(
            tf_levels,
            current_price,
        )

        if new_leg is None:
            return

        auction_progress.current_leg = new_leg

    # ---------------------------------------------------------
    # 4. Update the current leg
    # ---------------------------------------------------------

    leg = auction_progress.current_leg

    if (
        leg.origin is None
        or leg.objective is None
    ):
        return

    # ---------------------------------------------------------
    # 5. Calculate progress toward current objective
    # ---------------------------------------------------------

    total_distance = (
        abs(
            leg.objective.price
            - leg.origin.price
        )
    )

    if total_distance <= 0:
        leg.progress = 0.0
    else:

        if leg.direction == AuctionDirection.BULLISH:

            travelled = (
                current_price
                - leg.origin.price
            )

        else:

            travelled = (
                leg.origin.price
                - current_price
            )

        leg.progress = (
            travelled / total_distance
        )

        leg.progress = max(
            0.0,
            min(leg.progress, 1.0),
        )

    # ---------------------------------------------------------
    # 6. Confirm auction after 40%
    # ---------------------------------------------------------

    if leg.progress >= 0.40:

        leg.confirmed = True

        auction_progress.confirmed = True

        auction_progress.confirmed_direction = (
            leg.direction
        )

    else:

        leg.confirmed = False

        auction_progress.confirmed = False

        auction_progress.confirmed_direction = (
            AuctionDirection.NEUTRAL
        )

    auction_progress.progress = leg.progress

    # ---------------------------------------------------------
    # 7. Check if objective has already been swept.
    #
    #    This can happen when the 30m status update swept the
    #    objective before we reached this function.
    # ---------------------------------------------------------

    if leg.objective.is_swept:

        leg.progress = 1.0
        leg.completed = True

        auction_progress.progress = 1.0
        auction_progress.completed = True

        auction_progress.previous_direction = (
            leg.direction
        )

        auction_progress.previous_leg = leg

        # If objective is an HTF level, preserve HTF state.
        auction_progress.at_htf = True
        auction_progress.at_htf_level = (
            leg.objective
        )

        return

    # ---------------------------------------------------------
    # 8. Otherwise auction is still active
    # ---------------------------------------------------------

    auction_progress.completed = False
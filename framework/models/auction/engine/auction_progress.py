from data.models.candle import Candle
from framework.models.auction.models.auction_progress import AuctionDirection, AuctionProgress
from framework.models.auction.models.enums import LevelType, LiquidityType

def _closest_level(
    levels,
    direction,
):
    """
    Return the closest level to reference_level
    in the direction of the auction.

    `levels` should already contain only valid candidates
    that are ahead of reference_level.
    """

    if not levels:
        return None

    if direction == AuctionDirection.BULLISH:

        return min(
            levels,
            key=lambda level: level.price,
        )

    if direction == AuctionDirection.BEARISH:

        return max(
            levels,
            key=lambda level: level.price,
        )

    return None

def _is_in_direction(
    level,
    reference_level,
    direction,
):
    """
    Return True if `level` is ahead of `reference_level`
    in the direction of the auction.
    """

    if direction == AuctionDirection.BULLISH:
        return level.price > reference_level.price

    if direction == AuctionDirection.BEARISH:
        return level.price < reference_level.price

    return False

def _candle_interacts_with_level(
    level,
    candle_high,
    candle_low,
):
    """
    Return True if the 30m candle reaches the HTF level.
    """

    # ---------------------------------------------------------
    # Swing = single price
    # ---------------------------------------------------------

    if level.level_type == LevelType.SWING:

        return (
            candle_low
            <= level.price
            <= candle_high
        )

    # ---------------------------------------------------------
    # FVG / VI / CISD = price range
    # ---------------------------------------------------------

    if level.is_bullish:
        return (
            candle_low  <= level.upper
            and candle_high >= level.upper
        )
    else:
        return (
            candle_high >= level.lower
            and candle_low <= level.lower
        )


def _update_timeframe_progress(
    tf_auction_progress: AuctionProgress,
    bullish_levels,
    bearish_levels,
    candle_30m: Candle,
):
    """
    auction_progress is the auction progress for a specific timeframe daily, 7h, 4h
    Update auction progress for one HTF timeframe.

    Auction model:

    1. Price is either at HTF or not at HTF.

    2. If NOT at HTF:
       - Find the latest swept liquidity.
       - Find the closest next liquidity in the direction
         of travel.
       - Anticipate that auction.
       - Confirm it after 40% delivery.

    3. If the objective is reached:
       - Mark the auction complete.
       - Find the next closest liquidity.
       - Begin anticipating the next auction.

    4. If AT HTF:
       - Determine direction from the HTF level.
       - Find the closest previously swept opposing level.
       - Preserve that direction in previous_direction.
       - Mark at_htf=True.
    """

    current_price = candle_30m.close
    current_candle_high = candle_30m.high
    current_candle_low = candle_30m.low
    all_levels = bullish_levels + bearish_levels
    print("updating auction progress for :", tf_auction_progress.timeframe)
    tf_levels = [
        level
        for level in all_levels
        if level.timeframe
        == tf_auction_progress.timeframe
    ]

    if not tf_levels:
        return

    # =========================================================
    # 1. Check HTF interaction
    # =========================================================

    # interacting levels includes all buy side and sell side interacting levels
    interacting_levels = [
        level
        for level in tf_levels
        if _candle_interacts_with_level(
            level,
            current_candle_high,
            current_candle_low,
        )
    ]

    current_htf = None

    if interacting_levels:

        current_htf = min(
            interacting_levels,
            key=lambda level: abs(
                current_price - level.price
            ),
        )
        print("interacting with htf: ", current_htf)
        # current_htf = min(
        #     interacting_levels,
        #     key=lambda level: level.price
        # ) if is_bullish else max(
        #     interacting_levels,
        #     key=lambda level: level.price
        # )

    # =========================================================
    # 2. PRICE IS AT HTF
    # =========================================================

    if current_htf is not None:
        print("current_htf is not None")

        tf_auction_progress.at_htf = True
        tf_auction_progress.at_htf_level = current_htf

        # -----------------------------------------------------
        # Determine auction direction from HTF level.
        #
        # Bullish level = price arrived from below.
        # Bearish level = price arrived from above.
        # -----------------------------------------------------

        if current_htf.is_buy_side:
            print("current_htf is buy_side")
            direction = AuctionDirection.BULLISH

            opposing_levels = [
                level
                for level in tf_levels
                if (
                    level.is_swept
                    and not level.is_buy_side
                    and level.timestamp
                    <= current_htf.timestamp
                )
            ]
            

        else:
            print("current_htf is sell_side")
            direction = AuctionDirection.BEARISH

            opposing_levels = [
                level
                for level in tf_levels
                if (
                    level.is_swept
                    and level.is_buy_side
                    and level.timestamp
                    <= current_htf.timestamp
                )
            ]

        # -----------------------------------------------------
        # Find closest opposing swept liquidity.
        # -----------------------------------------------------

        if opposing_levels:
            print("opposing levels is not None")

            if direction == AuctionDirection.BULLISH:

                previous = max(
                    opposing_levels,
                    key=lambda level: level.price,
                )

            else:

                previous = min(
                    opposing_levels,
                    key=lambda level: level.price,
                )
            print("previous htf: ", previous)
            tf_auction_progress.previous_origin = previous
            tf_auction_progress.previous_objective = (
                current_htf
            )

        # -----------------------------------------------------
        # Preserve direction of auction that reached HTF.
        # -----------------------------------------------------

        tf_auction_progress.previous_direction = (
            direction
        )

        tf_auction_progress.confirmed_direction = (
            direction
        )

        tf_auction_progress.confirmed = True
        tf_auction_progress.progress = 1.0
        tf_auction_progress.completed = True

        return

    # =========================================================
    # 3. PRICE IS NOT AT HTF
    # =========================================================

    tf_auction_progress.at_htf = False
    tf_auction_progress.at_htf_level = None

    # ---------------------------------------------------------
    # Find latest swept liquidity.
    # ---------------------------------------------------------

    swept_levels = [
        level
        for level in tf_levels
        if level.is_swept
    ]

    if not swept_levels:
        return

    latest_swept = max(
        swept_levels,
        key=lambda level: level.mitigation_time,
    )
    swept_levels.sort(
        key=lambda level: level.mitigation_time,
        reverse=True
    )
    if tf_auction_progress.timeframe == "4h":
        print("swept_levels: ", swept_levels)
    print("recent swept: ", latest_swept)
    # ---------------------------------------------------------
    # Determine direction of anticipated auction.
    # ---------------------------------------------------------

    # if latest_swept.is_bullish and current_price > latest_swept.price:
    #     direction = AuctionDirection.BULLISH
    # else:
    #     direction = AuctionDirection.BEARISH
    # if latest_swept.is_bearish and current_price < latest_swept.price:
    #     direction = AuctionDirection.BEARISH
    # else:
    #     direction = AuctionDirection.BULLISH
    if current_price > latest_swept.price:
        direction = AuctionDirection.BULLISH
    elif current_price < latest_swept.price:
        direction = AuctionDirection.BEARISH
    else:
        direction = AuctionDirection.NEUTRAL
    print("direction relative to last swept: ", direction)
    # ---------------------------------------------------------
    # Find candidate objectives.
    # Prefer INTERNAL liquidity.
    # If none exists, use EXTERNAL.
    # ---------------------------------------------------------

    candidates = [
        level
        for level in tf_levels
        if (
            not level.is_swept
            and _is_in_direction(
                level,
                latest_swept,
                direction,
            )
        )
    ]

    if not candidates:
        return

    internal = [
        level
        for level in candidates
        if level.liquidity_type
        == LiquidityType.INTERNAL
    ]

    if internal:

        objective = _closest_level(
            internal,
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
            return

        objective = _closest_level(
            external,
            direction,
        )

    # ---------------------------------------------------------
    # New anticipated auction
    # ---------------------------------------------------------
    print("next target: ", objective)
    tf_auction_progress.origin = latest_swept
    tf_auction_progress.current_objective = objective

    total_distance = abs(
        objective.price
        - latest_swept.price
    )

    if total_distance <= 0:
        return

    if direction == AuctionDirection.BULLISH:

        travelled = (
            current_candle_high
            - latest_swept.price
        )

    else:

        travelled = (
            latest_swept.price
            - current_candle_low
        )
    print("travelled: ", travelled)
    progress = (
        travelled / total_distance
    )
    print("progress after travelled: ", progress)

    progress = max(
        0.0,
        min(progress, 1.0),
    )
    print("progressX: ", progress)

    tf_auction_progress.progress = progress

    # ---------------------------------------------------------
    # Confirm auction after 40%
    # ---------------------------------------------------------

    if progress >= 0.40:
        print("progress > 0.4")
        tf_auction_progress.confirmed = True
        tf_auction_progress.confirmed_direction = (
            direction
        )

    else:
        print("progress less than 0.4")

        tf_auction_progress.confirmed = False
        tf_auction_progress.confirmed_direction = (
            AuctionDirection.NEUTRAL
        )

    # ---------------------------------------------------------
    # Objective reached
    # ---------------------------------------------------------

    if objective.is_swept:
        print("new objective reached")

        tf_auction_progress.progress = 1.0
        tf_auction_progress.completed = True

        tf_auction_progress.previous_direction = (
            direction
        )

        # The next invocation will identify the next
        # closest liquidity and begin a new anticipated auction.

    else:
        print("price not at htf and auction is not complete")
        tf_auction_progress.completed = False

def update_auction_progress(context, candle_30m):

    _update_timeframe_progress(
        context.daily,
        context.bullish_levels,
        context.bearish_levels,
        candle_30m,
    )

    # _update_timeframe_progress(
    #     context.daily,
    #     context.bullish_levels,
    #     context.bearish_levels,
    #     candle_30m,
    # )

    _update_timeframe_progress(
        context.h7,
        context.bullish_levels,
        context.bearish_levels,
        candle_30m,
    )

    # _update_timeframe_progress(
    #     context.h7,
    #     context.bullish_levels,
    #     context.bearish_levels,
    #     candle_30m,
    # )

    _update_timeframe_progress(
        context.h4,
        context.bullish_levels,
        context.bearish_levels,
        candle_30m,
    )

    # _update_timeframe_progress(
    #     context.h4,
    #     context.bullish_levels,
    #     context.bearish_levels,
    #     candle_30m,
    # )
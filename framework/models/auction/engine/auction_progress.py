from framework.models.auction.models.auction_progress import AuctionDirection, AuctionProgress
from framework.models.auction.models.base_model import LevelType, LiquidityType

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
        auction_progress: AuctionProgress,
        levels,
        candle_30m,
        is_bullish
):
    
    """
    Update auction progress for one HTF timeframe.

    Logic:

    1. If the current 30m candle is interacting with an HTF level:
       - Identify the HTF level being interacted with.
       - Find the most recent swept level before it.
       - The movement from previous swept level -> current HTF
         level determines the previous auction direction.

    2. If the current 30m candle is not interacting with an HTF level:
       - Find the most recent swept level.
       - Find the nearest OPEN level with alternating liquidity type.
       - Confirm price is between the two levels.
       - Calculate auction progress.
       - Confirm auction once progress >= 50%.
    """
    current_price = candle_30m["Close"]
    candle_high = candle_30m["High"]
    candle_low = candle_30m["Low"]

    # ---------------------------------------------------------
    # 1. Levels for this timeframe
    # ---------------------------------------------------------

    tf_levels = [
        level
        for level in levels
        if level.timeframe == auction_progress.timeframe
    ]

    if not tf_levels:
        return

    # ---------------------------------------------------------
    # 2. Find HTF level currently being interacted with
    # ---------------------------------------------------------

    interacting_levels = [
        level
        for level in tf_levels
        if (
            _candle_interacts_with_level(
                level,
                candle_high,
                candle_low,
            )
        )
    ]

    # =========================================================
    # CASE 1:
    # Current 30m candle is interacting with an HTF level
    # =========================================================

    if interacting_levels:

        # If multiple levels are being interacted with,
        # use the closest one to current price.
        # use the one closest based on bullush or bearish levels
        # current_level = min(
        #     interacting_levels,
        #     key=lambda level: abs(
        #         current_price - level.price
        #     ),
        # )
        current_level = min(
            interacting_levels,
            key=lambda level: level.price
        ) if is_bullish else max(
            interacting_levels,
            key=lambda level: level.price
        )

        # -----------------------------------------------------
        # Find the most recent swept level BEFORE current level
        # -----------------------------------------------------

        previous_liquidity_type = (
            LiquidityType.INTERNAL
            if current_level.liquidity_type == LiquidityType.EXTERNAL
            else LiquidityType.EXTERNAL
        )

        previous_swept_levels = [
            level
            for level in tf_levels
            if (
                level.is_swept
                and level.liquidity_type == previous_liquidity_type
                and level.timestamp < current_level.timestamp
            )
        ]

        if not previous_swept_levels:
            return

        if current_level.is_bullish:
            if previous_liquidity_type == LiquidityType.EXTERNAL:
                # bullish internal objective.
                # previous external liquidity is above
                candidates = [
                    level
                    for level in previous_swept_levels
                    if level.price > current_level.price
                ]
                if not candidates:
                    return

                previous = min(
                    candidates,
                    key=lambda level: level.price,
                )
            else:
                # bullish external objective.
                # previous internal liquidity is below.
                candidates = [
                    level
                    for level in previous_swept_levels
                    if level.price < current_level.price
                ]
                if not candidates:
                    return
                previous = max(
                    candidates,
                    key=lambda level: level.price,
                )
        else:

            if previous_liquidity_type == LiquidityType.EXTERNAL:
                # bearish internal objective
                # previous external liquidity is below
                candidates = [
                    level
                    for level in previous_swept_levels
                    if level.price < current_level.price
                ]

                if not candidates:
                    return

                previous = max(
                    candidates,
                    key=lambda level: level.price,
                )
            else:
                # bearish external objective
                # previous internal liquidity is above
                candidates = [
                    level
                    for level in previous_swept_levels
                    if level.price > current_level.price
                ]

                if not candidates:
                    return
                previous = min(
                    candidates,
                    key=lambda level: level.price,
                )
        

        # -----------------------------------------------------
        # Determine auction direction from price movement
        #
        # Previous level -> Current level
        # -----------------------------------------------------

        if current_level.price > previous.price:

            auction_direction = (
                AuctionDirection.BULLISH
            )

        elif current_level.price < previous.price:

            auction_direction = (
                AuctionDirection.BEARISH
            )

        else:
            return

        # -----------------------------------------------------
        # Store current HTF interaction
        # -----------------------------------------------------
        # auction at key level
        # reset auction progress
        auction_progress.at_htf = True
        auction_progress.at_htf_level = current_level
        auction_progress.completed = True
        auction_progress.previous_objective = previous
        auction_progress.current_objective = current_level

        auction_progress.progress = 0.0

        auction_progress.confirmed = False
        auction_progress.previous_direction = auction_direction
        auction_progress.confirmed_direction = (
            AuctionDirection.NEUTRAL
        )

        
        

        return
    
    # =========================================================
    # CASE 2:
    # Price is NOT currently interacting with HTF
    # =========================================================

    # ---------------------------------------------------------
    # Find most recent swept level
    # ---------------------------------------------------------

    swept = [
        level
        for level in tf_levels
        if level.is_swept
    ]

    if not swept:
        return

    previous = max(
        swept,
        key=lambda level: level.timestamp,
    )

    target_liquidity_type = (
        LiquidityType.INTERNAL
        if previous.LiquidityType == LiquidityType.EXTERNAL
        else LiquidityType.EXTERNAL
    )

    open_levels = [
        level
        for level in tf_levels
        if (
            not level.is_swept
            and level.liquidity_type == target_liquidity_type
        )
    ]

    current_objective = None
    if is_bullish:
        if target_liquidity_type == LiquidityType.EXTERNAL:
            candidates = [
                level
                for level in open_levels
                if level.price > previous.price
            ]

            current_objective = min(
                candidates,
                key=lambda level: level.price,
            )
        elif target_liquidity_type == LiquidityType.INTERNAL:
            candidates = [
                level
                for level in open_levels
                if level.price < previous.price
            ]
            current_objective = max(
                candidates,
                key=lambda level: level.price,
            )
        else:
            return
    else:
        if target_liquidity_type == LiquidityType.EXTERNAL:
            candidates = [
                level
                for level in open_levels
                if level.price < previous.price
            ]
            current_objective = max(
                candidates,
                key=lambda level: level.price,
            )
        elif target_liquidity_type == LiquidityType.INTERNAL:
            candidates = [
                level
                for level in open_levels
                if level.price > previous.price
            ]
            current_objective = min(
                candidates,
                key=lambda level: level.price,
            )
        else:
            return
    total_distance = 0
    travelled = 0
    progress = 0.0
    if current_objective.price > previous.price:
        auction_direction = (
            AuctionDirection.BULLISH
        )
        total_distance = (
            current_objective.price - previous.price
        )
        travelled = (
            candle_30m["high"] - previous.price
        )
        if total_distance <= 0:
            progress = 0.0
        else:
            progress = travelled / total_distance

        
    elif current_objective.price < previous.price:
        auction_direction = (
            AuctionDirection.BEARISH
        )
        total_distance = (
            previous.price - current_objective.price
        )
        travelled = (
            previous.price - candle_30m["low"]
        )
        if total_distance <= 0:
            progress = 0.0
        else:
            progress = travelled / total_distance
    else:
        return

    # ---------------------------------------------------------
    # Make sure price is actually between the two levels
    # ---------------------------------------------------------

    if not (
        min(previous.price, current_objective.price)
        <= current_price
        <= max(previous.price, current_objective.price)
    ):
        return
    
    # -----------------------------------------------------
    # Store current HTF interaction
    # -----------------------------------------------------
    progress = max(0.0, min(progress, 1.0))
    auction_progress.previous_objective = previous
    auction_progress.current_objective = current_objective

    auction_progress.progress = progress

    if progress >= 0.5:
        auction_progress.confirmed = True
        auction_progress.confirmed_direction = (
                auction_direction
            )
    else:
        auction_progress.confirmed = False
        auction_progress.confirmed_direction = AuctionDirection.NEUTRAL


    # We are at the objective, but it has not necessarily
    # been swept yet.
    auction_progress.completed = (
        current_level.is_swept
    )

    return



def update_auction_progress(context, candle_30m):

    _update_timeframe_progress(
        context.daily,
        context.bullish_levels,
        candle_30m,
        True,
    )

    _update_timeframe_progress(
        context.daily,
        context.bearish_levels,
        candle_30m,
        False,
    )

    _update_timeframe_progress(
        context.h7,
        context.bullish_levels,
        candle_30m,
        True,
    )

    _update_timeframe_progress(
        context.h7,
        context.bearish_levels,
        candle_30m,
        False,
    )

    _update_timeframe_progress(
        context.h4,
        context.bullish_levels,
        candle_30m,
        True,
    )

    _update_timeframe_progress(
        context.h4,
        context.bearish_levels,
        candle_30m,
        False,
    )
from framework.models.auction.models.auction_progress import AuctionDirection
from framework.models.auction.models.auction_status import AuctionStatus



def get_individual_auction_status(auction) -> dict:

    if auction.at_htf:
        return {
            "state": "at_htf",
            "direction": auction.previous_direction,
            "progress": auction.progress,
            "htf_level": (
                auction.at_htf_level.price
                if auction.at_htf_level is not None
                else None
            ),
        }

    if auction.confirmed:
        return {
            "state": "ongoing",
            "direction": auction.confirmed_direction,
            "progress": auction.progress,
            "objective": (
                auction.current_objective.price
                if auction.current_objective is not None
                else None
            ),
        }

    return {
        "state": "neutral",
        "direction": AuctionDirection.NEUTRAL,
        "progress": auction.progress,
        "objective": None,
    }

def build_auction_status(context):

    status = AuctionStatus(
        daily=context.daily,
        h7=context.h7,
        h4=context.h4,
    )

    # ---------------------------------------------------------
    # Capture individual auction statuses
    # ---------------------------------------------------------

    status.daily_status = get_individual_auction_status(
        context.daily
    )

    status.h7_status = get_individual_auction_status(
        context.h7
    )

    status.h4_status = get_individual_auction_status(
        context.h4
    )

    # ---------------------------------------------------------
    # 1. HTF interaction takes precedence
    # ---------------------------------------------------------

    for auction in (
        context.daily,
        context.h7,
        context.h4,
    ):

        if auction.at_htf:

            status.at_htf = True
            status.at_htf_level = auction.at_htf_level
            status.previous_direction = (
                auction.previous_direction
            )

            # Highest timeframe HTF wins
            status.active_timeframe = None
            status.active_direction = (
                AuctionDirection.NEUTRAL
            )
            status.active_progress = 0.0

            return status

    # ---------------------------------------------------------
    # 2. No HTF interaction
    # Find highest timeframe with confirmed auction
    # ---------------------------------------------------------

    for timeframe, auction in (
        ("1d", context.daily),
        ("7h", context.h7),
        ("4h", context.h4),
    ):

        if auction.confirmed:
            print("confirmed auction timeframe when not at htf: ", timeframe)
            if auction.current_objective is None:
                print(
                    f"WARNING: {timeframe} auction is confirmed "
                    f"but current_objective is None. "
                    f"Skipping this timeframe."
                )
                continue

            print(
                "confirmed auction timeframe when not at htf: ",
                timeframe,
            )

            status.active_timeframe = timeframe
            status.active_direction = (
                auction.confirmed_direction
            )
            status.active_progress = auction.progress
            status.active_objective = auction.current_objective.price

            return status

    # ---------------------------------------------------------
    # 3. No HTF interaction and no confirmed auction
    # ---------------------------------------------------------

    return status
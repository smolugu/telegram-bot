from framework.models.auction.models.auction_progress import AuctionDirection
from framework.models.auction.models.auction_status import AuctionStatus


def build_auction_status(context):

    status = AuctionStatus(
        daily=context.daily,
        h7=context.h7,
        h4=context.h4,
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
        ("D", context.daily),
        ("7H", context.h7),
        ("4H", context.h4),
    ):

        if auction.confirmed:

            status.active_timeframe = timeframe
            status.active_direction = (
                auction.confirmed_direction
            )
            status.active_progress = auction.progress

            return status

    # ---------------------------------------------------------
    # 3. No HTF interaction and no confirmed auction
    # ---------------------------------------------------------

    return status
from framework.models.auction.models.auction_progress import AuctionDirection
from framework.models.auction.models.auction_status import AuctionStatus


def determine_auction_direction(
    auction_status: AuctionStatus,
) -> AuctionDirection:
    """
    Determine the directional bias allowed for trade candidates.

    Priority:
        Daily > 7H > 4H

    If price is at HTF:
        Trade opposite to the auction that brought price
        to the HTF objective.

    If price is not at HTF:
        Trade in the direction of the confirmed auction
        toward its HTF objective.

    Returns:
        BULLISH
        BEARISH
        NEUTRAL
    """

    auctions = (
        auction_status.daily,
        auction_status.h7,
        auction_status.h4,
    )

    # ---------------------------------------------------------
    # 1. Price is AT HTF
    # ---------------------------------------------------------

    for auction in auctions:

        if not auction.at_htf:
            continue
        print("price is at htf")
        if auction.previous_direction == (
            AuctionDirection.BULLISH
        ):
            return AuctionDirection.BEARISH

        if auction.previous_direction == (
            AuctionDirection.BEARISH
        ):
            return AuctionDirection.BULLISH

        return AuctionDirection.NEUTRAL

    # ---------------------------------------------------------
    # 2. Price is NOT at HTF
    #
    # Follow the highest-priority confirmed auction.
    # ---------------------------------------------------------
    print("price is not at htf")
    for auction in auctions:

        if not auction.confirmed:
            print("auction direction is not confirmed")
            continue
        print("auction confirmed direction: ", auction.confirmed_direction)
        if auction.confirmed_direction == (
            AuctionDirection.BULLISH
        ):
            return AuctionDirection.BULLISH

        if auction.confirmed_direction == (
            AuctionDirection.BEARISH
        ):
            return AuctionDirection.BEARISH

    # ---------------------------------------------------------
    # 3. No directional auction
    # ---------------------------------------------------------
    print("Auction direction is neutral")
    return AuctionDirection.NEUTRAL
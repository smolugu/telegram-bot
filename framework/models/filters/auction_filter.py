from framework.models.auction.models.auction_progress import AuctionDirection
from framework.models.auction.models.auction_status import AuctionStatus

# def check_auction_status(
#     auction_status: AuctionStatus,
# ) -> bool:
#     state = auction_status.h7_status["state"]
#     direction = auction_status.h7_status["direction"]


def get_auction_details(
    auction_engine,
    co_asset_auction_engine,
) -> bool:

    def is_auction_in_progress(auction):
        is_bullish_auction_in_progress = False
        is_bearish_auction_in_progress = False
        if auction.confirmed_direction == AuctionDirection.BEARISH:
            is_bullish_auction_in_progress = False
            is_bearish_auction_in_progress = True
        elif auction.confirmed_direction == AuctionDirection.BULLISH:
            is_bullish_auction_in_progress = True
            is_bearish_auction_in_progress = False
        elif auction.previous_direction == AuctionDirection.BULLISH and auction.progress > 0.0 and auction.progress < 1.0:
            # initial signs of bearish auction progress, candidate direction is confirmation
            is_bullish_auction_in_progress = False
            is_bearish_auction_in_progress = True
        elif auction.previous_direction == AuctionDirection.BEARISH and auction.progress > 0.0 and auction.progress < 1.0:
            # initial signs of bullish auction progress, candidate direction is confirmation
            is_bullish_auction_in_progress = True
            is_bearish_auction_in_progress = False
        return is_bullish_auction_in_progress, is_bearish_auction_in_progress
        
        
    is_bullish_auction_in_progress = False
    is_bearish_auction_in_progress = False
    # Primary asset auction completion
    print("7h")
    is_7h_bullish_auction_in_progress, is_7h_bearish_auction_in_progress = is_auction_in_progress(
            auction_engine.status.h7,
        )
    print("4h")
    is_4h_bullish_auction_in_progress, is_4h_bearish_auction_in_progress = is_auction_in_progress(
            auction_engine.status.h4,
        )

    is_7h_bullish_co_asset_auction_in_progress, is_7h_bearish_co_asset_auction_in_progress = is_auction_in_progress(
            co_asset_auction_engine.status.h7,
        )
    print("4h")
    is_4h_bullish_co_asset_auction_in_progress, is_4h_bearish_co_asset_auction_in_progress = is_auction_in_progress(
            co_asset_auction_engine.status.h4,
        )

    is_bullish_auction_in_progress = (
        is_7h_bullish_auction_in_progress 
        and is_4h_bullish_auction_in_progress 
        and is_7h_bullish_co_asset_auction_in_progress 
        and is_4h_bullish_co_asset_auction_in_progress
    )
    is_bearish_auction_in_progress = (
        is_7h_bearish_auction_in_progress 
        and is_4h_bearish_auction_in_progress 
        and is_7h_bearish_co_asset_auction_in_progress 
        and is_4h_bearish_co_asset_auction_in_progress
    )
    
    return is_bullish_auction_in_progress, is_bearish_auction_in_progress


def check_auction_status(
    auction_engine,
    session_direction,
    candidate_side,
    co_asset_auction_engine,
    co_asset_session_direction,
    co_asset_candidate_side,
) -> bool:

    def is_auction_complete(auction, session_direction, candidate_side):
        if session_direction == "bullish":
            if auction.confirmed_direction == AuctionDirection.BEARISH:
                print("201")
                return True

            if (
                auction.previous_direction == AuctionDirection.BULLISH
                and auction.anticipated_direction == AuctionDirection.NEUTRAL
            ):
                print("202")
                return True

        elif session_direction == "bearish":
            if auction.confirmed_direction == AuctionDirection.BULLISH:
                print("203")
                return True

            if (
                auction.previous_direction == AuctionDirection.BEARISH
                and auction.anticipated_direction == AuctionDirection.NEUTRAL
            ):
                print("204")
                return True
        print("205")
        return False

    # Primary asset auction completion
    print("7h")
    is_7h_auction_complete = is_auction_complete(
        auction_engine.status.h7,
        session_direction,
        candidate_side,
    )
    print("7h status: ", is_7h_auction_complete)

    print("4h")
    is_4h_auction_complete = is_auction_complete(
        auction_engine.status.h4,
        session_direction,
        candidate_side,
    )
    print("4h status: ", is_4h_auction_complete)

    # Cross-asset auction completion
    print("7h co asset")
    is_co_asset_7h_auction_complete = is_auction_complete(
        co_asset_auction_engine.status.h7,
        co_asset_session_direction,
        co_asset_candidate_side,
    )
    print("7h co asset status: ", is_co_asset_7h_auction_complete)

    print("4h co asset")
    is_co_asset_4h_auction_complete = is_auction_complete(
        co_asset_auction_engine.status.h4,
        co_asset_session_direction,
        co_asset_candidate_side,
    )
    print("4h co asset status: ", is_co_asset_4h_auction_complete)

    return (
        is_7h_auction_complete
        and is_4h_auction_complete
        and is_co_asset_7h_auction_complete
        and is_co_asset_4h_auction_complete
    )

        


# def check_auction_status(
#     auction_engine, direction, co_asset_auction_engine, co_asset_direction
# ) -> bool:
#     is_auction_complete = False
#     is_co_asset_auction_complete = False
#     if auction_engine.status.h7_status["state"] == "at_htf" and auction_engine.status.h4_status == "at_htf":
#         print("x01")
#         if (
#             direction == "bullish" 
#             and auction_engine.status.h7_status["direction"] == AuctionDirection.BULLISH 
#             and auction_engine.status.h4_status["direction"] == AuctionDirection.BULLISH
#         ):
#             print("x02")
#             is_auction_complete = True
#         elif (
#             direction == "bearish" 
#             and auction_engine.status.h7_status["direction"] == AuctionDirection.BEARISH
#             and auction_engine.status.h4_status["direction"] == AuctionDirection.BEARISH
#         ):
#             print("x03")
#             is_auction_complete = True

#     if co_asset_auction_engine.status.h7_status["state"] == "at_htf" and co_asset_auction_engine.status.h4_status == "at_htf":
#         print("x04")
#         if (
#             co_asset_direction == "bullish" 
#             and co_asset_auction_engine.status.h7_status["direction"] == AuctionDirection.BULLISH 
#             and co_asset_auction_engine.status.h4_status["direction"] == AuctionDirection.BULLISH
#         ):
#             print("x05")
#             is_co_asset_auction_complete = True
#         elif (
#             co_asset_direction == "bearish" 
#             and co_asset_auction_engine.status.h7_status["direction"] == AuctionDirection.BEARISH
#             and co_asset_auction_engine.status.h4_status["direction"] == AuctionDirection.BEARISH
#         ):
#             print("x06")
#             is_co_asset_auction_complete = True
    

#     return is_auction_complete and is_co_asset_auction_complete



def get_auction_direction(
        auction_status: AuctionStatus,
) -> AuctionDirection:
    # print("auction status daily: ", auction_status.daily)
    # print("auction status daily: ", auction_status.h7)
    # print("auction status daily: ", auction_status.h4)
    # print("auction summary: ", auction_status.summary)
    if auction_status.active_direction == AuctionDirection.NEUTRAL:
        return auction_status.previous_direction
    else:
        return auction_status.active_direction

# used with ATR filter
def allowed_auction_direction(
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
        # return neutral for london session
        # return AuctionDirection.NEUTRAL
        
        # return opposite direction, assuming reversal from htf. the structure will decide if the
        # level is appropriate for reversal
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
        default_direction = AuctionDirection.NEUTRAL
        if not auction.confirmed:
            print("auction direction is not confirmed")
            if default_direction == AuctionDirection.NEUTRAL:
                default_direction = auction.direction
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
    # 3. default direction - no confirmed auction but direction is present
    # ---------------------------------------------------------
    print("Auction direction is default_direction")
    return AuctionDirection.NEUTRAL
    # return default_direction
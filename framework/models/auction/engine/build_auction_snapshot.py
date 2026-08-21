from copy import deepcopy

from framework.models.auction.models.auction_snapshot import AuctionSnapshot
from framework.models.auction.models.enums import AuctionDirection


def create_auction_snapshot(
    auction_status,
    timestamp,
):
    return AuctionSnapshot(
        timestamp=timestamp,

        daily=deepcopy(
            auction_status.daily
        ),

        h7=deepcopy(
            auction_status.h7
        ),

        h4=deepcopy(
            auction_status.h4
        ),

        active_timeframe=(
            auction_status.active_timeframe
            if hasattr(
                auction_status,
                "active_timeframe",
            )
            else None
        ),

        direction=(
            auction_status.direction
            if hasattr(
                auction_status,
                "direction",
            )
            else AuctionDirection.NEUTRAL
        ),

        at_htf=(
            auction_status.at_htf
            if hasattr(
                auction_status,
                "at_htf",
            )
            else False
        ),

        at_htf_level=(
            auction_status.at_htf_level
            if hasattr(
                auction_status,
                "at_htf_level",
            )
            else None
        ),
    )
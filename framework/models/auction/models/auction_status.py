from dataclasses import dataclass

from framework.models.auction.models.auction_progress import AuctionDirection, AuctionProgress


@dataclass
class AuctionStatus:

    # Overall HTF state
    at_htf: bool = False
    at_htf_level = None
    previous_direction: AuctionDirection = (
        AuctionDirection.NEUTRAL
    )

    # Highest-priority active auction
    active_timeframe: str | None = None
    active_direction: AuctionDirection = (
        AuctionDirection.NEUTRAL
    )
    active_progress: float = 0.0

    # Individual timeframe states
    daily: AuctionProgress | None = None
    h7: AuctionProgress | None = None
    h4: AuctionProgress | None = None
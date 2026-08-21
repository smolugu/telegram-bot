from dataclasses import dataclass
from datetime import datetime

from framework.models.auction.models.auction_progress import AuctionProgress
from framework.models.auction.models.enums import AuctionDirection


@dataclass
class AuctionSnapshot:

    timestamp: datetime

    daily: AuctionProgress
    h7: AuctionProgress
    h4: AuctionProgress

    # The highest-priority HTF state at that moment
    active_timeframe: str | None = None

    direction: AuctionDirection = (
        AuctionDirection.NEUTRAL
    )

    at_htf: bool = False
    at_htf_level = None
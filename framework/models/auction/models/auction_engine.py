from dataclasses import dataclass

from framework.models.auction.models.auction_context import AuctionContext
from framework.models.auction.models.auction_status import AuctionStatus


from dataclasses import dataclass, field

@dataclass
class AuctionEngine:
    context: AuctionContext = field(default_factory=AuctionContext)
    status: AuctionStatus = field(default_factory=AuctionStatus)
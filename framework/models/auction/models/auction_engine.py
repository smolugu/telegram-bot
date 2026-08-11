from dataclasses import dataclass

from framework.models.auction.models.auction_context import AuctionContext
from framework.models.auction.models.auction_status import AuctionStatus


@dataclass
class AuctionEngine:

    context: AuctionContext

    status: AuctionStatus
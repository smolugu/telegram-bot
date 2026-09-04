from dataclasses import dataclass, field
from typing import Optional

from framework.models.auction.models.auction_leg import AuctionLeg
from framework.models.auction.models.enums import AuctionDirection


@dataclass
class AuctionProgress:

    timeframe: str

    # ---------------------------------------------------------
    # Current anticipated auction
    # ---------------------------------------------------------

    origin = None
    current_objective = None

    progress: float = 0.0
    direction: AuctionDirection = (
        AuctionDirection.NEUTRAL
    )

    confirmed: bool = False

    confirmed_direction: AuctionDirection = (
        AuctionDirection.NEUTRAL
    )

    # ---------------------------------------------------------
    # HTF state
    # ---------------------------------------------------------

    at_htf: bool = False
    at_htf_level = None

    # Auction direction that brought price to HTF
    previous_direction: AuctionDirection = (
        AuctionDirection.NEUTRAL
    )

    previous_origin = None
    previous_objective = None

    completed: bool = False

    def summary(self) -> dict:
        return {
            "timeframe": self.timeframe,
            "progress": self.progress,
            "confirmed": self.confirmed,
            "confirmed_direction": self.confirmed_direction,
            "previous_direction": self.previous_direction,
            "at_htf": self.at_htf,
            "at_htf_level": self.at_htf_level,
        }

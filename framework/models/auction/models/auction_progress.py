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

@dataclass
class AuctionProgressOld2:

    timeframe: str

    # ---------------------------------------------------------
    # Current auction leg
    # ---------------------------------------------------------

    current_leg: AuctionLeg = field(
        default_factory=AuctionLeg
    )

    previous_leg: AuctionLeg | None = None

    # ---------------------------------------------------------
    # Current confirmed auction
    # ---------------------------------------------------------

    confirmed_direction: AuctionDirection = (
        AuctionDirection.NEUTRAL
    )

    confirmed: bool = False
    completed: bool = False

    progress: float = 0.0

    # ---------------------------------------------------------
    # HTF state
    # ---------------------------------------------------------

    at_htf: bool = False
    at_htf_level = None

    # Direction of auction that brought price to HTF
    previous_direction: AuctionDirection = (
        AuctionDirection.NEUTRAL
    )

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



@dataclass
class AuctionProgressOld:

    timeframe: str                      # D, 7H, 4H

    previous_objective = None
    current_objective = None

    progress: float = 0.0               # 0.0 - 1.0

    confirmed_direction: str = AuctionDirection.NEUTRAL
    previous_direction: str = AuctionDirection.NEUTRAL
    confirmed: bool = False
    completed: bool = False

    at_htf: bool = False
    at_htf_level: object | None = None

    def summary(self) -> dict:
        return {
            "timeframe": self.timeframe,
            "progress": self.progress,
            "confirmed": self.confirmed,
            "previous_objective": self.previous_objective,
            "current_objective": self.current_objective,
            "confirmed_direction": self.confirmed_direction,
            "previous_direction": self.previous_direction,
            "at_htf": self.at_htf,
            "at_htf_level": self.at_htf_level,
        }

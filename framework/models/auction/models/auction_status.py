from dataclasses import dataclass

from framework.models.auction.models.auction_progress import AuctionProgress
from framework.models.auction.models.auction_snapshot import AuctionSnapshot
from framework.models.auction.models.enums import AuctionDirection, AuctionMomentumType, AuctionStageType



@dataclass
class AuctionStatus:

    # Overall HTF state
    at_htf: bool = False
    at_htf_level: object | None = None
    previous_direction: AuctionDirection = (
        AuctionDirection.NEUTRAL
    )
    stage: AuctionStageType = AuctionStageType.NEUTRAL
    momentum: AuctionMomentumType = AuctionMomentumType.NEUTRAL

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

    # ---------------------------------------------------------
    # Historical auction snapshots
    # ---------------------------------------------------------

    snapshot_1am: AuctionSnapshot | None = None
    snapshot_8am: AuctionSnapshot | None = None
    snapshot_3pm: AuctionSnapshot | None = None

    def summary(self) -> dict:
        return {
            "daily": self.daily.summary(),
            "h7": self.h7.summary(),
            "h4": self.h4.summary(),
        }
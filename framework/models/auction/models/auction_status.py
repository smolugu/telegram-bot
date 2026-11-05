from dataclasses import dataclass, field
from typing import Any

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
    active_objective: float | None = None

    # Individual timeframe states
    daily: AuctionProgress | None = None
    h7: AuctionProgress | None = None
    h4: AuctionProgress | None = None

    h7_status: dict[str, Any] = field(default_factory=dict)
    h4_status: dict[str, Any] = field(default_factory=dict)
    daily_status: dict[str, Any] = field(default_factory=dict)

    # ---------------------------------------------------------
    # Historical auction snapshots
    # ---------------------------------------------------------

    snapshot_1am: AuctionSnapshot | None = None
    snapshot_8am: AuctionSnapshot | None = None
    snapshot_3pm: AuctionSnapshot | None = None

    # previous_direction: AuctionDirection = (
    #         AuctionDirection.NEUTRAL
    #     )
    #     stage: AuctionStageType = AuctionStageType.NEUTRAL
    #     momentum: AuctionMomentumType = AuctionMomentumType.NEUTRAL
    
    #     # Highest-priority active auction
    #     active_timeframe: str | None = None
    #     active_direction: AuctionDirection = (
    #         AuctionDirection.NEUTRAL
    #     )
    #     active_progress: float = 0.0
    def h7summary(self) -> dict:
        return {
            # "final at_htf": self.at_htf,
            # "final at_htf_level": self.at_htf_level,
            # "final previous direction": self.previous_direction,
            # "final active timeframe": self.active_timeframe,
            # "final active direction": self.active_direction,
            # "final active progress": self.active_progress,

            # "daily": self.daily.summary() if self.daily else None,
            "h7": self.h7.summary() if self.h7 else None,
            # "h4": self.h4.summary() if self.h4 else None,
            "h7_status": self.h7_status,
            # "h4_status": self.h4_status,
            # "daily_status": self.daily_status,
        }
    
    def h4summary(self) -> dict:
        return {
            # "final at_htf": self.at_htf,
            # "final at_htf_level": self.at_htf_level,
            # "final previous direction": self.previous_direction,
            # "final active timeframe": self.active_timeframe,
            # "final active direction": self.active_direction,
            # "final active progress": self.active_progress,

            # "daily": self.daily.summary() if self.daily else None,
            # "h7": self.h7.summary() if self.h7 else None,
            "h4": self.h4.summary() if self.h4 else None,
            # "h7_status": self.h7_status,
            "h4_status": self.h4_status,
            # "daily_status": self.daily_status,
        }
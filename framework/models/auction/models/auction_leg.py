from dataclasses import dataclass

from framework.models.auction.models.enums import AuctionDirection


@dataclass
class AuctionLeg:

    direction: AuctionDirection = (
        AuctionDirection.NEUTRAL
    )

    # Liquidity that anchors this leg
    origin = None

    # Current objective of this leg
    objective = None

    # Opposing liquidity used to measure progress
    opposing_liquidity = None

    progress: float = 0.0

    confirmed: bool = False

    completed: bool = False
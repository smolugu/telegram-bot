from dataclasses import dataclass, field
from typing import Optional

from framework.models.auction.models.auction_progress import AuctionProgress



@dataclass
class AuctionContext:

    # HTF Levels
    bullish_levels: list = field(default_factory=list)
    bearish_levels: list = field(default_factory=list)

    #
    # HTF Auctions
    #
    daily: AuctionProgress = field(
        default_factory=lambda: AuctionProgress("1d", "NEUTRAL")
    )

    h7: AuctionProgress = field(
        default_factory=lambda: AuctionProgress("7h", "NEUTRAL")
    )

    h4: AuctionProgress = field(
        default_factory=lambda: AuctionProgress("4h", "NEUTRAL")
    )
    
    bullish_swings: list = field(default_factory=list)
    bearish_swings: list = field(default_factory=list)

    bullish_fvgs: list = field(default_factory=list)
    bearish_fvgs: list = field(default_factory=list)

    bullish_vis: list = field(default_factory=list)
    bearish_vis: list = field(default_factory=list)

    bullish_cisds: list = field(default_factory=list)
    bearish_cisds: list = field(default_factory=list)

    #
    # nearest OPEN objectives
    #

    nearest_bullish_level = None
    nearest_bearish_level = None
    nearest_bullish_swing = None
    nearest_bearish_swing = None

    nearest_bullish_fvg = None
    nearest_bearish_fvg = None

    nearest_bullish_vi = None
    nearest_bearish_vi = None

    nearest_bullish_cisd = None
    nearest_bearish_cisd = None

    #
    # statistics
    #

    open_bullish_levels = 0
    open_bearish_levels = 0

    swept_bullish_levels = 0
    swept_bearish_levels = 0

    def summary(self) -> dict:
        return {
            "bullish_levels": self.bullish_levels,
            "bearish_levels": self.bearish_levels,
        }
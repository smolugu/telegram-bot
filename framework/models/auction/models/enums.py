from enum import Enum

class AuctionDirection(Enum):
    NEUTRAL = "NEUTRAL"
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"

class AuctionStageType(Enum):
    NEUTRAL="NEUTRAL"
    EARLY="EARLY"
    MID="MID"
    LATE="LATE"
    COMPLETE="COMPLETE"

class AuctionMomentumType(Enum):
    NEUTRAL="NEUTRAL"
    WEAK="WEAK"
    MEDIUM="MEDIUM"
    STRONG="STRONG"
    EXPLOSIVE="EXPLOSIVE"

class LiquidityType(Enum):
    EXTERNAL = "EXTERNAL"
    INTERNAL = "INTERNAL"

class LevelType(Enum):
    FVG = "FVG"
    VI = "VI"
    CISD = "CISD"
    SWING = "SWING"

class SwingType(str, Enum):
    BUY_SIDE = "BUY_SIDE"
    SELL_SIDE = "SELL_SIDE"

    @property
    def opposite(self):
        return (
            SwingType.SELL_SIDE
            if self == SwingType.BUY_SIDE
            else SwingType.BUY_SIDE
        )

class HTFSwingStatus(str, Enum):
    OPEN = "OPEN"
    TOUCHED = "TOUCHED"
    MITIGATED = "MITIGATED"
    SWEPT = "SWEPT"
    CLOSED = "CLOSED"

class HTFFvgStatus(str, Enum):
    OPEN = "OPEN"              # Newly created
    TOUCHED = "TOUCHED"        # Price enters the gap
    PARTIAL = "PARTIAL"        # Gap partially filled
    MITIGATED = "MITIGATED"    # Entire gap filled
    RECLAIMED = "RECLAIMED"          # Invalidated (optional)

class HTFViStatus(str, Enum):
    OPEN = "OPEN"              # Newly created
    TOUCHED = "TOUCHED"        # Price enters the gap
    PARTIAL = "PARTIAL"        # Gap partially filled
    MITIGATED = "MITIGATED"    # Entire gap filled
    RECLAIMED = "RECLAIMED"          # Invalidated (optional)

class HTFCisdStatus(str, Enum):
    OPEN = "OPEN"              # Newly created
    # PARTIAL = "PARTIAL"        # CISD partially tapped
    MITIGATED = "MITIGATED"    # Entire CISD tapped
    RECLAIMED = "RECLAIMED"    # Invalidated (optional) candle close above cisd body
    RCISD = "RCISD"            # Reclaimed CISD, close or high/low above /below lower/higher wick
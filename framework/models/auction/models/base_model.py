from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class LiquidityType(Enum):
    EXTERNAL = "EXTERNAL"
    INTERNAL = "INTERNAL"

class LevelType(Enum):
    FVG = "FVG"
    VI = "VI"
    CISD = "CISD"
    SWING = "SWING"

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

# @dataclass
# class HTFLevel:
#     timeframe: str
#     timestamp: datetime
#     status: HTFLevelStatus = HTFLevelStatus.OPEN
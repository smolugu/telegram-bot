from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class HTFLevelStatus(str, Enum):
    OPEN = "OPEN"
    TOUCHED = "TOUCHED"
    MITIGATED = "MITIGATED"
    SWEPT = "SWEPT"
    CLOSED = "CLOSED"

class FVGStatus(str, Enum):
    OPEN = "OPEN"              # Newly created
    TOUCHED = "TOUCHED"        # Price enters the gap
    PARTIAL = "PARTIAL"        # Gap partially filled
    MITIGATED = "MITIGATED"    # Entire gap filled
    RECLAIMED = "RECLAIMED"          # Invalidated (optional)

class VIStatus(str, Enum):
    OPEN = "OPEN"              # Newly created
    TOUCHED = "TOUCHED"        # Price enters the gap
    PARTIAL = "PARTIAL"        # Gap partially filled
    MITIGATED = "MITIGATED"    # Entire gap filled
    RECLAIMED = "RECLAIMED"          # Invalidated (optional)

class CISDStatus(str, Enum):
    OPEN = "OPEN"              # Newly created
    PARTIAL = "PARTIAL"        # CISD partially tapped
    MITIGATED = "MITIGATED"    # Entire CISD tapped and closed beyond
    RECLAIMED = "RECLAIMED"    # Invalidated (optional)
    RCISD = "RCISD"            # Reclaimed CISD

@dataclass
class HTFLevel:
    timeframe: str
    timestamp: datetime
    status: HTFLevelStatus = HTFLevelStatus.OPEN
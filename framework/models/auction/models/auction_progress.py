from dataclasses import dataclass
from typing import Optional

from enum import Enum

class AuctionDirection(Enum):
    NEUTRAL = "NEUTRAL"
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"

@dataclass
class AuctionProgress:

    timeframe: str                      # D, 7H, 4H

    previous_objective = None
    current_objective = None

    progress: float = 0.0               # 0.0 - 1.0

    confirmed_direction: str = AuctionDirection.NEUTRAL
    previous_direction: str = AuctionDirection.NEUTRAL
    confirmed: bool = False
    completed: bool = False

    at_htf: bool = False
    at_htf_level = None

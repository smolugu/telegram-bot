from dataclasses import dataclass
from data.models.auction.models.base_model import HTFLevel

@dataclass
class HTFCISD(HTFLevel):
    price: float
    bullish: bool
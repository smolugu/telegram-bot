from datetime import datetime
from data.models.auction.models.candle import Candle

def candle_from_dict(c):
    return Candle(
        time=datetime.fromisoformat(c["timestamp"]),
        open=c["open"],
        high=c["high"],
        low=c["low"],
        close=c["close"],
    )
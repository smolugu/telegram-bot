from datetime import datetime
from data.models.candle import Candle

def candle_from_dict(c):
    return Candle(
        timestamp=datetime.fromisoformat(c["timestamp"]),
        open=c["open"],
        high=c["high"],
        low=c["low"],
        close=c["close"],
        instrument="",
        timeframe=0,
        contract="",
        volume=c.get("volume", 0)
    )
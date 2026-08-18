from datetime import datetime
from data.models.candle import Candle

def candle_from_dict(c, instrument, contract, timeframe):
    timestamp = c["timestamp"]

    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp)
    return Candle(
        # timestamp=datetime.fromisoformat(c["timestamp"]),
        timestamp=timestamp,
        open=c["open"],
        high=c["high"],
        low=c["low"],
        close=c["close"],
        instrument=instrument,
        timeframe=timeframe,
        contract=contract,
        volume=c.get("volume", 0)
    )
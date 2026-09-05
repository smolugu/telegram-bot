from datetime import timezone
from typing import Callable

from data.models.candle import Candle
from data.models.trade import Trade

class MinuteCandleBuilder:
    def __init__(self, on_candle: Callable[[Candle], None]):
        self._on_candle = on_candle
        self._current_candles: dict[tuple[str, str], Candle] = {}

    

    def add_trade(self, trade: Trade) -> None:
        timestamp = trade.timestamp.astimezone(timezone.utc)

        bucket = timestamp.replace(
            second=0,
            microsecond=0,
        )

        key = (trade.instrument, trade.contract)

        current_candle = self._current_candles.get(key)

        # First trade for this instrument/contract
        if current_candle is None:
            self._current_candles[key] = Candle(
                instrument=trade.instrument,
                timeframe=1,
                timestamp=bucket,
                contract=trade.contract,
                open=trade.price,
                high=trade.price,
                low=trade.price,
                close=trade.price,
                volume=trade.volume,
            )
            return

        # Same minute — update current candle
        if bucket == current_candle.timestamp:
            self._current_candles[key] = Candle(
                instrument=current_candle.instrument,
                timeframe=1,
                timestamp=current_candle.timestamp,
                contract=current_candle.contract,
                open=current_candle.open,
                high=max(current_candle.high, trade.price),
                low=min(current_candle.low, trade.price),
                close=trade.price,
                volume=current_candle.volume + trade.volume,
            )
            return

        # New minute — finalize previous candle
        if bucket > current_candle.timestamp:
            # self._on_candle(current_candle)
            if (
                self._realtime_start_bucket is None
                or current_candle.timestamp > self._realtime_start_bucket
            ):
                self._on_candle(current_candle)

            self._current_candles[key] = Candle(
                instrument=trade.instrument,
                timeframe=1,
                timestamp=bucket,
                contract=trade.contract,
                open=trade.price,
                high=trade.price,
                low=trade.price,
                close=trade.price,
                volume=trade.volume,
            )
            return

        # Older/out-of-order trade
        print(
            f"WARNING: Ignoring out-of-order trade: "
            f"{trade.timestamp} < {current_candle.timestamp} "
            f"for {trade.instrument}/{trade.contract}"
        )

    def flush(self) -> None:
        """Emit all currently forming candles."""
        for candle in self._current_candles.values():
            self._on_candle(candle)

        self._current_candles.clear()
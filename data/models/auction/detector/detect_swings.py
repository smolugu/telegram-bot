from typing import List

from data.models.auction.models.candle import Candle
from data.models.auction.models.htf_swing import HTFSwing, SwingType


def detect_swings(
    candles: List[Candle],
    timeframe: str,
    pivot: int = 2,
) -> List[HTFSwing]:
    """
    Detect swing highs and swing lows.

    BUY_SIDE  = Swing High
    SELL_SIDE = Swing Low
    """

    swings: List[HTFSwing] = []

    if len(candles) < (pivot * 2 + 1):
        return swings

    for i in range(pivot, len(candles) - pivot):

        current = candles[i]

        # --------------------------------------------------
        # Swing High
        # --------------------------------------------------
        is_swing_high = True

        for j in range(i - pivot, i + pivot + 1):

            if j == i:
                continue

            if candles[j].high >= current.high:
                is_swing_high = False
                break

        if is_swing_high:

            swings.append(
                HTFSwing(
                    timeframe=timeframe,
                    swing_type=SwingType.BUY_SIDE,
                    price=current.high,
                    index=i,
                    timestamp=current.time,
                )
            )

        # --------------------------------------------------
        # Swing Low
        # --------------------------------------------------
        is_swing_low = True

        for j in range(i - pivot, i + pivot + 1):

            if j == i:
                continue

            if candles[j].low <= current.low:
                is_swing_low = False
                break

        if is_swing_low:

            swings.append(
                HTFSwing(
                    timeframe=timeframe,
                    swing_type=SwingType.SELL_SIDE,
                    price=current.low,
                    index=i,
                    timestamp=current.time,
                )
            )

    return swings
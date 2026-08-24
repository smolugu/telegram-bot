from typing import List

from data.models.candle import Candle
from framework.models.auction.models.htf_swing import HTFSwing, SwingType

HTF_TIMEFRAMES = {"1d", "7h", "4h"}


def detect_htf_swings(
    candles,
    timeframe,
):
    """
    Detect pivot=1 HTF swings from the last 3 candles.

    C1 = candles[-3]
    C2 = candles[-2]  # pivot candle
    C3 = candles[-1]  # confirmation candle
    """

    if len(candles) < 3:
        return []

    c1 = candles[-3]
    c2 = candles[-2]
    c3 = candles[-1]
    print("c1: ", c1)
    print("c2: ", c2)
    print("c3: ", c3)

    swings = []

    # ---------------------------------------------------------
    # Swing High
    # ---------------------------------------------------------

    if (
        c1.high< c2.high
        and c2.high > c3.high
    ):
        swings.append(
            HTFSwing(
                timeframe=timeframe,
                swing_type=SwingType.BUY_SIDE,
                price=c2.high,
                index=-2,
                timestamp=c2.timestamp,
                is_bullish=True,
                is_buy_side=True
            )
        )

    # ---------------------------------------------------------
    # Swing Low
    # ---------------------------------------------------------

    if (
        c1.low > c2.low
        and c2.low < c3.low
    ):
        swings.append(
            HTFSwing(
                timeframe=timeframe,
                swing_type=SwingType.SELL_SIDE,
                price=c2.low,
                index=-2,
                timestamp=c2.timestamp,
                is_bullish=False,
                is_buy_side=False
            )
        )

    return swings


def detect_swings(
    candles: List[Candle],
    timeframe: str,
    pivot=None,
) -> List[HTFSwing]:
    """
    Detect swing highs and swing lows.

    BUY_SIDE  = Swing High
    SELL_SIDE = Swing Low
    """
    # print("CANDLES PASSED TO SWING DETECTOR")

    # for candle in candles:
    #     if candle.timestamp.strftime("%Y-%m-%d %H:%M") in [
    #         "2026-08-16 18:00",
    #         "2026-08-16 22:00",
    #     ]:
    #         print("candlesss: ")
    #         print(candle)
    if pivot is None:
        pivot = 1 if timeframe in HTF_TIMEFRAMES else 2

    swings: List[HTFSwing] = []

    if len(candles) < (pivot * 2 + 1):
        return swings

    for i in range(pivot, len(candles) - pivot):

        current = candles[i]
        # print("swings: ", swings)
        # print("************************")

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
                    timestamp=current.timestamp,
                    is_bullish=True,
                    is_buy_side=True
                )
            )

        # --------------------------------------------------
        # Swing Low
        # --------------------------------------------------
        is_swing_low = True

        for j in range(i - pivot, i + pivot + 1):

            if j == i:
                continue
            # print(
            #     "SWING LOW CHECK:",
            #     "current:", current.timestamp,
            #     current.low,
            #     "compare:", candles[j].timestamp,
            #     candles[j].low,
            # )


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
                    timestamp=current.timestamp,
                    is_bullish=False,
                    is_buy_side=False
                )
            )

    return swings
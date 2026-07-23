from typing import List
import pandas as pd

from data.models.auction.models.htf_swing import HTFSwing

# from models.htf_swing import HTFSwing


def detect_swings(
    df,
    timeframe: str,
    pivot: int = 2,
) -> List[HTFSwing]:
    """
    Detect swing highs and lows.

    Required columns:
        High
        Low

    DataFrame index should contain timestamps.
    """

    swings: List[HTFSwing] = []

    highs = df["High"].values
    lows = df["Low"].values

    for i in range(pivot, len(df) - pivot):

        # -------------------------
        # Swing High
        # -------------------------
        window_high = highs[i - pivot : i + pivot + 1]

        if highs[i] == window_high.max():

            # Ignore duplicate highs
            if list(window_high).count(highs[i]) == 1:

                swings.append(
                    HTFSwing(
                        timeframe=timeframe,
                        swing_type="BUY_SIDE",
                        price=float(highs[i]),
                        index=i,
                        timestamp=df.index[i],
                    )
                )

        # -------------------------
        # Swing Low
        # -------------------------
        window_low = lows[i - pivot : i + pivot + 1]

        if lows[i] == window_low.min():

            if list(window_low).count(lows[i]) == 1:

                swings.append(
                    HTFSwing(
                        timeframe=timeframe,
                        swing_type="SELL_SIDE",
                        price=float(lows[i]),
                        index=i,
                        timestamp=df.index[i],
                    )
                )

    return swings
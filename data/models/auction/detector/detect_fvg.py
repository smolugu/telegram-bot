from data.models.auction.models.candle import Candle
from data.models.auction.models.htf_fvg import HTFFVG


def detect_fvg(
    candles: list[Candle],
    timeframe: str,
) -> list[HTFFVG]:

    fvgs = []

    for i in range(2, len(candles)):

        c1 = candles[i - 2]
        c2 = candles[i - 1]
        c3 = candles[i]

        # Bullish FVG
        if c1.high < c3.low:

            fvgs.append(
                HTFFVG(
                    timeframe=timeframe,
                    timestamp=c3.time,
                    upper=c3.low,
                    lower=c1.high,
                    is_bullish=True,
                )
            )

        # Bearish FVG
        elif c1.low > c3.high:

            fvgs.append(
                HTFFVG(
                    timeframe=timeframe,
                    timestamp=c3.time,
                    upper=c1.low,
                    lower=c3.high,
                    is_bullish=False,
                )
            )

    return fvgs
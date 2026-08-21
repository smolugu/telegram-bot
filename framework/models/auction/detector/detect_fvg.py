from data.models.candle import Candle
from framework.models.auction.models.htf_fvg import HTFFVG


def detect_htf_fvg(
    candles,
    timeframe,
):
    """
    Detect an FVG formed by the last 3 candles.

    Returns:
        []        if no FVG
        [HTFFVG]  if an FVG is formed
    """

    if len(candles) < 3:
        return []

    c1 = candles[-3]
    c2 = candles[-2]
    c3 = candles[-1]

    fvg = []

    # ---------------------------------------------------------
    # Bullish FVG
    # C3 Low > C1 High
    # ---------------------------------------------------------

    if c3.low > c1.high:

        fvg.append(
            HTFFVG(
                timeframe=timeframe,
                timestamp=c3.timestamp,
                upper=c3.low,
                lower=c1.high,
                price=c3.low,
                is_bullish=True,
                is_buy_side=False
            )
        )

    # ---------------------------------------------------------
    # Bearish FVG
    # C3 High < C1 Low
    # ---------------------------------------------------------

    elif c3.high < c1.low:

        fvg.append(
            HTFFVG(
                timeframe=timeframe,
                timestamp=c3.timestamp,
                upper=c1.low,
                lower=c3.high,
                price=c3.high,
                is_bullish=False,
                is_buy_side=True
            )
        )

    return fvg


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
                    timestamp=c3.timestamp,
                    upper=c3.low,
                    lower=c1.high,
                    price=c3.low,
                    is_bullish=True,
                    is_buy_side=False
                )
            )

        # Bearish FVG
        elif c1.low > c3.high:

            fvgs.append(
                HTFFVG(
                    timeframe=timeframe,
                    timestamp=c3.timestamp,
                    upper=c1.low,
                    lower=c3.high,
                    price=c3.high,
                    is_bullish=False,
                    is_buy_side=True
                )
            )

    return fvgs
from data.models.candle import Candle
from framework.models.auction.models.htf_vi import HTFVolumeImbalance


def detect_htf_vi(
    candles,
    timeframe,
):
    """
    Detect a VI formed by the last 2 candles.

    Returns:
        []       if no VI
        [HTFVI]  if a VI is formed
    """

    if len(candles) < 2:
        return []

    c1 = candles[-2]
    c2 = candles[-1]

    vi = []

    # ---------------------------------------------------------
    # Put your existing VI conditions here
    # ---------------------------------------------------------

    if (
        c2.open > c1.close
    ):
        vi.append(
            HTFVolumeImbalance(
                timeframe=timeframe,
                timestamp=c2.timestamp,
                upper=c2.open,
                lower=c1.close,
                is_bullish=True,
                price=c2.open,
            )
        )

    elif (
        c1.close > c2.open
    ):
        vi.append(
            HTFVolumeImbalance(
                timeframe=timeframe,
                timestamp=c2.timestamp,
                upper=c1.close,
                lower=c2.open,
                is_bullish=False,
                price=c2.open,
            )
        )

    return vi

def detect_vi(
    candles: list[Candle],
    timeframe: str,
) -> list[HTFVolumeImbalance]:

    vis = []

    for i in range(1, len(candles)):

        prev = candles[i - 1]
        curr = candles[i]

        # Bullish VI
        if prev.close < curr.open:

            vis.append(
                HTFVolumeImbalance(
                    timeframe=timeframe,
                    timestamp=curr.timestamp,
                    upper=curr.open,
                    lower=prev.close,
                    is_bullish=True,
                    price=curr.open,
                )
            )

        # Bearish VI
        elif prev.close > curr.open:

            vis.append(
                HTFVolumeImbalance(
                    timeframe=timeframe,
                    timestamp=curr.timestamp,
                    upper=prev.close,
                    lower=curr.open,
                    is_bullish=False,
                    price=curr.open,
                )
            )

    return vis
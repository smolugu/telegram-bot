from data.models.candle import Candle
from framework.models.auction.models.htf_vi import HTFVolumeImbalance


def detect_volume_imbalances(
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
                    timestamp=curr.time,
                    upper=curr.open,
                    lower=prev.close,
                    is_bullish=True,
                )
            )

        # Bearish VI
        elif prev.close > curr.open:

            vis.append(
                HTFVolumeImbalance(
                    timeframe=timeframe,
                    timestamp=curr.time,
                    upper=prev.close,
                    lower=curr.open,
                    is_bullish=False,
                )
            )

    return vis
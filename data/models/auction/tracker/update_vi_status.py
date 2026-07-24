from data.models.auction.models.base_model import VIStatus

from data.models.auction.models.candle import Candle
from data.models.auction.models.htf_vi import HTFVolumeImbalance



def update_VI_status(
    vis: list[HTFVolumeImbalance],
    candles: list[Candle],
) -> None:
    """
    Updates the status of every HTF FVG.
    """

    if not vis:
        return

    # Ensure chronological order
    candles = sorted(candles, key=lambda c: c.time)

    for vi in vis:

        if vi.status == VIStatus.RECLAIMED:
            continue

        for candle in candles:

            # Ignore candles before the swing formed
            if candle.time <= vi.timestamp:
                continue

            if vi.is_bullish: # bullish vi
                if candle.low == vi.upper:
                    vi.status = VIStatus.TOUCHED
                    break
                elif candle.low < vi.upper:
                    vi.status = VIStatus.PARTIAL
                    break
                elif candle.low <= vi.lower:
                    vi.status = VIStatus.MITIGATED
                    break
                elif candle.close <= vi.lower:
                    vi.status = VIStatus.RECLAIMED
                
            else:   # bearish fvg
                if candle.high == vi.lower:
                    vi.status = VIStatus.TOUCHED
                    break
                elif candle.high > vi.lower:
                    vi.status = VIStatus.PARTIAL
                    break
                elif candle.low >= vi.upper:
                    vi.status = VIStatus.MITIGATED
                    break
                elif candle.close >= vi.upper:
                    vi.status = VIStatus.RECLAIMED

                
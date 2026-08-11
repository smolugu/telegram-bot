from framework.models.auction.models.base_model import HTFViStatus

from data.models.candle import Candle
from framework.models.auction.models.htf_vi import HTFVolumeImbalance



def update_vi_status(
    vis: list[HTFVolumeImbalance],
    candles: list[Candle],
) -> None:
    """
    Updates the status of every HTF VI.
    """

    if not vis:
        return

    # Ensure chronological order
    candles = sorted(candles, key=lambda c: c.time)

    for vi in vis:

        if vi.status == HTFViStatus.RECLAIMED:
            continue

        for candle in candles:

            # Ignore candles before the VI formed
            if candle.timestamp <= vi.timestamp:
                continue

            if vi.is_bullish: # bullish vi
                # set is_swept flag
                if candle.low < vi.higher and not vi.is_swept:
                    vi.is_swept = True
                if candle.low == vi.upper:
                    vi.status = HTFViStatus.TOUCHED
                    vi.mitigated_time = candle.timestamp
                    break
                elif candle.low < vi.upper:
                    vi.status = HTFViStatus.PARTIAL
                    vi.mitigated_time = candle.timestamp
                    break
                elif candle.low <= vi.lower:
                    vi.status = HTFViStatus.MITIGATED
                    vi.mitigated_time = candle.timestamp
                    break
                elif candle.close <= vi.lower:
                    vi.status = HTFViStatus.RECLAIMED
                    vi.mitigated_time = candle.timestamp
                
            else:   # bearish fvg
                # set is_swept flag
                if candle.high > vi.lower and not vi.is_swept:
                    vi.is_swept = True
                if candle.high == vi.lower:
                    vi.status = HTFViStatus.TOUCHED
                    vi.mitigated_time = candle.timestamp
                    break
                elif candle.high > vi.lower:
                    vi.status = HTFViStatus.PARTIAL
                    vi.mitigated_time = candle.timestamp
                    break
                elif candle.low >= vi.upper:
                    vi.status = HTFViStatus.MITIGATED
                    vi.mitigated_time = candle.timestamp
                    break
                elif candle.close >= vi.upper:
                    vi.status = HTFViStatus.RECLAIMED
                    vi.mitigated_time = candle.timestamp

                
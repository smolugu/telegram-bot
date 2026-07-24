from data.models.auction.models.base_model import FVGStatus, HTFLevelStatus
from data.models.auction.models.candle import Candle
from data.models.auction.models.htf_fvg import HTFFVG


def update_FVG_status(
    fvgs: list[HTFFVG],
    candles: list[Candle],
) -> None:
    """
    Updates the status of every HTF FVG.
    """

    if not fvgs:
        return

    # Ensure chronological order
    candles = sorted(candles, key=lambda c: c.time)

    for fvg in fvgs:

        if fvg.status != FVGStatus.OPEN:
            continue

        for candle in candles:

            # Ignore candles before the swing formed
            if candle.time <= fvg.timestamp:
                continue

            if fvg.is_bullish: # bullish fvg
                if candle.low == fvg.upper:
                    fvg.status = FVGStatus.TOUCHED
                    break
                elif candle.low < fvg.upper:
                    fvg.status = FVGStatus.PARTIAL
                    break
                elif candle.low <= fvg.lower:
                    fvg.status = FVGStatus.MITIGATED
                    break
                elif candle.close <= fvg.lower:
                    fvg.status = FVGStatus.RECLAIMED
                
            else:   # bearish fvg
                if candle.high == fvg.lower:
                    fvg.status = FVGStatus.TOUCHED
                    break
                elif candle.high > fvg.lower:
                    fvg.status = FVGStatus.PARTIAL
                    break
                elif candle.low >= fvg.upper:
                    fvg.status = FVGStatus.MITIGATED
                    break
                elif candle.close >= fvg.upper:
                    fvg.status = FVGStatus.RECLAIMED

                
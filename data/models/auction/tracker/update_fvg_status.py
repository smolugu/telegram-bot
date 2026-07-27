from data.models.auction.models.base_model import FVGStatus, HTFLevelStatus
from data.datamodels.candle import Candle
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

            # Ignore candles before the FVG formed
            if candle.time <= fvg.timestamp:
                continue

            if fvg.is_bullish: # bullish fvg
                if candle.low == fvg.upper:
                    fvg.status = FVGStatus.TOUCHED
                    fvg.mitigated_time = candle.time
                    break
                elif candle.low < fvg.upper:
                    fvg.status = FVGStatus.PARTIAL
                    fvg.mitigated_time = candle.time
                    break
                elif candle.low <= fvg.lower:
                    fvg.status = FVGStatus.MITIGATED
                    fvg.mitigated_time = candle.time
                    break
                elif candle.close <= fvg.lower:
                    fvg.status = FVGStatus.RECLAIMED
                    fvg.mitigated_time = candle.time
                
            else:   # bearish fvg
                if candle.high == fvg.lower:
                    fvg.status = FVGStatus.TOUCHED
                    fvg.mitigated_time = candle.time
                    break
                elif candle.high > fvg.lower:
                    fvg.status = FVGStatus.PARTIAL
                    fvg.mitigated_time = candle.time
                    break
                elif candle.low >= fvg.upper:
                    fvg.status = FVGStatus.MITIGATED
                    fvg.mitigated_time = candle.time
                    break
                elif candle.close >= fvg.upper:
                    fvg.status = FVGStatus.RECLAIMED
                    fvg.mitigated_time = candle.time

                
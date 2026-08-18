from framework.models.auction.models.enums import HTFFvgStatus
from data.models.candle import Candle
from framework.models.auction.models.htf_fvg import HTFFVG


def update_fvg_status(
    fvgs: list[HTFFVG],
    candles: list[Candle],
) -> None:
    """
    Updates the status of every HTF FVG.
    """

    if not fvgs:
        return

    # Ensure chronological order
    candles = sorted(candles, key=lambda c: c.timestamp)

    for fvg in fvgs:

        if fvg.status != HTFFvgStatus.OPEN:
            continue

        for candle in candles:

            # Ignore candles before the FVG formed
            if candle.timestamp <= fvg.timestamp:
                continue

            if fvg.is_bullish: # bullish fvg
                # set is_swept flag
                if candle.low < fvg.upper and not fvg.is_swept:
                    fvg.is_swept = True

                if candle.low == fvg.upper:
                    fvg.status = HTFFvgStatus.TOUCHED
                    fvg.mitigation_time = candle.timestamp
                    break
                elif candle.low < fvg.upper:
                    fvg.status = HTFFvgStatus.PARTIAL
                    fvg.mitigation_time = candle.timestamp
                    break
                elif candle.low <= fvg.lower:
                    fvg.status = HTFFvgStatus.MITIGATED
                    fvg.mitigation_time = candle.timestamp
                    break
                elif candle.close <= fvg.lower:
                    fvg.status = HTFFvgStatus.RECLAIMED
                    fvg.mitigation_time = candle.timestamp
                
            else:   # bearish fvg
                # set is_swept flag
                if candle.high > fvg.lower and not fvg.is_swept:
                    fvg.is_swept = True
                if candle.high == fvg.lower:
                    fvg.status = HTFFvgStatus.TOUCHED
                    fvg.mitigation_time = candle.timestamp
                    break
                elif candle.high > fvg.lower:
                    fvg.status = HTFFvgStatus.PARTIAL
                    fvg.mitigation_time = candle.timestamp
                    break
                elif candle.low >= fvg.upper:
                    fvg.status = HTFFvgStatus.MITIGATED
                    fvg.mitigation_time = candle.timestamp
                    break
                elif candle.close >= fvg.upper:
                    fvg.status = HTFFvgStatus.RECLAIMED
                    fvg.mitigation_time = candle.timestamp

                
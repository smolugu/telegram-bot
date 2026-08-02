from framework.models.auction.models.base_model import CISDStatus
from data.models.candle import Candle
from framework.models.auction.models.htf_cisd import HTFCISD


def update_CISD_status(
    cisds: list[HTFCISD],
    candles: list[Candle],
) -> None:
    """
    Updates the status of every HTF CISD.
    """

    if not cisds:
        return

    # Ensure chronological order
    candles = sorted(candles, key=lambda c: c.time)

    for cisd in cisds:

        if cisd.status != CISDStatus.OPEN:
            continue

        for candle in candles:

            # Ignore candles before the cisd formed
            if candle.timestamp <= cisd.timestamp:
                continue

            if cisd.is_bullish: # bullish cisd
                if candle.close < cisd.lower_wick or candle.low < cisd.lower_wick:
                    cisd.status = CISDStatus.RCISD
                    cisd.mitigated_time = candle.timestamp
                    break
                elif candle.low < cisd.lower_wick:
                    cisd.status = CISDStatus.RCISD
                    cisd.mitigated_time = candle.timestamp
                    break
                elif candle.close < cisd.lower_body:
                    cisd.status = CISDStatus.RECLAIMED
                    cisd.mitigated_time = candle.timestamp
                    break
                elif candle.low < cisd.upper_body:
                    cisd.status = CISDStatus.MITIGATED
                    cisd.mitigated_time = candle.timestamp
                    break                
            else:   # bearish CISD
                if candle.close > cisd.upper_wick or candle.high > cisd.upper_wick:
                    cisd.status = CISDStatus.RCISD
                    cisd.mitigated_time = candle.timestamp
                    break
                elif candle.high > cisd.upper_wick:
                    cisd.status = CISDStatus.RCISD
                    cisd.mitigated_time = candle.timestamp
                    break
                elif candle.close > cisd.upper_body:
                    cisd.status = CISDStatus.RECLAIMED
                    cisd.mitigated_time = candle.timestamp
                    break
                elif candle.high > cisd.lower_body:
                    cisd.status = CISDStatus.MITIGATED
                    cisd.mitigated_time = candle.timestamp
                    break
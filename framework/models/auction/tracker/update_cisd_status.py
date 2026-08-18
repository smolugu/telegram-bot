from framework.models.auction.models.enums import HTFCisdStatus
from data.models.candle import Candle
from framework.models.auction.models.htf_cisd import HTFCISD


def update_cisd_status(
    cisds: list[HTFCISD],
    candles: list[Candle],
) -> None:
    """
    Updates the status of every HTF CISD.
    """

    if not cisds:
        return

    # Ensure chronological order
    candles = sorted(candles, key=lambda c: c.timestamp)

    for cisd in cisds:

        if cisd.status != HTFCisdStatus.OPEN:
            continue

        for candle in candles:

            # Ignore candles before the cisd formed
            if candle.timestamp <= cisd.timestamp:
                continue

            if cisd.is_bullish: # bullish cisd
                # set is_swept value
                if candle.close < cisd.upper and not cisd.is_swept:
                    cisd.is_swept = True
                if candle.close < cisd.lower_wick or candle.low < cisd.lower_wick:
                    cisd.status = HTFCisdStatus.RCISD
                    cisd.mitigation_time = candle.timestamp
                    break
                elif candle.low < cisd.lower_wick:
                    cisd.status = HTFCisdStatus.RCISD
                    cisd.mitigation_time = candle.timestamp
                    break
                elif candle.close < cisd.lower:
                    cisd.status = HTFCisdStatus.RECLAIMED
                    cisd.mitigation_time = candle.timestamp
                    break
                elif candle.low < cisd.upper:
                    cisd.status = HTFCisdStatus.MITIGATED
                    cisd.mitigation_time = candle.timestamp
                    break                
            else:   # bearish CISD
                # set is_swept value
                if candle.high > cisd.lower and not cisd.is_swept:
                    cisd.is_swept = True
                if candle.close > cisd.upper_wick or candle.high > cisd.upper_wick:
                    cisd.status = HTFCisdStatus.RCISD
                    cisd.mitigation_time = candle.timestamp
                    break
                elif candle.high > cisd.upper_wick:
                    cisd.status = HTFCisdStatus.RCISD
                    cisd.mitigation_time = candle.timestamp
                    break
                elif candle.close > cisd.upper:
                    cisd.status = HTFCisdStatus.RECLAIMED
                    cisd.mitigation_time = candle.timestamp
                    break
                elif candle.high > cisd.lower:
                    cisd.status = HTFCisdStatus.MITIGATED
                    cisd.mitigation_time = candle.timestamp
                    break
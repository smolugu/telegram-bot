from datetime import timedelta

from framework.models.auction.models.enums import HTFCisdStatus
from data.models.candle import Candle
from framework.models.auction.models.htf_cisd import HTFCISD


def update_cisd_status(
    cisds: list[HTFCISD],
    ltf_candles: list[Candle],
    htf_candles: list[Candle]
) -> None:
    """
    Updates the status of every HTF CISD.
    """

    if not cisds:
        return

    # Ensure chronological order
    # candles = sorted(candles, key=lambda c: c.timestamp)
    # ltf_candles = historical_candles.get('1m', [])
    # htf_candles = historical_candles.get(cisds[0].timeframe, [])
    for cisd in cisds:

        # if cisd.status != HTFCisdStatus.OPEN:
        #     continue

        for candle in ltf_candles:
            # Ignore candles before the cisd formed
            cisd_confirmation_time = cisd.timestamp
            if cisd.timeframe == "4h":
                cisd_confirmation_time = cisd.timestamp + timedelta(hours=4)
            elif cisd.timeframe == "7h":
                cisd_confirmation_time = cisd.timestamp + timedelta(hours=7)
            elif cisd.timeframe == '1d':
                cisd_confirmation_time = cisd.timestamp + timedelta(days=1)

            if candle.timestamp <= cisd_confirmation_time:
                continue
                
            if cisd.is_bullish: # bullish cisd
                # set is_swept value
                if (
                    candle.low < cisd.upper
                    and candle.open > cisd.upper
                    # and candle.low < cisd.upper < candle.high
                    and not cisd.is_swept
                ): 
                    cisd.is_swept=True
                
                elif (
                    candle.low < cisd.upper
                    and candle.open > cisd.lower
                ):
                    cisd.status = HTFCisdStatus.MITIGATED
                    cisd.mitigation_time = candle.timestamp
                    break                
            else:   # bearish CISD
                # set is_swept value
                if (
                    candle.high > cisd.lower 
                    and candle.open < cisd.lower
                ):
                    cisd.is_swept=True
                elif (
                    candle.high > cisd.lower
                    and candle.open < cisd.upper
                ):
                    cisd.status = HTFCisdStatus.MITIGATED
                    cisd.mitigation_time = candle.timestamp
                    break
                

    for cisd in cisds:
        for candle in htf_candles:
            # Ignore candles before the cisd formed
            cisd_confirmation_time = cisd.timestamp
            if cisd.timeframe == "4h":
                cisd_confirmation_time = cisd.timestamp + timedelta(hours=4)
            elif cisd.timeframe == "7h":
                cisd_confirmation_time = cisd.timestamp + timedelta(hours=7)
            elif cisd.timeframe == '1d':
                cisd_confirmation_time = cisd.timestamp + timedelta(days=1)

            if candle.timestamp <= cisd_confirmation_time:
                continue
            if cisd.is_bullish:
                if (
                    candle.open > cisd.lower_wick
                    and (
                        candle.close < cisd.lower_wick or candle.low < cisd.lower_wick
                    )
                    
                ):
                    cisd.status = HTFCisdStatus.RCISD
                    cisd.mitigation_time = candle.timestamp
                    break
                
                elif (
                    candle.close < cisd.lower
                    and candle.open > cisd.lower
                ):
                    cisd.status = HTFCisdStatus.RECLAIMED
                    cisd.mitigation_time = candle.timestamp
                    break
            else:
                if (
                    candle.open < cisd.upper_wick
                    and (
                        candle.close > cisd.upper_wick or candle.high > cisd.upper_wick
                    )        
                ):
                    cisd.status = HTFCisdStatus.RCISD
                    cisd.mitigation_time = candle.timestamp
                    break
                
                elif (
                    candle.close > cisd.upper
                    and candle.open < cisd.upper
                ):
                    cisd.status = HTFCisdStatus.RECLAIMED
                    cisd.mitigation_time = candle.timestamp
                    break


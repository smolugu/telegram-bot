from datetime import timedelta

from framework.models.auction.models.enums import HTFFvgStatus
from data.models.candle import Candle
from framework.models.auction.models.htf_fvg import HTFFVG


def update_fvg_status(
    fvgs: list[HTFFVG],
    # historical_candles,
    ltf_candles: list[Candle],
    htf_candles: list[Candle]
) -> None:
    """
    Updates the status of every HTF FVG.
    """

    if not fvgs:
        return

    # Ensure chronological order
    # candles = sorted(candles, key=lambda c: c.timestamp)
    # ltf_candles = historical_candles.get('1m', [])
    # htf_candles = historical_candles.get(fvgs[0].timeframe, [])
    for fvg in fvgs:

        # if fvg.status != HTFFvgStatus.OPEN:
        #     continue

        for candle in ltf_candles:

            # Ignore candles before the FVG formed
            fvg_confirmation_time = fvg.timestamp
            if fvg.timeframe == "4h":
                fvg_confirmation_time = fvg.timestamp + timedelta(hours=4)
            elif fvg.timeframe == "7h":
                fvg_confirmation_time = fvg.timestamp + timedelta(hours=7)
            elif fvg.timeframe == '1d':
                fvg_confirmation_time = fvg.timestamp + timedelta(days=1)

            if candle.timestamp <= fvg_confirmation_time:
                continue
            
            # candle should be interating with the fvg
            if fvg.is_bullish: # bullish fvg
                # set is_swept flag
                
                if (
                    candle.low < fvg.upper
                    and candle.open > fvg.upper
                    # and candle.low < fvg.upper < candle.high
                    and not fvg.is_swept
                ):
                    fvg.is_swept=True
                    fvg.is_touched=False

                if (
                    candle.low == fvg.upper
                    and candle.open > fvg.upper
                ):
                    fvg.status = HTFFvgStatus.TOUCHED
                    fvg.mitigation_time = candle.timestamp
                    fvg.is_touched=True
                    break
                elif (
                    candle.low < fvg.upper
                    and candle.open > fvg.lower
                ):
                    fvg.status = HTFFvgStatus.PARTIAL
                    fvg.mitigation_time = candle.timestamp
                    fvg.is_touched=False
                    break
                
                elif (
                    candle.low <= fvg.lower 
                    and candle.open > fvg.lower
                ):
                    fvg.status = HTFFvgStatus.MITIGATED
                    fvg.mitigation_time = candle.timestamp
                    fvg.is_touched=False
                    break

                # reclaimed can only be finalized with a 4h candle
                # elif candle.close <= fvg.lower:
                #     fvg.status = HTFFvgStatus.RECLAIMED
                #     fvg.mitigation_time = candle.timestamp
                
            else:   # bearish fvg
                # set is_swept flag
                if (
                    candle.high > fvg.lower
                    and candle.open < fvg.lower
                    and not fvg.is_swept
                ):
                    fvg.is_swept = True
                    fvg.is_touched = False

                if (
                    candle.high == fvg.lower
                    and candle.open < fvg.lower
                ): 
                    fvg.status = HTFFvgStatus.TOUCHED
                    fvg.mitigation_time = candle.timestamp
                    fvg.is_touched=True
                    break
                elif (
                    candle.high > fvg.lower
                    and candle.open < fvg.upper
                ):
                    fvg.status = HTFFvgStatus.PARTIAL
                    fvg.mitigation_time = candle.timestamp
                    fvg.is_touched=False
                    break
                elif candle.high >= fvg.upper:
                    fvg.status = HTFFvgStatus.MITIGATED
                    fvg.mitigation_time = candle.timestamp
                    fvg.is_touched=False
                    break

    for fvg in fvgs:
        # process through htf timeframe candles to set RECLAIMED status
        for candle in htf_candles:

            # Ignore candles before the FVG formed
            fvg_confirmation_time = fvg.timestamp
            if fvg.timeframe == "4h":
                fvg_confirmation_time = fvg.timestamp + timedelta(hours=4)
            elif fvg.timeframe == "7h":
                fvg_confirmation_time = fvg.timestamp + timedelta(hours=7)
            elif fvg.timeframe == '1d':
                fvg_confirmation_time = fvg.timestamp + timedelta(days=1)

            if candle.timestamp <= fvg_confirmation_time:
                continue
            
            # candle should be interating with the fvg
            if fvg.is_bullish: # bullish fvg
                # set is_swept flag
                
                if candle.close <= fvg.lower:
                    fvg.status=HTFFvgStatus.RECLAIMED
                    break

                
            else:   # bearish fvg
                # set is_swept flag
                if candle.close >= fvg.upper:
                    fvg.status = HTFFvgStatus.RECLAIMED
                    break

                
from datetime import timedelta

from framework.models.auction.models.enums import HTFViStatus

from data.models.candle import Candle
from framework.models.auction.models.htf_vi import HTFVolumeImbalance


def update_vi_status(
    vis: list[HTFVolumeImbalance],
    ltf_candles: list[Candle],
    htf_candles: list[Candle]
) -> None:
    """
    Updates the status of every HTF VI.
    """

    if not vis:
        return

    # Ensure chronological order
    # candles = sorted(candles, key=lambda c: c.timestamp)
    # ltf_candles = historical_candles.get('1m', [])
    # htf_candles = historical_candles.get(vis[0].timeframe, [])
    for vi in vis:

        for candle in ltf_candles:

            # Ignore candles before the FVG formed
            vi_confirmation_time = vi.timestamp
            if vi.timeframe == "4h":
                vi_confirmation_time = vi.timestamp + timedelta(hours=4)
            elif vi.timeframe == "7h":
                vi_confirmation_time = vi.timestamp + timedelta(hours=7)
            elif vi.timeframe == '1d':
                vi_confirmation_time = vi.timestamp + timedelta(days=1)

            if candle.timestamp <= vi_confirmation_time:
                continue
            
            # candle should be interating with the fvg
            if vi.is_bullish: # bullish vi
                # set is_swept flag
                
                if (
                    candle.low < vi.upper
                    and candle.open > vi.upper
                    # and candle.low < vi.upper < candle.high
                    and not vi.is_swept
                ):
                    vi.is_swept=True
                    vi.is_touched=False

                if (
                    candle.low == vi.upper
                    and candle.open > vi.upper
                ):
                    vi.status = HTFViStatus.TOUCHED
                    vi.mitigation_time = candle.timestamp
                    vi.is_touched=True
                    break
                elif (
                    candle.low < vi.upper
                    and candle.open > vi.lower
                ):
                    vi.status = HTFViStatus.PARTIAL
                    vi.mitigation_time = candle.timestamp
                    vi.is_touched=False
                    break
                
                elif (
                    candle.low <= vi.lower 
                    and candle.open > vi.lower
                ):
                    vi.status = HTFViStatus.MITIGATED
                    vi.mitigation_time = candle.timestamp
                    vi.is_touched=False
                    break

                # reclaimed can only be finalized with a 4h candle
                # elif candle.close <= vi.lower:
                #     vi.status = HTFViStatus.RECLAIMED
                #     vi.mitigation_time = candle.timestamp
                
            else:   # bearish fvg
                # set is_swept flag
                if (
                    candle.high > vi.lower
                    and candle.open < vi.lower
                    and not vi.is_swept
                ):
                    vi.is_swept = True
                    vi.is_touched = False

                if (
                    candle.high == vi.lower
                    and candle.open < vi.lower
                ): 
                    vi.status = HTFViStatus.TOUCHED
                    vi.mitigation_time = candle.timestamp
                    vi.is_touched=True
                    break
                elif (
                    candle.high > vi.lower
                    and candle.open < vi.upper
                ):
                    vi.status = HTFViStatus.PARTIAL
                    vi.mitigation_time = candle.timestamp
                    vi.is_touched=False
                    break
                elif candle.high >= vi.upper:
                    vi.status = HTFViStatus.MITIGATED
                    vi.mitigation_time = candle.timestamp
                    vi.is_touched=False
                    break
    for vi in vis:         
        # process through htf timeframe candles to set RECLAIMED status
        for candle in htf_candles:
        
            # Ignore candles before the FVG formed
            vi_confirmation_time = vi.timestamp
            if vi.timeframe == "4h":
                vi_confirmation_time = vi.timestamp + timedelta(hours=4)
            elif vi.timeframe == "7h":
                vi_confirmation_time = vi.timestamp + timedelta(hours=7)
            elif vi.timeframe == '1d':
                vi_confirmation_time = vi.timestamp + timedelta(days=1)

            if candle.timestamp <= vi_confirmation_time:
                continue
            # candle should be interating with the fvg
            if vi.is_bullish: # bullish fvg
                # set is_swept flag
                
                if candle.close <= vi.lower:
                    vi.status=HTFViStatus.RECLAIMED
                    break

                
            else:   # bearish fvg
                # set is_swept flag
                if candle.close >= vi.upper:
                    vi.status = HTFViStatus.RECLAIMED
                    break

                
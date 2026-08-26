from datetime import timedelta

from framework.models.auction.models.enums import HTFSwingStatus
from data.models.candle import Candle
from framework.models.auction.models.htf_swing import HTFSwing, SwingType


def update_swing_status(
    swings: list[HTFSwing],
    candles: list[Candle],
) -> None:
    """
    Updates the status of every HTF swing.

    HIGH swing:
        OPEN -> MITIGATED when price trades above the swing high.

    LOW swing:
        OPEN -> MITIGATED when price trades below the swing low.

    Status is updated in-place.
    """

    if not swings:
        return

    # Ensure chronological order
    # candles = sorted(candles, key=lambda c: c.timestamp)

    for swing in swings:

        if swing.status != HTFSwingStatus.OPEN:
            continue

        for candle in candles:

            # Ignore candles before the swing formed
            swing_confirmation_time = (
                swing.timestamp + timedelta(hours=8)
            )
            if swing.timeframe == "4h":
                swing_confirmation_time = swing.timestamp + timedelta(hours=8)
            elif swing.timeframe == "7h":
                swing_confirmation_time = swing.timestamp + timedelta(hours=14)
            elif swing.timeframe == "1d":
                swing_confirmation_time = swing.timestamp + timedelta(days=2)

            if candle.timestamp <= swing_confirmation_time:
                continue
            
            if swing.swing_type == SwingType.BUY_SIDE:
                # set is_swept flag
                if (
                    candle.high > swing.price
                    and candle.low < swing.price < candle.high
                    and candle.open < swing.price
                    and not swing.is_swept

                ):
                    swing.is_swept = True
                    swing.status = HTFSwingStatus.SWEPT
                    swing.mitigation_time = candle.timestamp
                    swing.is_touched = False
                    swing.is_mitigated=True
                    break
                elif (
                    candle.high == swing.price
                    and candle.open < swing.price
                    and not swing.is_swept
                ):
                    swing.status = HTFSwingStatus.TOUCHED
                    swing.mitigation_time=candle.timestamp
                    swing.is_touched=True
                    swing.is_mitigated=True
                    break

            else:   # LOW
                # set is_swept flag
                if (
                    candle.low < swing.price 
                    and candle.open > swing.price
                    and candle.low < swing.price < candle.high
                    and not swing.is_swept
                ):
                    swing.is_swept = True
                    swing.status = HTFSwingStatus.SWEPT
                    swing.mitigation_time = candle.timestamp
                    swing.is_touched=False
                    swing.is_mitigated=True
                    break

                elif (
                    candle.low == swing.price
                    and candle.open > swing.price
                    and not swing.is_swept
                ):
                    swing.status = HTFSwingStatus.TOUCHED
                    swing.mitigation_time = candle.timestamp
                    swing.is_touched=True
                    swing.is_mitigated=True
                    break
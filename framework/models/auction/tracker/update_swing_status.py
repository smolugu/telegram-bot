from framework.models.auction.models.base_model import HTFSwingStatus
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
    candles = sorted(candles, key=lambda c: c.time)

    for swing in swings:

        if swing.status != HTFSwingStatus.OPEN:
            continue

        for candle in candles:

            # Ignore candles before the swing formed
            if candle.timestamp <= swing.timestamp:
                continue

            if swing.swing_type == SwingType.BUY_SIDE:
                # set is_swept flag
                if candle.high > swing.price and not swing.is_swept:
                    swing.is_swept = True
                if candle.high > swing.price:
                    swing.status = HTFSwingStatus.SWEPT
                    swing.mitigated_time = candle.timestamp
                    break
                elif candle.high == swing.price:
                    swing.status = HTFSwingStatus.TOUCHED
                    swing.mitigated_time = candle.timestamp
                    break

            else:   # LOW
                # set is_swept flag
                if candle.low < swing.price and not swing.is_swept:
                    swing.is_swept = True

                if candle.low < swing.price:
                    swing.status = HTFSwingStatus.SWEPT
                    swing.mitigated_time = candle.timestamp
                    break
                elif candle.low == swing.price:
                    swing.status = HTFSwingStatus.TOUCHED
                    swing.mitigated_time = candle.timestamp
                    break
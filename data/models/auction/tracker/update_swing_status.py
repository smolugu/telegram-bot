from data.models.auction.models.base_model import HTFLevelStatus
from data.models.auction.models.candle import Candle
from data.models.auction.models.htf_swing import HTFSwing, SwingType


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

        if swing.status != HTFLevelStatus.OPEN:
            continue

        for candle in candles:

            # Ignore candles before the swing formed
            if candle.time <= swing.timestamp:
                continue

            if swing.swing_type == SwingType.BUY_SIDE:

                if candle.high > swing.price:
                    swing.status = HTFLevelStatus.SWEPT
                    break
                elif candle.high == swing.price:
                    swing.status = HTFLevelStatus.TOUCHED
                    break

            else:   # LOW

                if candle.low < swing.price:
                    swing.status = HTFLevelStatus.SWEPT
                    break
                elif candle.low == swing.price:
                    swing.status = HTFLevelStatus.TOUCHED
                    break
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

    BUY-SIDE / HIGH swing:
        OPEN -> TOUCHED when price first touches the swing level.
        OPEN/TOUCHED -> SWEPT when price subsequently trades through
        the swing level.

    SELL-SIDE / LOW swing:
        OPEN -> TOUCHED when price first touches the swing level.
        OPEN/TOUCHED -> SWEPT when price subsequently trades through
        the swing level.

    Important:
        A touch does NOT mean the swing has been swept.

        A swing can therefore transition:

            OPEN -> TOUCHED -> SWEPT

        A candle that opens directly beyond the swing level after the
        previous candle was completely on the opposite side is treated
        as a sweep.

        Once price is already beyond the level, subsequent candles do
        not generate another sweep.

    Status is updated in-place.
    """

    if not swings or not candles:
        return

    # Ensure chronological order
    candles = sorted(candles, key=lambda c: c.timestamp)

    for swing in swings:

        # Once swept, the swing has completed its lifecycle.
        if swing.status == HTFSwingStatus.SWEPT:
            continue

        # ---------------------------------------------------------
        # Determine when the swing becomes eligible for interaction
        # ---------------------------------------------------------

        if swing.timeframe == "4h":
            swing_confirmation_time = (
                swing.timestamp + timedelta(hours=8)
            )

        elif swing.timeframe == "7h":
            swing_confirmation_time = (
                swing.timestamp + timedelta(hours=14)
            )

        elif swing.timeframe == "1d":
            swing_confirmation_time = (
                swing.timestamp + timedelta(days=2)
            )

        else:
            raise ValueError(
                f"Unsupported swing timeframe: {swing.timeframe}"
            )

        # ---------------------------------------------------------
        # Need a previous candle because sweep detection depends
        # on whether price was completely on the opposite side
        # of the swing before the current candle.
        # ---------------------------------------------------------

        for i in range(1, len(candles)):

            previous_candle = candles[i - 1]
            candle = candles[i]

            # Ignore candles before the swing was confirmed
            if candle.timestamp <= swing_confirmation_time:
                continue

            # -----------------------------------------------------
            # BUY-SIDE / HIGH SWING
            # -----------------------------------------------------

            if swing.swing_type == SwingType.BUY_SIDE:

                # -------------------------------------------------
                # We only care about the FIRST interaction after
                # price was completely below the swing.
                #
                # If previous candle was completely below:
                #
                #     previous.high < swing.price
                #
                # and current candle reaches the level:
                #
                #     current.high == swing.price
                #
                # -> TOUCHED
                #
                # If current candle exceeds it:
                #
                #     current.high > swing.price
                #
                # -> SWEPT
                # -------------------------------------------------

                if previous_candle.high < swing.price:

                    # ---------------------------------------------
                    # Exact touch
                    # ---------------------------------------------

                    if candle.high == swing.price:

                        swing.status = HTFSwingStatus.TOUCHED
                        swing.mitigation_time = candle.timestamp
                        swing.is_touched = True
                        swing.is_mitigated = True

                        # Do NOT mark swept.
                        # Continue looking for a future sweep.
                        continue

                    # ---------------------------------------------
                    # Price penetrated the swing
                    # ---------------------------------------------

                    elif candle.high > swing.price:

                        swing.is_swept = True
                        swing.status = HTFSwingStatus.SWEPT
                        swing.mitigation_time = candle.timestamp
                        swing.is_touched = False
                        swing.is_mitigated = True

                        break

            # -----------------------------------------------------
            # SELL-SIDE / LOW SWING
            # -----------------------------------------------------

            else:

                # -------------------------------------------------
                # We only care about the FIRST interaction after
                # price was completely above the swing.
                #
                # If previous candle was completely above:
                #
                #     previous.low > swing.price
                #
                # and current candle reaches the level:
                #
                #     current.low == swing.price
                #
                # -> TOUCHED
                #
                # If current candle goes below it:
                #
                #     current.low < swing.price
                #
                # -> SWEPT
                # -------------------------------------------------

                if previous_candle.low > swing.price:

                    # ---------------------------------------------
                    # Exact touch
                    # ---------------------------------------------

                    if candle.low == swing.price:

                        swing.status = HTFSwingStatus.TOUCHED
                        swing.mitigation_time = candle.timestamp
                        swing.is_touched = True
                        swing.is_mitigated = True

                        # Do NOT mark swept.
                        # Continue looking for a future sweep.
                        continue

                    # ---------------------------------------------
                    # Price penetrated the swing
                    # ---------------------------------------------

                    elif candle.low < swing.price:

                        swing.is_swept = True
                        swing.status = HTFSwingStatus.SWEPT
                        swing.mitigation_time = candle.timestamp
                        swing.is_touched = False
                        swing.is_mitigated = True

                        break
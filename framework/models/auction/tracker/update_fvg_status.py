from datetime import timedelta

from framework.models.auction.models.enums import HTFFvgStatus
from data.models.candle import Candle
from framework.models.auction.models.htf_fvg import HTFFVG


def update_fvg_status(
    fvgs: list[HTFFVG],
    ltf_candles: list[Candle],
    htf_candles: list[Candle],
) -> None:
    """
    Updates the status of every HTF FVG.

    Bullish FVG:

        OPEN
          |
          | price touches upper boundary
          v
        TOUCHED
          |
          | price enters the FVG
          v
        PARTIAL
          |
          | price reaches lower boundary
          v
        MITIGATED
          |
          | HTF candle closes below lower boundary
          v
        RECLAIMED


    Bearish FVG:

        OPEN
          |
          | price touches lower boundary
          v
        TOUCHED
          |
          | price enters the FVG
          v
        PARTIAL
          |
          | price reaches upper boundary
          v
        MITIGATED
          |
          | HTF candle closes above upper boundary
          v
        RECLAIMED


    Important:

    - A touch does NOT mean mitigation.
    - A partial penetration does NOT mean mitigation.
    - Reaching the opposite boundary means MITIGATED.
    - RECLAIMED requires an HTF candle close beyond the FVG.
    - A candle can open directly inside or beyond the FVG.
    """

    if not fvgs:
        return

    if not ltf_candles and not htf_candles:
        return

    # ---------------------------------------------------------
    # Ensure chronological order
    # ---------------------------------------------------------

    ltf_candles = sorted(
        ltf_candles,
        key=lambda c: c.timestamp,
    )

    htf_candles = sorted(
        htf_candles,
        key=lambda c: c.timestamp,
    )

    # =========================================================
    # LTF PROCESSING
    # =========================================================

    for fvg in fvgs:

        # -----------------------------------------------------
        # Once reclaimed, the FVG lifecycle is complete.
        # -----------------------------------------------------

        if fvg.status == HTFFvgStatus.RECLAIMED or fvg.status == HTFFvgStatus.MITIGATED:
            continue

        # -----------------------------------------------------
        # Determine FVG confirmation time
        # -----------------------------------------------------

        if fvg.timeframe == "4h":
            fvg_confirmation_time = (
                fvg.timestamp + timedelta(hours=4)
            )

        elif fvg.timeframe == "7h":
            fvg_confirmation_time = (
                fvg.timestamp + timedelta(hours=7)
            )

        elif fvg.timeframe == "1d":
            fvg_confirmation_time = (
                fvg.timestamp + timedelta(days=1)
            )

        else:
            raise ValueError(
                f"Unsupported FVG timeframe: {fvg.timeframe}"
            )

        # -----------------------------------------------------
        # We need the previous candle to determine whether the
        # current candle is the first interaction with the FVG.
        # -----------------------------------------------------

        for i in range(1, len(ltf_candles)):

            previous_candle = ltf_candles[i - 1]
            candle = ltf_candles[i]

            # -------------------------------------------------
            # Ignore candles before FVG confirmation
            # -------------------------------------------------

            if candle.timestamp <= fvg_confirmation_time:
                continue

            # =================================================
            # BULLISH FVG
            # =================================================

            if fvg.is_bullish:

                # -------------------------------------------------
                # Previous candle completely ABOVE the FVG
                #
                # This establishes that the current candle is
                # potentially the first interaction with the FVG.
                # -------------------------------------------------

                if previous_candle.low > fvg.upper:

                    # ---------------------------------------------
                    # Exact touch of upper boundary
                    #
                    # Example:
                    #
                    # previous low = 20,110
                    # current low  = 20,100
                    #
                    # FVG upper = 20,100
                    # ---------------------------------------------

                    if candle.low == fvg.upper:

                        fvg.status = HTFFvgStatus.TOUCHED
                        # First interaction with the FVG
                        if not fvg.is_mitigated:
                            fvg.mitigation_time = candle.timestamp
                        fvg.is_touched = True
                        fvg.is_mitigated = True
                        continue

                    # ---------------------------------------------
                    # Price entered the FVG
                    #
                    # upper > low > lower
                    #
                    # This is a partial mitigation.
                    # ---------------------------------------------

                    elif (
                        fvg.lower < candle.low < fvg.upper
                    ):

                        fvg.status = HTFFvgStatus.PARTIAL
                        # First interaction with the FVG
                        if not fvg.is_mitigated:
                            fvg.mitigation_time = candle.timestamp
                        fvg.is_touched = False
                        fvg.is_mitigated = True

                        continue

                    # ---------------------------------------------
                    # Price jumped directly through the FVG
                    # and reached/passed the lower boundary.
                    #
                    # This is immediately MITIGATED.
                    # ---------------------------------------------

                    elif candle.low <= fvg.lower:

                        fvg.status = HTFFvgStatus.MITIGATED
                        # First interaction with the FVG
                        if not fvg.is_mitigated:
                            fvg.mitigation_time = candle.timestamp
                        fvg.is_touched = False
                        fvg.is_mitigated = True

                        continue

                # -------------------------------------------------
                # If the FVG has already been touched/partially
                # entered, allow a later candle to progress it.
                # -------------------------------------------------

                if fvg.status in (
                    HTFFvgStatus.TOUCHED,
                    HTFFvgStatus.PARTIAL,
                ):

                    # ---------------------------------------------
                    # Reached lower boundary
                    # ---------------------------------------------

                    if candle.low <= fvg.lower:

                        fvg.status = HTFFvgStatus.MITIGATED
                        # First interaction with the FVG
                        if not fvg.is_mitigated:
                            fvg.mitigation_time = candle.timestamp
                        fvg.is_touched = False
                        fvg.is_mitigated = True
                        continue

                    # ---------------------------------------------
                    # Still inside FVG
                    #
                    # Ensure PARTIAL remains the state.
                    # ---------------------------------------------

                    if (
                        fvg.lower < candle.low < fvg.upper
                    ):

                        fvg.status = HTFFvgStatus.PARTIAL
                        fvg.is_touched = False
                        # First interaction with the FVG
                        if not fvg.is_mitigated:
                            fvg.mitigation_time = candle.timestamp
                        fvg.is_mitigated = True

            # =================================================
            # BEARISH FVG
            # =================================================

            else:

                # -------------------------------------------------
                # Previous candle completely BELOW the FVG
                # -------------------------------------------------

                if previous_candle.high < fvg.lower:

                    # ---------------------------------------------
                    # Exact touch of lower boundary
                    # ---------------------------------------------

                    if candle.high == fvg.lower:

                        fvg.status = HTFFvgStatus.TOUCHED
                        # First interaction with the FVG
                        if not fvg.is_mitigated:
                            fvg.mitigation_time = candle.timestamp
                        fvg.is_touched = True
                        fvg.is_mitigated = True

                        # Touch is NOT mitigation.
                        continue

                    # ---------------------------------------------
                    # Price entered the FVG
                    #
                    # lower < high < upper
                    # ---------------------------------------------

                    elif (
                        fvg.lower < candle.high < fvg.upper
                    ):

                        fvg.status = HTFFvgStatus.PARTIAL
                        # First interaction with the FVG
                        if not fvg.is_mitigated:
                            fvg.mitigation_time = candle.timestamp
                        fvg.is_touched = False
                        fvg.is_mitigated = True

                        continue

                    # ---------------------------------------------
                    # Price jumped directly through the FVG
                    # and reached/passed upper boundary.
                    # ---------------------------------------------

                    elif candle.high >= fvg.upper:

                        fvg.status = HTFFvgStatus.MITIGATED
                        # First interaction with the FVG
                        if not fvg.is_mitigated:
                            fvg.mitigation_time = candle.timestamp
                        fvg.is_touched = False
                        fvg.is_mitigated = True

                        continue

                # -------------------------------------------------
                # Already touched / partially entered
                # -------------------------------------------------

                if fvg.status in (
                    HTFFvgStatus.TOUCHED,
                    HTFFvgStatus.PARTIAL,
                ):

                    # ---------------------------------------------
                    # Reached upper boundary
                    # ---------------------------------------------

                    if candle.high >= fvg.upper:

                        fvg.status = HTFFvgStatus.MITIGATED
                        # First interaction with the FVG
                        if not fvg.is_mitigated:
                            fvg.mitigation_time = candle.timestamp
                        fvg.is_touched = False
                        fvg.is_mitigated = True

                        continue

                    # ---------------------------------------------
                    # Still inside FVG
                    # ---------------------------------------------

                    if (
                        fvg.lower < candle.high < fvg.upper
                    ):

                        fvg.status = HTFFvgStatus.PARTIAL
                        fvg.is_touched = False
                        # First interaction with the FVG
                        if not fvg.is_mitigated:
                            fvg.mitigation_time = candle.timestamp
                        fvg.is_mitigated = True

    # =========================================================
    # HTF RECLAIM PROCESSING
    # =========================================================

    for fvg in fvgs:

        # -----------------------------------------------------
        # FVG not mitigated by ltf candles
        # -----------------------------------------------------
        
        if fvg.status == HTFFvgStatus.RECLAIMED:
            continue

        # -----------------------------------------------------
        # Determine FVG confirmation time
        # -----------------------------------------------------

        if fvg.timeframe == "4h":
            fvg_confirmation_time = (
                fvg.timestamp + timedelta(hours=4)
            )

        elif fvg.timeframe == "7h":
            fvg_confirmation_time = (
                fvg.timestamp + timedelta(hours=7)
            )

        elif fvg.timeframe == "1d":
            fvg_confirmation_time = (
                fvg.timestamp + timedelta(days=1)
            )

        else:
            raise ValueError(
                f"Unsupported FVG timeframe: {fvg.timeframe}"
            )

        # -----------------------------------------------------
        # Find first qualifying HTF reclaim
        # -----------------------------------------------------

        for candle in htf_candles:

            if candle.timestamp <= fvg_confirmation_time:
                continue

            # -------------------------------------------------
            # Bullish FVG:
            # HTF close below lower boundary
            # -------------------------------------------------

            if fvg.is_bullish:

                if candle.close <= fvg.lower:

                    fvg.status = HTFFvgStatus.RECLAIMED
                    if not fvg.is_mitigated:
                        fvg.mitigation_time = candle.timestamp
                        fvg.is_mitigated = True
                    fvg.is_touched = False

                    break

            # -------------------------------------------------
            # Bearish FVG:
            # HTF close above upper boundary
            # -------------------------------------------------

            else:

                if candle.close >= fvg.upper:

                    fvg.status = HTFFvgStatus.RECLAIMED
                    if not fvg.is_mitigated:
                        fvg.mitigation_time = candle.timestamp
                        fvg.is_mitigated = True
                    fvg.is_touched = False

                    break

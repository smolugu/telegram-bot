from datetime import timedelta

from framework.models.auction.models.enums import HTFViStatus

from data.models.candle import Candle
from framework.models.auction.models.htf_vi import HTFVolumeImbalance

def update_vi_status(
    vis: list[HTFVolumeImbalance],
    ltf_candles: list[Candle],
    htf_candles: list[Candle],
) -> None:
    """
    Updates the status of every HTF Volume Imbalance (VI).

    Bullish VI:

        OPEN
          |
          | price touches upper boundary
          v
        TOUCHED
          |
          | price enters the VI
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


    Bearish VI:

        OPEN
          |
          | price touches lower boundary
          v
        TOUCHED
          |
          | price enters the VI
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


    is_mitigated:
        True once price first interacts with the VI.

    mitigation_time:
        Timestamp of the FIRST interaction with the VI.
        It is never overwritten by subsequent interactions or reclaim.
    """

    if not vis:
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

    for vi in vis:

        # -----------------------------------------------------
        # Once reclaimed, lifecycle is complete.
        # -----------------------------------------------------

        if vi.status == HTFViStatus.RECLAIMED or vi.status == HTFViStatus.MITIGATED:
            continue

        # -----------------------------------------------------
        # Determine VI confirmation time
        # -----------------------------------------------------

        if vi.timeframe == "4h":
            vi_confirmation_time = (
                vi.timestamp + timedelta(hours=4)
            )

        elif vi.timeframe == "7h":
            vi_confirmation_time = (
                vi.timestamp + timedelta(hours=7)
            )

        elif vi.timeframe == "1d":
            vi_confirmation_time = (
                vi.timestamp + timedelta(days=1)
            )

        else:
            raise ValueError(
                f"Unsupported VI timeframe: {vi.timeframe}"
            )

        # -----------------------------------------------------
        # Need previous candle to determine whether the current
        # candle is the first interaction with the VI.
        # -----------------------------------------------------

        for i in range(1, len(ltf_candles)):

            previous_candle = ltf_candles[i - 1]
            candle = ltf_candles[i]

            if candle.timestamp <= vi_confirmation_time:
                continue

            # =================================================
            # BULLISH VI
            # =================================================

            if vi.is_bullish:

                # -------------------------------------------------
                # Previous candle completely ABOVE VI
                # -------------------------------------------------

                if previous_candle.low > vi.upper:

                    # ---------------------------------------------
                    # Exact touch of upper boundary
                    # ---------------------------------------------

                    if candle.low == vi.upper:

                        if not vi.is_mitigated:
                            vi.mitigation_time = candle.timestamp
                            vi.is_mitigated = True

                        vi.status = HTFViStatus.TOUCHED
                        vi.is_touched = True

                        continue

                    # ---------------------------------------------
                    # Price enters VI but does not reach lower
                    # boundary
                    # ---------------------------------------------

                    elif (
                        vi.lower < candle.low < vi.upper
                    ):

                        if not vi.is_mitigated:
                            vi.mitigation_time = candle.timestamp
                            vi.is_mitigated = True

                        vi.status = HTFViStatus.PARTIAL
                        vi.is_touched = False
                        vi.is_swept = True

                        continue

                    # ---------------------------------------------
                    # Price reaches / passes lower boundary
                    # ---------------------------------------------

                    elif candle.low <= vi.lower:

                        if not vi.is_mitigated:
                            vi.mitigation_time = candle.timestamp
                            vi.is_mitigated = True

                        vi.status = HTFViStatus.MITIGATED
                        vi.is_touched = False
                        vi.is_swept = True

                        continue

                # -------------------------------------------------
                # VI was already touched / partially entered.
                # Allow it to progress to complete mitigation.
                # -------------------------------------------------

                if vi.status in (
                    HTFViStatus.TOUCHED,
                    HTFViStatus.PARTIAL,
                ):

                    # ---------------------------------------------
                    # Reached lower boundary
                    # ---------------------------------------------

                    if candle.low <= vi.lower:

                        vi.status = HTFViStatus.MITIGATED
                        if not vi.is_mitigated:
                            vi.mitigation_time = candle.timestamp
                            vi.is_mitigated = True
                        vi.is_touched = False
                        vi.is_swept = True

                        continue

                    # ---------------------------------------------
                    # Still inside VI
                    # ---------------------------------------------

                    if (
                        vi.lower < candle.low < vi.upper
                    ):

                        vi.status = HTFViStatus.PARTIAL
                        if not vi.is_mitigated:
                            vi.mitigation_time = candle.timestamp
                            vi.is_mitigated = True
                        vi.is_touched = False
                        vi.is_swept = True

            # =================================================
            # BEARISH VI
            # =================================================

            else:

                # -------------------------------------------------
                # Previous candle completely BELOW VI
                # -------------------------------------------------

                if previous_candle.high < vi.lower:

                    # ---------------------------------------------
                    # Exact touch of lower boundary
                    # ---------------------------------------------

                    if candle.high == vi.lower:

                        if not vi.is_mitigated:
                            vi.mitigation_time = candle.timestamp
                            vi.is_mitigated = True

                        vi.status = HTFViStatus.TOUCHED
                        vi.is_touched = True

                        continue

                    # ---------------------------------------------
                    # Price enters VI but does not reach upper
                    # boundary
                    # ---------------------------------------------

                    elif (
                        vi.lower < candle.high < vi.upper
                    ):

                        if not vi.is_mitigated:
                            vi.mitigation_time = candle.timestamp
                            vi.is_mitigated = True

                        vi.status = HTFViStatus.PARTIAL
                        vi.is_touched = False
                        vi.is_swept = True

                        continue

                    # ---------------------------------------------
                    # Price reaches / passes upper boundary
                    # ---------------------------------------------

                    elif candle.high >= vi.upper:

                        if not vi.is_mitigated:
                            vi.mitigation_time = candle.timestamp
                            vi.is_mitigated = True

                        vi.status = HTFViStatus.MITIGATED
                        vi.is_touched = False
                        vi.is_swept = True

                        continue

                # -------------------------------------------------
                # VI was already touched / partially entered.
                # Allow it to progress to complete mitigation.
                # -------------------------------------------------

                if vi.status in (
                    HTFViStatus.TOUCHED,
                    HTFViStatus.PARTIAL,
                ):

                    # ---------------------------------------------
                    # Reached upper boundary
                    # ---------------------------------------------

                    if candle.high >= vi.upper:

                        vi.status = HTFViStatus.MITIGATED
                        if not vi.is_mitigated:
                            vi.mitigation_time = candle.timestamp
                            vi.is_mitigated = True
                        vi.is_touched = False
                        vi.is_swept = True

                        continue

                    # ---------------------------------------------
                    # Still inside VI
                    # ---------------------------------------------

                    if (
                        vi.lower < candle.high < vi.upper
                    ):

                        vi.status = HTFViStatus.PARTIAL
                        if not vi.is_mitigated:
                            vi.mitigation_time = candle.timestamp
                            vi.is_mitigated = True
                        vi.is_touched = False
                        vi.is_swept = True

    # =========================================================
    # HTF RECLAIM PROCESSING
    # =========================================================

    for vi in vis:

        # -----------------------------------------------------
        # Reclaim requires prior interaction with the VI.
        # -----------------------------------------------------

        if not vi.is_mitigated:
            continue

        # Already reclaimed
        if vi.status == HTFViStatus.RECLAIMED:
            continue

        # -----------------------------------------------------
        # Determine VI confirmation time
        # -----------------------------------------------------

        if vi.timeframe == "4h":
            vi_confirmation_time = (
                vi.timestamp + timedelta(hours=4)
            )

        elif vi.timeframe == "7h":
            vi_confirmation_time = (
                vi.timestamp + timedelta(hours=7)
            )

        elif vi.timeframe == "1d":
            vi_confirmation_time = (
                vi.timestamp + timedelta(days=1)
            )

        else:
            raise ValueError(
                f"Unsupported VI timeframe: {vi.timeframe}"
            )

        # -----------------------------------------------------
        # Look for first qualifying HTF reclaim
        # -----------------------------------------------------

        for candle in htf_candles:

            if candle.timestamp <= vi_confirmation_time:
                continue

            # -------------------------------------------------
            # Bullish VI
            # -------------------------------------------------

            if vi.is_bullish:

                if (
                    candle.close <= vi.lower
                    and vi.status != HTFViStatus.RECLAIMED
                ):

                    vi.status = HTFViStatus.RECLAIMED
                    if not vi.is_mitigated:
                        vi.mitigation_time = candle.timestamp
                        vi.is_mitigated = True
                    vi.is_touched = False

                    # mitigation_time is preserved.
                    # Reclaim is NOT a new mitigation event.

                    break

            # -------------------------------------------------
            # Bearish VI
            # -------------------------------------------------

            else:

                if (
                    candle.close >= vi.upper
                    and vi.status != HTFViStatus.RECLAIMED
                ):

                    vi.status = HTFViStatus.RECLAIMED
                    if not vi.is_mitigated:
                        vi.mitigation_time = candle.timestamp
                        vi.is_mitigated = True
                    vi.is_touched = False

                    # mitigation_time is preserved.

                    break

# def update_vi_status(
#     vis: list[HTFVolumeImbalance],
#     ltf_candles: list[Candle],
#     htf_candles: list[Candle]
# ) -> None:
#     """
#     Updates the status of every HTF VI.
#     """

#     if not vis:
#         return

#     # Ensure chronological order
#     # candles = sorted(candles, key=lambda c: c.timestamp)
#     # ltf_candles = historical_candles.get('1m', [])
#     # htf_candles = historical_candles.get(vis[0].timeframe, [])
#     for vi in vis:

#         for candle in ltf_candles:

#             # Ignore candles before the FVG formed
#             vi_confirmation_time = vi.timestamp
#             if vi.timeframe == "4h":
#                 vi_confirmation_time = vi.timestamp + timedelta(hours=4)
#             elif vi.timeframe == "7h":
#                 vi_confirmation_time = vi.timestamp + timedelta(hours=7)
#             elif vi.timeframe == '1d':
#                 vi_confirmation_time = vi.timestamp + timedelta(days=1)

#             if candle.timestamp <= vi_confirmation_time:
#                 continue
            
#             # candle should be interating with the fvg
#             if vi.is_bullish: # bullish vi
#                 # set is_swept flag
                
#                 if (
#                     candle.low < vi.upper
#                     and candle.open > vi.upper
#                     # and candle.low < vi.upper < candle.high
#                     and not vi.is_swept
#                 ):
#                     vi.is_swept=True
#                     vi.is_touched=False

#                 if (
#                     candle.low == vi.upper
#                     and candle.open > vi.upper
#                 ):
#                     vi.status = HTFViStatus.TOUCHED
#                     vi.mitigation_time = candle.timestamp
#                     vi.is_touched=True
#                     break
#                 elif (
#                     candle.low < vi.upper
#                     and candle.open > vi.lower
#                 ):
#                     vi.status = HTFViStatus.PARTIAL
#                     vi.mitigation_time = candle.timestamp
#                     vi.is_touched=False
#                     break
                
#                 elif (
#                     candle.low <= vi.lower 
#                     and candle.open > vi.lower
#                 ):
#                     vi.status = HTFViStatus.MITIGATED
#                     vi.mitigation_time = candle.timestamp
#                     vi.is_touched=False
#                     break

#                 # reclaimed can only be finalized with a 4h candle
#                 # elif candle.close <= vi.lower:
#                 #     vi.status = HTFViStatus.RECLAIMED
#                 #     vi.mitigation_time = candle.timestamp
                
#             else:   # bearish fvg
#                 # set is_swept flag
#                 if (
#                     candle.high > vi.lower
#                     and candle.open < vi.lower
#                     and not vi.is_swept
#                 ):
#                     vi.is_swept = True
#                     vi.is_touched = False

#                 if (
#                     candle.high == vi.lower
#                     and candle.open < vi.lower
#                 ): 
#                     vi.status = HTFViStatus.TOUCHED
#                     vi.mitigation_time = candle.timestamp
#                     vi.is_touched=True
#                     break
#                 elif (
#                     candle.high > vi.lower
#                     and candle.open < vi.upper
#                 ):
#                     vi.status = HTFViStatus.PARTIAL
#                     vi.mitigation_time = candle.timestamp
#                     vi.is_touched=False
#                     break
#                 elif candle.high >= vi.upper:
#                     vi.status = HTFViStatus.MITIGATED
#                     vi.mitigation_time = candle.timestamp
#                     vi.is_touched=False
#                     break
#     for vi in vis:         
#         # process through htf timeframe candles to set RECLAIMED status
#         for candle in htf_candles:
        
#             # Ignore candles before the FVG formed
#             vi_confirmation_time = vi.timestamp
#             if vi.timeframe == "4h":
#                 vi_confirmation_time = vi.timestamp + timedelta(hours=4)
#             elif vi.timeframe == "7h":
#                 vi_confirmation_time = vi.timestamp + timedelta(hours=7)
#             elif vi.timeframe == '1d':
#                 vi_confirmation_time = vi.timestamp + timedelta(days=1)

#             if candle.timestamp <= vi_confirmation_time:
#                 continue
#             # candle should be interating with the fvg
#             if vi.is_bullish: # bullish fvg
#                 # set is_swept flag
                
#                 if candle.close <= vi.lower:
#                     vi.status=HTFViStatus.RECLAIMED
#                     break

                
#             else:   # bearish fvg
#                 # set is_swept flag
#                 if candle.close >= vi.upper:
#                     vi.status = HTFViStatus.RECLAIMED
#                     break

                
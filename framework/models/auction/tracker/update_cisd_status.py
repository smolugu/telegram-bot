from datetime import timedelta

from framework.models.auction.models.enums import HTFCisdStatus
from data.models.candle import Candle
from framework.models.auction.models.htf_cisd import HTFCISD


def update_cisd_status(
    cisds: list[HTFCISD],
    ltf_candles: list[Candle],
    htf_candles: list[Candle],
) -> None:
    """
    Updates the status of every HTF CISD.

    LTF lifecycle:
        OPEN -> MITIGATED

    HTF lifecycle:
        MITIGATED -> RECLAIMED
        MITIGATED -> RCISD

    mitigation_time is the first LTF interaction time and is
    never overwritten by later HTF events.
    """

    if not cisds:
        return

    ltf_candles = sorted(
        ltf_candles,
        key=lambda c: c.timestamp,
    )

    htf_candles = sorted(
        htf_candles,
        key=lambda c: c.timestamp,
    )

    for cisd in cisds:

        # ---------------------------------------------------------
        # Confirmation time
        # ---------------------------------------------------------

        if cisd.timeframe == "4h":
            cisd_confirmation_time = (
                cisd.timestamp + timedelta(hours=4)
            )
        elif cisd.timeframe == "7h":
            cisd_confirmation_time = (
                cisd.timestamp + timedelta(hours=7)
            )
        elif cisd.timeframe == "1d":
            cisd_confirmation_time = (
                cisd.timestamp + timedelta(days=1)
            )
        else:
            raise ValueError(
                f"Unsupported CISD timeframe: {cisd.timeframe}"
            )

        # =========================================================
        # LTF CISD MITIGATION
        # =========================================================

        if cisd.status == HTFCisdStatus.OPEN:

            for i in range(1, len(ltf_candles)):

                previous_candle = ltf_candles[i - 1]
                candle = ltf_candles[i]

                if candle.timestamp <= cisd_confirmation_time:
                    continue

                # -------------------------------------------------
                # Bullish CISD
                # -------------------------------------------------

                if cisd.is_bullish:

                    # Previous candle must be completely above
                    # the CISD before the current candle enters it.
                    if previous_candle.low > cisd.upper:

                        if candle.low <= cisd.upper:

                            cisd.status = HTFCisdStatus.MITIGATED
                            cisd.mitigation_time = candle.timestamp
                            cisd.is_swept = True
                            cisd.is_mitigated = True
                            break

                # -------------------------------------------------
                # Bearish CISD
                # -------------------------------------------------

                else:

                    # Previous candle must be completely below
                    # the CISD before the current candle enters it.
                    if previous_candle.high < cisd.lower:

                        if candle.high >= cisd.lower:

                            cisd.status = HTFCisdStatus.MITIGATED
                            cisd.mitigation_time = candle.timestamp
                            cisd.is_swept = True
                            cisd.is_mitigated = True
                            break

        # =========================================================
        # HTF RECLAIM / RCISD
        # =========================================================

        if cisd.status not in (
            HTFCisdStatus.MITIGATED,
        ):
            continue

        for i in range(1, len(htf_candles)):

            previous_candle = htf_candles[i - 1]
            candle = htf_candles[i]

            if candle.timestamp <= cisd_confirmation_time:
                continue

            # -----------------------------------------------------
            # Bullish CISD
            # -----------------------------------------------------

            if cisd.is_bullish:

                # Previous candle must be above the CISD lower
                # boundary before price crosses below it.
                if previous_candle.low > cisd.lower:

                    # RCISD:
                    # Candle closes below the wick of the original
                    # CISD candle.
                    if candle.close < cisd.lower_wick:

                        cisd.status = HTFCisdStatus.RCISD
                        break

                    # Reclaimed:
                    # Candle closes below the CISD lower boundary.
                    elif candle.close < cisd.lower:

                        cisd.status = HTFCisdStatus.RECLAIMED
                        break

            # -----------------------------------------------------
            # Bearish CISD
            # -----------------------------------------------------

            else:

                # Previous candle must be below the CISD upper
                # boundary before price crosses above it.
                if previous_candle.high < cisd.upper:

                    # RCISD:
                    # Candle closes above the wick of the original
                    # CISD candle.
                    if candle.close > cisd.upper_wick:

                        cisd.status = HTFCisdStatus.RCISD
                        break

                    # Reclaimed:
                    # Candle closes above the CISD upper boundary.
                    elif candle.close > cisd.upper:

                        cisd.status = HTFCisdStatus.RECLAIMED
                        break

# def update_cisd_status(
#     cisds: list[HTFCISD],
#     ltf_candles: list[Candle],
#     htf_candles: list[Candle]
# ) -> None:
#     """
#     Updates the status of every HTF CISD.
#     """

#     if not cisds:
#         return

#     # Ensure chronological order
#     # candles = sorted(candles, key=lambda c: c.timestamp)
#     # ltf_candles = historical_candles.get('1m', [])
#     # htf_candles = historical_candles.get(cisds[0].timeframe, [])
#     for cisd in cisds:

#         # if cisd.status != HTFCisdStatus.OPEN:
#         #     continue

#         for candle in ltf_candles:
#             # Ignore candles before the cisd formed
#             cisd_confirmation_time = cisd.timestamp
#             if cisd.timeframe == "4h":
#                 cisd_confirmation_time = cisd.timestamp + timedelta(hours=4)
#             elif cisd.timeframe == "7h":
#                 cisd_confirmation_time = cisd.timestamp + timedelta(hours=7)
#             elif cisd.timeframe == '1d':
#                 cisd_confirmation_time = cisd.timestamp + timedelta(days=1)

#             if candle.timestamp <= cisd_confirmation_time:
#                 continue
                
#             if cisd.is_bullish: # bullish cisd
#                 # set is_swept value
#                 if (
#                     candle.low < cisd.upper
#                     and candle.open > cisd.upper
#                     # and candle.low < cisd.upper < candle.high
#                     and not cisd.is_swept
#                 ): 
#                     cisd.is_swept=True
                
#                 elif (
#                     candle.low < cisd.upper
#                     and candle.open > cisd.lower
#                 ):
#                     cisd.status = HTFCisdStatus.MITIGATED
#                     cisd.mitigation_time = candle.timestamp
#                     break                
#             else:   # bearish CISD
#                 # set is_swept value
#                 if (
#                     candle.high > cisd.lower 
#                     and candle.open < cisd.lower
#                 ):
#                     cisd.is_swept=True
#                 elif (
#                     candle.high > cisd.lower
#                     and candle.open < cisd.upper
#                 ):
#                     cisd.status = HTFCisdStatus.MITIGATED
#                     cisd.mitigation_time = candle.timestamp
#                     break
                

#     for cisd in cisds:
#         for candle in htf_candles:
#             # Ignore candles before the cisd formed
#             cisd_confirmation_time = cisd.timestamp
#             if cisd.timeframe == "4h":
#                 cisd_confirmation_time = cisd.timestamp + timedelta(hours=4)
#             elif cisd.timeframe == "7h":
#                 cisd_confirmation_time = cisd.timestamp + timedelta(hours=7)
#             elif cisd.timeframe == '1d':
#                 cisd_confirmation_time = cisd.timestamp + timedelta(days=1)

#             if candle.timestamp <= cisd_confirmation_time:
#                 continue
#             if cisd.is_bullish:
#                 if (
#                     candle.open > cisd.lower_wick
#                     and (
#                         candle.close < cisd.lower_wick or candle.low < cisd.lower_wick
#                     )
                    
#                 ):
#                     cisd.status = HTFCisdStatus.RCISD
#                     cisd.mitigation_time = candle.timestamp
#                     break
                
#                 elif (
#                     candle.close < cisd.lower
#                     and candle.open > cisd.lower
#                 ):
#                     cisd.status = HTFCisdStatus.RECLAIMED
#                     cisd.mitigation_time = candle.timestamp
#                     break
#             else:
#                 if (
#                     candle.open < cisd.upper_wick
#                     and (
#                         candle.close > cisd.upper_wick or candle.high > cisd.upper_wick
#                     )        
#                 ):
#                     cisd.status = HTFCisdStatus.RCISD
#                     cisd.mitigation_time = candle.timestamp
#                     break
                
#                 elif (
#                     candle.close > cisd.upper
#                     and candle.open < cisd.upper
#                 ):
#                     cisd.status = HTFCisdStatus.RECLAIMED
#                     cisd.mitigation_time = candle.timestamp
#                     break


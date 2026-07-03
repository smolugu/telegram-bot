from datetime import datetime
from datetime import timedelta

def initialize_weekly_state():

    return {
        "week_start": None,
        "weekly_open": None,
        "price_location": None,      # above | below

        "bullish_cisd": None,
        "bearish_cisd": None,

        "bullish_fvg": None,
        "bearish_fvg": None,

        "bias": None,
        "bias_reason": None,
    }


def get_week_start(dt):
    """
    Monday 00:00 of current week.
    """
    return dt.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    ) - timedelta(days=dt.weekday())


def filter_weekly_1h_candles(candles_1h):

    if not candles_1h:
        return []

    last_dt = datetime.fromisoformat(
        candles_1h[-1]["timestamp"]
    )

    week_start = get_week_start(last_dt)

    return [
        c
        for c in candles_1h
        if datetime.fromisoformat(
            c["timestamp"]
        ) >= week_start
    ]


def _detect_latest_fvg(candles):

    bullish_fvg = None
    bearish_fvg = None

    if len(candles) < 3:
        return bullish_fvg, bearish_fvg

    c1 = candles[-3]
    c2 = candles[-2]
    c3 = candles[-1]

    #
    # Bullish FVG
    #

    if c3["low"] > c1["high"]:

        bullish_fvg = {
            "low": c1["high"],
            "high": c3["low"],
            "ce": (c1["high"] + c3["low"]) / 2,
            "state": "open",
            "timestamp": c3["timestamp"],
        }

    #
    # Bearish FVG
    #

    elif c3["high"] < c1["low"]:

        bearish_fvg = {
            "low": c3["high"],
            "high": c1["low"],
            "ce": (c3["high"] + c1["low"]) / 2,
            "state": "open",
            "timestamp": c3["timestamp"],
        }

    return bullish_fvg, bearish_fvg

def _find_recent_bullish_candle(candles):

    for candle in reversed(candles[:-1]):

        if candle["close"] > candle["open"]:
            return candle

    return None

def _find_recent_bearish_candle(candles):

    for candle in reversed(candles[:-1]):

        if candle["close"] < candle["open"]:
            return candle

    return None

def update_weekly_1h_structure(
    weekly_state,
    candles_1h,
):
    """
    Called at every 1H close.
    """

    candles = filter_weekly_1h_candles(
        candles_1h
    )

    if len(candles_1h) < 3:
        return weekly_state

    #
    # Reset at new week
    #

    current_week = get_week_start(
        datetime.fromisoformat(
            candles[-1]["timestamp"]
        )
    )

    if weekly_state["week_start"] != current_week:

        weekly_state = initialize_weekly_state()

        weekly_state["week_start"] = current_week

        weekly_state["weekly_open"] = candles[0]["open"]

    current_price = candles[-1]["close"]
    last_closed = candles_1h[-1]

    #
    # Weekly Open Location
    #

    if current_price > weekly_state["weekly_open"]:

        weekly_state["price_location"] = "above"

    else:

        weekly_state["price_location"] = "below"

    #
    # --------------------------------------------------
    # Invalidate Existing CISDs
    # --------------------------------------------------
    #

    if (
        weekly_state["bullish_cisd"] is not None
        and
        last_closed["close"]
        <
        weekly_state["bullish_cisd"]["invalidate_below"]
    ):

        print("Weekly Bullish CISD invalidated")

        weekly_state["bullish_cisd"] = None

    if (
        weekly_state["bearish_cisd"] is not None
        and
        last_closed["close"]
        >
        weekly_state["bearish_cisd"]["invalidate_above"]
    ):

        print("Weekly Bearish CISD invalidated")

        weekly_state["bearish_cisd"] = None

    #
    # --------------------------------------------------
    # Detect Bullish CISD
    # --------------------------------------------------
    #

    recent_bearish = _find_recent_bearish_candle(
        candles_1h
    )

    if (
        recent_bearish is not None
        and
        last_closed["close"]
        >
        recent_bearish["open"]
    ):

        if weekly_state["bullish_cisd"] is None:

            print("Weekly Bullish CISD formed")

            weekly_state["bullish_cisd"] = {
                "timestamp": last_closed["timestamp"],
                "cisd_level": recent_bearish["open"],
                "invalidate_below": recent_bearish["low"],
            }

    #
    # --------------------------------------------------
    # Detect Bearish CISD
    # --------------------------------------------------
    #

    recent_bullish = _find_recent_bullish_candle(
        candles_1h
    )

    if (
        recent_bullish is not None
        and
        last_closed["close"]
        <
        recent_bullish["open"]
    ):

        if weekly_state["bearish_cisd"] is None:

            print("Weekly Bearish CISD formed")

            weekly_state["bearish_cisd"] = {
                "timestamp": last_closed["timestamp"],
                "cisd_level": recent_bullish["open"],
                "invalidate_above": recent_bullish["high"],
            }

    #
    # --------------------------------------------------
    # Detect New FVGs
    # --------------------------------------------------
    #

    bullish_fvg, bearish_fvg = _detect_latest_fvg(
        candles_1h
    )

    if (
        bullish_fvg is not None
        and (
            weekly_state["bullish_fvg"] is None
            or weekly_state["bullish_fvg"]["state"] == "reclaimed"
        )
    ):

        print("Weekly Bullish FVG formed")

        weekly_state["bullish_fvg"] = bullish_fvg

    if (
        bearish_fvg is not None
        and (
            weekly_state["bearish_fvg"] is None
            or weekly_state["bearish_fvg"]["state"] == "reclaimed"
        )
    ):

        print("Weekly Bearish FVG formed")

        weekly_state["bearish_fvg"] = bearish_fvg

    #
    # --------------------------------------------------
    # Update FVG States
    # --------------------------------------------------
    #

    if weekly_state["bullish_fvg"] is not None:

        if (
            last_closed["close"]
            <
            weekly_state["bullish_fvg"]["low"]
        ):

            print("Weekly Bullish FVG reclaimed")

            weekly_state["bullish_fvg"]["state"] = "reclaimed"

        elif (
            last_closed["low"]
            <
            weekly_state["bullish_fvg"]["high"]
        ):

            weekly_state["bullish_fvg"]["state"] = "mitigated"

    if weekly_state["bearish_fvg"] is not None:

        if (
            last_closed["close"]
            >
            weekly_state["bearish_fvg"]["high"]
        ):

            print("Weekly Bearish FVG reclaimed")
            weekly_state["bearish_fvg"]["state"] = "reclaimed"

        elif (
            last_closed["high"]
            >
            weekly_state["bearish_fvg"]["low"]
        ):

            weekly_state["bearish_fvg"]["state"] = "mitigated"

    #
    # --------------------------------------------------
    # Determine HTF Bias
    # --------------------------------------------------
    #

    weekly_state["bias"] = None
    weekly_state["bias_reason"] = None

    #
    # Strong Bullish
    #

    if (
        weekly_state["bullish_cisd"]
        and
        weekly_state["bullish_fvg"]
        and
        weekly_state["bullish_fvg"]["state"]
        != "reclaimed"
    ):

        weekly_state["bias"] = "bullish"
        weekly_state["bias_reason"] = (
            "bullish_cisd_plus_bullish_fvg"
        )

    #
    # Strong Bearish
    #

    elif (
        weekly_state["bearish_cisd"]
        and
        weekly_state["bearish_fvg"]
        and
        weekly_state["bearish_fvg"]["state"]
        != "reclaimed"
    ):

        weekly_state["bias"] = "bearish"
        weekly_state["bias_reason"] = (
            "bearish_cisd_plus_bearish_fvg"
        )

    #
    # Conflicting CISDs
    #

    elif (
        weekly_state["bullish_cisd"]
        and
        weekly_state["bearish_cisd"]
    ):

        weekly_state["bias"] = "neutral"
        weekly_state["bias_reason"] = (
            "conflicting_cisds"
        )

    #
    # Weak Bullish
    #

    elif weekly_state["bullish_cisd"]:

        weekly_state["bias"] = "bullish"
        weekly_state["bias_reason"] = (
            "bullish_cisd_only"
        )

    #
    # Weak Bearish
    #

    elif weekly_state["bearish_cisd"]:

        weekly_state["bias"] = "bearish"
        weekly_state["bias_reason"] = (
            "bearish_cisd_only"
        )

    #
    # Weekly Open Fallback
    #

    else:

        if (
            weekly_state["price_location"]
            == "above"
        ):

            weekly_state["bias"] = "bullish"
            weekly_state["bias_reason"] = (
                "above_weekly_open"
            )

        else:

            weekly_state["bias"] = "bearish"
            weekly_state["bias_reason"] = (
                "below_weekly_open"
            )

    return weekly_state

















# def update_weekly_state(
#     weekly_state,
#     candles_1h,
# ):
#     """
#     Called at every 1H close.
#     """

#     candles = filter_weekly_1h_candles(
#         candles_1h
#     )

#     if len(candles) < 3:
#         return weekly_state

#     #
#     # Reset at new week
#     #

#     current_week = get_week_start(
#         datetime.fromisoformat(
#             candles[-1]["timestamp"]
#         )
#     )

#     if weekly_state["week_start"] != current_week:

#         weekly_state = initialize_weekly_state()

#         weekly_state["week_start"] = current_week

#         weekly_state["weekly_open"] = candles[0]["open"]

#     current_price = candles[-1]["close"]

#     #
#     # Weekly Open Location
#     #

#     if current_price > weekly_state["weekly_open"]:

#         weekly_state["price_location"] = "above"

#     else:

#         weekly_state["price_location"] = "below"

#     #
#     # CISD Detection
#     #
#     # Replace with your CISD detector
#     #

#     bullish_cisd = detect_bullish_cisd(
#         candles
#     )

#     bearish_cisd = detect_bearish_cisd(
#         candles
#     )

#     if bullish_cisd:
#         weekly_state["bullish_cisd"] = True
#         weekly_state["bearish_cisd"] = False

#     elif bearish_cisd:
#         weekly_state["bearish_cisd"] = True
#         weekly_state["bullish_cisd"] = False

#     #
#     # FVG Detection
#     #
#     # Replace with your FVG detector
#     #

#     bullish_fvg = find_latest_bullish_fvg(
#         candles
#     )

#     bearish_fvg = find_latest_bearish_fvg(
#         candles
#     )

#     if bullish_fvg:
#         weekly_state["bullish_fvg"] = bullish_fvg

#     if bearish_fvg:
#         weekly_state["bearish_fvg"] = bearish_fvg

#     #
#     # HTF Bias Logic
#     #

#     if weekly_state["price_location"] == "below":

#         if (
#             weekly_state["bullish_cisd"]
#             and weekly_state["bullish_fvg"]
#             and weekly_state["bullish_fvg_state"]
#             != "reclaimed"
#         ):

#             weekly_state["bias"] = "bullish"

#         else:

#             weekly_state["bias"] = "bearish"

#     else:

#         if (
#             weekly_state["bearish_cisd"]
#             and weekly_state["bearish_fvg"]
#             and weekly_state["bearish_fvg_state"]
#             != "reclaimed"
#         ):

#             weekly_state["bias"] = "bearish"

#         else:

#             weekly_state["bias"] = "bullish"

#     return weekly_state
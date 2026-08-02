from datetime import datetime, timedelta

def initialize_weekly_state(instrument):

    return {
        "instrument": instrument,
        "week_start": None,
        "weekly_open": None,
        "price_location": None,      # above | below

        "bullish_cisd": None,
        "bearish_cisd": None,
        "new_bullish_cisd": None,
        "new_bearish_cisd": None,

        "bullish_fvg": None,
        "bearish_fvg": None,
        "new_bullish_fvg": None,
        "new_bearish_fvg": None,

        "bias": None,
        "bias_reason": None,

        "bullish_ready": False,
        "bearish_ready": False,
        "flush": {"status": False, "time": None},
        "rocket": {"status": False, "time": None},
    }


from datetime import timedelta

def get_week_start(dt):
    """
    Returns the start of the CME trading week (Sunday 18:00 ET).
    Correctly handles Sunday before 18:00 as part of the previous week.
    """

    midnight = dt.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    days_since_sunday = (dt.weekday() + 1) % 7
    sunday = midnight - timedelta(days=days_since_sunday)
    week_start = sunday.replace(hour=18)

    # Before Sunday 18:00 -> still previous trading week
    if dt < week_start:
        week_start -= timedelta(days=7)

    return week_start

def get_week_start_midnight(dt):
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
    print("c1: ", c1)
    print("c2: ", c2)
    print("c3: ", c3)

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
        print("c3 high < c1 low")

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


def build_weekly_state(
    candles_1d,
    candles_1h,
    current_day_start,
    instrument
):
    """
    Build weekly state by replaying all completed 1H candles
    from Sunday 18:00 up to (but not including) current_day_start.
    """

    weekly_state = initialize_weekly_state(instrument)
    
    week_start = get_week_start(current_day_start)
    print("week start 101: ", week_start)
    
    week_open_daily = None
    # print("candles daily: ", candles_1d)
    # Yahoo labels the session by the next calendar day
    target_date = (week_start + timedelta(days=1)).date()

    week_open_daily = next(
        (
            candle
            for candle in candles_1d
            if datetime.fromisoformat(candle["timestamp"]).date() == target_date
        ),
        None,
    )
    
    
    # weekly_state["week_start"] = week_start
    print("weekly_open_daily: ", week_open_daily)
    if week_open_daily is None:
        if instrument == "NQ":
            weekly_state["weekly_open"] = 28747.5
        elif instrument == "ES":
            weekly_state["weekly_open"] = 7484.5
    else:
        weekly_state["weekly_open"] = week_open_daily["open"]

    history = []

    for candle in candles_1h:

        ts = datetime.fromisoformat(candle["timestamp"])
        # print("week_start: ", week_start)
        # print("ts: ", ts)
        # print("current_day_start: ", current_day_start)
        if week_start <= ts < current_day_start:
            # print("appending")
            
            history.append(candle)

    print("history: ", history)
    weekly_state["week_start"] = week_start
    # we need to loop through these candles from start of week to start of current day and update weekly state
    candles_to_update_state = []
    for candle in history:
        
        candles_to_update_state.append(candle)
        # temporary fix to correct 1st 1h candle at week open
        if len(candles_to_update_state) == 1:
            print("updating first candle")
            candles_to_update_state[0]["open"] = 28747.5 if instrument == "NQ" else 7484.5
            # print("candles_to_update_state 0 open: ", candles_to_update_state[0]["open"])
            candles_to_update_state[0]["high"] = 28851.25 if instrument == "NQ" else 7502.5
            candles_to_update_state[0]["low"] = 28706.75 if instrument == "NQ" else 7482
            candles_to_update_state[0]["close"] = 28815.75 if instrument == "NQ" else 7495.75
        # print("candles_to_update_state: ", candles_to_update_state[0])
        weekly_state = update_weekly_1h_structure(
            weekly_state,
            candles_to_update_state
        )

    return weekly_state


def update_weekly_1h_structure(
    weekly_state,
    candles_1h,
):
    """
    Called at every 1H close.
    """

    # candles = filter_weekly_1h_candles(
    #     candles_1h
    # )

    if len(candles_1h) < 3:
        return weekly_state

    #
    # Reset at new week
    #

    # current_week = get_week_start(
    #     datetime.fromisoformat(
    #         candles_1h[-1]["timestamp"]
    #     )
    # )
    # print("currnt_week: ", current_week)
    # print("week start: ", weekly_state["week_start"])

    # if weekly_state["week_start"] is not None and weekly_state["week_start"] != current_week:
    #     print("resetting week state 102")

    #     weekly_state = initialize_weekly_state()

    #     weekly_state["week_start"] = current_week
    #     print("week start X: ", weekly_state["week_start"])
    #     # print("candle 0:", candles[0])

    #     # weekly_state["weekly_open"] = candles[0]["open"]
        
    # print("weekly open: ", weekly_state["weekly_open"])
    
    current_price = candles_1h[-1]["close"]
    last_closed = candles_1h[-1]
    print("===========================")
    print("last_closed: ", last_closed)
    print("===========================")

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
        last_closed["close"] < weekly_state["bullish_cisd"]["invalidate_below"]
    ):
        print("Weekly Bullish CISD invalidated")
        weekly_state["bullish_cisd"] = None

    if (
        weekly_state["bearish_cisd"] is not None
        and
        last_closed["close"] > weekly_state["bearish_cisd"]["invalidate_above"]
    ):
        print("Weekly Bearish CISD invalidated")
        weekly_state["bearish_cisd"] = None
    
    if (
        weekly_state["new_bullish_cisd"] is not None
        and
        last_closed["close"] < weekly_state["new_bullish_cisd"]["invalidate_below"]
    ):
        print("Weekly New Bullish CISD invalidated")
        weekly_state["new_bullish_cisd"] = None

    if (
        weekly_state["new_bearish_cisd"] is not None
        and
        last_closed["close"] > weekly_state["new_bearish_cisd"]["invalidate_above"]
    ):
        print("Weekly New Bearish CISD invalidated")
        weekly_state["new_bearish_cisd"] = None

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
        and last_closed["close"] > recent_bearish["open"]
        and last_closed["timestamp"] != recent_bearish["timestamp"]

    ):
        print("last_closed timestamp: ", last_closed["timestamp"])
        print("recent timestamp: ", recent_bearish["timestamp"])
        # bullish cisd detected
        # update state and bias
            # if there is a valid bearish cisd, set bias to neutral
            # if bullish cisd followed by bullish fvg set bias to bullish 
            # if a new bearish fvg is reclaimed, set bias to strong bullish
        if weekly_state["bullish_cisd"] is None:

            weekly_state["bullish_cisd"] = {
                "timestamp": last_closed["timestamp"],
                "cisd_level": recent_bearish["open"],
                "invalidate_below": recent_bearish["close"] if recent_bearish["close"] < last_closed["open"] else last_closed["open"],
            }
            print("Weekly Bullish CISD formed: ", weekly_state["bullish_cisd"])
        elif weekly_state["new_bullish_cisd"] is not None:

            weekly_state["new_bullish_cisd"] = {
                "timestamp": last_closed["timestamp"],
                "cisd_level": recent_bearish["open"],
                "invalidate_below": recent_bearish["close"] if recent_bearish["close"] < last_closed["open"] else last_closed["open"],
            }
            print("Weekly New Bullish CISD formed: ", weekly_state["new_bullish_cisd"])
        
        # update weekly bias and reason
        # dont change to neutral yet
        # if weekly_state["bearish_cisd"] and weekly_state["bullish_cisd"]:
        #     weekly_state["bias"] = "neutral"
        #     weekly_state["bias_reason"] = "conflicting cisd's"
        

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
        and last_closed["close"] < recent_bullish["open"]
        and last_closed["timestamp"] != recent_bullish["timestamp"]
    ):
        print("check for new bearish cisd")
        print("recent_bullish: ", recent_bullish)
        print("last_closed timestamp: ", last_closed["timestamp"])
        print("recent timestamp: ", recent_bullish["timestamp"])
        print("last_closed close: ", last_closed["close"])
        print("recent bullish open: ", recent_bullish["open"])
        print("prevous cisd: ", weekly_state["bearish_cisd"])
        if weekly_state["bearish_cisd"] is None:

            weekly_state["bearish_cisd"] = {
                "timestamp": last_closed["timestamp"],
                "cisd_level": recent_bullish["open"],
                # "invalidate_above": recent_bullish["high"] if recent_bullish["high"] > last_closed["high"] else last_closed["high"],
                "invalidate_above": recent_bullish["close"] if recent_bullish["close"] > last_closed["open"] else last_closed["open"],
            }
            print("Weekly Bearish CISD formed: ", weekly_state["bearish_cisd"])
            # update weekly state
        elif weekly_state["new_bearish_cisd"] is not None:
            weekly_state["new_bearish_cisd"] = {
                "timestamp": last_closed["timestamp"],
                "cisd_level": recent_bullish["open"],
                "invalidate_above": recent_bullish["close"] if recent_bullish["close"] > last_closed["open"] else last_closed["open"],
            }
            print("Weekly New Bearish CISD formed: ", weekly_state["new_bearish_cisd"])

    #
    # --------------------------------------------------
    # Detect New FVGs
    # --------------------------------------------------
    #

    bullish_fvg, bearish_fvg = _detect_latest_fvg(
        candles_1h
    )
    print("bullish fvgs: ", bullish_fvg)
    print("bearish fvgs: ", bearish_fvg)

    if bullish_fvg:
        print("fresh bullish fvg detected")
        print("bearish_fvg and CISd:", weekly_state["bearish_cisd"], weekly_state["bearish_fvg"])
    if bearish_fvg:
        print("fresh bearish fvg detected")
        print("bullish_fvg and CISd:", weekly_state["bullish_cisd"], weekly_state["bullish_fvg"])

    if bullish_fvg is not None:
        
        if (
            weekly_state["bullish_fvg"] is None
            or weekly_state["bullish_fvg"]["state"] == "reclaimed"
        ):
    
            weekly_state["bullish_fvg"] = bullish_fvg
            print("Weekly Bullish FVG formed: ", weekly_state["bullish_fvg"])
            # update weekly state
            if weekly_state["bullish_cisd"]:
                weekly_state["bias"] = "bullish"
                weekly_state["bias_reason"] = "bullish_cisd_plus_fvg"
        else:
            weekly_state["new_bullish_fvg"] = bullish_fvg
    
    if bearish_fvg is not None:
        
        if (
            weekly_state["bearish_fvg"] is None
            or weekly_state["bearish_fvg"]["state"] == "reclaimed"
        ):
    
            weekly_state["bearish_fvg"] = bearish_fvg
            print("Weekly Bearish FVG formed: ", weekly_state["bearish_fvg"])
            # update weekly state
            if weekly_state["bearish_cisd"]:
                weekly_state["bias"] = "bearish"
                weekly_state["bias_reason"] = "bearish_cisd_plus_fvg"
        else:
            weekly_state["new_bearish_fvg"] = bearish_fvg

    #  update weekly bias since we have new cisd_and_fvg formed



    #
    # --------------------------------------------------
    # Update FVG States
    # --------------------------------------------------
    #

    if weekly_state["bullish_fvg"] is not None:

        if (
            last_closed["close"] < weekly_state["bullish_fvg"]["low"]
            and weekly_state["bullish_fvg"]["state"] != "reclaimed"
        ):
            print("Weekly Bullish FVG reclaimed at: ", last_closed["timestamp"])
            weekly_state["bullish_fvg"]["state"] = "reclaimed"

            if weekly_state["price_location"] == "above":
                if weekly_state["bullish_cisd"] is None:
                    weekly_state['bias'] = "neutral"
                    weekly_state["bias_reason"] = "invalidation of bullish fvg and cisd above open"
                elif weekly_state["bearish_fvg"] is not None:
                    weekly_state["bias"] = "bearish"
                    weekly_state["bias_reason"] = "bearish cisd plus fvg above open"
                elif weekly_state["bullish_cisd"] is not None and weekly_state["bearish_cisd"] is not None:
                    weekly_state["bias"] = "neutral"
                    weekly_state["bias_reason"] = "conflicting cisds"
                else:
                    weekly_state['bias'] = "bullish"
                    weekly_state["bias_reason"] = "price above weekly open"
            else:
                if weekly_state["bearish_fvg"] is not None:
                    weekly_state["bias"] = "bearish"
                    weekly_state["bias_reason"] = "bearish fvg and cisd below open"
                elif weekly_state["bearish_cisd"] is not None and weekly_state["bullish_cisd"] is not None:
                    weekly_state["bias"] = "neutral"
                    weekly_state["bias_reason"] = "conflicting cisds below open"
                elif weekly_state["bearish_cisd"] is None and weekly_state["bullish_cisd"] is None:
                    weekly_state["bias"] = "neutral"
                    weekly_state["bias_reason"] = "price below open with reclaimed bullish fvg"
                else:
                    weekly_state["bias"] = "bearish"
                    weekly_state["bias_reason"] = "price below open"
            # weekly_state["bias"] = "neutral"
            # weekly_state["bias_reason"] = "bullish fvg reclaimed"
            weekly_state["rocket"]["status"] = False
            weekly_state["rocket"]["time"] = None

        elif (
            last_closed["low"] < weekly_state["bullish_fvg"]["high"]
            and weekly_state["bullish_fvg"]["state"] == "open"
        ):
            weekly_state["bullish_fvg"]["state"] = "mitigated"
            weekly_state["rocket"]["status"] = True
            weekly_state["rocket"]["time"] = last_closed["timestamp"]

    if weekly_state["bearish_fvg"] is not None:

        if (
            last_closed["close"] > weekly_state["bearish_fvg"]["high"]
            and weekly_state["bearish_fvg"]["state"] != "reclaimed"
        ):

            print("Weekly Bearish FVG reclaimed at: ", last_closed["timestamp"])
            print("bearish fvg: ", weekly_state["bearish_fvg"])
            weekly_state["bearish_fvg"]["state"] = "reclaimed"

            if weekly_state["price_location"] == "above":
                if weekly_state["bearish_cisd"] is None:
                    weekly_state['bias'] = "bullish"
                    weekly_state["bias_reason"] = "invalidation of bearish fvg and cisd above open"
                elif weekly_state["bullish_fvg"] is not None:
                    weekly_state["bias"] = "bullish"
                    weekly_state["bias_reason"] = "bullish cisd and fvg above open"
                elif weekly_state["bearish_cisd"] is not None:
                    weekly_state["bias"] = "neutral"
                    weekly_state["bias_reason"] = "conflicting cisds"
                else:
                    weekly_state['bias'] = "bullish"
                    weekly_state["bias_reason"] = "price above weekly open"
            else:
                if weekly_state["bullish_fvg"] is not None:
                    weekly_state["bias"] = "bullish"
                    weekly_state["bias_reason"] = "bullish fvg and cisd below open"
                elif weekly_state["bearish_cisd"] is not None and weekly_state["bullish_cisd"] is not None:
                    weekly_state["bias"] = "neutral"
                    weekly_state["bias_reason"] = "conflicting cisds below open"
                elif weekly_state["bearish_cisd"] is None and weekly_state["bullish_cisd"] is None:
                    weekly_state["bias"] = "neutral"
                    weekly_state["bias_reason"] = "price below open"
                else:
                    weekly_state["bias"] = "bearish"
                    weekly_state["bias_reason"] = "price below open"
            weekly_state["flush"]["status"] = False
            weekly_state["flush"]["time"] = None

        elif (
            last_closed["high"] > weekly_state["bearish_fvg"]["low"]
            and weekly_state["bearish_fvg"]["state"] == "open"
        ):
            weekly_state["bearish_fvg"]["state"] = "mitigated"
            weekly_state["flush"]["status"] = True
            weekly_state["flush"]["time"] = last_closed["timestamp"]

    #
    # --------------------------------------------------
    # Determine HTF Bias
    # --------------------------------------------------
    #

    if not weekly_state["bullish_fvg"] and not weekly_state["bearish_fvg"]:
        if weekly_state["bullish_cisd"] and weekly_state["bearish_cisd"]:
            weekly_state["bias"] = "neutral"
            weekly_state["bias_reason"] = "conflicting cisds"
        elif weekly_state["bullish_cisd"] and weekly_state["price_location"] == "above":
            weekly_state["bias"] = "bullish"
            weekly_state["bias_reason"] = "bullish CISD above weekly open"
        elif weekly_state["bullish_cisd"] and weekly_state["price_location"] == "below":
            weekly_state["bias"] = "neutral"
            weekly_state["bias_reason"] = "bullish CISD below weekly open"
        elif weekly_state["bearish_cisd"] and weekly_state["price_location"] == "below":
            weekly_state["bias"] = "bearish"
            weekly_state["bias_reason"] = "bearish CISD below weekly open"
        elif weekly_state["bearish_cisd"] and weekly_state["price_location"] == "above":
            weekly_state["bias"] = "neutral"
            weekly_state["bias_reason"] = "bearish CISD above weekly open"
        elif weekly_state["price_location"] == "below":
            weekly_state["bias"] = "bearish"
            weekly_state["bias_reason"] = "start of week. price below weekly open"
        elif weekly_state["price_location"] == "above":
            weekly_state["bias"] = "bullish"
            weekly_state["bias_reason"] = "start of week. price above weekly open"
        else:
            weekly_state["bias"] = "neutral"
            weekly_state["bias_reason"] = "too early in the week"

    # weekly_state["bias"] = None
    # weekly_state["bias_reason"] = None
    # print("weekly_state: ", weekly_state)
    # # neutral
    # if (
    #     weekly_state["bullish_cisd"]
    #     and
    #     weekly_state["bullish_fvg"]
    #     and
    #     weekly_state["bullish_fvg"]["state"]
    #     != "reclaimed" and weekly_state["bearish_cisd"]
    #     and
    #     weekly_state["bearish_fvg"]
    #     and
    #     weekly_state["bearish_fvg"]["state"]
    #     != "reclaimed"
    # ):
    #     weekly_state["bias"] = "neutral"
    #     weekly_state["bias_reason"] = (
    #         "cisd+fvg on both sides"
    #     )
    # #
    # # Strong Bullish
    # #

    # elif (
    #     weekly_state["bullish_cisd"]
    #     and
    #     weekly_state["bullish_fvg"]
    #     and
    #     weekly_state["bullish_fvg"]["state"]
    #     != "reclaimed" 
    # ):

    #     weekly_state["bias"] = "bullish"
    #     weekly_state["bias_reason"] = (
    #         "bullish_cisd_plus_bullish_fvg"
    #     )

    # #
    # # Strong Bearish
    # #

    # elif (
    #     weekly_state["bearish_cisd"]
    #     and
    #     weekly_state["bearish_fvg"]
    #     and
    #     weekly_state["bearish_fvg"]["state"]
    #     != "reclaimed"
    # ):

    #     weekly_state["bias"] = "bearish"
    #     weekly_state["bias_reason"] = (
    #         "bearish_cisd_plus_bearish_fvg"
    #     )

    # #
    # # Conflicting CISDs
    # #

    # elif (
    #     weekly_state["bullish_cisd"]
    #     and
    #     weekly_state["bearish_cisd"]
    # ):

    #     weekly_state["bias"] = "neutral"
    #     weekly_state["bias_reason"] = (
    #         "conflicting_cisds"
    #     )

    # #
    # # Weak Bullish
    # #

    # elif weekly_state["bullish_cisd"]:

    #     weekly_state["bias"] = "bullish"
    #     weekly_state["bias_reason"] = (
    #         "bullish_cisd_only"
    #     )

    # #
    # # Weak Bearish
    # #

    # elif weekly_state["bearish_cisd"]:

    #     weekly_state["bias"] = "bearish"
    #     weekly_state["bias_reason"] = (
    #         "bearish_cisd_only"
    #     )

    # #
    # # Weekly Open Fallback
    # #

    # else:

    #     if (
    #         weekly_state["price_location"]
    #         == "above"
    #     ):

    #         weekly_state["bias"] = "bullish"
    #         weekly_state["bias_reason"] = (
    #             "above_weekly_open"
    #         )

    #     else:

    #         weekly_state["bias"] = "bearish"
    #         weekly_state["bias_reason"] = (
    #             "below_weekly_open"
    #         )
    print("weekly bias: ", weekly_state["bias"])
    print("weekly reason: ", weekly_state["bias_reason"])
    return weekly_state

# def update_daily_delivery_state(
#     weekly_state,
#     candles_1h,
# ):
#     """
#     Called at every 1H close.
#     """

#     candles = filter_weekly_1h_candles(
#         candles_1h
#     )

#     if len(candles_1h) < 3:
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
#     last_closed = candles_1h[-1]

#     #
#     # Weekly Open Location
#     #

#     if current_price > weekly_state["weekly_open"]:

#         weekly_state["price_location"] = "above"

#     else:

#         weekly_state["price_location"] = "below"

#     #
#     # --------------------------------------------------
#     # Invalidate Existing CISDs
#     # --------------------------------------------------
#     #

#     if (
#         weekly_state["bullish_cisd"] is not None
#         and
#         last_closed["close"]
#         <
#         weekly_state["bullish_cisd"]["invalidate_below"]
#     ):

#         print("Weekly Bullish CISD invalidated")

#         weekly_state["bullish_cisd"] = None

#     if (
#         weekly_state["bearish_cisd"] is not None
#         and
#         last_closed["close"]
#         >
#         weekly_state["bearish_cisd"]["invalidate_above"]
#     ):

#         print("Weekly Bearish CISD invalidated")

#         weekly_state["bearish_cisd"] = None

#     #
#     # --------------------------------------------------
#     # Detect Bullish CISD
#     # --------------------------------------------------
#     #

#     recent_bearish = _find_recent_bearish_candle(
#         candles_1h
#     )

#     if (
#         recent_bearish is not None
#         and
#         last_closed["close"]
#         >
#         recent_bearish["open"]
#     ):

#         if weekly_state["bullish_cisd"] is None:

#             print("Weekly Bullish CISD formed")

#             weekly_state["bullish_cisd"] = {
#                 "timestamp": last_closed["timestamp"],
#                 "cisd_level": recent_bearish["open"],
#                 "invalidate_below": recent_bearish["low"],
#             }

#     #
#     # --------------------------------------------------
#     # Detect Bearish CISD
#     # --------------------------------------------------
#     #

#     recent_bullish = _find_recent_bullish_candle(
#         candles_1h
#     )

#     if (
#         recent_bullish is not None
#         and
#         last_closed["close"]
#         <
#         recent_bullish["open"]
#     ):

#         if weekly_state["bearish_cisd"] is None:

#             print("Weekly Bearish CISD formed uuu")

#             weekly_state["bearish_cisd"] = {
#                 "timestamp": last_closed["timestamp"],
#                 "cisd_level": recent_bullish["open"],
#                 "invalidate_above": recent_bullish["high"],
#             }

#     #
#     # --------------------------------------------------
#     # Detect New FVGs
#     # --------------------------------------------------
#     #

#     bullish_fvg, bearish_fvg = _detect_latest_fvg(
#         candles_1h
#     )

#     if (
#         bullish_fvg is not None
#         and (
#             weekly_state["bullish_fvg"] is None
#             or weekly_state["bullish_fvg"]["state"] == "reclaimed"
#         )
#     ):

#         print("Weekly Bullish FVG formed")

#         weekly_state["bullish_fvg"] = bullish_fvg

#     if (
#         bearish_fvg is not None
#         and (
#             weekly_state["bearish_fvg"] is None
#             or weekly_state["bearish_fvg"]["state"] == "reclaimed"
#         )
#     ):

#         print("Weekly Bearish FVG formed")

#         weekly_state["bearish_fvg"] = bearish_fvg

#     #
#     # --------------------------------------------------
#     # Update FVG States
#     # --------------------------------------------------
#     #

#     if weekly_state["bullish_fvg"] is not None:

#         if (
#             last_closed["close"]
#             <
#             weekly_state["bullish_fvg"]["low"]
#         ):

#             print("Weekly Bullish FVG reclaimed")

#             weekly_state["bullish_fvg"]["state"] = "reclaimed"

#         elif (
#             last_closed["low"]
#             <
#             weekly_state["bullish_fvg"]["high"]
#         ):

#             weekly_state["bullish_fvg"]["state"] = "mitigated"

#     if weekly_state["bearish_fvg"] is not None:

#         if (
#             last_closed["close"]
#             >
#             weekly_state["bearish_fvg"]["high"]
#         ):

#             print("Weekly Bearish FVG reclaimed")
#             weekly_state["bearish_fvg"]["state"] = "reclaimed"

#         elif (
#             last_closed["high"]
#             >
#             weekly_state["bearish_fvg"]["low"]
#         ):

#             weekly_state["bearish_fvg"]["state"] = "mitigated"

#     #
#     # --------------------------------------------------
#     # Determine HTF Bias
#     # --------------------------------------------------
#     #

#     weekly_state["bias"] = None
#     weekly_state["bias_reason"] = None

#     #
#     # Strong Bullish
#     #

#     if (
#         weekly_state["bullish_cisd"]
#         and
#         weekly_state["bullish_fvg"]
#         and
#         weekly_state["bullish_fvg"]["state"]
#         != "reclaimed"
#     ):

#         weekly_state["bias"] = "bullish"
#         weekly_state["bias_reason"] = (
#             "bullish_cisd_plus_bullish_fvg"
#         )

#     #
#     # Strong Bearish
#     #

#     elif (
#         weekly_state["bearish_cisd"]
#         and
#         weekly_state["bearish_fvg"]
#         and
#         weekly_state["bearish_fvg"]["state"]
#         != "reclaimed"
#     ):

#         weekly_state["bias"] = "bearish"
#         weekly_state["bias_reason"] = (
#             "bearish_cisd_plus_bearish_fvg"
#         )

#     #
#     # Conflicting CISDs
#     #

#     elif (
#         weekly_state["bullish_cisd"]
#         and
#         weekly_state["bearish_cisd"]
#     ):

#         weekly_state["bias"] = "neutral"
#         weekly_state["bias_reason"] = (
#             "conflicting_cisds"
#         )

#     #
#     # Weak Bullish
#     #

#     elif weekly_state["bullish_cisd"]:

#         weekly_state["bias"] = "bullish"
#         weekly_state["bias_reason"] = (
#             "bullish_cisd_only"
#         )

#     #
#     # Weak Bearish
#     #

#     elif weekly_state["bearish_cisd"]:

#         weekly_state["bias"] = "bearish"
#         weekly_state["bias_reason"] = (
#             "bearish_cisd_only"
#         )

#     #
#     # Weekly Open Fallback
#     #

#     else:

#         if (
#             weekly_state["price_location"]
#             == "above"
#         ):

#             weekly_state["bias"] = "bullish"
#             weekly_state["bias_reason"] = (
#                 "above_weekly_open"
#             )

#         else:

#             weekly_state["bias"] = "bearish"
#             weekly_state["bias_reason"] = (
#                 "below_weekly_open"
#             )

#     return weekly_state

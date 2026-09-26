from datetime import datetime, timedelta

from market_data.candle_builder.htf_candle_builder import UTC_TZ

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

        "active_bullish_fvgs": [],
        "active_bearish_fvgs": [],
        "active_bullish_cisds": [],
        "active_bearish_cisds": [],

        "bias": None,
        "bias_reason": None,

        "bullish_ready": False,
        "bearish_ready": False,
        "flush": {"status": False, "time": None},
        "rocket": {"status": False, "time": None},
    }

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

    last_dt_ny = candles_1h[-1].timestamp
    

    week_start_ny = get_week_start(last_dt_ny)

    return [
        c
        for c in candles_1h
        if c.timestamp >= week_start_ny
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
    # print("c1: ", c1)
    # print("c2: ", c2)
    # print("c3: ", c3)

    if c3.low > c1.high:

        bullish_fvg = {
            "low": c1.high,
            "high": c3.low,
            "ce": (c1.high + c3.low) / 2,
            "state": "open",
            "timestamp": c3.timestamp,
        }

    #
    # Bearish FVG
    #

    elif c3.high < c1.low:
        print("c3 high < c1 low")

        bearish_fvg = {
            "low": c3.high,
            "high": c1.low,
            "ce": (c3.high + c1.low) / 2,
            "state": "open",
            "timestamp": c3.timestamp,
        }

    return bullish_fvg, bearish_fvg

def _find_recent_bullish_candle(candles):

    for candle in reversed(candles[:-1]):

        if candle.close > candle.open:
            return candle

    return None

def _find_recent_bearish_candle(candles):

    for candle in reversed(candles[:-1]):

        if candle.close < candle.open:
            return candle

    return None


def build_weekly_state(
    candles_1d,
    candles_1h,
    current_day_start_ny,
    instrument,
    week_start_ny
):
    """
    Build weekly state by replaying all completed 1H candles
    from Sunday 18:00 up to (but not including) current_day_start.
    """

    weekly_state = initialize_weekly_state(instrument)
    
    # week_start_ny = get_week_start(current_day_start_ny)
    print("current_day_start_ny:", current_day_start_ny)
    print("WEEK START:", week_start_ny)
    print("WEEK START UTC:", week_start_ny.astimezone(UTC_TZ))

    
    week_open_candle = None
    week_open_candle = next(
        (
            candle
            for candle in candles_1h
            if candle.timestamp == week_start_ny
        ),
        None,
    ) 
    
    print("weekly_open_candle: ", week_open_candle)
    weekly_state["weekly_open"] = week_open_candle.open

    history = []

    for candle in candles_1h:

        ts_ny = candle.timestamp
        if week_start_ny <= ts_ny < current_day_start_ny:    
            history.append(candle)

    weekly_state["week_start"] = week_start_ny
    # we need to loop through these candles from start of week to start of current day and update weekly state
    candles_to_update_state = []
    for candle in history:
        
        candles_to_update_state.append(candle)
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

    Structure lifecycle
    -------------------
    First CISD/FVG of a direction:
        -> anchor

    Subsequent CISD/FVG:
        -> active list
        -> new_* points to latest active structure

    Reclaimed/invalidated:
        -> removed from active list
        -> new_* falls back to previous active structure

    Mitigated FVG:
        -> remains active
        -> remains eligible to be new_*

    Bias
    ----
    Below weekly open:
        bearish CISD + bearish FVG -> bearish
        bullish CISD + bullish FVG -> neutral_bullish

    Above weekly open:
        bullish CISD + bullish FVG -> bullish
        bearish CISD + bearish FVG -> neutral_bearish

    A transition from bearish -> bullish requires the
    original bearish anchor pair to be invalidated.

    A transition from bullish -> bearish requires the
    original bullish anchor pair to be invalidated.
    """

    if len(candles_1h) < 3:
        return weekly_state
    # --------------------------------------------------
    # Ensure active lists exist
    # --------------------------------------------------

    if weekly_state["active_bullish_fvgs"] is None:
        weekly_state["active_bullish_fvgs"] = []

    if weekly_state["active_bearish_fvgs"] is None:
        weekly_state["active_bearish_fvgs"] = []

    if weekly_state["active_bullish_cisds"] is None:
        weekly_state["active_bullish_cisds"] = []

    if weekly_state["active_bearish_cisds"] is None:
        weekly_state["active_bearish_cisds"] = []
    
    current_price = candles_1h[-1].close
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

    # --------------------------------------------------
    # Detect Bullish CISD
    # --------------------------------------------------

    recent_bearish = _find_recent_bearish_candle(
        candles_1h
    )

    if (
        recent_bearish is not None
        and last_closed.close > recent_bearish.open
        and last_closed.timestamp != recent_bearish.timestamp
    ):

        bullish_cisd = {
            "timestamp": last_closed.timestamp,
            "cisd_level": recent_bearish.open,
            "invalidate_below": (
                recent_bearish.close
                if recent_bearish.close < last_closed.open
                else last_closed.open
            ),
        }

        print("Bullish CISD detected:", bullish_cisd)

        # First bullish CISD = anchor
        if weekly_state["bullish_cisd"] is None:

            weekly_state["bullish_cisd"] = bullish_cisd

            weekly_state["active_bullish_cisds"].append(
                bullish_cisd
            )

            print(
                "Weekly Bullish CISD anchor formed:",
                weekly_state["bullish_cisd"]
            )

        else:

            # Subsequent bullish CISD
            weekly_state["active_bullish_cisds"].append(
                bullish_cisd
            )

            weekly_state["new_bullish_cisd"] = bullish_cisd

            print(
                "Weekly New Bullish CISD formed:",
                weekly_state["new_bullish_cisd"]
            )

    # --------------------------------------------------
    # Detect Bearish CISD
    # --------------------------------------------------

    recent_bullish = _find_recent_bullish_candle(
        candles_1h
    )

    if (
        recent_bullish is not None
        and last_closed.close < recent_bullish.open
        and last_closed.timestamp != recent_bullish.timestamp
    ):

        bearish_cisd = {
            "timestamp": last_closed.timestamp,
            "cisd_level": recent_bullish.open,
            "invalidate_above": (
                recent_bullish.close
                if recent_bullish.close > last_closed.open
                else last_closed.open
            ),
        }

        print("Bearish CISD detected:", bearish_cisd)

        # First bearish CISD = anchor
        if weekly_state["bearish_cisd"] is None:

            weekly_state["bearish_cisd"] = bearish_cisd

            weekly_state["active_bearish_cisds"].append(
                bearish_cisd
            )

            print(
                "Weekly Bearish CISD anchor formed:",
                weekly_state["bearish_cisd"]
            )

        else:

            # Subsequent bearish CISD
            weekly_state["active_bearish_cisds"].append(
                bearish_cisd
            )

            weekly_state["new_bearish_cisd"] = bearish_cisd

            print(
                "Weekly New Bearish CISD formed:",
                weekly_state["new_bearish_cisd"]
            )



    # --------------------------------------------------
    # Detect New FVGs
    # --------------------------------------------------

    bullish_fvg, bearish_fvg = _detect_latest_fvg(
        candles_1h
    )

    print("bullish fvg:", bullish_fvg)
    print("bearish fvg:", bearish_fvg)

    # --------------------------------------------------
    # Store Bullish FVG
    # --------------------------------------------------

    if bullish_fvg is not None:

        print("Fresh bullish FVG detected")

        # First bullish FVG = anchor
        if weekly_state["bullish_fvg"] is None:

            weekly_state["bullish_fvg"] = bullish_fvg

            weekly_state["active_bullish_fvgs"].append(
                bullish_fvg
            )

            print(
                "Weekly Bullish FVG anchor formed:",
                weekly_state["bullish_fvg"]
            )

        else:

            # Subsequent bullish FVG
            weekly_state["active_bullish_fvgs"].append(
                bullish_fvg
            )

            weekly_state["new_bullish_fvg"] = bullish_fvg

            print(
                "Weekly New Bullish FVG formed:",
                weekly_state["new_bullish_fvg"]
            )

    # --------------------------------------------------
    # Store Bearish FVG
    # --------------------------------------------------

    if bearish_fvg is not None:

        print("Fresh bearish FVG detected")

        # First bearish FVG = anchor
        if weekly_state["bearish_fvg"] is None:

            weekly_state["bearish_fvg"] = bearish_fvg

            weekly_state["active_bearish_fvgs"].append(
                bearish_fvg
            )

            print(
                "Weekly Bearish FVG anchor formed:",
                weekly_state["bearish_fvg"]
            )

        else:

            # Subsequent bearish FVG
            weekly_state["active_bearish_fvgs"].append(
                bearish_fvg
            )

            weekly_state["new_bearish_fvg"] = bearish_fvg

            print(
                "Weekly New Bearish FVG formed:",
                weekly_state["new_bearish_fvg"]
            )

    # ==================================================
    # INVALIDATE / RECLAIM CISDs
    # ==================================================

    # --------------------------------------------------
    # Bullish CISDs
    # --------------------------------------------------

    bullish_cisds = weekly_state["active_bullish_cisds"]

    for cisd in bullish_cisds[:]:

        if last_closed.close < cisd["invalidate_below"]:

            print(
                "Bullish CISD invalidated:",
                cisd
            )

            bullish_cisds.remove(cisd)

            # If this was the anchor, the anchor is gone
            if weekly_state["bullish_cisd"] is cisd:
                weekly_state["bullish_cisd"] = None

    # Latest surviving bullish CISD after anchor
    if weekly_state["bullish_cisd"] is not None:

        post_anchor = [
            cisd
            for cisd in bullish_cisds
            if cisd is not weekly_state["bullish_cisd"]
        ]

        weekly_state["new_bullish_cisd"] = (
            post_anchor[-1]
            if post_anchor
            else None
        )

    else:
        weekly_state["new_bullish_cisd"] = (
            bullish_cisds[-1]
            if bullish_cisds
            else None
        )

    # --------------------------------------------------
    # Bearish CISDs
    # --------------------------------------------------

    bearish_cisds = weekly_state["active_bearish_cisds"]

    for cisd in bearish_cisds[:]:

        if last_closed.close > cisd["invalidate_above"]:

            print(
                "Bearish CISD invalidated:",
                cisd
            )

            bearish_cisds.remove(cisd)

            if weekly_state["bearish_cisd"] is cisd:
                weekly_state["bearish_cisd"] = None

    # Latest surviving bearish CISD after anchor
    if weekly_state["bearish_cisd"] is not None:

        post_anchor = [
            cisd
            for cisd in bearish_cisds
            if cisd is not weekly_state["bearish_cisd"]
        ]

        weekly_state["new_bearish_cisd"] = (
            post_anchor[-1]
            if post_anchor
            else None
        )

    else:
        weekly_state["new_bearish_cisd"] = (
            bearish_cisds[-1]
            if bearish_cisds
            else None
        )

    # ==================================================
    # UPDATE FVG STATES
    # ==================================================

    # --------------------------------------------------
    # Bullish FVGs
    # --------------------------------------------------

    bullish_fvgs = weekly_state["active_bullish_fvgs"]

    for fvg in bullish_fvgs[:]:

        # ----------------------------------------------
        # Reclaim
        # ----------------------------------------------

        if (
            last_closed.close < fvg["low"]
            and fvg["state"] != "reclaimed"
        ):

            print(
                "Weekly Bullish FVG reclaimed:",
                fvg
            )

            fvg["state"] = "reclaimed"

            bullish_fvgs.remove(fvg)

            # If this was the anchor, remove anchor
            if weekly_state["bullish_fvg"] is fvg:
                weekly_state["bullish_fvg"] = None

            # Rocket is no longer active for this FVG
            if weekly_state["rocket"]["time"] == fvg.get("timestamp"):
                weekly_state["rocket"]["status"] = False
                weekly_state["rocket"]["time"] = None

        # ----------------------------------------------
        # Mitigation
        # ----------------------------------------------

        elif (
            last_closed.low < fvg["high"]
            and fvg["state"] == "open"
        ):
            fvg["state"] = "mitigated"

            weekly_state["rocket"]["status"] = True
            weekly_state["rocket"]["time"] = last_closed.timestamp

            print(
                "Weekly Bullish FVG mitigated:",
                fvg
            )

    # Determine latest surviving bullish FVG
    if weekly_state["bullish_fvg"] is not None:

        post_anchor = [
            fvg
            for fvg in bullish_fvgs
            if fvg is not weekly_state["bullish_fvg"]
        ]

        weekly_state["new_bullish_fvg"] = (
            post_anchor[-1]
            if post_anchor
            else None
        )

    else:
        weekly_state["new_bullish_fvg"] = (
            bullish_fvgs[-1]
            if bullish_fvgs
            else None
        )

    # --------------------------------------------------
    # Bearish FVGs
    # --------------------------------------------------

    bearish_fvgs = weekly_state["active_bearish_fvgs"]

    for fvg in bearish_fvgs[:]:

        # ----------------------------------------------
        # Reclaim
        # ----------------------------------------------

        if (
            last_closed.close > fvg["high"]
            and fvg["state"] != "reclaimed"
        ):

            print(
                "Weekly Bearish FVG reclaimed:",
                fvg
            )

            fvg["state"] = "reclaimed"

            bearish_fvgs.remove(fvg)

            if weekly_state["bearish_fvg"] is fvg:
                weekly_state["bearish_fvg"] = None

            if weekly_state["flush"]["time"] == fvg.get("timestamp"):
                weekly_state["flush"]["status"] = False
                weekly_state["flush"]["time"] = None

        # ----------------------------------------------
        # Mitigation
        # ----------------------------------------------

        elif (
            last_closed.high > fvg["low"]
            and fvg["state"] == "open"
        ):

            fvg["state"] = "mitigated"

            weekly_state["flush"]["status"] = True
            weekly_state["flush"]["time"] = last_closed.timestamp

            print(
                "Weekly Bearish FVG mitigated:",
                fvg
            )

    # Determine latest surviving bearish FVG
    if weekly_state["bearish_fvg"] is not None:

        post_anchor = [
            fvg
            for fvg in bearish_fvgs
            if fvg is not weekly_state["bearish_fvg"]
        ]

        weekly_state["new_bearish_fvg"] = (
            post_anchor[-1]
            if post_anchor
            else None
        )

    else:
        weekly_state["new_bearish_fvg"] = (
            bearish_fvgs[-1]
            if bearish_fvgs
            else None
        )

    # ==================================================
    # DETERMINE WEEKLY BIAS
    # ==================================================

    bullish_cisd_exists = (
        weekly_state["bullish_cisd"] is not None
        or weekly_state["new_bullish_cisd"] is not None
    )

    bearish_cisd_exists = (
        weekly_state["bearish_cisd"] is not None
        or weekly_state["new_bearish_cisd"] is not None
    )

    bullish_fvg_exists = (
        weekly_state["bullish_fvg"] is not None
        or weekly_state["new_bullish_fvg"] is not None
    )

    bearish_fvg_exists = (
        weekly_state["bearish_fvg"] is not None
        or weekly_state["new_bearish_fvg"] is not None
    )

    # A complete directional structure requires BOTH CISD + FVG
    bullish_structure = (
        bullish_cisd_exists
        and bullish_fvg_exists
    )

    bearish_structure = (
        bearish_cisd_exists
        and bearish_fvg_exists
    )

    # Any opposing structure — used for neutral_bullish / neutral_bearish
    bullish_structure_exists = (
        bullish_cisd_exists
        or bullish_fvg_exists
    )

    bearish_structure_exists = (
        bearish_cisd_exists
        or bearish_fvg_exists
    )

    
    # ------------------------------------------------------------
    # BELOW WEEKLY OPEN
    # ------------------------------------------------------------
    #
    # Bullish CISD + Bullish FVG below open:
    #
    #   No bearish structure  -> bullish
    #   Bearish structure     -> neutral_bullish
    #
    # ------------------------------------------------------------

    if weekly_state["price_location"] == "below":

        if bullish_structure:

            if bearish_structure_exists:
                weekly_state["bias"] = "neutral_bullish"
                weekly_state["bias_reason"] = (
                    "Bullish CISD and FVG formed below weekly open "
                    "while bearish structure remains."
                )

            else:
                weekly_state["bias"] = "bullish"
                weekly_state["bias_reason"] = (
                    "Bullish CISD and FVG formed below weekly open "
                    "with no bearish structure remaining."
                )
        elif bearish_structure_exists:

            weekly_state["bias"] = "bearish"
            weekly_state["bias_reason"] = (
                "Price is below weekly open with bearish structure "
                "and no complete bullish structure."
            )

        else:

            weekly_state["bias"] = "neutral"
            weekly_state["bias_reason"] = (
                "Price is below weekly open with no bullish or bearish "
                "structure."
            )


    # ------------------------------------------------------------
    # ABOVE WEEKLY OPEN
    # ------------------------------------------------------------
    #
    # Bearish CISD + Bearish FVG above open:
    #
    #   No bullish structure  -> bearish
    #   Bullish structure     -> neutral_bearish
    #
    # ------------------------------------------------------------

    elif weekly_state["price_location"] == "above":

        if bearish_structure:

            if bullish_structure_exists:
                weekly_state["bias"] = "neutral_bearish"
                weekly_state["bias_reason"] = (
                    "Bearish CISD and FVG formed above weekly open "
                    "while bullish structure remains."
                )

            else:
                weekly_state["bias"] = "bearish"
                weekly_state["bias_reason"] = (
                    "Bearish CISD and FVG formed above weekly open "
                    "with no bullish structure remaining."
                )

        elif bullish_structure_exists:

            weekly_state["bias"] = "bullish"
            weekly_state["bias_reason"] = (
                "Price is above weekly open with bullish structure "
                "and no complete bearish structure."
            )

        else:

            weekly_state["bias"] = "neutral"
            weekly_state["bias_reason"] = (
                "Price is above weekly open with no bullish or bearish "
                "structure."
            )

    else:
        weekly_state["bias"] = "neutral"
        weekly_state["bias_reason"] = "weekly open location unavailable"

    print("weekly bias: ", weekly_state["bias"])
    print("weekly reason: ", weekly_state["bias_reason"])
    return weekly_state


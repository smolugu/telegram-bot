from data.models.compression import detect_compression
from data.models.displacement import is_displacement_candle
from helpers.ib_helpers import check_ib_rejection
from helpers.sessions import in_session
from helpers.time_windows import get_active_window


from datetime import datetime
from zoneinfo import ZoneInfo

# decision flow: context layer, direction layer and validation layer
def should_take_trade(context, setup):
    
    # context
    if context.chop:
        return False
    if context.atr_usage > 0.9:
        if setup.direction == context.direction:
            return False # block continuation
    
    # base setup
    if not (setup.sweep and setup.ob):
        return False
    # Filters
    score = 0
    if setup.smt:
        score += 2
    if setup.key_level:
        score += 2
    if setup.displacement:
        score += 3
    if score < 4:
        return False
    return True


# context to track the formation of low or high of the day on 1h timeframe, sweep of previous day high/low 
# and formation of 1h cisd will be a strong indication of reversal setup. 
# we can also use fvg formation as an additional layer of confirmation or disqualification depending on the context.
def track_asia_context(
    candles_1h,
    pdh,
    pdl,
    weekly_high,
    weekly_low,
    tz_str="America/New_York"):

    tz = ZoneInfo(tz_str)

    context = {
        "swept_pdh": False,
        "swept_pdl": False,

        "cisd": None,  # "bullish" or "bearish"
        "cisd_candle": None,

        "fvg": None,  # {"type": "bullish"/"bearish", "low": x, "high": y}

        "asia_high": None,
        "asia_low": None,

        "hod_candidate": None,
        "lod_candidate": None,

        "weekly_high_taken": False,
        "weekly_low_taken": False
    }

    prev_candle = None
    prev_prev_candle = None

    for i, c in enumerate(candles_1h):

        high = c["high"]
        low = c["low"]
        close = c["close"]
        open_ = c["open"]

        # -------------------------
        # Track Asia High/Low
        # -------------------------
        if context["asia_high"] is None or high > context["asia_high"]:
            context["asia_high"] = high

        if context["asia_low"] is None or low < context["asia_low"]:
            context["asia_low"] = low

        # -------------------------
        # Sweep PDH / PDL
        # -------------------------
        if high > pdh:
            context["swept_pdh"] = True

        if low < pdl:
            context["swept_pdl"] = True

        # -------------------------
        # Weekly High / Low Sweep
        # -------------------------
        if high > weekly_high:
            context["weekly_high_taken"] = True

        if low < weekly_low:
            context["weekly_low_taken"] = True

        # -------------------------
        # Detect CISD (simple version)
        # -------------------------
        if prev_candle:

            # Bullish CISD
            if (
                context["swept_pdl"]
                and close > prev_candle["high"]
            ):
                context["cisd"] = "bullish"
                context["cisd_candle"] = c

            # Bearish CISD
            if (
                context["swept_pdh"]
                and close < prev_candle["low"]
            ):
                context["cisd"] = "bearish"
                context["cisd_candle"] = c

        # -------------------------
        # Detect FVG (3-candle model)
        # -------------------------
        if prev_prev_candle and prev_candle:

            # Bullish FVG
            if prev_prev_candle["high"] < c["low"]:
                context["fvg"] = {
                    "type": "bullish",
                    "low": prev_prev_candle["high"],
                    "high": c["low"],
                    "created_at": c["timestamp"]
                }

            # Bearish FVG
            if prev_prev_candle["low"] > c["high"]:
                context["fvg"] = {
                    "type": "bearish",
                    "low": c["high"],
                    "high": prev_prev_candle["low"],
                    "created_at": c["timestamp"]
                }

        prev_prev_candle = prev_candle
        prev_candle = c

    # -------------------------
    # Identify HOD / LOD candidates
    # -------------------------
    if context["cisd"] == "bearish" and context["swept_pdh"]:
        context["hod_candidate"] = context["asia_high"]

    if context["cisd"] == "bullish" and context["swept_pdl"]:
        context["lod_candidate"] = context["asia_low"]

    return context



def context_for_london(market_context):
    # check price delivery in asia and early london
    # check session direction and atr usage
    # atr_usage > 1, no smt confirmation needed
    # atr_usage < 0.9, require smt confirmation
    # when asia delivers, we need ib rejectin at 1am for reversal
    # get bias on 1hr, sweep of previous day and formation of 1h cisd
    require_smt_confirmation = False
    if market_context.atr_usage < 0.9:
        require_smt_confirmation = True

    return {
        "is_asia_choppy": False,  # update with actual logic
        "session_direction": market_context.session_direction,  # update with actual logic
        "require_smt_confirmation": require_smt_confirmation,  # update with actual logic
    }

def check_for_reversal_setup_confirmation(market_context, london_context, newyork_context, seven_hour_builder_candles, liquidity_levels_nq, liquidity_levels_es, candidate, last_closed_candle, current_30m_start, daily_atr, smt_summary):
    # get session time
    # bias from previous 7hr candle (ex: bearish)
    # price is below (bearish) previous 7hr candle and (or) rejecting previous 7hr ib
    # price should be below or rejecting current 7hr ib
    # if price is above current 7hr ib and rejecting previous 7hr ib = Manipulation of current 7hr
    # high = last_closed_candle["high"]
    # low = last_closed_candle["low"]
    # get seven hour candles
    seven_hour_candle_6pm = seven_hour_builder_candles["6PM"].values()
    seven_hour_candle_1am = seven_hour_builder_candles["1AM"].values()
    seven_hour_candle_8am = seven_hour_builder_candles["8AM"].values()
    
    window_name = get_active_window(current_30m_start)
    close = last_closed_candle["close"]
    high = last_closed_candle["high"]
    low = last_closed_candle["low"]

    # direction of trade
    look_for_shorts = False
    look_for_longs = False
    if candidate.side == "buy_side":
        look_for_shorts = True
    elif candidate.side == "sell_side":
        look_for_longs = True

    # displacement and atr check function
    def displacement_atr_filter():
        allow_shorts = True
        allow_longs = True
        filters_passed = False
        if (market_context.overnight_expansion or market_context.exhaustion):
            if market_context.session_direction == "bearish":
                print("overnight bearish expansion or exhausion. not allowing shorts")
                allow_shorts = False
            elif market_context.session_direction == "bullish":
                print("overnight bullish expansion or exhausion. not allowing shorts")
                allow_longs = False        
            else:
                print("step 4")
        
        print("inside last: ", candidate.instrument, candidate.sweep_and_ob_ce_confirmed)
        print("structure break: ", candidate.ob_data["structure_break"] if candidate.ob_data is not None else None, "strong_body_displacement: ", candidate.ob_data["strong_body_displacement"] if candidate.ob_data is not None else None)
        print("ob body range: ", candidate.ob_data["ob_body_range"] if candidate.ob_data is not None else None)
        if candidate.sweep_and_ob_ce_confirmed:
            filters_passed = True
            print("aksnkdna 2")
        elif candidate.sweep_and_ob_confirmed:
            if candidate.ob_data is not None:
                if candidate.ob_data["structure_break"] and candidate.ob_data["ob_body_range"] > 0.5:
                    filters_passed = True
                    print("lklkl 2")
        elif candidate.ob_data is not None:
            if candidate.ob_data["structure_break"] and candidate.ob_data["ob_body_range"] > 0.5:
                filters_passed = True
                print("aksnkdnaasdadasdas 2")
            elif candidate.ob_data["strong_body_displacement"]:
                filters_passed = True
                print("strong body displacement, allowing reversal")
            else:
                print("no strong body displacement, not allowing reversal")
        if look_for_longs and not allow_longs:
            print("market exhauted, not allowing longs")
            filters_passed = False
        if look_for_shorts and not allow_shorts:
            print("market exhauted, not allowing shorts")
            filters_passed = False
        
        return filters_passed

    def smt_check():
        is_smt = False
        print("smt summary: ", smt_summary)
        if look_for_shorts:
            if market_context.bearish_smt_1h is not None or market_context.bearish_smt_30m is not None:
                is_smt = True
        elif look_for_longs:
            if market_context.bullish_smt_1h is not None or market_context.bullish_smt_30m is not None:
                is_smt = True
        return is_smt
    
    def determine_daily_bias():
        bias = "neutral"
        return bias
    # sweep candle in totally below ib
    def below_ib(last_closed_candle, ib_low):
        if last_closed_candle["high"] < ib_low:
            return True
        return False
    
    # sweep candle is totally above ib
    def above_ib(last_closed_candle, ib_high):
        if last_closed_candle["low"] > ib_high:
            return True
        return False

    def filter_longs_london(look_for_longs, session_direction, atr_usage, is_smt):
        if not look_for_longs:
            return False
        if session_direction == "bullish":
            if atr_usage > 0.9:
                look_for_longs = False
                print("not allowing longs as atr > 0.9")
        elif session_direction == "bearish":
            if atr_usage < 0.9 and not is_smt:
                look_for_longs = False
                print("not allowing longs as atr < 0.9 and no smt")
        return look_for_longs

    def filter_shorts_london(look_for_shorts, session_direction, atr_usage, is_smt):
        if not look_for_shorts:
            return False
        if session_direction == "bearish":
            if atr_usage > 0.9:
                look_for_shorts = False
                print("not allowing shorts as atr > 0.9")
        elif session_direction == "bullish":
            if atr_usage < 0.9 and not is_smt:
                look_for_shorts = False
                print("not allowing shorts as atr < 0.9 and no smt")
        return look_for_shorts

    reversal_confirmation = False
    is_reversal_candidate = False
    ib_entry = None
    ib_stop_loss = None
    # direction = "bullish" if candidate.side == "sell_side" else "bearish"
    # check displacement, use displacement for confirmation but not disqualification, as some reversals can be disguised as displacement candles.
    # is_displacement = is_displacement_candle(
    #     last_closed_candle,
    #     daily_atr,
    #     direction,
    #     None,
    # )
    asia_swept = False

    # check session, identify session
    is_london_killzone = in_session(current_30m_start, 3, 0, 5, 0)
    is_post_london_killzone = in_session(current_30m_start, 5, 0, 6, 30)
    is_post_1AM_IB = in_session(current_30m_start, 2, 30, 8, 0)
    is_post_8AM_IB = in_session(current_30m_start, 9, 30, 15, 0 )
    # in ny killzone lets include 8am wick window as out setup forms around 7hr wicks
    is_ny_am_killzone = in_session(current_30m_start, 8, 0, 11, 30)
    is_ny_lunch_time = in_session(current_30m_start, 12, 0, 13, 30)
    expansion_setup = False
    if market_context.compression_flags["nested_1_in_18"] or market_context.compression_flags["engulfing_1_over_18"]:
        # sweep is valid, already checked
        # check for displacement and structure break
        expansion_setup = True
    if window_name is "7h_wick_0800" and is_ny_am_killzone:
        is_ny_am_killzone = False
    print("----------------------------------------")
    print(f"Candidate: {candidate.instrument} {candidate.side}")
    print("is_london_killzone: ", is_london_killzone, " | is_post_london_killzone:", is_post_london_killzone, " |  is_ny_am_killzone: ", is_ny_am_killzone, " | is_ny_lunch_time: ", is_ny_lunch_time, " | window_name: ", window_name)
    print("market context: ", market_context.values())

    print("bullish 1h smt: ", market_context.bullish_smt_1h, "bearish 1h smt: ", market_context.bearish_smt_1h, "bullish 30m swing smt: ", market_context.bullish_smt_30m, "bearish 30m swing smt: ", market_context.bearish_smt_30m)
    # print("smt summary: ", smt_summary)
    
    # bias = prev_seven_hour_candle["bias"]

    
    session_direction = market_context.session_direction
    atr_usage = market_context.atr_usage
    london_context_from_market_context = context_for_london(market_context)

    # smt check
    is_smt = smt_check()

    # daily bias
    daily_bias = determine_daily_bias()

    # -----------------------------------------------
    # disable or allow longs and shorts based on atr_usage and smt
    # -----------------------------------------------
    
    # -----------------------------------------------
    if is_post_1AM_IB:
        # get IB zones
        print("post 1am IB zone:")
        # Asia and London compression
        #   - if 1am doesn't go beyond 18 IB and stays inside, with 1am IB forming inside 18 IB, wait for 8AM candle reaction at compression range of 18IB and 1am IB. implement this in 8am wick window.
        # Asia compression, London expansion or London expansion - recompression
        #   - London expansion: (needs smt at 1am sweep for expansion, otherwise price can continue from upper section of 18 IB)
        #       - if 1am starts inside 18 IB, we have asia compression, we shall look for sweep of 18 IB extremes and high and low of 18 7hr candle and strong rejection back inside 18 IB - 2 AM Reversal, 3AM continuation, Expansion setup
        #           - look for displacement after sweep, smt confirmation (reversal, need SMT as it is early in price delivery)
        #           - if not displacement and SMT after 1am Sweep, look for continuation from 18 IB CE preferebly with SMT
        #           
        #   - London expansion - re-compression
        #       - 1am engulfs 18 IB with no displacement, we have expansion followed by recompression, setup at 6am or 8am with sweep of extremes at compression range of 1am IB
        # - if 1am IB engulfs 18 IB, we have expansion
        #   - if there is a displacement in IB direction, then continuation in the direction of 1am IB expansion
        #   - if there is no displacement, expect recompression, wait for sweep of 1am IB extremes, reversal expansion from sweep of the extremes of 1am compression range
        
        # # wait for sweep of compression range / structure range
            # at this point, invalid sweeps are already being rejected after sweep detection
            # even inducement is checked for nq and es with 10 and 3 points as buffer respectively
            # current sweep is the sweep of compression range
            # there is a candidate -> valid sweep. check for bias, ib rejection, compression context, smt, 
            # expansion trade confirmation
            # get ib reaction data
        if london_context.structure["compression"] and london_context.structure["ib_relationship"] == "inside":
            # trade ready for expansion.
            # get htf bias, displacement, fvg imbalance, smt.
            # at this point price is rejecting IB18 low or high
            # apply atr and displacement filter
            passed_atr_displacement_filter = displacement_atr_filter()
            print("post 1AM IB, passed atr displacemet filter: ", passed_atr_displacement_filter)
            reversal_confirmation = passed_atr_displacement_filter

            
        elif london_context.structure["ib_relationship"] == "engulfing":
            # this implies expansion, expect recompression or continuation of 1AM IB direction or reversal from IB low
            ## continuation
                # continuation here implies reversal from 1am 
                # 1am IB direction, displacement above 1am IB, retracement to top of 1am IB
                # formation of OB after 2am IB in 1AM IB direction
            
            # continuation: ib direction, rejection from ib extreme or ce + rejection of 2am IB + no deep retracement into engulfing range
            # ib direction
            direction_1am_ib = london_context.structure["ib_direction_1"]
            allow_trade = False
            if look_for_longs and direction_1am_ib == "bullish":
                allow_trade = True
            elif look_for_shorts and direction_1am_ib == "bearish":
                allow_trade = True
            # should reject IB_18 amd IB_2. no deep retracement covers rejection of IB_18
            rejection_of_ib_2 = False
            if look_for_shorts:
                if london_context.ib_2["direction"] == "bullish" and last_closed_candle["close"] < london_context.ib_2["open"]:
                    rejection_of_ib_2 = True
                elif london_context.ib_2["direction"] == "bearish" and not last_closed_candle["close"] > london_context.ib_2["open"]:
                    rejection_of_ib_2 = True
            elif look_for_longs:
                if london_context.ib_2["direction"] == "bearish" and last_closed_candle["close"] > london_context.ib_2["open"]:
                    rejection_of_ib_2 = True
                elif london_context.ib_2["direction"] == "bullish" and not last_closed_candle["close"] < london_context.ib_2["open"]:
                    rejection_of_ib_2 = True
                
            if allow_trade and rejection_of_ib_2 and london_context.structure["is_strong_body"] and not london_context.structure["engulfing_deep_retracement"]:
                reversal_confirmation = True

                
            ## reversal
                # bearish 1am Ib -> deep retracement -> rejection of ce -> strong displacement

            ## re-compression
                # deep retracement -> inside 1am IB extremes

        elif london_context.structure["ib_relationship"] == "overlap":
            print("weak compression - london overlap")
            reversal_confirmation = False
            # weak compression
            # continuation with HTF confirmation mainly 1h CISD after sweep of key level (PDH/L)
                # bearish overlap
                    # 1am IB overlapping with 18 IB lows
                    # htf bearish confirmation - sweep of pdh (smt) with 1h CISD
                    # look for shorts below 2am IB
                # bullish overlap
                    # 1am IB overlapping with 18 IB highs
                    # htf bullish confirmation - sweep of pdl (smt) with 1h CISD
                    # look for longs above 2am IB
        else:
            print(" no compression during london, wait for 8am IB formation")
            reversal_confirmation = False

    elif is_post_8AM_IB:
        
        # compression
            # 8am IB inside 1am IB
            # 8am IB between 18 IB and 1am IB
        # Early expansion
            # 8am IB engulfs 1am IB
            ## continuation
                # continuation here implies reversal from 1am 
                # 1am IB direction, displacement above 1am IB, retracement to top of 1am IB
                # formation of OB after 2am IB in 1AM IB direction
            
        # continuation: ib direction, rejection from ib extreme or ce + rejection of 2am IB + no deep retracement into engulfing range
        # ib direction
        direction_8am_ib = newyork_context.structure["ib_direction_8"]
        # Ib_relationship: inside_1am, inside_18, engulfing_1am, engulfing_18, sandwich, above_1_18,
        # partial_overlap_bullish, partial_overlap_neutral, below_1_18, partial_overlap_bearish
        ib_relationship = newyork_context.structure["ib_relationship"]
        if ib_relationship in ("inside_1am", "inside_18"):
            print("8am compression: ", ib_relationship, "sweep info: ", newyork_context.sweep)
            print("ib18_above_ib1: ", newyork_context.structure["ib18_above_ib1"])
            print("ib1_above_ib18: ", newyork_context.structure["ib18_below_ib1"])
            # at this point both nq and es have swept range high or low, or there is an SMT
            # in either case, allow both es and nq trades
            # main objective is time - SMT makes the time A+
            passed_atr_displacement_filter = displacement_atr_filter()
            print("post 8AM IB, passed atr displacemet filter: ", passed_atr_displacement_filter)
            reversal_confirmation = passed_atr_displacement_filter

            # 8am_inside_1am compression
            # 1am_IB above 18 IB. -> reversal shorts when atr exhaustion or pdh taken
            
            # 1am_IB below 18 Ib. -> reversal longs when atr exhaustion or pdl taken
            
            # if atr not exhausted, we need key level plus SMT

            # 8am_inside_18 ib compression
            # 1am Ib is above 18 ib, -> rebalance to equilibrium (sweep of range high)
        elif ib_relationship in ("engulfing_1am", "engulfing_18"):
            print("8am early expansion: ", ib_relationship)
            # ist scenario: deep retracement = re-compression, sweep is valid, checked after the initial
            # sweep is detected
            if newyork_context.phase == "recompression":
                # handle similar to inside compression
                passed_atr_displacement_filter = displacement_atr_filter()
                print("post 8AM IB, passed atr displacemet filter: ", passed_atr_displacement_filter)
                reversal_confirmation = passed_atr_displacement_filter
            else:
                # not recompression, we have sweep below ce of compression range.
                # we already have a valid ob. key OB similar to 2am IB is not required
                # we just need smt
                passed_atr_displacement_filter = displacement_atr_filter()
                print("post 8AM IB, passed atr displacemet filter: ", passed_atr_displacement_filter)
                reversal_confirmation = passed_atr_displacement_filter and is_smt

                
            # additional - pdh or pdl taken, atr exhausted, and onesided 8am IB

        elif ib_relationship == "sandwich":
            print("8am compression: ", ib_relationship)
            # no need to check displacement or atr exhaustion
            # valid sweep accounted for including inducement
            reversal_confirmation = True

        elif ib_relationship in ("above_1_18", "below_1_18"):
            print("8am market exhaustion or trending: ", ib_relationship)
            # main setup is reversal upon atr exhaustion
            passed_atr_displacement_filter = displacement_atr_filter()
            print("post 8AM IB, passed atr displacemet filter: ", passed_atr_displacement_filter)
            reversal_confirmation = passed_atr_displacement_filter and is_smt

        elif ib_relationship in ("partial_overlap_bullish", "partial_overlap_bearish"):
            # ib18 < ib1 < ib8 or ib18 > ib1 > 1b8
            # price movement in one direction
            # if atr not exhausted, anticipate retracement towards rebalance level taking range_high (bearish) or range_low (bullish)
            # if atr is exhausted, anticipate total reversal
            print("8am weak compression: ", ib_relationship)
            passed_atr_displacement_filter = displacement_atr_filter()
            print("post 8AM IB, passed atr displacemet filter: ", passed_atr_displacement_filter)
            reversal_confirmation = passed_atr_displacement_filter and is_smt

        elif ib_relationship in ("partial_overlap_bullish_neutral", "partial_overlap_bearish_neutral"):
            # high probability scenarios
                # if ib1 is below ib18 with ib8 above ib18, anticipate rebalance towards rebalance level and continue higher
                # if ib1 is above 1b18 with ib8 below ib18, anticipate rebalance towards rebalance level and continue lower
            # low probability
                # quick trade towards rebalance level as price is ranging
                # quick or short trade to rebalance level and Ib
            print("8am weak compression -> will range or continue from rebalance level: ", ib_relationship)
            passed_atr_displacement_filter = displacement_atr_filter()
            print("post 8AM IB, passed atr displacemet filter: ", passed_atr_displacement_filter)
            reversal_confirmation = passed_atr_displacement_filter and is_smt
            
        else:
            print("ib relationship scenario not captured: ", ib_relationship)
            reversal_confirmation = False

        

    
    elif is_london_killzone:
        
        ib_high_18 = seven_hour_candle_6pm["ib_high"]
        ib_low_18 = seven_hour_candle_6pm["ib_low"]
        ib_ce_18 = seven_hour_candle_6pm["ib_ce"]
        ib_high_1 = seven_hour_candle_1am["ib_high"]
        ib_low_1 = seven_hour_candle_1am["ib_low"]
        ib_ce_1 = seven_hour_candle_1am["ib_ce"]
        #  filter london longs and shorts
        allow_longs = filter_longs_london(look_for_longs, session_direction, atr_usage, is_smt)
        allow_shorts = filter_shorts_london(look_for_shorts, session_direction, atr_usage, is_smt)    

        # london killzone shorts
        if look_for_shorts and allow_shorts:
            
            is_below_ib_18 = False
            is_above_ib_18 = False
            is_below_ib_1 = False
            is_above_ib_1 = False
            
            is_ib_rejection_18 = check_ib_rejection(last_closed_candle, ib_high_18, ib_low_18, ib_ce_18, "bearish")
            is_ib_rejection_1 = check_ib_rejection(last_closed_candle, ib_high_1, ib_low_1, ib_ce_1, "bearish")
            
            is_below_ib_18 = below_ib(last_closed_candle, ib_low_18)
            is_above_ib_18 = above_ib(last_closed_candle, ib_high_18)
            is_below_ib_1 = below_ib(last_closed_candle, ib_low_1)
            is_above_ib_1 = above_ib(last_closed_candle, ib_high_1)
            # asia sweep confirmation
            # update with smt. either es or nq or both should sweep asia
            asia_swept = liquidity_levels_nq["asia_high"]["swept"] or liquidity_levels_es["asia_high"]["swept"]
            print("instrument, direction: ", candidate.instrument, "bearish")
            print("is_ib_rejection_18: ", is_ib_rejection_18)
            print("is_ib_rejection_1: ", is_ib_rejection_1)
            print("is_below_ib_18: ", is_below_ib_18)
            print("is_above_ib_18: ", is_above_ib_18)
            print("is_below_ib_1: ", is_below_ib_1)
            print("is_above_ib_1: ", is_above_ib_1)
            print("asia_swept: ", asia_swept)
            # is_displacement = is_displacement_candle(
            #     last_closed_candle,
            #     daily_atr,
            #     direction,
            #     None,
            # )
            
            # bearish confirmation rules
            if is_ib_rejection_18 and is_ib_rejection_1:
                reversal_confirmation = True
                print("ib_high_18: ", ib_high_18, "ib_high_1: ", ib_high_1)
                if close < ib_low_18:
                    ib_entry = ib_low_18
                    ib_stop_loss = ib_high_18
                elif close < ib_ce_18:
                    ib_entry = ib_ce_18
                    ib_stop_loss = ib_high_18
                elif close < ib_low_1:
                    ib_entry = ib_low_1
                    ib_stop_loss = ib_high_1
                elif close < ib_ce_1:
                    ib_entry = ib_ce_1
                    ib_stop_loss = ib_high_1
                    
                print("step1: strong IB rejection, reversal confirmation")
                print("IB entry: ", ib_entry, "IB stop loss: ", ib_stop_loss)
                
            # manipulation
            elif is_ib_rejection_18 and is_above_ib_1:
                reversal_confirmation = False
                is_reversal_candidate = True
                print("step2: reversal candidate")
            elif is_ib_rejection_18 and is_below_ib_1:
                reversal_confirmation = True
                if close < ib_low_18:
                    ib_entry = ib_low_18
                    ib_stop_loss = ib_high_18
                elif close < ib_ce_18:
                    ib_entry = ib_ce_18
                    ib_stop_loss = ib_high_18
                print("step3, entry, stop_loss: ", ib_entry, ib_stop_loss)
                
            elif is_ib_rejection_18 and close < ib_ce_1:
                reversal_confirmation = True
                ib_entry = ib_ce_1
                ib_stop_loss = ib_high_1
                print("reversal confirmation at close below ib ce of 8am, entry, stop_loss: ", ib_entry, ib_stop_loss)
            
            elif is_ib_rejection_1 and close < ib_ce_18:
                reversal_confirmation = True
                ib_entry = ib_ce_18
                ib_stop_loss = ib_high_18
                print("reversal confirmation at close below ib ce of 1am - 2. entry, SL", ib_entry, ib_stop_loss)
            
            # bearish confirmation
            elif is_ib_rejection_1 and is_below_ib_18:
                reversal_confirmation = True
                if close < ib_low_1:
                    ib_entry = ib_low_1
                    ib_stop_loss = ib_high_1
                elif close < ib_ce_1:
                    ib_entry = ib_ce_1
                    ib_stop_loss = ib_high_1
                print("step4, entry, stop_loss: ", ib_entry, ib_stop_loss)
                
            elif is_ib_rejection_1 and is_above_ib_18:
                reversal_confirmation = False
                is_reversal_candidate = True
                print("step5")
            else:
                reversal_confirmation = False
                print("step6")
            # final confirmation using smt
            #  allow trade for reversal candidate only when SMT is present
            if is_smt and is_reversal_candidate:
                print("Smt confirmation for reversal candidate, allowing trade")
                reversal_confirmation = True
            
            # if asia_swept:
            #     if reversal_confirmation:
            #         print("Ib reversal confirmation: ", reversal_confirmation)
            #         print("asia high swept, allowing trade")
            # else:          
            #     print("Ib reversal confirmation: ", reversal_confirmation)
            #     print("asia high not swept, not allowing trade")
            #     reversal_confirmation = False
        
        # london killzone shorts
        elif look_for_longs and allow_longs:
            
            is_below_ib_18 = False
            is_above_ib_18 = False
            is_below_ib_1 = False
            is_above_ib_1 = False
            
            is_ib_rejection_18 = check_ib_rejection(last_closed_candle, ib_high_18, ib_low_18, ib_ce_18, "bullish")
            is_ib_rejection_1 = check_ib_rejection(last_closed_candle, ib_high_1, ib_low_1, ib_ce_1, "bullish")
            
            is_below_ib_18 = below_ib(last_closed_candle, ib_low_18)
            is_above_ib_18 = above_ib(last_closed_candle, ib_high_18)
            is_below_ib_1 = below_ib(last_closed_candle, ib_low_1)
            is_above_ib_1 = above_ib(last_closed_candle, ib_high_1)
            # asia sweep confirmation
            # update with smt. either es or nq or both should sweep asia
            asia_swept = liquidity_levels_nq["asia_low"]["swept"] or liquidity_levels_es["asia_low"]["swept"]
            print("instrument, direction: ", candidate.instrument, "bullish")
            print("is_ib_rejection_18: ", is_ib_rejection_18)
            print("is_ib_rejection_1: ", is_ib_rejection_1)
            print("is_below_ib_18: ", is_below_ib_18)
            print("is_above_ib_18: ", is_above_ib_18)
            print("is_below_ib_1: ", is_below_ib_1)
            print("is_above_ib_1: ", is_above_ib_1)
            print("asia_swept: ", asia_swept)
            
            # bullish confirmation rules
            if is_ib_rejection_18 and is_ib_rejection_1:
                reversal_confirmation = True
                print("ib_high_18: ", ib_high_18, "ib_high_1: ", ib_high_1)
                # displacement is from not the ob confirmation candle but last closed candle which passed 
                # bullish confirmation rules around ib_18 and ib_1
                # get fvg imbalance inside the last closed candle and use it for entry and stop loss if it is there. otherwise use ib levels for entry and stop loss
                if close > ib_high_18:
                    ib_entry = ib_high_18
                    ib_stop_loss = ib_low_18
                elif close > ib_ce_18:
                    ib_entry = ib_ce_18
                    ib_stop_loss = ib_low_18
                elif close > ib_high_1:
                    ib_entry = ib_high_1
                    ib_stop_loss = ib_low_1
                elif close > ib_ce_1:
                    ib_entry = ib_ce_1
                    ib_stop_loss = ib_low_1
                    
                print("step1: strong IB rejection, reversal confirmation")
                print("IB entry: ", ib_entry, "IB stop loss: ", ib_stop_loss)
                
            # manipulation
            elif is_ib_rejection_18 and is_below_ib_1:
                reversal_confirmation = False
                is_reversal_candidate = True
                print("step2: reversal candidate")
            elif is_ib_rejection_18 and is_above_ib_1:
                reversal_confirmation = True
                if close > ib_high_18:
                    ib_entry = ib_high_18
                    ib_stop_loss = ib_low_18
                elif close > ib_ce_18:
                    ib_entry = ib_ce_18
                    ib_stop_loss = ib_low_18
                print("step3, entry, stop_loss: ", ib_entry, ib_stop_loss)
                
            elif is_ib_rejection_18 and close > ib_ce_1:
                reversal_confirmation = True
                ib_entry = ib_ce_1
                ib_stop_loss = ib_low_1
                print("reversal confirmation at close below ib ce of 8am, entry, stop_loss: ", ib_entry, ib_stop_loss)
                
            elif is_ib_rejection_1 and close > ib_ce_18:
                reversal_confirmation = True
                ib_entry = ib_ce_18
                ib_stop_loss = ib_low_18
                print("reversal confirmation at close above ib ce of 1am. entry, stop loss: ", ib_entry, ib_stop_loss)
                
            # bearish confirmation
            elif is_ib_rejection_1 and is_above_ib_18:
                reversal_confirmation = True
                if close > ib_high_1:
                    ib_entry = ib_high_1
                    ib_stop_loss = ib_low_1
                elif close > ib_ce_1:
                    ib_entry = ib_ce_1
                    ib_stop_loss = ib_low_1
                print("step4, entry, stop_loss: ", ib_entry, ib_stop_loss)                
            elif is_ib_rejection_1 and is_below_ib_18:
                reversal_confirmation = False
                is_reversal_candidate = True
                print("step5: reversal candidate")
            else:
                reversal_confirmation = False
                print("step6: no IB rules met")

            # final confirmation using smt
            #  allow trade for reversal candidate only when SMT is present
            if is_smt and is_reversal_candidate:
                print("Smt confirmation for reversal candidate, allowing trade")
                reversal_confirmation = True
            # if asia_swept and reversal_confirmation:
            #     print("Ib reversal confirmation: ", reversal_confirmation)
            #     print("asia high swept, allowing trade")
            #     reversal_confirmation = True
            # else:
            #     reversal_confirmation = False
            #     print("asia high not swept, not allowing trade")
            #     print("Ib reversal confirmation: ", reversal_confirmation)
        # allow trade temporarity. implement other killzones and rules later.
        # elif is_displacement:
        #     print("outside london Killzone, but displacement candle detected, allowing trade")
        #     reversal_confirmation = True
        # else:
        #     print("outside london Killzone, no displacement, rejecting trade")
        #     reversal_confirmation = False
        
        # return True
        print("smt, reversal confirmation, candidate: ", is_smt, reversal_confirmation, is_reversal_candidate)
        # return reversal_confirmation or is_reversal_candidate
        candidate.set_ib_entry(ib_entry, ib_stop_loss)
        return reversal_confirmation
    # implement other killzones and rules later
    elif is_ny_am_killzone:
        ib_high_8 = seven_hour_candle_8am["ib_high"]
        ib_low_8 = seven_hour_candle_8am["ib_low"]
        ib_ce_8 = seven_hour_candle_8am["ib_ce"]
        ib_high_1 = seven_hour_candle_1am["ib_high"]
        ib_low_1 = seven_hour_candle_1am["ib_low"]
        ib_ce_1 = seven_hour_candle_1am["ib_ce"]
        
        allow_shorts = True
        allow_longs = True
        print("overnight expansion: ", market_context.overnight_expansion, "exhaustion: ", market_context.exhaustion, "bias: ", market_context.bias )
        if (market_context.overnight_expansion or market_context.exhaustion) and market_context.session_direction == "bearish":
            allow_shorts = False
        elif (market_context.overnight_expansion or market_context.exhaustion) and market_context.session_direction == "bullish":
            allow_longs = False
        print("allow_shorts: ", allow_shorts, "allow_longs: ", allow_longs)

        # look for shorts
        if look_for_shorts:
            # get IB reaction values
            is_below_ib_1 = False
            is_above_ib_1 = False
            is_below_ib_8 = False
            is_above_ib_8 = False
            
            is_ib_rejection_1 = check_ib_rejection(last_closed_candle, ib_high_1, ib_low_1, ib_ce_1, "bearish")
            is_ib_rejection_8 = check_ib_rejection(last_closed_candle, ib_high_8, ib_low_8, ib_ce_8, "bearish")
            
            is_below_ib_8 = below_ib(last_closed_candle, ib_low_8)
            is_above_ib_8 = above_ib(last_closed_candle, ib_high_8)
            is_below_ib_1 = below_ib(last_closed_candle, ib_low_1)
            is_above_ib_1 = above_ib(last_closed_candle, ib_high_1)

            # print ib reaction values
            print("instrument, direction: ", candidate.instrument, "bearish")
            print("is_ib_rejection_8: ", is_ib_rejection_8)
            print("is_ib_rejection_1: ", is_ib_rejection_1)
            print("is_below_ib_8: ", is_below_ib_8)
            print("is_above_ib_8: ", is_above_ib_8)
            print("is_below_ib_1: ", is_below_ib_1)
            print("is_above_ib_1: ", is_above_ib_1)
            print("asia_swept: ", asia_swept)

            # bearish confirmation rules
            if is_ib_rejection_1 and is_ib_rejection_8:
                reversal_confirmation = True
                print("ib_high_1: ", ib_high_1, "ib_high_8: ", ib_high_8)
                if close < ib_low_1:
                    ib_entry = ib_low_1
                    ib_stop_loss = ib_high_1
                elif close < ib_ce_1:
                    ib_entry = ib_ce_1
                    ib_stop_loss = ib_high_1
                elif close < ib_low_8:
                    ib_entry = ib_low_8
                    ib_stop_loss = ib_high_8
                elif close < ib_ce_8:
                    ib_entry = ib_ce_8
                    ib_stop_loss = ib_high_8
                    
                print("step1: strong IB rejection, reversal confirmation")
                print("IB entry: ", ib_entry, "IB stop loss: ", ib_stop_loss)
                
            # manipulation
            elif is_ib_rejection_1 and is_above_ib_8:
                reversal_confirmation = False
                is_reversal_candidate = True
                print("step2: reversal candidate")
            elif is_ib_rejection_1 and is_below_ib_8:
                reversal_confirmation = True
                if close < ib_low_1:
                    ib_entry = ib_low_1
                    ib_stop_loss = ib_high_1
                elif close < ib_ce_1:
                    ib_entry = ib_ce_1
                    ib_stop_loss = ib_high_1
                print("step3, entry, stop_loss: ", ib_entry, ib_stop_loss)
                
            elif is_ib_rejection_1 and close < ib_ce_8:
                reversal_confirmation = True
                ib_entry = ib_ce_8
                ib_stop_loss = ib_high_8
                print("reversal confirmation at close below ib ce of 8am, entry, stop_loss: ", ib_entry, ib_stop_loss)
            
            elif is_ib_rejection_8 and close < ib_ce_1:
                reversal_confirmation = True
                ib_entry = ib_ce_1
                ib_stop_loss = ib_high_1
                print("reversal confirmation at close below ib ce of 1am - 2. entry, SL", ib_entry, ib_stop_loss)
            
            # bearish confirmation
            elif is_ib_rejection_8 and is_below_ib_1:
                reversal_confirmation = True
                if close < ib_low_8:
                    ib_entry = ib_low_8
                    ib_stop_loss = ib_high_8
                elif close < ib_ce_8:
                    ib_entry = ib_ce_8
                    ib_stop_loss = ib_high_8
                print("step4, entry, stop_loss: ", ib_entry, ib_stop_loss)
                
            elif is_ib_rejection_8 and is_above_ib_1:
                reversal_confirmation = False
                is_reversal_candidate = True
                print("step5")
            else:
                reversal_confirmation = False
                print("step6")
            # final confirmation using smt
            #  allow trade for reversal candidate only when SMT is present
            if is_smt and is_reversal_candidate:
                print("Smt confirmation for reversal candidate, not allowing trade in ny am")
                reversal_confirmation = False
                print("is_ny_lunch_time: ", is_ny_lunch_time)
                if is_ny_lunch_time:
                    print("smt + reversal candidate during lunch time = allowing trade")
                    reversal_confirmation = True
                else:
                    print("is_ny_lunch_time: ", is_ny_lunch_time)
                
            if not allow_shorts:
                reversal_confirmation = False
                print("Not in a bearish overnight expansion or exhaustion, rejecting shorts")            
        
        elif look_for_longs:
            # get IB reaction values
            is_below_ib_1 = False
            is_above_ib_1 = False
            is_below_ib_8 = False
            is_above_ib_8 = False
            
            is_ib_rejection_1 = check_ib_rejection(last_closed_candle, ib_high_1, ib_low_1, ib_ce_1, "bullish")
            is_ib_rejection_8 = check_ib_rejection(last_closed_candle, ib_high_8, ib_low_8, ib_ce_8, "bullish")
            
            is_below_ib_8 = below_ib(last_closed_candle, ib_low_8)
            is_above_ib_8 = above_ib(last_closed_candle, ib_high_8)
            is_below_ib_1 = below_ib(last_closed_candle, ib_low_1)
            is_above_ib_1 = above_ib(last_closed_candle, ib_high_1)

            # print ib reaction values
            # print("instrument, direction: ", candidate.instrument, "bullish")
            # print("is_ib_rejection_8: ", is_ib_rejection_8)
            # print("is_ib_rejection_1: ", is_ib_rejection_1)
            # print("is_below_ib_8: ", is_below_ib_8)
            # print("is_above_ib_8: ", is_above_ib_8)
            # print("is_below_ib_1: ", is_below_ib_1)
            # print("is_above_ib_1: ", is_above_ib_1)
            # print("asia_swept: ", asia_swept)

            # bullish confirmation rules
            if is_ib_rejection_1 and is_ib_rejection_8:
                reversal_confirmation = True
                print("ib_high_1: ", ib_high_1, "ib_high_8: ", ib_high_8)
                if close > ib_high_1:
                    ib_entry = ib_high_1
                    ib_stop_loss = ib_low_1
                elif close > ib_ce_1:
                    ib_entry = ib_ce_1
                    ib_stop_loss = ib_low_1
                elif close > ib_high_8:
                    ib_entry = ib_high_8
                    ib_stop_loss = ib_low_8
                elif close > ib_ce_8:
                    ib_entry = ib_ce_8
                    ib_stop_loss = ib_low_8
                    
                print("step1: strong IB rejection, reversal confirmation")
                print("IB entry: ", ib_entry, "IB stop loss: ", ib_stop_loss)
                
            # manipulation
            elif is_ib_rejection_1 and is_below_ib_8:
                reversal_confirmation = False
                is_reversal_candidate = True
                print("step2: reversal candidate")
            elif is_ib_rejection_1 and is_above_ib_8:
                reversal_confirmation = True
                if close > ib_high_1:
                    ib_entry = ib_high_1
                    ib_stop_loss = ib_low_1
                elif close > ib_ce_1:
                    ib_entry = ib_ce_1
                    ib_stop_loss = ib_low_1
                print("step3, entry, stop_loss: ", ib_entry, ib_stop_loss)
                
            elif is_ib_rejection_1 and close > ib_ce_8:
                reversal_confirmation = True
                ib_entry = ib_ce_8
                ib_stop_loss = ib_low_8
                print("reversal confirmation at close below ib ce of 8am, entry, stop_loss: ", ib_entry, ib_stop_loss)
                
            elif is_ib_rejection_8 and close > ib_ce_1:
                reversal_confirmation = True
                ib_entry = ib_ce_1
                ib_stop_loss = ib_low_1
                print("reversal confirmation at close above ib ce of 1am. entry, stop loss: ", ib_entry, ib_stop_loss)
                
            # bearish confirmation
            elif is_ib_rejection_8 and is_above_ib_1:
                reversal_confirmation = True
                if close > ib_high_8:
                    ib_entry = ib_high_8
                    ib_stop_loss = ib_low_8
                elif close > ib_ce_8:
                    ib_entry = ib_ce_8
                    ib_stop_loss = ib_low_8
                print("step4, entry, stop_loss: ", ib_entry, ib_stop_loss)                
            elif is_ib_rejection_8 and is_below_ib_1:
                reversal_confirmation = False
                is_reversal_candidate = True
                print("step5: reversal candidate")
            else:
                reversal_confirmation = False
                print("step6: no IB rules met")
            # final confirmation using smt
            #  allow trade for reversal candidate only when SMT is present
            if is_smt and is_reversal_candidate:
                print("Smt confirmation for reversal candidate, not allowing trade in ny am")
                reversal_confirmation = False
            if not allow_longs:
                reversal_confirmation = False
                print("Not in a bullish overnight expansion or exhaustion, rejecting longs")
        print("smt, reversal confirmation, candidate: ", is_smt, reversal_confirmation, is_reversal_candidate)
        # return reversal_confirmation or is_reversal_candidate
        candidate.set_ib_entry(ib_entry, ib_stop_loss)
        return reversal_confirmation
            
    elif window_name == "7h_wick_0100":
        # approach : 
        # - 1am starts inside 18 IB and then moves outside of it with rejection, strong confirmation
        # - 1am starts outside 18 IB and then moves inside of it with rejection, strong confirmation
        # - 1am starts inside 18 IB and then moves inside of it with rejection, moderate confirmation
        # - 1am starts outside 18 IB and then moves outside of it with rejection, moderate confirmation
        # - if 1am is a strong rejection candle with close beyond 18 IB in either direction, strong confirmation
        # - if 1am is a strong rejection candle but close is within 18 IB, moderate confirmation

        # We shall implement compression and only strong confirmations, skip weak and moderate confirmations for now. We shall also skip smt confirmation for now. So the rules we shall implement now are:
        # - if 1am is a strong rejection candle with close beyond 18 IB in either direction, strong confirmation - 3 AM Continuation
        
        


        
        return reversal_confirmation
    
    elif window_name == "7h_wick_0800":
        allow_shorts = True
        allow_longs = True
        print("overnight expansion: ", market_context.overnight_expansion, "exhaustion: ", market_context.exhaustion, "bias: ", market_context.bias )
        
        ib_high_18 = seven_hour_candle_6pm["ib_high"]
        ib_low_18 = seven_hour_candle_6pm["ib_low"]
        ib_ce_18 = seven_hour_candle_6pm["ib_ce"]
        ib_high_1 = seven_hour_candle_1am["ib_high"]
        ib_low_1 = seven_hour_candle_1am["ib_low"]
        ib_ce_1 = seven_hour_candle_1am["ib_ce"]

        # check if the setup passes displacement and atr filters

        passed_atr_displacement_filter = displacement_atr_filter()
        if passed_atr_displacement_filter:
            reversal_confirmation = True

        # if (market_context.overnight_expansion or market_context.exhaustion):
        #     if market_context.session_direction == "bearish":
        #         print("overnight bearish expansion or exhausion. not allowing shorts")
        #         allow_shorts = False
        #     elif market_context.session_direction == "bullish":
        #         print("overnight bullish expansion or exhausion. not allowing shorts")
        #         allow_longs = False        
        #     else:
        #         print("step 4")
        
        # print("inside last: ", candidate.instrument, candidate.sweep_and_ob_ce_confirmed)
        # print("structure break: ", candidate.ob_data["structure_break"] if candidate.ob_data is not None else None, "strong_body_displacement: ", candidate.ob_data["strong_body_displacement"] if candidate.ob_data is not None else None)
        # print("ob body range: ", candidate.ob_data["ob_body_range"] if candidate.ob_data is not None else None)
        # if candidate.sweep_and_ob_ce_confirmed:
        #     reversal_confirmation = True
        #     print("aksnkdna 2")
        # elif candidate.sweep_and_ob_confirmed:
        #     if candidate.ob_data is not None:
        #         if candidate.ob_data["structure_break"] and candidate.ob_data["ob_body_range"] > 0.5:
        #             reversal_confirmation = True
        #             print("lklkl 2")
        # elif candidate.ob_data is not None:
        #     if candidate.ob_data["structure_break"] and candidate.ob_data["ob_body_range"] > 0.5:
        #         reversal_confirmation = True
        #         print("aksnkdnaasdadasdas 2")
        #     elif candidate.ob_data["strong_body_displacement"]:
        #         reversal_confirmation = True
        #         print("strong body displacement, allowing reversal")
        #     else:
        #         print("no strong body displacement, not allowing reversal")
   
            
        # else:
        #     print("none+none")

        # # elif (market_context.overnight_expansion or market_context.exhaustion) and market_context.session_direction == "bullish":
        # #     allow_longs = False
        # print("allow_shorts: ", allow_shorts, "allow_longs: ", allow_longs)
        # # allow reversal with reversal_confirmation as true
        
        # if look_for_longs and not allow_longs:
        #     print("market exhauted, not allowing longs")
        #     reversal_confirmation = False
        # if look_for_shorts and not allow_shorts:
        #     print("market exhauted, not allowing shorts")
        #     reversal_confirmation = False
        return reversal_confirmation
    elif is_post_london_killzone:
        allow_longs = filter_longs_london(look_for_longs, session_direction, atr_usage, is_smt)
        allow_shorts = filter_shorts_london(look_for_shorts, session_direction, atr_usage, is_smt)
        if look_for_longs and allow_longs:
            reversal_confirmation = True
        if look_for_shorts and allow_shorts:
            reversal_confirmation = True
        return reversal_confirmation
    elif is_ny_lunch_time:
        # capture major reversal, skip retracements
        if candidate.ob_data is not None:
            if candidate.ob_data["structure_break"] and candidate.ob_data["strong_body_displacement"]:
                reversal_confirmation = True
        return reversal_confirmation
    else:
        print("inside last: ", candidate.instrument, candidate.sweep_and_ob_ce_confirmed)
        print("structure break: ", candidate.ob_data["structure_break"] if candidate.ob_data is not None else None, "strong_body_displacement: ", candidate.ob_data["strong_body_displacement"] if candidate.ob_data is not None else None)
        print("ob body range: ", candidate.ob_data["ob_body_range"] if candidate.ob_data is not None else None)
        print("market direction: ", market_context.session_direction)
        allow_shorts = True
        allow_longs = True
        if market_context.session_direction == "bearish" and market_context.atr_usage > 0.9:
            allow_shorts = False
            print("not allowing shorts as atr > 0.9 and direction is bearish")
        elif market_context.session_direction == "bullish" and market_context.atr_usage > 0.9:
            allow_longs = False
            print("not allowing longs as atr > 0.9 and direction is bullish")
        elif market_context.session_direction == "bearish" and market_context.atr_usage < 0.9:
            allow_longs = False

            print("not allowing longs as atr < 0.9 and direction is bearish")
        elif market_context.session_direction == "bullish" and market_context.atr_usage < 0.9:
            allow_shorts = False
            # check again, candidate is beind accessed after the reversal_confirmation is returned
            candidate.invalidate()
            print("not allowing shorts as atr < 0.9 and direction is bullish. resetting candidate")
        # TODO: integrate SMT
        # if short trade and bullish smt, dont allow trade and viceversa
        if candidate.sweep_and_ob_ce_confirmed:
            reversal_confirmation = True
            print("aksnkdna")
        elif candidate.sweep_and_ob_confirmed:
            if candidate.ob_data is not None:
                if candidate.ob_data["structure_break"] and candidate.ob_data["ob_body_range"] > 0.5:
                    reversal_confirmation = True
                    print("lklkl")
        elif candidate.ob_data is not None:
            if candidate.ob_data["structure_break"] and candidate.ob_data["strong_body_displacement"]:
                reversal_confirmation = True
                print("aksnkdnaasdadasdas")
            else:
                print("ob data not none, structure break: ", candidate.ob_data["structure_break"], "strong body displacement: ", candidate.ob_data["strong_body_displacement"])
        else:
            print("none+none")
        if look_for_longs and not allow_longs:
            print("market exhauted, not allowing longs")
            reversal_confirmation = False
        if look_for_shorts and not allow_shorts:
            print("market exhauted, not allowing shorts")
            reversal_confirmation = False
        return reversal_confirmation
        



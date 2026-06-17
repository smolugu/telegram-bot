from data.models.compression import detect_compression
from data.models.displacement import is_displacement_candle
from data.models.final_context import determine_ping_direction
from data.models.ib_alignment import analyze_cross_asset_alignment
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

def check_for_reversal_setup_confirmation(market_context, london_context, newyork_context, seven_hour_builder_candles, liquidity_levels, candidate, last_closed_candle, current_30m_start, smt_summary, co_asset, co_asset_candidate):
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

    # expansion type function
    def categorize_expansion():
        # types: expansion, flush, rocket

        # is_strong_compression
        # strong displacement
        # smt
        # external liquidity untapped
        # prime time = liquidity injection + volatility expansion
        # atr availability


        expansion_type = "expansion"

        return expansion_type
    # displacement and atr check function
    # TODO: integrated 3m FVG detected in 30m OB candle,
    # we are currently looking at OB size only
    def displacement_atr_filter():
        allow_shorts = True
        allow_longs = True
        filters_passed = False
        if (market_context.overnight_expansion or market_context.exhaustion):
            if market_context.session_direction == "bearish":
                print("overnight bearish expansion or exhausion. not allowing shorts")
                allow_shorts = False
            elif market_context.session_direction == "bullish":
                print("overnight bullish expansion or exhausion. not allowing longs")
                allow_longs = False        
            else:
                print("step 4")
        
        print("inside last: ", candidate.instrument, candidate.sweep_and_ob_ce_confirmed)
        print("structure break: ", candidate.ob_data["structure_break"] if candidate.ob_data is not None else None, "strong_body_displacement: ", candidate.ob_data["strong_body_displacement"] if candidate.ob_data is not None else None)
        print("ob body range: ", candidate.ob_data["ob_body_range"] if candidate.ob_data is not None else None)
        if candidate.sweep_and_ob_ce_confirmed:
            print("sweep_and_ob_ce_confirmed")
            filters_passed = True
            print("aksnkdna 2")
        elif candidate.sweep_and_ob_confirmed:
            print("sweep_and_ob_confirmed")
            if candidate.ob_data is not None:
                # if candidate.ob_data["structure_break"] and candidate.ob_data["ob_body_range"] > 0.5:
                if candidate.ob_data["ob_body_range"] > 0.5:
                    filters_passed = True
                    print("lklkl 2")
            else:
                filters_passed = True
                print("lklkl 22")
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
    
    def rejection_filter():
        filters_passed = False
        return (candidate.sweep_and_ob_confirmed 
            or candidate.sweep_and_ob_ce_confirmed
            or candidate.level_rejection 
            or candidate.fvg_confirmed
        )
        

    # strong ob body check important in decompression, value flip, migration continuation structures.
    def displacement_filter():
        filters_passed = False
        
        print("inside displacement filter: ", candidate.instrument, candidate.sweep_and_ob_ce_confirmed)
        print("sweep_and_ob_ce_confirmed: ", candidate.sweep_and_ob_ce_confirmed)
        print("structure break: ", candidate.ob_data["structure_break"] if candidate.ob_data is not None else None, "strong_body_displacement: ", candidate.ob_data["strong_body_displacement"] if candidate.ob_data is not None else None)
        print("ob body range: ", candidate.ob_data["ob_body_range"] if candidate.ob_data is not None else None)
        if candidate.sweep_and_ob_ce_confirmed:
            print("sweep_and_ob_ce_confirmed")
            filters_passed = True
            print("displacement_filter: sweep_and_ob_ce_confirmed")
        elif candidate.sweep_and_ob_confirmed:
            print("sweep_and_ob_confirmed")
            if candidate.ob_data is not None:
                # if candidate.ob_data["structure_break"] and candidate.ob_data["ob_body_range"] > 0.5:
                if candidate.ob_data["ob_body_range"] > 0.5:
                    filters_passed = True
                    print("displacement_filter: ob_body_range > 0.5 and sweep_and_ob_confirmed")
            else:
                filters_passed = True
                print("displacement_filter: sweep_and_ob_confirmed")
        elif candidate.ob_data is not None:
            if candidate.ob_data["structure_break"] and candidate.ob_data["ob_body_range"] > 0.5:
                filters_passed = True
                print("displacement_filter: structure break and ob_body_range > 0.5")
            elif candidate.ob_data["strong_body_displacement"]:
                filters_passed = True
                print("displacement_filter: strong body displacement, allowing reversal")
            else:
                print("displacement_filter: no strong body displacement, not allowing reversal")
        
        return filters_passed

    def atr_filter():
        allow_shorts = True
        allow_longs = True
        filters_passed = True
        print("overnight_expansion: ", market_context.overnight_expansion)
        print("exhaustion: ", market_context.exhaustion)
        print("direction: ", market_context.session_direction)
        if (market_context.overnight_expansion or market_context.exhaustion):
            if market_context.session_direction == "bearish":
                print("overnight bearish expansion or exhausion. not allowing shorts")
                allow_shorts = False
            elif market_context.session_direction == "bullish":
                print("overnight bullish expansion or exhausion. not allowing longs")
                allow_longs = False        
        else:
            print("there is no overning expansion or exhaustion, not filtering based on that")
        
        
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
            if smt_summary["bearish_smt_1h"] is not None or smt_summary["bearish_smt_key_level"] is not None or smt_summary["bearish_smt_30m_swing"] is not None:
                is_smt = True
        elif look_for_longs:
            if smt_summary["bullish_smt_1h"] is not None or smt_summary["bullish_smt_key_level"] is not None or smt_summary["bullish_smt_30m_swing"] is not None:
                is_smt = True
        return is_smt
    

    # HTF BIAS
    # Primarily for the following structures as these are balanced inventory structures
        # sandwich_bullish
        # sandwich_bearish
        # sandwich_overlap_bullish
        # sandwich_overlap_bearish
        # bullish_rebalance_compression
        # bearish_rebalance_compression
        # bullish reintergration
        # bearish reintegration


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
    if window_name == "7h_wick_0800" and is_ny_am_killzone:
        is_ny_am_killzone = False
    print("----------------------------------------")
    print(f"Candidate: {candidate.instrument} {candidate.side}")
    print("is_london_killzone: ", is_london_killzone, " | is_post_london_killzone:", is_post_london_killzone, " |  is_ny_am_killzone: ", is_ny_am_killzone, " | is_ny_lunch_time: ", is_ny_lunch_time, " | window_name: ", window_name)
    print("market context: ", market_context.values())

    print("bullish 1h smt: ", market_context.bullish_smt_1h, "bearish 1h smt: ", market_context.bearish_smt_1h, "bullish 30m swing smt: ", market_context.bullish_smt_30m, "bearish 30m swing smt: ", market_context.bearish_smt_30m)
    
    session_direction = market_context.session_direction
    atr_usage = market_context.atr_usage
    london_context_from_market_context = context_for_london(market_context)

    # smt check
    is_smt = smt_check()
    is_atr_filter = atr_filter()
    is_displacement = displacement_filter()
    is_rejection = rejection_filter()
    passed_atr_displacement_filter = displacement_atr_filter()
    
    # rejection or fvg_confirmed or strong OB

    is_sweep_rejection = candidate.fvg_confirmed or candidate.sweep_and_ob_confirmed or is_displacement

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
        # check cross ib relationships between nq and es
        continue_with_candidate = True
        if london_context.structure["compression"] and co_asset["london_context"].structure["compression"]:
            continue_with_candidate = True
        elif london_context.structure["compression"] and not co_asset["london_context"].structure["compression"]:
            # allow trades in the direction of co_asset or session direction
            if co_asset["london_context"].structure["ib_relationship"] == "above_18" \
                and look_for_shorts and co_asset["market_context"].atr_usage < 0.7:
                continue_with_candidate = False
            elif co_asset["london_context"].structure["ib_relationship"] == "below_18" \
                and look_for_longs and co_asset["market_context"].atr_usage < 0.7:
                continue_with_candidate = False
        elif not london_context.structure["compression"] and co_asset["london_context"].structure["compression"]:
            # allow trades in the direction of co_asset or session direction
            if london_context.structure["ib_relationship"] == "above_18" \
                and look_for_shorts and market_context.atr_usage < 0.7:
                continue_with_candidate = False
            elif london_context.structure["ib_relationship"] == "below_18" \
                and look_for_longs and market_context.atr_usage < 0.7:
                continue_with_candidate = False
        elif not london_context.structure["compression"] and not co_asset["london_context"].structure["compression"]:
            if london_context.structure["ib_relationship"] == "above_18" and co_asset["london_context"].structure["ib_relationship"] == "above_18"\
                and look_for_shorts:
                continue_with_candidate = False
            elif london_context.structure["ib_relationship"] == "below_18" and co_asset["london_context"].structure["ib_relationship"] == "below_18"\
                and look_for_longs:
                continue_with_candidate = False
            else:
                continue_with_candidate = False
            
                


        if london_context.structure["compression"] and london_context.structure["ib_relationship"] == "inside":
            # trade ready for expansion.
            # get htf bias, displacement, fvg imbalance, smt.
            # at this point price is rejecting IB18 low or high
            # apply atr and displacement filter
            passed_atr_displacement_filter = displacement_atr_filter()
            print("post 1AM IB, passed atr displacemet filter: ", passed_atr_displacement_filter)
            reversal_confirmation = passed_atr_displacement_filter and continue_with_candidate
            candidate.ping_type = "Rocket" if look_for_longs and is_smt else "Flush" if look_for_shorts and is_smt else "Expansion"
            candidate.final_target = "ATR"

            
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
                
            if continue_with_candidate and allow_trade and rejection_of_ib_2 and london_context.structure["is_strong_body"]\
                and not london_context.structure["engulfing_deep_retracement"]:
                reversal_confirmation = True

                
            ## reversal
                # bearish 1am Ib -> deep retracement -> rejection of ce -> strong displacement

            ## re-compression
                # deep retracement -> inside 1am IB extremes

        elif london_context.structure["ib_relationship"] == "partial_overlap":
            print("weak compression - london overlap")
            reversal_confirmation = False
            # main confirmations: atr_usage_direction, 
            # weak compression
            # continuation with HTF confirmation mainly 1h CISD after sweep of key level (PDH/L)
                # bearish overlap - continuation
                    # 1am IB overlapping with 18 IB lows
                    # htf bearish confirmation - sweep of pdh (smt) with 1h CISD
                    # look for shorts below 2am IB
                    # skip continuation if no expansion shorts below open
                # bullish overlap - continuation
                    # 1am IB overlapping with 18 IB highs
                    # htf bullish confirmation - sweep of pdl (smt) with 1h CISD
                    # look for longs above 2am IB
                    # skip continuation if no expansion longs above open
            # reversal - no htf 1h cisd after key level sweep (PDH/PDL)
                # bearish overlap - reversal
                    # sweep of lows + OB + 2am IB support + 3:30 continuation
                    # no expansion continuation below open
                # bullish overlap - reversal
                    # sweep of highs + OB + 2am IB support + 3:30 continuation
                    # no expansion continuation above open
            allow_trade = True
            no_bearish_expansion = market_context.no_bearish_expansion_below_open or co_asset["market_context"].no_bearish_expansion_below_open
            no_bullish_expansion = market_context.no_bullish_expansion_above_open or co_asset["market_context"].no_bullish_expansion_above_open
            if look_for_longs and no_bullish_expansion:
                print("no bullish expansion above open")
                allow_trade = False
            elif look_for_shorts and no_bearish_expansion:
                print("no bearish expansion below open")
                allow_trade = False
            
            # additional filters
            if allow_trade:
                passed_atr_displacement_filter = displacement_atr_filter()
                print("post 1AM IB, passed atr displacemet filter: ", passed_atr_displacement_filter)
                reversal_confirmation = passed_atr_displacement_filter and continue_with_candidate

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
        structure_name = newyork_context.structure["name"]
        # if ib_relationship in ("inside_1am", "inside_18"):
        # get relative IB relationship context
        # for example nq sandwich and es not. if sandwich by 9. ignore trade at 9 we need a sweep of extreme
        # reset IBs
        # split different filters like displacement, atr_usage, smt, direction, htf bias, 
        passed_atr_displacement_filter = displacement_atr_filter()
        # ===========================================
        # cross asset relationships and final context
        # ===========================================
        # cross asset alignment relationships
        # same and similar : confidence, inducement,leader, laggard
        # conflicting: preferred direction, conflic_resolution_direction
        # all cross asset relationships: inducement check
        cross_alignment = analyze_cross_asset_alignment(
            # nq structure
            newyork_context.structure if candidate.instrument == "NQ" else co_asset["newyork_context"].structure,
            # es structure
            co_asset["newyork_context"].structure if candidate.instrument == "NQ" else newyork_context.structure,
            # nq atr exhaustion

            market_context.overnight_expansion or market_context.exhaustion if candidate.instrument == "NQ" else co_asset["market_context"].overnight_expansion or co_asset["market_context"].exhaustion,
            # es atr exhasution
            co_asset["market_context"].overnight_expansion or co_asset["market_context"].exhaustion if candidate.instrument == "NQ" else market_context.overnight_expansion or market_context.exhaustion,
        )

        # TODO: replace with HTF bias
        structure_bias = "bullish" if look_for_longs else "bearish"
        htf_bias = weekly_context["bias"] if weekly_context["bias"] is not None else structure_bias
        direction_context = determine_ping_direction(
            cross_alignment,
            newyork_context.structure if candidate.instrument == "NQ" else co_asset["newyork_context"].structure,
            co_asset["newyork_context"].structure if candidate.instrument == "NQ" else newyork_context.structure,
            htf_bias,
        )
        # inducement asset needs extra confirmation - strong OB
        require_strong_ob = False
        if direction_context["possible_inducement_asset"] == candidate.instrument:
            require_strong_ob = True
        
        # conflict handling
        allow_conflict_longs = True
        allow_conflict_shorts = True
        
        if direction_context["true_directional_conflict"]:

            if direction_context["conflict_resolution_direction"] == "bullish":
                allow_conflict_shorts = False

            elif direction_context["conflict_resolution_direction"] == "bearish":
                allow_conflict_longs = False
                
        # base confidence scoring
        base_confidence_modifier = 0

        if direction_context["confidence"] == "very_high":
            base_confidence_modifier += 2

        elif direction_context["confidence"] == "high":
            base_confidence_modifier += 1

        elif direction_context["confidence"] == "low":
            base_confidence_modifier -= 1
        # ===========================================
        # *******************************************
        # ===========================================

        # if ib_relationship == "inside_1am":
        # ====================================
        # staircase confirmations
        # ====================================
        # block completed
        if structure_name == "staircase_gap_bullish":
            print("structure : staircase_gap_bullish")
            # strongest bullish migration structure
            # no overlap between IBs
            # active bullish repricing / migration
            # In staircase gap structures, shorts require migration failure — not just exhaustion

            # core pings:
            # long from retest of IB1 ↔ IB8 gap (Rocket)
            # short only after migration failure (Flush)
        
            if look_for_longs and allow_conflict_longs:
                # primary continuation setup
                # expect mitigation into latest migration gap
                # TODO: we need confirmation that the sweep is inside the gap or at mitigation level
                # staircase gap bullish is already migrated and atr could be close to atr exhaustion
                # so atr filter is too restrictive
                if (
                    # not is_atr_filter
                    is_smt
                    and is_rejection
                    and candidate.ob_level >
                        newyork_context.structure["mitigation_level"]
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Rocket"
                    # continuation target
                    candidate.initial_target = newyork_context.structure["range_high"]
                    candidate.final_target = "ATR"

            elif look_for_shorts and allow_conflict_shorts:

                # only allow shorts after:
                # upside ATR exhaustion
                # SMT divergence
                # failed bullish migration = atr exhaustion + 30m OB
                # we dont need OB level to be below mitigation level -  too late
                
                if (
                    is_atr_filter
                    and is_smt
                    and is_rejection
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Flush"
                    # retracement/reversal target = gap between ib18 and ib1
                    candidate.initial_target = (newyork_context.ib_1["low"] + newyork_context.ib_18["high"]) / 2
                    candidate.final_target = "DO"
        # block completed
        elif structure_name == "staircase_gap_bearish":
            print("structure : staircase_gap_bearish")
            # strongest bearish migration structure
            # no overlap between IBs
            # active bearish repricing / migration
            # In staircase gap structures, longs require migration failure — not just exhaustion

            # core pings:
            # short from retest of IB1 ↔ IB8 gap (Flush)
            # long only after migration failure (Rocket)

            # TODO: we need confirmation that the sweep is inside the gap or at mitigation level
            if look_for_shorts and allow_conflict_shorts:
                # primary continuation setup
                # expect mitigation into latest migration gap
                if (
                    is_smt
                    and is_rejection
                    and candidate.ob_level <
                        newyork_context.structure["mitigation_level"]
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Flush"
                    # continuation target
                    candidate.initial_target = newyork_context.structure["range_low"]
                    candidate.final_target = "ATR"

            elif look_for_longs and allow_conflict_longs:

                # only allow longs after:
                # downside ATR exhaustion
                # SMT divergence

                if (
                    is_atr_filter
                    and is_smt
                    and is_rejection
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Rocket" 
                    # retracement/reversal target = gap between ib18 and ib1
                    candidate.initial_target = (newyork_context.ib_1["high"] + newyork_context.ib_18["low"]) / 2
                    candidate.final_target = "DO"
        # block completed
        elif structure_name == "staircase_early_overlap_bullish":
            print("structure : staircase_early_overlap_bullish")
            # ideal trades:
            # 1. sweep of ib8 low + 3m smt long to ATR or HTF
            # 2. sweep of MTL + 3m smt long to ATR or HTF
            # 
            # In staircase overlap structures, liquidity resolution matters more than retracement depth
            # bullish migration already accepted
            # latest overlap formed early during migration in early london session
            # possible expansion in london
            # typically behaves like:
            # post-compression continuation structure

            # core pings:
            # long from equilibrium / mitigation (Rocket) - between ib8 low and overlap region, can even retest DO
            # short only after upside ATR exhaustion (Flush)

            if look_for_longs and allow_conflict_longs:
                # primary continuation setup
                # expect shallow or deep mitigation based on migration strength from IB1 to IB8
                # TODO: valid sweep inside gap or at mitigation level
                if (
                    not is_atr_filter
                    and is_smt
                    and is_rejection
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Rocket"
                    # target opposite end of active migration range
                    candidate.initial_target = newyork_context.structure["range_high"]
                    candidate.final_target = "ATR"

            elif look_for_shorts and allow_conflict_shorts:
                # only allow shorts after:
                # upside ATR exhaustion
                # SMT divergence
                # failed bullish continuation
                if (
                    is_atr_filter
                    and is_smt
                    and is_rejection
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Flush"
                    # retracement/reversal target - equilibrium of IB18 to ib8 range
                    candidate.initial_target = newyork_context.structure["mitigation_level"]
                    # TODO: recheck final_target DO or early Compression high IB1["high"]
                    candidate.final_target = "DO"
        # block completed
        elif structure_name == "staircase_late_overlap_bullish":
            print("structure : staircase_late_overlap_bullish")
            # core pings: 
                # long from mitigation level (expansion)
                # short after ATR exhaustion (Flush)
            
            if look_for_longs and allow_conflict_longs:
                # TODO: valid sweep at ib1 low or ce of IB18 high and Ib1 low
                # candidate.sweep_level <= newyork_context.structure["mitigation_level"] or compression low
                
                if is_rejection and is_smt:
                    reversal_confirmation = True
                    candidate.ping_type = "Rocket"
                    candidate.final_target = "ATR"
                    candidate.initial_target = newyork_context.structure["compression_high"]

            elif look_for_shorts and allow_conflict_shorts:
                if is_atr_filter and is_smt and is_rejection:
                    reversal_confirmation = True
                    candidate.ping_type = "Flush"
                    candidate.initial_target = newyork_context.structure["mitigation_level"]
                    candidate.final_target = "DO"
            

        # block completed
        elif structure_name == "staircase_early_overlap_bearish":
            print("structure : staircase_early_overlap_bearish")
            # In staircase overlap structures,
            # liquidity resolution matters more than retracement depth

            # bearish migration already accepted
            # latest overlap formed early during migration in early london session
            # typically behaves like:
            # post-compression continuation structure

            # core pings:
            # short from equilibrium / mitigation (Flush)
            # - between ib8 high and overlap region, can even retest DO
            # long only after downside ATR exhaustion (Rocket)
            
            if look_for_shorts and allow_conflict_shorts:
                # primary continuation setup
                # expect shallow or deep mitigation
                # based on migration strength from IB1 to IB8

                if (
                    not is_atr_filter
                    and is_smt
                    and is_rejection
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Flush"
                    # target opposite end of active migration range
                    candidate.initial_target = newyork_context.structure["range_low"]
                    candidate.final_target = "ATR"
            
            elif look_for_longs and allow_conflict_longs:
                # only allow longs after:
                # downside ATR exhaustion
                # SMT divergence
                # failed bearish continuation
                if (
                    is_atr_filter
                    and is_smt
                    and is_rejection
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Rocket"
                    # retracement/reversal target - equilibrium of IB18 to ib8 range
                    candidate.initial_target = newyork_context.structure["mitigation_level"]
                    # TODO: recheck final_target DO or early Compression high IB1["high"]
                    candidate.final_target = "DO"
            
        # block completed
        elif structure_name == "staircase_late_overlap_bearish":
            print("structure : staircase_late_overlap_bearish")
            # core pings: 
                # short from mitigation level (Flush)
                # long after ATR exhaustion (Rocket)
            if look_for_shorts and allow_conflict_shorts:
                # TODO: valid sweep at ib1 high or ce of IB18 low and Ib1 high
                # candidate.sweep_level = newyork_context.structure["mitigation_level"] or compression high
                
                if is_rejection and is_smt:
                    reversal_confirmation = True
                    candidate.ping_type = "Flush"
                    candidate.final_target = "ATR"
                    candidate.initial_target = newyork_context.structure["compression_low"]

            elif look_for_longs and allow_conflict_longs:
                if is_atr_filter and is_smt and is_rejection:
                    reversal_confirmation = True
                    candidate.ping_type = "Rocket"
                    candidate.final_target = "DO"
                    candidate.initial_target = newyork_context.structure["mitigation_level"]
            
        # block completed
        elif structure_name == "staircase_bullish":
            print("structure : staircase_bullish")
            # continuous overlap bullish migration and equilibrium constantly rebuilding upward
            # continuous overlap migration favors exhaustion reversals more than explosive continuation
            # no displacement gaps
            # grinding continuation structure

            # core ping:
                # high probability Flush after ATR exhaustion
                # longs possible but lower expansion quality

            if look_for_longs and allow_conflict_longs:

                # continuation possible
                # but lower quality than staircase gap structures
                # not sure about longs, once bearish move starts it will flush to daily open
                
                if (
                    not is_atr_filter
                    and is_smt
                    and is_rejection
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Rocket"
                    candidate.initial_target = newyork_context.structure["range_high"]
                    candidate.final_target = "ATR"

                    # optional:
                    # lower confidence weighting
                # TODO: disabling longs for now as there is no: gap, compression low, mitigation level, rebalance level. review later
                reversal_confirmation = False

            elif look_for_shorts and allow_conflict_shorts:

                # ideal setup:
                # exhaustion reversal after grinding migration
                if (
                    is_atr_filter
                    and is_smt
                    and is_rejection
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Flush"
                    candidate.initial_target = newyork_context.ib_18["high"]
                    # final target ATR or DO
                    candidate.final_target = "DO"

        # block completed
        elif structure_name == "staircase_bearish":
            print("structure : staircase_bearish")
            # continuous overlap bearish migration and equilibrium constantly rebuilding downward
            # continuous overlap migration favors exhaustion reversals more than explosive continuation
            # no displacement gaps
            # grinding continuation structure

            # core ping:
                # high probability Rocket after ATR exhaustion
                # shorts possible but lower expansion quality

            if look_for_shorts and allow_conflict_shorts:

                # continuation possible
                # but lower quality than staircase gap structures

                if (
                    not is_atr_filter
                    and is_smt
                    and is_rejection
                ):

                    reversal_confirmation = True
                    candidate.ping_type = "Flush"
                    candidate.initial_target = newyork_context.structure["range_low"]
                    candidate.final_target = "ATR"

                    # optional:
                    # lower confidence weighting
                # TODO: disabling longs for now. review later
                reversal_confirmation = False

            elif look_for_longs and allow_conflict_longs:

                # ideal setup:
                # exhaustion reversal after grinding migration

                if (
                    is_atr_filter
                    and is_smt
                    and is_rejection
                ):

                    reversal_confirmation = True
                    candidate.ping_type = "Rocket"
                    candidate.initial_target = newyork_context.ib_18["low"]
                    candidate.final_target = "DO"

        # =====================================================
        # ACCEPTANCE COMPRESSION CONFIRMATIONS
        # TODO: candidate.fvg_confirmed may not be always true, need sweep_and_ob or fvg_confirmed or sweep rejection
        # at compression sweep
        # =====================================================
        # block completed
        elif structure_name == "bullish_acceptance_compression":
            print("structure : bullish_acceptance_compression")

            # bullish migration accepted first
            # then compression formed inside higher value

            # active compression structure
            # inducement/sweeps likely before expansion release

            # mitigation can occur:
            # - at IB1/IB8 extremes
            # - OR deeper into transition equilibrium
            #   between IB18 high and IB1 low

            # core pings:
                # long after downside liquidity sweep (Rocket)
                # short only after failed bullish acceptance + ATR exhaustion

            if look_for_longs and allow_conflict_longs:

                # primary setup:
                # bullish release after compression sweep
                # Compression reversals are validated more by failed continuation than by immediate displacement
                    # so displacement check or strong body check is optional.
                    # we are only checking if there is an fvg formed inside the OB
                # TODO: filter sweeps for compression lows or mitigation level or 
                # sweep and ob candles rejecting compression lows, mitigation level
                # since this is compression, we need sweep with strong rejection
                # sweep candle time will be ping time
                if (
                    not is_atr_filter
                    and is_smt
                    and is_rejection
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Rocket"
                    candidate.initial_target = newyork_context.structure["range_high"]
                    candidate.final_target = "ATR"

            elif look_for_shorts and allow_conflict_shorts:

                # allow shorts only after:
                # failed bullish compression
                # upside ATR exhaustion
                # failed continuation
                # TODO: order of sweeps?

                if (
                    is_atr_filter
                    and is_smt
                    and is_rejection
                ):

                    reversal_confirmation = True
                    candidate.ping_type = "Flush"
                    candidate.initial_target = newyork_context.structure["mitigation_level"]
                    candidate.final_target = "DO"

        # block completed
        elif structure_name == "bearish_acceptance_compression":
            print("structure : bearish_acceptance_compression")
            
            # bearish migration accepted first
            # then compression formed inside lower value

            # active compression structure
            # inducement/sweeps likely before expansion release

            # mitigation can occur:
            # - at IB1/IB8 extremes
            # - OR deeper into transition equilibrium
            #   between IB18 low and IB1 high

            # core pings:
            # short after upside liquidity sweep (Flush)
            # long only after failed bearish acceptance + ATR exhaustion

            if look_for_shorts and allow_conflict_shorts:

                # primary setup:
                # bearish release after compression sweep
                # Compression reversals are validated more by failed continuation than by immediate displacement
                    # so displacement check or strong body check is optional.
                    # we are only checking if there is an fvg formed inside the OB

                if (
                    not is_atr_filter
                    and is_smt
                    and is_rejection
                ):

                    reversal_confirmation = True
                    candidate.ping_type = "Flush"
                    candidate.initial_target = newyork_context.structure["range_low"]
                    candidate.final_target = "ATR"

            elif look_for_longs and allow_conflict_longs:

                # only allow longs after:
                # failed bearish compression
                # downside ATR exhaustion
                # failed continuation

                if (
                    is_atr_filter
                    and is_smt
                    and is_rejection
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Rocket"
                    candidate.initial_target = newyork_context.structure["mitigation_level"]
                    candidate.final_target = "DO"
        
        # =====================================================
        # REBALANCE COMPRESSION CONFIRMATIONS
        # =====================================================
        # block completed
        elif structure_name == "bullish_rebalance_compression":
            print("structure : bullish_rebalance_compression")

            # initial bullish migration occurred
            # then price compressed/rebalanced back into IB18

            # active rebalance compression structure
            #
            # both directions possible:
            # - Flush from compression highs
            # - Rocket from compression lows
            #
            # liquidity resolution matters more than retracement depth

            # ATR determines:
            # whether further expansion is feasible
            # TODO: sweep validation - long at sweep of compression low only
            # after sweep validation add a flag

            # also if there is no conflict with co asset, then default HTF bias is structure bias
            # here structure is bullish, so 
            # set final targets accordingly, for sweep of compression_high, final_target = compression_lows, ping_type = Mini Flush
            # for sweep of Lows, final_target = ATR, initial_target= Compression_highs, Ping_type = Rocket
            if look_for_longs and allow_conflict_longs:

                # Rocket:
                # typical bullish setup, initial bullish migration, retest of DO, and the expansding higher
                # sweep of compression lows
                # failed downside acceptance
                #
                # can revisit:
                # - premarket highs and ATR
                # - IB1 highs
                # - migration highs

                if (
                    is_smt
                    and is_rejection
                    # TODO: and is_sweep_at_compression_lows or is_sweep_valid
                    # also if HTF is bearish, final_target = compression_high
                    # set ping_type = Mini Rocket
                    # if compression_highs already swept and htf is bullish, then Rocket from Compression_lows
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Rocket"
                    candidate.initial_target = newyork_context.structure["compression_high"]

                    # if ATR still available:
                    # expansion can continue higher
                    # default for bullish structure = ATR 
                    candidate.final_target = "ATR"

            elif look_for_shorts and allow_conflict_shorts:

                # Flush:
                # sweep of compression highs
                # rejection from migration equilibrium

                if (
                    is_smt
                    and is_rejection
                    # TODO: and is_sweep_at_compression_highs or is_sweep_valid
                    # also if HTF is bullish, final_target = compression_low, set ping_type = Mini Flush
                    # if HTF is bearish, if compression_lows already swept and htf is bearish, then Flush from Compression_Highs
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Flush"
                    candidate.initial_target = newyork_context.structure["compression_low"]
                    

                    # if upside ATR already exhausted:
                    # downside move likely terminates
                    # at compression lows / IB18 lows
                    #
                    # otherwise:
                    # full downside expansion still feasible

                    candidate.final_target = (
                        "ATR"
                        if not is_atr_filter
                        else "MINI"
                    )
        # block completed
        elif structure_name == "bearish_rebalance_compression":
            print("structure : bearish_rebalance_compression")
            # initial bearish migration occurred
            # then price compressed/rebalanced back into IB18

            # active rebalance compression structure
            #
            # both directions possible:
            # - Rocket from compression lows
            # - Flush from compression highs
            #
            # liquidity resolution matters more than retracement depth

            # ATR determines:
            # whether further expansion is feasible

            if look_for_shorts and allow_conflict_shorts:

                # Flush:
                # sweep of compression highs
                # typical bearish setup, initial bearish migration, retest of DO, and the expansding lower
                # failed upside acceptance
                #
                # can revisit:
                # - premarket lows
                # - IB1 lows
                # - migration lows

                if (
                    is_smt
                    and is_rejection
                    # TODO: and is_sweep_at_compression_lows or is_sweep_valid
                    # also if HTF is bearish, final_target = compression_high
                    # set ping_type = Mini Rocket
                    # if compression_highs already swept and htf is bullish, then Rocket from Compression_lows
                ):
                    
                    reversal_confirmation = True
                    candidate.ping_type = "Flush"
                    candidate.initial_target = newyork_context.structure["compression_low"]

                    # if ATR still available:
                    # downside expansion can continue
                    # default for bearish structure = ATR
                    candidate.final_target = (
                        "ATR"
                        )

            elif look_for_longs and allow_conflict_longs:

                # Rocket:
                # sweep of compression lows
                # rejection from migration equilibrium

                if (
                    is_smt
                    and is_rejection
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Rocket"
                    candidate.initial_target = newyork_context.structure["compression_high"]

                    # if downside ATR already exhausted:
                    # upside move likely terminates
                    # at compression highs / IB18 highs
                    #
                    # otherwise:
                    # full upside expansion still feasible
                    # default final target = compression high inside bearish structure
                    candidate.final_target = (
                        "ATR" if not is_atr_filter
                        else "MINI"
                    )
        
        
        # ====================================
        # reintegration confirmations
        # ==================================== 
        # Especially In Reintegration Environments The move often begins through acceptance failure
        # key confirmations: smt, atr > 0.9, sweep of IB8 extremes, 30m OB, 3m imbalance
        # optional but not required: displacement, 30m ob is acceptance failure
        # cross asset structure alignment?
        # ping type : Flush (failed continuation after trapped positioning)
        # block completed
        elif structure_name == "bullish_reintegration":
            print("structure : bullish reintegration")
            # weakened bullish structure
            # allow shorts if atr left
            # allow longs if atr exhaustion or used, smt, cross asset alignment
            # this is weak compression = so inducement is additional confirmation, not required
            # additional check using co_asset structure alignment
            # atr usage above open >0.9, no expansion below open
            # atr exhaustion -> reversal to ib1 high
            print("atr filter value: ", is_atr_filter)

            if look_for_shorts and allow_conflict_shorts:
                # atr not exhausted
                # classic protraction: london high, ny continuation - ATR used above open is low. 
                # expect short flush from mitigation level or after sweep of compression high
                # here atr could be close to exhaustion when reinterating, can retrace and push up hisher
                # dont use atr filter, user atr for targets
                if is_smt and candidate.ob_level < newyork_context.structure["mitigation_level"] and is_rejection:
                    reversal_confirmation = True
                    candidate.ping_type = "Flush"
                    candidate.initial_target = newyork_context.structure["compression_low"]
                    candidate.final_target = "ATR"
            # for longs we want to use atr_filter, because the bearish move into reintegration should exhaust
            # for ideal flush
            elif look_for_longs and allow_conflict_longs:
                if is_atr_filter and is_smt and is_rejection:
                    reversal_confirmation = True
                    candidate.ping_type = "Rocket"
                    # tp1 other end of compression range
                    candidate.initial_target = newyork_context.structure["compression_high"]
                    candidate.final_target = "MITL"
            # bullish reintegration reversed to ib1 ce or high
            # at this point dont allow 30m OB as it is still in expansion
            print("candidate.sweep level: ", candidate.sweep_level)
            if look_for_shorts and candidate.ob_level > market_context.session_open:
                print("at this point dont allow 30m OB as it is still in expansion")
                reversal_confirmation = False
        # block completed
        elif structure_name == "bearish_reintegration":
            print("structure : bearish reintegration")
            # weakened bearish structure
            # allow longs if atr left
            # allow shorts if atr exhaustion or used, smt, cross asset alignment
            # this is weak compression = so inducement is additional confirmation, not required
            # additional check using co_asset structure alignment
            # atr usage below open >0.9, no expansion above open
            # atr exhaustion -> reversal to ib1 low
            print("atr filter value: ", is_atr_filter)

            if look_for_longs and allow_conflict_longs:
                # atr not exhausted
                # classic protraction: london low, ny continuation - ATR used below open is low. 
                # expect long expansion from mitigation level or after sweep of compression low
                # here atr could be close to exhaustion when reinterating, can retrace and push up higher
                # dont use atr filter, user atr for targets
                # TODO: valid sweep at compression lows
                if is_smt and candidate.ob_level > newyork_context.structure["mitigation_level"] and is_rejection:
                    reversal_confirmation = True
                    candidate.ping_type = "Rocket"
                    candidate.initial_target = newyork_context.structure["compression_high"]
                    candidate.final_target = "ATR"

            # for shorts we want to use atr_filter, because the bullish move into reintegration should exhaust
            # for ideal flush
            elif look_for_shorts and allow_conflict_shorts:
                if is_atr_filter and is_smt and is_rejection:
                    reversal_confirmation = True
                    candidate.ping_type = "Flush"
                    # tp1 other end of compression range
                    candidate.initial_target = newyork_context.structure["compression_low"]
                    # candidate.final_target = newyork_context.structure["mitigation_level"]
                    candidate.final_target = "MITL"
            # bearish reintegration reversed to ib1 ce or low
            # at this point dont allow 30m OB as it is still in expansion
            print("candidate.sweep level: ", candidate.sweep_level)
            if look_for_longs and candidate.ob_level < market_context.session_open:
                print("at this point dont allow 30m OB as it is still in expansion")
                reversal_confirmation = False
            
        # ====================================
        # value flip confirmations
        # ==================================== 
        # block completed
        elif structure_name == "bullish_value_flip":
            print("structure : bullish value flip")
            # strong bearish repricing structure
            # failed bullish migration
            # market migrated below prior value aggressively

            # core pings:
                # short continuation from mitigation (Flush)
                # long only after downside ATR exhaustion (Rocket)

            if look_for_shorts and allow_conflict_shorts:
                # downside expansion still available
                # continuation flush from failed bullish reclaim
                # strong bearish sign moving towards ATR exhaustion
                #  we only need smt and rejection from IB18 lows
                #  basically retest of gap between ib8 and ib18

                # TODO: valid sweep is sweep of IB8 and retest of gap or retest of ib18 lows
                if (
                    is_smt
                    and is_rejection
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Flush"
                    # opposite end of active range
                    candidate.initial_target = newyork_context.structure["range_low"]
                    candidate.final_target = "ATR"

            elif look_for_longs and allow_conflict_longs:

                # only allow reversal after:
                # downside ATR exhaustion
                # SMT divergence
                # failed downside continuation

                if (
                    is_atr_filter
                    and is_smt
                    and is_rejection
                ):

                    reversal_confirmation = True
                    candidate.ping_type = "Rocket"
                    # reversal objective back into failed migration equilibrium
                    candidate.initial_target = (
                        newyork_context.structure["mitigation_level"]
                    )
                    candidate.final_target = "DO"

            # after successful bullish reversal reclaim above open,
            # do not allow fresh shorts
            # bearish expansion already resolved

            # the below block is removed because the logic is very weak.
            # commenting now so i dont reintroduce it later
            # if look_for_shorts and candidate.ob_level > market_context.session_open:
            #     print("not allowing fresh shorts as bearish move completed and in bullish expansion")
            #     reversal_confirmation = False

        # block completed
        elif structure_name == "bearish_value_flip":
            print("structure : bearish value flip")
            # strongest bullish failure structure
            # initial bearish migration completely failed
            # market migrated above prior value aggressively

            # core pings:
            # long continuation from mitigation (Rocket)
            # short only after upside ATR exhaustion (Flush)

            if look_for_longs and allow_conflict_longs:
                # upside expansion still available
                # continuation rocket from failed bearish reclaim
                if (
                    is_smt
                    and is_rejection
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Rocket"
                    # opposite end of active range
                    candidate.initial_target = newyork_context.structure["range_high"]
                    candidate.final_target = "ATR"

            elif look_for_shorts and allow_conflict_shorts:
                # only allow reversal after:
                # upside ATR exhaustion
                # SMT divergence
                # failed upside continuation
                if (
                    is_atr_filter
                    and is_smt
                    and is_rejection
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Flush"
                    # reversal objective back into failed migration equilibrium
                    candidate.initial_target = newyork_context.structure["mitigation_level"]
                    candidate.final_target = "DO"

            # after successful bearish reversal reclaim below open,
            # do not allow fresh longs
            # bullish expansion already resolved
            # the below block is removed because the logic is very weak.
            # commenting now so i dont reintroduce it later
            # if look_for_longs and candidate.ob_level < market_context.session_open:
            #     reversal_confirmation = False
        
        # ====================================
        # Decompression confirmations
        # ====================================
        # Set 1
        # ==================================== 
        elif structure_name == "bullish_decompression":
            print("structure : bullish decompression")
            # --------------------------------------------------
            # Accepted bullish migration
            # Active expansion phase
            # Strongest continuation environment
            # --------------------------------------------------
            # dont deactivate buy and sell candidates after 8am IB formation
            
            # core pings:
                # long to atr
                # short to DO

            if look_for_longs and allow_conflict_longs:

                # ideal:
                # SMT
                # rejection
                # not a compression zone so we need strong OB displacement filter
                # sweep + OB above CE for long in decompression zone
                # sweep + Strong OB at DO

                if (
                    is_smt
                    and passed_atr_displacement_filter
                    # TODO:
                    # sweep at ib1 low + OB or sweep at DO + OB
                ):

                    reversal_confirmation = True
                    candidate.ping_type = "Expansion"
                    # opposite side of expansion
                    candidate.initial_target = newyork_context.structure["range_high"]
                    candidate.final_target = "ATR"

            elif look_for_shorts and allow_conflict_shorts:

                # countertrend only
                # require exhaustion

                if (
                    is_atr_filter
                    and is_smt
                    and is_rejection
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Mini Flush"
                    candidate.initial_target = newyork_context.structure["mitigation_level"]
                    candidate.final_target = "DO"

        elif structure_name == "bearish_decompression":
            print("structure : bearish decompression")
            # --------------------------------------------------
            # Accepted bearish migration
            # Active expansion phase
            # Strongest continuation environment
            # --------------------------------------------------
            # dont deactivate buy and sell candidates after 8am IB formation
            
            # core pings:
                # short to atr
                # long to DO

            if look_for_shorts and allow_conflict_shorts:

                # ideal:
                # SMT
                # rejection
                # not a compression zone so we need strong OB displacement filter
                # sweep + OB below CE for short in decompression zone
                # sweep + Strong OB at DO
                
                if (
                    is_smt
                    and 
                    passed_atr_displacement_filter
                    # TODO:
                    # sweep at ib1 high + OB or sweep at DO + OB
                ):

                    reversal_confirmation = True
                    candidate.ping_type = "Expansion"
                    # opposite side of expansion
                    candidate.initial_target = newyork_context.structure["range_low"]
                    candidate.final_target = "ATR"

            elif look_for_longs and allow_conflict_longs:

                # countertrend only
                # require exhaustion

                if (
                    is_atr_filter
                    and is_smt
                    and is_rejection
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Mini Rockets"
                    candidate.initial_target = newyork_context.structure["mitigation_level"]
                    candidate.final_target = "DO"
        elif structure_name == "bullish_mixed_decompression":
            print("structure : bullish mixed decompression")
            # structure coming out or weak compression from overlap of ib18 and ib1, sweeping ib1 high
            # core pings:
                # mini flush to compression low
                # Rocket from compression low sweep
            if look_for_longs and allow_conflict_longs:
                # TODO: sweep at compression low
                if is_smt and is_rejection:
                    reversal_confirmation = True
                    candidate.ping_type = "Rocket"
                    candidate.initial_target = newyork_context.structure["compression_high"]
                    candidate.final_target = "ATR"
            elif look_for_shorts and allow_conflict_shorts:
                # TODO: Ob level below ce of decompression range
                if candidate.ob_level < newyork_context.structure["range_ce"]:
                    reversal_confirmation = True
                    candidate.ping_type = "Mini Flush"
                    candidate.initial_target = newyork_context.structure["compression_low"]
                    candidate.final_target = "MINI"
        elif structure_name == "bearish_mixed_decompression":
            print("structure : bearish mixed decompression")
            # structure coming out or weak compression from overlap of ib18 and ib1, sweeping ib1 low
            # core pings:
                # mini rocket to compression high
                # Flush from compression high sweep
            if look_for_shorts and allow_conflict_shorts:
                # TODO: sweep at compression low
                if is_smt and is_rejection:
                    reversal_confirmation = True
                    candidate.ping_type = "Flush"
                    candidate.initial_target = newyork_context.structure["compression_low"]
                    candidate.final_target = "ATR"
            elif look_for_longs and allow_conflict_longs:
                # TODO: Ob level below ce of decompression range or strong Ob
                if candidate.ob_level > newyork_context.structure["range_ce"]:
                    reversal_confirmation = True
                    candidate.ping_type = "Mini Rocket"
                    candidate.initial_target = newyork_context.structure["compression_high"]
                    candidate.final_target = "MINI"
        # ====================================
        # Set 2 Decompression Structures
        # ==================================== 
        elif structure_name == "bullish_macro_decompression":
            print("structure : bullish macro decompression")
            # TODO: give preference to recent candidate among buy and sell candidates
            # dont deactivate candidates at the formation of IB8
            if look_for_longs and allow_conflict_longs:
                if is_smt and passed_atr_displacement_filter:
                    reversal_confirmation = True
                    candidate.ping_type = "Expansion"
                    candidate.initial_target = newyork_context.structure["range_high"]
                    candidate.final_target = "ATR"
            
            elif look_for_shorts and allow_conflict_shorts:
                if is_smt and passed_atr_displacement_filter:
                    reversal_confirmation = True
                    candidate.ping_type = "Expansion"
                    candidate.initial_target = newyork_context.structure["range_low"]
                    candidate.final_target = "ATR"

        elif structure_name == "bearish_macro_decompression":
            print("structure : bearish macro decompression")
            # TODO: give preference to recent candidate among buy and sell candidates
            # dont deactivate candidates at the formation of IB8
            if look_for_shorts and allow_conflict_shorts:
                if is_smt and passed_atr_displacement_filter:
                    reversal_confirmation = True
                    candidate.ping_type = "Expansion"
                    candidate.initial_target = newyork_context.structure["range_low"]
                    candidate.final_target = "ATR"
            
            elif look_for_longs and allow_conflict_longs:
                if is_smt and passed_atr_displacement_filter:
                    reversal_confirmation = True
                    candidate.ping_type = "Expansion"
                    candidate.initial_target = newyork_context.structure["range_high"]
                    candidate.final_target = "ATR"
        elif structure_name == "bullish_mixed_macro_decompression":
            print("structure : bullish mixed macro decompression")
            # this decompression arising from weak compression with sweep of ib18 low
            # core pings:
                # mini rocket to compression high ib1 high
                # Flush from compression high sweep
            if look_for_longs and allow_conflict_longs:
                if is_smt and is_rejection:
                    reversal_confirmation = True
                    candidate.ping_type = "Mini Rocket"
                    candidate.initial_target = newyork_context["compression_high"]
                    candidate.final_target = "MINI"
            elif look_for_shorts and allow_conflict_shorts:
                if is_smt and is_rejection:
                    reversal_confirmation = True
                    candidate.ping_type = "Flush"
                    candidate.initial_target = newyork_context["compression_low"]
                    candidate.final_target = "ATR"
        elif structure_name == "bearish_mixed_macro_decompression":
            print("structure : bearish mixed macro decompression")
            # this decompression arising from weak compression with sweep of IB18 high
            # core pings:
                # mini flush to compression low ib1 low
                # Rocket from compression low sweep
            if look_for_shorts and allow_conflict_shorts:
                if is_smt and is_rejection:
                    reversal_confirmation = True
                    candidate.ping_type = "Mini Flush"
                    candidate.initial_target = newyork_context["compression_low"]
                    candidate.final_target = "MINI"
            elif look_for_longs and allow_conflict_longs:
                if is_smt and is_rejection:
                    reversal_confirmation = True
                    candidate.ping_type = "Rocket"
                    candidate.initial_target = newyork_context["compression_high"]
                    candidate.final_target = "ATR"

        # ====================================
        # Set 3 Decompression Structures
        # ====================================
        # TODO: bullish early decompression but ib8 overlaps with top of IB1 
        # TODO: bearish early decompression but ib8 overlaps with bottom of IB1
        elif structure_name == "bullish_early_decompression":
            print("structure : bullish early decompression")
            # market phase is in decompresion, expansion phase
            # core pings:
                # long from mitigation level to ATR
                # short at atr exhaustion to DO
            if look_for_longs and allow_conflict_longs:
                if is_smt and is_rejection:
                    reversal_confirmation + True
                    candidate.ping_type = "Rocket"
                    candidate.initial_target = newyork_context.structure["range_high"]
                    candidate.final_target = "ATR"
            elif look_for_shorts and allow_conflict_shorts:
                if is_smt and is_rejection and is_atr_filter:
                    reversal_confirmation = True
                    candidate.ping_type = "Flush"
                    candidate.initial_target = newyork_context.structure["mitigation_level"]
                    # TODO: final target can be IB1 high or DO
                    candidate.final_target = "MINI"
        elif structure_name == "bearish_early_decompression":
            print("structure : bearish early decompression")
            # market phase is in decompresion, expansion phase
            # core pings:
                # short from mitigation level to ATR
                # long at atr exhaustion to DO
            if look_for_shorts and allow_conflict_shorts:
                if is_smt and is_rejection:
                    reversal_confirmation + True
                    candidate.ping_type = "Flush"
                    candidate.initial_target = newyork_context.structure["range_low"]
                    candidate.final_target = "ATR"
            elif look_for_longs and allow_conflict_longs:
                if is_smt and is_rejection and is_atr_filter:
                    reversal_confirmation = True
                    candidate.ping_type = "Rocket"
                    candidate.initial_target = newyork_context.structure["mitigation_level"]
                    # TODO: final target can be IB1 low or DO
                    candidate.final_target = "MINI"
        elif structure_name == "mixed_early_decompression":
            print("structure : mixed early decompression")
        
        elif structure_name == "dual_inside_compression":
            print("structure : dual side compression")
        elif structure_name == "centered_compression":
            print("structure : centered compression")
            

        # ====================================
        # sandwich confirmations
            # Most directional
            # ↓
            # sandwich_gap_bullish

            # sandwich_partial_overlap_bullish (acceptance)

            # sandwich_partial_overlap_bullish (rebalance)

            # sandwich_overlap_bullish

            # sandwich_bullish
            # ↑
            # Most balanced
        # ==================================== 
        # block completed
        elif structure_name == "sandwich_gap_bullish":
            print("structure : sandwich gap bullish")
    
            # strongest bullish sandwich compression
            # compression inside bullish repricing territory and not inside old value
            # expect choppy price action at ny open, more than staircase structures
            # structure:
            # IB1 migrated above IB18
            # IB8 compressed cleanly inside the gap
            #
            # no overlap between:
            # - IB18 and IB8
            # - IB8 and IB1
            #
            # this is:
            # elevated compression inside accepted bullish migration

            # active liquidity battlefield:
            # IB8 compression range inside migration gap

            # core behavior:
            # - sweep of compression lows -> Rocket
            # - sweep of compression highs -> Flush
            #  Scenario A: Most common
                #  Compression Low Sweep
                #  ↓
                #  Rocket
            #  Scenario B: Next  common
                #  Compression High Sweep
                #  ↓
                #  Compression Low Sweep
                #  ↓
                #  Rocket
            #  Scenario C: 3rd most common
                #  Compression High Sweep
                #  ↓
                #  Compression Lows (Mini Flush)
            # Least :
                # Compression High Sweep
                # Flush to ATR

            # liquidity resolution matters more than retracement depth

            # ATR determines:
            # whether continuation expansion still feasible

            if look_for_longs and allow_conflict_longs:

                # Rocket:
                # sweep of compression lows
                # failed downside acceptance
                #
                # ideal continuation setup
                # because bullish migration already accepted
                # TODO: valid sweep and rejection of compression lows

                if (
                    is_smt
                    and is_rejection
                ):

                    reversal_confirmation = True
                    candidate.ping_type = "Rocket"
                    # opposite side of compression
                    candidate.initial_target = newyork_context.structure["compression_high"]
                    
                    # if ATR still available:
                    # continuation expansion possible
                    candidate.final_target = "ATR"

            elif look_for_shorts and allow_conflict_shorts:

                # Flush:
                # sweep of compression highs
                # rejection from elevated migration equilibrium

                # if sweep of compression high and compression low already swept, skip short
                # else target compression low -> mini flush

                if (
                    is_smt
                    and is_rejection
                    and not liquidity_levels["cr8am_low"]["swept"]
                    and not co_asset["liquidity_levels"]["cr8am_low"]["swept"]
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Mini Flush"

                    # opposite side of compression
                    candidate.initial_target = newyork_context.structure["compression_low"]

                    # if upside ATR exhausted:
                    # downside likely terminates
                    # at lower compression boundary
                    #
                    # otherwise:
                    # full downside expansion possible
                    # close trade at compression lows as there will be sharp rejection from compression lows
                    candidate.final_target = "MINI"
        # block completed
        elif structure_name == "sandwich_gap_bearish":
            print("structure : sandwich gap bearish")
    
            # strongest bearish sandwich compression
            # compression inside bearish repricing territory and not inside old value
            # expect choppy price action at ny open, more than staircase structures
            #
            # structure:
            # IB1 migrated below IB18
            # IB8 compressed cleanly inside the gap
            #
            # no overlap between:
            # - IB18 and IB8
            # - IB8 and IB1
            #
            # this is:
            # elevated compression inside accepted bearish migration

            # active liquidity battlefield:
            # IB8 compression range inside migration gap

            # core behavior:
            # - sweep of compression highs -> Flush
            # - sweep of compression lows -> Rocket
            #
            # liquidity resolution matters more than retracement depth

            # ATR determines:
            # whether continuation expansion still feasible
            # TODO: valid sweep and rejection of compression lows
            if look_for_shorts and allow_conflict_shorts:

                # Flush:
                # sweep of compression highs
                # failed upside acceptance
                #
                # ideal continuation setup
                # because bearish migration already accepted

                if (
                    is_smt
                    and is_rejection
                ):

                    reversal_confirmation = True
                    candidate.ping_type = "Flush"
                    # opposite side of compression
                    candidate.initial_target = (
                        newyork_context.structure["compression_low"]
                    )

                    # if ATR still available:
                    # continuation expansion possible
                    # bearish structure, final target is ATR
                    candidate.final_target = "ATR"

            elif look_for_longs and allow_conflict_longs:

                # Rocket:
                # sweep of compression lows
                # rejection from elevated migration equilibrium

                if (
                    is_smt
                    and is_rejection
                    and not liquidity_levels["cr8am_high"]["swept"]
                    and not co_asset["liquidity_levels"]["cr8am_high"]["swept"]
                ):

                    reversal_confirmation = True
                    candidate.ping_type = "Mini Rocket"
                    # opposite side of compression
                    candidate.initial_target = newyork_context.structure["compression_high"]

                    # if downside ATR exhausted:
                    # upside likely terminates
                    # at upper compression boundary
                    #
                    # otherwise:
                    # full upside expansion possible
                    # close at compression highs
                    candidate.final_target = "MINI"
        # block completed
        elif structure_name == "sandwich_partial_overlap_bullish":
            print("structure : sandwich partial overlap bullish")
            
            if newyork_context.structure["is_acceptance"]:
                # acceptance block
                # bullish migration accepted first
                # value acceptance / inventory balancing
                # compared to Sandwich Gap Bullish, market has already accepted higher values
                # so sweep of lows -> rocket will be preferred expectation
                
                # IB8 partially overlaps with IB1
                # while still remaining above IB18
                #
                # this is:
                # accepted bullish sandwich compression
                #
                # unlike sandwich_gap_bullish:
                # compression is now partially integrating
                # into the upper migration range

                # active liquidity battlefield:
                # IB8 compression range
                #
                # active migration equilibrium:
                # overlap between IB8 and IB1

                # core behavior:
                # - sweep of compression lows -> Rocket
                # - sweep of compression highs + atr axhaustion -> Flush
                #
                # liquidity resolution matters more than retracement depth

                # ATR determines:
                # whether continuation expansion still feasible

                # possible scenarious:
                # Most likely:
                #     sweep lows first
                #     → Rocket

                # Second most likely:
                #     sweep highs
                #     → sweep lows
                #     → Rocket

                # Less likely:
                #     sweep highs
                #     → immediate bullish continuation

                # Least likely:
                #     sweep highs
                #     → bearish expansion

                if look_for_longs and allow_conflict_longs:

                    # Rocket:
                    # sweep of compression lows
                    # failed downside acceptance
                    #
                    # bullish migration already accepted
                    # overlap acts as continuation equilibrium
                    # TODO: valid sweep at compression low (ib8 low) and initial migration CE (ib18-ib1 ce)
                    if (
                        is_smt
                        and is_rejection
                        # TODO: and is_valid_sweep
                    ):

                        reversal_confirmation = True
                        candidate.ping_type = "Rocket"
                        # opposite side of compression
                        candidate.initial_target = newyork_context.structure["compression_high"]

                        # bullish expansion is preferred expectation, so ATR
                        candidate.final_target = "ATR"

                elif look_for_shorts and allow_conflict_shorts:

                    # Flush:
                    # sweep of compression highs
                    # rejection from upper migration equilibrium
                    #
                    # because overlap now exists,
                    # downside mitigation/rebalance becomes easier
                    # than pure sandwich gap structures

                    if (
                        is_smt
                        and is_rejection
                        and not liquidity_levels["cr8am_low"]["swept"]
                        and not co_asset["liquidity_levels"]["cr8am_low"]["swept"]
                    ):
                        reversal_confirmation = True
                        candidate.ping_type = "Mini Flush"
                        # opposite side of compression
                        candidate.initial_target = newyork_context.structure["compression_low"]

                        # final target is compression low
                        candidate.final_target = "MINI"

            # rebalance block
            # compared to acceptance, both sides likely get cleaned in rebalance structure
            if newyork_context.structure["is_rebalance"]:

                print("structure : sandwich_partial_overlap_bullish with rebalance")

                # initial bullish migration occurred
                # but IB8 rebalanced downward into IB18
                #
                # active rebalance compression structure
                #
                # bullish separation weakened
                # equilibrium shifted lower

                # active compression range:
                # IB8 high ↔ IB18 low

                # core behavior:
                # - Rocket from compression lows
                # - Flush from compression highs

                # liquidity resolution matters more than retracement depth

                # scenarios
                # 1.
                    #  high sweep
                    # ↓
                    # low sweep
                    # ↓
                    # Rocket
                # 2. 
                    # low sweep
                    # ↓
                    # Rocket
                # 3. 
                    # high sweep
                    # ↓
                    # Flush
                    # ↓
                    # compression lows
                # 4. TODO: implement Flush if needed based on HTF
                    # high sweep
                    # ↓
                    # bearish expansion

                if look_for_longs and allow_conflict_longs:

                    # Rocket:
                    # sweep of compression lows
                    # failed downside acceptance

                    if (
                        is_smt
                        and is_rejection
                    ):

                        reversal_confirmation = True
                        candidate.ping_type = "Rocket"
                        candidate.initial_target = newyork_context.structure["compression_high"]
                        # primary expansion candidate, final target is ATR
                        candidate.final_target = "ATR"

                elif look_for_shorts and allow_conflict_shorts:

                    # Flush:
                    # sweep of compression highs
                    # rejection from migration imbalance

                    if (
                        is_smt
                        and is_rejection
                        and not liquidity_levels["cr8am_low"]["swept"]
                        and not co_asset["liquidity_levels"]["cr8am_low"]["swept"]
                    ):

                        reversal_confirmation = True
                        candidate.ping_type = "Mini Flush"

                        candidate.initial_target = newyork_context.structure["compression_low"]
                        candidate.final_target = "MINI"

        # block completed
        elif structure_name == "sandwich_partial_overlap_bearish":
            print("structure : sandwich partial overlap bearish")
            # acceptance block
            if newyork_context.structure["is_acceptance"]:
                print("structure : sandwich_partial_overlap_bearish with acceptance")

                # bearish migration accepted first
                #
                # IB8 partially overlaps with IB1
                # while still remaining below IB18
                #
                # this is:
                # accepted bearish sandwich compression
                #
                # unlike sandwich_gap_bearish:
                # compression is now partially integrating
                # into the lower migration range

                # active liquidity battlefield:
                # IB1 ↔ IB8 overlap compression
                #
                # active compression range:
                # IB8 high ↔ IB1 low

                # active migration equilibrium:
                # overlap between IB8 and IB1

                # core behavior:
                # - sweep of compression highs -> Flush
                # - sweep of compression lows -> Rocket
                #
                # liquidity resolution matters more than retracement depth

                # ATR determines:
                # whether continuation expansion still feasible

                if look_for_shorts and allow_conflict_shorts:

                    # Flush:
                    # sweep of compression highs
                    # failed upside acceptance
                    #
                    # bearish migration already accepted
                    # overlap acts as continuation equilibrium

                    if (
                        is_smt
                        and is_rejection
                        # TODO: and is_valid_sweep
                    ):

                        reversal_confirmation = True
                        candidate.ping_type = "Flush"

                        # opposite side of compression
                        candidate.initial_target = newyork_context.structure["compression_low"]

                        # primary scenario towards ATR

                        candidate.final_target = "ATR"

                elif look_for_longs and allow_conflict_longs:

                    # Rocket:
                    # sweep of compression lows
                    # rejection from lower migration equilibrium
                    #
                    # because overlap now exists,
                    # upside mitigation/rebalance becomes easier
                    # than pure sandwich gap structures

                    if (
                        is_smt
                        and is_rejection
                        and not liquidity_levels["cr8am_high"]["swept"]
                        and not co_asset["liquidity_levels"]["cr8am_high"]["swept"]
                    ):
                        reversal_confirmation = True

                        candidate.ping_type = "Mini Rocket"

                        # opposite side of compression
                        candidate.initial_target = newyork_context.structure["compression_high"]
                        candidate.final_target = "MINI"

            # rebalance block
            if newyork_context.structure["is_rebalance"]:
                print("structure : sandwich_partial_overlap_bearish with rebalance")

                # initial bearish migration occurred
                # but IB8 rebalanced upward into IB18
                #
                # active rebalance compression structure
                #
                # bearish separation weakened
                # equilibrium shifted higher

                # IB8 did NOT integrate into IB1
                # instead:
                # compression rebalanced upward toward prior value

                # active compression range:
                # IB18 high ↔ IB8 low

                # migration imbalance zone:
                # IB1 high ↔ IB8 low

                # core behavior:
                # - Flush from compression highs
                # - Rocket from compression lows
                #
                # liquidity resolution matters more than retracement depth

                # ATR determines:
                # whether continuation expansion still feasible
                # scenarios
                # 1.
                    # low sweep
                    # ↓
                    # high sweep
                    # ↓
                    # Flush
                # 2. 
                    # high sweep
                    # ↓
                    # Flush
                # 3. 
                    # Low sweep
                    # ↓
                    # Mini Rocket
                    # ↓
                    # compression highs
                # 4. TODO: implement Rocket if needed based on HTF
                    # low sweep
                    # ↓
                    # bullish expansion

                if look_for_shorts and allow_conflict_shorts:

                    # Flush:
                    # sweep of compression highs
                    # rejection from rebalance equilibrium
                    #
                    # continuation back toward:
                    # - IB1 lows
                    # - migration lows
                    # - external liquidity

                    if (
                        is_smt
                        and is_rejection
                    ):

                        reversal_confirmation = True

                        candidate.ping_type = "Flush"

                        candidate.initial_target = newyork_context.structure["compression_low"]

                        # primary expansion towards ATR in bearish structure
                        candidate.final_target = "ATR"

                elif look_for_longs and allow_conflict_longs:

                    # Rocket:
                    # sweep of compression lows
                    # failed downside continuation
                    #
                    # rebalance acting like:
                    # retest of daily open / prior equilibrium

                    if (
                        is_smt
                        and is_rejection
                        and not liquidity_levels["cr8am_high"]["swept"]
                        and not co_asset["liquidity_levels"]["cr8am_high"]["swept"]
                    ):

                        reversal_confirmation = True
                        candidate.ping_type = "Mini Rocket"
                        candidate.initial_target = newyork_context.structure["compression_high"]
                        # close at compression highs.
                        candidate.final_target = "MINI"

                        
        # block completed
        elif structure_name == "sandwich_overlap_bullish":
            print("structure : sandwich overlap bullish")
            # as compared to sandwich gap bullish, this is no longer repricing, but balanced inventory
            # sandwich gap still contains unresolved migration
            # sandwich_overlap_bullish: resolved migration + balanced inventory. two-sided liquidity collection
    
            # initial bullish migration occurred
            #
            # but now:
            # - IB8 overlaps upward into IB1
            # - AND downward into IB18
            #
            # this is:
            # full sandwich overlap compression
            #
            # equilibrium now spans:
            # - prior value
            # - migration value
            # - active compression value

            # strongest two-sided compression battlefield
            #
            # bullish migration still exists,
            # but separation weakened materially

            # active compression range:
            # IB1 high ↔ IB18 low

            # active equilibrium:
            # overlap between:
            # - IB18
            # - IB8
            # - IB1

            # core behavior:
            # - Rocket from compression lows
            # - Flush from compression highs
            #
            # liquidity resolution matters more than retracement depth

            # ATR determines:
            # whether continuation expansion still feasible
            
            # market behavior in this structure
            # auction
            # ↓
            # auction
            # ↓
            # auction complete
            # ↓
            # expansion

            if look_for_longs and allow_conflict_longs:

                # Rocket:
                # sweep of compression lows
                # continuation back toward:
                # - IB1 highs
                # - migration highs
                # - external liquidity
                # TODO: review smt for all structures for cr8am_high or low levels
                if (
                    is_smt
                    and is_rejection
                    and not liquidity_levels["cr8am_high"]["swept"]
                    and not co_asset["liquidity_levels"]["cr8am_high"]["swept"]
                ):

                    reversal_confirmation = True
                    candidate.ping_type = "Mini Rocket"
                    candidate.initial_target = newyork_context.structure["compression_high"]
                    # market still hasnt decided direction, close at compression high
                    candidate.final_target = "MINI"
                elif (
                    is_smt
                    and is_rejection
                    and (
                        liquidity_levels["cr8am_high"]["swept"] 
                        or co_asset["liquidity_levels"]["cr8am_high"]["swept"]
                    )
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Rocket"
                    candidate.initial_target = newyork_context.structure["compression_high"]
                    # both sides liquidity harvested, price ready to expand
                    candidate.final_target = "ATR"

            elif look_for_shorts and allow_conflict_shorts:

                # Flush:
                # sweep of compression highs
                # rejection from upper equilibrium
                #
                # because equilibrium fully rebuilt,
                # downside rebalancing becomes highly viable

                if (
                    is_smt
                    and is_rejection
                    and not liquidity_levels["cr8am_low"]["swept"]
                    and not co_asset["liquidity_levels"]["cr8am_low"]["swept"]
                ):

                    reversal_confirmation = True
                    candidate.ping_type = "Mini Flush"
                    candidate.initial_target = newyork_context.structure["compression_low"]
                    # market hasnt decided yet
                    candidate.final_target = "MINI"
                elif (
                    is_smt
                    and is_rejection
                    and (
                        liquidity_levels["cr8am_low"]["swept"] 
                        or 
                        co_asset["liquidity_levels"]["cr8am_low"]["swept"]
                    )
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Flush"
                    candidate.initial_target = newyork_context.structure["compression_low"]
                    # market harvested liquidity on both sides
                    candidate.final_target = "ATR"
                    
        # block completed
        elif structure_name == "sandwich_overlap_bearish":
            print("structure : sandwich_overlap_bearish")

            # initial bearish migration occurred
            #
            # but now:
            # - IB8 overlaps downward into IB1
            # - AND upward into IB18
            #
            # this is:
            # full sandwich overlap compression
            #
            # equilibrium now spans:
            # - prior value
            # - migration value
            # - active compression value

            # strongest two-sided compression battlefield
            #
            # bearish migration still exists,
            # but separation weakened materially

            # active compression range:
            # IB18 high ↔ IB1 low

            # active equilibrium:
            # overlap between:
            # - IB18
            # - IB8
            # - IB1

            # core behavior:
            # - Flush from compression highs
            # - Rocket from compression lows
            #
            # liquidity resolution matters more than retracement depth

            # ATR determines:
            # whether continuation expansion still feasible

            if look_for_shorts and allow_conflict_shorts:

                # Flush:
                # sweep of compression highs
                # failed upside acceptance
                #
                # continuation back toward:
                # - IB1 lows
                # - migration lows
                # - external liquidity

                if (
                    is_smt
                    and is_rejection
                    and not liquidity_levels["cr8am_low"]["swept"]
                    and not co_asset["liquidity_levels"]["cr8am_low"]["swept"]
                ):

                    reversal_confirmation = True
                    candidate.ping_type = "Mini Flush"

                    candidate.initial_target = newyork_context.structure["compression_low"]
                    # market is not ready yet for the move
                    candidate.final_target = "MINI"
                elif (
                    is_smt
                    and is_rejection
                    and (
                        liquidity_levels["cr8am_low"]["swept"]
                          or 
                        co_asset["liquidity_levels"]["cr8am_low"]["swept"]
                    )
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Flush"

                    candidate.initial_target = newyork_context.structure["compression_low"]
                    # market has harvested liquidity on both sides and ready to expand
                    candidate.final_target = "ATR"

            elif look_for_longs and allow_conflict_longs:

                # Rocket:
                # sweep of compression lows
                # rejection from lower equilibrium
                #
                # because equilibrium fully rebuilt,
                # upside rebalancing becomes highly viable

                if (
                    is_smt
                    and is_rejection
                    and not liquidity_levels["cr8am_high"]["swept"]
                    and not co_asset["liquidity_levels"]["cr8am_high"]["swept"]
                ):

                    reversal_confirmation = True
                    candidate.ping_type = "Mini Rocket"
                    candidate.initial_target = newyork_context.structure["compression_high"]
                    # market not ready yet for the final move
                    candidate.final_target = "MINI"
                elif (
                    is_smt
                    and is_rejection
                    and (
                        liquidity_levels["cr8am_high"]["swept"] 
                         or 
                        co_asset["liquidity_levels"]["cr8am_high"]["swept"]
                    )
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Rocket"
                    candidate.initial_target = newyork_context.structure["compression_high"]
                    # market has harvested liquidity on both sides and ready to expand
                    candidate.final_target = "ATR"
        # block completed
        elif structure_name == "sandwich_bullish":
            print("structure : sandwich_bullish")

            # continuous bullish overlap migration
            #
            # no clean gaps between IBs
            #
            # structure:
            # - IB1 migrated above IB18
            # - but still overlaps IB18
            # - IB8 overlaps both IB1 and IB18
            #
            # this is:
            # fully integrated bullish sandwich compression
            #
            # equilibrium continuously rebuilt upward

            # active compression range:
            # IB18 low ↔ IB1 high

            # IB8 acts as:
            # internal equilibrium node
            #
            # NOT:
            # isolated compression container

            # this structure behaves like:
            # grinding bullish migration with broad equilibrium

            # core behavior:
            # - Rocket from compression lows
            # - Flush from compression highs
            #
            # liquidity resolution matters more than retracement depth

            # ATR determines:
            # whether continuation expansion still feasible

            # both sides liquidity resolution required before expansion

            if look_for_longs and allow_conflict_longs:

                # Rocket:
                # Mini Rocket:

                if (
                    is_smt
                    and is_rejection
                    and not liquidity_levels["cr8am_high"]["swept"]
                    and not co_asset["liquidity_levels"]["cr8am_high"]["swept"]
                ):

                    reversal_confirmation = True
                    candidate.ping_type = "Mini Rocket"
                    candidate.initial_target = (
                        newyork_context.structure["compression_high"]
                    )
                    candidate.final_target = "MINI"
                elif (
                    is_smt
                    and is_rejection
                    and (
                        liquidity_levels["cr8am_high"]["swept"]
                        or 
                        co_asset["liquidity_levels"]["cr8am_high"]["swept"]
                    )
                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Rocket"
                    candidate.initial_target = (
                        newyork_context.structure["compression_high"]
                    )
                    candidate.final_target = "ATR"

            elif look_for_shorts and allow_conflict_shorts:

                # Flush:
                # sweep of compression highs
                # rejection from upper equilibrium
                #
                # because equilibrium rebuilt continuously,
                # downside rebalance becomes highly viable

                if (
                    is_smt
                    and is_rejection
                    and not liquidity_levels["cr8am_low"]["swept"]
                    and not co_asset["liquidity_levels"]["cr8am_low"]["swept"]
                ):

                    reversal_confirmation = True
                    candidate.ping_type = "Mini Flush"
                    candidate.initial_target = (
                        newyork_context.structure["compression_low"]
                    )
                    candidate.final_target = "MINI"

                elif (
                    is_smt
                    and is_rejection
                    and (
                        liquidity_levels["cr8am_low"]["swept"] or co_asset["liquidity_levels"]["cr8am_low"]["swept"])
                ):

                    reversal_confirmation = True
                    candidate.ping_type = "Flush"
                    candidate.initial_target = (
                        newyork_context.structure["compression_low"]
                    )
                    candidate.final_target = "ATR"
                    
        # block completed      
        elif structure_name == "sandwich_bearish":
            print("structure : sandwich_bearish")

            # continuous bearish overlap migration
            #
            # no clean gaps between IBs
            #
            # structure:
            # - IB1 migrated below IB18
            # - but still overlaps IB18
            # - IB8 overlaps both IB1 and IB18
            #
            # this is:
            # fully integrated bearish sandwich compression
            #
            # equilibrium continuously rebuilt downward

            # active compression range:
            # IB18 high ↔ IB1 low

            # IB8 acts as:
            # internal equilibrium node
            #
            # NOT:
            # isolated compression container

            # this structure behaves like:
            # grinding bearish migration with broad equilibrium

            # core behavior:
            # - Flush from compression highs
            # - Rocket from compression lows
            #
            # liquidity resolution matters more than retracement depth

            # ATR determines:
            # whether continuation expansion still feasible

            if look_for_shorts and allow_conflict_shorts:

                # Flush:
                # sweep of compression highs
                # failed upside acceptance
                #
                # continuation toward:
                # - IB1 lows
                # - migration lows
                # - external liquidity

                if (
                    is_smt
                    and is_rejection
                    and not liquidity_levels["cr8am_low"]["swept"]
                    and not co_asset["liquidity_levels"]["cr8am_low"]["swept"]
                ):

                    reversal_confirmation = True
                    candidate.ping_type = "Mini Flush"
                    candidate.initial_target = newyork_context.structure["compression_low"]
                    candidate.final_target = "MINI"
                elif (
                    is_smt
                    and is_rejection
                    and (
                        liquidity_levels["cr8am_low"]["swept"] 
                        or co_asset["liquidity_levels"]["cr8am_low"]["swept"]
                    )
                ):

                    reversal_confirmation = True
                    candidate.ping_type = "Flush"
                    candidate.initial_target = (
                        newyork_context.structure["compression_low"]
                    )
                    candidate.final_target = "ATR"

            elif look_for_longs and allow_conflict_longs:

                # Rocket:
                # sweep of compression lows
                # rejection from lower equilibrium
                #
                # because equilibrium rebuilt continuously,
                # upside rebalance becomes highly viable

                if (
                    is_smt
                    and is_rejection
                    and not liquidity_levels["cr8am_high"]["swept"]
                    and not co_asset["liquidity_levels"]["cr8am_high"]["swept"]

                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Mini Rocket"
                    candidate.initial_target = newyork_context.structure["compression_high"]
                    candidate.final_target = "MINI"
                elif (
                    is_smt
                    and is_rejection
                    and (
                        liquidity_levels["cr8am_high"]["swept"] 
                        or co_asset["liquidity_levels"]["cr8am_high"]["swept"]
                    )

                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Rocket"
                    candidate.initial_target = (
                        newyork_context.structure["compression_high"]
                    )
                    candidate.final_target = "ATR"
                        
        elif structure_name == "sandwich_neutral":
            print("structure : sandwich_neutral")

            # structure:
            # - IB1 engulfs IB18
            # - IB8 inside IB1
            
            # core behavior:
            # - Flush from compression highs
            # - Rocket from compression lows
            #
            # liquidity resolution matters more than retracement depth

            # ATR determines:
            # whether continuation expansion still feasible

            if look_for_shorts and allow_conflict_shorts:

                if (
                    is_smt
                    and is_rejection
                    and not liquidity_levels["cr8am_low"]["swept"]
                    and not co_asset["liquidity_levels"]["cr8am_low"]["swept"]
                ):

                    reversal_confirmation = True
                    candidate.ping_type = "Mini Flush"
                    candidate.initial_target = newyork_context.structure["compression_low"]
                    candidate.final_target = "MINI"
                elif (
                    is_smt
                    and is_rejection
                    and (
                        liquidity_levels["cr8am_low"]["swept"] or co_asset["liquidity_levels"]["cr8am_low"]["swept"] )
                ):

                    reversal_confirmation = True
                    candidate.ping_type = "Flush"
                    candidate.initial_target = newyork_context.structure["compression_low"]
                    candidate.final_target = "ATR"

            elif look_for_longs and allow_conflict_longs:

                # Rocket:
                # sweep of compression lows
                if (
                    is_smt
                    and is_rejection
                    and not liquidity_levels["cr8am_high"]["swept"]
                    and not co_asset["liquidity_levels"]["cr8am_high"]["swept"]

                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Mini Rocket"
                    candidate.initial_target = newyork_context.structure["compression_high"]
                    candidate.final_target = "MINI"
                elif (
                    is_smt
                    and is_rejection
                    and (
                        liquidity_levels["cr8am_high"]["swept"] 
                        or co_asset["liquidity_levels"]["cr8am_high"]["swept"]
                    )

                ):
                    reversal_confirmation = True
                    candidate.ping_type = "Rocket"
                    candidate.initial_target = newyork_context.structure["compression_high"]
                    candidate.final_target = "ATR"
                        
        
        elif structure_name == "centered_compression":
            print("structure : centered compression")
        
        elif ib_relationship == "inside_18":
            print("ib8am is inside ib18")
            # one line rule: returning to the edge weakens the move, compressing inside preserves it
            print("8am compression: ", ib_relationship, "sweep info: ", newyork_context.sweep)
            print("ib18_above_ib1: ", newyork_context.structure["ib18_above_ib1"])
            print("ib1_above_ib18: ", newyork_context.structure["ib18_below_ib1"])
            passed_atr_displacement_filter = displacement_atr_filter()
            print("post 8AM IB, passed atr displacemet filter: ", passed_atr_displacement_filter)
            
            # when ib8 is inside ib18 with ib1 above or below ib18
                # ib1 direction still intact, as it did not overlap with ib18 extremes
                # this is re-compression
                # if atr not exhausted, then high probability in the direction of IB1
            if newyork_context.structure["ib18_below_ib1"]:
                # allow longs when atr not exhausted and ib18 lows are swept with smt
                allow_bearish_expansion: True
                allow_bullish_expansion: True
                if market_context.atr_used_above_open > 0.7 or market_context.no_bearish_expansion_below_open:   
                    # invalidate shorts as expansion is low probability below open
                    allow_bearish_expansion = False
                    
                # else:
                #     # bearish expansion possible after rebalance to ib18 and ib1 range equilibrium
                #     print("implement this block")
                if look_for_longs and allow_bullish_expansion and passed_atr_displacement_filter and is_smt:
                    reversal_confirmation = True
                    candidate.ping_type = "Expansion"
                    # final target = 2nd target, actual final target = ATR
                    candidate.final_target = "PMH"
                elif look_for_shorts and allow_bearish_expansion and passed_atr_displacement_filter and is_smt:
                    reversal_confirmation = True
                    candidate.ping_type = "Expansion"
                    candidate.final_target = "IBL18"


            elif newyork_context.structure["ib18_above_ib1"]:
                # allow shorts when atr not exhausted and ib18 lows are swept with smt
                allow_bearish_expansion: True
                allow_bullish_expansion: True
                if market_context.atr_used_below_open > 0.7 or market_context.no_bullish_expansion_above_open:
                    # invalidate longs as expansion is low probability above open
                    allow_bullish_expansion = False
                    print("implement this block")

                if look_for_longs and allow_bullish_expansion and passed_atr_displacement_filter and is_smt:
                    reversal_confirmation = True
                    candidate.ping_type = "Expansion"
                    candidate.final_target = "IBH18"

                elif look_for_shorts and allow_bearish_expansion and passed_atr_displacement_filter and is_smt:
                    reversal_confirmation = True
                    candidate.ping_type = "Expansion"
                    candidate.final_target = "PML"
            
        elif ib_relationship in ("engulfing_1am", "engulfing_18"):
            print("8am early expansion: ", ib_relationship)
            # ist scenario: deep retracement = re-compression, sweep is valid, checked after the initial
            # sweep is detected
            if newyork_context.phase == "recompression":
                # handle similar to inside compression
                passed_atr_displacement_filter = displacement_atr_filter()
                print("post 8AM IB, passed atr displacemet filter: ", passed_atr_displacement_filter)
                reversal_confirmation = passed_atr_displacement_filter
                candidate.ping_type = "Flush" if look_for_longs else "Rocket"
                candidate.final_target = "ATR"
            else:
                # not recompression, we have sweep below ce of compression range.
                # we already have a valid ob. key OB similar to 2am IB is not required
                # we just need smt
                passed_atr_displacement_filter = displacement_atr_filter()
                print("post 8AM IB, passed atr displacemet filter: ", passed_atr_displacement_filter)
                reversal_confirmation = passed_atr_displacement_filter and is_smt
                candidate.ping_type = "Expansion"
                candidate.final_target = "ATR"

                
            # additional - pdh or pdl taken, atr exhausted, and onesided 8am IB

        elif ib_relationship == "sandwich":
            print("8am compression: ", ib_relationship)
            # no need to check displacement or atr exhaustion
            # valid sweep accounted for including inducement
            mini = False

            if co_asset["newyork_context"].structure["ib_relationship"] != "sandwich":
                if not co_asset["newyork_context"].structure["compression"]:
                    mini = True
            reversal_confirmation = True
            if last_closed_candle["open"] > newyork_context.structure["range_high"] or last_closed_candle["open"] < newyork_context.structure["range_low"]:
                # sweep is not at compression range extremes
                mini = False
            if mini:
                candidate.ping_type = "Mini Rocket" if look_for_longs else "Mini Flush"
            else:
                candidate.ping_type = "Rocket" if look_for_longs else "Flush"
            candidate.final_target = "LIQUIDITY"

        elif ib_relationship in ("above_1_18", "below_1_18"):
            print("8am market exhaustion or trending: ", ib_relationship)
            # main setup is reversal upon atr exhaustion
            passed_atr_displacement_filter = displacement_atr_filter()
            print("post 8AM IB, passed atr displacemet filter: ", passed_atr_displacement_filter)
            reversal_confirmation = passed_atr_displacement_filter and is_smt

        elif ib_relationship in ("partial_overlap_bullish", "partial_overlap_bearish"):
            # where is the sweep happening at compression high or rebalance level?
            
            # scanario 1:
            # no overlap between ib1 and ib8. there is a gap. 
            # so price can rebalance to this gap and expand higher
            # we need smt at rebalance level and atr not exhausted(optional) in the direction of asia and london
                # two options:
                # option1: if setup is forming at compressin high or low, then anticipate reversal to daily open. no expansion below
                # daily open as atr is already used up
                # option2: if setup is forming at rebalance level, expect continuation higher towards pre-market highs and atr 0.95%
                 
            if not newyork_context.structure["is_staircase"] and not co_asset["newyork_context"].structure["is_staircase"]:
                print("no staricase on both assets: ", newyork_context.structure["ib_relationship"])
                # there is a gap on both es and nq, price movement in one direction
                # sweep is already validated
                # need to check atr exhaustion for continuation, smt at rebalance level
                # additional: rejecting rebalance level and or IB1
                # option1: sweep at compression extremes external (partial_overlap_bullish -> compression high, partial_overlap_bearish -> compression low )
                # option2: sweep at RL, targer pre market highs and lows and atrs
                passed_atr_displacement_filter = displacement_atr_filter()
                print("post 8AM IB, passed atr displacemet filter: ", passed_atr_displacement_filter)
                print("is_smt: ", is_smt)
                # update candidate with profit targets
                if ib_relationship == "partial_overlap_bullish" and look_for_shorts:
                    # atr exhaustion -> target daily open
                    # atr not exhausted -> target ib18 high, rebalance level
                    if (market_context.overnight_expansion or market_context.exhaustion):
                        candidate.ping_type = "Expansion"
                        candidate.final_target = "DO"
                    else:
                        candidate.ping_type = "Quick Short"
                        candidate.final_target = "RL"
                    
                elif ib_relationship == "partial_overlap_bullish" and look_for_longs:
                    # target pre-market highs and atr 95%
                    if (market_context.overnight_expansion or market_context.exhaustion):
                        candidate.ping_type = "Quick Long"
                        candidate.final_target = "PMH"
                    else:
                        candidate.ping_type = "Expansion"
                        candidate.final_target = "ATR"
                elif ib_relationship == "partial_overlap_bearish" and look_for_longs:
                    # atr exhaustion -> target daily open
                    # atr not exhausted -> target ib18 lows, rebalance level
                    if (market_context.overnight_expansion or market_context.exhaustion):
                        candidate.ping_type = "Expansion"
                        candidate.final_target = "DO"
                    else:
                        candidate.ping_type = "Quick Long"
                        candidate.final_target = "RL"
                elif ib_relationship == "partial_overlap_bearish" and look_for_shorts:
                    # target pre-market lows and atr 95%
                    if (market_context.overnight_expansion or market_context.exhaustion):
                        candidate.ping_type = "Quick Short"
                        candidate.final_target = "PML"
                    else:
                        candidate.ping_type = "Expansion"
                        candidate.final_target = "ATR"

                reversal_confirmation = passed_atr_displacement_filter and is_smt
                print("xxx1: ", reversal_confirmation)
                print("targets: pre-market high/low and 0.95 atr")
                
            
            # scenario 2:
            elif newyork_context.structure["is_staircase"] and co_asset["newyork_context"].structure["is_staircase"]:
                print("staricase on both assets: ", newyork_context.structure["ib_relationship"])
                # there is no gap on both es and nq, asia and london build LRLR on staircase asset
                # allow only reversal = Ping Flush. 
                # additional: 
                    # liquidity purge at key levels PDH/L or London H/L
                    # atr exhaustion (optional)
                    # smt
                key_level_swept = False
                if look_for_longs:
                    key_level_swept = liquidity_levels["pdl"]["swept"] or liquidity_levels["london_low"]["swept"] or co_asset["liquidity_levels"]["pdl"]["swept"] or co_asset["liquidity_levels"]["london_low"]["swept"]
                elif look_for_shorts:
                    key_level_swept = liquidity_levels["pdh"]["swept"] or liquidity_levels["london_high"]["swept"] or co_asset["liquidity_levels"]["pdh"]["swept"] or co_asset["liquidity_levels"]["london_high"]["swept"]
                passed_atr_displacement_filter = displacement_atr_filter()
                print("post 8AM IB, passed atr displacemet filter: ", passed_atr_displacement_filter)
                print("is_smt: ", is_smt)
                reversal_confirmation = passed_atr_displacement_filter and is_smt and key_level_swept
                print("xxx1: ", reversal_confirmation)
                print("targets: pre-market high/low and 0.95 atr")
                candidate.ping_type = "Flush" if look_for_shorts else "Rocket"
                candidate.final_target = "ATR"
            # scenario 3:
            # same as scenario 2
            else:
                # gap on one of the asset, staicase on other
                # we shall look for only reversals, as there is strong compression on one and
                # weak compression on the other
                print("staricase on at leaset one assets: ", newyork_context.structure["ib_relationship"])
                key_level_swept = False
                if look_for_longs:
                    key_level_swept = liquidity_levels["pdl"]["swept"] or liquidity_levels["london_low"]["swept"] or co_asset["liquidity_levels"]["pdl"]["swept"] or co_asset["liquidity_levels"]["london_low"]["swept"]
                elif look_for_shorts:
                    key_level_swept = liquidity_levels["pdh"]["swept"] or liquidity_levels["london_high"]["swept"] or co_asset["liquidity_levels"]["pdh"]["swept"] or co_asset["liquidity_levels"]["london_high"]["swept"]
                passed_atr_displacement_filter = displacement_atr_filter()
                print("post 8AM IB, passed atr displacemet filter: ", passed_atr_displacement_filter)
                print("is_smt: ", is_smt)
                reversal_confirmation = passed_atr_displacement_filter and is_smt and key_level_swept
                print("xxx1: ", reversal_confirmation)
                print("targets: pre-market high/low and 0.95 atr")
                candidate.ping_type = "Flush" if look_for_shorts else "Rocket"
                candidate.final_target = "ATR"

        elif ib_relationship in ("partial_overlap_bullish_neutral", "partial_overlap_bearish_neutral"):
            print("ib_relationship: ", ib_relationship)
            # since price reaches edge of ib18 after initial move from ib18 to ib1, the initial move is weakened
            # high probability scenarios
                # if ib1 is below ib18 with ib8 above ib18, anticipate rebalance towards rebalance level and continue higher
                # if ib1 is above 1b18 with ib8 below ib18, anticipate rebalance towards rebalance level and continue lower
                # ib18 to ib1 -> atr should be small -> which implies manipulation
                # if atr ib18 to ib1 is large then there will be no continuation because atr is exhausted or used up from ib18 to ib1
            allow_shorts = True
            allow_longs = True
            # price is already at open near ib18, so no trade to target daily open
            if market_context.no_bullish_expansion_above_open:
                allow_longs = False
            elif market_context.no_bearish_expansion_below_open:
                allow_shorts = False
            

            if ib_relationship == "partial_overlap_bullish_neutral":
                # ib8 above ib18, ib1 below ib18
                if 0.4 < market_context.atr_used_below_open < 0.6:
                    # allow expansion above open from rebalance level
                    # sweep is already check for validity from rebalance level
                    reversal_confirmation = True
                else:
                    reversal_confirmation = False
            elif ib_relationship == "partial_overlap_bearish_neutral":
                if 0.4 < market_context.atr_used_above_open < 0.6:
                    # allow expansion below open from rebalance level
                    # sweep is already check for validity from rebalance level
                    reversal_confirmation = True
                else:
                    reversal_confirmation = False

           # low probability - we shall skip this for now
                # quick trade towards rebalance level as price is ranging
                # quick or short trade to rebalance level and Ib
            # check for displacement_atr_filter()
            if reversal_confirmation:
                print("8am weak compression -> will range or continue from rebalance level: ", ib_relationship)
                passed_atr_displacement_filter = displacement_atr_filter()
                print("post 8AM IB, passed atr displacemet filter: ", passed_atr_displacement_filter)
                reversal_confirmation = passed_atr_displacement_filter and is_smt
                candidate.ping_type = "Expansion"
                candidate.final_target = "ATR"
            
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
            asia_swept = liquidity_levels["asia_high"]["swept"] or co_asset["liquidity_levels"]["asia_high"]["swept"]
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
            asia_swept = liquidity_levels["asia_low"]["swept"] or co_asset["liquidity_levels"]["asia_low"]["swept"]
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
            
    # TODO: implement this block after implementing IB blocks
    elif window_name == "7h_wick_0100":
        print("window trade: ", window_name)

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
        print("window trade: ", window_name)
        # sweep should be inside the 7h wick window. this window is only to capture 7h wick reversals
        # at least sweep should be in this window
        sweep_window_name = get_active_window(candidate.sweep_timestamp)
        print("sweep window: ", sweep_window_name)

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
        if passed_atr_displacement_filter and window_name == sweep_window_name:
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
        print("window trade: ", "post london killzone")
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
        # block setups outside structures
        reversal_confirmation = False
        return reversal_confirmation
    else:
        print("window trade: ", "no window")
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
        # return reversal_confirmation
        return False
    print("final return: ", reversal_confirmation)
    return reversal_confirmation
        



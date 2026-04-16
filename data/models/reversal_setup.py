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

def check_for_reversal_setup_confirmation(market_context, seven_hour_builder_candles, liquidity_levels_nq, liquidity_levels_es, candidate, last_closed_candle, current_30m_start, daily_atr, smt_summary):
    # get session time
    # bias from previous 7hr candle (ex: bearish)
    # price is below (bearish) previous 7hr candle and (or) rejecting previous 7hr ib
    # price should be below or rejecting current 7hr ib
    # if price is above current 7hr ib and rejecting previous 7hr ib = Manipulation of current 7hr
    # high = last_closed_candle["high"]
    # low = last_closed_candle["low"]
    window_name = get_active_window(current_30m_start)
    close = last_closed_candle["close"]
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
    # in ny killzone lets include 8am wick window as out setup forms around 7hr wicks
    is_ny_am_killzone = in_session(current_30m_start, 8, 0, 12, 30)
    is_ny_lunch_time = in_session(current_30m_start, 11, 0, 13, 30)
    if window_name is "7h_wick_0800" and is_ny_am_killzone:
        is_ny_am_killzone = False
    print("----------------------------------------")
    print("is_london_killzone: ", is_london_killzone, " |  is_ny_am_killzone: ", is_ny_am_killzone)
    print("market context: ", market_context.values())
    # print("smt summary: ", smt_summary)
    
    # bias = prev_seven_hour_candle["bias"]

    look_for_shorts = False
    look_for_longs = False
    if candidate.side == "buy_side":
        look_for_shorts = True
    elif candidate.side == "sell_side":
        look_for_longs = True
    is_smt = False
    print("smt summary: ", smt_summary)
    if look_for_shorts:
        if smt_summary["bearish_smt_1h"] is not None or smt_summary["bearish_smt_30m_swing"] is not None:
            is_smt = True
    elif look_for_longs:
        if smt_summary["bullish_smt_1h"] is not None or smt_summary["bullish_smt_30m_swing"] is not None:
            is_smt = True
    
    session_direction = market_context.session_direction
    atr_usage = market_context.atr_usage
    london_context = context_for_london(market_context)

    # -----------------------------------------------
    # disable or allow longs and shorts based on atr_usage and smt
    # -----------------------------------------------
    look_for_longs = filter_longs_london(look_for_longs, session_direction, atr_usage, is_smt)
    look_for_shorts = filter_shorts_london(look_for_shorts, session_direction, atr_usage, is_smt)    
    # -----------------------------------------------

    
    if is_london_killzone:
        # get seven hour candles
        seven_hour_candle_6pm = seven_hour_builder_candles["6PM"].values()
        seven_hour_candle_1am = seven_hour_builder_candles["1AM"].values()
        
        ib_high_18 = seven_hour_candle_6pm["ib_high"]
        ib_low_18 = seven_hour_candle_6pm["ib_low"]
        ib_ce_18 = seven_hour_candle_6pm["ib_ce"]
        ib_high_1 = seven_hour_candle_1am["ib_high"]
        ib_low_1 = seven_hour_candle_1am["ib_low"]
        ib_ce_1 = seven_hour_candle_1am["ib_ce"]

        # london killzone shorts
        if look_for_shorts:
            
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
        elif look_for_longs:
            
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
        #  get 1am and 8am seven hour candles
        seven_hour_candle_8am = seven_hour_builder_candles["8AM"].values()
        seven_hour_candle_1am = seven_hour_builder_candles["1AM"].values()
        
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
            
    elif window_name is "7h_wick_0800":
        allow_shorts = True
        allow_longs = True
        print("overnight expansion: ", market_context.overnight_expansion, "exhaustion: ", market_context.exhaustion, "bias: ", market_context.bias )
        if (market_context.overnight_expansion or market_context.exhaustion):
            if market_context.session_direction == "bearish":
                print("overnight bearish expansion or exhausion. not allowing shorts")
                allow_shorts = False
            elif market_context.session_direction == "bullish":
                print("overnight bullish expansion or exhausion. not allowing shorts")
                allow_longs = False
        else:
            if market_context.session_direction == "bullish" and look_for_shorts and not is_smt:
                print("no bullish exhausion and no bearish smt. not allowing shorts ")
                allow_shorts = False
            elif market_context.session_direction == "bearish" and look_for_longs and not is_smt:
                print("no bearish exhausion and no bullish smt. not allowing longs ")
                allow_longs = False
            
        # elif (market_context.overnight_expansion or market_context.exhaustion) and market_context.session_direction == "bullish":
        #     allow_longs = False
        print("allow_shorts: ", allow_shorts, "allow_longs: ", allow_longs)
        # allow reversal with reversal_confirmation as true
        
        if look_for_longs and allow_longs:
            reversal_confirmation = True
        if look_for_shorts and allow_shorts:
            reversal_confirmation = True
        return reversal_confirmation
    else:
        return True




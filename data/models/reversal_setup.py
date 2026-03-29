from data.models.displacement import is_displacement_candle
from helpers.ib_helpers import check_ib_rejection
from helpers.sessions import in_session


def check_for_reversal_setup_confirmation(prev_seven_hour_candle, current_seven_hour_candle, liquidity_levels_nq, liquidity_levels_es, candidate, last_closed_candle, current_30m_start, daily_atr, smt_summary):
    # get session time
    # bias from previous 7hr candle (ex: bearish)
    # price is below (bearish) previous 7hr candle and (or) rejecting previous 7hr ib
    # price should be below or rejecting current 7hr ib
    # if price is above current 7hr ib and rejecting previous 7hr ib = Manipulation of current 7hr

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

    reversal_confirmation = False
    is_reversal_candidate = False
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
    is_london_killzone = in_session(current_30m_start, 3, 0, 5,0)
    print("----------------------------------------")
    print("is_london_killzone: ", is_london_killzone)
    # print("smt summary: ", smt_summary)
    
    bias = prev_seven_hour_candle["bias"]
    ib_high_18 = prev_seven_hour_candle["ib_high"]
    ib_low_18 = prev_seven_hour_candle["ib_low"]
    ib_ce_18 = prev_seven_hour_candle["ib_ce"]
    ib_high_1 = current_seven_hour_candle["ib_high"]
    ib_low_1 = current_seven_hour_candle["ib_low"]
    ib_ce_1 = current_seven_hour_candle["ib_ce"]

    look_for_shorts = False
    look_for_longs = False
    if candidate.side == "buy_side":
        look_for_shorts = True
    elif candidate.side == "sell_side":
        look_for_longs = True
    is_smt = False
    if look_for_shorts:
        if smt_summary["bearish_smt_1h"] is not None or smt_summary["bearish_smt_30m_swing"] is not None:
            is_smt = True
    elif look_for_longs:
        if smt_summary["bullish_smt_1h"] is not None or smt_summary["bullish_smt_30m_swing"] is not None:
            is_smt = True

    
    # london killzone shorts
    if is_london_killzone and look_for_shorts:
        
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
        # bearish confirmation
        if is_ib_rejection_18 and is_ib_rejection_1:
            reversal_confirmation = True
            print("step1")
        # manipulation
        elif is_ib_rejection_18 and is_above_ib_1:
            reversal_confirmation = False
            is_reversal_candidate = True
            print("step2: reversal candidate")
        elif is_ib_rejection_18 and is_below_ib_1:
            reversal_confirmation = True
            print("step3")
        # bearish confirmation
        elif is_ib_rejection_1 and is_below_ib_18:
            reversal_confirmation = True
            print("step4")
        # 
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
    elif is_london_killzone and look_for_longs:
        
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
        
        # bullish confirmation
        if is_ib_rejection_18 and is_ib_rejection_1:
            reversal_confirmation = True
            print("step1")
        # manipulation
        elif is_ib_rejection_18 and is_below_ib_1:
            reversal_confirmation = False
            is_reversal_candidate = True
            print("step2: reversal candidate")
        elif is_ib_rejection_18 and is_above_ib_1:
            reversal_confirmation = True
            print("step3")
        # bearish confirmation
        elif is_ib_rejection_1 and is_above_ib_18:
            reversal_confirmation = True
            print("step4")

        # 
        elif is_ib_rejection_1 and is_below_ib_18:
            reversal_confirmation = False
            is_reversal_candidate = True
            print("step5: reversal candidate")
        else:
            reversal_confirmation = False
            print("step6: no IB rules met")
        if asia_swept and reversal_confirmation:
            print("Ib reversal confirmation: ", reversal_confirmation)
            print("asia high swept, allowing trade")
            reversal_confirmation = True
        else:
            reversal_confirmation = False
            print("asia high not swept, not allowing trade")
            print("Ib reversal confirmation: ", reversal_confirmation)
    # allow trade temporarity. implement other killzones and rules later.
    # elif is_displacement:
    #     print("outside london Killzone, but displacement candle detected, allowing trade")
    #     reversal_confirmation = True
    # else:
    #     print("outside london Killzone, no displacement, rejecting trade")
    #     reversal_confirmation = False
    print("smt, reversal confirmation, candidate: ", is_smt, reversal_confirmation, is_reversal_candidate)
    # return reversal_confirmation or is_reversal_candidate
    return reversal_confirmation
    # return True




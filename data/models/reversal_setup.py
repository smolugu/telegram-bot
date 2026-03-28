from helpers.ib_helpers import check_ib_rejection
from helpers.sessions import in_session


def check_for_reversal_setup_confirmation(prev_seven_hour_candle, current_seven_hour_candle, liquidity_es, candidate, last_closed_candle, current_30m_start):
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
        if last_closed_candle["low"] < ib_high:
            return True
        return False

    reversal_confirmation = False
    # check session

    

    bias = prev_seven_hour_candle.bias
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
    
    # identify session
    is_london_killzone = in_session(current_30m_start, 3, 0, 5,0)
    
    # london killzone shorts
    if is_london_killzone and look_for_shorts:
        is_scenario_1 = False
        is_scenario_2 = False
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

        # bearish confirmation
        if is_ib_rejection_18 and is_ib_rejection_1:
            reversal_confirmation = True
        # manipulation
        elif is_ib_rejection_18 and is_above_ib_1:
            reversal_confirmation = False
        # bearish confirmation
        elif is_ib_rejection_1 and is_below_ib_18:
            reversal_confirmation = True
        # 
        elif is_ib_rejection_1 and is_above_ib_18:
            reversal_confirmation = False
        else:
            reversal_confirmation = False
        
        




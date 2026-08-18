from datetime import datetime

from helpers.sessions import get_session_high_low

def update_compression_range_levels(liquidity_levels, compression_range, session):
    
    if session == "1AM" and liquidity_levels["cr1am_high"]["price"] is None:
        liquidity_levels["cr1am_high"]["price"] = compression_range["high"]
        liquidity_levels["cr1am_low"]["price"] = compression_range["low"]
        print("cr1am_high: ", liquidity_levels["cr1am_high"]["price"]) 
    elif session == "8AM" and liquidity_levels["cr8am_high"]["price"] is None:
        liquidity_levels["cr8am_high"]["price"] = compression_range["high"]
        liquidity_levels["cr8am_low"]["price"] = compression_range["low"]

def add_ob_mitigation_level(liquidity_levels, ob_level, session, side):
    if side == "sell_side" and session == "8AM":
        liquidity_levels["ob8_mtl_low"]["price"] = ob_level
    if side == "buy_side" and session == "8AM":
        liquidity_levels["ob8_mtl_high"]["price"] = ob_level
    if side == "sell_side" and session == "1AM":
        liquidity_levels["ob1_mtl_low"]["price"] = ob_level
    if side == "buy_side" and session == "1AM":
        liquidity_levels["ob1_mtl_high"]["price"] = ob_level


def add_mitigation_level(liquidity_levels, mtl_level, session, side):
    
    if session == "1AM" and liquidity_levels["mr1am_mtl_low"]["price"] is None and side == "sell_side":
        liquidity_levels["mr1am_mtl_low"]["price"] = mtl_level
    elif session == "1AM" and liquidity_levels["mr1am_mtl_high"]["price"] is None and side == "buy_side":
        liquidity_levels["mr1am_mtl_high"]["price"] = mtl_level
    elif session == "8AM" and liquidity_levels["mr8am_mtl_low"]["price"] is None and side == "sell_side":
        liquidity_levels["mr8am_mtl_low"]["price"] = mtl_level
    elif session == "8AM" and liquidity_levels["mr8am_mtl_high"]["price"] is None and side == "buy_side":
        liquidity_levels["mr8am_mtl_high"]["price"] = mtl_level

def add_ib_ce_level(liquidity_levels, mtl_level, session, side):
    
    if session == "1AM" and liquidity_levels["ib_ce_1am_low"]["price"] is None and side == "sell_side":
        liquidity_levels["ib_ce_1am_low"]["price"] = mtl_level
    elif session == "1AM" and liquidity_levels["ib_ce_1am_high"]["price"] is None and side == "buy_side":
        liquidity_levels["ib_ce_1am_high"]["price"] = mtl_level
    elif session == "8AM" and liquidity_levels["ib_ce_8am_low"]["price"] is None and side == "sell_side":
        liquidity_levels["ib_ce_8am_low"]["price"] = mtl_level
    elif session == "8AM" and liquidity_levels["ib_ce_8am_high"]["price"] is None and side == "buy_side":
        liquidity_levels["ib_ce_8am_high"]["price"] = mtl_level


def add_8am_ob_mitigation_levels(liquidity_levels, bullish_ob_level, bearish_ob_level):
    if bullish_ob_level is not None:
        add_ob_mitigation_level(liquidity_levels, bullish_ob_level, "8AM", "sell_side")
    if bearish_ob_level is not None:
        add_ob_mitigation_level(liquidity_levels, bearish_ob_level, "8AM", "buy_side")

def add_1am_ob_mitigation_levels(liquidity_levels, bullish_ob_level, bearish_ob_level):
    if bullish_ob_level is not None:
        add_ob_mitigation_level(liquidity_levels, bullish_ob_level, "1AM", "sell_side")
    if bearish_ob_level is not None:
        add_ob_mitigation_level(liquidity_levels, bearish_ob_level, "1AM", "buy_side")


# add ib ce as mitigation key level
def add_ib_ce_key_level(structure_data, liquidity_levels):
    # strong 8am Ib and migration structure
    market_phase = structure_data.structure["market_phase"]
    structure_name = structure_data.structure["name"]
    ib_ce_level = structure_data.ib_8["ce"]
    is_strong_body = structure_data.structure["is_ib_strong_body"]
    print("add ib ce: is strong body: ", is_strong_body)
    if market_phase == "migration" and is_strong_body:
        print("adding ib ce level")
        if "bullish" in structure_name:
            add_ib_ce_level(liquidity_levels, ib_ce_level, "8AM", "sell_side")
        elif "bearish" in structure_name:
            add_ib_ce_level(liquidity_levels, ib_ce_level, "8AM", "buy_side")
        

# def add_post_8am_mitigation_levels(structure_data, liquidity_levels, bullish_mtl_level, bearish_mtl_level):
def add_post_8am_mitigation_levels(structure_data, liquidity_levels):
    structure_name = structure_data.structure["name"]
    mitigation_level = structure_data.structure["mitigation_level"]

    # here we are adding new mitigation levels based on structure specifically for migration structures
    # no need for structure name check
    
    # if structure_name == "staircase_late_overlap_bullish":
    #     add_mitigation_level(liquidity_levels, mitigation_level, "8AM", "sell_side")
    # elif structure_name == "staircase_late_overlap_bearish":
    #     add_mitigation_level(liquidity_levels, mitigation_level, "8AM", "buy_side")
    if "bullish" in structure_name and not structure_name == "bullish_value_flip":
        add_mitigation_level(liquidity_levels, mitigation_level, "8AM", "sell_side")
    elif "bearish" in structure_name and not structure_name == "bearish_value_flip":
        add_mitigation_level(liquidity_levels, mitigation_level, "8AM", "buy_side")
        
    if structure_name == "bullish_value_flip" and mitigation_level is not None:
        add_mitigation_level(liquidity_levels, mitigation_level, "8AM", "buy_side")
    elif structure_name == "bearish_value_flip" and mitigation_level is not None:
        add_mitigation_level(liquidity_levels, mitigation_level, "8AM", "sell_side")
    

def refresh_liquidity(liquidity_levels, prev_levels):
    carry_forward = {
        "asia_high", "asia_low",
        "london_high", "london_low",
        "ny_am_high", "ny_am_low",
        "ny_lunch_high", "ny_lunch_low",
        "ny_pm_high", "ny_pm_low",
    }
    for key, level in prev_levels.items():
        if key in carry_forward and not level["swept"]:
            liquidity_levels[key] = level
    return liquidity_levels


def reset_liquidity():

    return {
        "pdh": {"name": "pdh", "price": None, "side": "buy_side", "swept": False, "timestamp": None},
        "pdl": {"name": "pdl","price": None, "side": "sell_side", "swept": False, "timestamp": None},

        "cr1am_high": {"name": "cr1am_high", "price": None, "side": "buy_side", "swept": False, "timestamp": None},
        "cr1am_low": {"name": "cr1am_low", "price": None, "side": "sell_side", "swept": False, "timestamp": None},

        "cr8am_high": {"name": "cr8am_high", "price": None, "side": "buy_side", "swept": False, "timestamp": None},
        "cr8am_low": {"name": "cr8am_low", "price": None, "side": "sell_side", "swept": False, "timestamp": None},

        "mr1am_mtl_high": {"name": "mr1am_mtl_high", "price": None, "side": "buy_side", "swept": False, "timestamp": None},
        "mr1am_mtl_low": {"name": "mr1am_mtl_low", "price": None, "side": "sell_side", "swept": False, "timestamp": None},

        "mr8am_mtl_high": {"name": "mr8am_mtl_high", "price": None, "side": "buy_side", "swept": False, "timestamp": None},
        "mr8am_mtl_low": {"name": "mr8am_mtl_low", "price": None, "side": "sell_side", "swept": False, "timestamp": None},

        "ib_ce_8am_high": {"name": "ib_ce_8am_high", "price": None, "side": "buy_side", "swept": False, "timestamp": None},
        "ib_ce_8am_low": {"name": "ib_ce_8am_low", "price": None, "side": "sell_side", "swept": False, "timestamp": None},

        "ib_ce_1am_high": {"name": "ib_ce_1am_high", "price": None, "side": "buy_side", "swept": False, "timestamp": None},
        "ib_ce_1am_low": {"name": "ib_ce_1am_low", "price": None, "side": "sell_side", "swept": False, "timestamp": None},

        "ob8_mtl_high": {"name": "ob8_mtl_high", "price": None, "side": "buy_side", "swept": False, "timestamp": None},
        "ob8_mtl_low": {"name": "ob8_mtl_low", "price": None, "side": "sell_side", "swept": False, "timestamp": None},

        "ob1_mtl_high": {"name": "ob1_mtl_high", "price": None, "side": "buy_side", "swept": False, "timestamp": None},
        "ob1_mtl_low": {"name": "ob1_mtl_low", "price": None, "side": "sell_side", "swept": False, "timestamp": None},

        "asia_high": {"name": "asia_high","price": None, "side": "buy_side", "swept": False, "timestamp": None},
        "asia_low": {"name": "asia_low","price": None, "side": "sell_side", "swept": False, "timestamp": None},

        "london_high": {"name": "london_high","price": None, "side": "buy_side", "swept": False, "timestamp": None},
        "london_low": {"name": "london_low","price": None, "side": "sell_side", "swept": False, "timestamp": None},

        "ny_am_high": {"name": "ny_am_high","price": None, "side": "buy_side", "swept": False, "timestamp": None},
        "ny_am_low": {"name": "ny_am_low","price": None, "side": "sell_side", "swept": False, "timestamp": None},

        "ny_lunch_high": {"name": "ny_lunch_high","price": None, "side": "buy_side", "swept": False, "timestamp": None},
        "ny_lunch_low": {"name": "ny_lunch_low","price": None, "side": "sell_side", "swept": False, "timestamp": None},

        "ny_pm_high": {"name": "ny_pm_high", "price": None, "side": "buy_side", "swept": False, "timestamp": None},
        "ny_pm_low": {"name": "ny_pm_low", "price": None, "side": "sell_side", "swept": False, "timestamp": None},

        "ib_high": {"name": "ib_high", "price": None, "side": "buy_side", "swept": False, "timestamp": None},
        "ib_low": {"name": "ib_low", "price": None, "side": "sell_side", "swept": False, "timestamp": None}
    }

def get_liquidity_values(symbol, candles_30m, test_date, liquidity_levels, current_start, pdh, pdl):
    
    liquidity_levels["pdh"]["price"] = pdh
    liquidity_levels["pdl"]["price"] = pdl
    asia_levels = get_session_high_low(candles_30m, 20, 0, 0, 0, current_start, "Asia")
    if asia_levels["high"] is not None and liquidity_levels["asia_high"]["price"] != asia_levels["high"]:
        print("updating asia high at :", current_start)
        liquidity_levels["asia_high"]["price"] = asia_levels["high"]
        liquidity_levels["asia_high"]["swept"] = False
        liquidity_levels["asia_low"]["price"] = asia_levels["low"]
        liquidity_levels["asia_low"]["swept"] = False
        liquidity_levels["asia_low"]["timestamp"] = asia_levels["low_ts"]
        liquidity_levels["asia_high"]["timestamp"] = asia_levels["high_ts"]
    
    london_levels = get_session_high_low(candles_30m, 2, 0, 5, 0, current_start)
    if london_levels["high"] is not None and liquidity_levels["london_high"]["price"] != london_levels["high"]:
        liquidity_levels["london_high"]["price"] = london_levels["high"]
        liquidity_levels["london_low"]["price"] = london_levels["low"]
        liquidity_levels["london_low"]["swept"] = False
        liquidity_levels["london_high"]["swept"] = False
        liquidity_levels["london_high"]["timestamp"] = london_levels["high_ts"]
        liquidity_levels["london_low"]["timestamp"] = london_levels["low_ts"]

    ny_am_levels = get_session_high_low(candles_30m, 9, 30, 11, 0, current_start)
    if ny_am_levels["high"] is not None and liquidity_levels["ny_am_high"]["price"] != ny_am_levels["high"]:
        liquidity_levels["ny_am_high"]["price"] = ny_am_levels["high"]
        liquidity_levels["ny_am_low"]["price"] = ny_am_levels["low"]
        liquidity_levels["ny_am_low"]["swept"] = False
        liquidity_levels["ny_am_high"]["swept"] = False
        liquidity_levels["ny_am_high"]["timestamp"] = ny_am_levels["high_ts"]
        liquidity_levels["ny_am_low"]["timestamp"] = ny_am_levels["low_ts"]

    ny_lunch_levels = get_session_high_low(candles_30m, 12, 0, 13, 0, current_start)
    if ny_lunch_levels["high"] is not None and liquidity_levels["ny_lunch_high"]["price"] != ny_lunch_levels["high"]:
        liquidity_levels["ny_lunch_high"]["price"] = ny_lunch_levels["high"]
        liquidity_levels["ny_lunch_low"]["price"] = ny_lunch_levels["low"]
        liquidity_levels["ny_lunch_low"]["swept"] = False
        liquidity_levels["ny_lunch_high"]["swept"] = False
        liquidity_levels["ny_lunch_high"]["timestamp"] = ny_lunch_levels["high_ts"]
        liquidity_levels["ny_lunch_low"]["timestamp"] = ny_lunch_levels["low_ts"]
    ny_pm_levels = get_session_high_low(candles_30m, 13, 30, 16, 0, current_start)
    if ny_pm_levels["high"] is not None and liquidity_levels["ny_pm_high"]["price"] != ny_pm_levels["high"]:
        liquidity_levels["ny_pm_high"]["price"] = ny_pm_levels["high"]
        liquidity_levels["ny_pm_low"]["price"] = ny_pm_levels["low"]
        liquidity_levels["ny_pm_high"]["swept"] = False
        liquidity_levels["ny_pm_low"]["swept"] = False
        liquidity_levels["ny_pm_high"]["timestamp"] = ny_pm_levels["high_ts"]
        liquidity_levels["ny_pm_low"]["timestamp"] = ny_pm_levels["low_ts"]
    # or_high, or_low = session_high_low(candles_30m, 9.5, 10.5, candles_30m[-1]["timestamp"])
    # liquidity_levels["or_high"]["price"] = or_high
    # liquidity_levels["or_low"]["price"] = or_low
    ib_levels = get_session_high_low(candles_30m, 8, 0, 9, 0, current_start)
    if ib_levels["high"] is not None and liquidity_levels["ib_high"]["price"] != ib_levels["high"]:
        liquidity_levels["ib_high"]["price"] = ib_levels["high"]
        liquidity_levels["ib_low"]["price"] = ib_levels["low"]
        
        liquidity_levels["ib_high"]["timestamp"] = ib_levels["high_ts"]
        liquidity_levels["ib_low"]["timestamp"] = ib_levels["low_ts"]
    return liquidity_levels


def detect_stacked_liquidity_fast(liquidity, tolerance):

    # collect active levels
    levels = [
        {
            "type": k,
            "price": v["price"],
            "side": v["side"]
        }
        for k, v in liquidity.items()
        if v["price"] is not None and not v["swept"]
    ]

    # sort by price
    levels.sort(key=lambda x: x["price"])

    stacks = []
    current_stack = [levels[0]] if levels else []

    for i in range(1, len(levels)):

        prev = current_stack[-1]
        curr = levels[i]

        # must be same side and within tolerance
        if (
            curr["side"] == prev["side"]
            and abs(curr["price"] - prev["price"]) <= tolerance
        ):
            current_stack.append(curr)

        else:

            if len(current_stack) >= 2:
                stacks.append(current_stack)

            current_stack = [curr]

    # check final stack
    if len(current_stack) >= 2:
        stacks.append(current_stack)

    return stacks
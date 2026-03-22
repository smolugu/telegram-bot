from datetime import datetime

from helpers.sessions import get_session_high_low


def reset_liquidity():

    return {
        "pdh": {"name": "pdh", "price": None, "side": "buy_side", "swept": False, "timestamp": None},
        "pdl": {"name": "pdl","price": None, "side": "sell_side", "swept": False, "timestamp": None},

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
    liquidity_levels["asia_high"]["price"] = asia_levels["high"]
    liquidity_levels["asia_low"]["price"] = asia_levels["low"]
    liquidity_levels["asia_low"]["timestamp"] = asia_levels["low_ts"]
    liquidity_levels["asia_high"]["timestamp"] = asia_levels["high_ts"]

    london_levels = get_session_high_low(candles_30m, 2, 0, 5, 0, current_start)
    liquidity_levels["london_high"]["price"] = london_levels["high"]
    liquidity_levels["london_low"]["price"] = london_levels["low"]
    liquidity_levels["london_high"]["timestamp"] = london_levels["high_ts"]
    liquidity_levels["london_low"]["timestamp"] = london_levels["low_ts"]

    ny_am_levels = get_session_high_low(candles_30m, 9, 30, 11, 0, current_start)
    liquidity_levels["ny_am_high"]["price"] = ny_am_levels["high"]
    liquidity_levels["ny_am_low"]["price"] = ny_am_levels["low"]
    liquidity_levels["ny_am_high"]["timestamp"] = ny_am_levels["high_ts"]
    liquidity_levels["ny_am_low"]["timestamp"] = ny_am_levels["low_ts"]

    ny_lunch_levels = get_session_high_low(candles_30m, 12, 0, 13, 0, current_start)
    liquidity_levels["ny_lunch_high"]["price"] = ny_lunch_levels["high"]
    liquidity_levels["ny_lunch_low"]["price"] = ny_lunch_levels["low"]
    liquidity_levels["ny_lunch_high"]["timestamp"] = ny_lunch_levels["high_ts"]
    liquidity_levels["ny_lunch_low"]["timestamp"] = ny_lunch_levels["low_ts"]
    ny_pm_levels = get_session_high_low(candles_30m, 13, 30, 16, 0, current_start)
    liquidity_levels["ny_pm_high"]["price"] = ny_pm_levels["high"]
    liquidity_levels["ny_pm_low"]["price"] = ny_pm_levels["low"]
    liquidity_levels["ny_pm_high"]["timestamp"] = ny_pm_levels["high_ts"]
    liquidity_levels["ny_pm_low"]["timestamp"] = ny_pm_levels["low_ts"]
    # or_high, or_low = session_high_low(candles_30m, 9.5, 10.5, candles_30m[-1]["timestamp"])
    # liquidity_levels["or_high"]["price"] = or_high
    # liquidity_levels["or_low"]["price"] = or_low
    ib_levels = get_session_high_low(candles_30m, 8, 0, 9, 0, current_start)
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
from datetime import datetime

from helpers.sessions import get_session_high_low


def reset_liquidity():

    return {
        "pdh": {"price": None, "side": "buy_side", "swept": False},
        "pdl": {"price": None, "side": "sell_side", "swept": False},

        "asia_high": {"price": None, "side": "buy_side", "swept": False},
        "asia_low": {"price": None, "side": "sell_side", "swept": False},

        "london_high": {"price": None, "side": "buy_side", "swept": False},
        "london_low": {"price": None, "side": "sell_side", "swept": False},

        "ny_am_high": {"price": None, "side": "buy_side", "swept": False},
        "ny_am_low": {"price": None, "side": "sell_side", "swept": False},

        "ny_lunch_high": {"price": None, "side": "buy_side", "swept": False},
        "ny_lunch_low": {"price": None, "side": "sell_side", "swept": False},

        "ny_pm_high": {"price": None, "side": "buy_side", "swept": False},
        "ny_pm_low": {"price": None, "side": "sell_side", "swept": False},

        "ib_high": {"price": None, "side": "buy_side", "swept": False},
        "ib_low": {"price": None, "side": "sell_side", "swept": False}
    }

def get_liquidity_values(symbol, candles_30m, test_date, liquidity_levels, current_start):
    
    # pdh, pdl = get_pdh_pdl_fixed_date(test_date, symbol)
    # liquidity_levels["pdh"]["price"] = pdh
    # liquidity_levels["pdl"]["price"] = pdl
    # print("current_start: ", current_start)
    # print("last candle ts: ", candles_30m[-1]["timestamp"])

    # asia_high, asia_low = session_high_low(candles_30m, 20, 24, candles_30m[-1]["timestamp"])
    asia_high, asia_low = get_session_high_low(candles_30m, 20,0, 0,0, candles_30m[-1]["timestamp"], "Asia")
    liquidity_levels["asia_high"]["price"] = asia_high
    liquidity_levels["asia_low"]["price"] = asia_low
    london_high, london_low = get_session_high_low(candles_30m, 2,0, 5,0, candles_30m[-1]["timestamp"])
    liquidity_levels["london_high"]["price"] = london_high
    liquidity_levels["london_low"]["price"] = london_low
    ny_am_high, ny_am_low = get_session_high_low(candles_30m, 9,30,11,0, candles_30m[-1]["timestamp"])
    liquidity_levels["ny_am_high"]["price"] = ny_am_high
    liquidity_levels["ny_am_low"]["price"] = ny_am_low
    ny_lunch_high, ny_lunch_low = get_session_high_low(candles_30m, 12,0, 13,0, candles_30m[-1]["timestamp"])
    liquidity_levels["ny_lunch_high"]["price"] = ny_lunch_high
    liquidity_levels["ny_lunch_low"]["price"] = ny_lunch_low
    ny_pm_high, ny_pm_low = get_session_high_low(candles_30m, 13, 30, 16,0, candles_30m[-1]["timestamp"])
    liquidity_levels["ny_pm_high"]["price"] = ny_pm_high
    liquidity_levels["ny_pm_low"]["price"] = ny_pm_low
    # or_high, or_low = session_high_low(candles_30m, 9.5, 10.5, candles_30m[-1]["timestamp"])
    # liquidity_levels["or_high"]["price"] = or_high
    # liquidity_levels["or_low"]["price"] = or_low
    ib_high, ib_low = get_session_high_low(candles_30m, 8,0, 9,0, candles_30m[-1]["timestamp"])
    liquidity_levels["ib_high"]["price"] = ib_high
    liquidity_levels["ib_low"]["price"] = ib_low
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
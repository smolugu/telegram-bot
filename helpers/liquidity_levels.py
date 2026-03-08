from datetime import datetime

from data.market_data import get_pdh_pdl_fixed_date, session_high_low

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

        "or_high": {"price": None, "side": "buy_side", "swept": False},
        "or_low": {"price": None, "side": "sell_side", "swept": False}
    }

def get_liquidity_values(symbol, candles_30m, test_date):
    liquidity_levels = {}
    pdh, pdl = get_pdh_pdl_fixed_date(test_date, symbol)
    liquidity_levels["pdh"] = {"price": pdh, "swept": False}
    liquidity_levels["pdl"] = {"price": pdl, "swept": False}

    asia_high, asia_low = session_high_low(candles_30m, 20, 24, candles_30m[-1]["timestamp"])
    liquidity_levels["asia_high"] = {"price": asia_high, "swept": False}
    liquidity_levels["asia_low"] = {"price": asia_low, "swept": False}
    london_high, london_low = session_high_low(candles_30m, 2, 5, candles_30m[-1]["timestamp"])
    liquidity_levels["london_high"] = {"price": london_high, "swept": False}
    liquidity_levels["london_low"] = {"price": london_low, "swept": False}
    ny_am_high, ny_am_low = session_high_low(candles_30m, 9.5, 11, candles_30m[-1]["timestamp"])
    liquidity_levels["ny_am_high"] = {"price": ny_am_high, "swept": False}
    liquidity_levels["ny_am_low"] = {"price": ny_am_low, "swept": False}
    ny_lunch_high, ny_lunch_low = session_high_low(candles_30m, 12, 13, candles_30m[-1]["timestamp"])
    liquidity_levels["ny_lunch_high"] = {"price": ny_lunch_high, "swept": False}
    liquidity_levels["ny_lunch_low"] = {"price": ny_lunch_low, "swept": False}
    ny_pm_high, ny_pm_low = session_high_low(candles_30m, 13.5, 16, candles_30m[-1]["timestamp"])
    liquidity_levels["ny_pm_high"] = {"price": ny_pm_high, "swept": False}
    liquidity_levels["ny_pm_low"] = {"price": ny_pm_low, "swept": False}
    or_high, or_low = session_high_low(candles_30m, 9.5, 10.5, candles_30m[-1]["timestamp"])
    liquidity_levels["or_high"] = {"price": or_high, "swept": False}
    liquidity_levels["or_low"] = {"price": or_low, "swept": False}

    return liquidity_levels
# from datetime import datetime
from datetime import datetime, timedelta

from helpers.swing_points import filter_valid_swing_lows, filter_valid_swing_highs, find_swing_highs, find_swing_lows
from helpers.time_windows import (
    get_reversal_windows,
    is_in_reversal_window
)
def find_sweep_time_3m(inside_3m, swing_level, direction, tolerance=0.25):

    for c in inside_3m:
        h = c["high"]
        l = c["low"]

        if direction == "buy_side":
            # Upward sweep / buy-side liquidity grab
            if h >= swing_level - tolerance:           # using tolerance
                return c["timestamp"]
        
        else:  # "sell_side"
            # Downward sweep / sell-side liquidity grab
            if l <= swing_level + tolerance:
                return c["timestamp"]

    return None

# -------------------------------------------------------
# Session-based liquidity levels
# -------------------------------------------------------
def detect_key_liquidity_sweep(last_candle, liquidity, tolerance=0):

    sweep_at_key_level = False
    swept_levels = []

    high = last_candle["high"]
    low = last_candle["low"]
    close = last_candle["close"]
    

    for level_type, level_data in liquidity.items():

        price = level_data["price"]
        swept = level_data["swept"]

        if price is None or swept:
            continue

        # Buy-side liquidity (price above level)
        if level_type.endswith("high") or level_type == "pdh":
            # Check if high touches or exceeds the level (potential sweep) and set swept to True
            # if high >= price - tolerance:
            # --------------------------------
            # IMPORTANT: updated high >= price to high > price, as the same candle forming the low or high
            # of the session can trigger sweep as the session high/ low == candle high/ low
            # remove equality for sweep across this function
            # --------------------------------
            if high > price:
                liquidity[level_type]["swept"] = True
            # check for valid sweep (rejection off level)
            # if high >= price - tolerance and close < price:
            if high > price and close < price:

                sweep_at_key_level = True
                liquidity[level_type]["swept"] = True

                swept_levels.append({
                    "level_name": level_type,
                    "price": price,
                    "side": "buy_side",
                    "type": "rejection"
                })
            # elif high >= price - tolerance and close >= price:
            elif high > price and close > price:
                # potential sweep but no rejection, still mark as swept
                liquidity[level_type]["swept"] = True
                swept_levels.append({
                    "level_name": level_type,
                    "price": price,
                    "side": "buy_side",
                    "type": "breakout"
                })


        # Sell-side liquidity (price below level)
        elif level_type.endswith("low") or level_type == "pdl":
            # Check if low touches or goes below the level (potential sweep) and set swept to True
            # if low <= price + tolerance:
            if low < price:
                liquidity[level_type]["swept"] = True
            #  check for valid sweep (rejection off level)
            # if low <= price + tolerance and close > price:
            if low < price and close > price:

                sweep_at_key_level = True
                liquidity[level_type]["swept"] = True

                swept_levels.append({
                    "level_name": level_type,
                    "price": price,
                    "side": "sell_side",
                    "type": "rejection"
                })
            # elif low <= price + tolerance and close <= price:
            elif low < price and close < price:
                # potential sweep but no rejection, still mark as swept
                liquidity[level_type]["swept"] = True
                swept_levels.append({
                    "level_name": level_type,
                    "price": price,
                    "side": "sell_side",
                    "type": "breakout"
                })

    return sweep_at_key_level, swept_levels

def detect_key_liquidity_sweep_highs(last_candle, liquidity, tolerance=0):

    sweep_at_key_level = False
    swept_levels = []
    sweep_type = None

    high = last_candle["high"]
    # low = last_candle["low"]
    close = last_candle["close"]
    

    for level_type, level_data in liquidity.items():

        price = level_data["price"]
        swept = level_data["swept"]

        if price is None or swept:
            continue

        # Buy-side liquidity (price above level)
        if level_type.endswith("high") or level_type == "pdh":
        # if level_type == "pdh":
            # Check if high touches or exceeds the level (potential sweep) and set swept to True
            # if high >= price - tolerance:
            # --------------------------------
            # IMPORTANT: updated high >= price to high > price, as the same candle forming the low or high
            # of the session can trigger sweep as the session high/ low == candle high/ low
            # remove equality for sweep across this function
            # --------------------------------
            if high > price:
                liquidity[level_type]["swept"] = True
            # check for valid sweep (rejection off level)
            # if high >= price - tolerance and close < price:
            if high > price and close <= price:

                sweep_at_key_level = True
                liquidity[level_type]["swept"] = True
                sweep_type = "rejection"

                swept_levels.append({
                    "level_name": level_type,
                    "price": price,
                    "side": "buy_side",
                    "type": "rejection"
                })
            # elif high >= price - tolerance and close >= price:
            elif high > price and close > price:
                # potential sweep but no rejection, still mark as swept
                liquidity[level_type]["swept"] = True
                sweep_type = "breakout"
                swept_levels.append({
                    "level_name": level_type,
                    "price": price,
                    "side": "buy_side",
                    "type": "breakout"
                })

    return sweep_at_key_level, swept_levels, sweep_type

def detect_key_liquidity_sweep_lows(last_candle, liquidity, tolerance=0):

    sweep_at_key_level = False
    swept_levels = []
    sweep_type = None

    # high = last_candle["high"]
    low = last_candle["low"]
    close = last_candle["close"]
    

    for level_type, level_data in liquidity.items():

        price = level_data["price"]
        swept = level_data["swept"]

        if price is None or swept:
            continue

        # Sell-side liquidity (price below level)
        if level_type.endswith("low") or level_type == "pdl":
        # if level_type == "pdl":
            # Check if low touches or goes below the level (potential sweep) and set swept to True
            # if low <= price + tolerance:
            if low < price:
                liquidity[level_type]["swept"] = True
            #  check for valid sweep (rejection off level)
            # if low <= price + tolerance and close > price:
            if low < price and close >= price:

                sweep_at_key_level = True
                liquidity[level_type]["swept"] = True
                sweep_type = "rejection"

                swept_levels.append({
                    "level_name": level_type,
                    "price": price,
                    "side": "sell_side",
                    "type": "rejection"
                })
            # elif low <= price + tolerance and close <= price:
            elif low < price and close < price:
                # potential sweep but no rejection, still mark as swept
                liquidity[level_type]["swept"] = True
                sweep_type = "breakout"
                swept_levels.append({
                    "level_name": level_type,
                    "price": price,
                    "side": "sell_side",
                    "type": "breakout"
                })

    return sweep_at_key_level, swept_levels, sweep_type




def detect_key_liquidity_sweep(instrument, key_levels, candles_3m, last_closed_candle, current_30m_start):
    sweep_highs_key_levels_info = None
    sweep_lows_key_levels_info = None
    
    sweep_candle_start = last_closed_candle["timestamp"]
    sweep_candle_end = (
        datetime.fromisoformat(sweep_candle_start)
        + timedelta(minutes=30)
    ).isoformat()
    
    sweep_highs, swept_levels_high, sweep_type = detect_key_liquidity_sweep_highs(last_closed_candle, key_levels)
    sweep_lows, swept_levels_low, sweep_type = detect_key_liquidity_sweep_lows(last_closed_candle, key_levels)
    inside_3m_candles = [c for c in candles_3m if c["timestamp"] >= sweep_candle_start and c["timestamp"] < sweep_candle_end]
    
    
    if sweep_lows:
        sweep_time_low = find_sweep_time_3m(inside_3m_candles, last_closed_candle["low"], "sell_side")
        nq_sweep_and_ob_entry = None
        nq_sweep_and_ob_ce_entry = None
        nq_sweep_and_ob_confirmed = False
        nq_sweep_and_ob_ce_confirmed = False
        nq_sweep_and_ob_confirmation_timestamp = None
        
        nq_sweep_and_ob_confirmed = last_closed_candle["close"] > last_closed_candle["open"] - 3
        
        if nq_sweep_and_ob_confirmed:
            nq_sweep_and_ob_entry = last_closed_candle["open"]
            nq_sweep_and_ob_confirmation_timestamp = last_closed_candle["timestamp"]
        if last_closed_candle["close"] > last_closed_candle["open"] and last_closed_candle["close"] - last_closed_candle["open"] > 60:
            nq_sweep_and_ob_ce_entry = (last_closed_candle["open"] + last_closed_candle["close"]) / 2
            nq_sweep_and_ob_ce_confirmed = True
        
        sweep_lows_key_levels_info = {
            "instrument": instrument,
            "side": "sell_side",
            
            "timestamp": last_closed_candle["timestamp"],
            "sweep_candle_low": last_closed_candle["low"],
            "sweep_time": sweep_time_low,
            "sweep_key_level": True,
            "swept_levels": swept_levels_low,
            "sweep_type": sweep_type,
            "sweep_and_ob_confirmed": nq_sweep_and_ob_confirmed,
            "sweep_and_ob_entry": nq_sweep_and_ob_entry,
            "sweep_and_ob_ce_confirmed": nq_sweep_and_ob_ce_confirmed,
            "sweep_and_ob_ce_entry": nq_sweep_and_ob_ce_entry,
            "sweep_and_ob_confirmation_timestamp": nq_sweep_and_ob_confirmation_timestamp
        }

    if sweep_highs:
        sweep_time_high = find_sweep_time_3m(inside_3m_candles, last_closed_candle["high"], "buy_side")
        nq_sweep_and_ob_entry = None
        nq_sweep_and_ob_ce_entry = None
        nq_sweep_and_ob_confirmed = False
        nq_sweep_and_ob_ce_confirmed = False
        nq_sweep_and_ob_confirmation_timestamp = None
        nq_sweep_and_ob_confirmed = last_closed_candle["close"] < last_closed_candle["open"] + 3 
    
    
        if nq_sweep_and_ob_confirmed:
            nq_sweep_and_ob_entry = last_closed_candle["open"]
            # confirmation timestamp is current timestamp
            nq_sweep_and_ob_confirmation_timestamp = last_closed_candle["timestamp"]
    
        if last_closed_candle["close"] < last_closed_candle["open"] and (last_closed_candle["open"] - last_closed_candle["close"]) > 60:
            nq_sweep_and_ob_ce_entry = (last_closed_candle["open"] + last_closed_candle["close"]) / 2
            nq_sweep_and_ob_ce_confirmed = True
        
        sweep_highs_key_levels_info = {
            "instrument": instrument,
            "side": "buy_side",
            "timestamp": last_closed_candle["timestamp"],
            "sweep_candle_high": last_closed_candle["high"],
            "sweep_time": sweep_time_high,
            "sweep_key_level": True,
            "swept_levels": swept_levels_high,
            "sweep_type": sweep_type,
            "sweep_and_ob_confirmed": nq_sweep_and_ob_confirmed,
            "sweep_and_ob_entry": nq_sweep_and_ob_entry,
            "sweep_and_ob_ce_confirmed": nq_sweep_and_ob_ce_confirmed,
            "sweep_and_ob_ce_entry": nq_sweep_and_ob_ce_entry,
            "sweep_and_ob_confirmation_timestamp": nq_sweep_and_ob_confirmation_timestamp
        }

    return sweep_highs_key_levels_info, sweep_lows_key_levels_info

def detect_30m_and_key_level_sweep(instrument, valid_swing_highs, valid_swing_lows, candles_3m, last_closed_candle, key_levels, current_30m_start):
    sweep_highs_info = None
    sweep_lows_info = None
    
    for swing in valid_swing_highs:
        if last_closed_candle["high"] > swing["high"]:
            sweep_type = None
            sweep_type = "rejection" if last_closed_candle["close"] < swing["high"] else "breakout"
            # last candle high and low
            sweep_candle_start = last_closed_candle["timestamp"]
            sweep_candle_end = (
                datetime.fromisoformat(sweep_candle_start)
                + timedelta(minutes=30)
            ).isoformat()
            
            nq_sweep_and_ob_entry = None
            nq_sweep_and_ob_ce_entry = None
            nq_sweep_and_ob_confirmed = False
            nq_sweep_and_ob_ce_confirmed = False
            nq_sweep_and_ob_confirmation_timestamp = None
            
            inside_3m_candles = [c for c in candles_3m if c["timestamp"] >= sweep_candle_start and c["timestamp"] < sweep_candle_end]
            sweep_time = find_sweep_time_3m(inside_3m_candles, last_closed_candle["high"], "buy_side")
            sweep, levels, sweep_type = detect_key_liquidity_sweep_highs(last_closed_candle, key_levels)
            # print(f"{instrument} Sweep highs, Swept levels:", sweep, levels)
            
            if sweep:
                nq_sweep_and_ob_confirmed = last_closed_candle["close"] < last_closed_candle["open"] + 3 
            else:
                nq_sweep_and_ob_confirmed = last_closed_candle["close"] < last_closed_candle["open"]
            
            if nq_sweep_and_ob_confirmed:
                nq_sweep_and_ob_entry = last_closed_candle["open"]
                # confirmation timestamp is current timestamp
                nq_sweep_and_ob_confirmation_timestamp = last_closed_candle["timestamp"]
            
            if last_closed_candle["close"] < last_closed_candle["open"] and (last_closed_candle["open"] - last_closed_candle["close"]) > 60:
                nq_sweep_and_ob_ce_entry = (last_closed_candle["open"] + last_closed_candle["close"]) / 2
                nq_sweep_and_ob_ce_confirmed = True
            # ny_am bias = bullish
            # ny_lunch = bearish - reversal or retracement
            # ny_pm = 7h wick window - setup based on 30m sweep and ob or 3pm retest of 30m ob for continuation
            sweep_highs_info = {
                "instrument": instrument,
                "side": "buy_side",
                "timestamp": last_closed_candle["timestamp"],
                "sweep_candle_high": last_closed_candle["high"],
                "sweep_time": sweep_time,
                
                "sweep_key_level": sweep,
                "swept_levels": levels,
                "sweep_type": sweep_type,
                "sweep_and_ob_confirmed": nq_sweep_and_ob_confirmed,
                "sweep_and_ob_entry": nq_sweep_and_ob_entry,
                "sweep_and_ob_ce_confirmed": nq_sweep_and_ob_ce_confirmed,
                "sweep_and_ob_ce_entry": nq_sweep_and_ob_ce_entry,
                "sweep_and_ob_confirmation_timestamp": nq_sweep_and_ob_confirmation_timestamp
            }
            break

    for swing in valid_swing_lows:
        if last_closed_candle["low"] < swing["low"]:
            # print("swept low: ", swing["low"], " last candle low: ", last_closed_candle["low"])
            sweep_type = None
            sweep_type =  "rejection" if last_closed_candle["close"] > swing["low"] else "breakout"
            sweep_candle_start = last_closed_candle["timestamp"]
            sweep_candle_end = (
                datetime.fromisoformat(sweep_candle_start)
                + timedelta(minutes=30)
            ).isoformat()
            nq_sweep_and_ob_confirmed = False
            nq_sweep_and_ob_ce_confirmed = False
            nq_sweep_and_ob_entry = None
            nq_sweep_and_ob_ce_entry = None
            nq_sweep_and_ob_confirmation_timestamp = None

            
            inside_3m_candles = [c for c in candles_3m if c["timestamp"] >= sweep_candle_start and c["timestamp"] < sweep_candle_end]
            sweep_time = find_sweep_time_3m(inside_3m_candles, last_closed_candle["low"], "sell_side")
            sweep, levels, sweep_type = detect_key_liquidity_sweep_lows(last_closed_candle, key_levels)
            # print(f"{instrument} Sweep lows, Swept levels:", sweep, levels)

            if sweep:
                nq_sweep_and_ob_confirmed = last_closed_candle["close"] > last_closed_candle["open"] - 3
            else:
                nq_sweep_and_ob_confirmed = last_closed_candle["close"] > last_closed_candle["open"]
            
            if nq_sweep_and_ob_confirmed:
                nq_sweep_and_ob_entry = last_closed_candle["open"]
                nq_sweep_and_ob_confirmation_timestamp = last_closed_candle["timestamp"]
            if last_closed_candle["close"] > last_closed_candle["open"] and last_closed_candle["close"] - last_closed_candle["open"] > 60:
                nq_sweep_and_ob_ce_entry = (last_closed_candle["open"] + last_closed_candle["close"]) / 2
                nq_sweep_and_ob_ce_confirmed = True
            
            
            sweep_lows_info = {
                "instrument": instrument,
                "side": "sell_side",
                "timestamp": last_closed_candle["timestamp"],
                "sweep_candle_low": last_closed_candle["low"],
                "sweep_time": sweep_time,
                "sweep_key_level": sweep,
                "swept_levels": levels,
                "sweep_type": sweep_type,
                "sweep_and_ob_confirmed": nq_sweep_and_ob_confirmed,
                "sweep_and_ob_entry": nq_sweep_and_ob_entry,
                "sweep_and_ob_ce_confirmed": nq_sweep_and_ob_ce_confirmed,
                "sweep_and_ob_ce_entry": nq_sweep_and_ob_ce_entry,
                "sweep_and_ob_confirmation_timestamp": nq_sweep_and_ob_confirmation_timestamp
            }
            break

    return sweep_highs_info, sweep_lows_info

def detect_dual_sweep(
    nq_30m,
    nq_3m,
    es_30m,
    current_7h_open_iso,
    wick_window_minutes
):

    windows = get_reversal_windows(
        current_7h_open_iso,
        wick_window_minutes
    )
    # print("Last 30m candle timestamp:", nq_30m[-1]["timestamp"])
    # print("Last 3m candle timestamp:", nq_3m[-1]["timestamp"])

    nq_result = detect_30m_swing_sweep(nq_30m, windows, "NQ")
    # print("NQ sweep result:", nq_result)
    es_result = detect_30m_swing_sweep(es_30m, windows, "ES")
    # print("ES sweep result:", es_result)

    # smt on 1hr
    # smt_1hr = detect_smt_1h()
    # smt_1h = {
    #     "smt_exists": smt_exists,
    #     "sweep_on_nq": sweep_on_nq,
    #     "sweep_on_es": sweep_on_es
    # }

    # smt at key level

    # smt at 30m swing
    



    return {
        "sweep_exists": nq_result["sweep_detected"] or es_result["sweep_detected"],
        "NQ": nq_result,
        "ES": es_result
    }




# -------------------------------------------------------
# Swing-based sweep logic
# -------------------------------------------------------

def detect_30m_swing_sweep(candles, windows, instrument):

    if len(candles) < 5:
        return _no_sweep()
    instrument = instrument
    raw_swings_high = find_swing_highs(candles[:-1])
    raw_swings_low = find_swing_lows(candles[:-1])
    valid_swings_high = filter_valid_swing_highs(raw_swings_high)
    valid_swings_low = filter_valid_swing_lows(raw_swings_low)
    print("{instrument} valid swing highs")
    for swing in valid_swings_high:
        print(swing["high"], end=", ")
    print("\n{instrument} valid swing lows")
    for swing in valid_swings_low:
        print(swing["low"], end=", ")
    
    # Last closed 30m candle (just completed)
    last_closed = candles[-1]

    valid, window_name = is_in_reversal_window(
        last_closed["timestamp"],
        windows
    )
    print(f"valid: {valid}, window_name: {window_name} for timestamp {last_closed['timestamp']} in windows {windows}")
    if not valid:
        return _no_sweep()
    
    # -------------------------
    # Bearish sweep (buy-side taken)
    # -------------------------
    # print(f"Valid swings high: {valid_swings_high}")
    if not valid_swings_high:
        return _no_sweep()

    # -----------------------------------------
    # 3️⃣ Check if last_closed swept ≥ 1
    # -----------------------------------------
    swept_levels = []

    for swing in valid_swings_high:
        print(f"Comparing last closed high {last_closed['high']} with swing high {swing['high']}")
        if last_closed["high"] > swing["high"]:
            swept_levels.append(swing)
    print(f"Swept levels: {swept_levels}")
    # print("---------------------------")
    if swept_levels:
        print("Swept highs:", swept_levels)
        return {
            "sweep_detected": True,
            "side": "buy_side",   # buy-side liquidity taken
            "timestamp": last_closed["timestamp"],
            "window": window_name,
            "swept_levels": swept_levels,
            "valid_window": valid
        }

    # -------------------------
    # Bullish sweep (sell-side taken)
    # -------------------------
    # print(f"Valid swings low: {valid_swings_low}")
    
    if not valid_swings_low:
        return _no_sweep()
    swept_levels_low = []
    for swing in valid_swings_low:
        if last_closed["low"] < swing["low"]:
            swept_levels_low.append(swing)

    if swept_levels_low:
        # print("Swept lows:", swept_levels_low)
        return {
            "sweep_detected": True,
            "side": "sell_side",
            "timestamp": last_closed["timestamp"],
            "window": window_name,
            "swept_levels": swept_levels_low,
            "valid_window": valid
        }

    return _no_sweep()


def _no_sweep():
    return {
        "sweep_detected": False,
        "side": None,
        "timestamp": None,
        "window": None
    }

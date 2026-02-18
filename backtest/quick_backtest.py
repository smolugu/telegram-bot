from data.market_data import fetch_symbol_data_safe
from data.models.setup_candidate import SetupCandidate
from helpers.time_windows import get_active_window
from modules.imbalance_detector import detect_3m_fvg
from modules.orchestrator import evaluate_7h_setup
from helpers.zones import get_7h_open_from_timestamp

from datetime import datetime
from modules.smt_detector import detect_smt_dual
from modules.ob_detector import detect_30m_order_block
from modules.sweep_detector import find_swing_highs, find_swing_lows

def filter_valid_swing_lows(swings, candles):

    valid = []

    for swing in swings:

        swing_ts = swing["timestamp"]
        swing_low = swing["low"]

        # 1️⃣ Remove structurally dominated lows
        valid = [v for v in valid if v["low"] < swing_low]

        # 2️⃣ Check if swept after forming
        swept = False
        for c in candles:
            if c["timestamp"] > swing_ts:
                if c["low"] < swing_low:
                    swept = True
                    break

        if not swept:
            valid.append(swing)

    return valid


def filter_valid_swing_highs(swings, candles):

    valid = []

    for swing in swings:

        swing_ts = swing["timestamp"]
        swing_high = swing["high"]
        # 1️⃣ Remove structurally dominated highs
        valid = [v for v in valid if v["high"] > swing_high]

        swept = False

        for c in candles:
            if c["timestamp"] > swing_ts:
                if c["high"] > swing_high:
                    swept = True
                    break

        if not swept:
            valid.append(swing)

    return valid


def filter_valid_swing_highs_old(swings):

    if not swings:
        return []

    valid = []

    for swing in swings:
        # Remove any existing swings lower than this one
        valid = [s for s in valid if s["high"] > swing["high"]]

        valid.append(swing)

    return valid

def filter_valid_swing_lows_old(swings):

    if not swings:
        return []

    valid = []

    for swing in swings:
        # Remove any existing swings higher than this one
        valid = [s for s in valid if s["low"] < swing["low"]]

        valid.append(swing)

    return valid

def debug_print_30m_swings(nq_30m, test_date):

    # Filter only that day
    day_30m = [c for c in nq_30m if test_date in c["timestamp"]]

    swings_high = find_swing_highs(day_30m)
    swings_low = find_swing_lows(day_30m)

    print("\n--- 30M SWING HIGHS ---")
    for s in swings_high:
        print(s["timestamp"], s["high"])

    print("\n--- 30M SWING LOWS ---")
    for s in swings_low:
        print(s["timestamp"], s["low"])
    #  print only relevant swings for the day
    print("\n--- FILTERED PROGRESSIVE SWING HIGHS ---")
    progressive_highs = filter_valid_swing_highs(swings_high)
    
    for s in progressive_highs:
        print(s["timestamp"], s["high"])
    progressive_lows = filter_valid_swing_lows(swings_low)
    print("\n--- FILTERED PROGRESSIVE SWING LOWS ---")
    for s in progressive_lows:
        print(s["timestamp"], s["low"])



def run_quick_backtest(test_date: str):

    print(f"Backtesting {test_date}")

    nq = fetch_symbol_data_safe("NQ=F")
    es = fetch_symbol_data_safe("ES=F")
    # Filter only Feb 13
    nq_30m = [c for c in nq["30m"] if test_date in c["timestamp"]]
    nq_3m  = [c for c in nq["3m"] if test_date in c["timestamp"]]
    print("Sample 30m timestamp:", nq["30m"][0]["timestamp"])
    # print("Sample 3m timestamp:", nq_3m[0]["timestamp"])

    es_30m = [c for c in es["30m"] if test_date in c["timestamp"]]
    es_3m  = [c for c in es["3m"] if test_date in c["timestamp"]]

    print("Total 30m candles:", len(nq_30m))
    print("Total 3m candles:", len(nq_3m))

    
    # debug_print_30m_swings(nq_30m, test_date)

    if not nq or not es:
        print("No data available.")
        return
    nq_buy_candidate = SetupCandidate("buy_side")
    nq_sell_candidate = SetupCandidate("sell_side")
    es_buy_candidate = SetupCandidate("buy_side")
    es_sell_candidate = SetupCandidate("sell_side")
    current_window = None

    for i in range(3, len(nq_30m)):
        print("\n---------------------------")
        # reset setup candidates at the start of each 7h window
        current_30m_start = nq_30m[i]["timestamp"]
        window_name = get_active_window(current_30m_start)

        if window_name != current_window:
            print("🔄 New window detected:", window_name)

            nq_buy_candidate.reset()
            nq_sell_candidate.reset()
            es_buy_candidate.reset()
            es_sell_candidate.reset()

            current_window = window_name
        print("Current window:", current_window)
        # previous 30m candle just closed
        last_closed_nq = nq_30m[i - 1]
        last_closed_es = es_30m[i - 1]
        print("i =", i)
        print("Last closed:", last_closed_nq["timestamp"])
        # current_30m_start = nq_30m[i]["timestamp"]
        print("current 30m boundary at:", current_30m_start)
        
        # ts_dt = datetime.fromisoformat(current_ts)
        # print("Current TS:", current_ts)
        # if ts_dt.minute % 30 != 0:
        #     continue
        historical_nq = nq_30m[:i - 1]
        historical_es = es_30m[:i - 1]
        print("Historical count:", len(historical_nq))
        print("Historical count:", len(historical_es))

        raw_swings_high_nq = find_swing_highs(historical_nq)
        raw_swings_low_nq  = find_swing_lows(historical_nq)
        print("Raw swing highs:", [(s["timestamp"], s["high"]) for s in raw_swings_high_nq])
        print("Raw swing lows:", [(s["timestamp"], s["low"]) for s in raw_swings_low_nq])
        raw_swings_high_es = find_swing_highs(historical_es)
        raw_swings_low_es  = find_swing_lows(historical_es)
        print("Raw swing highs:", [(s["timestamp"], s["high"]) for s in raw_swings_high_es])
        print("Raw swing lows:", [(s["timestamp"], s["low"]) for s in raw_swings_low_es])
        valid_highs_nq = filter_valid_swing_highs(raw_swings_high_nq, nq_30m[i:])
        valid_lows_nq  = filter_valid_swing_lows(raw_swings_low_nq, nq_30m[i:])
        valid_highs_es = filter_valid_swing_highs(raw_swings_high_es, es_30m[i:])
        valid_lows_es  = filter_valid_swing_lows(raw_swings_low_es, es_30m[i:])

        print("Valid swing highs NQ:", [(s["timestamp"], s["high"]) for s in valid_highs_nq])
        print("Valid swing lows NQ:", [(s["timestamp"], s["low"]) for s in valid_lows_nq])
        print("Valid swing highs ES:", [(s["timestamp"], s["high"]) for s in valid_highs_es])
        print("Valid swing lows ES:", [(s["timestamp"], s["low"]) for s in valid_lows_es])
        sweep_nq = None
        sweep_es = None

        for swing in valid_highs_nq:
            if last_closed_nq["high"] > swing["high"]:
                sweep_nq = {
                    "side": "buy_side",
                    "timestamp": last_closed_nq["timestamp"]
                }
                break

        for swing in valid_lows_nq:
            if last_closed_nq["low"] < swing["low"]:
                sweep_nq = {
                    "side": "sell_side",
                    "timestamp": last_closed_nq["timestamp"]
                }
                break
        
        for swing in valid_highs_es:
            if last_closed_es["high"] > swing["high"]:
                sweep_es = {
                    "side": "buy_side",
                    "timestamp": last_closed_es["timestamp"]
                }
                break

        for swing in valid_lows_es:
            if last_closed_es["low"] < swing["low"]:
                sweep_es = {
                    "side": "sell_side",
                    "timestamp": last_closed_es["timestamp"]
                }
                break
        if not sweep_nq and not sweep_es:
            continue
        
        if sweep_nq:
            print("SWEEP DETECTED NQ:", sweep_nq)

            if sweep_nq["side"] == "buy_side":
                nq_buy_candidate.register_sweep(sweep_nq["timestamp"])

            if sweep_nq["side"] == "sell_side":
                nq_sell_candidate.register_sweep(sweep_nq["timestamp"])
        
        if sweep_es:
            print("SWEEP DETECTED ES:", sweep_es)

            if sweep_es["side"] == "buy_side":
                es_buy_candidate.register_sweep(sweep_es["timestamp"])

            if sweep_es["side"] == "sell_side":
                es_sell_candidate.register_sweep(sweep_es["timestamp"])
        
        # print for debug
        print("Nq Buy candidate active:", nq_buy_candidate.active,
            "| NQ sweep at:", nq_buy_candidate.sweep_timestamp)

        print("Nq Sell candidate active:", nq_sell_candidate.active,
            "| NQ sweep at:", nq_sell_candidate.sweep_timestamp)

        print("Es Buy candidate active:", es_buy_candidate.active,
            "| ES sweep at:", es_buy_candidate.sweep_timestamp)

        print("Es Sell candidate active:", es_sell_candidate.active,
            "| ES sweep at:", es_sell_candidate.sweep_timestamp)

        # smt = detect_smt_dual(
        # nq_30m[:i],
        # es_30m[:i])

        # if not smt["smt_confirmed"]:
        #     continue

        # print("SMT CONFIRMED:", smt)

        # ob = detect_30m_order_block(
        # nq_30m[:i],
        # direction="SHORT" if sweep["side"] == "buy_side" else "LONG"
        # )

        # if not ob["ob_found"]:
        #     continue

        # print("30M OB CONFIRMED:", ob)

        # current_ts = last_closed_nq["timestamp"]

        # nq_3m_partial = [
        # c for c in nq_3m
        # if c["timestamp"] <= current_ts
        # ]

        # fvg = detect_3m_fvg(
        # nq_3m_partial,
        # ob
        # )

        # if not fvg:
        #     continue

        # print("3M FVG FOUND:", fvg)

        # # alert
        # print("🚨 ALERT 🚨")
        # print("Entry:", fvg["entry"])
        # print("Stop:", ob["protected_high"])
        # print("Target:", fvg["entry"] - 2 * (ob["protected_high"] - fvg["entry"]))







        

        # partial_market_data = {
        #     "NQ": {
        #         "30m": nq["30m"],
        #         "1h": nq["1h"],
        #         "3m": nq_3m[:i],
        #         "protected_high": None,
        #         "protected_low": None
        #     },
        #     "ES": {
        #         "30m": es["30m"],
        #         "1h": es["1h"],
        #         "3m": es_3m[:i],
        #         "protected_high": None,
        #         "protected_low": None
        #     },
        #     "daily": nq["30m"],
        #     "current_price": nq_3m[i]["close"]
        # }
        
        # result = evaluate_7h_setup(
        #     market_data=partial_market_data,
        #     seven_hour_open_ts=seven_open,
        #     wick_window_minutes=60
        # )

        # if result["stage"] != "NONE":
        #     print(
        #         current_ts,
        #         result["stage"],
        #         result.get("smt")
        #     )
        

from alerts.execute import execute_trade_and_log
from data.sqlite.db import DB_FILE

from data.market_data import fetch_symbol_data_safe
from data.models.setup_candidate import SetupCandidate
from data.sqlite.db_functions import insert_trade, monitor_open_trades
from helpers.sweep_time import find_sweep_time_3m
from helpers.time_windows import get_active_window
from modules.imbalance_detector_old import detect_3m_fvg
from modules.orchestrator import evaluate_7h_setup
from helpers.zones import get_7h_open_from_timestamp

from datetime import datetime, timedelta
from modules.smt_detector import detect_smt_dual
from modules.ob_detector import detect_30m_order_block
from modules.sweep_detector import find_swing_highs, find_swing_lows
from modules.imbalance_detector import detect_3m_imbalance_inside_ob_candle
from alerts.alert_engine import send_telegram_alert_to_all
from alerts.alert_payload import build_trade_alert


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
    # print("NQ: ", nq)
    # print("ES: ", es)
    # Filter only Feb 13
    nq_30m = [c for c in nq["30m"] if test_date in c["timestamp"]]
    nq_3m  = [c for c in nq["3m"] if test_date in c["timestamp"]]
    # nq_30m = nq["30m"]
    # nq_3m = nq["3m"]
    print("Sample 30m timestamp:", nq["30m"][0]["timestamp"])
    # print("Sample 3m timestamp:", nq_3m[0]["timestamp"])

    es_30m = [c for c in es["30m"] if test_date in c["timestamp"]]
    es_3m  = [c for c in es["3m"] if test_date in c["timestamp"]]
    # es_30m = es["30m"]
    # es_3m = es["3m"]
    print("Sample 30m timestamp:", es["30m"][0]["timestamp"])

    # print("Total 30m candles:", len(nq_30m))
    # print("Total 3m candles:", len(nq_3m))

    
    # debug_print_30m_swings(nq_30m, test_date)

    if not nq or not es:
        print("No data available.")
        return
    nq_30m_closes = {
        nq_30m[i]["timestamp"]: i
        for i in range(len(nq_30m))
    }
    nq_sell_candidate = SetupCandidate("buy_side")
    nq_buy_candidate = SetupCandidate("sell_side")
    es_sell_candidate = SetupCandidate("buy_side")
    es_buy_candidate = SetupCandidate("sell_side")
    current_window = None
    for candle_3m in nq_3m:
        ts = candle_3m["timestamp"]
        if ts in nq_30m_closes:
            i = nq_30m_closes[ts]
            print("Matching 30m candle found for 3m timestamp:", ts, "at index", i)
            if i >= 3:
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
                # print("Historical count:", len(historical_nq))
                # print("Historical count:", len(historical_es))
                #  check if there is already a sweep
                raw_swings_high_nq = find_swing_highs(historical_nq)
                raw_swings_low_nq  = find_swing_lows(historical_nq)
                # print("Raw swing highs:", [(s["timestamp"], s["high"]) for s in raw_swings_high_nq])
                # print("Raw swing lows:", [(s["timestamp"], s["low"]) for s in raw_swings_low_nq])
                raw_swings_high_es = find_swing_highs(historical_es)
                raw_swings_low_es  = find_swing_lows(historical_es)
                # print("Raw swing highs:", [(s["timestamp"], s["high"]) for s in raw_swings_high_es])
                # print("Raw swing lows:", [(s["timestamp"], s["low"]) for s in raw_swings_low_es])
                valid_highs_nq = filter_valid_swing_highs(raw_swings_high_nq, nq_30m[i:])
                valid_lows_nq  = filter_valid_swing_lows(raw_swings_low_nq, nq_30m[i:])
                valid_highs_es = filter_valid_swing_highs(raw_swings_high_es, es_30m[i:])
                valid_lows_es  = filter_valid_swing_lows(raw_swings_low_es, es_30m[i:])

                # print("Valid swing highs NQ:", [(s["timestamp"], s["high"]) for s in valid_highs_nq])
                # print("Valid swing lows NQ:", [(s["timestamp"], s["low"]) for s in valid_lows_nq])
                # print("Valid swing highs ES:", [(s["timestamp"], s["high"]) for s in valid_highs_es])
                # print("Valid swing lows ES:", [(s["timestamp"], s["low"]) for s in valid_lows_es])
                sweep_nq = None
                sweep_es = None

                for swing in valid_highs_nq:
                    if last_closed_nq["high"] > swing["high"]:
                        # last candle high and low
                        sweep_candle_start = last_closed_nq["timestamp"]
                        sweep_candle_end = (
                            datetime.fromisoformat(sweep_candle_start)
                            + timedelta(minutes=30)
                        ).isoformat()
                        inside_3m_candles = [c for c in nq_3m if c["timestamp"] >= sweep_candle_start and c["timestamp"] < sweep_candle_end]
                        sweep_time = find_sweep_time_3m(inside_3m_candles, last_closed_nq["high"], "buy_side")
                        sweep_nq = {
                            "side": "buy_side",
                            "timestamp": last_closed_nq["timestamp"],
                            "sweep candle high": last_closed_nq["high"],
                            "sweep_time": sweep_time
                        }
                        break

                for swing in valid_lows_nq:
                    if last_closed_nq["low"] < swing["low"]:
                        sweep_candle_start = last_closed_nq["timestamp"]
                        sweep_candle_end = (
                            datetime.fromisoformat(sweep_candle_start)
                            + timedelta(minutes=30)
                        ).isoformat()
                        inside_3m_candles = [c for c in nq_3m if c["timestamp"] >= sweep_candle_start and c["timestamp"] < sweep_candle_end]
                        sweep_time = find_sweep_time_3m(inside_3m_candles, last_closed_nq["low"], "sell_side")
                        sweep_nq = {
                            "side": "sell_side",
                            "timestamp": last_closed_nq["timestamp"],
                            "sweep candle low": last_closed_nq["low"],
                            "sweep_time": sweep_time
                        }
                        break
                
                for swing in valid_highs_es:
                    
                    if last_closed_es["high"] > swing["high"]:
                        sweep_candle_start = last_closed_es["timestamp"]
                        sweep_candle_end = (
                            datetime.fromisoformat(sweep_candle_start)
                            + timedelta(minutes=30)
                        ).isoformat()
                        inside_3m_candles = [c for c in es_3m if c["timestamp"] >= sweep_candle_start and c["timestamp"] < sweep_candle_end]
                        sweep_time = find_sweep_time_3m(inside_3m_candles, last_closed_es["high"], "buy_side")
                        sweep_es = {
                            "side": "buy_side",
                            "timestamp": last_closed_es["timestamp"],
                            "sweep candle high": last_closed_es["high"],
                            "sweep_time": sweep_time
                        }
                        break

                for swing in valid_lows_es:
                    if last_closed_es["low"] < swing["low"]:
                        sweep_candle_start = last_closed_es["timestamp"]
                        sweep_candle_end = (
                            datetime.fromisoformat(sweep_candle_start)
                            + timedelta(minutes=30)
                        ).isoformat()
                        inside_3m_candles = [c for c in es_3m if c["timestamp"] >= sweep_candle_start and c["timestamp"] < sweep_candle_end]
                        sweep_time = find_sweep_time_3m(inside_3m_candles, last_closed_es["low"], "sell_side")
                        sweep_es = {
                            "side": "sell_side",
                            "timestamp": last_closed_es["timestamp"],
                            "sweep candle low": last_closed_es["low"],
                            "sweep_time": sweep_time
                        }
                        break
                # if not sweep_nq and not sweep_es:
                #     continue
                
                if sweep_nq:
                    print("SWEEP DETECTED NQ:", sweep_nq)
                    if sweep_nq["side"] == "buy_side":
                        nq_sell_candidate.register_sweep(sweep_nq["timestamp"], sweep_nq["sweep candle high"], sweep_nq["sweep_time"])
                    
                    if sweep_nq["side"] == "sell_side":
                        nq_buy_candidate.register_sweep(sweep_nq["timestamp"], sweep_nq["sweep candle low"], sweep_nq["sweep_time"])
                
                if sweep_es:
                    print("SWEEP DETECTED ES:", sweep_es)
                    if sweep_es["side"] == "buy_side":
                        es_sell_candidate.register_sweep(sweep_es["timestamp"], sweep_es["sweep candle high"], sweep_es["sweep_time"])

                    if sweep_es["side"] == "sell_side":
                        es_buy_candidate.register_sweep(sweep_es["timestamp"], sweep_es["sweep candle low"], sweep_es["sweep_time"])
                
                if not nq_buy_candidate.active and not nq_sell_candidate.active and not es_buy_candidate.active and not es_sell_candidate.active:
                    continue
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
                # --- NQ OB detection ---
                # call OB detector for both candidates if either is active
                if nq_buy_candidate.active or es_buy_candidate.active:

                    nq_ob = detect_30m_order_block(nq_30m[:i], nq_buy_candidate)
                    if nq_ob:
                        nq_buy_candidate.register_ob(nq_ob)

                    es_ob = detect_30m_order_block(es_30m[:i], es_buy_candidate)
                    if es_ob:
                        es_buy_candidate.register_ob(es_ob)

                if nq_sell_candidate.active or es_sell_candidate.active:

                    nq_ob = detect_30m_order_block(nq_30m[:i], nq_sell_candidate)
                    if nq_ob:
                        nq_sell_candidate.register_ob(nq_ob)

                    es_ob = detect_30m_order_block(es_30m[:i], es_sell_candidate)
                    if es_ob:
                        es_sell_candidate.register_ob(es_ob)

                # we can continue if no OBs found for active candidates
                should_continue = False
                if (nq_buy_candidate.active and not nq_buy_candidate.ob_confirmed) and (es_buy_candidate.active and not es_buy_candidate.ob_confirmed):
                    should_continue = True
                if (nq_sell_candidate.active and not nq_sell_candidate.ob_confirmed) and (es_sell_candidate.active and not es_sell_candidate.ob_confirmed):
                    should_continue = True
                if should_continue:
                    continue

                # print for debug
                print("Nq Buy candidate OB:", nq_buy_candidate.ob_confirmed, "| NQ sweep at:", nq_buy_candidate.sweep_timestamp,
                    "| OB data:", nq_buy_candidate.ob_data)

                print("Nq Sell candidate OB:", nq_sell_candidate.ob_confirmed, "| NQ sweep at:", nq_sell_candidate.sweep_timestamp,
                    "| OB data:", nq_sell_candidate.ob_data)

                print("Es Buy candidate OB:", es_buy_candidate.ob_confirmed, "| ES sweep at:", es_buy_candidate.sweep_timestamp,
                    "| OB data:", es_buy_candidate.ob_data)

                print("Es Sell candidate OB:", es_sell_candidate.ob_confirmed, "| ES sweep at:", es_sell_candidate.sweep_timestamp,
                    "| OB data:", es_sell_candidate.ob_data)

                
                fvg = None
                if nq_buy_candidate.active and nq_buy_candidate.ob_confirmed:
                    print("Processing FVG for NQ Buy candidate")
                    #  imbalance should be present between sweep time and Ob time

                    fvg = detect_3m_imbalance_inside_ob_candle(
                        nq_3m,
                        nq_buy_candidate,
                        "NQ"
                    )
                    if fvg:
                        nq_buy_candidate.register_fvg(fvg)
                        print("Bullish FVG detected:", fvg)
                
                if nq_sell_candidate.active and nq_sell_candidate.ob_confirmed:
                    print("Processing FVG for NQ Sell candidate")

                    fvg = detect_3m_imbalance_inside_ob_candle(
                        nq_3m,
                        nq_sell_candidate,
                        "NQ"
                    )
                    if fvg:
                        nq_sell_candidate.register_fvg(fvg)
                        print("Bearish FVG detected:", fvg)

                # send alert if FVG confirmed and alert not sent for that candidate
                if nq_sell_candidate.fvg_confirmed and not nq_sell_candidate.alert_sent:
                    # send alert for NQ sell candidate
                    message = build_trade_alert(nq_sell_candidate)
                    if message:
                        execute_trade_and_log(nq_sell_candidate, message)
                        # send_telegram_alert_to_all(message)
                        # nq_sell_candidate.alert_sent = True
                        # insert_trade(nq_sell_candidate)

                        # conn = sqlite3.connect(DB_FILE)
                        # cursor = conn.cursor()

                        # cursor.execute("SELECT COUNT(*) FROM trades")
                        # print("Total trades:", cursor.fetchone())

                        # conn.close()
                if nq_buy_candidate.fvg_confirmed and not nq_buy_candidate.alert_sent:
                    # send alert for NQ buy candidate
                    message = build_trade_alert(nq_buy_candidate)
                    if message:
                        execute_trade_and_log(nq_buy_candidate, message)
                        # send_telegram_alert_to_all(message)
                        # nq_buy_candidate.alert_sent = True
                        # insert_trade(nq_buy_candidate)
                # if es_sell_candidate.fvg_confirmed and not es_sell_candidate.alert_sent:
                #     # send alert for ES sell candidate
                #     message = build_trade_alert(es_sell_candidate)
                #     if message:
                #         send_telegram_alert_to_all(message)
                #         es_sell_candidate.alert_sent = True
                #         insert_trade(es_sell_candidate)
                # if es_buy_candidate.fvg_confirmed and not es_buy_candidate.alert_sent:
                #     # send alert for ES buy candidate
                #     message = build_trade_alert(es_buy_candidate)
                #     if message:
                #         send_telegram_alert_to_all(message)
                #         es_buy_candidate.alert_sent = True
                #         insert_trade(es_buy_candidate)

                
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
        # Always monitor open trades
        monitor_open_trades(candle_3m)

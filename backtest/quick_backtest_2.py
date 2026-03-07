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

from datetime import datetime, timedelta, timezone
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


# def filter_valid_swing_highs(swings, candles):

#     valid = []

#     for swing in swings:

#         swing_ts = swing["timestamp"]
#         swing_high = swing["high"]
#         # 1️⃣ Remove structurally dominated highs
#         valid = [v for v in valid if v["high"] > swing_high]

#         swept = False

#         for c in candles:
#             if c["timestamp"] > swing_ts:
#                 if c["high"] > swing_high:
#                     swept = True
#                     break

#         if not swept:
#             valid.append(swing)

#     return valid
def filter_valid_swing_highs(swings):

    valid = []

    for swing in swings:

        swing_high = swing["high"]

        # Remove previous highs that are lower than the current swing
        valid = [v for v in valid if v["high"] > swing_high]

        # Add the current swing
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



def run_quick_backtest2(test_date: str):

    print(f"Backtesting {test_date}")

    nq = fetch_symbol_data_safe("NQ=F")
    es = fetch_symbol_data_safe("ES=F")
    # print("NQ: ", nq)
    # print("ES: ", es)
    # Filter only Feb 13
    test_dt = datetime.fromisoformat(test_date).replace(tzinfo=timezone.utc)
    start_dt = test_dt - timedelta(days=2)
    end_dt = test_dt + timedelta(days=1)
    nq_30m = [c for c in nq["30m"] if start_dt <= datetime.fromisoformat(c["timestamp"]).astimezone(timezone.utc) < end_dt]
    nq_3m  = [c for c in nq["3m"] if start_dt <= datetime.fromisoformat(c["timestamp"]).astimezone(timezone.utc) < end_dt]
    # nq_30m = [c for c in nq["30m"] if test_date in c["timestamp"]]
    # nq_3m  = [c for c in nq["3m"] if test_date in c["timestamp"]]
    # nq_30m = nq["30m"]
    # nq_3m = nq["3m"]
    print("Sample 30m timestamp:", nq["30m"][0]["timestamp"])
    # print("Sample 3m timestamp:", nq_3m[0]["timestamp"])

    # es_30m = [c for c in es["30m"] if test_date in c["timestamp"]]
    # es_3m  = [c for c in es["3m"] if test_date in c["timestamp"]]
    es_30m = [c for c in es["30m"] if start_dt <= datetime.fromisoformat(c["timestamp"]).astimezone(timezone.utc) < end_dt]
    es_3m  = [c for c in es["3m"] if start_dt <= datetime.fromisoformat(c["timestamp"]).astimezone(timezone.utc) < end_dt]
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
                valid_highs_nq = filter_valid_swing_highs(raw_swings_high_nq)
                # valid_lows_nq  = filter_valid_swing_lows(raw_swings_low_nq, nq_30m[i:])
                # valid_highs_es = filter_valid_swing_highs(raw_swings_high_es, es_30m[i:])
                # valid_lows_es  = filter_valid_swing_lows(raw_swings_low_es, es_30m[i:])
                print("nq raw swing highs")
                for swing in raw_swings_high_nq:
                    print(swing["high"], end=", ")
                print("nq valid highs")
                for swing in valid_highs_nq:
                    print(swing["timestamp"], swing["high"])
                # print("es raw highs")
                # for swing in raw_swings_high_es:
                #     print(swing["timestamp"], swing["high"])
                # print("es valid highs")
                # for swing in valid_highs_es:
                #     print(swing["timestamp"], swing["high"])
                print("================================")
                # print("nq raw swings high: ", raw_swings_high_nq)
                # print("nq valid swings high: ", valid_highs_nq)
                # print("nq raw swings low: ", raw_swings_low_nq)
                # print("nq valid swings low: ", valid_lows_nq)
                # print("es raw swings high: ", raw_swings_high_es)
                # print("es valid swings high: ", valid_highs_es)
                # print("es raw swings low: ", raw_swings_low_es)
                # print("es valid swings low: ", valid_lows_es)
                # print("================================")









        # monitor_open_trades(candle_3m)

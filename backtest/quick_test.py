from alerts.execute import execute_trade_and_log
from data.models.candle_7h import SevenHourBuilder
from data.models.day_type_detector import DayTypeContext, MarketContext
from data.sqlite.db import DB_FILE

from data.market_data import fetch_symbol_data_safe, get_futures_session, get_pdh_pdl_fixed_date, session_high_low
from data.models.setup_candidate import SetupCandidate
from data.models.ib_continuation_candidate import IBContinuationCandidate
from data.sqlite.db_functions import insert_trade, monitor_open_trades
from helpers.atr import calculate_daily_atr
from helpers.liquidity_levels import get_liquidity_values, reset_liquidity
from helpers.sweep_time import find_sweep_time_3m
from helpers.time_windows import get_active_window
from modules.imbalance_detector_old import detect_3m_fvg
from modules.nyam_context import get_morning_context
from modules.orchestrator import evaluate_7h_setup
from helpers.zones import get_7h_open_from_timestamp

from datetime import datetime, timedelta, timezone
from modules.smt_detector import detect_smt_dual
from modules.ob_detector import detect_30m_order_block
from modules.sweep_detector import detect_key_liquidity_sweep, find_swing_highs, find_swing_lows
from modules.imbalance_detector import detect_3m_imbalance_inside_ob_candle
from alerts.alert_engine import send_telegram_alert_to_all
from alerts.alert_payload import build_trade_alert


def filter_valid_swing_lows(swings):

    valid = []

    for swing in swings:

        swing_low = swing["low"]

        # Remove previous lows that are higher than the current swing
        valid = [v for v in valid if v["low"] < swing_low]

        # Add the current swing
        valid.append(swing)

    return valid

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



def run_quick_test(test_date: str):

    print(f"Backtesting {test_date}")

    nq = fetch_symbol_data_safe("NQ=F")
    es = fetch_symbol_data_safe("ES=F")
    # print("NQ: ", nq)
    # print("ES: ", es)
    # Filter only Feb 13
    test_dt = datetime.fromisoformat(test_date).replace(tzinfo=timezone.utc)
    start_dt = test_dt - timedelta(days=2)
    end_dt = test_dt + timedelta(days=1)
    # nq_pdh, nq_pdl = get_pdh_pdl(nq["30m"], test_date)
    # es_pdh, es_pdl = get_pdh_pdl(es["30m"], test_date)
    high, low = get_pdh_pdl_fixed_date(test_date)
    print("NQ high, low:", high, low)
    high, low = get_pdh_pdl_fixed_date(test_date, "ES=F")
    print("ES high, low:", high, low)
    
    # print("nq h,l:", nq_pdh, nq_pdl)
    # print("es h,l:", es_pdh, es_pdl)
    nq_daily_atr = calculate_daily_atr(nq["30m"])
    es_daily_atr = calculate_daily_atr(es["30m"])
    
    # nq_30m = [c for c in nq["30m"] if start_dt <= datetime.fromisoformat(c["timestamp"]).astimezone(timezone.utc) < end_dt]
    # nq_3m  = [c for c in nq["3m"] if start_dt <= datetime.fromisoformat(c["timestamp"]).astimezone(timezone.utc) < end_dt]
    # nq_30m = [c for c in nq["30m"] if test_date in c["timestamp"]]
    # nq_3m  = [c for c in nq["3m"] if test_date in c["timestamp"]]
    nq_30m = get_futures_session(nq["30m"], test_date)
    nq_3m = get_futures_session(nq["3m"], test_date)
    # nq_30m = nq["30m"]
    # nq_3m = nq["3m"]
    print("Sample 30m timestamp:", nq["30m"][0]["timestamp"])
    # print("Sample 3m timestamp:", nq_3m[0]["timestamp"])

    # es_30m = [c for c in es["30m"] if test_date in c["timestamp"]]
    # es_3m  = [c for c in es["3m"] if test_date in c["timestamp"]]
    # es_30m = get_futures_session(es["30m"], test_date)
    # es_3m = get_futures_session(es["3m"], test_date)
    # es_30m = [c for c in es["30m"] if start_dt <= datetime.fromisoformat(c["timestamp"]).astimezone(timezone.utc) < end_dt]
    # es_3m  = [c for c in es["3m"] if start_dt <= datetime.fromisoformat(c["timestamp"]).astimezone(timezone.utc) < end_dt]
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
    # print("nq 30m closes: ", nq_30m_closes)
    for candle_3m in nq_3m:
        ts = candle_3m["timestamp"]
        if ts in nq_30m_closes:
            i = nq_30m_closes[ts]
            print("Matching 30m candle found for 3m timestamp:", ts, "at index", i)
            if i >= 3:
                print("\n---------------------------")
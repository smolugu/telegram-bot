from alerts.execute import execute_trade_and_log
from data.models.candle_7h import SevenHourBuilder
from data.models.market_context import MarketContext
from data.sqlite.db import DB_FILE

from data.market_data import fetch_symbol_data_safe, get_current_contract, get_pdh_pdl_fixed_date
from data.models.setup_candidate import SetupCandidate
from data.models.ib_continuation_candidate import IBContinuationCandidate
from data.sqlite.db_functions import insert_trade, monitor_open_trades
from helpers.atr import calculate_daily_atr
from helpers.liquidity_levels import get_liquidity_values, reset_liquidity
from helpers.sessions import get_futures_session, get_session_high_low, in_session
from helpers.swing_points import get_valid_swings
from helpers.time_windows import get_active_window
from modules.imbalance_detector_old import detect_3m_fvg
from modules.nyam_context import get_morning_context
from modules.orchestrator import evaluate_7h_setup
from helpers.zones import get_7h_open_from_timestamp

from datetime import datetime, timedelta, timezone
from modules.smt_detector import detect_30m_swing_smt, detect_smt_key_levels
from modules.ob_detector import detect_30m_order_block
from modules.sweep_detector import detect_30m_and_key_level_sweep, detect_key_liquidity_sweep, find_swing_highs, find_swing_lows
from modules.imbalance_detector import detect_3m_imbalance_inside_ob_candle
from alerts.alert_engine import send_telegram_alert_to_all
from alerts.alert_payload import build_trade_alert


def run_quick_test(test_date: str):

    print(f"Backtesting {test_date}")
    nq_contract = get_current_contract("NQ",test_date)
    es_contract = get_current_contract("ES",test_date)
    print("nq contract: ", nq_contract)
    print("es contract: ", es_contract)

    nq = fetch_symbol_data_safe(nq_contract)
    es = fetch_symbol_data_safe(es_contract)
    # print("NQ: ", nq)
    # print("ES: ", es)
    # Filter only Feb 13
    test_dt = datetime.fromisoformat(test_date).replace(tzinfo=timezone.utc)
    start_dt = test_dt - timedelta(days=2)
    end_dt = test_dt + timedelta(days=1)
    # nq_pdh, nq_pdl = get_pdh_pdl(nq["30m"], test_date)
    # es_pdh, es_pdl = get_pdh_pdl(es["30m"], test_date)
    
    nq_pdh, nq_pdl = get_pdh_pdl_fixed_date(test_date, nq_contract)
    print("NQ high, low:", nq_pdh, nq_pdl)
    es_pdh, es_pdl = get_pdh_pdl_fixed_date(test_date, es_contract)
    print("ES high, low:", es_pdh, es_pdl)
    # high, low = get_pdh_pdl_fixed_date(test_date, "ES=F")
    
    # print("nq h,l:", nq_pdh, nq_pdl)
    # print("es h,l:", es_pdh, es_pdl)
    nq_daily_atr = calculate_daily_atr(nq["30m"])
    es_daily_atr = calculate_daily_atr(es["30m"])
    print("nq daily atr: ", nq_daily_atr, "es daily atr: ", es_daily_atr)
    
    # nq_30m = [c for c in nq["30m"] if start_dt <= datetime.fromisoformat(c["timestamp"]).astimezone(timezone.utc) < end_dt]
    # nq_3m  = [c for c in nq["3m"] if start_dt <= datetime.fromisoformat(c["timestamp"]).astimezone(timezone.utc) < end_dt]
    # nq_30m = [c for c in nq["30m"] if test_date in c["timestamp"]]
    # nq_3m  = [c for c in nq["3m"] if test_date in c["timestamp"]]
    nq_30m = get_futures_session(nq["30m"], test_date)
    # print("nq_30m candles for date: ", nq_30m)
    nq_3m = get_futures_session(nq["3m"], test_date)
    # print("nq_3m candles for date: ", nq_3m)
    # 
    es_30m = get_futures_session(es["30m"], test_date)
    es_3m = get_futures_session(es["3m"], test_date)
    liquidity_nq = reset_liquidity()
    liquidity_es = reset_liquidity()
    # nq_30m = nq["30m"]
    # nq_3m = nq["3m"]
    # print("Sample 30m timestamp:", nq["30m"][0]["timestamp"])
    # print("Sample 3m timestamp:", nq_3m[0]["timestamp"])

    # es_30m = [c for c in es["30m"] if test_date in c["timestamp"]]
    # es_3m  = [c for c in es["3m"] if test_date in c["timestamp"]]
    # es_30m = get_futures_session(es["30m"], test_date)
    # es_3m = get_futures_session(es["3m"], test_date)
    # es_30m = [c for c in es["30m"] if start_dt <= datetime.fromisoformat(c["timestamp"]).astimezone(timezone.utc) < end_dt]
    # es_3m  = [c for c in es["3m"] if start_dt <= datetime.fromisoformat(c["timestamp"]).astimezone(timezone.utc) < end_dt]
    # es_30m = es["30m"]
    # es_3m = es["3m"]
    

    # print("Total 30m candles:", len(nq_30m))
    # print("Total 3m candles:", len(nq_3m))
    # debug_print_30m_swings(nq_30m, test_date)
    nq_market_context = MarketContext("NQ", nq_daily_atr)
    print("daily_atr_nq: ", nq_market_context.daily_atr)
    print("instrument: ", nq_market_context.instrument)
    nq_seven_hour_builder = SevenHourBuilder("NQ")
    es_seven_hour_builder = SevenHourBuilder("ES")

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
        # print("3m candle timestamp: ", ts)
        if ts in nq_30m_closes:
            i = nq_30m_closes[ts]
            print("Matching 30m candle found for 3m timestamp:", ts, "at index", i)
            if i >= 3:
                print("\n---------------------------")
                # reset setup candidates at the start of each 7h window
                current_30m_start = nq_30m[i]["timestamp"]
                is_post_1AM_IB = in_session(current_30m_start, 2, 00, 8, 0)
                print("is_post_1AM_IB: ", is_post_1AM_IB)
                # previous 30m candle just closed
                last_closed_nq = nq_30m[i - 1]
                last_closed_es = es_30m[i - 1]
                prev_last_closed_nq = nq_30m[i-2]
                prev_last_closed_es = es_30m[i-2]
                t1 = datetime.fromisoformat(nq_30m[i-1]["timestamp"])
                t0 = datetime.fromisoformat(nq_30m[i-2]["timestamp"])
                delta = t1 - t0
                print("delta: ", delta, t1, t0)

                if delta > timedelta(minutes=30):
                    print("Irregular gap:", delta)
                

                print("i =", i)
                print("NQ Last closed:", last_closed_nq["timestamp"], last_closed_nq["high"], last_closed_nq["low"])
                print("NQ prev Last closed:", prev_last_closed_nq["timestamp"], prev_last_closed_nq["high"], prev_last_closed_nq["low"])
                # print("ES Last closed:", last_closed_es["timestamp"], last_closed_es["high"], last_closed_es["low"])
                
                # current_30m_start = nq_30m[i]["timestamp"]
                print("current 30m boundary at:", current_30m_start)
                dt = datetime.fromisoformat(last_closed_nq["timestamp"])
                dt_current = datetime.fromisoformat(current_30m_start)
                print("current tix: ", dt.hour)
                if (i == 3):
                    nq_current_session_high = max(nq_30m[0]["high"], nq_30m[1]["high"], nq_30m[2]["high"])
                    nq_current_session_low = min(nq_30m[0]["low"], nq_30m[1]["low"], nq_30m[2]["low"])
                    
                    nq_seven_hour_builder.update(nq_30m[0])
                    nq_seven_hour_builder.update(nq_30m[1])
                    nq_seven_hour_builder.update(nq_30m[2])

                    
                    nq_current_session_high = max(nq_30m[0]["high"], nq_30m[1]["high"], nq_30m[2]["high"])
                    nq_current_session_low = min(nq_30m[0]["low"], nq_30m[1]["low"], nq_30m[2]["low"])
                    es_current_session_high = max(es_30m[0]["high"], es_30m[1]["high"], es_30m[2]["high"])
                    es_current_session_low = min(es_30m[0]["low"], es_30m[1]["low"], es_30m[2]["low"])
                    # update 18:00 candle with the initial 3 candles
                    
                    nq_market_context.update_session_range(nq_30m[0]["high"], nq_30m[0]["low"], nq_30m[0]["open"], nq_30m[0]["close"])
                    nq_market_context.update_session_range(nq_30m[1]["high"], nq_30m[1]["low"], nq_30m[1]["open"], nq_30m[1]["close"])
                    nq_market_context.update_session_range(nq_30m[2]["high"], nq_30m[2]["low"], nq_30m[2]["open"], nq_30m[2]["close"])
                    
                
                if dt.hour == 16:
                    print("resetting liquidity at : ", dt.hour)
                    liquidity_nq = reset_liquidity()
                    liquidity_es = reset_liquidity()
                    print("resetting market context at : ", dt.hour)
                    print("daily atrs before reset: ", nq_market_context.daily_atr)
                    nq_market_context.reset()
                    nq_daily_atr = calculate_daily_atr(nq["30m"])
                    
                    print("new atrs at 16:", nq_daily_atr, es_daily_atr)
                
                historical_nq = nq_30m[:i]
                historical_es = es_30m[:i]
                
                #  gather session liquidity
                liquidity_nq = get_liquidity_values(symbol="NQ=F", candles_30m = historical_nq, test_date=test_date, liquidity_levels=liquidity_nq, current_start = current_30m_start, pdh = nq_pdh, pdl = nq_pdl)
                liquidity_es = get_liquidity_values(symbol="ES=F", candles_30m = historical_es, test_date=test_date, liquidity_levels=liquidity_es, current_start = current_30m_start, pdh = es_pdh, pdl = es_pdl)
                # print("liquidity es: ", liquidity_es)
                sweep_nq = None
                sweep_es = None
                nq_market_context.update_session_range(last_closed_nq["high"], last_closed_nq["low"], last_closed_nq["open"], last_closed_nq["close"])
            
                # update atr_usage based on daily atr and session range
                # nq_market_context.update_atr_usage(current_30m_start)
            
                
                # print(" es swing points high: ", es_valid_swing_highs)
                # print(" es swing points low: ", es_valid_swing_lows)
                # sweep detection and key level detection
                # sweep_nq = detect_30m_and_key_level_sweep(instrument = "NQ", valid_swing_highs=nq_valid_swing_highs, valid_swing_lows = nq_valid_swing_lows, candles_3m = nq_3m, last_closed_candle = last_closed_nq, key_levels = liquidity_nq, current_30m_start = current_30m_start)
                # sweep_es = detect_30m_and_key_level_sweep(instrument = "ES", valid_swing_highs=es_valid_swing_highs, valid_swing_lows = es_valid_swing_lows, candles_3m = es_3m, last_closed_candle = last_closed_es, key_levels = liquidity_es, current_30m_start = current_30m_start)
                # def detect_smt(
                #     nq_swings_high,
                #     nq_swings_low,
                #     es_swings_high,
                #     es_swings_low,
                #     current_nq_candle,
                #     current_es_candle,
                #     time_tolerance=timedelta(minutes=5)
                # ):
                # print('nq valid swing highs: ', nq_valid_swing_highs)
                # print('es valid swing highs: ', es_valid_swing_highs)
                # sweep detection and key level detection
                # sweep_nq = detect_30m_and_key_level_sweep(instrument = "NQ", valid_swing_highs=nq_valid_swing_highs, valid_swing_lows = nq_valid_swing_lows, candles_3m = nq_3m, last_closed_candle = last_closed_nq, key_levels = liquidity_nq, current_30m_start = current_30m_start)
                # sweep_es = detect_30m_and_key_level_sweep(instrument = "ES", valid_swing_highs=es_valid_swing_highs, valid_swing_lows = es_valid_swing_lows, candles_3m = es_3m, last_closed_candle = last_closed_es, key_levels = liquidity_es, current_30m_start = current_30m_start)
                
                # key_level_smt_result = detect_smt_key_levels(sweep_nq["swept_levels"] if sweep_nq else None,
                #     sweep_es["swept_levels"] if sweep_es else None)
                # smt_result = detect_30m_swing_smt(nq_valid_swing_highs, nq_valid_swing_lows, es_valid_swing_highs, es_valid_swing_lows, last_closed_nq, last_closed_es)
                # if smt_result is None:
                #     print('no smt result')
                # else:
                #     print("smt_result: ", smt_result)
                # if key_level_smt_result is None:
                #     print("no key level smt")
                # else:
                #     print("key_level_smt_result: ", key_level_smt_result)
                # detect smt at key level
                # nq_1h_filtered = filter_hourly_candles(nq["1h"], current_30m_start)
                # es_1h_filtered = filter_hourly_candles(es["1h"], current_30m_start)

                # detect smt at 1h
                # h1_smt = detect_hourly_smt_precise(nq_1h_filtered, es_1h_filtered)
                # print("smt on 1h: ", h1_smt)

                # detect htf at daily, 7h, 4h
                
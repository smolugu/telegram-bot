from alerts.execute import execute_trade_and_log
from data.models.candle_7h import SevenHourBuilder
from data.models.compression import detect_compression
from data.models.london_market_context import LondonMarketContextES, LondonMarketContext
from data.models.market_context import MarketContext
from data.models.nyam_market_context import NewYorkMarketContext
from data.sqlite.db import DB_FILE

from data.market_data import fetch_symbol_data_safe, filter_hourly_candles, get_current_contract, get_pdh_pdl_fixed_date
from data.models.reversal_setup import check_for_reversal_setup_confirmation
from helpers.date_time_helpers import to_ny_datetime
from helpers.sessions import get_futures_session, in_session
from data.models.setup_candidate import SetupCandidate
from data.models.ib_continuation_candidate import IBContinuationCandidate
from data.sqlite.db_functions import insert_trade, monitor_open_trades
from helpers.atr import calculate_daily_atr

from helpers.liquidity_levels import get_liquidity_values, reset_liquidity, update_compression_range_levels
from helpers.swing_points import filter_valid_swing_highs, filter_valid_swing_lows, get_valid_swings
from helpers.time_windows import get_active_window, is_blocked_time
from modules.imbalance_detector_old import detect_3m_fvg
from modules.nyam_context import get_morning_context
from modules.orchestrator import evaluate_7h_setup
from helpers.zones import get_7h_open_from_timestamp

from datetime import datetime, timedelta, timezone
from modules.ob_detector import detect_30m_order_block
from modules.smt_detector import detect_30m_swing_smt, detect_bearish_smt_key_levels, detect_bullish_smt_key_levels, detect_hourly_smt_precise, detect_smt_key_levels, summary_smt
from modules.sweep_detector import detect_30m_and_key_level_sweep, detect_key_liquidity_sweep, find_swing_highs, find_swing_lows
from modules.imbalance_detector import detect_3m_imbalance_inside_ob_candle
from alerts.alert_engine import send_telegram_alert_to_all
from alerts.alert_payload import build_trade_alert




def run_quick_backtest(test_date: str):

    print(f"Backtesting {test_date}")
    nq_contract = get_current_contract("NQ", test_date)
    es_contract = get_current_contract("ES", test_date)
    print("nq contract: ", nq_contract)
    print("es contract: ", es_contract)

    nq = fetch_symbol_data_safe(nq_contract)
    es = fetch_symbol_data_safe(es_contract)
    
    test_dt = datetime.fromisoformat(test_date).replace(tzinfo=timezone.utc)
    # start_dt = test_dt - timedelta(days=2)
    # end_dt = test_dt + timedelta(days=1)
    nq_pdh, nq_pdl = get_pdh_pdl_fixed_date(test_date, nq_contract)
    print("NQ PDh, PDl:", nq_pdh, nq_pdl)
    es_pdh, es_pdl = get_pdh_pdl_fixed_date(test_date, es_contract)
    print("ES PDh, PDl:", es_pdh, es_pdl)
    
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
    # nq_30m = nq["30m"]
    # nq_3m = nq["3m"]
    
    # es_30m = [c for c in es["30m"] if test_date in c["timestamp"]]
    # es_3m  = [c for c in es["3m"] if test_date in c["timestamp"]]
    es_30m = get_futures_session(es["30m"], test_date)
    es_3m = get_futures_session(es["3m"], test_date)
    # es_30m = [c for c in es["30m"] if start_dt <= datetime.fromisoformat(c["timestamp"]).astimezone(timezone.utc) < end_dt]
    # es_3m  = [c for c in es["3m"] if start_dt <= datetime.fromisoformat(c["timestamp"]).astimezone(timezone.utc) < end_dt]
    # es_30m = es["30m"]
    # es_3m = es["3m"]
    

    if not nq or not es:
        print("No data available.")
        return
    nq_30m_closes = {
        nq_30m[i]["timestamp"]: i
        for i in range(len(nq_30m))
    }
    nq_sell_candidate = SetupCandidate("buy_side", "NQ")
    nq_buy_candidate = SetupCandidate("sell_side", "NQ")
    es_sell_candidate = SetupCandidate("buy_side", "ES")
    es_buy_candidate = SetupCandidate("sell_side", "ES")
    

    nq_seven_hour_builder = SevenHourBuilder("NQ")
    es_seven_hour_builder = SevenHourBuilder("ES")
    nq_ib_candidate = IBContinuationCandidate("NQ")
    es_ib_candidate = IBContinuationCandidate("ES")
    checkval = ""

    
    current_window = None
    liquidity_nq = reset_liquidity()
    liquidity_es = reset_liquidity()
    
    nq_market_context = MarketContext("NQ")
    es_market_context = MarketContext("ES")
    nq_london_market_context = LondonMarketContext("NQ")
    es_london_market_context = LondonMarketContext("ES")
    nq_ny_market_context = NewYorkMarketContext("NQ")
    es_ny_market_context = NewYorkMarketContext("ES")
    
    
    nq_current_session_high = float("-inf")
    nq_current_session_low = float("inf")
    es_current_session_high = float("-inf")
    es_current_session_low = float("inf")
    
    #  looping through 30m candles from 18:00 futures start
    for candle_3m in nq_3m:
        ts = candle_3m["timestamp"]
        if ts in nq_30m_closes:
            i = nq_30m_closes[ts]
            print("Matching 30m candle found for 3m timestamp:", ts, "at index", i)
            if i == 0:
                print("resetting liquidity at : ", i, ts)
                liquidity_nq = reset_liquidity()
                liquidity_es = reset_liquidity()
                # print("resetting market context at : ", dt.hour)
                print("daily atrs before reset: ", nq_market_context.daily_atr, es_market_context.daily_atr)
                nq_market_context.reset()
                es_market_context.reset()
                nq_daily_atr = calculate_daily_atr(nq["30m"])
                es_daily_atr = calculate_daily_atr(es["30m"])
                
                # update market context with new daily atrs
                print("new atrs at 16:", nq_daily_atr, es_daily_atr)
                nq_market_context.set_daily_atr(nq_daily_atr)
                es_market_context.set_daily_atr(es_daily_atr)
            if i >= 3:

                print("\n---------------------------")
                t1 = datetime.fromisoformat(nq_30m[i-1]["timestamp"])
                t0 = datetime.fromisoformat(nq_30m[i-2]["timestamp"])
                delta = t1 - t0
                print("delta: ", delta, t1, t0)

                if delta > timedelta(minutes=30):
                    print("Irregular gap:", delta)

                # update weekly context at formation of new 1hr candle
                # weekly_context.update(candle_1h) 
                # weekly_context.update_cisd(prev, current)
                # weekly_context.update_fvg(c1, c2, c3)
                # prifile = weekly_context.infer_profile()
                # reset setup candidates at the start of each 7h window
                current_30m_start = nq_30m[i]["timestamp"]
                window_name = get_active_window(current_30m_start)
                
                if window_name != current_window:
                    print("🔄 New window detected:", window_name)
                    # reset only candidates whose alert is sent when a new window starts
                    # dont reset active candidates    
                    if nq_buy_candidate.alert_sent:
                        nq_buy_candidate.reset()
                    if nq_sell_candidate.alert_sent:
                        nq_sell_candidate.reset()
                    if es_buy_candidate.alert_sent:
                        es_buy_candidate.reset()
                    if es_sell_candidate.alert_sent:
                        es_sell_candidate.reset()
                    current_window = window_name

                print("Current window:", current_window)
                # previous 30m candle just closed
                last_closed_nq = nq_30m[i - 1]
                last_closed_es = es_30m[i - 1]

                print("i =", i, " | current 30m boundary at: ", current_30m_start)
                print("NQ Last closed:", last_closed_nq["timestamp"], "| Open: ", last_closed_nq["open"], "| Low: ", last_closed_nq["low"], "| High: ", last_closed_nq["high"], "| Close: ", last_closed_nq["close"])
                # print("ES Last closed:", last_closed_es["timestamp"], last_closed_es["high"], last_closed_es["low"])            
                # print("current 30m boundary at:", current_30m_start)

                dt = datetime.fromisoformat(last_closed_nq["timestamp"])
                dt_current = datetime.fromisoformat(current_30m_start)
                is_post_1AM_IB = in_session(current_30m_start, 2, 0, 8, 0)
                is_post_8AM_IB = in_session(current_30m_start, 9, 0, 15, 0 )
                
                # update currest_session for i=0, 1, 2 
                if (i == 3):
                    nq_current_session_high = max(nq_30m[0]["high"], nq_30m[1]["high"], nq_30m[2]["high"])
                    nq_current_session_low = min(nq_30m[0]["low"], nq_30m[1]["low"], nq_30m[2]["low"])
                    es_current_session_high = max(es_30m[0]["high"], es_30m[1]["high"], es_30m[2]["high"])
                    es_current_session_low = min(es_30m[0]["low"], es_30m[1]["low"], es_30m[2]["low"])
                    # update 18:00 candle with the initial 3 candles
                    nq_seven_hour_builder.update(nq_30m[0])
                    nq_seven_hour_builder.update(nq_30m[1])
                    nq_seven_hour_builder.update(nq_30m[2])
                    es_seven_hour_builder.update(es_30m[0])
                    es_seven_hour_builder.update(es_30m[1])
                    es_seven_hour_builder.update(es_30m[2])
                    nq_market_context.update_session_range(nq_30m[0]["high"], nq_30m[0]["low"], nq_30m[0]["open"], nq_30m[0]["close"])
                    nq_market_context.update_session_range(nq_30m[1]["high"], nq_30m[1]["low"], nq_30m[1]["open"], nq_30m[1]["close"])
                    nq_market_context.update_session_range(nq_30m[2]["high"], nq_30m[2]["low"], nq_30m[2]["open"], nq_30m[2]["close"])
                    es_market_context.update_session_range(es_30m[0]["high"], es_30m[0]["low"], es_30m[0]["open"], es_30m[0]["close"])
                    es_market_context.update_session_range(es_30m[1]["high"], es_30m[1]["low"], es_30m[1]["open"], es_30m[1]["close"])
                    es_market_context.update_session_range(es_30m[2]["high"], es_30m[2]["low"], es_30m[2]["open"], es_30m[2]["close"])
                    
                #  track current current day high and low (HOD, LOD)
                if last_closed_nq["high"] > nq_current_session_high:
                    nq_current_session_high = last_closed_nq["high"]
                if last_closed_nq["low"] < nq_current_session_low:
                    nq_current_session_low = last_closed_nq["low"]

                if last_closed_es["high"] > es_current_session_high:
                    es_current_session_high = last_closed_es["high"]
                if last_closed_es["low"] < es_current_session_low:
                    es_current_session_low = last_closed_es["low"]
                # print("nq HOD:", nq_current_session_high, "nq LOD: ", nq_current_session_low)
                # print("es HOD:", es_current_session_high, "es LOD: ", es_current_session_low)
                # update 7hr candle through seven hour builder
                # he 18:00 7hr candle is not complete with the first 3 30m candles
                nq_seven_hour_builder.update(last_closed_nq)
                es_seven_hour_builder.update(last_closed_es)
                
                
                # get liquidity levels at end of each 30m candle
                historical_nq = nq_30m[:i]
                historical_es = es_30m[:i]
                #  gather session liquidity
                liquidity_nq = get_liquidity_values(symbol= nq_contract, candles_30m = historical_nq, test_date=test_date, liquidity_levels=liquidity_nq, current_start = current_30m_start, pdh = nq_pdh, pdl = nq_pdl)
                liquidity_es = get_liquidity_values(symbol= es_contract, candles_30m = historical_es, test_date=test_date, liquidity_levels=liquidity_es, current_start = current_30m_start, pdh = es_pdh, pdl = es_pdl)

                # update london context with IBS
                if dt.hour == 1 and dt.minute == 30:
                    nq_london_market_context.set_18_1am_ibs(nq_seven_hour_builder.candles["6PM"].values(),nq_seven_hour_builder.candles["1AM"].values())
                    es_london_market_context.set_18_1am_ibs(es_seven_hour_builder.candles["6PM"].values(),es_seven_hour_builder.candles["1AM"].values())
                    print("nq london structure: ", nq_london_market_context.structure)
                    print("es london structure: ", es_london_market_context.structure)
                    
                # update london context with 2AM 4hr IB
                if dt.hour == 2 and dt.minute == 00:
                    nq_london_market_context.set_2am_ib(last_closed_nq)
                    es_london_market_context.set_2am_ib(last_closed_es)
                    print("nq 2am IB: ", nq_london_market_context.ib_2)
                    print("es 2am IB: ", es_london_market_context.ib_2)
                
                # update london context
                if dt.hour > 1 and dt.hour < 8:
                    nq_london_market_context.update(last_closed_nq, liquidity_nq)
                    es_london_market_context.update(last_closed_es, liquidity_es)
                
                # update new york context with IBs
                if dt.hour == 8 and dt.minute == 30:
                    nq_ny_market_context.set_8am_ib(nq_seven_hour_builder.candles, nq_london_market_context.ib_18, nq_london_market_context.ib_1)
                    es_ny_market_context.set_8am_ib(es_seven_hour_builder.candles, es_london_market_context.ib_18, es_london_market_context.ib_1)
                    print("test 1: ", nq_ny_market_context.structure)
                    print("rest es: ", es_ny_market_context.structure)
                if dt.hour == 10 and dt.minute == 0:
                    nq_ny_market_context.set_10am_ib(last_closed_nq)
                    es_ny_market_context.set_10am_ib(last_closed_es)
                    print("nq 10am IB: ", nq_ny_market_context. ib_10)
                    print("es 10am IB: ", es_ny_market_context. ib_10)
                # update market context for NQ and ES
                nq_market_context.update_session_range(last_closed_nq["high"], last_closed_nq["low"], last_closed_nq["open"], last_closed_nq["close"])
                es_market_context.update_session_range(last_closed_es["high"], last_closed_es["low"], last_closed_es["open"], last_closed_es["close"])
                # update Newyork Context
                if dt.hour > 8 and dt.hour < 15:
                    nq_ny_market_context.update(last_closed_nq, liquidity_nq)
                    es_ny_market_context.update(last_closed_es, liquidity_es)
                    print("nq market structure ny at each 30m candle: ", nq_ny_market_context.structure)
                    print("es market structure ny at each 30m candle: ", es_ny_market_context.structure)
                    
                # update atr_usage based on daily atr and session range
                nq_market_context.update_atr_usage(current_30m_start, last_closed_nq["close"])
                es_market_context.update_atr_usage(current_30m_start, last_closed_es["close"])
                print("nq atr: ", nq_market_context.get_atr_info())
                print("es atr: ", es_market_context.get_atr_info())
                
                if nq_market_context.ib_ready:
                    nq_market_context.update_ib_acceptance(last_closed_nq["close"])
                    es_market_context.update_ib_acceptance(last_closed_es["close"])
                    nq_market_context.compute_expansion_metrics(last_closed_nq["timestamp"])
                    es_market_context.compute_expansion_metrics(last_closed_es["timestamp"])
                    nq_market_context.update_relative_expansion(es_market_context.expansion_ratio)
                    es_market_context.update_relative_expansion(nq_market_context.expansion_ratio)
                    # ideally detect_day_type() function should run only when needed at 10:00, 10:30, 11:00 and 11:30
                    # which reduces unnecessary checks
                    nq_day_type = nq_market_context.detect_day_type(last_closed_nq["timestamp"], current_30m_start, last_closed_nq["close"])
                    es_day_type = es_market_context.detect_day_type(last_closed_es["timestamp"], current_30m_start, last_closed_nq["close"])
                    print("nq day type: ", nq_day_type)
                    print("es dat type: ", es_day_type)
                # call set_ib towards the end so ib_ready is true for the next candle
                # populate IB for NQ and ES
                if dt_current.hour == 9:
                    # update Ib setup 
                    nq_ib_candidate.update(nq_seven_hour_builder.candles["8AM"].values())
                    es_ib_candidate.update(es_seven_hour_builder.candles["8AM"].values())
                    nq_market_context.set_ib(nq_ib_candidate.ib_high, nq_ib_candidate.ib_low)
                    es_market_context.set_ib(es_ib_candidate.ib_high, es_ib_candidate.ib_low)
                
                # print("NQ Market Context: ", nq_market_context.values())
                # print("ES Market Context: ", es_market_context.values())
                
                #  check if there is already a sweep
                sweep_nq_highs = None
                sweep_nq_lows = None
                sweep_es_highs = None
                sweep_es_lows = None
                # get valid swing points and key levels and send to detect_30m_key_level_sweep
                nq_valid_swing_lows, nq_valid_swing_highs = get_valid_swings(historical_nq, i)
                es_valid_swing_lows, es_valid_swing_highs = get_valid_swings(historical_es, i)
                # sweep detection 30m Swing points
                sweep_nq_highs, sweep_nq_lows = detect_30m_and_key_level_sweep(instrument = "NQ", valid_swing_highs=nq_valid_swing_highs, valid_swing_lows = nq_valid_swing_lows, candles_3m = nq_3m, last_closed_candle = last_closed_nq, key_levels = liquidity_nq, current_30m_start = current_30m_start)
                sweep_es_highs, sweep_es_lows = detect_30m_and_key_level_sweep(instrument = "ES", valid_swing_highs=es_valid_swing_highs, valid_swing_lows = es_valid_swing_lows, candles_3m = es_3m, last_closed_candle = last_closed_es, key_levels = liquidity_es, current_30m_start = current_30m_start)
                
                # sweep detection at key levels
                sweep_nq_highs_key_level, sweep_nq_lows_key_level = detect_key_liquidity_sweep(instrument = "NQ", key_levels = liquidity_nq, candles_3m = nq_3m, last_closed_candle = last_closed_nq, current_30m_start = current_30m_start)
                sweep_es_highs_key_level, sweep_es_lows_key_level = detect_key_liquidity_sweep(instrument = "ES", key_levels = liquidity_es, candles_3m = es_3m, last_closed_candle = last_closed_es, current_30m_start = current_30m_start)
                print("sweep_nq_highs: ", sweep_nq_highs)
                print("sweep_nq_lows: ", sweep_nq_lows)
                print("sweep_es_highs: ", sweep_es_highs)
                print("sweep_es_lows: ", sweep_es_lows)
                print("sweep_nq_highs_key_level: ", sweep_nq_highs_key_level)
                print("sweep_nq_lows_key_level: ", sweep_nq_lows_key_level)
                print("sweep_es_highs_key_level: ", sweep_es_highs_key_level)
                print("sweep_es_lows_key_level: ", sweep_es_lows_key_level)

                # TODO: if there is a sweep then check for compression otherwise skip
                # filter sweeps using compression logic
                
                is_compression_nq = False
                is_compression_es = False
                compression_range_nq = None
                compression_range_es = None
                compression_sweep_data_es = None
                compression_sweep_data_nq = None
                
                # detect compression values at each beginning of 30m cycle
                # use the compression range to invalidate sweeps
                is_compression_nq, compression_flags_nq, compression_range_nq = detect_compression(nq_seven_hour_builder.candles)
                is_compression_es, compression_flags_es, compression_range_es = detect_compression(es_seven_hour_builder.candles)
                # compression is stored in london_context and newyork_context
                # get compression and compression range based on london and newyork context
                if is_post_1AM_IB:
                    is_compression_nq, compression_range_nq, compression_sweep_data_nq = nq_london_market_context.get_compression_data()
                    is_compression_es, compression_range_es, compression_sweep_data_es = es_london_market_context.get_compression_data()
                    if dt.hour == 1 and dt.minute == 30:
                        if is_compression_nq or is_compression_es:
                            print("resetting previous candidates as we have compression at 1am IB")
                            nq_buy_candidate.reset()
                            nq_sell_candidate.reset()
                            es_buy_candidate.reset()
                            es_sell_candidate.reset()
                    # we have compression range, update liquidity key levels if no talready there
                    update_compression_range_levels(liquidity_nq, compression_range_nq, "1AM")
                    update_compression_range_levels(liquidity_es, compression_range_es, "1AM")
                    print("nq_liquidity_rr: ", liquidity_nq)
                    print("es_liquidity_rr: ", liquidity_es)
                    # print("li_re: ", li_re)
                    # liquidity_nq = li_re
                    # print("nq_liquidity: ", liquidity_nq)
                    
                if is_post_8AM_IB:
                    is_compression_nq, compression_range_nq, compression_sweep_data_nq = nq_ny_market_context.get_compression_data()
                    is_compression_es, compression_range_es, compression_sweep_data_es = es_ny_market_context.get_compression_data()
                    update_compression_range_levels(liquidity_nq, compression_range_nq, "8AM")
                    update_compression_range_levels(liquidity_es, compression_range_es, "8AM")
                    
                is_post_1am_8am_ibs = is_post_8AM_IB or is_post_1AM_IB

                print("is post 8am: ", is_post_8AM_IB)
                print("is post 1am: ", is_post_1AM_IB)
                print("compression data nq: ", is_compression_nq, compression_range_nq, compression_sweep_data_nq)
                print("compression data es: ", is_compression_es, compression_range_es, compression_sweep_data_es)

                # flow for types of compression on both nq and es
                # 1. if both nq and es strong compression => require inducement
                # 2. either is weak or both weak => no inducement, strong displacement with smt
                # 3. sandwich => require inducement
                # 4. partial_overlap_neutral => no inducement required, sweep above rebalance level or between rebalance level and range high or low
                # 5. if strong compression, expect one more sweep, inducement
                # 6. no compression trend day => atr exhaustion
                # 7. partial overlap => no inducement, smt + exhaustion + key level
                
                # store compression data in market context as they form and dont change
                # compression range is the latest compression range
                nq_market_context.update_compression_info(compression_flags_nq, compression_range_nq)
                es_market_context.update_compression_info(compression_flags_es, compression_range_es)
                # print("check last closed nq: ", last_closed_nq)
                # print("check compression range nq: ", compression_range_nq)
                nq_sweep_rejected_highs = True
                es_sweep_rejected_highs = True
                nq_sweep_rejected_lows = True   
                es_sweep_rejected_lows = True
                invalidate_sweeps_highs = False
                invalidate_sweeps_lows = False
                # if compression - inside 1am ib inside 18 ib
                
                # nq_compression_or_recompression = compression_flags_nq["nested_1_in_18"] or compression_flags_nq["engulfing_1_over_18"]
                # es_compression_or_recompression = compression_flags_es["nested_1_in_18"] or compression_flags_es["engulfing_1_over_18"]
                # compression or re-compression at 1am IB, trade only extremes
                if is_post_1am_8am_ibs and is_compression_nq and (sweep_nq_highs or sweep_nq_highs_key_level) and last_closed_nq["open"] > compression_range_nq["low"] and last_closed_nq["open"] < compression_range_nq["high"]:
                    # also captures staircase_overlap_bearish and staircase_overlap_bullish when candle is inside compression zones
                    # below we have a separate block for sweep outside compression range and candle outside compression range
                    # nq_swept_level = max(sweep_nq_highs["sweep_level"], sweep_nq_highs_key_level["sweep_level"]) if sweep_nq_highs and sweep_nq_highs_key_level else (sweep_nq_highs["sweep_level"] if sweep_nq_highs else sweep_nq_highs_key_level["sweep_level"])
                    print("101:")
                    invalidate_sweeps_highs = True
                    nq_swept_level = (
                        max(sweep_nq_highs["sweep_level"], sweep_nq_highs_key_level["sweep_level"]) if sweep_nq_highs is not None and sweep_nq_highs_key_level is not None
                        else sweep_nq_highs["sweep_level"] if sweep_nq_highs is not None
                        else sweep_nq_highs_key_level["sweep_level"] if sweep_nq_highs_key_level is not None
                        else None
                    )
                    if nq_swept_level < compression_range_nq["high"] and last_closed_nq["high"] < compression_range_nq["high"]:
                        print("NQ Sweep at highs rejected due to compression. invalidating sweep inside compression range")
                        # sweep_nq_highs = None
                        # sweep_nq_highs_key_level = None
                        # here rejected highs implies price is still inside compression range
                        nq_sweep_rejected_highs = True
                    elif compression_sweep_data_nq["count_high"] >= 2:
                        # here count_high == 1 => inducecment level
                        # count_high >=2 => sweep of inducement level => actual move
                        nq_sweep_rejected_highs = False
                    else:
                        # here nq swept keylevel and compression high, inducement is not confirmed
                        # disallow sweep if the breakout is less than 10 points on nq and less than 
                        # 3 points on ES
                        nq_sweep_rejected_highs = False
                        if abs(last_closed_nq["high"] - compression_range_nq["high"]) < 10:
                            print("NQ sweep at highs accepted but price near compression range. exercise caution")
                            nq_sweep_rejected_highs = True
                if is_post_1am_8am_ibs and is_compression_es and (sweep_es_highs or sweep_es_highs_key_level) and last_closed_es["open"] > compression_range_es["low"] and last_closed_es["open"] < compression_range_es["high"]:
                    # es_swept_level = max(sweep_es_highs["sweep_level"], sweep_es_highs_key_level["sweep_level"]) if sweep_es_highs and sweep_es_highs_key_level else (sweep_es_highs["sweep_level"] if sweep_es_highs else sweep_es_highs_key_level["sweep_level"])
                    invalidate_sweeps_highs = True
                    print("102:")

                    print("compre3: ", compression_sweep_data_es)
                    es_swept_level = (
                        max(sweep_es_highs["sweep_level"], sweep_es_highs_key_level["sweep_level"]) if sweep_es_highs is not None and sweep_es_highs_key_level is not None
                        else sweep_es_highs["sweep_level"] if sweep_es_highs is not None
                        else sweep_es_highs_key_level["sweep_level"] if sweep_es_highs_key_level is not None
                        else None
                    )
                    if es_swept_level < compression_range_es["high"] and last_closed_es["high"] < compression_range_es["high"]:
                        print("ES Sweep at highs rejected due to compression. invalidating sweep inside compression range")
                        # sweep_es_highs = None
                        # sweep_es_highs_key_level = None
                        es_sweep_rejected_highs = True
                    elif compression_sweep_data_es["count_high"] >= 2:
                        es_sweep_rejected_highs = False
                    else:
                        es_sweep_rejected_highs = False
                        if abs(last_closed_es["high"] - compression_range_es["high"]) < 3:               
                            print("ES sweep at highs accepted but price near compression range. exercise caution")
                            es_sweep_rejected_highs = True

                #  if both es and nq sweeps inside compression, invalidate sweeps
                #  store smt with sweeper information
                if invalidate_sweeps_highs:
                    print("103:")
                    if es_sweep_rejected_highs and nq_sweep_rejected_highs:
                        print("Both NQ and ES sweeps at highs rejected due to compression. no smt, invalidating all sweeps inside compression range")
                        sweep_nq_highs = None
                        sweep_nq_highs_key_level = None
                        sweep_es_highs = None
                        sweep_es_highs_key_level = None
                    elif es_sweep_rejected_highs and not nq_sweep_rejected_highs:
                        # smt with NQ as sweeper
                        nq_ny_market_context.sweep["is_smt_high"] = True
                        es_ny_market_context.sweep["is_smt_high"] = True
                        nq_ny_market_context.sweep["sweeper_high"] = "NQ"
                        es_ny_market_context.sweep["sweeper_high"] = "NQ"
                    elif nq_sweep_rejected_highs and not es_sweep_rejected_highs:
                        # smt with NQ as sweeper
                        nq_ny_market_context.sweep["is_smt_high"] = True
                        es_ny_market_context.sweep["is_smt_high"] = True
                        nq_ny_market_context.sweep["sweeper_high"] = "ES"
                        es_ny_market_context.sweep["sweeper_high"] = "ES"
                    else:
                        # valid sweep with no smt
                        nq_ny_market_context.sweep["is_smt_high"] = False
                        es_ny_market_context.sweep["is_smt_high"] = False
                        nq_ny_market_context.sweep["sweeper_high"] = None
                        es_ny_market_context.sweep["sweeper_high"] = None
                    

                if is_post_1am_8am_ibs and is_compression_nq and (sweep_nq_lows or sweep_nq_lows_key_level) and last_closed_nq["open"] > compression_range_nq["low"] and last_closed_nq["open"] < compression_range_nq["high"]:
                    print("sweep_nq_lows: ", sweep_nq_lows)
                    print("104:")
                    if sweep_nq_lows is not None:
                        print("sweep_nq_lows: ", sweep_nq_lows["sweep_level"])
                    print("sweep_nq_lows_key_level: ", sweep_nq_lows_key_level)
                    print("last_closed_nq: ", last_closed_nq)
                    print("compression_range_nq: ", compression_range_nq)
                    # nq_swept_level = min(sweep_nq_lows["sweep_level"], sweep_nq_lows_key_level["sweep_level"]) if sweep_nq_lows and sweep_nq_lows_key_level else (sweep_nq_lows["sweep_level"] if sweep_nq_lows else sweep_nq_lows_key_level["sweep_level"])
                    invalidate_sweeps_lows = True
                    nq_swept_level = (
                        min(sweep_nq_lows["sweep_level"], sweep_nq_lows_key_level["sweep_level"])
                        if sweep_nq_lows is not None and sweep_nq_lows_key_level is not None
                        else sweep_nq_lows["sweep_level"] if sweep_nq_lows is not None
                        else sweep_nq_lows_key_level["sweep_level"] if sweep_nq_lows_key_level is not None
                        else None
                    )
                    print("nq swept level 1: ", nq_swept_level)
                    print("com r low 2: ", compression_range_nq["low"])
                    print("last closed low 3: ", last_closed_nq["low"])
                    
                    if nq_swept_level > compression_range_nq["low"] and last_closed_nq["low"] > compression_range_nq["low"]:
                        print("NQ Sweep at lows rejected due to compression. invalidating sweep inside compression range")
                        print("section 4")
                        # sweep_nq_lows = None
                        # sweep_nq_lows_key_level = None
                        nq_sweep_rejected_lows = True
                    elif compression_sweep_data_nq["count_low"] >= 2:
                        print("section 5")
                        # if sweep is previous candle low then be cautious, wait for displacement or one more sweep
                        prev_to_last_closed_nq = nq_30m[i - 2]
                        print("prev_to_last_closed_nq: ", prev_to_last_closed_nq["low"])
                        if nq_swept_level == prev_to_last_closed_nq["low"]:
                            print("section 5.1")
                            nq_sweep_rejected_lows = True
                        else:
                            nq_sweep_rejected_lows = False
                    else:
                        print("section 6")
                        nq_sweep_rejected_lows = False
                        print("compression_range_nq: ", compression_range_nq)
                        print("last_closed_nq: ", last_closed_nq["low"])
                        if abs(last_closed_nq["low"] - compression_range_nq["low"]) < 10:
                            print("section 7")
                            print("NQ sweep at lows accepted but price near compression range. exercise caution: ", abs(last_closed_nq["low"] - compression_range_nq["low"]))
                            nq_sweep_rejected_lows = True
                print("section 8: nq_sweep_rejected_lows: ", nq_sweep_rejected_lows)
                if is_post_1am_8am_ibs and is_compression_es and (sweep_es_lows or sweep_es_lows_key_level) and last_closed_es["open"] > compression_range_es["low"] and last_closed_es["open"] < compression_range_es["high"]:
                    # es_swept_level = min(sweep_es_lows["sweep_level"], sweep_es_lows_key_level["sweep_level"]) if sweep_es_lows and sweep_es_lows_key_level else (sweep_es_lows["sweep_level"] if sweep_es_lows else sweep_es_lows_key_level["sweep_level"])
                    invalidate_sweeps_lows = True
                    print("105:")
                    es_swept_level = (
                        min(sweep_es_lows["sweep_level"], sweep_es_lows_key_level["sweep_level"])
                        if sweep_es_lows is not None and sweep_es_lows_key_level is not None
                        else sweep_es_lows["sweep_level"] if sweep_es_lows is not None
                        else sweep_es_lows_key_level["sweep_level"] if sweep_es_lows_key_level is not None
                        else None
                    )
                    if es_swept_level > compression_range_es["low"] and last_closed_es["low"] > compression_range_es["low"]:
                        print("ES Sweep at lows rejected due to compression. invalidating sweep inside compression range")
                        # sweep_es_lows = None
                        # sweep_es_lows_key_level = None
                        es_sweep_rejected_lows = True
                    elif compression_sweep_data_es["count_low"] >= 2:
                        es_sweep_rejected_highs = False
                    else:
                        es_sweep_rejected_lows = False
                        print("last_closed_es low: ", last_closed_es["low"], "compression_range_es low: ", compression_range_es["low"])
                        if abs(last_closed_es["low"] - compression_range_es["low"]) < 3:
                            print("last_closed_es low: ", last_closed_es["low"], "compression_range_es low: ", compression_range_es["low"])
                            print("ES sweep at lows accepted but price near compression range. exercise caution", abs(last_closed_es["low"] - compression_range_es["low"]))
                            es_sweep_rejected_lows = True
                #  if both es and nq sweeps at lows inside compression, invalidate sweeps
                if invalidate_sweeps_lows:
                    print("106:")
                    if es_sweep_rejected_lows and nq_sweep_rejected_lows:
                        print("Both NQ and ES sweeps at lows rejected due to compression. invalidating all sweeps inside compression range")
                        sweep_nq_lows = None
                        sweep_nq_lows_key_level = None
                        sweep_es_lows = None
                        sweep_es_lows_key_level = None
                    elif es_sweep_rejected_lows and not nq_sweep_rejected_lows:
                        # smt with NQ as sweeper
                        nq_ny_market_context.sweep["is_smt_low"] = True
                        es_ny_market_context.sweep["is_smt_low"] = True
                        nq_ny_market_context.sweep["sweeper_low"] = "NQ"
                        es_ny_market_context.sweep["sweeper_low"] = "NQ"
                    elif nq_sweep_rejected_lows and not es_sweep_rejected_lows:
                        # smt with ES as sweeper
                        nq_ny_market_context.sweep["is_smt_low"] = True
                        es_ny_market_context.sweep["is_smt_low"] = True
                        nq_ny_market_context.sweep["sweeper_low"] = "ES"
                        es_ny_market_context.sweep["sweeper_low"] = "ES"
                    else:
                        # valid sweep with no smt
                        nq_ny_market_context.sweep["is_smt_low"] = False
                        es_ny_market_context.sweep["is_smt_low"] = False
                        nq_ny_market_context.sweep["sweeper_low"] = None
                        es_ny_market_context.sweep["sweeper_low"] = None
                # ----------------------------------
                nq_sweep_rejected_highs = True
                es_sweep_rejected_highs = True
                nq_sweep_rejected_lows = True   
                es_sweep_rejected_lows = True
                invalidate_sweeps_highs = False
                invalidate_sweeps_lows = False
                if is_post_1am_8am_ibs and is_compression_nq and nq_ny_market_context.structure["ib_relationship"] == "partial_overlap_bullish_neutral" and compression_sweep_data_nq["is_valid_sweep"]:
                    nq_sweep_rejected_lows = False
                    invalidate_sweeps_lows = True
                if is_post_1am_8am_ibs and is_compression_es and es_ny_market_context.structure["ib_relationship"] == "partial_overlap_bullish_neutral" and compression_sweep_data_es["is_valid_sweep"]:
                    es_sweep_rejected_lows = False
                    invalidate_sweeps_lows = True
                
                if is_post_1am_8am_ibs and is_compression_nq and nq_ny_market_context.structure["ib_relationship"] == "partial_overlap_bearish_neutral" and compression_sweep_data_nq["is_valid_sweep"]:
                    nq_sweep_rejected_highs = False
                    invalidate_sweeps_highs = True
                if is_post_1am_8am_ibs and is_compression_es and es_ny_market_context.structure["ib_relationship"] == "partial_overlap_bearish_neutral" and compression_sweep_data_es["is_valid_sweep"]:
                    es_sweep_rejected_highs = False
                    invalidate_sweeps_highs = True
                
                if invalidate_sweeps_lows:
                    print("107:")
                    if nq_sweep_rejected_lows and es_sweep_rejected_lows:
                        # invalidate sweeps
                        print("partial_overlap_bullish_neutral not ready")
                        print("Both NQ and ES sweeps at lows rejected due to compression. invalidating all sweeps inside compression range")
                        sweep_nq_lows = None
                        sweep_nq_lows_key_level = None
                        sweep_es_lows = None
                        sweep_es_lows_key_level = None
                    elif nq_sweep_rejected_lows and not es_sweep_rejected_lows:
                        # smt with ES as sweeper
                        nq_ny_market_context.sweep["is_smt_low"] = True
                        es_ny_market_context.sweep["is_smt_low"] = True
                        nq_ny_market_context.sweep["sweeper_low"] = "ES"
                        es_ny_market_context.sweep["sweeper_low"] = "ES"
                    elif es_sweep_rejected_lows and not nq_sweep_rejected_lows:
                        # smt with NQ as sweeper
                        nq_ny_market_context.sweep["is_smt_low"] = True
                        es_ny_market_context.sweep["is_smt_low"] = True
                        nq_ny_market_context.sweep["sweeper_low"] = "NQ"
                        es_ny_market_context.sweep["sweeper_low"] = "NQ"
                    else:
                        # valid sweep with no smt
                        nq_ny_market_context.sweep["is_smt_low"] = False
                        es_ny_market_context.sweep["is_smt_low"] = False
                        nq_ny_market_context.sweep["sweeper_low"] = None
                        es_ny_market_context.sweep["sweeper_low"] = None
                
                if invalidate_sweeps_highs:
                    print("108:")
                    if nq_sweep_rejected_highs and es_sweep_rejected_highs:
                        # invalidate sweeps
                        print("partial_overlap_bearish_neutral not ready")
                        print("Both NQ and ES sweeps at lows rejected due to compression. invalidating all sweeps inside compression range")
                        sweep_nq_highs = None
                        sweep_nq_highs_key_level = None
                        sweep_es_highs = None
                        sweep_es_highs_key_level = None
                    elif nq_sweep_rejected_highs and not es_sweep_rejected_highs:
                        # smt with ES as sweeper
                        nq_ny_market_context.sweep["is_smt_high"] = True
                        es_ny_market_context.sweep["is_smt_high"] = True
                        nq_ny_market_context.sweep["sweeper_high"] = "ES"
                        es_ny_market_context.sweep["sweeper_high"] = "ES"
                    elif es_sweep_rejected_lows and not nq_sweep_rejected_lows:
                        # smt with NQ as sweeper
                        nq_ny_market_context.sweep["is_smt_high"] = True
                        es_ny_market_context.sweep["is_smt_high"] = True
                        nq_ny_market_context.sweep["sweeper_high"] = "NQ"
                        es_ny_market_context.sweep["sweeper_high"] = "NQ"
                    else:
                        # valid sweep with no smt
                        nq_ny_market_context.sweep["is_smt_high"] = False
                        es_ny_market_context.sweep["is_smt_high"] = False
                        nq_ny_market_context.sweep["sweeper_high"] = None
                        es_ny_market_context.sweep["sweeper_high"] = None


                
                # block for ib_relationship is directional partial_overlap directional
                    # Rule: Structure
                    # invalidate sweeps at lows, market is already directional and is compressing so a ping flush is high probable
                
                invalidate_sweeps = False
                # invalidate if either nq or es is a staircase (each IB overlapping others, strong compression)
                if nq_ny_market_context.structure["is_staircase"] or es_ny_market_context.structure["is_staircase"]:
                    invalidate_sweeps = True

                if invalidate_sweeps and is_post_1am_8am_ibs and is_compression_nq and nq_ny_market_context.structure["ib_relationship"] == "partial_overlap_bullish":
                    # invalidate nq sweep lows
                    sweep_nq_lows = None
                    sweep_nq_lows_key_level = None
                    
                if invalidate_sweeps and is_post_1am_8am_ibs and is_compression_es and es_ny_market_context.structure["ib_relationship"] == "partial_overlap_bullish":
                    # invalidate es sweep lows
                    sweep_es_lows = None
                    sweep_es_lows_key_level = None
                if invalidate_sweeps and is_post_1am_8am_ibs and is_compression_nq and nq_ny_market_context.structure["ib_relationship"] == "partial_overlap_bearish":
                    # invalidate nq sweep highs
                    sweep_nq_highs = None
                    sweep_nq_highs_key_level = None
                if invalidate_sweeps and is_post_1am_8am_ibs and is_compression_es and es_ny_market_context.structure["ib_relationship"] == "partial_overlap_bearish":
                    # invalidate es sweep highs
                    sweep_es_highs = None
                    sweep_es_highs_key_level = None

                # block where there is gap on both directional partial overlap
                # allow reversal sweeps at rebalance levels
                if not nq_ny_market_context.structure["is_staircase"] and not es_ny_market_context.structure["is_staircase"]:
                    invalidate_sweeps = False

                # if is_post_1am_8am_ibs and is_compression_nq and (sweep_nq_highs or sweep_nq_highs_key_level) and nq_ny_market_context.structure["ib_relationship"] == "staircase_overlap_bearish" and last_closed_nq["open"] > compression_range_nq["high"]:
                #     # staricase compression and candle above compression range high
                #     # sweep is valid
                #     print("NQ: staircase_overlap_bearish - location above - valid sweep")
                
                # if is_post_1am_8am_ibs and is_compression_nq and (sweep_nq_lows or sweep_nq_lows_key_level) and nq_ny_market_context.structure["ib_relationship"] == "staircase_overlap_bullish" and last_closed_nq["open"] < compression_range_nq["low"]:
                #     # staricase compression and candle below compression range low
                #     # sweep is valid
                #     print("NQ: staircase_overlap_bullish - location below - valid sweep")
                
                # if is_post_1am_8am_ibs and is_compression_es and (sweep_es_highs or sweep_es_highs_key_level) and es_ny_market_context.structure["ib_relationship"] == "staircase_overlap_bearish" and last_closed_es["open"] > compression_range_es["high"]:
                #     # staricase compression and candle above compression range high
                #     # sweep is valid
                #     print("ES: staircase_overlap_bearish - location above - valid sweep")
                
                # if is_post_1am_8am_ibs and is_compression_es and (sweep_es_lows or sweep_es_lows_key_level) and es_ny_market_context.structure["ib_relationship"] == "staircase_overlap_bullish" and last_closed_es["open"] < compression_range_es["low"]:
                #     # staricase compression and candle below compression range low
                #     # sweep is valid
                #     print("ES: staircase_overlap_bullish - location below - valid sweep")
                
            
                
                # compression -> expansion -> re-compression
                # 1am Ib is engulfing - reset candidates. price will go into re-compression and then manipulate 
                # and expand. here is we are basically ignoring continuation signals from the first 7hr candle if there is compression detected because of the potential for manipulation and false breakouts. we will wait for a clean breakout from the compression range and then look for continuation signals. this is especially important for the first 7hr candle because it sets the tone for the rest of the day and is more likely to be manipulated. by ignoring continuation signals from the first 7hr candle in a compression scenario, we can avoid getting caught in false breakouts and increase our chances of identifying genuine continuation setups later in the day when the price breaks out of the compression range.
                if (compression_flags_nq["engulfing_1_over_18"] or compression_flags_es["engulfing_1_over_18"]) and dt_current.hour == 2 and dt_current.minute == 0:
                    # at the formation of engulfing 1am IB reset all candidates and current candle sweeps
                    # this is not true. the price movement can be directional in the direction of IB. 
                    # so 1am can sweep one side and also sweep the other side with strong body which
                    # can continue in IB direction when there is a strong body or not recompression
                    print("Engulfing compression detected in NQ. rejecting all sweeps for the first 7hr candle to avoid false breakouts and manipulation. waiting for a clean breakout from the compression range before looking for continuation signals.")
                    print("commenting")
                    # sweep_nq_highs = None
                    # sweep_nq_highs_key_level = None
                    # sweep_nq_lows = None
                    # sweep_nq_lows_key_level = None
                    # sweep_es_highs = None
                    # sweep_es_highs_key_level = None
                    # sweep_es_lows = None
                    # sweep_es_lows_key_level = None
                    # nq_buy_candidate.reset()
                    # nq_sell_candidate.reset()
                    # es_buy_candidate.reset()
                    # es_sell_candidate.reset()
                # sweep detection at previous hour highs and lows

                # if not sweep_nq and not sweep_es:
                #     continue
                # if sweep_nq and not sweep_nq["sweep_key_level"]:
                #     continue
                # print("Liquidity levels NQ:", liquidity_nq)
                # print("Liquidity levels ES:", liquidity_es)
                # print("nq seven hour candle: ", nq_seven_hour_builder.candles["1AM"].values())
                # print("nq seven hour candle: ", nq_seven_hour_builder.candles["8AM"].values())
                # print("nq seven hour candle: ", nq_seven_hour_builder.candles["3PM"].values())
                
                # capture key level sweep separately, 1hr sweep

                # if sweep_nq and sweep_nq["sweep_key_level"]:
                # if sweep_nq_highs or sweep_nq_key_level_highs
                if sweep_nq_highs or sweep_nq_highs_key_level:
                    if sweep_nq_highs_key_level:
                        print("SWEEP DETECTED NQ Highs at Key Level:", sweep_nq_highs_key_level)
                        nq_sell_candidate.register_sweep(sweep_nq_highs_key_level["timestamp"], sweep_nq_highs_key_level["sweep_candle_high"], sweep_nq_highs_key_level["sweep_time"], sweep_nq_highs_key_level["sweep_and_ob_confirmed"], sweep_nq_highs_key_level["sweep_and_ob_entry"], sweep_nq_highs_key_level["sweep_and_ob_ce_confirmed"], sweep_nq_highs_key_level["sweep_and_ob_ce_entry"], sweep_nq_highs_key_level["sweep_and_ob_confirmation_timestamp"], sweep_nq_highs_key_level["swept_levels"], "NQ", sweep_nq_highs_key_level["sweep_type"], sweep_nq_highs_key_level["sweep_candle"])
                    elif sweep_nq_highs:
                        print("SWEEP DETECTED NQ Highs:", sweep_nq_highs)
                        nq_sell_candidate.register_sweep(sweep_nq_highs["timestamp"], sweep_nq_highs["sweep_candle_high"], sweep_nq_highs["sweep_time"], sweep_nq_highs["sweep_and_ob_confirmed"], sweep_nq_highs["sweep_and_ob_entry"], sweep_nq_highs["sweep_and_ob_ce_confirmed"], sweep_nq_highs["sweep_and_ob_ce_entry"], sweep_nq_highs["sweep_and_ob_confirmation_timestamp"], sweep_nq_highs["swept_levels"], "NQ", sweep_nq_highs["sweep_type"], sweep_nq_highs["sweep_candle"])
                
                if sweep_nq_lows or sweep_nq_lows_key_level:
                    if sweep_nq_lows_key_level:
                        print("SWEEP DETECTED NQ Lows at Key Level:", sweep_nq_lows_key_level)
                        nq_buy_candidate.register_sweep(sweep_nq_lows_key_level["timestamp"], sweep_nq_lows_key_level["sweep_candle_low"], sweep_nq_lows_key_level["sweep_time"], sweep_nq_lows_key_level["sweep_and_ob_confirmed"], sweep_nq_lows_key_level["sweep_and_ob_entry"], sweep_nq_lows_key_level["sweep_and_ob_ce_confirmed"], sweep_nq_lows_key_level["sweep_and_ob_ce_entry"], sweep_nq_lows_key_level["sweep_and_ob_confirmation_timestamp"], sweep_nq_lows_key_level["swept_levels"], "NQ", sweep_nq_lows_key_level["sweep_type"], sweep_nq_lows_key_level["sweep_candle"])
                    elif sweep_nq_lows:
                        print("Sweep detected NQ Lows:", sweep_nq_lows)
                        nq_buy_candidate.register_sweep(sweep_nq_lows["timestamp"], sweep_nq_lows["sweep_candle_low"], sweep_nq_lows["sweep_time"], sweep_nq_lows["sweep_and_ob_confirmed"], sweep_nq_lows["sweep_and_ob_entry"], sweep_nq_lows["sweep_and_ob_ce_confirmed"], sweep_nq_lows["sweep_and_ob_ce_entry"], sweep_nq_lows["sweep_and_ob_confirmation_timestamp"], sweep_nq_lows["swept_levels"], "NQ", sweep_nq_lows["sweep_type"], sweep_nq_lows["sweep_candle"])

                if sweep_es_highs or sweep_es_highs_key_level:
                    if sweep_es_highs_key_level:
                        print("SWEEP DETECTED ES Highs at Key Level:", sweep_es_highs_key_level)
                        es_sell_candidate.register_sweep(sweep_es_highs_key_level["timestamp"], sweep_es_highs_key_level["sweep_candle_high"], sweep_es_highs_key_level["sweep_time"], sweep_es_highs_key_level["sweep_and_ob_confirmed"], sweep_es_highs_key_level["sweep_and_ob_entry"], sweep_es_highs_key_level["sweep_and_ob_ce_confirmed"], sweep_es_highs_key_level["sweep_and_ob_ce_entry"], sweep_es_highs_key_level["sweep_and_ob_confirmation_timestamp"], sweep_es_highs_key_level["swept_levels"], "ES", sweep_es_highs_key_level["sweep_type"], sweep_es_highs_key_level["sweep_candle"])
                    elif sweep_es_highs:     
                        print("SWEEP DETECTED ES Highs:", sweep_es_highs)
                        es_sell_candidate.register_sweep(sweep_es_highs["timestamp"], sweep_es_highs["sweep_candle_high"], sweep_es_highs["sweep_time"], sweep_es_highs["sweep_and_ob_confirmed"], sweep_es_highs["sweep_and_ob_entry"], sweep_es_highs["sweep_and_ob_ce_confirmed"], sweep_es_highs["sweep_and_ob_ce_entry"], sweep_es_highs["sweep_and_ob_confirmation_timestamp"], sweep_es_highs["swept_levels"], "ES", sweep_es_highs["sweep_type"], sweep_es_highs["sweep_candle"])
                
                if sweep_es_lows or sweep_es_lows_key_level:
                    if sweep_es_lows_key_level:
                        print("SWEEP DETECTED ES Lows at Key Level:", sweep_es_lows_key_level)
                        es_buy_candidate.register_sweep(sweep_es_lows_key_level["timestamp"], sweep_es_lows_key_level["sweep_candle_low"], sweep_es_lows_key_level["sweep_time"], sweep_es_lows_key_level["sweep_and_ob_confirmed"], sweep_es_lows_key_level["sweep_and_ob_entry"], sweep_es_lows_key_level["sweep_and_ob_ce_confirmed"], sweep_es_lows_key_level["sweep_and_ob_ce_entry"], sweep_es_lows_key_level["sweep_and_ob_confirmation_timestamp"], sweep_es_lows_key_level["swept_levels"], "ES", sweep_es_lows_key_level["sweep_type"], sweep_es_lows_key_level["sweep_candle"])
                    elif sweep_es_lows:
                        print("Sweep detected ES Lows:", sweep_es_lows)
                        es_buy_candidate.register_sweep(sweep_es_lows["timestamp"], sweep_es_lows["sweep_candle_low"], sweep_es_lows["sweep_time"], sweep_es_lows["sweep_and_ob_confirmed"], sweep_es_lows["sweep_and_ob_entry"], sweep_es_lows["sweep_and_ob_ce_confirmed"], sweep_es_lows["sweep_and_ob_ce_entry"], sweep_es_lows["sweep_and_ob_confirmation_timestamp"], sweep_es_lows["swept_levels"], "ES", sweep_es_lows["sweep_type"], sweep_es_lows["sweep_candle"])
                
                
                #  continue if there are no active candidates
                if not nq_buy_candidate.active and not nq_sell_candidate.active and not es_buy_candidate.active and not es_sell_candidate.active:
                    continue

                # print for debug
                if nq_buy_candidate.active:
                    print("Nq Buy candidate active:", nq_buy_candidate.active,
                        "| NQ sweep at:", nq_buy_candidate.sweep_timestamp)
                if nq_sell_candidate.active:
                    print("Nq Sell candidate active:", nq_sell_candidate.active,
                        "| NQ sweep at:", nq_sell_candidate.sweep_timestamp)
                if es_buy_candidate.active:
                    print("Es Buy candidate active:", es_buy_candidate.active,
                        "| ES sweep at:", es_buy_candidate.sweep_timestamp)
                if es_sell_candidate.active:
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
                # we dont need to skip once sweep and ob is formed
                # continue to detect OB, in case of smt if there is not sweep on ES but on NQ, and ES forms OB we can alert SMT signal
                # if nq_buy_candidate.active and not nq_buy_candidate.sweep_and_ob_confirmed or es_buy_candidate.active and not es_buy_candidate.sweep_and_ob_confirmed:
                if nq_buy_candidate.active or es_buy_candidate.active:

                    nq_ob = detect_30m_order_block(nq_30m[:i], nq_buy_candidate, es_buy_candidate, last_closed_es)

                    if nq_ob:
                        nq_buy_candidate.register_ob(nq_ob)

                    es_ob = detect_30m_order_block(es_30m[:i], es_buy_candidate, nq_buy_candidate, last_closed_nq)
                    if es_ob:
                        es_buy_candidate.register_ob(es_ob)

                if nq_sell_candidate.active or es_sell_candidate.active:
                    print("calling detect 30m OB")
                    nq_ob = detect_30m_order_block(nq_30m[:i], nq_sell_candidate, es_sell_candidate, last_closed_es)
                    print("nq ob: ", nq_ob)
                    if nq_ob:
                        nq_sell_candidate.register_ob(nq_ob)

                    es_ob = detect_30m_order_block(es_30m[:i], es_sell_candidate, nq_sell_candidate, last_closed_nq)
                    if es_ob:
                        es_sell_candidate.register_ob(es_ob)
                        print("es sell candidate OB: ", es_sell_candidate.ob_data)
                    
                #  confirmation of sweep on or actual ob detection
                
                if (nq_buy_candidate.sweep_and_ob_confirmed or nq_buy_candidate.ob_confirmed):
                    nq_buy_candidate.final_ob_confirmed = True
                if (nq_sell_candidate.sweep_and_ob_confirmed or nq_sell_candidate.ob_confirmed):
                    nq_sell_candidate.final_ob_confirmed = True
                if (es_buy_candidate.sweep_and_ob_confirmed or es_buy_candidate.ob_confirmed):
                    es_buy_candidate.final_ob_confirmed = True
                if (es_sell_candidate.sweep_and_ob_confirmed or es_sell_candidate.ob_confirmed):
                    es_sell_candidate.final_ob_confirmed = True

                # we can continue if no OBs found for active candidates
                should_continue = False
                if (nq_buy_candidate.active and not nq_buy_candidate.final_ob_confirmed) and (es_buy_candidate.active and not es_buy_candidate.final_ob_confirmed) and (nq_sell_candidate.active and not nq_sell_candidate.final_ob_confirmed) and (es_sell_candidate.active and not es_sell_candidate.final_ob_confirmed):
                    print("should continue: nq, es buy candidate not ready ", should_continue)
                    should_continue = True
                
                if should_continue:
                    continue
                
                # check smt once OB is confirmed, as it will be confirmation for smt to hold
                key_level_bullish_smt_result = detect_bullish_smt_key_levels(nq_buy_candidate.swept_levels,
                    es_buy_candidate.swept_levels)
                key_level_bearish_smt_result = detect_bearish_smt_key_levels(nq_sell_candidate.swept_levels,
                    es_sell_candidate.swept_levels)
                
                bullish_30m_swing_smt, bearish_30m_swing_smt = detect_30m_swing_smt(nq_valid_swing_highs, nq_valid_swing_lows, es_valid_swing_highs, es_valid_swing_lows, last_closed_nq, last_closed_es)
                
                if bullish_30m_swing_smt is None and bearish_30m_swing_smt is None:
                    print('no smt result')
                else:
                    print("30m swing bullish smt, bearish smt: ", bullish_30m_swing_smt, bearish_30m_swing_smt)
                
                if key_level_bullish_smt_result is None and key_level_bearish_smt_result is None:
                    print("no key level smt")
                else:
                    print("key_level_bullish_smt_result: ", key_level_bullish_smt_result)
                    print("key_level_bearish_smt_result: ", key_level_bearish_smt_result)
                # detect smt at key level
                # print("nq keys: ", nq.keys())
                nq_1h_filtered = filter_hourly_candles(nq["1h"], current_30m_start)
                # print("nq_1h_filtered: ", nq_1h_filtered)
                
                es_1h_filtered = filter_hourly_candles(es["1h"], current_30m_start)
                # print("es_1h_filtered: ", es_1h_filtered)

                # detect smt at 1h
                h1_bullish_smt, h1_bearish_smt = detect_hourly_smt_precise(nq_1h_filtered, es_1h_filtered)
                if h1_bullish_smt is not None or h1_bearish_smt is not None:
                    # store smt details in market context and update when it fails
                    print("h1 bullish smt, bearish smt: ", h1_bullish_smt, h1_bearish_smt)
                    nq_market_context.update_1h_smt(h1_bullish_smt, h1_bearish_smt)
                # check if smt is holdinh
                nq_market_context.update_1h_smt_status(last_closed_nq, last_closed_es)
                summary_bullish_smt, summary_bearish_smt = summary_smt(h1_bullish_smt, h1_bearish_smt, key_level_bullish_smt_result, key_level_bearish_smt_result, bullish_30m_swing_smt, bearish_30m_swing_smt)
                # print for debug
                print("Nq Buy candidate OB:", nq_buy_candidate.ob_confirmed, "| NQ sweep at:", nq_buy_candidate.sweep_timestamp,
                    "| OB data:", nq_buy_candidate.ob_data, "| Final OB confirmed:", nq_buy_candidate.final_ob_confirmed)

                print("Nq Sell candidate OB:", nq_sell_candidate.ob_confirmed, "| NQ sweep at:", nq_sell_candidate.sweep_timestamp,
                    "| OB data:", nq_sell_candidate.ob_data, "| Final OB confirmed:", nq_sell_candidate.final_ob_confirmed)

                print("Es Buy candidate OB:", es_buy_candidate.ob_confirmed, "| ES sweep at:", es_buy_candidate.sweep_timestamp,
                    "| OB data:", es_buy_candidate.ob_data, "| Final OB confirmed:", es_buy_candidate.final_ob_confirmed)

                print("Es Sell candidate OB:", es_sell_candidate.ob_confirmed, "| ES sweep at:", es_sell_candidate.sweep_timestamp,
                    "| OB data:", es_sell_candidate.ob_data, "| Final OB confirmed:", es_sell_candidate.final_ob_confirmed)


                fvg = None
                
                if nq_buy_candidate.final_ob_confirmed:
                    print("Processing FVG for NQ Buy candidate")
                    #  imbalance should be present between sweep time and Ob time

                    fvg = detect_3m_imbalance_inside_ob_candle(
                        nq_3m,
                        nq_buy_candidate,
                        "NQ",
                        last_closed_nq
                    )
                    if fvg:
                        nq_buy_candidate.register_fvg(fvg)
                        print("Bullish FVG detected:", fvg)
                
                if nq_sell_candidate.final_ob_confirmed:
                    print("Processing FVG for NQ Sell candidate")

                    fvg = detect_3m_imbalance_inside_ob_candle(
                        nq_3m,
                        nq_sell_candidate,
                        "NQ",
                        last_closed_nq
                    )
                    if fvg:
                        nq_sell_candidate.register_fvg(fvg)
                        print("Bearish FVG detected:", fvg)
                
                if es_buy_candidate.final_ob_confirmed:
                    print("Processing FVG for ES Buy candidate")

                    fvg = detect_3m_imbalance_inside_ob_candle(
                        es_3m,
                        es_buy_candidate,
                        "ES",
                        last_closed_es
                    )
                    if fvg:
                        es_buy_candidate.register_fvg(fvg)
                        print("Bullish FVG detected:", fvg)

                if es_sell_candidate.final_ob_confirmed:
                    print("Processing FVG for ES Sell candidate")

                    fvg = detect_3m_imbalance_inside_ob_candle(
                        es_3m,
                        es_sell_candidate,
                        "ES",
                        last_closed_es
                    )
                    if fvg:
                        es_sell_candidate.register_fvg(fvg)
                        print("Bearish FVG detected:", fvg)
                if(nq_sell_candidate.fvg_confirmed or nq_sell_candidate.final_ob_confirmed):
                    print("NQ Sell candidate ready for alert. FVG confirmed:", nq_sell_candidate.fvg_confirmed, "| Sweep and OB confirmed:", nq_sell_candidate.sweep_and_ob_confirmed, "| current candle time:", current_30m_start)
                    # print("Market Context: ", nq_market_context.values())
                # else:
                    # print("NQ Sell candidate NOT ready for alert. FVG confirmed:", nq_sell_candidate.fvg_confirmed, "| Sweep and OB confirmed:", nq_sell_candidate.sweep_and_ob_confirmed, "| current candle time:", current_30m_start)
                    # print("Market Context: ", nq_market_context.values())
                if(nq_buy_candidate.fvg_confirmed or nq_buy_candidate.final_ob_confirmed):
                    print("NQ buy candidate ready for alert. FVG confirmed:", nq_buy_candidate.fvg_confirmed, "| Sweep and OB confirmed:", nq_buy_candidate.sweep_and_ob_confirmed, "| current candle time:", current_30m_start)
                    # print("Market Context: ", nq_market_context.values())
                # else:
                #     print("NQ buy candidate NOT ready for alert. FVG confirmed:", nq_buy_candidate.fvg_confirmed, "| Sweep and OB confirmed:", nq_buy_candidate.sweep_and_ob_confirmed, "| current candle time:", current_30m_start)
                    # print("Market Context: ", nq_market_context.values())
                if(es_sell_candidate.fvg_confirmed or es_sell_candidate.final_ob_confirmed):
                    print("es Sell candidate ready for alert. FVG confirmed:", es_sell_candidate.fvg_confirmed, "| Sweep and OB confirmed:", es_sell_candidate.sweep_and_ob_confirmed, "| current candle time:", current_30m_start)
                    # print("Market Context: ", es_market_context.values())
                # else:
                #     print("ES Sell candidate NOT ready for alert. FVG confirmed:", es_sell_candidate.fvg_confirmed, "| Sweep and OB confirmed:", es_sell_candidate.sweep_and_ob_confirmed, "| current candle time:", current_30m_start)
                    # print("Market Context: ", es_market_context.values())
                if(es_buy_candidate.fvg_confirmed or nq_buy_candidate.final_ob_confirmed):
                    print("ES buy candidate ready for alert. FVG confirmed:", es_buy_candidate.fvg_confirmed, "| Sweep and OB confirmed:", es_buy_candidate.sweep_and_ob_confirmed, "| current candle time:", current_30m_start)
                    # print("Market Context: ", es_market_context.values())
                # else:
                #     print("ES buy candidate NOT ready for alert. FVG confirmed:", es_buy_candidate.fvg_confirmed, "| Sweep and OB confirmed:", es_buy_candidate.sweep_and_ob_confirmed, "| current candle time:", current_30m_start)
                    # print("Market Context: ", es_market_context.values())

                # filter alerts based on Market Context
                # send alert if FVG confirmed and alert not sent for that candidate

                # group contexts
                es_context = {
                    "market_context": es_market_context,
                    "london_context": es_london_market_context,
                    "newyork_context": es_ny_market_context,
                    "liquidity": liquidity_es,
                }
                nq_context = {
                    "market_context": nq_market_context,
                    "london_context": nq_london_market_context,
                    "newyork_context": nq_ny_market_context,
                    "liquidity": liquidity_nq,
                }

                if (nq_sell_candidate.fvg_confirmed or nq_sell_candidate.final_ob_confirmed) and not nq_sell_candidate.alert_sent:
                    # filter using market context
                    send = False
                    if (nq_market_context.day_type == "reversal" or nq_market_context.day_type is None) and nq_market_context.bias == "bearish":
                        send = True
                    # filter based on SMT and other market context
                    # if nq_market_context.atr_usage > 0.8:
                    #     send = True
                    send = check_for_reversal_setup_confirmation(nq_market_context, nq_london_market_context, nq_ny_market_context, nq_seven_hour_builder.candles, liquidity_nq, nq_sell_candidate, last_closed_nq, current_30m_start, summary_bearish_smt, es_context)
                    # check for alert at 9:30
                    if send:
                        # check for blocked time
                        result = is_blocked_time(current_30m_start)
                        if result:
                            print("is blocked time (current_30m_start): ", current_30m_start)
                            send = False
                            print("send from blocked time: ", send)
                        # current_last_closed_dt = to_ny_datetime(last_closed_nq["timestamp"])
                        # confirmation_dt = to_ny_datetime(nq_sell_candidate.confirmation_time)
                        # if confirmation_dt < current_last_closed_dt:
                        #     print("current time is ahead of confirmation time, not sending alert")
                        #     send = False
                        
                        # check smt and other confirmations
                        # if no smt, both es and nq should have OB with displacement

                        
                        
                        
                        # check if existing candidate in opp direction
                        # if there is, then both es and nq should be active with OBs formed with smt
                        if nq_buy_candidate.alert_sent or es_buy_candidate.alert_sent:
                            if nq_sell_candidate.final_ob_confirmed and es_sell_candidate.final_ob_confirmed:
                                if summary_bearish_smt["bearish_smt_1h"] is not None or summary_bearish_smt["bearish_smt_30m_swing"] is not None or summary_bearish_smt["bearish_smt_key_level"]:
                                    send = True
                                    print("allowing counter trend trade as both candidates have OB confirmed with smt confirmation")
                                else:
                                    send = False
                                    print("not allowing counter trade as no SMT confirmation even though both candidates have OBs confirmed")   
                            else:
                                send = False
                                print("not allowing counter trend trade as one of the candidates do not have OB confirmed")
                    print("send === ", send, "trade confirmation time: ", nq_sell_candidate.confirmation_time, "last_closed_candle: ", last_closed_nq["timestamp"])
                    if send:
                        print("Market Context: ", nq_market_context.values())
                        message = build_trade_alert(candidate = nq_sell_candidate, liquidity_map = liquidity_nq, daily_atr = nq_daily_atr, current_time = current_30m_start)
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
                if (nq_buy_candidate.fvg_confirmed or nq_buy_candidate.final_ob_confirmed) and not nq_buy_candidate.alert_sent:
                    send = False
                    if (nq_market_context.day_type == "reversal" or nq_market_context.day_type is None) and (nq_market_context.bias == "bullish" or nq_market_context.bias == "neutral"):
                        send = True
                    # if nq_market_context.atr_usage > 0.8:
                    #     send = True
                    send = check_for_reversal_setup_confirmation(nq_market_context, nq_london_market_context, nq_ny_market_context, nq_seven_hour_builder.candles, liquidity_nq, nq_buy_candidate, last_closed_nq, current_30m_start, summary_bullish_smt, es_context)
                    print("send from check nq buy candidate: ", send)
                    # check for alert at 9:30
                    if send:
                        result = is_blocked_time(current_30m_start)
                        if result:
                            print("is blocked time (current_30m_start): ", current_30m_start)
                            send = False
                            print("send from blocked time: ", send)
                        
                        # current_last_closed_dt = to_ny_datetime(last_closed_nq["timestamp"])
                        # confirmation_dt = to_ny_datetime(nq_buy_candidate.confirmation_time)
                        # if confirmation_dt < current_last_closed_dt:
                        #     print("current time is ahead of confirmation time, not sending alert")
                        #     send = False
                        # send = True
                        print("send == ", send, "trade confirmation time: ", nq_buy_candidate.confirmation_time, "last_closed_candle: ", last_closed_nq["timestamp"])
                        # check if existing candidate in opp direction
                        # if there is, then both es and nq should be active with OBs formed with smt
                        if nq_sell_candidate.alert_sent or es_sell_candidate.alert_sent:
                            if nq_buy_candidate.final_ob_confirmed and es_buy_candidate.final_ob_confirmed:
                                if summary_bullish_smt["bullish_smt_1h"] is not None or summary_bullish_smt["bullish_smt_30m_swing"] is not None or summary_bullish_smt["bullish_smt_key_level"]:
                                    send = True
                                    print("allowing counter trend trade as both candidates have OB confirmed with smt confirmation")
                                else:
                                    send = False
                                    print("not allowing counter trade as no SMT confirmation even though both candidates have OBs confirmed")
                            else:
                                send = False
                                print("not allowing counter trend trade as one of the candidates do not have OB confirmed")
                    if send:
                        print("Market Context: ", nq_market_context.values())
                        # send alert for NQ buy candidate
                        message = build_trade_alert(candidate = nq_buy_candidate, liquidity_map = liquidity_nq, daily_atr = nq_daily_atr, current_time = current_30m_start)
                        if message:
                            execute_trade_and_log(nq_buy_candidate, message)
                            # send_telegram_alert_to_all(message)
                            # nq_buy_candidate.alert_sent = True
                            # insert_trade(nq_buy_candidate)
                
                if (es_sell_candidate.fvg_confirmed or es_sell_candidate.final_ob_confirmed) and not es_sell_candidate.alert_sent:
                    # filters
                    # session time
                    # earlier 7h bias, sweep of Asia session high or low
                    # rejection of IB at asia session sweep
                    # atr for move
                    send = False                    
                    send = check_for_reversal_setup_confirmation(es_market_context, es_london_market_context, es_ny_market_context, es_seven_hour_builder.candles, liquidity_es, es_sell_candidate, last_closed_es, current_30m_start, summary_bearish_smt, nq_context)
                    print("send 1: ", send)
                    # if (es_market_context.day_type == "reversal" or es_market_context.day_type is None) and nq_market_context.bias == "bearish":
                    #     send = True
                    #     print("es sell: step 2")
                    # else:
                    #     print("es sell: step 3")
                    # if es_market_context.atr_usage > 0.8:
                    #     send = True
                    #     print("es sell: step 4")
                    # elif es_current_session_high > es_current_session_low:
                    #     # allow continuation shorts
                    #     send = True
                    #     print("es sell: step 5")
                    # elif es_current_session_high < es_current_session_low:
                    #     #  dont allow shorts. atr incomplete, allow longs
                    #     print("es sell: step 6")
                    #     send = False
                    # check for alert at 9:30
                    # if send is true, check other conditions
                    if send:
                        result = is_blocked_time(current_30m_start)
                        if result:
                            print("is blocked time (current_30m_start): ", current_30m_start)
                            send = False
                            print("send from blocked time: ", send)
                        
                        # check last_closed_timestamp with confirmation_time
                        current_last_closed_dt = to_ny_datetime(last_closed_es["timestamp"])
                        confirmation_dt = to_ny_datetime(es_sell_candidate.confirmation_time)
                        if confirmation_dt < current_last_closed_dt:
                            print("current time is ahead of confirmation time, not sending alert")
                            send = False
                        # send = True
                        print("ES send == ", send, "trade confirmation time: ", es_sell_candidate.confirmation_time, "last_closed_candle: ", last_closed_es["timestamp"])
                        # check if existing candidate in opp direction
                        # if there is, then both es and nq should be active with OBs formed with smt
                        if nq_buy_candidate.alert_sent or es_buy_candidate.alert_sent:
                            if nq_sell_candidate.final_ob_confirmed and es_sell_candidate.final_ob_confirmed:
                                if summary_bearish_smt["bearish_smt_1h"] is not None or summary_bearish_smt["bearish_smt_30m_swing"] is not None or summary_bearish_smt["bearish_smt_key_level"]:
                                    send = True
                                    print("allowing counter trend trade as both candidates have OB confirmed with smt confirmation")
                                else:
                                    send = False
                                    print("not allowing counter trade as no SMT confirmation even though both candidates have OBs confirmed")
                            else:
                                send = False
                                print("not allowing counter trend trade as one of the candidates do not have OB confirmed")
                    print("send 2: ", send)
                    if send:
                        print("ES Market Context: ", es_market_context.values())
                        # send alert for ES sell candidate
                        message = build_trade_alert(candidate = es_sell_candidate, liquidity_map = liquidity_es, daily_atr = es_daily_atr, current_time = current_30m_start)
                        if message:
                            execute_trade_and_log(es_sell_candidate, message)
                            # send_telegram_alert_to_all(message)
                            # es_sell_candidate.alert_sent = True
                            # insert_trade(es_sell_candidate)
                
                if (es_buy_candidate.fvg_confirmed or es_buy_candidate.final_ob_confirmed) and not es_buy_candidate.alert_sent:
                    send = False
                    if (es_market_context.day_type == "reversal" or es_market_context.day_type is None) and (es_market_context.bias == "bullish" or es_market_context.bias == "neutral"):
                        send = True
                    # if es_market_context.atr_usage > 0.8:
                    #     send = True
                    send = check_for_reversal_setup_confirmation(es_market_context, es_london_market_context,  es_ny_market_context, es_seven_hour_builder.candles, liquidity_es, es_buy_candidate, last_closed_es, current_30m_start, summary_bullish_smt, nq_context)
                    print("send 3: ", send)
                    # check for alert at 9:30
                    if send:
                        result = is_blocked_time(current_30m_start)
                        if result:
                            print("is blocked time (current_30m_start): ", current_30m_start)
                            send = False
                            print("send from blocked time: ", send)
                        
                        # current_last_closed_dt = to_ny_datetime(last_closed_es["timestamp"])
                        # confirmation_dt = to_ny_datetime(es_buy_candidate.confirmation_time)
                        # if confirmation_dt < current_last_closed_dt:
                        #     print("current time is ahead of confirmation time, not sending alert")
                        #     send = False
                        # send = True
                        print("send == ", send, "trade confirmation time: ", es_buy_candidate.confirmation_time, "last_closed_candle: ", last_closed_es["timestamp"])
                        # check if existing candidate in opp direction
                        # if there is, then both es and nq should be active with OBs formed with smt
                        if es_sell_candidate.alert_sent or nq_sell_candidate.alert_sent:
                            if es_buy_candidate.final_ob_confirmed and nq_buy_candidate.final_ob_confirmed:
                                if summary_bullish_smt["bullish_smt_1h"] is not None or summary_bullish_smt["bullish_smt_30m_swing"] is not None or summary_bullish_smt["bullish_smt_key_level"]:
                                    send = True
                                    print("allowing counter trend trade as both candidates have OB confirmed with smt confirmation")
                                else:
                                    send = False
                                    print("not allowing counter trade as no SMT confirmation even though both candidates have OB confirmeds")
                            else:
                                send = False
                                print("not allowing counter trend trade as one of the candidates do not have OB confirmed")
                            
                    print("send 4: ", send)
                    if send:
                        print("ES Market Context: ", es_market_context.values())
                        # send alert for ES buy candidate
                        message = build_trade_alert(candidate = es_buy_candidate, liquidity_map = liquidity_es, daily_atr = es_daily_atr, current_time = current_30m_start)
                        if message:
                            execute_trade_and_log(es_buy_candidate, message)
                            # send_telegram_alert_to_all(message)
                            # es_buy_candidate.alert_sent = True
                            # insert_trade(es_buy_candidate)

                
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
    print("checkval: ", checkval)

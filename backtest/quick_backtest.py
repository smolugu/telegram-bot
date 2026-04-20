from alerts.execute import execute_trade_and_log
from data.models.candle_7h import SevenHourBuilder
from data.models.market_context import MarketContext
from data.sqlite.db import DB_FILE

from data.market_data import fetch_symbol_data_safe, filter_hourly_candles, get_current_contract, get_pdh_pdl_fixed_date
from data.models.reversal_setup import check_for_reversal_setup_confirmation
from helpers.date_time_helpers import to_ny_datetime
from helpers.sessions import get_futures_session, in_session
from data.models.setup_candidate import SetupCandidate
from data.models.ib_continuation_candidate import IBContinuationCandidate
from data.sqlite.db_functions import insert_trade, monitor_open_trades
from helpers.atr import calculate_daily_atr

from helpers.liquidity_levels import get_liquidity_values, reset_liquidity
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
    nq_3m = get_futures_session(nq["3m"], test_date)
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
    nq_market_context.set_daily_atr(nq_daily_atr)
    es_market_context.set_daily_atr(es_daily_atr)
    
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
            if i >= 3:

                print("\n---------------------------")
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
                print("NQ Last closed:", last_closed_nq["timestamp"], nq_market_context.session_high, nq_market_context.session_low)
                # print("ES Last closed:", last_closed_es["timestamp"], last_closed_es["high"], last_closed_es["low"])            
                # print("current 30m boundary at:", current_30m_start)

                dt = datetime.fromisoformat(last_closed_nq["timestamp"])
                dt_current = datetime.fromisoformat(current_30m_start)
                
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

                # TODO: we need to reset the below at dt.hour == 18
                if dt.hour == 16:
                    print("resetting liquidity at : ", dt.hour)
                    liquidity_nq = reset_liquidity()
                    liquidity_es = reset_liquidity()
                    print("resetting market context at : ", dt.hour)
                    print("daily atrs before reset: ", nq_market_context.daily_atr, es_market_context.daily_atr)
                    nq_market_context.reset()
                    es_market_context.reset()
                    nq_daily_atr = calculate_daily_atr(nq["30m"])
                    es_daily_atr = calculate_daily_atr(es["30m"])
                    print("new atrs at 16:", nq_daily_atr, es_daily_atr)
                    # update new daily atrs
                    
                
                # update market context for NQ and ES
                nq_market_context.update_session_range(last_closed_nq["high"], last_closed_nq["low"], last_closed_nq["open"], last_closed_nq["close"])
                es_market_context.update_session_range(last_closed_es["high"], last_closed_es["low"], last_closed_es["open"], last_closed_es["close"])
                # update atr_usage based on daily atr and session range
                nq_market_context.update_atr_usage(current_30m_start)
                es_market_context.update_atr_usage(current_30m_start)
                
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
                
                historical_nq = nq_30m[:i]
                historical_es = es_30m[:i]
                #  gather session liquidity
                liquidity_nq = get_liquidity_values(symbol= nq_contract, candles_30m = historical_nq, test_date=test_date, liquidity_levels=liquidity_nq, current_start = current_30m_start, pdh = nq_pdh, pdl = nq_pdl)
                liquidity_es = get_liquidity_values(symbol= es_contract, candles_30m = historical_es, test_date=test_date, liquidity_levels=liquidity_es, current_start = current_30m_start, pdh = es_pdh, pdl = es_pdl)
                
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
                        nq_sell_candidate.register_sweep(sweep_nq_highs_key_level["timestamp"], sweep_nq_highs_key_level["sweep_candle_high"], sweep_nq_highs_key_level["sweep_time"], sweep_nq_highs_key_level["sweep_and_ob_confirmed"], sweep_nq_highs_key_level["sweep_and_ob_entry"], sweep_nq_highs_key_level["sweep_and_ob_ce_confirmed"], sweep_nq_highs_key_level["sweep_and_ob_ce_entry"], sweep_nq_highs_key_level["sweep_and_ob_confirmation_timestamp"], sweep_nq_highs_key_level["swept_levels"], "NQ", sweep_nq_highs_key_level["sweep_type"])
                    elif sweep_nq_highs:
                        print("SWEEP DETECTED NQ Highs:", sweep_nq_highs)
                        nq_sell_candidate.register_sweep(sweep_nq_highs["timestamp"], sweep_nq_highs["sweep_candle_high"], sweep_nq_highs["sweep_time"], sweep_nq_highs["sweep_and_ob_confirmed"], sweep_nq_highs["sweep_and_ob_entry"], sweep_nq_highs["sweep_and_ob_ce_confirmed"], sweep_nq_highs["sweep_and_ob_ce_entry"], sweep_nq_highs["sweep_and_ob_confirmation_timestamp"], sweep_nq_highs["swept_levels"], "NQ", sweep_nq_highs["sweep_type"])
                if sweep_nq_lows or sweep_nq_lows_key_level:
                    if sweep_nq_lows_key_level:
                        print("SWEEP DETECTED NQ Lows at Key Level:", sweep_nq_lows_key_level)
                        nq_buy_candidate.register_sweep(sweep_nq_lows_key_level["timestamp"], sweep_nq_lows_key_level["sweep_candle_low"], sweep_nq_lows_key_level["sweep_time"], sweep_nq_lows_key_level["sweep_and_ob_confirmed"], sweep_nq_lows_key_level["sweep_and_ob_entry"], sweep_nq_lows_key_level["sweep_and_ob_ce_confirmed"], sweep_nq_lows_key_level["sweep_and_ob_ce_entry"], sweep_nq_lows_key_level["sweep_and_ob_confirmation_timestamp"], sweep_nq_lows_key_level["swept_levels"], "NQ", sweep_nq_lows_key_level["sweep_type"])
                    elif sweep_nq_lows:
                        print("Sweep detected NQ Lows:", sweep_nq_lows)
                        nq_buy_candidate.register_sweep(sweep_nq_lows["timestamp"], sweep_nq_lows["sweep_candle_low"], sweep_nq_lows["sweep_time"], sweep_nq_lows["sweep_and_ob_confirmed"], sweep_nq_lows["sweep_and_ob_entry"], sweep_nq_lows["sweep_and_ob_ce_confirmed"], sweep_nq_lows["sweep_and_ob_ce_entry"], sweep_nq_lows["sweep_and_ob_confirmation_timestamp"], sweep_nq_lows["swept_levels"], "NQ", sweep_nq_lows["sweep_type"])

                if sweep_es_highs or sweep_es_highs_key_level:
                    if sweep_es_highs_key_level:
                        print("SWEEP DETECTED ES Highs at Key Level:", sweep_es_highs_key_level)
                        es_sell_candidate.register_sweep(sweep_es_highs_key_level["timestamp"], sweep_es_highs_key_level["sweep_candle_high"], sweep_es_highs_key_level["sweep_time"], sweep_es_highs_key_level["sweep_and_ob_confirmed"], sweep_es_highs_key_level["sweep_and_ob_entry"], sweep_es_highs_key_level["sweep_and_ob_ce_confirmed"], sweep_es_highs_key_level["sweep_and_ob_ce_entry"], sweep_es_highs_key_level["sweep_and_ob_confirmation_timestamp"], sweep_es_highs_key_level["swept_levels"], "ES", sweep_es_highs_key_level["sweep_type"])
                    elif sweep_es_highs:     
                        print("SWEEP DETECTED ES Highs:", sweep_es_highs)
                        es_sell_candidate.register_sweep(sweep_es_highs["timestamp"], sweep_es_highs["sweep_candle_high"], sweep_es_highs["sweep_time"], sweep_es_highs["sweep_and_ob_confirmed"], sweep_es_highs["sweep_and_ob_entry"], sweep_es_highs["sweep_and_ob_ce_confirmed"], sweep_es_highs["sweep_and_ob_ce_entry"], sweep_es_highs["sweep_and_ob_confirmation_timestamp"], sweep_es_highs["swept_levels"], "ES", sweep_es_highs["sweep_type"])
                if sweep_es_lows or sweep_es_lows_key_level:
                    if sweep_es_lows_key_level:
                        print("SWEEP DETECTED ES Lows at Key Level:", sweep_es_lows_key_level)
                        es_buy_candidate.register_sweep(sweep_es_lows_key_level["timestamp"], sweep_es_lows_key_level["sweep_candle_low"], sweep_es_lows_key_level["sweep_time"], sweep_es_lows_key_level["sweep_and_ob_confirmed"], sweep_es_lows_key_level["sweep_and_ob_entry"], sweep_es_lows_key_level["sweep_and_ob_ce_confirmed"], sweep_es_lows_key_level["sweep_and_ob_ce_entry"], sweep_es_lows_key_level["sweep_and_ob_confirmation_timestamp"], sweep_es_lows_key_level["swept_levels"], "ES", sweep_es_lows_key_level["sweep_type"])
                    elif sweep_es_lows:
                        print("Sweep detected ES Lows:", sweep_es_lows)
                        es_buy_candidate.register_sweep(sweep_es_lows["timestamp"], sweep_es_lows["sweep_candle_low"], sweep_es_lows["sweep_time"], sweep_es_lows["sweep_and_ob_confirmed"], sweep_es_lows["sweep_and_ob_entry"], sweep_es_lows["sweep_and_ob_ce_confirmed"], sweep_es_lows["sweep_and_ob_ce_entry"], sweep_es_lows["sweep_and_ob_confirmation_timestamp"], sweep_es_lows["swept_levels"], "ES", sweep_es_lows["sweep_type"])

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
                        print("es sell candidate OB: ", es_sell_candidate.ob_data)
                    else:
                        print("no ob found")
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
                nq_1h_filtered = filter_hourly_candles(nq["1h"], current_30m_start)
                es_1h_filtered = filter_hourly_candles(es["1h"], current_30m_start)

                # detect smt at 1h
                h1_bullish_smt, h1_bearish_smt = detect_hourly_smt_precise(nq_1h_filtered, es_1h_filtered)
                if h1_bullish_smt is not None or h1_bearish_smt is not None:
                    print("h1 bullish smt, bearish smt: ", h1_bullish_smt, h1_bearish_smt)
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
                    # print("Processing FVG for NQ Buy candidate")
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
                    # print("Processing FVG for NQ Sell candidate")

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
                    # print("Processing FVG for ES Buy candidate")

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
                    # print("Processing FVG for ES Sell candidate")

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
                if(nq_buy_candidate.fvg_confirmed or nq_buy_candidate.final_ob_confirmed):
                    print("ES buy candidate ready for alert. FVG confirmed:", es_buy_candidate.fvg_confirmed, "| Sweep and OB confirmed:", es_buy_candidate.sweep_and_ob_confirmed, "| current candle time:", current_30m_start)
                    # print("Market Context: ", es_market_context.values())
                # else:
                #     print("ES buy candidate NOT ready for alert. FVG confirmed:", es_buy_candidate.fvg_confirmed, "| Sweep and OB confirmed:", es_buy_candidate.sweep_and_ob_confirmed, "| current candle time:", current_30m_start)
                    # print("Market Context: ", es_market_context.values())

                # filter alerts based on Market Context
                # send alert if FVG confirmed and alert not sent for that candidate

                if (nq_sell_candidate.fvg_confirmed or nq_sell_candidate.final_ob_confirmed) and not nq_sell_candidate.alert_sent:
                    # filter using market context
                    send = False
                    if (nq_market_context.day_type == "reversal" or nq_market_context.day_type is None) and nq_market_context.bias == "bearish":
                        send = True
                    # filter based on SMT and other market context
                    # if nq_market_context.atr_usage > 0.8:
                    #     send = True
                    send = check_for_reversal_setup_confirmation(nq_market_context, nq_seven_hour_builder.candles, liquidity_nq, liquidity_es, nq_sell_candidate, last_closed_nq, current_30m_start, nq_daily_atr, summary_bearish_smt)
                    # check for alert at 9:30
                    time = None
                    if nq_sell_candidate.ob_data is None:
                        time = None
                    else:
                        time = nq_sell_candidate.ob_data["confirmation_timestamp"]
                    if nq_sell_candidate.sweep_and_ob_confirmation_timestamp is not None:
                        time = nq_sell_candidate.sweep_and_ob_confirmation_timestamp
                    
                    
                    result = is_blocked_time(current_30m_start)
                    if result:
                        print("is blocked time (current_30m_start): ", current_30m_start)
                        send = False
                        print("send from blocked time: ", send)
                    current_last_closed_dt = to_ny_datetime(last_closed_nq["timestamp"])
                    confirmation_dt = to_ny_datetime(nq_sell_candidate.confirmation_time)
                    if confirmation_dt < current_last_closed_dt:
                        print("current time is ahead of confirmation time, not sending alert")
                        send = False
                    # send alert for NQ sell candidate
                    print("send === ", send, "trade confirmation time: ", nq_sell_candidate.confirmation_time, "last_closed_candle: ", last_closed_nq["timestamp"])
                    if nq_buy_candidate.alert_sent or es_buy_candidate.alert_sent:
                        if nq_sell_candidate.final_ob_confirmed and es_sell_candidate.final_ob_confirmed:
                            if summary_bearish_smt["bearish_smt_1h"] is not None or summary_bearish_smt["bearish_smt_30m_swing"] is not None or summary_bearish_smt["bearish_smt_key_level"]:
                                send = True
                            else:
                                send = False
                        else:
                            send = False
                    if send:
                        print("Market Context: ", nq_market_context.values())
                        message = build_trade_alert(candidate = nq_sell_candidate, liquidity_map = liquidity_nq, daily_atr = nq_daily_atr)
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
                    send = check_for_reversal_setup_confirmation(nq_market_context, nq_seven_hour_builder.candles, liquidity_nq, liquidity_es, nq_buy_candidate, last_closed_nq, current_30m_start, nq_daily_atr, summary_bullish_smt)
                    print("send from check nq buy candidate: ", send)
                    # check for alert at 9:30
                    result = is_blocked_time(current_30m_start)
                    if result:
                        print("is blocked time (current_30m_start): ", current_30m_start)
                        send = False
                        print("send from blocked time: ", send)
                    
                    current_last_closed_dt = to_ny_datetime(last_closed_nq["timestamp"])
                    confirmation_dt = to_ny_datetime(nq_buy_candidate.confirmation_time)
                    if confirmation_dt < current_last_closed_dt:
                        print("current time is ahead of confirmation time, not sending alert")
                        send = False
                    # send = True
                    print("send == ", send, "trade confirmation time: ", nq_buy_candidate.confirmation_time, "last_closed_candle: ", last_closed_nq["timestamp"])
                    if nq_sell_candidate.alert_sent or es_sell_candidate.alert_sent:
                        if nq_buy_candidate.final_ob_confirmed and es_buy_candidate.final_ob_confirmed:
                            if summary_bullish_smt["bullish_smt_1h"] is not None or summary_bullish_smt["bullish_smt_30m_swing"] is not None or summary_bullish_smt["bullish_smt_key_level"]:
                                send = True
                            else:
                                send = False
                        else:
                            send = False
                    if send:
                        print("Market Context: ", nq_market_context.values())
                        # send alert for NQ buy candidate
                        message = build_trade_alert(candidate = nq_buy_candidate, liquidity_map = liquidity_nq, daily_atr = nq_daily_atr)
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
                    send = check_for_reversal_setup_confirmation(es_market_context, es_seven_hour_builder.candles, liquidity_nq, liquidity_es, es_sell_candidate, last_closed_es, current_30m_start, es_daily_atr, summary_bearish_smt)
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
                    if nq_buy_candidate.alert_sent or es_buy_candidate.alert_sent:
                        if nq_sell_candidate.final_ob_confirmed and es_sell_candidate.final_ob_confirmed:
                            if summary_bearish_smt["bearish_smt_1h"] is not None or summary_bearish_smt["bearish_smt_30m_swing"] is not None or summary_bearish_smt["bearish_smt_key_level"]:
                                send = True
                            else:
                                send = False
                        else:
                            send = False
                    if send:
                        print("ES Market Context: ", es_market_context.values())
                        # send alert for ES sell candidate
                        message = build_trade_alert(candidate = es_sell_candidate, liquidity_map = liquidity_es, daily_atr = es_daily_atr)
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
                    send = check_for_reversal_setup_confirmation(es_market_context, es_seven_hour_builder.candles, liquidity_nq, liquidity_es, es_buy_candidate, last_closed_es, current_30m_start, es_daily_atr, summary_bullish_smt)
                    # check for alert at 9:30
                    result = is_blocked_time(current_30m_start)
                    if result:
                        print("is blocked time (current_30m_start): ", current_30m_start)
                        send = False
                        print("send from blocked time: ", send)
                    
                    current_last_closed_dt = to_ny_datetime(last_closed_es["timestamp"])
                    confirmation_dt = to_ny_datetime(es_buy_candidate.confirmation_time)
                    if confirmation_dt < current_last_closed_dt:
                        print("current time is ahead of confirmation time, not sending alert")
                        send = False
                    # send = True
                    print("send == ", send, "trade confirmation time: ", es_buy_candidate.confirmation_time, "last_closed_candle: ", last_closed_es["timestamp"])
                    # check if existing candidate in opp direction
                    # if there is, then both es and nq should be active with smt
                    if es_sell_candidate.alert_sent or nq_sell_candidate.alert_sent:
                        if es_buy_candidate.final_ob_confirmed and nq_buy_candidate.final_ob_confirmed:
                            if summary_bullish_smt["bullish_smt_1h"] is not None or summary_bullish_smt["bullish_smt_30m_swing"] is not None or summary_bullish_smt["bullish_smt_key_level"]:
                                send = True
                            else:
                                send = False
                        else:
                            send = False
                    if send:
                        print("ES Market Context: ", es_market_context.values())
                        # send alert for ES buy candidate
                        message = build_trade_alert(candidate = es_buy_candidate, liquidity_map = liquidity_es, daily_atr = es_daily_atr)
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

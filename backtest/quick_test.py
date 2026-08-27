from alerts.execute import execute_trade_and_log, send_newyork_summary
from framework.models.auction.detector.detect_swings import detect_swings
from framework.models.auction.engine.auction_engine import initialize_auction, refresh_auction
from framework.models.auction.models.auction_engine import AuctionEngine
from framework.models.candle_7h import SevenHourBuilder
from framework.models.compression import detect_compression
from framework.models.delivery_context import initialize_delivery_state
from framework.models.london_market_context import LondonMarketContextES, LondonMarketContext
from framework.models.market_context import MarketContext
from framework.models.nyam_market_context import NewYorkMarketContext
from framework.models.sweep_validation import validate_sweeps
from framework.models.weekly_profile import WeeklyContext
from framework.models.weekly_state import build_weekly_state, initialize_weekly_state, update_weekly_1h_structure
from data.sqlite.db import DB_FILE


from data.market_data import fetch_symbol_data_safe, filter_daily_candles, filter_htf_candles, get_current_contract, get_pdh_pdl_fixed_date
from framework.models.reversal_setup import check_for_reversal_setup_confirmation
from helpers.candle import candle_from_dict
from helpers.date_time_helpers import to_ny_datetime
from helpers.sessions import get_daily_historical_candles, get_futures_session, get_htf_historical_candles, in_session
from framework.models.setup_candidate import SetupCandidate
from framework.models.ib_continuation_candidate import IBContinuationCandidate
from data.sqlite.db_functions import insert_trade, monitor_open_trades
from helpers.atr import calculate_daily_atr

from helpers.liquidity_levels import add_1am_ob_mitigation_levels, add_8am_ob_mitigation_levels, add_ib_ce_key_level, add_post_8am_mitigation_levels, get_liquidity_values, refresh_liquidity, reset_liquidity, update_compression_range_levels
from helpers.swing_points import filter_valid_swing_highs, filter_valid_swing_lows, get_valid_swings
from helpers.time_windows import get_active_window, is_blocked_time
from modules.nyam_context import get_morning_context
from modules.orchestrator import evaluate_7h_setup
from helpers.zones import get_7h_open_from_timestamp

from datetime import datetime, time, timedelta, timezone
from modules.ob_detector import detect_30m_order_block
from modules.smt_detector import detect_30m_swing_smt, detect_bearish_smt_key_levels, detect_bullish_smt_key_levels, detect_daily_smt_precise, detect_htf_smt_liquidity, detect_htf_smt_precise, detect_smt_key_levels, summary_smt
from modules.sweep_detector import detect_30m_and_key_level_sweep, detect_key_liquidity_sweep, find_swing_highs, find_swing_lows, update_sweep_info
from modules.imbalance_detector import detect_3m_imbalance_inside_ob_candle
from alerts.alert_engine import send_telegram_alert_to_all
from alerts.alert_payload import build_summary_alert, build_trade_alert




def run_quick_test(test_date: str):

    print(f"Backtesting {test_date}")

    test_dtx = datetime.strptime(test_date, "%Y-%m-%d")
    previous_day = test_dtx - timedelta(days=1)

    print(previous_day)
    print(previous_day.strftime("%Y-%m-%d"))
    prev_test_date = previous_day.strftime("%Y-%m-%d")
    prev_day_nq_contract = get_current_contract("NQ", prev_test_date)
    prev_day_es_contract = get_current_contract("ES", prev_test_date)

    nq_contract = get_current_contract("NQ", test_date)
    es_contract = get_current_contract("ES", test_date)
    print("nq contract: ", nq_contract)
    print("es contract: ", es_contract)

    nq = fetch_symbol_data_safe(nq_contract)
    es = fetch_symbol_data_safe(es_contract)
    # for c in nq["3m"]:
    #     if "18:" in c["timestamp"]:
    #         print(c["timestamp"])
    
    test_dt = datetime.fromisoformat(test_date).replace(tzinfo=timezone.utc)
    
    # start_dt = test_dt - timedelta(days=2)
    # end_dt = test_dt + timedelta(days=1)
    nq_pdh, nq_pdl = get_pdh_pdl_fixed_date(test_date, nq_contract)
    print("NQ PDh, PDl:", nq_pdh, nq_pdl)
    es_pdh, es_pdl = get_pdh_pdl_fixed_date(test_date, es_contract)
    print("ES PDh, PDl:", es_pdh, es_pdl)
    
    nq_daily_atr = calculate_daily_atr(nq["30m"])
    es_daily_atr = calculate_daily_atr(es["30m"])
    # print("nq daily atr: ", nq_daily_atr, "es daily atr: ", es_daily_atr)
    
    # nq_30m = [c for c in nq["30m"] if start_dt <= datetime.fromisoformat(c["timestamp"]).astimezone(timezone.utc) < end_dt]
    # nq_3m  = [c for c in nq["3m"] if start_dt <= datetime.fromisoformat(c["timestamp"]).astimezone(timezone.utc) < end_dt]
    # nq_30m = [c for c in nq["30m"] if test_date in c["timestamp"]]
    # nq_3m  = [c for c in nq["3m"] if test_date in c["timestamp"]]
    nq_30m = get_futures_session(nq["30m"], test_date)
    nq_3m_historical = get_htf_historical_candles(nq["3m"], test_date)
    nq_4h_historical = get_htf_historical_candles(nq["4h"], test_date)
    nq_7h_historical = get_htf_historical_candles(nq["7h"], test_date)
    nq_1d_historical = get_daily_historical_candles(nq["1d"], test_date)
    # print("nq_30m candles for date: ", nq_30m)
    print("First 3:", nq_3m_historical[:3])
    print("Last 3:", nq_3m_historical[-3:])
    
    nq_3m = get_futures_session(nq["3m"], test_date)
    nq_1m = get_futures_session(nq["1m"], test_date)
    # print("first 10 candles: ",nq_3m)
    # print("nq_30_candles: ", nq_30m)
    # print("nq_3_candles: ", nq_3m)
    # print("nq_3m candles for date: ", nq_3m)
    # nq_30m = nq["30m"]
    # nq_3m = nq["3m"]
    
    # es_30m = [c for c in es["30m"] if test_date in c["timestamp"]]
    # es_3m  = [c for c in es["3m"] if test_date in c["timestamp"]]
    es_30m = get_futures_session(es["30m"], test_date)
    es_3m_historical = get_htf_historical_candles(es["3m"], test_date)
    es_4h_historical = get_htf_historical_candles(es["4h"], test_date)
    es_7h_historical = get_htf_historical_candles(es["7h"], test_date)
    es_3m_historical = get_htf_historical_candles(es["3m"], test_date)
    es_1d_historical = get_daily_historical_candles(es["1d"], test_date)
    es_3m = get_futures_session(es["3m"], test_date)
    es_1m = get_futures_session(es["1m"], test_date)
    
    

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
    prev_liquidity_nq = reset_liquidity()
    prev_liquidity_es = reset_liquidity()
    if prev_day_nq_contract == nq_contract:
        # get prev_day_pdh and pdl
        prev_day_test_dt = datetime.fromisoformat(prev_test_date).replace(tzinfo=timezone.utc)
            
        # start_dt = test_dt - timedelta(days=2)
        # end_dt = test_dt + timedelta(days=1)
        prev_nq_pdh, prev_nq_pdl = get_pdh_pdl_fixed_date(prev_test_date, nq_contract)
        print("NQ prev PDh, prev PDl:", prev_nq_pdh, prev_nq_pdl)
        prev_es_pdh, prev_es_pdl = get_pdh_pdl_fixed_date(prev_test_date, es_contract)
        print("ES prev PDh, prev PDl:", prev_es_pdh, prev_es_pdl)
        prev_nq_30m = get_futures_session(nq["30m"], prev_test_date)
        # print("nq_30m candles for date: ", nq_30m)
        
        prev_nq_3m = get_futures_session(nq["3m"], prev_test_date)
        prev_nq_1m = get_futures_session(nq["1m"], prev_test_date)
        
        prev_es_30m = get_futures_session(es["30m"], prev_test_date)
        prev_es_3m = get_futures_session(es["3m"], prev_test_date)
        prev_es_1m = get_futures_session(es["1m"], prev_test_date)

        if not nq or not es:
            print("No data available.")
            return
        prev_nq_30m_closes = {
            prev_nq_30m[i]["timestamp"]: i
            for i in range(len(prev_nq_30m))
        }
        for candle_3m in prev_nq_3m:
                
            ts = candle_3m["timestamp"]
            if ts in prev_nq_30m_closes:
                i = prev_nq_30m_closes[ts]
                print("Matching 30m candle in prev code found for 3m timestamp:", ts, "at index", i)
                prev_current_30m_start = prev_nq_30m[i]["timestamp"]
                prev_last_closed_nq = prev_nq_30m[i - 1]
                prev_last_closed_es = prev_es_30m[i - 1]
                if i == 1:
                    print("resetting liquidity at : ", i, ts)
                    # TODO: IMP update only swept liquidity, for example keep NYPM unswept levels for next session or day
                    prev_liquidity_nq = reset_liquidity()
                    prev_liquidity_es = reset_liquidity()
                


    
    nq_market_context = MarketContext("NQ")
    es_market_context = MarketContext("ES")
    nq_london_market_context = LondonMarketContext("NQ")
    es_london_market_context = LondonMarketContext("ES")
    nq_ny_market_context = NewYorkMarketContext("NQ")
    es_ny_market_context = NewYorkMarketContext("ES")

    # print("nq daily candles: ", nq["1d"])
    # print("current day: ", nq["1d"][-1]["open"])
    # print("es daily candles: ", es["1d"])
    # weekly context
    # nq_weekly_context = WeeklyContext(
    # instrument = "NQ",
    # daily_candles = nq["1d"],
    # candles_1h = nq["1h"],
    # current_date = "2026-05-15T09:30:00-04:00")
    # es_weekly_context = WeeklyContext(
    # instrument = "ES",
    # daily_candles = nq["1d"],
    # candles_1h = nq["1h"],
    # current_date = "2026-05-15T09:30:00-04:00")

    # print("nq weekly summary: ", nq_weekly_context.summary())
    # print("es weekly summary: ", es_weekly_context.summary())
    
    nq_current_session_high = float("-inf")
    nq_current_session_low = float("inf")
    es_current_session_high = float("-inf")
    es_current_session_low = float("inf")

    # weekly state
    print("resetting in main")
    # nq_weekly_state = initialize_weekly_state("NQ")
    # es_weekly_state = initialize_weekly_state("ES")
    

    # delivery state
    nq_delivery_state = initialize_delivery_state()
    es_delivery_state = initialize_delivery_state()

    def update_weekly_1h_structure_abs(nq_weekly_state, es_weekly_state, current_30m_start):
        nq_1h_filtered_candles = filter_htf_candles(nq["1h"], current_30m_start)
        es_1h_filtered_candles = filter_htf_candles(es["1h"], current_30m_start)
        nq_weekly_state = update_weekly_1h_structure(nq_weekly_state, nq_1h_filtered_candles)
        es_weekly_state = update_weekly_1h_structure(es_weekly_state, es_1h_filtered_candles)
        return nq_weekly_state, es_weekly_state
    
    
    # current_day_start = datetime.combine(
    #     test_date,
    #     time(18, 0)
    # )
    from zoneinfo import ZoneInfo

    current_day_start = (
        datetime.strptime(test_date, "%Y-%m-%d")
        - timedelta(days=1)
    ).replace(
        hour=18,
        minute=0,
        second=0,
        microsecond=0,
        tzinfo=ZoneInfo("America/New_York")
    )

    # nq_weekly_state = build_weekly_state(
    #     nq["1d"],
    #     nq["1h"],
    #     current_day_start,
    #     "NQ"
    # )
    # es_weekly_state = build_weekly_state(
    #     es["1d"],
    #     es["1h"],
    #     current_day_start,
    #     "ES"
    # )
    # for c in nq["4h"][:10]:
    #     print(c["timestamp"])
    #     print(c)
    converted_1m_nq = [candle_from_dict(c=c, timeframe="1m", instrument= "NQ", contract=nq_contract) for c in nq_1m]
    converted_3m_nq = [candle_from_dict(c=c, timeframe="1m", instrument= "NQ", contract=nq_contract) for c in nq_3m]
    # converted_4h_nq = [candle_from_dict(c=c, timeframe="4h", instrument= "NQ", contract=nq_contract) for c in nq_4h]
    # converted_7h_nq = [candle_from_dict(c=c, timeframe="7h", instrument= "NQ", contract=nq_contract) for c in nq_7h]
    # converted_1d_nq = [candle_from_dict(c=c, timeframe="1d", instrument= "NQ", contract=nq_contract) for c in nq_1d]
    converted_1m_es = [candle_from_dict(c=c, timeframe="1m", instrument= "ES", contract=nq_contract) for c in es_1m]
    converted_3m_es = [candle_from_dict(c=c, timeframe="1m", instrument= "ES", contract=nq_contract) for c in es_3m]
    # converted_4h_es = [candle_from_dict(c=c, timeframe="4h", instrument= "ES", contract=es_contract) for c in es_4h]
    # converted_7h_es = [candle_from_dict(c=c, timeframe="7h", instrument= "ES", contract=es_contract) for c in es_7h]
    # converted_1d_es = [candle_from_dict(c=c, timeframe="1d", instrument= "ES", contract=es_contract) for c in es_1d]
    # h4_swings_nq = detect_swings(
    #     candles = converted_4h_nq,
    #     timeframe = "4h",
    # )
    # print("h4_swings_nq: ", h4_swings_nq)
    # h7_swings_nq = detect_swings(
    #     candles = converted_7h_nq,
    #     timeframe = "7h",
    # )
    # print("h7_swings_nq: ", h7_swings_nq)

    # d_swings_nq = detect_swings(
    #     candles = converted_1d_nq,
    #     timeframe = "1d",
    # )
    # print("d_swings_nq: ", d_swings_nq)
    # h4_swings_es = detect_swings(
    #     candles = converted_4h_es,
    #     timeframe = "4h",
    # )
    # print("h4_swings_es: ", h4_swings_es)
    # h7_swings_es = detect_swings(
    #     candles = converted_7h_es,
    #     timeframe = "7h",
    # )
    # print("h7_swings_es: ", h7_swings_es)

    # d_swings_es = detect_swings(
    #     candles = converted_1d_es,
    #     timeframe = "1d",
    # )
    # print("d_swings_es: ", d_swings_es)
    converted_3m_nq_h = [candle_from_dict(c=c, timeframe="1m", instrument= "NQ", contract=nq_contract) for c in nq_3m_historical]
    converted_4h_nq_h = [candle_from_dict(c=c, timeframe="4h", instrument= "NQ", contract=nq_contract) for c in nq_4h_historical]
    converted_7h_nq_h = [candle_from_dict(c=c, timeframe="7h", instrument= "NQ", contract=nq_contract) for c in nq_7h_historical]
    converted_1d_nq_h = [candle_from_dict(c=c, timeframe="1d", instrument= "NQ", contract=nq_contract) for c in nq_1d_historical]
    converted_3m_es_h = [candle_from_dict(c=c, timeframe="1m", instrument= "ES", contract=es_contract) for c in es_3m_historical]
    converted_4h_es_h = [candle_from_dict(c=c, timeframe="4h", instrument= "ES", contract=es_contract) for c in es_4h_historical]
    converted_7h_es_h = [candle_from_dict(c=c, timeframe="7h", instrument= "ES", contract=es_contract) for c in es_7h_historical]
    converted_1d_es_h = [candle_from_dict(c=c, timeframe="1d", instrument= "ES", contract=es_contract) for c in es_1d_historical]
    # initialize auction engine
    nq_candles_for_auction = {
        "3m": converted_3m_nq_h,
        "4h": converted_4h_nq_h,
        "7h": converted_7h_nq_h,
        "1d": converted_1d_nq_h
    }
    es_candles_for_auction = {
        "3m": converted_3m_es_h,
        "4h": converted_4h_es_h,
        "7h": converted_7h_es_h,
        "1d": converted_1d_es_h
    }
    nq_auction_engine = AuctionEngine()
    es_auction_engine = AuctionEngine()
    # print("nq candles: ", nq_candles_for_auction)
    # print("es candles: ", es_candles_for_auction)
    # filter candles by test_date and send to initialize_auction
    
    initialize_auction(nq_auction_engine, nq_candles_for_auction)
    initialize_auction(es_auction_engine, es_candles_for_auction)
    print("initialized context")
    # print("nq auction engine status: ", nq_auction_engine.status.summary())
    # print("nq auction engine context: ", nq_auction_engine.context.summary())
    # print("es auction engine status: ", es_auction_engine.status.summary())
    # print("es auction engine context: ", es_auction_engine.context.summary())
    # print("====================================================")
    #  looping through 30m candles from 18:00 futures start
    for candle_3m in nq_3m:
        
        ts = candle_3m["timestamp"]
        if ts in nq_30m_closes:
            i = nq_30m_closes[ts]
            print("Matching 30m candle found for 3m timestamp:", ts, "at index", i)
            current_30m_start = nq_30m[i]["timestamp"]
            last_closed_nq = nq_30m[i - 1]
            last_closed_es = es_30m[i - 1]
            last_closed_candle_timestamp = nq_30m[i - 1]["timestamp"] 

            dt = datetime.fromisoformat(last_closed_nq["timestamp"])
            dt_current = datetime.fromisoformat(current_30m_start)
            inside_1m_candles_nq = [c for c in nq_1m if c["timestamp"] >= last_closed_nq["timestamp"] and c["timestamp"] < last_closed_nq["timestamp"]]
            inside_1m_candles_es = [c for c in es_1m if c["timestamp"] >= last_closed_es["timestamp"] and c["timestamp"] < last_closed_es["timestamp"]]
            
            # if dt.minute == 0:
            # if i <= 3:
                # nq_weekly_state, es_weekly_state = update_weekly_1h_structure_abs(nq_weekly_state, es_weekly_state, current_30m_start)
            # if i == 1:
            #     print("current start cc: ", current_30m_start)

            # continue
            if i == 1:
                print("resetting liquidity at : ", i, ts)
                # TODO: IMP update only swept liquidity, for example keep NYPM unswept levels for next session or day
                liquidity_nq = reset_liquidity()
                liquidity_es = reset_liquidity()
                liquidity_nq = refresh_liquidity(liquidity_nq, prev_liquidity_nq)
                liquidity_es = refresh_liquidity(liquidity_es, prev_liquidity_es) 
                # print("refreshed liquidity nq: ", liquidity_nq)
                # print("refreshed liquidity es: ", liquidity_es)
                

                # print("resetting market context at : ", dt.hour)
                print("daily atrs before reset: ", nq_market_context.daily_atr, es_market_context.daily_atr)
                nq_market_context.reset()
                es_market_context.reset()
                nq_daily_atr = calculate_daily_atr(nq["30m"])
                es_daily_atr = calculate_daily_atr(es["30m"])
                
                # update market context with new daily atrs
                # print("new atrs at 16:", nq_daily_atr, es_daily_atr)
                nq_market_context.set_daily_atr(nq_daily_atr)
                es_market_context.set_daily_atr(es_daily_atr)

            if i >= 1:
                # get completed 4h and 7h candle
                # 7h candle
                last_3_7h_nq=None
                last_3_7h_es=None
                # start last closed 8am 30m candle, 
                # we have 7hr candle built at last closed 7:30 candle
                if dt.hour in [1, 8, 15] and dt.minute == 00:
                    if dt_current.hour == 1:
                        new_7h_candle_nq = nq_seven_hour_builder.candles["6PM"].values()
                        new_7h_candle_es = es_seven_hour_builder.candles["6PM"].values()
                    elif dt_current.hour == 8:
                        new_7h_candle_nq = nq_seven_hour_builder.candles["1AM"].values()
                        new_7h_candle_es = es_seven_hour_builder.candles["1AM"].values()
                    elif dt_current.hour == 15:
                        new_7h_candle_nq = nq_seven_hour_builder.candles["8AM"].values()
                        new_7h_candle_es = es_seven_hour_builder.candles["8AM"].values()
                    # 3pm candle will be captured converted_7h_nq before the start of day
                    converted_7h_nq_h.append(candle_from_dict(c=new_7h_candle_nq, timeframe="7h", instrument= "NQ", contract=nq_contract))
                    converted_7h_es_h.append(candle_from_dict(c=new_7h_candle_es, timeframe="7h", instrument= "ES", contract=es_contract))
                    last_3_7h_nq = converted_7h_nq_h[-3:]
                    last_3_7h_es = converted_7h_es_h[-3:]

                # 4h candle
                last_3_4h_nq=None
                last_3_4h_es=None
                if dt.hour in [22, 2, 6, 10, 14] and dt.minute == 00:
                    new_4h_candle_nq = {
                        "open": nq_market_context.four_session_open,
                        "close": nq_market_context.four_session_close,
                        "low": nq_market_context.four_session_low,
                        "high": nq_market_context.four_session_high,
                        "timestamp": nq_market_context.four_session_timestamp,
                    }
                    print("new 4h candle: ", new_4h_candle_nq)
                    new_4h_candle_es = {
                        "open": es_market_context.four_session_open,
                        "close": es_market_context.four_session_close,
                        "low": es_market_context.four_session_low,
                        "high": es_market_context.four_session_high,
                        "timestamp": es_market_context.four_session_timestamp,
                    }
                    converted_4h_nq_h.append(candle_from_dict(c=new_4h_candle_nq, timeframe="4h", instrument= "NQ", contract=nq_contract))
                    converted_4h_es_h.append(candle_from_dict(c=new_4h_candle_es, timeframe="4h", instrument= "ES", contract=es_contract))
                    last_3_4h_nq = converted_4h_nq_h[-3:]
                    last_3_4h_es = converted_4h_es_h[-3:]

                # update auction engine with context and status
                # TODO: send 1m or 3m candle to mitigation time
                # current_30m_start = datetime.fromisoformat(
                #     last_closed_30m["timestamp"]
                # )
                current_30m_start_datetime = datetime.fromisoformat(current_30m_start)
                nq_candles_3m_for_auction = [
                    candle
                    for candle in converted_3m_nq
                    if candle.timestamp < current_30m_start_datetime
                ][-40:]
                es_candles_3m_for_auction = [
                    candle
                    for candle in converted_3m_es
                    if candle.timestamp < current_30m_start_datetime
                ][-40:]
                # new 4h candle for reclaimed levels
                
                refresh_auction(
                    auction_engine=nq_auction_engine,
                    candle_30m=candle_from_dict(c=last_closed_nq, timeframe="30m", instrument= "NQ", contract=nq_contract),
                    ltf_candles=nq_candles_3m_for_auction,
                    last_3_4h_candles=last_3_4h_nq,
                    last_3_7h_candles=last_3_7h_nq,
                )
                
                refresh_auction(
                    auction_engine=es_auction_engine,
                    candle_30m=candle_from_dict(c=last_closed_es,timeframe="30m", instrument= "ES", contract=es_contract),
                    ltf_candles=es_candles_3m_for_auction,
                    last_3_4h_candles=last_3_4h_es,
                    last_3_7h_candles=last_3_7h_es,
                )
                print("nq auction engine status: ", nq_auction_engine.status.summary())
                # if dt.hour == 8:
                    # print("nq auction engine status: ", nq_auction_engine.status.summary())
                    # print("nq auction engine context: ", nq_auction_engine.context.summary())
                    # print("es auction engine status: ", es_auction_engine.status.summary())
                    # print("es auction engine context: ", es_auction_engine.context.summary())
                
            # continue
            # if i == 2:
            #     update_weekly_1h_structure_abs(nq_weekly_state = nq_weekly_state, es_weekly_state= es_weekly_state, current_30m_start=current_30m_start)
        
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
                
                # TODO: revisit and check again. candidates reset
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
                # last_closed_nq = nq_30m[i - 1]
                # last_closed_es = es_30m[i - 1]

                print("i =", i, " | current 30m boundary at: ", current_30m_start)
                print("NQ Last closed:", last_closed_nq["timestamp"], "| Open: ", last_closed_nq["open"], "| Low: ", last_closed_nq["low"], "| High: ", last_closed_nq["high"], "| Close: ", last_closed_nq["close"])
                print("ES Last closed:", last_closed_es["timestamp"], "| Open: ", last_closed_es["open"], "| Low: ", last_closed_es["low"], "| High: ", last_closed_es["high"], "| Close: ", last_closed_es["close"])
                # print("current 30m boundary at:", current_30m_start)

                dt = datetime.fromisoformat(last_closed_nq["timestamp"])
                dt_current = datetime.fromisoformat(current_30m_start)
                is_post_1AM_IB = in_session(current_30m_start, 2, 0, 8, 0)
                is_post_8AM_IB = in_session(current_30m_start, 9, 0, 15, 0)

                # section to update context after the end of prev candle to current last closed candles
                if dt.hour == 9 and dt.minute == 00:
                    # add 8am IB CE as key level for migration structures
                    add_ib_ce_key_level(structure_data=nq_ny_market_context, liquidity_levels=liquidity_nq)
                    add_ib_ce_key_level(structure_data=es_ny_market_context, liquidity_levels=liquidity_es)
                    # add mitigation level from ny am structure
                    add_post_8am_mitigation_levels(structure_data=nq_ny_market_context, liquidity_levels=liquidity_nq)
                    add_post_8am_mitigation_levels(structure_data=es_ny_market_context, liquidity_levels=liquidity_es)
                    # add compression levels from nyam structure to liquidity objects
                    # update_compression_range_levels(liquidity_nq, compression_range_nq, "8AM")
                    # update_compression_range_levels(liquidity_es, compression_range_es, "8AM")
                    
                
                # update currest_session for i=0, 1, 2 
                if (i == 3):
                    # nq_current_session_high = max(nq_30m[0]["high"], nq_30m[1]["high"], nq_30m[2]["high"])
                    # nq_current_session_low = min(nq_30m[0]["low"], nq_30m[1]["low"], nq_30m[2]["low"])
                    # TODO: remove - we are storing current day session high and low in market context
                    # nq_current_session_high = max(nq_30m[0]["high"], nq_30m[1]["high"], nq_30m[2]["high"])
                    # nq_current_session_low = min(nq_30m[0]["low"], nq_30m[1]["low"], nq_30m[2]["low"])
                    # es_current_session_high = max(es_30m[0]["high"], es_30m[1]["high"], es_30m[2]["high"])
                    # es_current_session_low = min(es_30m[0]["low"], es_30m[1]["low"], es_30m[2]["low"])
                    # update 18:00 candle with the initial 3 candles
                    nq_seven_hour_builder.update(nq_30m[0])
                    nq_seven_hour_builder.update(nq_30m[1])
                    nq_seven_hour_builder.update(nq_30m[2])
                    print("nq 7h before: ", nq_seven_hour_builder.candles["6PM"].values())
                 
                    # nq_seven_hour_builder.candles["6PM"].ib_high = 29283.75
                    # nq_seven_hour_builder.candles["6PM"].ib_low = 29110
                    # nq_seven_hour_builder.candles["6PM"].ib_open = 29135
                    # nq_seven_hour_builder.candles["6PM"].ib_close = 29232.75
                    # nq_seven_hour_builder.candles["6PM"].ib_ce = (29110+29283.75)/2
                    es_seven_hour_builder.update(es_30m[0])
                    es_seven_hour_builder.update(es_30m[1])
                    es_seven_hour_builder.update(es_30m[2])
                    print("es 7h before: ", es_seven_hour_builder.candles["6PM"].values())                   
                    # es_seven_hour_builder.candles["6PM"].ib_high = 7435
                    # es_seven_hour_builder.candles["6PM"].ib_low = 7408.5
                    # es_seven_hour_builder.candles["6PM"].ib_ce = (7408.5+7435)/2
                    # nq_seven_hour_builder.candles["6PM"].ib_open = 7410
                    # nq_seven_hour_builder.candles["6PM"].ib_close = 7429
                    nq_market_context.update_session_range(nq_30m[0]["high"], nq_30m[0]["low"], nq_30m[0]["open"], nq_30m[0]["close"], dt.hour, dt.minute, nq_30m[0]["timestamp"])
                    nq_market_context.update_session_range(nq_30m[1]["high"], nq_30m[1]["low"], nq_30m[1]["open"], nq_30m[1]["close"], dt.hour, dt.minute, nq_30m[1]["timestamp"])
                    nq_market_context.update_session_range(nq_30m[2]["high"], nq_30m[2]["low"], nq_30m[2]["open"], nq_30m[2]["close"], dt.hour, dt.minute, nq_30m[2]["timestamp"])
                    es_market_context.update_session_range(es_30m[0]["high"], es_30m[0]["low"], es_30m[0]["open"], es_30m[0]["close"], dt.hour, dt.minute, nq_30m[0]["timestamp"])
                    es_market_context.update_session_range(es_30m[1]["high"], es_30m[1]["low"], es_30m[1]["open"], es_30m[1]["close"], dt.hour, dt.minute, nq_30m[1]["timestamp"])
                    es_market_context.update_session_range(es_30m[2]["high"], es_30m[2]["low"], es_30m[2]["open"], es_30m[2]["close"], dt.hour, dt.minute, nq_30m[2]["timestamp"])
                    # nq_market_context.session_open = 29135

                    # nq_market_context.session_close = 29232.75
                    # es_market_context.session_open = 7410
                    # es_market_context.session_close = 7429
                    print("session_open: ", nq_market_context.session_open)
                    print("session_high: ", nq_market_context.session_high)
                    print("session_low: ", nq_market_context.session_low)
                    print("session_close: ", nq_market_context.session_close)
                # print("nq 7h: ", nq_seven_hour_builder.candles["6PM"].values())                
                # print("es 7h: ", es_seven_hour_builder.candles["6PM"].values())                    
                
                # if dt_current.minute == 00:
                #     update_weekly_1h_structure_abs(nq_weekly_state = nq_weekly_state, es_weekly_state= es_weekly_state, current_30m_start=current_30m_start)
                
                # at the start of each new candle check if there is a sweep candidate with type = breakout and if the current candle closes above the sweep_candle open, then confirm the breakout sweep and update the type to rejection
                # changing breakout to rejection if the next candle closes above or below the sweep level
                if nq_buy_candidate.active and nq_buy_candidate.check_breakout_rejection:
                    update_sweep_info(nq_buy_candidate, nq["3m"], last_closed_nq)
                if nq_sell_candidate.active and nq_sell_candidate.check_breakout_rejection:
                    update_sweep_info(nq_sell_candidate, nq["3m"], last_closed_nq)
                if es_buy_candidate.active and es_buy_candidate.check_breakout_rejection:
                    update_sweep_info(es_buy_candidate, es["3m"], last_closed_es)
                if es_sell_candidate.active and es_sell_candidate.check_breakout_rejection:
                    update_sweep_info(es_sell_candidate, es["3m"], last_closed_es)
                        
                # invalidate failed candidates
                # invalidate of ob is confirmed
                if nq_buy_candidate.active and nq_buy_candidate.final_ob_confirmed and nq_buy_candidate.sweep_candle_extreme > last_closed_nq["low"]:
                    nq_buy_candidate.reset()
                    es_buy_candidate.reset()
                if nq_sell_candidate.active and nq_sell_candidate.final_ob_confirmed and nq_sell_candidate.sweep_candle_extreme < last_closed_nq["high"]:
                    nq_sell_candidate.reset()
                    nq_sell_candidate.reset()
                if es_buy_candidate.active and es_buy_candidate.final_ob_confirmed and es_buy_candidate.sweep_candle_extreme > last_closed_es["low"]:
                    es_buy_candidate.reset()
                    nq_buy_candidate.reset()
                if es_sell_candidate.active and es_sell_candidate.final_ob_confirmed and es_sell_candidate.sweep_candle_extreme < last_closed_es["high"]:
                    es_sell_candidate.reset()
                    nq_sell_candidate.reset()
                
                # update 7hr candle through seven hour builder
                # he 18:00 7hr candle is not complete with the first 3 30m candles
                nq_seven_hour_builder.update(last_closed_nq)
                print("nq 7h after ib ready: ", nq_seven_hour_builder.candles["6PM"].values())   
                es_seven_hour_builder.update(last_closed_es)

                
                
                # get liquidity levels at end of each 30m candle
                historical_nq = nq_30m[:i]
                historical_es = es_30m[:i]
                #  gather session liquidity
                liquidity_nq = get_liquidity_values(symbol= nq_contract, candles_30m = historical_nq, test_date=test_date, liquidity_levels=liquidity_nq, current_start = current_30m_start, pdh = nq_pdh, pdl = nq_pdl)
                liquidity_es = get_liquidity_values(symbol= es_contract, candles_30m = historical_es, test_date=test_date, liquidity_levels=liquidity_es, current_start = current_30m_start, pdh = es_pdh, pdl = es_pdl)
                
                # at 1am store ob_level formed before 1am
                # storing OB levels formed before 1am as key level and removing old active candidates
                if dt_current.hour == 1 and dt_current.minute == 00:
                    # add bearish and bullish ob levels to liquidity levels
                    bullish_nq_ob_level = nq_buy_candidate.ob_level if nq_buy_candidate.final_ob_confirmed else None
                    bullish_es_ob_level = es_buy_candidate.ob_level if es_buy_candidate.final_ob_confirmed else None
                    bearish_nq_ob_level = nq_sell_candidate.ob_level if nq_sell_candidate.final_ob_confirmed else None
                    bearish_es_ob_level = es_sell_candidate.ob_level if es_sell_candidate.final_ob_confirmed else None
                    add_1am_ob_mitigation_levels(liquidity_levels=liquidity_nq, bullish_ob_level=bullish_nq_ob_level, bearish_ob_level=bearish_nq_ob_level)
                    add_1am_ob_mitigation_levels(liquidity_levels=liquidity_es, bullish_ob_level= bullish_es_ob_level, bearish_ob_level=bearish_es_ob_level)
                    # reset active candidates
                    nq_buy_candidate.reset()
                    es_buy_candidate.reset()
                    nq_sell_candidate.reset()
                    es_sell_candidate.reset()

                # update london context with IBS
                if dt.hour == 1 and dt.minute == 30:
                    nq_london_market_context.set_18_1am_ibs(nq_seven_hour_builder.candles["6PM"].values(),nq_seven_hour_builder.candles["1AM"].values())
                    es_london_market_context.set_18_1am_ibs(es_seven_hour_builder.candles["6PM"].values(),es_seven_hour_builder.candles["1AM"].values())
                    # print("nq london structure: ", nq_london_market_context.structure)
                    # print("es london structure: ", es_london_market_context.structure)
                    
                # update london context with 2AM 4hr IB
                if dt.hour == 2 and dt.minute == 00:
                    nq_london_market_context.set_2am_ib(last_closed_nq)
                    es_london_market_context.set_2am_ib(last_closed_es)
                    # print("nq 2am IB: ", nq_london_market_context.ib_2)
                    # print("es 2am IB: ", es_london_market_context.ib_2)
                    # update ob_levels if new are formed after 1am IB
                    bullish_nq_ob_level = nq_buy_candidate.ob_level if nq_buy_candidate.final_ob_confirmed else None
                    bullish_es_ob_level = es_buy_candidate.ob_level if es_buy_candidate.final_ob_confirmed else None
                    bearish_nq_ob_level = nq_sell_candidate.ob_level if nq_sell_candidate.final_ob_confirmed else None
                    bearish_es_ob_level = es_sell_candidate.ob_level if es_sell_candidate.final_ob_confirmed else None
                    add_1am_ob_mitigation_levels(liquidity_levels=liquidity_nq, bullish_ob_level=bullish_nq_ob_level, bearish_ob_level=bearish_nq_ob_level)
                    add_1am_ob_mitigation_levels(liquidity_levels=liquidity_es, bullish_ob_level= bullish_es_ob_level, bearish_ob_level=bearish_es_ob_level)
                
                # update london context
                if dt.hour > 1 and dt.hour < 8:
                    nq_london_market_context.update(last_closed_nq, liquidity_nq)
                    es_london_market_context.update(last_closed_es, liquidity_es)
                
                # at 8am store ob_level formed before 8am
                # calling this block at dt.hour == 8 intead of 7 beacause ob detection is below towards the end
                if dt.hour == 8 and dt.minute == 30:
                    print("8:30 candle")
                if dt.hour == 8 and dt.minute == 00:
                    # add bearish and bullish ob levels to liquidity levels
                    bullish_nq_ob_level = nq_buy_candidate.ob_level if nq_buy_candidate.final_ob_confirmed else None
                    bullish_es_ob_level = es_buy_candidate.ob_level if es_buy_candidate.final_ob_confirmed else None
                    bearish_nq_ob_level = nq_sell_candidate.ob_level if nq_sell_candidate.final_ob_confirmed else None
                    bearish_es_ob_level = es_sell_candidate.ob_level if es_sell_candidate.final_ob_confirmed else None
                    # print("bullish_nq_ob_level: ", bullish_nq_ob_level)
                    # print("bullish_es_ob_level: ", bullish_es_ob_level)
                    # print("bearish_nq_ob_level: ", bearish_nq_ob_level)
                    # print("bearish_es_ob_level: ", bearish_es_ob_level)

                    add_8am_ob_mitigation_levels(liquidity_levels=liquidity_nq, bullish_ob_level=bullish_nq_ob_level, bearish_ob_level=bearish_nq_ob_level)
                    add_8am_ob_mitigation_levels(liquidity_levels=liquidity_es, bullish_ob_level= bullish_es_ob_level, bearish_ob_level=bearish_es_ob_level)
                    # reset active candidates
                    nq_buy_candidate.reset()
                    es_buy_candidate.reset()
                    nq_sell_candidate.reset()
                    es_sell_candidate.reset()
                # update new york context with IBs
                if dt_current.hour == 9 and dt_current.minute == 00:
                    
                    nq_ny_market_context.set_8am_ib(nq_seven_hour_builder.candles, nq_london_market_context.ib_18, nq_london_market_context.ib_1)
                    es_ny_market_context.set_8am_ib(es_seven_hour_builder.candles, es_london_market_context.ib_18, es_london_market_context.ib_1)
                    # print("test 1: ", nq_ny_market_context.structure)
                    # print("rest es: ", es_ny_market_context.structure)
                    # print("add new mitigation or equilibrium level to liquidity key levels")
                    # print("xxib8am: ",  nq_seven_hour_builder.candles["8AM"].values())
                    # print("xxib8am: ",  es_seven_hour_builder.candles["8AM"].values())
                    # print("es liquidity levels: ", liquidity_es)
                    # send nyam summary at 9am est
                    summary_message = build_summary_alert(nq_ny_market_context, es_ny_market_context, current_30m_start)
                    send_newyork_summary(summary_message)
                    
                    bullish_nq_ob_level = nq_buy_candidate.ob_level if nq_buy_candidate.final_ob_confirmed else None
                    bullish_es_ob_level = es_buy_candidate.ob_level if es_buy_candidate.final_ob_confirmed else None
                    bearish_nq_ob_level = nq_sell_candidate.ob_level if nq_sell_candidate.final_ob_confirmed else None
                    bearish_es_ob_level = es_sell_candidate.ob_level if es_sell_candidate.final_ob_confirmed else None
                    # add ob mitigation levels formed before or after 8am
                    add_8am_ob_mitigation_levels(liquidity_levels=liquidity_nq, bullish_ob_level=bullish_nq_ob_level, bearish_ob_level=bearish_nq_ob_level)
                    add_8am_ob_mitigation_levels(liquidity_levels=liquidity_es, bullish_ob_level= bullish_es_ob_level, bearish_ob_level=bearish_es_ob_level)
                    
                    
                if dt.hour == 10 and dt.minute == 0:
                    nq_ny_market_context.set_10am_ib(last_closed_nq)
                    es_ny_market_context.set_10am_ib(last_closed_es)
                    
                
                # update market context for NQ and ES
                nq_market_context.update_session_range(last_closed_nq["high"], last_closed_nq["low"], last_closed_nq["open"], last_closed_nq["close"], dt.hour, dt.minute, last_closed_candle_timestamp)
                es_market_context.update_session_range(last_closed_es["high"], last_closed_es["low"], last_closed_es["open"], last_closed_es["close"], dt.hour, dt.minute, last_closed_candle_timestamp)
                # print("session_open: ", nq_market_context.session_open)
                # print("session_high: ", nq_market_context.session_high)
                # print("session_low: ", nq_market_context.session_low)
                # print("session_close: ", nq_market_context.session_close)
                # update Newyork Context
                if dt.hour > 8 and dt.hour < 15:
                    nq_ny_market_context.update(last_closed_nq, liquidity_nq)
                    es_ny_market_context.update(last_closed_es, liquidity_es)
                    
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
                    
                # call set_ib towards the end so ib_ready is true for the next candle
                # populate IB for NQ and ES
                if dt_current.hour == 9:
                    # update Ib setup 
                    nq_ib_candidate.update(nq_seven_hour_builder.candles["8AM"].values())
                    es_ib_candidate.update(es_seven_hour_builder.candles["8AM"].values())
                    nq_market_context.set_ib(nq_ib_candidate.ib_high, nq_ib_candidate.ib_low)
                    es_market_context.set_ib(es_ib_candidate.ib_high, es_ib_candidate.ib_low)
                
        # Always monitor open trades
        monitor_open_trades(candle_3m)
    print("checkval: ", checkval)

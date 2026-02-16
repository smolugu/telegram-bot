from data.market_data import fetch_symbol_data
from modules.orchestrator import evaluate_7h_setup
from helpers.zones import get_7h_open_from_timestamp

from datetime import datetime
from modules.sweep_detector import find_swing_highs, find_swing_lows


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


def run_quick_backtest(test_date: str):

    print(f"Backtesting {test_date}")

    nq = fetch_symbol_data("NQ=F")
    es = fetch_symbol_data("ES=F")
    nq_30m = [c for c in nq["30m"] if test_date in c["timestamp"]]
    debug_print_30m_swings(nq_30m, test_date)

    # if not nq or not es:
    #     print("No data available.")
    #     return

    # nq_3m = [c for c in nq["3m"] if test_date in c["timestamp"]]
    # es_3m = [c for c in es["3m"] if test_date in c["timestamp"]]
    # print("Total 3m candles for date:", len(nq_3m))
    


    # for i in range(30, len(nq_3m)):

    #     current_ts = nq_3m[i]["timestamp"]
    #     # print("Current 3m ts:", current_ts)
    #     # ⬇️ Only evaluate on 30m closes
    #     ts_dt = datetime.fromisoformat(current_ts)

    #     if ts_dt.minute % 30 != 0:
    #         continue

    #     seven_open = get_7h_open_from_timestamp(current_ts)

    #     partial_market_data = {
    #         "NQ": {
    #             "30m": nq["30m"],
    #             "1h": nq["1h"],
    #             "3m": nq_3m[:i],
    #             "protected_high": None,
    #             "protected_low": None
    #         },
    #         "ES": {
    #             "30m": es["30m"],
    #             "1h": es["1h"],
    #             "3m": es_3m[:i],
    #             "protected_high": None,
    #             "protected_low": None
    #         },
    #         "daily": nq["30m"],
    #         "current_price": nq_3m[i]["close"]
    #     }
        
    #     result = evaluate_7h_setup(
    #         market_data=partial_market_data,
    #         seven_hour_open_ts=seven_open,
    #         wick_window_minutes=60
    #     )

    #     if result["stage"] != "NONE":
    #         print(
    #             current_ts,
    #             result["stage"],
    #             result.get("smt")
    #         )
        

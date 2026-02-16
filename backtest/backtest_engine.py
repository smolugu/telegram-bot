from data.market_data import fetch_symbol_data
from modules.orchestrator import evaluate_7h_setup
from helpers.zones import get_current_7h_open
import pandas as pd


def run_backtest(symbol_date: str):

    print(f"Running backtest for {symbol_date}")

    nq = fetch_symbol_data("NQ=F")
    es = fetch_symbol_data("ES=F")

    if not nq or not es:
        print("No data available.")
        return

    # Filter only that date
    nq_3m = [c for c in nq["3m"] if symbol_date in c["timestamp"]]
    es_3m = [c for c in es["3m"] if symbol_date in c["timestamp"]]

    if not nq_3m:
        print("No 3m data for date.")
        return

    for i in range(20, len(nq_3m)):  # start after some candles exist
        current_ts = nq_3m[i]["timestamp"]

        partial_market_data = build_partial_market_data(
            nq, es, nq_3m, es_3m, i, current_ts
        )

        # partial_market_data = build_partial_market_data(
        #     nq, es, nq_3m, es_3m, i
        # )

        result = evaluate_7h_setup(
            market_data=partial_market_data,
            seven_hour_open_ts=get_current_7h_open(),
            wick_window_minutes=60
        )

        if result["stage"] != "NONE":
            print(
                nq_3m[i]["timestamp"],
                result["stage"],
                result.get("smt")
            )


def build_partial_market_data(nq_full, es_full, nq_3m, es_3m, i, current_ts):

    return {
        "NQ": {
            # "30m": nq_full["30m"],
            # "1h": nq_full["1h"],
            "30m": [c for c in nq_full["30m"] if c["timestamp"] <= current_ts],
            "1h": [c for c in nq_full["1h"] if c["timestamp"] <= current_ts],
            "3m": nq_3m[:i],
            "protected_high": None,
            "protected_low": None
        },
        "ES": {
            # "30m": es_full["30m"],
            # "1h": es_full["1h"],
            "30m": [c for c in nq_full["30m"] if c["timestamp"] <= current_ts],
            "1h": [c for c in nq_full["1h"] if c["timestamp"] <= current_ts],
            "3m": es_3m[:i],
            "protected_high": None,
            "protected_low": None
        },
        "daily": nq_full["30m"],  # placeholder
        "current_price": nq_3m[i]["close"]
    }

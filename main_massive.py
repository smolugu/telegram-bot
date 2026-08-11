import sqlite3
import time
import os
from zoneinfo import ZoneInfo
import pytz
import asyncio

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from database.session import SessionLocal
from market_data.htf.htf_candle_builder import HTFCandleBuilder
from market_data.repository.sqlite_candle_repository import SQLiteCandleRepository


from backtest.quick_test import run_quick_test
from config.settings import BOT_TOKEN, POLYGON_API_KEY
from market_data.api.massive_rest import MassiveREST
from market_data.providers.massive_futures_provider import FuturesProvider, MassiveFuturesProvider
from data.sqlite.db import init_db
from data.market_data import fetch_market_data

from datetime import date, datetime, timedelta

from engine.trading_engine import trading_engine_loop
from bot.handlers import register_handlers
from dotenv import load_dotenv

from market_data.repository.sqlite_contract_repository import SQLiteContractRepository
from market_data.services.history_loader import HistoryLoader
from modules.orchestrator import evaluate_7h_setup
from helpers.zones import get_current_7h_open
from alerts.alert_engine import handle_stage


from backtest.quick_backtest import run_quick_backtest


load_dotenv()

# client = MassiveREST(POLYGON_API_KEY)
# provider = FuturesProvider(client)
WICK_WINDOW_MINUTES = 60
CHECK_INTERVAL_SECONDS = 180
GRACE_SECONDS = 10
NY = pytz.timezone("America/New_York")
MODE = "BACKTEST"   # change to "LIVE" when done

def wait_until_next_3m_close():
    now = datetime.now(NY)
    minute = now.minute
    second = now.second

    # Find next multiple of 3
    next_minute = minute + (3 - minute % 3)

    if next_minute >= 60:
        next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    else:
        next_time = now.replace(minute=next_minute, second=0, microsecond=0)

    sleep_seconds = (next_time - now).total_seconds()

    if sleep_seconds > 0:
        time.sleep(sleep_seconds)
    


async def on_startup(application):
    print("Bot started. Launching trading engine...")
    asyncio.create_task(trading_engine_loop(application))

def run(bot):
    while True:
        wait_until_next_3m_close()

        # Grace delay after candle close
        time.sleep(GRACE_SECONDS)
        
        try:
            market_data = fetch_market_data()
            result = evaluate_7h_setup(
                market_data=market_data,
                seven_hour_open_ts=get_current_7h_open(),
                wick_window_minutes=WICK_WINDOW_MINUTES
            )

            handle_stage(result, bot)

        except Exception as e:
            print("Error:", e)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ *Hello! Your bot is running on macOS Monterey.\n"
        "Python 3.12 + MacPorts + venv ✨"
    )

def main():
    init_db()  # initialize database if needed
    
    if MODE == "BACKTEST":

        with SessionLocal() as session:
            repo = SQLiteCandleRepository(session)

            latest = repo.latest_timestamp("NQ", 1)

            print("latest: ", latest)
        rest = MassiveREST(POLYGON_API_KEY)

        provider = MassiveFuturesProvider(rest)
        session = SessionLocal()
        contract_repo = SQLiteContractRepository(session)
        candle_repo = SQLiteCandleRepository(session)
        loader = HistoryLoader(
            provider=provider,
            contract_repo=contract_repo,
            candle_repo=candle_repo,
        )
        # sync contracts
        for instrument in ["NQ", "ES"]:
            loader.sync_contracts(instrument)
        contract_info_nq = contract_repo.get_front_month("NQ")
        contract_info_es = contract_repo.get_front_month("ES")
        
        print("contract_info_nq: ", contract_info_nq)
        print("contract_info_es: ", contract_info_es)
        print("=========")
        for instrument in ["NQ", "ES"]:
            loader.sync_history(instrument)

        candles_1m = candle_repo.get_all(
            instrument="NQ",
            timeframe=1,
        )
        print("1m candles lenght: from get_all: ")
        print(len(candles_1m))
        print(candles_1m[0])
        print(candles_1m[-1])

        # candle_builder = HTFCandleBuilder()

        # candles_30m = candle_builder.build(
        #     candles_1m,
        #     timeframe=30,
        # )
        candles_30m = candle_repo.get_history(
            contract=contract_info_nq.contract,
            timeframe=30,
        )
        print("-----------")
        print(candles_1m[0].timestamp)
        
        print("-----------")
        print("candle length from get all:")
        print(len(candles_30m))
        print(candles_30m[0])
        print(candles_30m[-1])
        first = candles_30m[0].timestamp_ny
        last = candles_30m[-1].timestamp_ny
        print(candles_30m[0].timestamp_ny.hour)
        print(candles_30m[-1].timestamp_ny.hour)
        print("first:", first.strftime("%Y-%m-%d %H:%M:%S %Z"))
        print("last :", last.strftime("%Y-%m-%d %H:%M:%S %Z"))

        for candle in candles_30m[:10]:
            print(candle)

        

        # print(response.data.decode())
        # import requests

        # url = "https://api.massive.com/futures/v1/aggs/NQU6"

        # params = {
        #     "resolution": "1min",
        #     "window_start": "2026-07-15",
        #     "limit": 5,
        #     "apiKey": POLYGON_API_KEY,
        # }

        # r = requests.get(url, params=params)
        # print("***")
        # print(r.status_code)
        # print(r.text)
        # print(type(client.client))
        # print(dir(client.client))
        # import inspect

        # print(inspect.signature(client.client.list_futures_aggregates))
        # import requests

        # url = "https://api.massive.com/futures/v1/aggs/NQU26"

        # params = {
        #     "resolution": "1min",
        #     "window_start": "2025-12-15",
        #     "limit": 5,
        #     "apiKey": POLYGON_API_KEY,
        # }

        # r = requests.get(url, params=params)
        # print("****")
        # print(r.status_code)
        # print(r.text)
        run_quick_backtest("2026-07-31")
        # run_quick_test("2026-04-21")
        return
    # token = os.getenv("BOT_TOKEN")
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    register_handlers(application)

    application.post_init = on_startup
    print("Chartless bot is running...")
    application.run_polling()
    # token = os.getenv("BOT_TOKEN")
    # if not token:
    #     raise RuntimeError("BOT_TOKEN not found in .env")

    # app = ApplicationBuilder().token(token).build()
    # app.add_handler(CommandHandler("start", start))
    # app.add_handler(CommandHandler("subscribe", subscribe))
    # app.add_handler(CommandHandler("unsubscribe", unsubscribe))
    # app.add_handler(CommandHandler("testalert", testalert))
    # print("Chartless bot is running...")
    # app.run_polling()

if __name__ == "__main__":
    main()

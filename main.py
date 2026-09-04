import sqlite3
import time
import os
from zoneinfo import ZoneInfo
import pytz
import asyncio

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from database.session import SessionLocal
from market_data.api.projectx_rest import ProjectXREST
from market_data.contracts.contracts_mapper import ContractMapper
from market_data.htf.htf_candle_builder import HTFCandleBuilder, inspect_1m_gaps
from market_data.providers.projectx_futures_provider import ProjectXFuturesProvider
from market_data.repository.sqlite_candle_repository import SQLiteCandleRepository

from backtest.quick_test import run_quick_test
from config.settings import BOT_TOKEN, POLYGON_API_KEY, PROJECTX_API_KEY, PROJECTX_USERNAME
from market_data.api.massive_rest import MassiveREST
from market_data.providers.massive_futures_provider import FuturesProvider, MassiveFuturesProvider
from data.sqlite.db import init_db
from data.market_data import fetch_market_data

from datetime import date, datetime, timedelta, timezone

from engine.trading_engine import trading_engine_loop
from bot.handlers import register_handlers
from dotenv import load_dotenv

from market_data.repository.sqlite_contract_repository import SQLiteContractRepository
from market_data.services.massive_contracts_history_loader import MassiveContractsHistoryLoader
from market_data.services.projectx_candle_history_loader import ProjectxCandlesHistoryLoader
from market_data.services.set_rollovers import set_rollover_dates
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

            # latest = repo.latest_timestamp("NQ", 1)

            # print("latest: ", latest)
        rest = MassiveREST(POLYGON_API_KEY)

        provider = MassiveFuturesProvider(rest)
        session = SessionLocal()
        contract_repo = SQLiteContractRepository(session)
        candle_repo = SQLiteCandleRepository(session)
        loader = MassiveContractsHistoryLoader(
            provider=provider,
            contract_repo=contract_repo,
            candle_repo=candle_repo,
        )
        
        mapper = ContractMapper()
        mapper.add("NQU6", "CON.F.US.ENQ.U26")
        mapper.add("ESU6", "CON.F.US.EP.U26")
        mapper.add("ESM6","CON.F.US.EP.M26",
        )
        

        print(mapper.to_projectx("ESU6"))
        print(mapper.from_projectx("CON.F.US.EP.U26"))
        projectx_rest = ProjectXREST(
            username=PROJECTX_USERNAME,
            api_key=PROJECTX_API_KEY,
        )


        projectx_provider = ProjectXFuturesProvider(
            rest=projectx_rest,
            contract_mapper=mapper,
        )
        candle_loader = ProjectxCandlesHistoryLoader(
            provider=projectx_provider,
            contract_repo=contract_repo,
            candle_repo=candle_repo,
        )
        # latest = candle_repo.latest_timestamp_by_contract(
        #     contract="ESU6",
        #     timeframe=1,
        # )

        # end = datetime.now(timezone.utc)
        
        # start = end - timedelta(hours=1)
        # start = latest + timedelta(minutes=1)
        # end = start + timedelta(minutes=30)
        # start = datetime(
        #     2026, 5, 11, 13, 0,
        #     tzinfo=timezone.utc,
        # )
        # end = start + timedelta(hours=1)
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=30)

        # contracts = projectx_rest.search_contracts(
        #     search_text="ES",
        #     live=False,
        # )
        # contracts = projectx_rest.search_contracts(
        #     search_text="NQU6",
        #     live=False,
        # )
        # contracts = projectx_rest.search_contracts(
        #     search_text="ESU",
        #     live=False,
        # )
        # print("contracts: ", contracts)
        # latest = candle_repo.latest_timestamp_by_contract(
        #     contract="ESU6",
        #     timeframe=1,
        # )

        # start = latest + timedelta(minutes=1)
        # end = datetime.now(timezone.utc)

        # print("DB latest:", latest)
        # print("Requesting:", start, "→", end)
        # end = datetime.now(timezone.utc)
        # start = end - timedelta(hours=24)
        # start = datetime(
        #     2026, 8, 23, 0, 0,
        #     tzinfo=timezone.utc,
        # )

        # end = datetime(
        #     2026, 9, 3, 0, 0,
        #     tzinfo=timezone.utc,
        # )

        # candles = projectx_provider.get_history(
        #     instrument="ES",
        #     contract="ESU6",
        #     timeframe=1,
        #     start=start,
        #     end=end,
        #     latest=latest,
        # )
        # if candles:
        #     candle_repo.save(candles)
        #     print(f"Saved {len(candles)} candles")
        # print("Received:", len(candles))

        # for candle in candles:
        #     print(
        #         candle.timestamp,
        #         candle.open,
        #         candle.high,
        #         candle.low,
        #         candle.close,
        #         candle.volume,
        #     )
        # latest = candle_repo.latest_timestamp_by_contract(
        #     contract="ESU6",
        #     timeframe=1,
        # )

        # print("Latest:", latest)

        # ========================================
        # ========================================
        # Get historical contracts from massive
        # ========================================
        # ========================================
        # snapshot_dates = [
        #     date(2024, 9, 1),
        #     date(2024, 12, 1),
        #     date(2025, 3, 1),
        #     date(2025, 6, 1),
        #     date(2025, 9, 1),
        #     date(2025, 12, 1),
        #     date(2026, 3, 1),
        #     date(2026, 6, 1),
        #     date(2026, 7, 30),
        #     date(2026, 8, 30),
        # ]
        # getting historical contracts from massive
        # contracts = provider.get_historical_contracts(
        #     instrument="NQ",
        #     snapshot_dates=snapshot_dates,
        # )
        # contract_repo.save(contracts)
        # contracts = provider.get_historical_contracts(
        #     instrument="ES",
        #     snapshot_dates=snapshot_dates,
        # )
        # contract_repo.save(contracts)
        
        # for contract in contracts:
        #     print("contracts:")
        #     print(
        #         contract.contract,
        #         contract.first_trade_date,
        #         contract.last_trade_date,
        #         contract.rollover_date
        #     )
        
        # contracts = contract_repo.get_all(
        #     instrument="NQ",
        # )

        # for contract in contracts:
        #     print("contracts:")
        #     print(
        #         contract.contract,
        #         contract.first_trade_date,
        #         contract.last_trade_date,
        #     )

        # sync contracts daily
        for instrument in ["NQ", "ES"]:
            loader.sync_contracts(instrument)
        contract_info_nq = contract_repo.get_front_month("NQ", date.today())
        next_contract = contract_repo.get_next_contract(
            "NQ",
            contract_info_nq.contract,
        )
        contract_info_es = contract_repo.get_front_month("ES", date.today())
        
        print("contract_info_nq: ", contract_info_nq)
        print("next nq contract: ", next_contract)
        print("contract_info_es: ", contract_info_es)

        # map current contract to projectx contract and get projectx contract id
        nq_projectx_id = projectx_provider.resolve_contract(contract_info_nq.contract)
        es_projectx_id = projectx_provider.resolve_contract(contract_info_es.contract)

        print("NQ ProjectX ID:", nq_projectx_id)
        print("ES ProjectX ID:", es_projectx_id)

        # once we know the current contract ids, sync database with 1m candles
        # get lastest candles from db by current contract
        # sync candles daily
        for instrument in ["NQ", "ES"]:
            candle_loader.sync_candles(instrument)

        # NQ
        # nq_latest = candle_repo.latest_timestamp_by_contract(
        #     contract=contract_info_nq.contract,
        #     timeframe=1,
        # )
        # start = nq_latest + timedelta(minutes=1)
        # end = datetime.now(timezone.utc)
        # nq_candles = projectx_provider.get_history(
        #     instrument="NQ",
        #     contract=nq_projectx_id,
        #     timeframe=1,
        #     start=start,
        #     end=end,
        #     latest=nq_latest,
        # )
        # if nq_candles:
        #     candle_repo.save(nq_candles)
        #     print(f"Saved {len(nq_candles)} candles")
        # print("NQ candles Received:", len(nq_candles))

        # for candle in nq_candles:
        #     print(
        #         candle.timestamp,
        #         candle.open,
        #         candle.high,
        #         candle.low,
        #         candle.close,
        #         candle.volume,
        #     )
        # ES
        # es_latest = candle_repo.latest_timestamp_by_contract(
        #     contract=contract_info_es.contract,
        #     timeframe=1,
        # )
        # start = es_latest + timedelta(minutes=1)
        # end = datetime.now(timezone.utc)
        # es_candles = projectx_provider.get_history(
        #     instrument="ES",
        #     contract=es_projectx_id,
        #     timeframe=1,
        #     start=start,
        #     end=end,
        #     latest=es_latest,
        # )
        # if es_candles:
        #     candle_repo.save(es_candles)
        #     print(f"Saved {len(es_candles)} candles")
        # print("ES candles Received:", len(es_candles))

        # for candle in es_candles:
        #     print(
        #         candle.timestamp,
        #         candle.open,
        #         candle.high,
        #         candle.low,
        #         candle.close,
        #         candle.volume,
        #     )

        print("=========")
        # print("getting full history")
        # loader.download_full_history(
        #     instrument="NQ",
        #     timeframe=1,
        # )
        

        # print("1m:", len(candles_1m))

        # builder = HTFCandleBuilder()

        # candles_3m = builder.build(
        #     candles=candles_1m,
        #     timeframe=3,
        # )

        # print("3m:", len(candles_3m))

        # candles_30m = builder.build(
        #     candles=candles_1m,
        #     timeframe=30,
        # )

        # print("30m:", len(candles_30m))
        # latest = candle_repo.latest_timestamp(
        #     contract="NQU6",
        #     timeframe="3",
        # )
        # print("latest HTF timestamp:", latest)
        # for timeframe in [1, 3, 30, 60, 240, 420]:

        #     candles = candle_repo.get_history(
        #         contract="NQU6",
        #         timeframe=timeframe,
        #     )

        #     if candles:
        #         print(
        #             f"{timeframe}m: "
        #             f"{candles[0].timestamp} → "
        #             f"{candles[-1].timestamp}"
        #         )

        # candles_7h = HTFCandleBuilder().build(
        #     candles=candles_1m,
        #     timeframe=420,
        # )

        # print("7H candles:", len(candles_7h))

        # for candle in candles_7h[:10]:
        #     print(
        #         candle.timestamp,
        #         candle.timestamp.astimezone(
        #             ZoneInfo("America/New_York")
        #         )
        #     )

        # candles_4h = HTFCandleBuilder().build(
        #     candles=candles_1m,
        #     timeframe=240,
        # )

        # print("4H candles:", len(candles_4h))

        # for candle in candles_7h[:10]:
        #     print(
        #         candle.timestamp,
        #         candle.timestamp.astimezone(
        #             ZoneInfo("America/New_York")
        #         )
        #     )
        print("=========")
        # for instrument in ["NQ", "ES"]:
        #     loader.sync_history(instrument)

        # candles_1m = candle_repo.get_all(
        #     instrument="NQ",
        #     timeframe=1,
        # )
        # print("1m candles lenght: from get_all: ")
        # print(len(candles_1m))
        # print(candles_1m[0])
        # print(candles_1m[-1])

        # candle_builder = HTFCandleBuilder()

        # candles_30m = candle_builder.build(
        #     candles_1m,
        #     timeframe=30,
        # )
        # candles_30m = candle_repo.get_history(
        #     contract=contract_info_nq.contract,
        #     timeframe=30,
        # )
        # print("-----------")
        # print(candles_1m[0].timestamp)
        
        # print("-----------")
        # print("candle length from get all:")
        # print(len(candles_30m))
        # print(candles_30m[0])
        # print(candles_30m[-1])
        # first = candles_30m[0].timestamp_ny
        # last = candles_30m[-1].timestamp_ny
        # print(candles_30m[0].timestamp_ny.hour)
        # print(candles_30m[-1].timestamp_ny.hour)
        # print("first:", first.strftime("%Y-%m-%d %H:%M:%S %Z"))
        # print("last :", last.strftime("%Y-%m-%d %H:%M:%S %Z"))

        # for candle in candles_30m[:10]:
        #     print(candle)

        

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
        # run_quick_backtest("2026-08-26")
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

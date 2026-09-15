import sqlite3
import time
import os
from zoneinfo import ZoneInfo
import pytz
import asyncio

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from data.models.candle import Candle
from database.session import SessionLocal
from market_data.api.projectx.rest.projectx_rest import ProjectXREST
from market_data.api.projectx.websocket.projectx_websocket import ProjectXWebSocket
from market_data.candle_builder.htf_candle_builder import HTF_1H, HTF_30M, HTF_3M, HTF_4H, HTF_7H, HTF_D, HTF_NY_TZ, UTC_TZ, HTFCandleBuilder, HTFDefinition
from market_data.candle_builder.minute_candle_builder import MinuteCandleBuilder
from market_data.contracts.contracts_mapper import ContractMapper
from market_data.htf.htf_candle_builder import inspect_1m_gaps
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
from market_data.scheduler.scheduler import Scheduler
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

        projectx_session = SessionLocal()
        projectx_contract_repo = SQLiteContractRepository(
            projectx_session
        )

        projectx_candle_repo = SQLiteCandleRepository(
            projectx_session
        )

        projectx_provider = ProjectXFuturesProvider(
            rest=projectx_rest,
            contract_mapper=mapper,
        )
        projectx_history_candle_loader = ProjectxCandlesHistoryLoader(
            provider=projectx_provider,
            contract_repo=projectx_contract_repo,
            candle_repo=projectx_candle_repo,
        )
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
            projectx_history_candle_loader.sync_candles(instrument)

        
        print("=========")

        # ================================
        # ProjectX Websocket Connection
        # ================================
        
        # Callback for completed realtime candles
        def save_realtime_candle(candle: Candle) -> None:
            projectx_candle_repo.save([candle])

            print(
                f"Saved realtime candle: "
                f"{candle.instrument} "
                f"{candle.contract} "
                f"{candle.timestamp}"
            )
        # test
        
        # start = datetime(
        #     2026, 9, 7, 15, 0,
        #     tzinfo=timezone.utc,
        # )

        # end = datetime(
        #     2026, 9, 7, 15, 29,
        #     tzinfo=timezone.utc,
        # )

        # candles = candle_repo.get_between(
        #     contract="NQU6",
        #     timeframe=1,
        #     start=start,
        #     end=end,
        # )

        # print("COUNT:", len(candles))

        # for candle in candles[:3]:
        #     print("FIRST:", candle)

        # for candle in candles[-3:]:
        #     print("LAST:", candle)
        
        # latest = candle_repo.latest_timestamp_by_contract(
        #     "NQU6",
        #     timeframe=1,
        # )

        # print("LATEST NQ:", latest)

        # Create builder
        builder = MinuteCandleBuilder(
            on_candle=save_realtime_candle
        )
        htf_builder = HTFCandleBuilder(
            candle_repo=projectx_candle_repo,
            on_candle=save_realtime_candle,
            history_loader=projectx_history_candle_loader,
        )

        UTC_TZ = ZoneInfo("UTC")
        # NY_TZ = ZoneInfo("America/New_York")

        # tests = [
        #     # ---------------------------------------------------------
        #     # 7H completion boundaries
        #     # ---------------------------------------------------------
        #     ("7H", 420, "2026-09-09 01:00"),
        #     ("7H", 420, "2026-09-09 08:00"),
        #     ("7H", 420, "2026-09-09 15:00"),
        #     ("7H", 420, "2026-09-09 17:00"),
        #     ("7H", 420, "2026-09-09 18:00"),

        #     # ---------------------------------------------------------
        #     # 4H completion boundaries
        #     # ---------------------------------------------------------
        #     ("4H", 240, "2026-09-08 22:00"),
        #     ("4H", 240, "2026-09-09 02:00"),
        #     ("4H", 240, "2026-09-09 06:00"),
        #     ("4H", 240, "2026-09-09 10:00"),
        #     ("4H", 240, "2026-09-09 14:00"),
        #     ("4H", 240, "2026-09-09 17:00"),
        #     ("4H", 240, "2026-09-09 18:00"),
        # ]

        # for name, timeframe, ny_string in tests:

        #     completion_ny = datetime.strptime(
        #         ny_string,
        #         "%Y-%m-%d %H:%M",
        #     ).replace(tzinfo=NY_TZ)

        #     completion_utc = completion_ny.astimezone(UTC_TZ)

        #     definition = HTFDefinition(
        #         timeframe=timeframe,
        #         name=name,
        #     )

        #     start_utc, end_utc = htf_builder._get_completed_period(
        #         completion_utc,
        #         definition,
        #     )

        #     start_ny = start_utc.astimezone(NY_TZ)
        #     end_ny = end_utc.astimezone(NY_TZ)

        #     print(
        #         f"{name}: "
        #         f"completion={completion_ny.strftime('%m-%d %H:%M')} NY | "
        #         f"period="
        #         f"{start_ny.strftime('%m-%d %H:%M')} → "
        #         f"{end_ny.strftime('%m-%d %H:%M')} NY | "
        #         f"UTC="
        #         f"{start_utc.strftime('%m-%d %H:%M')} → "
        #         f"{end_utc.strftime('%m-%d %H:%M')}"
        #     )
        # start_utc = datetime(
        #     2026,
        #     9,
        #     9,
        #     5,
        #     0,
        #     tzinfo=ZoneInfo("UTC"),
        # )

        # end_utc = datetime(
        #     2026,
        #     9,
        #     9,
        #     12,
        #     0,
        #     tzinfo=ZoneInfo("UTC"),
        # )

        # candles = projectx_candle_repo.get_between(
        #     contract="NQU6",
        #     timeframe=1,
        #     start=start_utc,
        #     end=end_utc - timedelta(minutes=1),
        # )

        # print(f"Count: {len(candles)}")

        # if candles:
        #     print(f"First: {candles[0].timestamp}")
        #     print(f"Last:  {candles[-1].timestamp}")

        #     print(
        #         "First NY:",
        #         candles[0].timestamp.astimezone(HTF_NY_TZ),
        #     )

        #     print(
        #         "Last NY:",
        #         candles[-1].timestamp.astimezone(HTF_NY_TZ),
        #     )

        # definition = HTFDefinition(
        #     timeframe=420,
        #     name="7h",
        # )

        # candle = htf_builder.build_completed_candle(
        #     instrument="NQ",
        #     contract="NQU6",
        #     end_utc=datetime(
        #         2026,
        #         9,
        #         8,
        #         12,
        #         0,
        #         tzinfo=ZoneInfo("UTC"),
        #     ),
        #     definition=definition,
        # )

        # print(candle)
        
        # candle = htf_builder.build_completed_candle(
        #     instrument="NQ",
        #     contract="NQU6",
        #     end_utc=datetime(
        #         2026,
        #         9,
        #         8,
        #         14,
        #         33,
        #         tzinfo=ZoneInfo("UTC"),
        #     ),
        #     definition=HTFDefinition(
        #         timeframe=3,
        #         name="3m",
        #     ),
        # )

        # print(candle)
        # count = htf_builder.backfill_htf(
        #     instrument="NQ",
        #     contract="NQU6",
        #     start_utc=datetime(
        #         2026, 9, 7, 21, 0,
        #         tzinfo=UTC_TZ,
        #     ),
        #     end_utc=datetime(
        #         2026, 9, 9, 0, 0,
        #         tzinfo=UTC_TZ,
        #     ),
        #     definition=HTFDefinition(
        #         timeframe=240,
        #         name="4h",
        #     ),
        # )

        # print("Built:", count)
        # count = htf_builder.backfill_contract_htf_history(
        #     instrument="NQ",
        #     contract="NQU6",
        #     start_utc=datetime(
        #         2026, 9, 9, 21, 0,
        #         tzinfo=UTC_TZ,
        #     ),
        #     end_utc=datetime(
        #         2026, 9, 11, 0, 0,
        #         tzinfo=UTC_TZ,
        #     ),
        # )

        # print(count)
        
        
        # first_1m, last_1m = htf_builder._candle_repo.get_time_range(
        #     contract="NQU6",
        #     timeframe=1,
        # )

        # print("First 1m 2:", first_1m)
        # print("Last 1m 2:", last_1m)
        # print("First 1m 2:", first_1m.tzinfo)
        # print("Last 1m 2:", last_1m.tzinfo)

        # results = htf_builder.backfill_contract_htf_history(
        #     instrument="ES",
        #     contract="ESU6",
        # )
        # print(results)

        results = htf_builder.backfill_contract_htf_history(
            instrument="NQ",
            contract="NQU6",
        )
        print(results)


        # candles = htf_builder._candle_repo.get_between(
        #     contract="NQU6",
        #     timeframe=420,
        #     start=datetime(2026, 9, 8, 0, 0, tzinfo=UTC_TZ),
        #     end=datetime(2026, 9, 9, 0, 0, tzinfo=UTC_TZ),
        # )

        # for candle in candles:
        #     print(
        #         f"timestamp={candle.timestamp}, "
        #         f"tzinfo={candle.timestamp.tzinfo}, "
        #         f"NY={candle.timestamp_ny}"
        #     )
        # for day in [
        #     datetime(2026, 8, 10, tzinfo=UTC_TZ),
        #     datetime(2026, 8, 11, tzinfo=UTC_TZ),
        #     datetime(2026, 8, 12, tzinfo=UTC_TZ),
        #     datetime(2026, 9, 1, tzinfo=UTC_TZ),
        #     datetime(2026, 9, 2, tzinfo=UTC_TZ),
        #     datetime(2026, 9, 3, tzinfo=UTC_TZ),
        # ]:
        #     next_day = day + timedelta(days=1)

        #     candles = htf_builder._candle_repo.get_between(
        #         contract="NQU6",
        #         timeframe=1,
        #         start=day,
        #         end=next_day,
        #     )

        #     print(
        #         day.date(),
        #         "count=", len(candles),
        #         "first=", candles[0].timestamp if candles else None,
        #         "last=", candles[-1].timestamp if candles else None,
        #     )

        # Create ProjectX WebSocket connection
        # websocket_session = SessionLocal()

        # websocket_contract_repo = SQLiteContractRepository(
        #     websocket_session
        # )
        # projectx_websocket = ProjectXWebSocket(
        #     token=projectx_rest.token,
        #     contract_mapper=mapper,
        #     contract_repo=websocket_contract_repo,
        #     on_trade=builder.add_trade,
        # )

        # # Connect to ProjectX WebSocket and subscribe to trades for the current contracts
        # projectx_websocket.connect()

        # # Get the actual connection timestamp
        # builder.set_realtime_start(
        #     projectx_websocket.realtime_start
        # )

        # # Subscribe to trades for the current contracts
        # projectx_websocket.subscribe_trades(
        #     "CON.F.US.ENQ.U26"
        # )

        # projectx_websocket.subscribe_trades(
        #     "CON.F.US.EP.U26"
        # )
        # # Give the realtime feed some time to run
        # print("Waiting 10 seconds before reconciliation...")
        # time.sleep(10)

        # # Test REST reconciliation
        # # reconciled = projectx_history_candle_loader.reconcile_recent_candles(
        # #     "NQ",
        # #     lookback_minutes=60,
        # # )

        # # print(f"Reconciled NQ candles: {reconciled}")

        # # reconciled = projectx_history_candle_loader.reconcile_recent_candles(
        # #     "ES",
        # #     lookback_minutes=60,
        # # )
        
        def process_3m(end):
            print(">>> 3m processing started")

            nq_count = htf_builder.process_realtime_htf(
                instrument="NQ",
                contract="NQU6",
                boundary_utc=end,
                definition=HTF_3M,
            )

            es_count = htf_builder.process_realtime_htf(
                instrument="ES",
                contract="ESU6",
                boundary_utc=end,
                definition=HTF_3M,
            )

            print(
                f">>> 3m HTF processing complete: "
                f"NQ={nq_count}, ES={es_count}"
            )

        def process_30m_htf(end):
            print(">>> 30m HTF processing started")

            nq_count = htf_builder.process_realtime_htf(
                instrument="NQ",
                contract="NQU6",
                boundary_utc=end,
                definition=HTF_30M,
            )

            es_count = htf_builder.process_realtime_htf(
                instrument="ES",
                contract="ESU6",
                boundary_utc=end,
                definition=HTF_30M,
            )

            print(
                f">>> 30m HTF processing complete: "
                f"NQ={nq_count}, ES={es_count}"
            )

        def process_4h():
            print(">>> 4H processing started")

            end = datetime.now(timezone.utc).replace(
                second=0,
                microsecond=0,
            )

            nq_count = htf_builder.process_realtime_htf(
                instrument="NQ",
                contract="NQU6",
                boundary_utc=end,
                definition=HTF_4H,
            )

            es_count = htf_builder.process_realtime_htf(
                instrument="ES",
                contract="ESU6",
                boundary_utc=end,
                definition=HTF_4H,
            )

            print(
                f">>> 4H HTF processing complete: "
                f"NQ={nq_count}, ES={es_count}"
            )

        def process_7h():
            print(">>> 7H processing started")

            end = datetime.now(timezone.utc).replace(
                second=0,
                microsecond=0,
            )

            nq_count = htf_builder.process_realtime_htf(
                instrument="NQ",
                contract="NQU6",
                boundary_utc=end,
                definition=HTF_7H,
            )

            es_count = htf_builder.process_realtime_htf(
                instrument="ES",
                contract="ESU6",
                boundary_utc=end,
                definition=HTF_7H,
            )

            print(
                f">>> 7H HTF processing complete: "
                f"NQ={nq_count}, ES={es_count}"
            )

        def process_daily():
            print(">>> Daily processing started")

            end = datetime.now(timezone.utc).replace(
                second=0,
                microsecond=0,
            )

            nq_count = htf_builder.process_realtime_htf(
                instrument="NQ",
                contract="NQU6",
                boundary_utc=end,
                definition=HTF_D,
            )

            es_count = htf_builder.process_realtime_htf(
                instrument="ES",
                contract="ESU6",
                boundary_utc=end,
                definition=HTF_D,
            )

            print(
                f">>> Daily HTF processing complete: "
                f"NQ={nq_count}, ES={es_count}"
            )
        def process_ping():
            print("processing ping...")

        def process_30m():
            print(">>> 30m processing started")
            
            # Use one boundary timestamp for the entire pipeline.
            end = datetime.now(timezone.utc).replace(
                second=0,
                microsecond=0,
            )

            # Step 1: Reconcile recent 1m candles
            nq_reconciled = (
                projectx_history_candle_loader.reconcile_recent_candles(
                    "NQ",
                    lookback_minutes=60,
                )
            )

            es_reconciled = (
                projectx_history_candle_loader.reconcile_recent_candles(
                    "ES",
                    lookback_minutes=60,
                )
            )
            print(
                f">>> 30m reconciliation complete: "
                f"NQ={nq_reconciled}, ES={es_reconciled}"
            )
            # Rebuild 3m
            process_3m(end)

            # Build/rebuild 30m
            process_30m_htf(end)

            print(">>> 30m processing completed successfully")

            

        
        def process_scheduler_tasks():
            now_utc = datetime.now(timezone.utc).replace(
                second=0,
                microsecond=0,
            )

            if htf_builder.is_htf_boundary(now_utc, HTF_3M):
                process_3m()

            if htf_builder.is_htf_boundary(now_utc, HTF_30M):

                try:
                    process_30m()

                except Exception as e:
                    print(f">>> 30m processing FAILED: {e}")
                    print(">>> Ping skipped")

                else:
                    print(">>> 30m processing successful")
                    print(">>> Starting Ping")
                    process_ping(now_utc)
                
            if htf_builder.is_htf_boundary(now_utc, HTF_4H):
                process_4h()

            if htf_builder.is_htf_boundary(now_utc, HTF_7H):
                process_7h()

            if htf_builder.is_htf_boundary(now_utc, HTF_D):
                process_daily()
        # scheduler = Scheduler()

        # scheduler.add_boundary_job(
        #     name="30m_processing",
        #     minutes=30,
        #     callback=process_scheduler_tasks,
        # )

        # scheduler.start()

        # # Keep the WebSocket process alive
        # while True:
        #     time.sleep(1)

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
        # run_quick_backtest("2026-09-01")
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

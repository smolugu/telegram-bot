from datetime import datetime, timedelta
import pytz
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from engine.trading_engine import trading_engine_loop
from bot.handlers import register_handlers
from dotenv import load_dotenv
import os

import time
from data.market_data import fetch_market_data
from modules.orchestrator import evaluate_7h_setup
from alerts.alert_engine import handle_stage
from state.state_cache import reset_cycle
from helpers.zones import get_current_7h_open

from command_handlers.subscribe import subscribe
from command_handlers.unsubscribe import unsubscribe
from command_handlers.testalert import testalert
load_dotenv()
WICK_WINDOW_MINUTES = 60
CHECK_INTERVAL_SECONDS = 180
GRACE_SECONDS = 10
NY = pytz.timezone("America/New_York")

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
    token= os.getenv("BOT_TOKEN")
    application = ApplicationBuilder().token(token).build()

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

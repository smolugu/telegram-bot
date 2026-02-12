from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
import os

import time
from data.market_data import fetch_market_data
from modules.orchestrator import evaluate_7h_setup
from alerts.alert_engine import handle_stage
from state.state_cache import reset_cycle

from command_handlers.subscribe import subscribe
from command_handlers.unsubscribe import unsubscribe
from command_handlers.testalert import testalert
load_dotenv()
WICK_WINDOW_MINUTES = 60
CHECK_INTERVAL_SECONDS = 120

def run(bot):
    while True:
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

        time.sleep(CHECK_INTERVAL_SECONDS)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ *Hello! Your bot is running on macOS Monterey.\n"
        "Python 3.12 + MacPorts + venv ✨"
    )

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN not found in .env")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))
    app.add_handler(CommandHandler("testalert", testalert))
    print("Chartless bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

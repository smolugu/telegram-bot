from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
import os

from command_handlers.subscribe import subscribe
from command_handlers.unsubscribe import unsubscribe
from command_handlers.testalert import testalert



load_dotenv()

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

from telegram import Update
from telegram.ext import ContextTypes
from utils.subscriber_store import (
    load_subscribers,
    save_subscribers,
    load_unsubscribed,
    save_unsubscribed
)


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    subscribers = load_subscribers()
    unsubscribed = load_unsubscribed()

    if chat_id not in subscribers:
        await update.message.reply_text(
            "ℹ️ You are not currently subscribed."
        )
        return

    subscribers.remove(chat_id)
    save_subscribers(subscribers)

    unsubscribed.add(chat_id)
    save_unsubscribed(unsubscribed)

    print(f"[Chartless] Unsubscribed: {chat_id}")

    await update.message.reply_text(
        "🔕 <b>Unsubscribed</b>\n\n"
        "You will no longer receive Chartless alerts.\n"
        "You can re-enable them anytime with /subscribe.",
        parse_mode="HTML"
    )

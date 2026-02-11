from telegram import Update
from telegram.ext import ContextTypes
from utils.subscriber_store import (
    load_subscribers,
    save_subscribers,
    load_unsubscribed,
    save_unsubscribed
)


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    subscribers = load_subscribers()
    unsubscribed = load_unsubscribed()

    # Already subscribed
    if chat_id in subscribers:
        await update.message.reply_text(
            "✅ You are already subscribed to Chartless alerts."
        )
        return

    # Re-subscribing after unsubscribe
    if chat_id in unsubscribed:
        unsubscribed.remove(chat_id)
        save_unsubscribed(unsubscribed)

    subscribers.add(chat_id)
    save_subscribers(subscribers)

    print(f"[Chartless] Subscribed: {chat_id}")

    await update.message.reply_text(
        "🔔 <b>Subscription Enabled</b>\n\n"
        "You’ll receive alerts when a trade setup is approaching.\n"
        "No need to watch charts all day.\n\n"
        "Use /unsubscribe anytime.",
        parse_mode="HTML"
    )


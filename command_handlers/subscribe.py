# # new changes
# from telegram import Update
# from telegram.ext import ContextTypes
# from utils.subscriber_store import (
#     load_subscribers,
#     save_subscribers,
#     load_unsubscribed,
#     save_unsubscribed
# )


# async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     chat_id = update.effective_chat.id

#     subscribers = load_subscribers()
#     unsubscribed = load_unsubscribed()

#     # Already subscribed
#     if chat_id in subscribers:
#         await update.message.reply_text(
#             "✅ You are already subscribed to Chartless alerts."
#         )
#         return

#     # Re-subscribing after unsubscribe
#     if chat_id in unsubscribed:
#         unsubscribed.remove(chat_id)
#         save_unsubscribed(unsubscribed)

#     subscribers.add(chat_id)
#     save_subscribers(subscribers)

#     print(f"[Chartless] Subscribed: {chat_id}")

#     await update.message.reply_text(
#         "🔔 <b>Subscription Enabled</b>\n\n"
#         "You’ll receive alerts when a trade setup is approaching.\n"
#         "No need to watch charts all day.\n\n"
#         "Use /unsubscribe anytime.",
#         parse_mode="HTML"
#     )

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

    # Determine where to send the response
    if update.callback_query:
        reply = update.callback_query.message.reply_text
    else:
        reply = update.message.reply_text

    # Already subscribed
    if chat_id in subscribers:
        await reply(
            "✅ You are already subscribed to Ping alerts."
        )
        return

    # Re-subscribing after unsubscribe
    if chat_id in unsubscribed:
        unsubscribed.remove(chat_id)
        save_unsubscribed(unsubscribed)

    subscribers.add(chat_id)
    save_subscribers(subscribers)

    print(f"[Chartless] Subscribed: {chat_id}")
    await reply(
            "🔔 <b>Subscription Enabled</b>\n\n"
            "You will receive Ping alerts when its time to trade.\n\n"
            
            "Use /unsubscribe anytime.",
            parse_mode="HTML"
        )
    # await reply(
    #     "🔔 <b>Subscription Enabled</b>\n\n"
    #     "You’ll receive alerts when a trade setup is approaching.\n"
    #     "No need to watch charts all day.\n\n"
    #     "Use /unsubscribe anytime.",
    #     parse_mode="HTML"
    # )
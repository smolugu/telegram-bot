from telegram import Update
from telegram.ext import ContextTypes

from utils.subscriber_store import load_subscribers
from utils.admin_guard import is_admin, deny_access


async def testalert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 🔐 ADMIN CHECK
    if not await is_admin(update):
        await deny_access(update)
        return

    subscribers = load_subscribers()

    if not subscribers:
        await update.message.reply_text(
            "⚠️ No subscribers found.\n\n"
            "Ask users to use /subscribe first."
        )
        return

    message = (
        "🔔 <b>Chartless Alert (TEST)</b>\n\n"
        "<b>Symbol:</b> NQ\n"
        "<b>Direction:</b> Short\n"
        "<b>Entry:</b> 18405 (Limit)\n"
        "<b>Stop:</b> 18440\n"
        "<b>Target:</b> 18310\n\n"
        "⏱️ <b>Action window:</b> ~15 minutes\n"
        "Open charts only if you plan to execute."
    )

    sent, failed = 0, 0

    for chat_id in subscribers:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="HTML"
            )
            sent += 1
            print(f"[Chartless] Test alert sent to {chat_id}")
        except Exception as e:
            failed += 1
            print(f"[Chartless] Failed to send to {chat_id}: {e}")

    await update.message.reply_text(
        f"🧪 <b>Test alert completed</b>\n\n"
        f"Sent: {sent}\n"
        f"Failed: {failed}",
        parse_mode="HTML"
    )

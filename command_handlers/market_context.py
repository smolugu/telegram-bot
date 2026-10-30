
from telegram import Update
from telegram.ext import ContextTypes


from bot.screens.market_context_screen import market_context_screen
from config.settings import ADMIN_CHAT_LIST


async def market_context_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user
    message = update.effective_message

    if user is None or message is None:
        return

    if user.id not in ADMIN_CHAT_LIST:
        await message.reply_text("⛔ Admin access only.")
        return

    # Runtime data will be connected in the next step.
    runtime_data = {}
    runtime = context.application.bot_data["runtime"]
    screen_message = market_context_screen(runtime)
    # screen_message = market_context_screen(runtime_data)

    await message.reply_text(
        text=screen_message,
        parse_mode="HTML",
    )

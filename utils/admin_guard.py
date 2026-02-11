from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_CHAT_IDS


async def is_admin(update: Update) -> bool:
    chat_id = update.effective_chat.id
    return chat_id in ADMIN_CHAT_IDS


async def deny_access(update: Update):
    await update.message.reply_text(
        "⛔ This command is restricted to admins."
    )

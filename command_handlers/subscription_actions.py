from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from command_handlers.subscribe import subscribe
from command_handlers.unsubscribe import unsubscribe


async def subscription_action_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    print("SUBSCRIPTION CALLBACK:", query.data)

    try:
        await query.answer()
    except BadRequest:
        pass

    if query.data == "subscribe":
        await subscribe(update, context)

    elif query.data == "unsubscribe":
        await unsubscribe(update, context)
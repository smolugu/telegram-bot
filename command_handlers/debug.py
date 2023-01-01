from telegram.error import BadRequest


async def debug_callback(update, context):

    query = update.callback_query

    print("CALLBACK RECEIVED:", query.data)

    try:
        await query.answer()
    except BadRequest:
        pass
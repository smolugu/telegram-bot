async def debug_callback(update, context):

    query = update.callback_query

    print("CALLBACK RECEIVED:", query.data)

    await query.answer()
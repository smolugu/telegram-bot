async def start_command(update, context):

    await update.message.reply_text(
        "Welcome to TradeOnCall.\n"
        "Use /subscribe to receive trade alerts."
    )

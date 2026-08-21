from bot.screens.plans_screen import plans_home_screen


async def plans_callback(update, context):

    query = update.callback_query

    await query.answer()

    if query.data == "plans:home":

        message, keyboard = plans_home_screen()

    else:
        return

    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode="HTML",
    )
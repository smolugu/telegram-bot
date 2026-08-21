from bot.screens.alerts_screen import alerts_home_screen
from bot.utils.safe_edit_message import safe_edit_message


async def alerts_callback(update, context):

    query = update.callback_query
    # print("ALERT CALLBACK RECEIVED:", query.data)

    await query.answer()

    if query.data == "alerts:home":

        message, keyboard = alerts_home_screen()

    else:
        return

    await safe_edit_message(
        query,
        text=message,
        reply_markup=keyboard,
        parse_mode="HTML",
    )
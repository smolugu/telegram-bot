from bot.screens.about_screen import about_home_screen
from bot.utils.safe_edit_message import safe_edit_message

async def about_command(update, context):

    message, keyboard = about_home_screen()

    await update.message.reply_text(
        text=message,
        reply_markup=keyboard,
        parse_mode="HTML",
    )

async def about_callback(update, context):

    query = update.callback_query

    await query.answer()

    if query.data == "about:home":

        message, keyboard = about_home_screen()

    else:
        return

    await safe_edit_message(
        query,
        text=message,
        reply_markup=keyboard,
        parse_mode="HTML",
    )
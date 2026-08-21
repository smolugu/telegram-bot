from bot.screens.help.commands import help_commands_screen
from bot.screens.help.getting_started import help_getting_started_screen
from bot.screens.help.help import help_home_screen
from bot.screens.help.how_ping_works import help_how_ping_works_screen
from bot.screens.help.subscription import help_subscription_screen
from bot.screens.help.support import help_support_screen
from bot.screens.help.using_ping import help_using_ping_screen

from bot.utils.safe_edit_message import safe_edit_message
from database.session import SessionLocal

from accounts.repository.sqlite_user_repository import (
    SQLiteUserRepository,
)


async def help_command(update, context):

    message, keyboard = help_home_screen()

    await update.message.reply_text(
        text=message,
        reply_markup=keyboard,
        parse_mode="HTML",
    )

async def help_callback(update, context):

    query = update.callback_query

    await query.answer()

    if query.data == "help:home":

        message, keyboard = help_home_screen()

    elif query.data == "help:support":

        message, keyboard = help_support_screen()


    elif query.data == "help:getting_started":

        message, keyboard = help_getting_started_screen()

    elif query.data == "help:how_ping_works":

        message, keyboard = help_how_ping_works_screen()

    elif query.data == "help:using_ping":

        message, keyboard = help_using_ping_screen()
        
    elif query.data == "help:subscription":

        session = SessionLocal()

        try:

            user_repository = SQLiteUserRepository(
                session
            )

            user = user_repository.get_by_telegram_id(
                query.from_user.id
            )

            message, keyboard = help_subscription_screen(
                user
            )

        finally:

            session.close()

    elif query.data == "help:commands":

        message, keyboard = help_commands_screen()

    else:
        return

    await safe_edit_message(
        query,
        text=message,
        reply_markup=keyboard,
        parse_mode="HTML",
    )
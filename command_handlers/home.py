from accounts.repository.sqlite_user_repository import SQLiteUserRepository
from bot.screens.non_subscriber.welcome_screen import non_subscriber_welcome_screen
from bot.screens.subscriber.welcome_screen import subscriber_welcome_screen
from bot.utils.safe_edit_message import safe_edit_message
from database.session import SessionLocal

def get_home_screen(user):
    if (
        user is not None
        and user.subscription_status == "active"
    ):
        return subscriber_welcome_screen()

    return non_subscriber_welcome_screen()


async def home_command(update, context):

    session = SessionLocal()

    try:

        user_repository = SQLiteUserRepository(
            session
        )

        user = user_repository.get_by_telegram_id(
            update.effective_user.id
        )

        message, keyboard = get_home_screen(user)

    finally:

        session.close()

    await update.message.reply_text(
        text=message,
        reply_markup=keyboard,
        parse_mode="HTML",
    )

async def home_callback(update, context):

    query = update.callback_query

    await query.answer()

    session = SessionLocal()

    try:

        user_repository = SQLiteUserRepository(
            session
        )

        user = user_repository.get_by_telegram_id(
            query.from_user.id
        )

        message, keyboard = get_home_screen(user)

    finally:

        session.close()

    await safe_edit_message(
        query,
        text=message,
        reply_markup=keyboard,
        parse_mode="HTML",
    )

# async def home_callback(update, context):

#     query = update.callback_query

#     await query.answer()

#     user_id = query.from_user.id

#     session = SessionLocal()

#     try:

#         user_repository = SQLiteUserRepository(
#             session
#         )

#         user = user_repository.get_by_telegram_id(
#             user_id
#         )

#         if user is not None and user.subscription_status == "active":

#             message, keyboard = subscriber_welcome_screen()

#         else:

#             message, keyboard = non_subscriber_welcome_screen()

#     finally:

#         session.close()

#     await query.edit_message_text(
#         text=message,
#         reply_markup=keyboard,
#     )
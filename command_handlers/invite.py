from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from accounts.repository.sqlite_user_repository import SQLiteUserRepository
from accounts.services.referral_service import get_or_create_referral_code, get_referral_count
from bot.screens.invite_screen import invite_home_screen
from database.session import SessionLocal


async def invite_callback(update, context):

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

        if user is None:

            message = (
                "⚠️ We couldn't find your Ping account."
            )

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🏠 Home",
                        callback_data="nav:home",
                    ),
                ],
            ])

        elif query.data == "invite:home":

            referral_code = (
                get_or_create_referral_code(
                    session,
                    user,
                )
            )
            referral_count = get_referral_count(
                session,
                user.id,
            )

            message, keyboard = invite_home_screen(
                referral_code,
                referral_count,
            )

        else:

            return

    finally:

        session.close()

    await query.edit_message_text(
        text=message,
        reply_markup=keyboard,
        parse_mode="HTML",
    )

# async def invite_callback(update, context):

#     query = update.callback_query

#     await query.answer()

#     if query.data == "invite:home":

#         message, keyboard = invite_home_screen()

#     else:
#         return

#     await query.edit_message_text(
#         text=message,
#         reply_markup=keyboard,
#         parse_mode="HTML",
#     )
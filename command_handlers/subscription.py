from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest

from accounts.repository.sqlite_user_repository import SQLiteUserRepository
from bot.screens.subscription_screen import subscription_home_screen
from bot.utils.safe_edit_message import safe_edit_message
from database.session import SessionLocal

async def subscription_command(update, context):

    session = SessionLocal()

    try:

        user_repository = SQLiteUserRepository(session)

        user = user_repository.get_by_telegram_id(
            update.effective_user.id
        )

        message, keyboard = subscription_home_screen(
            user
        )

    finally:

        session.close()

    await update.message.reply_text(
        text=message,
        reply_markup=keyboard,
        parse_mode="HTML",
    )

async def subscription_callback(update, context):

    query = update.callback_query
    # print(
    #     "SUBSCRIPTION CALLBACK:",
    #     query.data,
    # )

    await query.answer()


    session = SessionLocal()

    try:

        user_repository = SQLiteUserRepository(session)

        user = user_repository.get_by_telegram_id(
            query.from_user.id
        )

        if query.data == "subscription:home":

            message, keyboard = subscription_home_screen(user)

            await safe_edit_message(
                query,
                text=message,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

            return

        elif query.data == "subscription:manage":

            print("MANAGE SUBSCRIPTION START")

            if user is not None:
                print(
                    "STATUS:",
                    user.subscription_status,
                )
                print(
                    "WHOP ID:",
                    user.whop_subscription_id,
                )

            if user is None:

                message = (
                    "💳 <b>MANAGE SUBSCRIPTION</b>\n\n"
                    "We couldn't find your Ping account."
                )

                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "🏠 Home",
                            callback_data="nav:home",
                        ),
                    ],
                ])

            elif user.subscription_status != "active":

                message = (
                    "💳 <b>MANAGE SUBSCRIPTION</b>\n\n"
                    "Your Ping subscription is not active."
                )

                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "◀️ Back",
                            callback_data="subscription:home",
                        ),
                        InlineKeyboardButton(
                            "🏠 Home",
                            callback_data="nav:home",
                        ),
                    ],
                ])

            else:

                print(
                    "WHOP SUBSCRIPTION ID:",
                    user.whop_subscription_id,
                )

                message = (
                    "💳 <b>MANAGE SUBSCRIPTION</b>\n\n"
                    "Your Ping subscription is active.\n\n"
                    "Your subscription is managed "
                    "through Whop."
                )

                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "◀️ Back",
                            callback_data="subscription:home",
                        ),
                        InlineKeyboardButton(
                            "🏠 Home",
                            callback_data="nav:home",
                        ),
                    ],
                ])

        else:
            return

    finally:

        session.close()

    await safe_edit_message(
        query,
        text=message,
        reply_markup=keyboard,
        parse_mode="HTML",
    )

    
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def subscription_home_screen(user):

    keyboard = [
        [
            InlineKeyboardButton(
                "💳 Manage Subscription",
                callback_data="subscription:manage",
            ),
        ],
        [
            InlineKeyboardButton(
                "◀️ Back",
                callback_data="help:home",
            ),
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="nav:home",
            ),
        ],
    ]

    if user is None:

        message = (
            "👤   <b>SUBSCRIPTION</b>\n\n"
            "We couldn't find your Ping account."
        )

        return (
            message,
            InlineKeyboardMarkup(keyboard),
        )

    if user.subscription_status == "active":

        message = (
            "👤   <b>SUBSCRIPTION</b>\n\n"
            "Status: ✅ Active\n\n"
            "Your Ping subscription is active "
            "and you can receive Ping alerts."
        )

    else:

        message = (
            "👤   <b>SUBSCRIPTION</b>\n\n"
            "Status: ❌ Inactive\n\n"
            "You don't currently have an active "
            "Ping subscription."
        )

    return message, InlineKeyboardMarkup(keyboard)
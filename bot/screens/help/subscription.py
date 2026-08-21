from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def help_subscription_screen(user):

    keyboard = [
        [
            InlineKeyboardButton(
                "👤 My Subscription",
                callback_data="subscription:home",
            ),
        ],
        [
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="nav:home",
            ),
        ],
    ]

    if user is not None and user.subscription_status == "active":

        message = (
            "💳   <b>SUBSCRIPTION</b>\n\n"
            "Your Ping subscription is active.\n\n"
            "Your subscription is managed through Whop.\n\n"
            "You can view your subscription details "
            "from the My Subscription screen."
        )

    else:

        message = (
            "💳   <b>SUBSCRIPTION</b>\n\n"
            "You don't currently have an active "
            "Ping subscription.\n\n"
            "Subscribe to Ping to start receiving "
            "market alerts."
        )

        keyboard.insert(
            0,
            [
                InlineKeyboardButton(
                    "🚀 Get Ping",
                    callback_data="subscribe:start",
                ),
            ],
        )

    return message, InlineKeyboardMarkup(keyboard)
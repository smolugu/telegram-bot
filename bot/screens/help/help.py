from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def help_home_screen():

    keyboard = [
        [
            InlineKeyboardButton(
                "🚀 Getting Started",
                callback_data="help:getting_started",
            ),
        ],
        [
            InlineKeyboardButton(
                "📡 How Ping Works",
                callback_data="help:how_ping_works",
            ),
        ],
        [
            InlineKeyboardButton(
                "⚙️ Using Ping",
                callback_data="help:using_ping",
            ),
        ],
        [
            InlineKeyboardButton(
                "💳 Subscription",
                callback_data="help:subscription",
            ),
        ],
        [
            InlineKeyboardButton(
                "📋 Commands",
                callback_data="help:commands",
            ),
        ],
        [
            InlineKeyboardButton(
                "🆘 Contact Support",
                callback_data="help:support",
            ),
        ],
        [
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="nav:home",
            ),
        ],
    ]

    message = (
        "❓   <b>HELP</b>\n\n"
        "How can we help?"
    )

    return message, InlineKeyboardMarkup(keyboard)
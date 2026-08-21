from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def non_subscriber_welcome_screen():

    keyboard = [
        [
            InlineKeyboardButton(
                "🚀 Get Ping",
                callback_data="subscribe:start",
            ),
            InlineKeyboardButton(
                "💎 Plans",
                callback_data="plans:home",
            ),
        ],
        [
            InlineKeyboardButton(
                "ℹ️ What is Ping?",
                callback_data="about:home",
            ),
            InlineKeyboardButton(
                "❓ Help",
                callback_data="help:home",
            ),
        ],
    ]

    return (
        "<b>Ping:</b> <i>It’s Time. Open Charts.</i>\n\n"
        
        "Ping watches the market so you don't "
        "have to watch your charts all day.\n\n"
        "We'll let you know when it's time "
        "to pay attention."
    ), InlineKeyboardMarkup(keyboard)
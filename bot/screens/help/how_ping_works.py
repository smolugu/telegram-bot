from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def help_how_ping_works_screen():

    keyboard = [
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

    message = (
        "📡   <b>HOW PING WORKS</b>\n\n"
        "Ping continuously monitors the market while you go about your day.\n\n"
        "It analyzes price action and market context to identify when the market is getting ready to make a significant move.\n\n"
        "When the time is right, Ping sends you an alert.\n\n"
        "You don't need to stare at charts waiting for the move.\n\n"
        "<b>Ping is not a signal service.**</b>\n\n"
        "It doesn't tell you what to buy or sell.\n\n"
        "<b>Ping tells you when it's time to open your charts and make your own trading decision.</b>\n\n"
        "Ping watches. Ping detects. Ping alerts.\n\n"
        "────────\n"
        "<b>Ping:</b> <i>It’s Time. Open Charts.</i>"
    )


    return message, InlineKeyboardMarkup(keyboard)
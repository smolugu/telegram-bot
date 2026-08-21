from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def help_using_ping_screen():

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
        "⚙️   <b>USING PING</b>\n\n"
        "Use Ping to:\n\n"
        "• View your current Pings\n"
        "• Choose the markets you follow\n"
        "• Choose trading sessions\n"
        "• Configure notifications\n"
        "• View your subscription\n\n"
        "Use the buttons on the Ping home screen "
        "to navigate."
    )

    return message, InlineKeyboardMarkup(keyboard)
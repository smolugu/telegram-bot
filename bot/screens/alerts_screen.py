from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def alerts_home_screen():

    keyboard = [
        [
            InlineKeyboardButton(
                "⚙️ Alert Settings",
                callback_data="settings:home",
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
        "📡   <b>MY PINGS</b>\n\n"
        "No active Ping right now.\n\n"
        "We'll notify you when your configured "
        "market conditions are triggered."
    )

    return message, InlineKeyboardMarkup(keyboard)
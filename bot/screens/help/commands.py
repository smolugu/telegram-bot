from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def help_commands_screen():

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
        "📋   <b>PING COMMANDS</b>\n\n"
        "/start\n"
        "Open Ping\n\n"
        "/ping\n"
        "View your current Ping\n\n"
        "/settings\n"
        "Manage your preferences\n\n"
        "/subscription\n"
        "View your subscription\n\n"
        "/about\n"
        "Learn about Ping\n\n"
        "/help\n"
        "Open Help"
    )

    return message, InlineKeyboardMarkup(keyboard)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def help_support_screen():

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
        "🆘   <b>CONTACT SUPPORT</b>\n\n"
        "Need help with Ping?\n\n"
        "If you're having trouble with your "
        "subscription, Telegram connection, "
        "or Ping alerts, contact our support team."
    )

    return message, InlineKeyboardMarkup(keyboard)
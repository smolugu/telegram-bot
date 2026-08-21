from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def settings_home_screen():

    keyboard = [
        [
            InlineKeyboardButton(
                "📈 Instruments",
                callback_data="settings:instruments",
            ),
        ],
        [
            InlineKeyboardButton(
                "⏰ Sessions",
                callback_data="settings:sessions",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔔 Notifications",
                callback_data="settings:notifications",
            ),
        ],
        [
            InlineKeyboardButton(
                "◀️ Back",
                callback_data="alerts:home",
            ),
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="nav:home",
            ),
        ],
    ]

    message = (
        "⚙️   <b>SETTINGS</b>\n\n"
        "Customize your Ping alert preferences."
    )

    return message, InlineKeyboardMarkup(keyboard)
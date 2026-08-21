from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def settings_notifications_screen(
    enabled: bool = True,
):

    if enabled:

        message = (
            "🔔   <b>NOTIFICATIONS</b>\n\n"
            "Ping notifications are currently ON.\n\n"
            "You will receive alerts for your "
            "chosen instruments and sessions."
        )

        toggle_label = "🔕 Turn Notifications OFF"

    else:

        message = (
            "🔔   <b>NOTIFICATIONS</b>\n\n"
            "Ping notifications are currently OFF.\n\n"
            "You will not receive Ping alerts."
        )

        toggle_label = "🔔 Turn Notifications ON"

    keyboard = [
        [
            InlineKeyboardButton(
                toggle_label,
                callback_data="settings:notifications:toggle",
            ),
        ],
        [
            InlineKeyboardButton(
                "◀️ Back",
                callback_data="settings:home",
            ),
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="nav:home",
            ),
        ],
    ]

    return message, InlineKeyboardMarkup(keyboard)
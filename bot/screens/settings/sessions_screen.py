from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def settings_sessions_screen(selected_sessions=None):

    if selected_sessions is None:
        selected_sessions = set()

    london_label = (
        "✅ London"
        if "LONDON" in selected_sessions
        else "London"
    )

    ny_am_label = (
        "✅ NY AM"
        if "NY_AM" in selected_sessions
        else "NY AM"
    )

    ny_pm_label = (
        "✅ NY PM"
        if "NY_PM" in selected_sessions
        else "NY PM"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                london_label,
                callback_data="settings:session:london",
            ),
            InlineKeyboardButton(
                ny_am_label,
                callback_data="settings:session:ny_am",
            ),
        ],
        [
            InlineKeyboardButton(
                ny_pm_label,
                callback_data="settings:session:ny_pm",
            ),
        ],
        [
            InlineKeyboardButton(
                "💾 Save",
                callback_data="settings:sessions:save",
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

    message = (
        "⏰   <b>SESSIONS</b>\n\n"
        "Choose the trading sessions you want "
        "Ping to monitor.\n\n"
        "You can select more than one."
    )

    return message, InlineKeyboardMarkup(keyboard)
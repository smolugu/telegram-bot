from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def settings_instruments_screen(selected_instruments=None):

    if selected_instruments is None:
        selected_instruments = set()

    nq_label = (
        "✅ NQ"
        if "NQ" in selected_instruments
        else "NQ"
    )

    es_label = (
        "✅ ES"
        if "ES" in selected_instruments
        else "ES"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                nq_label,
                callback_data="settings:instrument:nq",
            ),
            InlineKeyboardButton(
                es_label,
                callback_data="settings:instrument:es",
            ),
        ],
        [
            InlineKeyboardButton(
                "💾 Save",
                callback_data="settings:instruments:save",
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
        "📈   <b>INSTRUMENTS</b>\n\n"
        "Choose the markets you want Ping "
        "to monitor.\n\n"
        "You can select more than one."
    )

    return message, InlineKeyboardMarkup(keyboard)
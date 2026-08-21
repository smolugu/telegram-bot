from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def about_home_screen():

    keyboard = [
        [
            InlineKeyboardButton(
                "📡 How Ping Works",
                callback_data="help:how_ping_works",
            ),
        ],
        [
            InlineKeyboardButton(
                "❓ Help",
                callback_data="help:home",
            ),
        ],
        [
            InlineKeyboardButton(
                "◀️ Back",
                callback_data="nav:home",
            ),
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="nav:home",
            ),
        ],
    ]

    message = (
        "ℹ️   <b>ABOUT PING</b>\n\n"
        "No charts. No noise. Just Ping.\n\n"
        "Ping monitors the market while you live your life. "
        "When the market is about to make a move, Ping "
        "alerts you so you know when it’s time to open your charts.\n\n"

        "Stop wasting hours watching chop.\n"
        "Stop forcing trades because you’ve been staring at the screen all day. \n"
        "Stop missing the large moves because you weren’t there. \n\n"
        "Save time. \n"
        "Protect your focus. \n"
        "Trade when the market is ready.\n\n"
        "────────\n"
        "<b>Ping:</b> <i>It’s Time. Open Charts.</i>"

    )

    return message, InlineKeyboardMarkup(keyboard)
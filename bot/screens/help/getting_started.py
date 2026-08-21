from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def help_getting_started_screen():

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
        "🚀   <b>GETTING STARTED</b>\n\n"
        "Getting started with Ping is simple.\n\n"
        "1️⃣ Subscribe to Ping on Whop.\n\n"
        "2️⃣ Click the Telegram link after "
        "completing your purchase.\n\n"
        "3️⃣ Ping automatically connects your "
        "subscription to your Telegram account.\n\n"
        "4️⃣ Configure your preferences.\n\n"
        "5️⃣ Wait for Ping to engage with markets.\n\n"
        "────────\n"
        "<b>Ping:</b> <i>It’s Time. Open Charts.</i>"
        
    )

    return message, InlineKeyboardMarkup(keyboard)
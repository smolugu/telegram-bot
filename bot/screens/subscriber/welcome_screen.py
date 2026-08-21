from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def subscriber_welcome_screen():
    keyboard = [
        [
            InlineKeyboardButton(
                "📡 My Pings",
                callback_data="alerts:home",
            ),
        ],
        [
            InlineKeyboardButton(
                "⚙️ Settings",
                callback_data="settings:home",
            ),
            InlineKeyboardButton(
                "👤 Subscription",
                callback_data="subscription:home",
            ),
            InlineKeyboardButton(
                "💎 Plans",
                callback_data="plans:home",
            ),
        ],
        [
            InlineKeyboardButton(
                "ℹ️ About Ping",
                callback_data="about:home",
            ),
            InlineKeyboardButton(
                "❓ Help",
                callback_data="help:home",
            ),
        ],
    ]

    return (
        "👋   Welcome to Ping.\n\n"
        "Your subscription is active.\n\n"
        "────────\n"
        "<b>Ping:</b> <i>It’s Time. Open Charts.</i>\n\n"
    ), InlineKeyboardMarkup(keyboard)


def show_subscription_inactive():
    keyboard = [
        [
            InlineKeyboardButton(
                "📡 My Pings",
                callback_data="alerts:home",
            )
        ],
        [
            InlineKeyboardButton(
                "⚙️ Settings",
                callback_data="settings:home",
            ),
            InlineKeyboardButton(
                "👤 Subscription",
                callback_data="subscription:home",
            ),
        ],
        [
            InlineKeyboardButton(
                "ℹ️ About Ping",
                callback_data="about:home",
            ),
            InlineKeyboardButton(
                "❓ Help",
                callback_data="help:home",
            ),
        ],
    ]

    return (
        
        "👋   Welcome to Ping.\n\n"
        "Your subscription is active.\n\n"
        "────────\n"
        "<b>Ping:</b> <i>It’s Time. Open Charts.</i>\n\n"
    ), InlineKeyboardMarkup(keyboard)
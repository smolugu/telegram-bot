from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def onboarding_connecting_screen():
    return (
        "🔗 <b>CONNECTING PING</b>\n\n"
        "We're connecting your Ping subscription "
        "to this Telegram account.\n\n"
        "Please wait..."
    )

def onboarding_verified_screen():
    return (
        "✅ <b>SUBSCRIPTION FOUND</b>\n\n"
        "We've found your Ping subscription.\n\n"
        "Setting up your account..."
    )

def onboarding_complete_screen():
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
                "❓ Help",
                callback_data="help:home",
            ),
        ],
    ]

    return (
        "🎉   <b>YOU'RE ALL SET</b>\n\n"
        "Your Ping subscription is connected.\n\n"
        "You're ready to receive Ping alerts.\n\n"
        "────────\n"
        "<b>Ping:</b> <i>It’s Time. Open Charts.</i>"
    ), InlineKeyboardMarkup(keyboard)
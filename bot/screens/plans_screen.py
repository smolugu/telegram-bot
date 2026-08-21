from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def plans_home_screen():
    
    message = (
        "💎   <b>PING PLANS</b>\n\n"
        "Trade with less screen time.\n"
        "Know when it’s time to open your charts.\n\n"
        
        "━━━━━━━━━━━━━━━━━━\n\n"
        
        "<b>Ping Pro</b>\n"
        "$79/month\n\n"
        
        "• Real-time market monitoring\n"
        "• Ping alerts when conditions are triggered\n"
        "• Configure instruments and sessions\n"
        "• No need to watch charts all day\n\n"
        
        "━━━━━━━━━━━━━━━━━━\n\n"

        "<b>🔥 FOUNDING MEMBER</b>\n"
        "The first 100 subscribers \n"
        "automatically become Founding Members.\n\n"       

        "<b>$39/month — forever</b>\n\n"

        "After the first 100:\n"
        "$79/month\n\n"
        
        "━━━━━━━━━━━━━━━━━━\n\n"
        
        "<b>14-day free trial</b>\n"
        "Experience Ping before you commit."
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🚀 Start 14-Day Trial",
                callback_data="plans:start_trial",
            ),
        ],
        [
            InlineKeyboardButton(
                "🤝 Invite Traders",
                callback_data="invite:home",
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

    return message, InlineKeyboardMarkup(keyboard)
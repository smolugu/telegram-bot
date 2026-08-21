from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from accounts.services.referral_service import get_referral_link, get_share_link


def invite_home_screen(
    referral_code: str,
    referral_count: int,
):
    referral_link = get_referral_link(
        referral_code
    )

    message = (
        "🤝   <b>INVITE TRADERS</b>\n\n"
        "Know a trader who spends too much "
        "time watching charts?\n\n"
        "Send them Ping.\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Share Ping with your:\n\n"
        "• Trading friends\n"
        "• Fellow traders\n"
        "• Trading community\n\n"
        "Help them spend less time watching "
        "chop and more time trading when "
        "the market is ready.\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Your referral code:\n\n"
        f"<b>{referral_code}</b>\n\n"
        "Share your personal Ping link:\n\n"
        f"<code>{referral_link}</code>\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"Your referrals: {referral_count}"
    )

    

    keyboard = [
        [
            InlineKeyboardButton(
                "📤 Share Ping",
                url=get_share_link(referral_code),
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


# def invite_home_screen():

#     message = (
#         "🤝   <b>INVITE TRADERS</b>\n\n"
#         "Know a trader who spends too much "
#         "time watching charts?\n\n"
#         "Send them Ping.\n\n"
#         "━━━━━━━━━━━━━━━━━━\n\n"
#         "Share Ping with your:\n\n"
#         "• Trading friends\n"
#         "• Fellow traders\n"
#         "• Trading community\n\n"
#         "Help them spend less time watching "
#         "chop and more time trading when "
#         "the market is ready."
#     )

#     keyboard = [
#         [
#             InlineKeyboardButton(
#                 "📤 Invite Traders",
#                 callback_data="invite:share",
#             ),
#         ],
#         [
#             InlineKeyboardButton(
#                 "◀️ Back",
#                 callback_data="plans:home",
#             ),
#             InlineKeyboardButton(
#                 "🏠 Home",
#                 callback_data="nav:home",
#             ),
#         ],
#     ]

#     return message, InlineKeyboardMarkup(keyboard)
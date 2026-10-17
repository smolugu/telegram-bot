
from datetime import datetime, timezone
from config.settings import ADMIN_CHAT_LIST


async def notify_admins_new_user(
    context,
    telegram_user,
    referral_code=None,
    access_status="INACTIVE",
):
    username = (
        f"@{telegram_user.username}"
        if telegram_user.username
        else "Not provided"
    )

    referral_info = (
        referral_code
        if referral_code
        else "Direct / No referral"
    )

    joined_at = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )

    message = (
        "🆕 <b>New Ping User</b>\n\n"
        f"<b>Name:</b> {telegram_user.first_name or 'Not provided'}\n"
        f"<b>Username:</b> {username}\n"
        f"<b>Telegram ID:</b> <code>{telegram_user.id}</code>\n"
        f"<b>Referral:</b> {referral_info}\n"
        f"<b>Access Status:</b> {access_status}\n"
        f"<b>Joined:</b> {joined_at}"
    )

    for admin_id in ADMIN_CHAT_LIST:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=message,
                parse_mode="HTML",
            )
        except Exception as e:
            print(
                f"Failed to notify admin {admin_id}: {e}"
            )

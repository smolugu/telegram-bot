
from accounts.services.whop_service import WhopService
from alerts.notify_admin import notify_admins_new_user
from bot.screens.non_subscriber.welcome_screen import non_subscriber_welcome_screen
from bot.screens.subscriber.welcome_screen import subscriber_welcome_screen

from database.session import SessionLocal

from accounts.repository.sqlite_user_repository import (
    SQLiteUserRepository,
)

from accounts.services.referral_service import (
    find_user_by_referral_code,
    create_referral,
)

async def start_command(update, context):

    telegram_user = update.effective_user

    if telegram_user is None:
        return

    telegram_user_id = telegram_user.id
    telegram_username = telegram_user.username
    first_name = telegram_user.first_name

    print("telegram_user_id: ", telegram_user_id)
    print("telegram_username: ", telegram_username)
    print("first_name: ", first_name)

    # --------------------------------------------------
    # 1. Check for subscription ID from Telegram deep link
    # --------------------------------------------------

    # subscription_id = None

    # if context.args:
    #     subscription_id = context.args[0].strip()
    subscription_id = None
    referral_code = None

    if context.args:

        start_parameter = context.args[0].strip()

        if start_parameter.lower().startswith("ref_"):

            referral_code = start_parameter[4:].strip().upper()
            print("referral_code: ", referral_code)

        else:

            subscription_id = start_parameter
            print("subscription_id: ", subscription_id)

    session = SessionLocal()

    try:

        user_repository = SQLiteUserRepository(
            session
        )

        # --------------------------------------------------
        # 2. Subscription onboarding
        # --------------------------------------------------

        if subscription_id:

            await update.message.reply_text(
                "🔗 CONNECTING PING\n\n"
                "We're connecting your Ping subscription "
                "to this Telegram account.\n\n"
                "Please wait..."
            )

            # Temporary validation.
            whop_service = WhopService()
            is_valid = (
                whop_service.validate_subscription(
                    subscription_id
                )
            )

            if not is_valid:

                await update.message.reply_text(
                    "⚠️ SUBSCRIPTION NOT FOUND\n\n"
                    "We couldn't find an active Ping "
                    "subscription for this link."
                )

                return

            # --------------------------------------------------
            # 3. Save subscription information
            # --------------------------------------------------

            user = user_repository.create_or_update(
                telegram_user_id=telegram_user_id,
                telegram_username=telegram_username,
                first_name=first_name,
                whop_subscription_id=subscription_id,
                subscription_status="active",
            )

            # --------------------------------------------------
            # 4. Subscriber welcome
            # --------------------------------------------------

            await update.message.reply_text(
                "🎉 YOU'RE ALL SET\n\n"
                "Your Ping subscription is connected.\n\n"
                "You're ready to receive Ping alerts.\n\n"
                "────────\n"
                "<b>Ping:</b> <i>It’s Time. Open Charts.</i>"
            )

            return

        # --------------------------------------------------
        # 5. Normal /start
        # --------------------------------------------------

        user = user_repository.get_by_telegram_id(
            telegram_user_id
        )
        print("user: ", user)
        # --------------------------------------------------
        # 6. Invite-only access for new users
        # --------------------------------------------------

        if user is None:

            # New user must arrive through a valid referral.
            if not referral_code:

                user_repository.create_or_update(
                    telegram_user_id=telegram_user_id,
                    telegram_username=telegram_username,
                    first_name=first_name,
                    access_status="INACTIVE",
                )

                await notify_admins_new_user(
                    context=context,
                    telegram_user=telegram_user,
                    access_status="INACTIVE",
                )

                await update.message.reply_text(
                    "🔒 <b>Ping is Invite-Only</b>\n\n"
                    "Ping is currently available by invitation "
                    "during our beta.\n\n"
                    "Ask an existing Ping member to invite you.",
                    parse_mode="HTML",
                )

                return

            # Check whether the referral code is valid.
            referrer = find_user_by_referral_code(
                session,
                referral_code,
            )

            if referrer is None:
                
                user_repository.create_or_update(
                    telegram_user_id=telegram_user_id,
                    telegram_username=telegram_username,
                    first_name=first_name,
                    access_status="INACTIVE",
                )

                if referral_code:
                    
                    message = (
                        "🔒 <b>Invitation Not Found</b>\n\n"
                        "This Ping invitation is not valid.\n\n"
                        "Please ask an existing Ping member "
                        "for a new invitation."
                    )
                else:
                    message = (
                        "🔒 <b>Ping is Invite-Only</b>\n\n"
                        "Ping is currently available by invitation "
                        "during our beta.\n\n"
                        "Ask an existing Ping member to invite you."
                    )
                await notify_admins_new_user(
                    context=context,
                    telegram_user=telegram_user,
                    referral_code=referral_code,
                    access_status="INACTIVE",
                )
                await update.message.reply_text(
                    message,
                    parse_mode="HTML",
                )
            
                return

            # Valid invitation — create the user.
            user = user_repository.create_or_update(
                telegram_user_id=telegram_user_id,
                telegram_username=telegram_username,
                first_name=first_name,
                access_status="ACTIVE",
            )

            # Create referral attribution.
            referral = create_referral(
                session,
                referrer,
                user,
            )
            await notify_admins_new_user(
                context=context,
                telegram_user=telegram_user,
                referral_code=referral_code,
                access_status="ACTIVE",
            )

            if referral is not None:

                print(
                    "REFERRAL CREATED:",
                    referral_code,
                    "REFERRER:",
                    referrer.id,
                    "USER:",
                    user.id,
                )

            else:

                print(
                    "REFERRAL NOT CREATED:",
                    "self-referral or existing referral",
                    "CODE:",
                    referral_code,
                    "USER:",
                    user.id,
                )

        # --------------------------------------------------
        # 7. Existing / invited user
        # --------------------------------------------------

        if user.subscription_status == "active":

            message, keyboard = subscriber_welcome_screen()

            await update.message.reply_text(
                message,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

            return

        message, keyboard = non_subscriber_welcome_screen()

        await update.message.reply_text(
            message,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    finally:

        session.close()


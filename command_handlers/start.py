from telegram import Update
from telegram.ext import ContextTypes

from accounts.services.whop_service import WhopService
from bot.screens.non_subscriber.welcome_screen import non_subscriber_welcome_screen
from bot.screens.subscriber.onboarding_screen import onboarding_complete_screen, onboarding_connecting_screen, onboarding_verified_screen
from bot.screens.subscriber.welcome_screen import show_subscription_inactive, subscriber_welcome_screen

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

        else:

            subscription_id = start_parameter

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
                "It's Time. Open Charts."
            )

            return

        # --------------------------------------------------
        # 5. Normal /start
        # --------------------------------------------------

        user = user_repository.get_by_telegram_id(
            telegram_user_id
        )

        if user is None:

            user = user_repository.create_or_update(
                telegram_user_id=telegram_user_id,
                telegram_username=telegram_username,
                first_name=first_name,
            )

        # --------------------------------------------------
        # 6. Process referral
        # --------------------------------------------------

        if referral_code:

            referrer = find_user_by_referral_code(
                session,
                referral_code,
            )

            if referrer is not None:

                referral = create_referral(
                    session,
                    referrer,
                    user,
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

            else:

                print(
                    "REFERRAL CODE NOT FOUND:",
                    referral_code,
                )


        # --------------------------------------------------
        # Existing user
        # --------------------------------------------------

        if user.subscription_status == "active":

            message, keyboard = subscriber_welcome_screen()

            await update.message.reply_text(
                message,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

            return

        await update.message.reply_text(
            "Welcome back to Ping."
        )

    finally:

        session.close()

# async def start_command(
#     update: Update,
#     context: ContextTypes.DEFAULT_TYPE,
# ):

#     if update.effective_user is None:
#         return

#     telegram_user = update.effective_user

#     telegram_user_id = telegram_user.id
#     telegram_username = telegram_user.username
#     first_name = telegram_user.first_name

#     # ---------------------------------------------------------
#     # 1. Check whether this /start contains a subscription ID
#     # ---------------------------------------------------------

#     subscription_id = None

#     if context.args:
#         subscription_id = context.args[0].strip()

#     # ---------------------------------------------------------
#     # 2. Existing user without subscription deep link
#     # ---------------------------------------------------------

#     if subscription_id is None:

#         user = await user_repository.get_by_telegram_id(
#             telegram_user_id
#         )

#         if user is None:

#             message, keyboard = non_subscriber_welcome_screen()

#             await update.message.reply_text(
#                 message,
#                 reply_markup=keyboard,
#             )

#             return

#         # Existing active subscriber
#         if user.subscription_status == "active":

#             message, keyboard = subscriber_welcome_screen()

#             await update.message.reply_text(
#                 message,
#                 reply_markup=keyboard,
#             )

#             return

#         # Existing user but inactive subscription
#         await show_subscription_inactive(update)

#         return

#     # ---------------------------------------------------------
#     # 3. Deep-link onboarding
#     # ---------------------------------------------------------

#     # First acknowledge the request.
#     message = await update.message.reply_text(
#         onboarding_connecting_screen()
#     )

#     # ---------------------------------------------------------
#     # 4. Validate subscription
#     # ---------------------------------------------------------

#     subscription = await whop_service.validate_subscription(
#         subscription_id
#     )

#     if subscription is None:

#         await message.edit_text(
#             "⚠️ SUBSCRIPTION NOT FOUND\n\n"
#             "We couldn't find an active Ping subscription "
#             "for this link.\n\n"
#             "Please make sure you're opening Telegram "
#             "from your Whop purchase."
#         )

#         return

#     # ---------------------------------------------------------
#     # 5. Tell user that subscription was found
#     # ---------------------------------------------------------

#     await message.edit_text(
#         onboarding_verified_screen()
#     )

#     # ---------------------------------------------------------
#     # 6. Create/update Ping user
#     # ---------------------------------------------------------

#     await user_repository.upsert(
#         telegram_user_id=telegram_user_id,
#         telegram_username=telegram_username,
#         first_name=first_name,
#         whop_subscription_id=subscription.subscription_id,
#         subscription_status=subscription.status,
#     )

#     # ---------------------------------------------------------
#     # 7. Activation complete
#     # ---------------------------------------------------------

#     complete_message, keyboard = onboarding_complete_screen()

#     await message.edit_text(
#         complete_message,
#         reply_markup=keyboard,
#     )
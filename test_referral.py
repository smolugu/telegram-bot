from database.session import SessionLocal
from accounts.models.user import UserORM
from accounts.services.referral_service import (
    get_or_create_referral_code,
)
from accounts.services.referral_service import (
    find_user_by_referral_code,
)

session = SessionLocal()

try:

    user = (
        session.query(UserORM)
        .filter(
            UserORM.telegram_user_id == 5287590177
        )
        .first()
    )

    print("USER:", user)

    if user is None:
        print("User not found")

    else:

        print(
            "BEFORE:",
            user.referral_code,
        )

        code = user.referral_code

        referrer = find_user_by_referral_code(
            session,
            code,
        )

        print(
            "REFERRER:",
            referrer,
        )

        if referrer:
            print(
                "REFERRER USER ID:",
                referrer.id,
            )

            print(
                "REFERRER CODE:",
                referrer.referral_code,
            )

finally:

    session.close()
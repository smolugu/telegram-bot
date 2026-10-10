from accounts.services.referral_service import get_or_create_referral_code
from database.session import SessionLocal
from accounts.models.user import UserORM


session = SessionLocal()

try:

    users = (
        session.query(UserORM)
        .filter(
            UserORM.referral_code.is_(None)
        )
        .all()
    )

    print(
        "USERS WITHOUT REFERRAL CODES:",
        len(users),
    )

    for user in users:

        code = get_or_create_referral_code(
            session,
            user,
        )

        print(
            "USER:",
            user.id,
            "| TELEGRAM:",
            user.telegram_user_id,
            "| CODE:",
            code,
        )

finally:

    session.close()
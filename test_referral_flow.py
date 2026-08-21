from datetime import datetime, timezone

from database.session import SessionLocal
from accounts.models.user import UserORM
from accounts.services.referral_service import (
    get_or_create_referral_code,
    find_user_by_referral_code,
    create_referral,
)


session = SessionLocal()

try:

    # Existing user = referrer
    referrer = (
        session.query(UserORM)
        .filter(
            UserORM.telegram_user_id == 5287590177
        )
        .first()
    )

    if referrer is None:
        raise RuntimeError(
            "Referrer user not found"
        )

    # Make sure referrer has a code
    referral_code = get_or_create_referral_code(
        session,
        referrer,
    )

    print(
        "REFERRER:",
        referrer.id,
        referral_code,
    )

    # Create temporary referred user
    now = datetime.now(timezone.utc)

    test_user = UserORM(
        telegram_user_id=9999999999,
        telegram_username="referral_test_user",
        first_name="Referral Test",
        subscription_status="inactive",
        created_at=now,
        updated_at=now,
    )

    session.add(test_user)
    session.commit()
    session.refresh(test_user)

    print(
        "TEST USER CREATED:",
        test_user.id,
    )

    # Simulate /start ref_<code>
    code_from_link = referral_code

    found_referrer = find_user_by_referral_code(
        session,
        code_from_link,
    )

    print(
        "REFERRER FOUND:",
        found_referrer.id,
        found_referrer.referral_code,
    )

    # Create referral
    referral = create_referral(
        session,
        found_referrer,
        test_user,
    )
    print(
        "REFERRAL CREATED:",
        referral.id,
    )

    referral_again = create_referral(
        session,
        found_referrer,
        test_user,
    )

    print(
        "SECOND REFERRAL ID:",
        referral_again.id,
    )

    print(
        "REFERRAL CREATED:",
        referral.id,
    )

    print(
        "REFERRER USER ID:",
        referral.referrer_user_id,
    )

    print(
        "REFERRED USER ID:",
        referral.referred_user_id,
    )

    print(
        "REFERRAL CODE:",
        referral.referral_code,
    )

finally:

    session.close()
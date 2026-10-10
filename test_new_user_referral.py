from accounts.repository.sqlite_user_repository import SQLiteUserRepository
from database.session import SessionLocal
# from accounts.repositories.user import SQLiteUserRepository


session = SessionLocal()

try:
    repository = SQLiteUserRepository(session)

    test_telegram_id = 9999998876

    user = repository.create_or_update(
        telegram_user_id=test_telegram_id,
        telegram_username="referral_test",
        first_name="Referral Test",
    )

    print("USER ID:", user.id)
    print("TELEGRAM ID:", user.telegram_user_id)
    print("REFERRAL CODE:", user.referral_code)

finally:
    session.close()
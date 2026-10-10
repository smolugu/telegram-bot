from database.session import SessionLocal
from accounts.models.user import UserORM
from accounts.models.user_preferences import UserPreferenceORM


session = SessionLocal()

try:

    users = (
        session.query(UserORM)
        .join(
            UserPreferenceORM,
            UserPreferenceORM.user_id == UserORM.id,
        )
        .filter(
            UserPreferenceORM.notifications["enabled"].as_boolean() == True
        )
        .all()
    )

    print()
    print("ALERT RECIPIENTS:")
    print("-----------------")

    for user in users:

        preferences = (
            session.query(UserPreferenceORM)
            .filter(
                UserPreferenceORM.user_id == user.id
            )
            .first()
        )

        print(
            "USER:",
            user.id,
            "| TELEGRAM:",
            user.telegram_user_id,
            "| NOTIFICATIONS:",
            preferences.notifications,
        )

    print()
    print("TOTAL ALERT RECIPIENTS:", len(users))

finally:
    session.close()
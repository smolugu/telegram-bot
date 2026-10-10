from database.session import SessionLocal
from accounts.models.user import UserORM
from accounts.repository.sqlite_user_preferences_repository import (
    SQLiteUserPreferenceRepository,
)


session = SessionLocal()

try:

    users = session.query(UserORM).all()

    preference_repository = SQLiteUserPreferenceRepository(
        session
    )

    created = 0
    existing = 0

    for user in users:

        preferences = (
            preference_repository.get_by_user_id(
                user.id
            )
        )

        if preferences is not None:
            existing += 1
            continue

        preference_repository.create_or_update(
            user_id=user.id,
            instruments=["NQ", "ES"],
            sessions=["LONDON", "NY_AM"],
            notifications={
                "enabled": True,
            },
        )

        created += 1

        print(
            "PREFERENCES CREATED:",
            "USER:",
            user.id,
            "TELEGRAM:",
            user.telegram_user_id,
        )

    print()
    print("TOTAL USERS:", len(users))
    print("PREFERENCES CREATED:", created)
    print("ALREADY EXISTED:", existing)

finally:

    session.close()
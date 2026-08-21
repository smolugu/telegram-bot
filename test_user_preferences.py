from database.session import SessionLocal

from accounts.repository.sqlite_user_repository import (
    SQLiteUserRepository,
)

from accounts.repository.sqlite_user_preferences_repository import (
    SQLiteUserPreferenceRepository,
)


session = SessionLocal()

try:

    print("DATABASE:", session.bind.url)

    user_repository = SQLiteUserRepository(session)

    user = user_repository.get_by_telegram_id(
        5287590177
    )

    print("\nUSER:")
    print(user)

    if user is None:
        print("ERROR: Telegram user not found")
        raise SystemExit

    print("User DB ID:", user.id)

    preference_repository = (
        SQLiteUserPreferenceRepository(session)
    )

    preferences = (
        preference_repository.get_by_user_id(
            user.id
        )
    )

    print("\nPREFERENCES:")
    print(preferences)

    if preferences is not None:

        print("Preference ID:", preferences.id)
        print("User ID:", preferences.user_id)
        print("Instruments:", preferences.instruments)
        print("Sessions:", preferences.sessions)
        print("Notifications:", preferences.notifications)

finally:

    session.close()
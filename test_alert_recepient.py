"""
Smoke test for Ping's normal alert-recipient filter.

Run from the project root:
    python test_alert_recipient_filter.py

This test is read-only: it does not create, update, or delete database rows.
It checks that normal alert recipients have access_status == "ACTIVE" and
notifications.enabled == True.

If your project's import paths differ, update only the imports below.
"""

from sqlalchemy.orm import Session

# Adjust these imports if your project uses different module paths.
from accounts.models.user import UserORM
from accounts.models.user_preferences import UserPreferenceORM
from database.session import SessionLocal


def get_alert_recipients(session: Session) -> list[int]:
    """Mirror the recipient query used by send_telegram_alert_to_all()."""
    rows = (
        session.query(UserORM.telegram_user_id)
        .join(
            UserPreferenceORM,
            UserPreferenceORM.user_id == UserORM.id,
        )
        .filter(
            UserORM.access_status == "ACTIVE",
            UserPreferenceORM.notifications["enabled"].as_boolean() == True,
        )
        .all()
    )

    return [row.telegram_user_id for row in rows]


def main() -> None:
    session = SessionLocal()

    try:
        rows = (
            session.query(
                UserORM.telegram_user_id,
                UserORM.access_status,
                UserPreferenceORM.notifications,
            )
            .join(
                UserPreferenceORM,
                UserPreferenceORM.user_id == UserORM.id,
            )
            .all()
        )

        recipients = set(get_alert_recipients(session))

        inactive_count = 0
        active_notifications_on_count = 0
        expected_recipient_ids = set()

        print("\n--- User access / notification audit ---")

        for row in rows:
            notifications = row.notifications or {}
            enabled = notifications.get("enabled", True) is True
            is_active = row.access_status == "ACTIVE"

            if not is_active:
                inactive_count += 1

            if is_active and enabled:
                active_notifications_on_count += 1
                expected_recipient_ids.add(row.telegram_user_id)

            included = row.telegram_user_id in recipients

            print(
                f"telegram_user_id={row.telegram_user_id} | "
                f"access_status={row.access_status} | "
                f"notifications.enabled={enabled} | "
                f"recipient={included}"
            )

            if not is_active and included:
                raise AssertionError(
                    f"INACTIVE user {row.telegram_user_id} was included "
                    "in the alert recipient list."
                )

            if is_active and notifications.get("enabled") is False and included:
                raise AssertionError(
                    f"User {row.telegram_user_id} has notifications disabled "
                    "but was included in the alert recipient list."
                )

        if recipients != expected_recipient_ids:
            raise AssertionError(
                "Recipient list does not match ACTIVE + notifications-enabled "
                f"users. Expected {expected_recipient_ids}, got {recipients}."
            )

        print("\n--- Result ---")
        print(f"Users with preferences checked: {len(rows)}")
        print(f"INACTIVE users found: {inactive_count}")
        print(
            "ACTIVE users with notifications enabled: "
            f"{active_notifications_on_count}"
        )
        print(f"Alert recipients returned: {len(recipients)}")

        if inactive_count == 0:
            print(
                "NOTE: No INACTIVE users exist yet, so the exclusion rule "
                "was not exercised against an INACTIVE database record. "
                "Test again after creating a new visitor without a referral."
            )

        print("PASS: recipient filter matches the expected access rules.")

    finally:
        session.close()


if __name__ == "__main__":
    main()

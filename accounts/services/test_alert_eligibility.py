from datetime import datetime, timedelta, timezone

from database.session import SessionLocal

from accounts.models.user import UserORM
from accounts.models.user_preferences import UserPreferenceORM
from accounts.models.subscription import SubscriptionORM


# ---------------------------------------------
# APPLICATION-LEVEL BETA CONFIGURATION
# ---------------------------------------------

BETA_MODE = True


def has_alert_entitlement(
    session,
    user_id: int,
    now: datetime,
) -> bool:

    # -----------------------------------------
    # 1. BETA
    # -----------------------------------------

    if BETA_MODE:
        return True

    # -----------------------------------------
    # 2. ACTIVE TRIAL OR PAID SUBSCRIPTION
    # -----------------------------------------

    subscriptions = (
        session.query(SubscriptionORM)
        .filter(
            SubscriptionORM.user_id == user_id,
            SubscriptionORM.status == "ACTIVE",
            SubscriptionORM.started_at <= now,
        )
        .all()
    )

    for subscription in subscriptions:

        if (
            subscription.ended_at is None
            or subscription.ended_at > now
        ):
            return True

    return False


def can_receive_alerts(
    session,
    user_id: int,
    now: datetime,
) -> bool:

    # -----------------------------------------
    # NOTIFICATION PREFERENCE
    # -----------------------------------------

    preferences = (
        session.query(UserPreferenceORM)
        .filter(
            UserPreferenceORM.user_id == user_id
        )
        .first()
    )

    if preferences is None:
        return False

    notifications = (
        preferences.notifications or {}
    )

    if notifications.get("enabled", True) is not True:
        return False

    # -----------------------------------------
    # ENTITLEMENT
    # -----------------------------------------

    return has_alert_entitlement(
        session,
        user_id,
        now,
    )


session = SessionLocal()

try:

    now = datetime.now(timezone.utc)

    # Use test user 9
    user = (
        session.query(UserORM)
        .filter(
            UserORM.id == 8
        )
        .first()
    )

    if user is None:
        raise RuntimeError(
            "Test user 9 does not exist."
        )

    print()
    print("ALERT ELIGIBILITY TEST")
    print("======================")

    # -----------------------------------------
    # CASE 1 — BETA
    # -----------------------------------------

    BETA_MODE = True

    result = can_receive_alerts(
        session,
        user.id,
        now,
    )

    print(
        "BETA MODE:",
        BETA_MODE,
        "| CAN RECEIVE:",
        result,
    )

    # -----------------------------------------
    # CASE 2 — NO BETA, NO SUBSCRIPTION
    # -----------------------------------------

    BETA_MODE = False

    result = can_receive_alerts(
        session,
        user.id,
        now,
    )

    print(
        "NO BETA / NO SUBSCRIPTION",
        "| CAN RECEIVE:",
        result,
    )

    # -----------------------------------------
    # CASE 3 — ACTIVE FREE TRIAL
    # -----------------------------------------

    trial = SubscriptionORM(
        user_id=user.id,
        whop_subscription_id=None,
        type="FREE_TRIAL",
        plan="TRIAL",
        billing_interval=None,
        status="ACTIVE",
        started_at=now - timedelta(days=1),
        ended_at=now + timedelta(days=13),
        created_at=now,
        updated_at=now,
    )

    session.add(trial)
    session.commit()

    result = can_receive_alerts(
        session,
        user.id,
        now,
    )

    print(
        "ACTIVE FREE TRIAL",
        "| CAN RECEIVE:",
        result,
    )

    # -----------------------------------------
    # CASE 4 — EXPIRED TRIAL
    # -----------------------------------------

    trial.status = "ACTIVE"
    trial.started_at = now - timedelta(days=15)
    trial.ended_at = now - timedelta(days=1)

    session.commit()

    result = can_receive_alerts(
        session,
        user.id,
        now,
    )

    print(
        "EXPIRED TRIAL",
        "| CAN RECEIVE:",
        result,
    )

    # -----------------------------------------
    # CASE 5 — ACTIVE PAID
    # -----------------------------------------

    paid = SubscriptionORM(
        user_id=user.id,
        whop_subscription_id="test_paid_subscription",
        type="PAID",
        plan="FOUNDER",
        billing_interval="MONTHLY",
        status="ACTIVE",
        started_at=now - timedelta(days=5),
        ended_at=None,
        created_at=now,
        updated_at=now,
    )

    session.add(paid)
    session.commit()

    result = can_receive_alerts(
        session,
        user.id,
        now,
    )

    print(
        "ACTIVE PAID",
        "| CAN RECEIVE:",
        result,
    )

    # -----------------------------------------
    # CASE 6 — NOTIFICATIONS OFF
    # -----------------------------------------

    preferences = (
        session.query(UserPreferenceORM)
        .filter(
            UserPreferenceORM.user_id == user.id
        )
        .first()
    )

    original_notifications = (
        preferences.notifications
    )

    preferences.notifications = {
        "enabled": False,
    }

    session.commit()

    result = can_receive_alerts(
        session,
        user.id,
        now,
    )

    print(
        "NOTIFICATIONS OFF",
        "| CAN RECEIVE:",
        result,
    )

    # -----------------------------------------
    # RESTORE NOTIFICATION SETTING
    # -----------------------------------------

    preferences.notifications = (
        original_notifications
    )

    # -----------------------------------------
    # CLEAN UP TEST SUBSCRIPTIONS
    # -----------------------------------------

    session.delete(trial)
    session.delete(paid)

    session.commit()

    print()
    print("TEST SUBSCRIPTIONS DELETED")

finally:

    session.close()
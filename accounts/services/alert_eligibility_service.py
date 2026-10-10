from datetime import datetime

from sqlalchemy.orm import Session

from accounts.models.subscription import SubscriptionORM
from accounts.models.user_preferences import UserPreferenceORM


def has_alert_entitlement(
    session: Session,
    user_id: int,
    now: datetime,
    beta_mode: bool,
) -> bool:

    # Beta users have access while beta mode is enabled.
    if beta_mode:
        return True

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
    session: Session,
    user_id: int,
    now: datetime,
    beta_mode: bool,
) -> bool:

    # -----------------------------------------
    # Notification preference
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
    # Alert entitlement
    # -----------------------------------------

    return has_alert_entitlement(
        session=session,
        user_id=user_id,
        now=now,
        beta_mode=beta_mode,
    )
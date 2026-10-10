from datetime import datetime, timezone

from database.session import SessionLocal
from accounts.repository.sqlite_subscription_repository import (
    SQLiteSubscriptionRepository,
)


session = SessionLocal()

try:

    repository = SQLiteSubscriptionRepository(session)

    now = datetime.now(timezone.utc)

    created_ids = []

    print()
    print("CREATING TEST SUBSCRIPTIONS")
    print("============================")

    # --------------------------------------------------
    # 1. FREE TRIAL
    # --------------------------------------------------

    trial = repository.create(
        user_id=9,
        subscription_type="FREE_TRIAL",
        plan="TRIAL",
        billing_interval=None,
        status="ACTIVE",
        started_at=now,
    )

    created_ids.append(trial.id)

    print(
        "FREE_TRIAL:",
        trial.id,
        trial.type,
        trial.plan,
        trial.billing_interval,
        trial.status,
    )

    # --------------------------------------------------
    # 2. FOUNDER MONTHLY
    # --------------------------------------------------

    founder = repository.create(
        user_id=9,
        subscription_type="PAID",
        plan="FOUNDER",
        billing_interval="MONTHLY",
        status="ACTIVE",
        started_at=now,
        whop_subscription_id="test_whop_founder_monthly",
    )

    created_ids.append(founder.id)

    print(
        "FOUNDER:",
        founder.id,
        founder.type,
        founder.plan,
        founder.billing_interval,
        founder.status,
    )

    # --------------------------------------------------
    # 3. STANDARD YEARLY
    # --------------------------------------------------

    standard = repository.create(
        user_id=9,
        subscription_type="PAID",
        plan="STANDARD",
        billing_interval="YEARLY",
        status="ACTIVE",
        started_at=now,
        whop_subscription_id="test_whop_standard_yearly",
    )

    created_ids.append(standard.id)

    print(
        "STANDARD:",
        standard.id,
        standard.type,
        standard.plan,
        standard.billing_interval,
        standard.status,
    )

    # --------------------------------------------------
    # READ ALL USER SUBSCRIPTIONS
    # --------------------------------------------------

    subscriptions = repository.get_by_user_id(9)

    print()
    print("ALL USER SUBSCRIPTIONS")
    print("======================")

    for subscription in subscriptions:

        print(
            subscription.id,
            "|",
            subscription.type,
            "|",
            subscription.plan,
            "|",
            subscription.billing_interval,
            "|",
            subscription.status,
        )

    # --------------------------------------------------
    # READ ACTIVE SUBSCRIPTIONS
    # --------------------------------------------------

    active = repository.get_active_by_user_id(9)

    print()
    print("ACTIVE SUBSCRIPTIONS")
    print("====================")

    for subscription in active:

        print(
            subscription.id,
            "|",
            subscription.type,
            "|",
            subscription.plan,
            "|",
            subscription.billing_interval,
            "|",
            subscription.status,
        )

    print()
    print(
        "ACTIVE COUNT:",
        len(active),
    )

    # --------------------------------------------------
    # TEST UPDATE STATUS
    # --------------------------------------------------

    repository.update_status(
        trial,
        status="INACTIVE",
        ended_at=now,
    )

    print()
    print("TRIAL AFTER UPDATE")
    print("==================")
    print(
        trial.id,
        "|",
        trial.type,
        "|",
        trial.status,
        "|",
        trial.ended_at,
    )

    active_after_update = (
        repository.get_active_by_user_id(9)
    )

    print()
    print(
        "ACTIVE COUNT AFTER TRIAL DEACTIVATION:",
        len(active_after_update),
    )

    # --------------------------------------------------
    # CLEAN UP
    # --------------------------------------------------

    for subscription_id in created_ids:

        subscription = repository.get_by_id(
            subscription_id
        )

        if subscription is not None:

            session.delete(subscription)

    session.commit()

    print()
    print("TEST SUBSCRIPTIONS DELETED")

finally:

    session.close()
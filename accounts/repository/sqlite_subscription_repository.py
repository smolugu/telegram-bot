from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from accounts.models.subscription import SubscriptionORM


class SQLiteSubscriptionRepository:

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        user_id: int,
        subscription_type: str,
        status: str,
        plan: str,
        started_at: datetime,
        ended_at: datetime | None = None,
        billing_interval: str | None = None,
        whop_subscription_id: str | None = None,
    ) -> SubscriptionORM:

        now = datetime.now(timezone.utc)

        subscription = SubscriptionORM(
            user_id=user_id,
            whop_subscription_id=whop_subscription_id,
            type=subscription_type,
            plan=plan,
            billing_interval=billing_interval,
            status=status,
            started_at=started_at,
            ended_at=ended_at,
            created_at=now,
            updated_at=now,
        )

        self.session.add(subscription)
        self.session.commit()
        self.session.refresh(subscription)

        return subscription

    def get_by_id(
        self,
        subscription_id: int,
    ) -> SubscriptionORM | None:

        stmt = (
            select(SubscriptionORM)
            .where(
                SubscriptionORM.id == subscription_id
            )
        )

        return self.session.scalars(stmt).first()

    def get_by_user_id(
        self,
        user_id: int,
    ) -> list[SubscriptionORM]:

        stmt = (
            select(SubscriptionORM)
            .where(
                SubscriptionORM.user_id == user_id
            )
            .order_by(
                SubscriptionORM.started_at.desc()
            )
        )

        return list(
            self.session.scalars(stmt).all()
        )

    def get_active_by_user_id(
        self,
        user_id: int,
    ) -> list[SubscriptionORM]:

        stmt = (
            select(SubscriptionORM)
            .where(
                SubscriptionORM.user_id == user_id,
                SubscriptionORM.status == "ACTIVE",
            )
            .order_by(
                SubscriptionORM.started_at.desc()
            )
        )

        return list(
            self.session.scalars(stmt).all()
        )

    def update_status(
        self,
        subscription: SubscriptionORM,
        status: str,
        ended_at: datetime | None = None,
    ) -> SubscriptionORM:

        subscription.status = status
        subscription.ended_at = ended_at
        subscription.updated_at = (
            datetime.now(timezone.utc)
        )

        self.session.commit()
        self.session.refresh(subscription)

        return subscription
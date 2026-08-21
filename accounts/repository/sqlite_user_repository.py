from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from accounts.models.user import UserORM
from accounts.repository.user_repository import UserRepository


class SQLiteUserRepository(UserRepository):

    def __init__(self, session: Session):
        self.session = session

    def get_by_telegram_id(
        self,
        telegram_user_id: int,
    ) -> UserORM | None:

        stmt = (
            select(UserORM)
            .where(
                UserORM.telegram_user_id == telegram_user_id
            )
        )

        return self.session.scalars(stmt).first()

    def create_or_update(
        self,
        telegram_user_id: int,
        telegram_username: str | None,
        first_name: str | None,
        whop_subscription_id: str | None = None,
        subscription_status: str | None = None,
    ) -> UserORM:

        now = datetime.now(timezone.utc)

        user = self.get_by_telegram_id(
            telegram_user_id
        )

        if user is None:

            user = UserORM(
                telegram_user_id=telegram_user_id,
                telegram_username=telegram_username,
                first_name=first_name,
                whop_subscription_id=whop_subscription_id,
                subscription_status=subscription_status,
                created_at=now,
                updated_at=now,
            )

            self.session.add(user)

        else:

            user.telegram_username = telegram_username
            user.first_name = first_name
            user.updated_at = now

            if whop_subscription_id is not None:
                user.whop_subscription_id = (
                    whop_subscription_id
                )

            if subscription_status is not None:
                user.subscription_status = (
                    subscription_status
                )

        self.session.commit()
        self.session.refresh(user)

        return user
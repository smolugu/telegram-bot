from abc import ABC, abstractmethod

from accounts.models.user import UserORM


class UserRepository(ABC):

    @abstractmethod
    def get_by_telegram_id(
        self,
        telegram_user_id: int,
    ) -> UserORM | None:
        pass

    @abstractmethod
    def create_or_update(
        self,
        telegram_user_id: int,
        telegram_username: str | None,
        first_name: str | None,
        whop_subscription_id: str | None = None,
        subscription_status: str | None = None,
    ) -> UserORM:
        pass
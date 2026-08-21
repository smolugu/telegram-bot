from abc import ABC, abstractmethod

from accounts.models.user_preferences import UserPreferenceORM


class UserPreferenceRepository(ABC):

    @abstractmethod
    def get_by_user_id(
        self,
        user_id: int,
    ) -> UserPreferenceORM | None:
        pass

    @abstractmethod
    def create_or_update(
        self,
        user_id: int,
        instruments: list,
        sessions: list,
        notifications: dict,
    ) -> UserPreferenceORM:
        pass
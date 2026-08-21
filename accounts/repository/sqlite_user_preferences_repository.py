from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from accounts.models.user_preferences import UserPreferenceORM
from accounts.repository.user_preferences_repository import (
    UserPreferenceRepository,
)


class SQLiteUserPreferenceRepository(
    UserPreferenceRepository
):

    def __init__(self, session: Session):
        self.session = session

    def get_by_user_id(
        self,
        user_id: int,
    ) -> UserPreferenceORM | None:

        stmt = (
            select(UserPreferenceORM)
            .where(
                UserPreferenceORM.user_id == user_id
            )
        )

        return self.session.scalars(stmt).first()

    def create_or_update(
        self,
        user_id: int,
        instruments: list,
        sessions: list,
        notifications: dict,
    ) -> UserPreferenceORM:

        now = datetime.now(timezone.utc)

        preferences = self.get_by_user_id(
            user_id
        )

        if preferences is None:

            preferences = UserPreferenceORM(
                user_id=user_id,
                instruments=instruments,
                sessions=sessions,
                notifications=notifications,
                created_at=now,
                updated_at=now,
            )

            self.session.add(preferences)

        else:

            preferences.instruments = instruments
            preferences.sessions = sessions
            preferences.notifications = notifications
            preferences.updated_at = now

        self.session.commit()
        self.session.refresh(preferences)

        return preferences
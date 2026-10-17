
"""
Database integration test for SQLiteUserRepository access-status persistence.

Run from the project root:
    python test_user_repository_access_status.py

This test uses the configured Ping database and creates temporary test users.
It cleans up its test records (preferences, referral links, subscriptions, users)
in a finally block. Do not run this while another process is using the same
test Telegram IDs; IDs are generated uniquely for each run.
"""

import time
import unittest
from sqlalchemy import text, bindparam

# Reuse the imports already proven to work in the application's start module.
from command_handlers import start as start_module

SessionLocal = start_module.SessionLocal
SQLiteUserRepository = start_module.SQLiteUserRepository


class UserRepositoryAccessStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Large positive IDs to avoid collisions with real Telegram accounts.
        cls.test_id_base = 8_900_000_000_000_000 + (time.time_ns() % 1_000_000_000)
        cls.test_telegram_ids = [
            cls.test_id_base + offset for offset in range(1, 4)
        ]

    def setUp(self):
        self.session = SessionLocal()
        self.created_user_ids = []

    def tearDown(self):
        try:
            if self.created_user_ids:
                ids = tuple(self.created_user_ids)
                # These repository tests do not create referral-attribution
                # rows; referral codes are stored on users themselves.
                self.session.execute(
                    text("DELETE FROM subscriptions WHERE user_id IN :ids")
                    .bindparams(bindparam("ids", expanding=True)),
                    {"ids": ids},
                )
                self.session.execute(
                    text("DELETE FROM user_preferences WHERE user_id IN :ids")
                    .bindparams(bindparam("ids", expanding=True)),
                    {"ids": ids},
                )
                self.session.execute(
                    text("DELETE FROM users WHERE id IN :ids")
                    .bindparams(bindparam("ids", expanding=True)),
                    {"ids": ids},
                )
                self.session.commit()
        finally:
            self.session.close()

    def create_user(self, telegram_id, **kwargs):
        repo = SQLiteUserRepository(self.session)
        user = repo.create_or_update(
            telegram_user_id=telegram_id,
            telegram_username="ping_repository_test",
            first_name="Repository Test",
            **kwargs,
        )
        self.created_user_ids.append(user.id)
        return user

    def test_explicit_inactive_is_persisted(self):
        telegram_id = self.test_telegram_ids[0]
        user = self.create_user(telegram_id, access_status="INACTIVE")

        self.session.refresh(user)
        self.assertEqual(user.access_status, "INACTIVE")

        preference = self.session.execute(
            text(
                "SELECT notifications FROM user_preferences WHERE user_id = :user_id"
            ),
            {"user_id": user.id},
        ).first()
        self.assertIsNotNone(preference, "New user should receive default preferences")
        self.assertIsNotNone(user.referral_code, "New user should receive a referral code")

    def test_explicit_active_is_persisted(self):
        telegram_id = self.test_telegram_ids[1]
        user = self.create_user(telegram_id, access_status="ACTIVE")

        self.session.refresh(user)
        self.assertEqual(user.access_status, "ACTIVE")

    def test_omitted_status_defaults_inactive(self):
        telegram_id = self.test_telegram_ids[2]
        user = self.create_user(telegram_id)

        self.session.refresh(user)
        self.assertEqual(user.access_status, "INACTIVE")

    def test_update_without_access_status_preserves_existing_status(self):
        telegram_id = self.test_telegram_ids[0]
        user = self.create_user(telegram_id, access_status="INACTIVE")

        repo = SQLiteUserRepository(self.session)
        updated = repo.create_or_update(
            telegram_user_id=telegram_id,
            telegram_username="ping_repository_test_updated",
            first_name="Updated Test",
        )

        self.session.refresh(updated)
        self.assertEqual(updated.access_status, "INACTIVE")
        self.assertEqual(updated.telegram_username, "ping_repository_test_updated")


if __name__ == "__main__":
    unittest.main(verbosity=2)
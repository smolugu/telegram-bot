"""
Unit tests for Ping's start_command onboarding behavior.

Run from the project root:
    python test_start_command.py

These tests mock the database/repository and Telegram reply method. They do
not write to the real Ping database or send Telegram messages.

The traceback from the current run shows start_command is implemented in
command_handlers/start.py, so this imports that module directly.
"""

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from command_handlers import start as bot_module


class FakeSession:
    def close(self):
        pass


class FakeUserRepository:
    def __init__(self, session, existing_user=None):
        self.user_by_telegram_id = existing_user
        self.created_users = []

    def get_by_telegram_id(self, telegram_user_id):
        return self.user_by_telegram_id

    def create_or_update(self, **kwargs):
        self.created_users.append(kwargs)
        user = SimpleNamespace(
            id=100 + len(self.created_users),
            telegram_user_id=kwargs["telegram_user_id"],
            subscription_status=kwargs.get("subscription_status"),
            access_status=kwargs.get("access_status", "INACTIVE"),
            referral_code="TESTCODE",
        )
        self.user_by_telegram_id = user
        return user


class StartCommandTests(unittest.TestCase):
    def setUp(self):
        self.session = FakeSession()
        self.reply_text = AsyncMock()
        self.update = SimpleNamespace(
            effective_user=SimpleNamespace(
                id=777000001,
                username="test_new_user",
                first_name="Test",
            ),
            message=SimpleNamespace(reply_text=self.reply_text),
        )
        self.context = SimpleNamespace(args=[])
        self.repo = FakeUserRepository(self.session)
        self.find_referrer = Mock(return_value=None)
        self.create_referral = Mock(return_value=object())

        patches = [
            patch.object(bot_module, "SessionLocal", return_value=self.session),
            patch.object(
                bot_module, "SQLiteUserRepository", return_value=self.repo
            ),
            patch.object(
                bot_module,
                "find_user_by_referral_code",
                side_effect=lambda session, code: self.find_referrer.return_value,
            ),
            patch.object(bot_module, "create_referral", self.create_referral),
            patch.object(
                bot_module,
                "non_subscriber_welcome_screen",
                return_value=("Welcome", None),
            ),
            patch.object(
                bot_module,
                "subscriber_welcome_screen",
                return_value=("Subscriber welcome", None),
            ),
        ]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)

    def run_command(self):
        asyncio.run(bot_module.start_command(self.update, self.context))

    def test_new_user_without_referral_is_saved_inactive(self):
        self.context.args = []
        self.run_command()

        self.assertEqual(len(self.repo.created_users), 1)
        self.assertEqual(
            self.repo.created_users[0].get("access_status"), "INACTIVE"
        )
        self.reply_text.assert_awaited_once()
        self.assertIn(
            "Ping is Invite-Only", self.reply_text.await_args.args[0]
        )

    def test_new_user_with_invalid_referral_is_saved_inactive(self):
        self.context.args = ["ref_NOTREAL"]
        self.find_referrer.return_value = None
        self.run_command()

        self.assertEqual(len(self.repo.created_users), 1)
        self.assertEqual(
            self.repo.created_users[0].get("access_status"), "INACTIVE"
        )
        self.reply_text.assert_awaited_once()
        self.assertIn(
            "Invitation Not Found", self.reply_text.await_args.args[0]
        )

    def test_new_user_with_valid_referral_is_saved_active(self):
        referrer = SimpleNamespace(id=42, referral_code="VALID123")
        self.find_referrer.return_value = referrer
        self.context.args = ["ref_VALID123"]
        self.run_command()

        self.assertEqual(len(self.repo.created_users), 1)
        self.assertEqual(
            self.repo.created_users[0].get("access_status"), "ACTIVE",
            "Valid invitees must be explicitly created with ACTIVE access.",
        )
        self.create_referral.assert_called_once_with(
            self.session, referrer, self.repo.user_by_telegram_id
        )

    def test_existing_user_access_status_is_preserved(self):
        existing = SimpleNamespace(
            id=12,
            telegram_user_id=777000001,
            subscription_status=None,
            access_status="INACTIVE",
        )
        self.repo.user_by_telegram_id = existing
        self.context.args = []
        self.run_command()

        self.assertEqual(self.repo.created_users, [])
        self.assertEqual(existing.access_status, "INACTIVE")
        self.reply_text.assert_awaited_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)


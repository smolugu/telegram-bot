from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.screens.settings.instruments_screen import settings_instruments_screen
from bot.screens.settings.notifications_screen import settings_notifications_screen
from bot.screens.settings.sessions_screen import settings_sessions_screen
from bot.screens.settings.settings_screen import settings_home_screen

from bot.utils.safe_edit_message import safe_edit_message
from database.session import SessionLocal

from accounts.repository.sqlite_user_repository import (
    SQLiteUserRepository,
)
from accounts.repository.sqlite_user_preferences_repository import (
    SQLiteUserPreferenceRepository,
)

async def settings_command(update, context):

    message, keyboard = settings_home_screen()

    await update.message.reply_text(
        text=message,
        reply_markup=keyboard,
    )

async def settings_callback(update, context):

    query = update.callback_query

    await query.answer()

    if query.data == "settings:home":

        message, keyboard = settings_home_screen()

    elif query.data == "settings:notifications":

        session = SessionLocal()

        try:

            user_repository = SQLiteUserRepository(session)

            user = user_repository.get_by_telegram_id(
                query.from_user.id
            )

            if user is None:
                return

            preference_repository = (
                SQLiteUserPreferenceRepository(session)
            )

            preferences = (
                preference_repository.get_by_user_id(
                    user.id
                )
            )

            if preferences is None:

                preferences = (
                    preference_repository.create_or_update(
                        user_id=user.id,
                        instruments=[],
                        sessions=[],
                        notifications={
                            "enabled": True,
                        },
                    )
                )

            enabled = (
                preferences.notifications or {}
            ).get(
                "enabled",
                True,
            )

            context.user_data[
                "notification_enabled"
            ] = enabled

            message, keyboard = (
                settings_notifications_screen(
                    enabled
                )
            )

        finally:

            session.close()
    
    elif query.data == "settings:notifications:toggle":

        session = SessionLocal()

        try:

            user_repository = SQLiteUserRepository(session)

            user = user_repository.get_by_telegram_id(
                query.from_user.id
            )

            if user is None:
                return

            preference_repository = (
                SQLiteUserPreferenceRepository(session)
            )

            preferences = (
                preference_repository.get_by_user_id(
                    user.id
                )
            )

            if preferences is None:

                current_enabled = True
                instruments = []
                sessions = []

            else:

                current_enabled = (
                    preferences.notifications or {}
                ).get(
                    "enabled",
                    True,
                )

                instruments = (
                    preferences.instruments or []
                )

                sessions = (
                    preferences.sessions or []
                )

            # Toggle
            new_enabled = not current_enabled

            # Save immediately
            preference_repository.create_or_update(
                user_id=user.id,
                instruments=instruments,
                sessions=sessions,
                notifications={
                    "enabled": new_enabled,
                },
            )

            print(
                "NOTIFICATIONS SAVED:",
                new_enabled,
            )

            context.user_data[
                "notification_enabled"
            ] = new_enabled

            message, keyboard = (
                settings_notifications_screen(
                    new_enabled
                )
            )

        finally:

            session.close()

        await safe_edit_message(
            query,
            text=message,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

        return

    elif query.data == "settings:sessions":

        session = SessionLocal()

        try:

            user_repository = SQLiteUserRepository(session)

            user = user_repository.get_by_telegram_id(
                query.from_user.id
            )

            if user is None:
                return

            preference_repository = (
                SQLiteUserPreferenceRepository(session)
            )

            preferences = (
                preference_repository.get_by_user_id(
                    user.id
                )
            )

            if preferences is None:

                preferences = (
                    preference_repository.create_or_update(
                        user_id=user.id,
                        instruments=[],
                        sessions=[],
                        notifications={},
                    )
                )

            selected = set(
                preferences.sessions or []
            )

            context.user_data[
                "selected_sessions"
            ] = selected.copy()

            message, keyboard = (
                settings_sessions_screen(
                    selected
                )
            )

        finally:

            session.close()

    elif query.data == "settings:sessions:save":

        session = SessionLocal()

        try:

            user_repository = SQLiteUserRepository(
                session
            )

            user = user_repository.get_by_telegram_id(
                query.from_user.id
            )

            if user is None:
                return

            selected = context.user_data.get(
                "selected_sessions",
                set(),
            )

            preference_repository = (
                SQLiteUserPreferenceRepository(session)
            )

            preferences = (
                preference_repository.get_by_user_id(
                    user.id
                )
            )

            if preferences is None:

                preference_repository.create_or_update(
                    user_id=user.id,
                    instruments=[],
                    sessions=sorted(selected),
                    notifications={},
                )

            else:

                preference_repository.create_or_update(
                    user_id=user.id,
                    instruments=preferences.instruments or [],
                    sessions=sorted(selected),
                    notifications=preferences.notifications or {},
                )

            print(
                "SAVED SESSIONS:",
                sorted(selected),
            )

            context.user_data.pop(
                "selected_sessions",
                None,
            )

        finally:

            session.close()

        message = (
            "✅ SESSIONS SAVED\n\n"
            "Your Ping session preferences "
            "have been updated."
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "⏰ Sessions",
                    callback_data="settings:sessions",
                ),
            ],
            [
                InlineKeyboardButton(
                    "◀️ Back",
                    callback_data="settings:home",
                ),
                InlineKeyboardButton(
                    "🏠 Home",
                    callback_data="nav:home",
                ),
            ],
        ]

        await safe_edit_message(
            query,
            text=message,
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
            parse_mode="HTML",
        )

        return
    elif query.data == "settings:session:london":

        selected = context.user_data.setdefault(
            "selected_sessions",
            set(),
        )

        if "LONDON" in selected:
            selected.remove("LONDON")
        else:
            selected.add("LONDON")

        message, keyboard = settings_sessions_screen(
            selected
        )

    elif query.data == "settings:session:ny_am":

        selected = context.user_data.setdefault(
            "selected_sessions",
            set(),
        )

        if "NY_AM" in selected:
            selected.remove("NY_AM")
        else:
            selected.add("NY_AM")

        message, keyboard = settings_sessions_screen(
            selected
        )

    elif query.data == "settings:session:ny_pm":

        selected = context.user_data.setdefault(
            "selected_sessions",
            set(),
        )

        if "NY_PM" in selected:
            selected.remove("NY_PM")
        else:
            selected.add("NY_PM")

        message, keyboard = settings_sessions_screen(
            selected
        )
    elif query.data == "settings:instruments":

        session = SessionLocal()

        try:

            user_repository = SQLiteUserRepository(session)

            user = user_repository.get_by_telegram_id(
                query.from_user.id
            )

            if user is None:
                return

            preference_repository = (
                SQLiteUserPreferenceRepository(session)
            )

            preferences = (
                preference_repository.get_by_user_id(
                    user.id
                )
            )

            if preferences is None:

                preferences = (
                    preference_repository.create_or_update(
                        user_id=user.id,
                        instruments=[],
                        sessions=[],
                        notifications={},
                    )
                )

            selected = set(
                preferences.instruments or []
            )

            context.user_data[
                "selected_instruments"
            ] = selected.copy()

            # print(
            #     "LOADED INSTRUMENTS:",
            #     selected,
            # )

            message, keyboard = (
                settings_instruments_screen(
                    selected
                )
            )

        finally:

            session.close()

    elif query.data == "settings:instruments:save":

        session = SessionLocal()

        try:

            # Find Ping user
            user_repository = SQLiteUserRepository(
                session
            )

            user = user_repository.get_by_telegram_id(
                query.from_user.id
            )

            if user is None:
                return

            # Get current temporary selection
            selected = context.user_data.get(
                "selected_instruments",
                set(),
            )

            # Preference repository
            preference_repository = (
                SQLiteUserPreferenceRepository(session)
            )

            preferences = (
                preference_repository.get_by_user_id(
                    user.id
                )
            )

            if preferences is None:

                preference_repository.create_or_update(
                    user_id=user.id,
                    instruments=sorted(selected),
                    sessions=[],
                    notifications={},
                )

            else:

                preference_repository.create_or_update(
                    user_id=user.id,
                    instruments=sorted(selected),
                    sessions=preferences.sessions or [],
                    notifications=preferences.notifications or {},
                )

            print(
                "SAVED INSTRUMENTS:",
                sorted(selected),
            )

            # Clear temporary state
            context.user_data.pop(
                "selected_instruments",
                None,
            )

        finally:

            session.close()

        message = (
            "✅ INSTRUMENTS SAVED\n\n"
            "Your Ping instrument preferences "
            "have been updated."
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "📈 Instruments",
                    callback_data="settings:instruments",
                ),
            ],
            [
                InlineKeyboardButton(
                    "◀️ Back",
                    callback_data="settings:home",
                ),
                InlineKeyboardButton(
                    "🏠 Home",
                    callback_data="nav:home",
                ),
            ],
        ]

        await safe_edit_message(
            query,
            text=message,
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )

        return
    elif query.data == "settings:instrument:nq":

        selected = context.user_data.setdefault(
            "selected_instruments",
            set(),
        )

        if "NQ" in selected:
            selected.remove("NQ")
        else:
            selected.add("NQ")

        message, keyboard = settings_instruments_screen(
            selected
        )

    elif query.data == "settings:instrument:es":

        selected = context.user_data.setdefault(
            "selected_instruments",
            set(),
        )

        if "ES" in selected:
            selected.remove("ES")
        else:
            selected.add("ES")

        message, keyboard = settings_instruments_screen(
            selected
        )

    else:
        return

    await safe_edit_message(
        query,
        text=message,
        reply_markup=keyboard,
        parse_mode="HTML",
    )
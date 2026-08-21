from telegram.ext import CallbackQueryHandler, CommandHandler

from command_handlers.about import about_callback, about_command
from command_handlers.alerts import alerts_callback
from command_handlers.debug import debug_callback
from command_handlers.help import help_callback, help_command
from command_handlers.home import home_callback, home_command
from command_handlers.invite import invite_callback
from command_handlers.plans import plans_callback
from command_handlers.settings import settings_callback, settings_command
from command_handlers.start import start_command
from command_handlers.subscribe import subscribe
from command_handlers.subscription import subscription_callback, subscription_command
from command_handlers.unsubscribe import unsubscribe


def register_handlers(application):
    """
    Register all bot command handlers here.
    Keeps main.py clean and scalable.
    """

    # Core Commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))

    application.add_handler(
        CallbackQueryHandler(
            help_callback,
            pattern=r"^help:",
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            plans_callback,
            pattern=r"^plans:",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            invite_callback,
            pattern=r"^invite:",
        )
    )
    
    application.add_handler(
        CallbackQueryHandler(
            home_callback,
            pattern=r"^nav:home$",
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            alerts_callback,
            pattern=r"^alerts:home$",
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            settings_callback,
            pattern=r"^settings:",
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            subscription_callback,
            pattern=r"^subscription:",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            about_callback,
            pattern=r"^about:",
        )
    )
    application.add_handler(
        CommandHandler(
            "help",
            help_command,
        )
    )
    application.add_handler(
        CommandHandler(
            "settings",
            settings_command,
        )
    )
    application.add_handler(
        CommandHandler(
            "subscription",
            subscription_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "about",
            about_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "home",
            home_command,
        )
    )



    print("Handlers registered successfully.")

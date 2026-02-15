from telegram.ext import CommandHandler

from command_handlers.start import start_command
from command_handlers.subscribe import subscribe
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

    print("Handlers registered successfully.")

import json
import os


SUBSCRIBERS_FILE = "subscribers.json"


def load_subscribers():
    if not os.path.exists(SUBSCRIBERS_FILE):
        return []

    with open(SUBSCRIBERS_FILE, "r") as f:
        return json.load(f)


async def broadcast_message(application, message):

    subscribers = load_subscribers()

    for chat_id in subscribers:
        try:
            await application.bot.send_message(
                chat_id=chat_id,
                text=message
            )
        except Exception as e:
            print(f"Failed to send to {chat_id}: {e}")

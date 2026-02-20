import requests, os
from dotenv import load_dotenv

# load_dotenv()
token= os.getenv("BOT_TOKEN")

import requests

TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"

def send_telegram_alert_to_all(message):

    subscribers = load_subscribers()

    if not subscribers:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    for chat_id in subscribers:

        payload = {
            "chat_id": chat_id,
            "text": message
        }

        try:
            requests.post(url, data=payload)
        except Exception as e:
            print(f"Failed to send to {chat_id}: {e}")
import time as time_module

from dotenv import load_dotenv

from helpers.escape_char import escape_markdown_v2
from state.state_cache import update_active_window, should_alert
from bot.broadcast import broadcast_message, load_subscribers
from utils.time_utils import today_string
import requests, os

load_dotenv()
token = os.getenv("BOT_TOKEN")


async def handle_stage(result, application):

    if result["stage"] == "NONE":
        return

    window_name = (
        result.get("smt", {}).get("window")
        or result.get("sweep", {}).get("NQ", {}).get("window")
        or "unknown"
    )

    window_key = f"{window_name}_{today_string()}"

    update_active_window(window_key)

    stage_key = f"{result['stage']}_{result.get('smt', {}).get('trade_symbol')}"

    if not should_alert(stage_key):
        return

    message = build_message(result)

    await broadcast_message(application, message)


def build_message(result):

    if result["stage"] == "HEADS_UP":
        return "⚠ Sweep + SMT detected."

    if result["stage"] == "CONFIRMED":
        return "✅ OB confirmed. Waiting for imbalance."

    if result["stage"] == "EXECUTION":
        ex = result["execution"]
        return (
            f"🚀 TRADE READY\n"
            f"Symbol: {result['smt']['trade_symbol']}\n"
            f"Direction: {ex['direction']}\n"
            f"Entry: {ex['entry']}\n"
            f"Stop: {ex['stop']}\n"
            f"Target: {ex['target']}"
        )



def send_telegram_alert_to_all(message):

    subscribers = load_subscribers()

    if not subscribers:
        print("No subscribers found.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    active_subscribers = []

    for chat_id in subscribers:

        payload = {
            "chat_id": chat_id,
            "text": message,
            # "text": escape_markdown_v2(message),
            # "parse_mode": "Markdown"
            # "parse_mode": "MarkdownV2"
        }

        try:
            response = requests.post(url, data=payload, timeout=5)

            if response.status_code == 200:
                active_subscribers.append(chat_id)
            else:
                print("Telegram Error for", chat_id)
                print("Status:", response.status_code)
                print("Response:", response.text)

        except Exception as e:
            print(f"Error sending to {chat_id}: {e}")

        time_module.sleep(0.05)  # avoid Telegram rate limits

    # Save only active subscribers
    # save_subscribers(active_subscribers)
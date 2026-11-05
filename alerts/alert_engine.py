from datetime import datetime, timezone
import time as time_module

from accounts.models.user import UserORM
from accounts.services.alert_eligibility_service import can_receive_alerts
from config.settings import ADMIN_CHAT_LIST, BETA_MODE, BOT_TOKEN
from database.session import SessionLocal
from state.state_cache import update_active_window, should_alert
from bot.broadcast import broadcast_message
from utils.time_utils import today_string
import requests


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



# def send_telegram_alert_to_all(message, start_up, admin_only):

#     subscribers = load_subscribers()

#     if not subscribers:
#         print("No subscribers found.")
#         return

#     url = f"https://api.telegram.org/bot{token}/sendMessage"

#     active_subscribers = []
#     if start_up or admin_only:
#         subscribers = ADMIN_CHAT_LIST
    

#     for chat_id in subscribers:

#         payload = {
#             "chat_id": chat_id,
#             "text": message,
#             # "text": escape_markdown_v2(message),
#             # "parse_mode": "Markdown"
#             # "parse_mode": "MarkdownV2"
#         }

#         try:
#             response = requests.post(url, data=payload, timeout=5)

#             if response.status_code == 200:
#                 active_subscribers.append(chat_id)
#             else:
#                 print("Telegram Error for", chat_id)
#                 print("Status:", response.status_code)
#                 print("Response:", response.text)

#         except Exception as e:
#             print(f"Error sending to {chat_id}: {e}")

#         time_module.sleep(0.05)  # avoid Telegram rate limits

#     # Save only active subscribers
#     # save_subscribers(active_subscribers)

def send_telegram_alert_to_all(message, start_up, admin_only):

    if start_up or admin_only:
        print("start_up or admin_only")

        subscribers = ADMIN_CHAT_LIST
        # print("subscribers: ", subscribers)

    else:

        session = SessionLocal()

        try:

            users = (
                session.query(UserORM)
                .filter(
                    UserORM.access_status == "ACTIVE",
                )
                .all()
            )

            now = datetime.now(timezone.utc)

            subscribers = [
                user.telegram_user_id
                for user in users
                if can_receive_alerts(
                    session=session,
                    user_id=user.id,
                    now=now,
                    beta_mode=BETA_MODE,
                )
            ]

        finally:

            session.close()

    if not subscribers:
        print("No subscribers found.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    active_subscribers = []
    # print("subscribers: ", subscribers)
    for chat_id in subscribers:

        # print("Sending alert to", chat_id)

        payload = {
            "chat_id": chat_id,
            "text": message,
        }

        try:

            response = requests.post(
                url,
                data=payload,
                timeout=5,
            )

            if response.status_code == 200:

                active_subscribers.append(chat_id)

            else:

                print("Telegram Error for", chat_id)
                print("Status:", response.status_code)
                print("Response:", response.text)

        except Exception as e:

            print(
                f"Error sending to {chat_id}: {e}"
            )

        time_module.sleep(0.05)
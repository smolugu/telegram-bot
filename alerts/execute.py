import sqlite3
from data.sqlite.db import DB_FILE
from data.sqlite.db_functions import insert_trade
from alerts.alert_engine import send_telegram_alert_to_all  # adjust import if needed

from datetime import datetime, time
from zoneinfo import ZoneInfo

NY_TZ = ZoneInfo("America/New_York")


def is_alert_window() -> bool:
    now_ny = datetime.now(NY_TZ)
    return time(7, 0) <= now_ny.time() < time(14, 0)

def send_newyork_summary(message, start_up):
    if not message:
        return
    admin_only = False
    if not is_alert_window():
        admin_only = True
    # send alert
    send_telegram_alert_to_all(message, start_up, admin_only)

def execute_trade_and_log(candidate, message, start_up):

    if not message:
        return
    admin_only = False
    if not is_alert_window():
        admin_only = True

    # 1️⃣ Send alert
    send_telegram_alert_to_all(message, start_up, admin_only)

    # 2️⃣ Mark candidate as alerted
    print("Marking candidate as alerted.")
    candidate.alert_sent = True

    # 3️⃣ Insert into database
    insert_trade(candidate)

    # 4️⃣ Debug: print total trades
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM trades")
    total = cursor.fetchone()[0]

    conn.close()

    print(f"Trade inserted. Total trades in DB: {total}")
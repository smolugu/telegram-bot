import sqlite3
from data.sqlite.db import DB_FILE
from data.sqlite.db_functions import insert_trade
from alerts.alert_engine import send_telegram_alert_to_all  # adjust import if needed


def execute_trade_and_log(candidate, message):

    if not message:
        return

    # 1️⃣ Send alert
    send_telegram_alert_to_all(message)

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
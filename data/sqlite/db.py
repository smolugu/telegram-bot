import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "tradeoncall.db")
print("Database file path db.py:", DB_FILE)
def init_db():
    print("Initializing DB at:", DB_FILE)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        trade_id TEXT PRIMARY KEY,
        timestamp TEXT,
        instrument TEXT,
        side TEXT,
        entry REAL,
        stop REAL,
        tp REAL,
        risk REAL,
        imbalance_type TEXT,
        status TEXT,
        r_multiple REAL
    )
    """)

    conn.commit()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    print("Tables after init:", cursor.fetchall())
    conn.close()
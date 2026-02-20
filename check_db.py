import sqlite3
import os

DB_FILE = "tradeoncall.db"

print("Current working directory:", os.getcwd())
print("Full DB path:", os.path.abspath(DB_FILE))

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Tables found:", tables)

conn.close()
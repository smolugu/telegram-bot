
from data.sqlite.db import DB_FILE
import sqlite3

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM trades")
print("Total trades:", cursor.fetchone())

conn.close()
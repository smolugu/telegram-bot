from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
# Replace with YOUR Telegram chat_id(s)
ADMIN_CHAT_IDS = {
    5287590177,   # your personal Telegram chat ID
    # add more if needed
}
LIVE_HISTORY_DAYS = 60
SUPPORTED_TIMEFRAMES = [
    3,
    30,
    60,
    240,
    420,
    1440,
    10080,
]

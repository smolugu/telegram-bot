import asyncio
from datetime import datetime
import pytz

from data.market_data import fetch_market_data
from helpers.zones import get_current_7h_open
from modules.orchestrator import evaluate_7h_setup
from alerts.alert_engine import handle_stage
from helpers.zones import get_current_7h_open

WICK_WINDOW_MINUTES = 60
GRACE_SECONDS = 7
NY = pytz.timezone("America/New_York")


async def trading_engine_loop(application):

    while True:

        await wait_until_next_3m_close()

        await asyncio.sleep(GRACE_SECONDS)

        try:
            market_data = fetch_market_data()

            result = evaluate_7h_setup(
                market_data=market_data,
                seven_hour_open_ts=get_current_7h_open(),
                wick_window_minutes=WICK_WINDOW_MINUTES
            )

            await handle_stage(result, application)

        except Exception as e:
            print("Engine error:", e)


async def wait_until_next_3m_close():

    now = datetime.now(NY)

    minute = now.minute
    next_minute = minute + (3 - minute % 3)

    if next_minute >= 60:
        next_time = now.replace(minute=0, second=0, microsecond=0)
        next_time = next_time.replace(hour=(now.hour + 1) % 24)
    else:
        next_time = now.replace(minute=next_minute, second=0, microsecond=0)

    sleep_seconds = (next_time - now).total_seconds()

    if sleep_seconds > 0:
        await asyncio.sleep(sleep_seconds)

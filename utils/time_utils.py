from datetime import datetime
import pytz


def today_string():

    ny = pytz.timezone("America/New_York")
    now = datetime.now(ny)

    return now.strftime("%Y-%m-%d")

from datetime import datetime, timedelta
import pytz

from helpers.additional_windows import REVERSAL_WINDOWS
from helpers.zones import get_previous_7h_open


def get_reversal_windows(current_7h_open_iso: str, wick_window_minutes: int):

    ny = pytz.timezone("America/New_York")

    current_open = datetime.fromisoformat(current_7h_open_iso).astimezone(ny)

    previous_open_iso = get_previous_7h_open(current_7h_open_iso)
    previous_open = datetime.fromisoformat(previous_open_iso).astimezone(ny)

    wick_delta = timedelta(minutes=wick_window_minutes)
    seven_hours = timedelta(hours=7)

    windows = {}

    # Previous wick window
    windows["previous_wick"] = (
        (previous_open + seven_hours - wick_delta).isoformat(),
        (previous_open + seven_hours).isoformat()
    )

    # Current wick window
    windows["current_wick"] = (
        current_open.isoformat(),
        (current_open + wick_delta).isoformat()
    )

    # Custom configurable windows
    today = current_open.date()

    for window in REVERSAL_WINDOWS:

        start = ny.localize(datetime.combine(today, datetime.min.time())).replace(
            hour=window["start"]["hour"],
            minute=window["start"]["minute"]
        )

        end = ny.localize(datetime.combine(today, datetime.min.time())).replace(
            hour=window["end"]["hour"],
            minute=window["end"]["minute"]
        )

        windows[window["name"]] = (
            start.isoformat(),
            end.isoformat()
        )

    return windows

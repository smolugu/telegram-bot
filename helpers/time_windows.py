from datetime import datetime, timedelta
import pytz

from helpers.additional_windows import ADDITIONAL_WINDOWS
from helpers.zones import get_previous_7h_open


# Unified Helper
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

    for window in ADDITIONAL_WINDOWS:

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

# Timestamp Validation Helper
def is_in_reversal_window(timestamp_iso: str, windows: dict):

    ts = datetime.fromisoformat(timestamp_iso)

    for name, (start_iso, end_iso) in windows.items():

        start = datetime.fromisoformat(start_iso)
        end = datetime.fromisoformat(end_iso)

        if start <= ts <= end:
            return True, name

    return False, None

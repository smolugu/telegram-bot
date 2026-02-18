from datetime import datetime, timedelta
import pytz
from datetime import datetime, timedelta, time
NY_TZ = pytz.timezone("America/New_York")

from helpers.additional_windows import ADDITIONAL_WINDOWS, SPECIFIC_WINDOWS
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



def get_active_window(timestamp_iso, wick_minutes=90):

    ts = datetime.fromisoformat(timestamp_iso)

    if ts.tzinfo is None:
        ts = NY_TZ.localize(ts)

    # -------------------------------------------------
    # 1️⃣ Regular Time Windows (NY lunch, London etc.)
    # -------------------------------------------------
    ts_time = ts.time()

    for window_name, window_range in SPECIFIC_WINDOWS.items():

        if not window_range:
            continue

        start_str, end_str = window_range

        start_time = datetime.strptime(start_str, "%H:%M").time()
        end_time   = datetime.strptime(end_str, "%H:%M").time()

        if start_time <= ts_time <= end_time:
            return window_name

    # -------------------------------------------------
    # 2️⃣ Explicit 7H Wick Windows
    # -------------------------------------------------

    wick_delta = timedelta(minutes=wick_minutes)

    # ---- 18:00 → 18:00 + wick_minutes ----
    center_18 = ts.replace(hour=18, minute=0, second=0, microsecond=0)
    if ts.hour < 18:
        center_18 -= timedelta(days=1)

    if center_18 <= ts <= center_18 + wick_delta:
        return "7h_wick_1800"

    # ---- 01:00 ± wick_minutes ----
    center_01 = ts.replace(hour=1, minute=0, second=0, microsecond=0)
    start_01 = center_01 - wick_delta
    end_01   = center_01 + wick_delta

    if start_01 <= ts <= end_01:
        return "7h_wick_0100"

    # ---- 08:00 ± wick_minutes ----
    center_08 = ts.replace(hour=8, minute=0, second=0, microsecond=0)
    start_08 = center_08 - wick_delta
    end_08   = center_08 + wick_delta

    if start_08 <= ts <= end_08:
        return "7h_wick_0800"

    # ---- 15:00 ± wick_minutes ----
    center_15 = ts.replace(hour=15, minute=0, second=0, microsecond=0)
    start_15 = center_15 - wick_delta
    end_15   = center_15 + wick_delta

    if start_15 <= ts <= end_15:
        return "7h_wick_1500"

    return None

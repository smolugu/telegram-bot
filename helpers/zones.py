from datetime import datetime, timedelta
import pytz


def get_wick_windows(current_7h_open_iso: str, wick_window_minutes: int):

    ny = pytz.timezone("America/New_York")

    current_open = datetime.fromisoformat(current_7h_open_iso)
    previous_open_iso = get_previous_7h_open(current_7h_open_iso)
    previous_open = datetime.fromisoformat(previous_open_iso)

    # Each 7H candle lasts 7 hours (except 15:00 block, but timing logic still valid)
    seven_hours = timedelta(hours=7)
    wick_delta = timedelta(minutes=wick_window_minutes)

    # Previous 7H wick window (final X minutes)
    previous_wick_start = previous_open + seven_hours - wick_delta
    previous_wick_end = previous_open + seven_hours

    # Current 7H wick window (first X minutes)
    current_wick_start = current_open
    current_wick_end = current_open + wick_delta

    return {
        "previous_wick": (
            previous_wick_start.isoformat(),
            previous_wick_end.isoformat()
        ),
        "current_wick": (
            current_wick_start.isoformat(),
            current_wick_end.isoformat()
        )
    }


def get_previous_7h_open(current_7h_open_iso: str):

    ny = pytz.timezone("America/New_York")
    current_open = datetime.fromisoformat(current_7h_open_iso)

    hour = current_open.hour

    # Anchor transitions
    if hour == 1:
        prev_hour = 18
        prev_date = current_open.date() - timedelta(days=1)

    elif hour == 8:
        prev_hour = 1
        prev_date = current_open.date()

    elif hour == 15:
        prev_hour = 8
        prev_date = current_open.date()

    elif hour == 18:
        prev_hour = 15
        prev_date = current_open.date()

    else:
        raise ValueError("Invalid 7H open hour")

    previous_open = ny.localize(
        datetime.combine(prev_date, datetime.min.time()).replace(hour=prev_hour)
    )

    return previous_open.isoformat()


def get_current_7h_open():

    ny = pytz.timezone("America/New_York")
    now = datetime.now(ny)

    today = now.date()

    # Define anchor session starts
    anchors = [
        datetime.combine(today, datetime.min.time()).replace(hour=18),
        datetime.combine(today, datetime.min.time()).replace(hour=1),
        datetime.combine(today, datetime.min.time()).replace(hour=8),
        datetime.combine(today, datetime.min.time()).replace(hour=15),
    ]

    # Localize all anchors
    anchors = [ny.localize(a) for a in anchors]

    # If current time is before 01:00,
    # the valid session is yesterday 18:00
    if now.hour < 1:
        yesterday = today - timedelta(days=1)
        return ny.localize(
            datetime.combine(yesterday, datetime.min.time()).replace(hour=18)
        ).isoformat()

    # Otherwise find latest anchor <= now
    valid_sessions = [a for a in anchors if a <= now]

    if valid_sessions:
        return max(valid_sessions).isoformat()

    # Fallback (should not happen)
    yesterday = today - timedelta(days=1)
    return ny.localize(
        datetime.combine(yesterday, datetime.min.time()).replace(hour=18)
    ).isoformat()


from datetime import datetime, timedelta
import pytz


def get_7h_open_from_timestamp(timestamp_iso: str):

    ny = pytz.timezone("America/New_York")
    ts = datetime.fromisoformat(timestamp_iso).astimezone(ny)

    hour = ts.hour

    if 1 <= hour < 8:
        open_hour = 1
    elif 8 <= hour < 15:
        open_hour = 8
    elif 15 <= hour < 18:
        open_hour = 15
    else:
        # 18:00–23:59 or 00:00–00:59
        open_hour = 18
        if hour < 1:
            ts = ts - timedelta(days=1)

    seven_open = ts.replace(hour=open_hour, minute=0, second=0, microsecond=0)

    return seven_open.isoformat()

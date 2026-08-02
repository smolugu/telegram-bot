from datetime import datetime


CYCLE_TIMES = [
    (1,30),(3,0),(4,30),(6,0),(7,30),
    (9,0),(10,30),(12,0),(13,30),(15,0)
]


def in_cycle_window(timestamp, window_minutes=5):

    dt = datetime.fromisoformat(timestamp)

    for h,m in CYCLE_TIMES:

        if abs((dt.hour*60 + dt.minute) - (h*60 + m)) <= window_minutes:
            return True, (h,m)

    return False, None
from datetime import datetime, time, timedelta


def get_start_of_trading_day(start_time_ny: datetime) -> datetime:

    if start_time_ny.hour >= 18:
        trading_day = start_time_ny.date()
    else:
        trading_day = start_time_ny.date() - timedelta(days=1)

    return datetime.combine(
        trading_day,
        time(18, 0),
        tzinfo=start_time_ny.tzinfo,
    )
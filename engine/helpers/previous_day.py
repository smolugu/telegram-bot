from datetime import date, datetime, timedelta, timezone

from data.models.candle import NY_TZ


def trading_date_to_daily_candle_timestamp(
    trading_date: date,
) -> datetime:
    session_start_ny = datetime.combine(
        trading_date - timedelta(days=1),
        datetime.min.time(),
        tzinfo=NY_TZ,
    ).replace(hour=18)

    return session_start_ny.astimezone(timezone.utc)


def get_previous_trading_day_for_pdhl(start_time_ny: datetime) -> date:

    # Determine the date on which the current futures session started
    if start_time_ny.hour >= 18:
        current_session_date = start_time_ny.date()
    else:
        current_session_date = (
            start_time_ny.date() - timedelta(days=1)
        )

    # Previous session starts one calendar day earlier
    previous_trading_day = (
        current_session_date - timedelta(days=1)
    )

    # Saturday → Friday
    if previous_trading_day.weekday() == 5:
        previous_trading_day -= timedelta(days=2)

    # Sunday is VALID because Sunday 18:00 is the weekly open
    return previous_trading_day


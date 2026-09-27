from datetime import date, datetime, timedelta


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
        previous_trading_day -= timedelta(days=1)

    # Sunday is VALID because Sunday 18:00 is the weekly open
    return previous_trading_day


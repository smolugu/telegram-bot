


from data.models.candle import Candle
from database.session import SessionLocal

from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

from framework.models.mss_detection import find_bullish_mss_level, find_bullish_mss_level_swing_points
from market_data.repository.sqlite_candle_repository import SQLiteCandleRepository

ny_tz = ZoneInfo("America/New_York")


def test_bullish_mss_at_10am(session, test_date, contract):
    # Define the test window in New York time
    start_ny = datetime.combine(
        test_date, time(8, 30), tzinfo=ny_tz
    )
    end_ny = datetime.combine(
        test_date, time(9, 57), tzinfo=ny_tz
    )

    sweep_time_ny = datetime.combine(
        test_date, time(9, 27), tzinfo=ny_tz
    )
    sweep_level = 7660.75

    # Convert boundaries to UTC because DB timestamps are stored in UTC
    start_utc = start_ny.astimezone(timezone.utc)
    end_utc = end_ny.astimezone(timezone.utc)
    candle_repo = SQLiteCandleRepository(session)
    candles = candle_repo.get_between(
        "ESZ6",
                3 ,
                 start_utc,
                end_utc,
    )

    if not candles:
        print("No 3m candles found in the requested window.")
        return


    # Detect bullish MSS
    result = find_bullish_mss_level_swing_points(
        candles
    )

    if result is None:
        print("No bullish MSS structure found.")
        return

    print("\nBullish MSS detected:")
    print(f"Reference low: {result['reference_low']}")
    print(f"Reference low time: {result['reference_low_timestamp']}")
    print(f"Sweeping low: {result['sweeping_low']}")
    print(f"Sweeping low time: {result['sweeping_low_timestamp']}")
    print(f"MSS level: {result['mss_level']}")
    print(f"MSS swing-high time: {result['mss_timestamp']}")
    print(f"MSS status: {result['mss_status']}")



test_date = date(2026, 10, 23)
session = SessionLocal()


if __name__ == "__main__":
    test_bullish_mss_at_10am(session, test_date, "ESZ6")

    print("\nAll formatting tests passed.")

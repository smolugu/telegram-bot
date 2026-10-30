from datetime import timezone
from enum import StrEnum

from framework.models.mss_detection import find_bearish_mss_level_swing_points, find_bullish_mss_level_swing_points

class MSSStatus(StrEnum):
    CONFIRMED = "confirmed"
    WICKED = "wicked"
    UNTOUCHED = "untouched"


class RetracementRisk(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

def get_retracement_risk(
    direction,
    candle_repo,
    end_time,
    contract,
    start_time,
    mss_15m: dict | None,
) -> str | None:
    start_utc = start_time.astimezone(timezone.utc)
    end_utc = end_time.astimezone(timezone.utc)

    mss_statuses = []

    # Detect MSS on 3m and 5m
    for timeframe in (3, 5):
        candles = candle_repo.get_between(
            contract,
            timeframe,
            start_utc,
            end_utc,
        )
        if direction == "bearish":
            mss_result = find_bearish_mss_level_swing_points(candles)
        elif direction == "bullish":
            mss_result = find_bullish_mss_level_swing_points(candles)

        mss_statuses.append(
            mss_result["mss_status"] if mss_result else None
        )

    # Include 15m MSS status if available
    mss_statuses.append(
        mss_15m["mss_status"] if mss_15m else None
    )

    # Ignore timeframes where MSS detection returned None
    statuses = [
        status for status in mss_statuses
        if status is not None
    ]

    if not statuses:
        return None

    if all(status == "CONFIRMED" for status in statuses):
        return RetracementRisk.LOW.value

    if "NOT_TOUCHED" in statuses:
        return RetracementRisk.HIGH.value

    if "WICK_ONLY" in statuses:
        return RetracementRisk.MEDIUM.value

    return RetracementRisk.HIGH.value


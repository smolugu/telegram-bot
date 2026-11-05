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
    mss_15m_start_time,
    mss_15m: dict | None,
) -> str | None:

    start_utc = start_time.astimezone(timezone.utc)
    mss_15m_start_time_utc = mss_15m_start_time.astimezone(timezone.utc)
    end_utc = end_time.astimezone(timezone.utc)
    

    mss_statuses = []
    mss_unmitigated_levels = []
    unmitigated_mss_level = None
    mss_15m_status = None

    # Detect MSS on 3m and 5m
    for timeframe in (3, 5, 15):
        if timeframe == 15:
            start = mss_15m_start_time_utc
        else:
            start = start_utc
        candles = candle_repo.get_between(
            contract,
            timeframe,
            start,
            end_utc,
        )

        if direction == "bearish":
            mss_result = find_bearish_mss_level_swing_points(candles)
            print("mss_result_ss: ", mss_result)
            if mss_result and mss_result["mss_status"] == "CONFIRMED":
                mss_unmitigated_levels.append(mss_result["mss_level"])
        elif direction == "bullish":
            mss_result = find_bullish_mss_level_swing_points(candles)
            if mss_result and mss_result["mss_status"] == "CONFIRMED":
                mss_unmitigated_levels.append(mss_result["mss_level"])
        else:
            raise ValueError(f"Invalid direction: {direction}")

        mss_statuses.append(
            mss_result["mss_status"] if mss_result else None
        )
        if timeframe == 15 and mss_result:
            mss_15m_status = mss_result["mss_status"]


    # Include 15m MSS status if available
    mss_statuses.append(
        mss_15m["mss_status"] if mss_15m else None
    )

    # Ignore timeframes where MSS detection returned None
    statuses = [
        status for status in mss_statuses
        if status is not None
    ]
    if direction == "bearish":
        print("bearish unmitigated mss levels: ", mss_unmitigated_levels)
        unmitigated_mss_level = (
            min(mss_unmitigated_levels)
            if mss_unmitigated_levels
            else None
        )
    else:
        # unmitigated_mss_level = max(mss_unmitigated_levels)
        print("bullish unmitigated mss levels: ", mss_unmitigated_levels)
        unmitigated_mss_level = (
            max(mss_unmitigated_levels)
            if mss_unmitigated_levels
            else None
        )

    if not statuses:
        return None, None

    # HIGH: At least one MSS has not been touched
    if "NOT_TOUCHED" in statuses:
        return RetracementRisk.HIGH.value, None

    if mss_15m_status == "WICK_ONLY":
        return RetracementRisk.HIGH.value, None

    if "WICK_ONLY" in statuses:
        return RetracementRisk.HIGH.value, None
    # MEDIUM: MSS is wicked or confirmed but not mitigated
    if "WICK_ONLY" in statuses or "CONFIRMED" in statuses:
        return RetracementRisk.MEDIUM.value, unmitigated_mss_level

    # LOW: All detected MSS levels are mitigated
    if all(status == "MITIGATED" for status in statuses):
        return RetracementRisk.LOW.value, None


    return RetracementRisk.HIGH.value, None


# def get_retracement_risk(
#     direction,
#     candle_repo,
#     end_time,
#     contract,
#     start_time,
#     mss_15m: dict | None,
# ) -> str | None:
#     start_utc = start_time.astimezone(timezone.utc)
#     end_utc = end_time.astimezone(timezone.utc)

#     mss_statuses = []

#     # Detect MSS on 3m and 5m
#     for timeframe in (3, 5):
#         candles = candle_repo.get_between(
#             contract,
#             timeframe,
#             start_utc,
#             end_utc,
#         )
#         if direction == "bearish":
#             mss_result = find_bearish_mss_level_swing_points(candles)
#         elif direction == "bullish":
#             mss_result = find_bullish_mss_level_swing_points(candles)

#         mss_statuses.append(
#             mss_result["mss_status"] if mss_result else None
#         )

#     # Include 15m MSS status if available
#     mss_statuses.append(
#         mss_15m["mss_status"] if mss_15m else None
#     )

#     # Ignore timeframes where MSS detection returned None
#     statuses = [
#         status for status in mss_statuses
#         if status is not None
#     ]

#     if not statuses:
#         return None

#     if all(status == "CONFIRMED" for status in statuses):
#         return RetracementRisk.LOW.value

#     if "NOT_TOUCHED" in statuses:
#         return RetracementRisk.HIGH.value

#     if "WICK_ONLY" in statuses:
#         return RetracementRisk.MEDIUM.value

#     return RetracementRisk.HIGH.value


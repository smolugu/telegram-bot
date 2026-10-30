from helpers.swing_points import find_swing_highs, find_swing_lows

def get_highest_swing_between(swing_highs, start_timestamp, end_timestamp):
    highs_between = [
        swing
        for swing in swing_highs
        if start_timestamp < swing.timestamp < end_timestamp
    ]

    if not highs_between:
        return None

    return max(highs_between, key=lambda swing: swing.high)

def get_lowest_swing_between(swing_lows, start_timestamp, end_timestamp):
    lows_between = [
        swing
        for swing in swing_lows
        if start_timestamp < swing.timestamp < end_timestamp
    ]

    if not lows_between:
        return None

    return min(lows_between, key=lambda swing: swing.low)




def filter_valid_swing_lows(swings, potential_low_swing):
    valid = []
    
    # Get all previous swings before the potential low swing
    previous_swings = [
        swing for swing in swings
        if swing.timestamp < potential_low_swing.timestamp
    ]

    # Keep valid swing lows
    for swing in previous_swings:
        swing_low = swing.low

        # Remove previous lows that are higher than the current swing
        valid = [v for v in valid if v.low < swing_low]

        # Add the current swing
        valid.append(swing)

    return valid

def filter_valid_swing_highs(swings, potential_high_swing):
    valid = []
    
    # Get all previous swings before the potential high swing
    previous_swings = [
        swing for swing in swings
        if swing.timestamp < potential_high_swing.timestamp
    ]

    # Keep valid swing lows
    for swing in previous_swings:
        swing_high = swing.high

        # Remove previous highs that are lower than the current swing
        valid = [v for v in valid if v.high > swing_high]

        # Add the current swing
        valid.append(swing)

    return valid


def get_valid_swing_points_before(
    current_swing_timestamp,
    candles,
    swing_points,
    direction,
):
    """
    Return valid swing points before the current swing timestamp.

    direction:
        "low"  -> a swing low is swept when a later candle's low
                  goes below the swing low.
        "high" -> a swing high is swept when a later candle's high
                  goes above the swing high.
    """

    valid_swing_points = []

    for swing in swing_points:
        if swing.timestamp >= current_swing_timestamp:
            continue

        # Only candles after the swing and before the current swing
        subsequent_candles = [
            candle for candle in candles
            if swing.timestamp < candle.timestamp
            < current_swing_timestamp
        ]

        if direction == "low":
            
            swept = any(
                candle.low < swing.low
                for candle in subsequent_candles
            )
            
            print("swept: ", swept)
        elif direction == "high":
            swept = any(
                candle.high > swing.high
                for candle in subsequent_candles
            )
        else:
            raise ValueError("direction must be 'low' or 'high'")
        print("swept: ", swept)
        if not swept:
            valid_swing_points.append(swing)
            print("valid swing points: ", valid_swing_points)

    return valid_swing_points


def find_bullish_mss_level(candles, sweep_time, sweep_level):
    swing_lows = find_swing_lows(candles)
    swing_highs = find_swing_highs(candles)

    print("swing lows 101: ", swing_lows)

    # Find the 3m candle that first swept the 30m range
    sweep_index = next(
        (
            i for i, candle in enumerate(candles)
            if candle.timestamp == sweep_time
        ),
        None,
    )

    if sweep_index is None:
        print(f"No 3m candle found at sweep time: {sweep_time}")
        return None

    # Find the lowest low from the sweep candle through
    # the end of the 30m candle
    sweep_candles = candles[sweep_index:]

    lowest_candle = min(
        sweep_candles,
        key=lambda candle: candle.low,
    )

    # Use the actual lowest low as the potential sweeping low
    potential_low = lowest_candle

    print("Sweep level: ", sweep_level)
    print("Lowest sweeping candle: ", potential_low)

    # Reference lows must be earlier than the actual lowest low
    valid_swing_lows = get_valid_swing_points_before(
        # potential_low.timestamp,
        sweep_time,
        candles,
        swing_lows,
        "low",
    )

    print("Potential low timestamp:", potential_low.timestamp)
    print("Total swing lows:", len(swing_lows))
    print("All swing low timestamps:", [
        low.timestamp for low in swing_lows
    ])
    print("Valid swing lows:", valid_swing_lows)

    reference_lows = [
        low for low in valid_swing_lows
        if low.timestamp < potential_low.timestamp
    ]
    print("reference lows:", reference_lows)

    # Keep reference lows swept by the potential low
    swept_lows = [
        low for low in reference_lows
        if potential_low.low < low.low
    ]
    print("swept lows: ", swept_lows)

    if not swept_lows:
        return None

    # Deepest valid reference low that was swept
    reference_low = min(
        swept_lows,
        key=lambda swing: swing.low,
    )
    print("reference low: ", reference_low)

    # Highest swing high between the reference and sweeping lows
    mss_swing_high_candle = get_highest_swing_between(
        swing_highs,
        reference_low.timestamp,
        potential_low.timestamp,
    )
    print("mss high: ", mss_swing_high_candle)

    if mss_swing_high_candle is None:
        return None

    # Check completed 3m candles after the first sweep candle
    post_sweep_candles = [
        candle for candle in candles
        if candle.timestamp >= sweep_time
    ]

    if any(candle.close > mss_swing_high_candle.high for candle in post_sweep_candles):
        mss_status = "CONFIRMED"
    elif any(candle.high > mss_swing_high_candle.high for candle in post_sweep_candles):
        mss_status = "WICK_ONLY"
    else:
        mss_status = "NOT_TOUCHED"

    print("MSS level:", mss_swing_high_candle.high)
    print("MSS status:", mss_status)

    return {
        "mss_level": mss_swing_high_candle.high,
        "mss_timestamp": mss_swing_high_candle.timestamp,
        "reference_low": reference_low.low,
        "reference_low_timestamp": reference_low.timestamp,
        "sweeping_low": potential_low.low,
        "sweeping_low_timestamp": potential_low.timestamp,
        "mss_status": mss_status
    }


def find_bullish_mss_level_v1(candles):
    swing_lows = find_swing_lows(candles)
    swing_highs = find_swing_highs(candles)
    print("swing lows 101: ", swing_lows)

    # Loop backward: newest potential sweeping swing low first
    for potential_low in reversed(swing_lows):

        valid_swing_lows = get_valid_swing_points_before(
            potential_low.timestamp,
            candles,
            swing_lows,
            "low",
        )
        print("valid swing lows: ", valid_swing_lows)

        # Reference lows must be earlier than the potential low
        reference_lows = [
            low for low in valid_swing_lows
            if low.timestamp < potential_low.timestamp
        ]
        print("reference lows:", reference_lows)

        # Keep reference lows swept by the potential low
        swept_lows = [
            low for low in reference_lows
            if potential_low.low < low.low
        ]
        print("swept lows: ", swept_lows)

        if not swept_lows:
            continue

        # Deepest valid reference low that was swept
        reference_low = min(
            swept_lows,
            key=lambda swing: swing.low,
        )
        print("reference low: ", reference_low)

        # Highest swing high between the reference and sweeping lows
        mss_swing_high = get_highest_swing_between(
            swing_highs,
            reference_low.timestamp,
            potential_low.timestamp,
        )
        print("mss high: ", mss_swing_high)

        if mss_swing_high is None:
            continue

        return {
            "mss_level": mss_swing_high.high,
            "mss_timestamp": mss_swing_high.timestamp,
            "reference_low": reference_low.low,
            "reference_low_timestamp": reference_low.timestamp,
            "sweeping_low": potential_low.low,
            "sweeping_low_timestamp": potential_low.timestamp,
        }

    return None




def find_bullish_mss_level_swing_points(candles):
    swing_lows = find_swing_lows(candles)
    swing_highs = find_swing_highs(candles)

    print("Swing lows:", swing_lows)

    # Search from the most recent swing low backward.
    # Each swing low is a potential sweeping point.
    for potential_low in reversed(swing_lows):

        valid_swing_lows = filter_valid_swing_lows(
            swing_lows,
            potential_low,
        )

        # Earlier swing lows that were swept by this potential low
        swept_lows = [
            low for low in valid_swing_lows
            if potential_low.low < low.low
        ]

        print("Potential sweeping low:", potential_low)
        print("Swept reference lows:", swept_lows)

        if not swept_lows:
            continue

        # Select the deepest reference low swept
        reference_low = min(
            swept_lows,
            key=lambda swing: swing.low,
        )

        # Find the highest swing high between reference and sweep
        mss_swing_high = get_highest_swing_between(
            swing_highs,
            reference_low.timestamp,
            potential_low.timestamp,
        )

        if mss_swing_high is None:
            continue

        mss_level = mss_swing_high.high

        # Determine MSS status using completed candles
        relevant_candles = [
            candle for candle in candles
            if candle.timestamp > potential_low.timestamp
        ]

        if any(candle.close > mss_level for candle in relevant_candles):
            mss_status = "CONFIRMED"
        elif any(candle.high > mss_level for candle in relevant_candles):
            mss_status = "WICK_ONLY"
        else:
            mss_status = "NOT_TOUCHED"

        return {
            "mss_level": mss_level,
            "mss_timestamp": mss_swing_high.timestamp,
            "reference_low": reference_low.low,
            "reference_low_timestamp": reference_low.timestamp,
            "sweeping_low": potential_low.low,
            "sweeping_low_timestamp": potential_low.timestamp,
            "mss_status": mss_status
        }

    return None


def find_bearish_mss_level_swing_points(candles):
    swing_lows = find_swing_lows(candles)
    swing_highs = find_swing_highs(candles)

    print("Swing highs:", swing_highs)

    # Search from the most recent swing high backward.
    # Each swing high is a potential sweeping point.
    for potential_high in reversed(swing_highs):

        valid_swing_highs = filter_valid_swing_highs(
            swing_highs,
            potential_high,
        )

        # Earlier swing highs that were swept by this potential high
        swept_highs = [
            high for high in valid_swing_highs
            if potential_high.high > high.high
        ]

        print("Potential sweeping high:", potential_high)
        print("Swept reference highs:", swept_highs)

        if not swept_highs:
            continue

        # Select the deepest reference highlow swept
        reference_high = max(
            swept_highs,
            key=lambda swing: swing.high,
        )

        # Find the lowest swing low between reference and sweep
        mss_swing_low = get_lowest_swing_between(
            swing_lows,
            reference_high.timestamp,
            potential_high.timestamp,
        )

        if mss_swing_low is None:
            continue

        mss_level = mss_swing_low.low

        # Determine MSS status using completed candles
        relevant_candles = [
            candle for candle in candles
            if candle.timestamp > potential_high.timestamp
        ]

        if any(candle.close < mss_level for candle in relevant_candles):
            mss_status = "CONFIRMED"
        elif any(candle.high < mss_level for candle in relevant_candles):
            mss_status = "WICK_ONLY"
        else:
            mss_status = "NOT_TOUCHED"

        return {
            "mss_level": mss_level,
            "mss_timestamp": mss_swing_low.timestamp,
            "reference_high": reference_high.high,
            "reference_high_timestamp": reference_high.timestamp,
            "sweeping_high": potential_high.high,
            "sweeping_high_timestamp": potential_high.timestamp,
            "mss_status": mss_status
        }

    return None
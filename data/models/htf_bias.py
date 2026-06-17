def detect_fvgs(candles):
    """
    Detect ICT Fair Value Gaps.
    Returns:
    [
        {
            "type": "bullish",
            "high": 22050,
            "low": 22030,
            "ce": 22040,
            "index": 25
        },
        ...
    ]
    """

    fvgs = []

    for i in range(2, len(candles)):

        c1 = candles[i - 2]
        c2 = candles[i - 1]
        c3 = candles[i]

        #
        # Bullish FVG
        #
        if c3["low"] > c1["high"]:

            fvg_low = c1["high"]
            fvg_high = c3["low"]

            fvgs.append({
                "type": "bullish",
                "low": fvg_low,
                "high": fvg_high,
                "ce": (fvg_low + fvg_high) / 2,
                "index": i
            })

        #
        # Bearish FVG
        #
        elif c3["high"] < c1["low"]:

            fvg_low = c3["high"]
            fvg_high = c1["low"]

            fvgs.append({
                "type": "bearish",
                "low": fvg_low,
                "high": fvg_high,
                "ce": (fvg_low + fvg_high) / 2,
                "index": i
            })

    return fvgs


def find_closest_fvgs(
    candles,
    current_price=None,
):
    """
    Returns closest FVG above and below current price.
    """

    if current_price is None:
        current_price = candles[-1]["close"]

    fvgs = detect_fvgs(candles)

    closest_above = None
    closest_below = None

    min_above_distance = float("inf")
    min_below_distance = float("inf")

    for fvg in fvgs:

        #
        # Entire FVG above price
        #
        if fvg["low"] > current_price:

            distance = fvg["low"] - current_price

            if distance < min_above_distance:

                min_above_distance = distance
                closest_above = fvg

        #
        # Entire FVG below price
        #
        elif fvg["high"] < current_price:

            distance = current_price - fvg["high"]

            if distance < min_below_distance:

                min_below_distance = distance
                closest_below = fvg

    return {
        "current_price": current_price,
        "closest_fvg_above": closest_above,
        "closest_fvg_below": closest_below,
        "all_fvgs": fvgs,
    }


def determine_daily_liquidity_draw(
    current_price,
    last_swept_liquidity,
    nearest_fvg_above=None,
    nearest_fvg_below=None,
    nearest_daily_high=None,
    nearest_daily_low=None,
):
    """
    Determine Daily Draw on Liquidity.
    Parameters
    ----------
    current_price : float

    last_swept_liquidity : dict
        Example:
        {
            "type": "high",     # high | low
            "level": 21850
        }

    nearest_fvg_above : dict | None
        {
            "high": ...,
            "low": ...
        }

    nearest_fvg_below : dict | None
        {
            "high": ...,
            "low": ...
        }

    nearest_daily_high : float | None

    nearest_daily_low : float | None

    Returns
    -------
    {
        "bias": "bullish" | "bearish" | "neutral",

        "flow":
            "ERL_TO_IRL"
            "IRL_TO_ERL"
            None,

        "target": float | None,

        "target_type":
            "daily_fvg"
            "daily_high"
            "daily_low"
            None,

        "reason": str
    }
    """

    result = {
        "bias": "neutral",
        "flow": None,
        "target": None,
        "target_type": None,
        "reason": None,
    }

    #
    # ERL -> IRL
    #
    # External liquidity already achieved.
    # Draw shifts toward internal liquidity.
    #

    if (
        last_swept_liquidity
        and last_swept_liquidity["type"] == "high"
        and nearest_fvg_below is not None
    ):

        result["bias"] = "bearish"
        result["flow"] = "ERL_TO_IRL"
        result["target"] = (
            nearest_fvg_below["high"]
            + nearest_fvg_below["low"]
        ) / 2
        result["target_type"] = "daily_fvg"
        result["reason"] = (
            "Daily external liquidity swept at highs. "
            "Price seeking nearest daily FVG below."
        )

        return result

    if (
        last_swept_liquidity
        and last_swept_liquidity["type"] == "low"
        and nearest_fvg_above is not None
    ):

        result["bias"] = "bullish"
        result["flow"] = "ERL_TO_IRL"
        result["target"] = (
            nearest_fvg_above["high"]
            + nearest_fvg_above["low"]
        ) / 2
        result["target_type"] = "daily_fvg"
        result["reason"] = (
            "Daily external liquidity swept at lows. "
            "Price seeking nearest daily FVG above."
        )

        return result

    #
    # IRL -> ERL
    #
    # Price currently trading around internal liquidity.
    #

    if (
        nearest_fvg_below is not None
        and nearest_daily_high is not None
        and current_price > nearest_fvg_below["high"]
    ):

        result["bias"] = "bullish"
        result["flow"] = "IRL_TO_ERL"
        result["target"] = nearest_daily_high
        result["target_type"] = "daily_high"
        result["reason"] = (
            "Price trading above daily FVG. "
            "Seeking external liquidity at highs."
        )

        return result

    if (
        nearest_fvg_above is not None
        and nearest_daily_low is not None
        and current_price < nearest_fvg_above["low"]
    ):

        result["bias"] = "bearish"
        result["flow"] = "IRL_TO_ERL"
        result["target"] = nearest_daily_low
        result["target_type"] = "daily_low"
        result["reason"] = (
            "Price trading below daily FVG. "
            "Seeking external liquidity at lows."
        )

        return result

    return result
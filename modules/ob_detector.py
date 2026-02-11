from datetime import datetime


def detect_30m_order_block(
    candles_30m: list[dict],
    sweep_info: dict
) -> dict:
    """
    Detects a 30m Order Block AFTER a sweep using OPEN-violation logic.

    Bearish OB:
    - Find last bullish 30m candle after sweep
    - Any later candle closes BELOW its OPEN

    Bullish OB:
    - Find last bearish 30m candle after sweep
    - Any later candle closes ABOVE its OPEN
    """

    if not sweep_info.get("sweep_detected"):
        return _no_ob()

    sweep_ts = datetime.fromisoformat(sweep_info["timestamp"])
    sweep_side = sweep_info["side"]  # buy_side or sell_side

    # Filter candles AFTER sweep
    post_sweep = [
        c for c in candles_30m
        if datetime.fromisoformat(c["timestamp"]) >= sweep_ts
    ]

    if len(post_sweep) < 2:
        return _no_ob()

    # Directional intent
    looking_for = "BEARISH_OB" if sweep_side == "buy_side" else "BULLISH_OB"

    last_opposing_candle = None

    for candle in post_sweep:
        is_bullish = candle["close"] > candle["open"]
        is_bearish = candle["close"] < candle["open"]

        # Track last opposing candle
        if looking_for == "BEARISH_OB" and is_bullish:
            last_opposing_candle = candle

        if looking_for == "BULLISH_OB" and is_bearish:
            last_opposing_candle = candle

        # No opposing candle yet
        if last_opposing_candle is None:
            continue

        # Check OPEN violation
        if looking_for == "BEARISH_OB":
            if candle["close"] < last_opposing_candle["open"]:
                return {
                    "ob_found": True,
                    "direction": "SHORT",
                    "high": last_opposing_candle["high"],
                    "low": last_opposing_candle["low"],
                    "formed_at": last_opposing_candle["timestamp"]
                }

        if looking_for == "BULLISH_OB":
            if candle["close"] > last_opposing_candle["open"]:
                return {
                    "ob_found": True,
                    "direction": "LONG",
                    "high": last_opposing_candle["high"],
                    "low": last_opposing_candle["low"],
                    "formed_at": last_opposing_candle["timestamp"]
                }

    return _no_ob()


def _no_ob():
    return {
        "ob_found": False,
        "direction": None,
        "high": None,
        "low": None,
        "formed_at": None
    }

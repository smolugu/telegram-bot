from datetime import datetime


def detect_30m_order_block(candles, candidate):

    if not candidate.active:
        return None

    direction = candidate.side  # "buy_side" or "sell_side"

    if len(candles) < 2:
        return None

    # We evaluate the last closed candle
    last_closed = candles[-1]

    # ---------------------------------------
    # Bearish Setup (buy-side sweep first)
    # ---------------------------------------
    if direction == "buy_side":

        # find most recent bullish candle
        for i in range(len(candles) - 2, -1, -1):

            c = candles[i]

            if c["close"] > c["open"]:  # bullish candle

                # OB confirmed if last_closed closes below bullish open
                if last_closed["close"] < c["open"]:

                    return {
                        "type": "bearish_ob",
                        "confirmation_timestamp": last_closed["timestamp"],
                        "ob_candle_timestamp": c["timestamp"],
                        "ob_high": c["high"],
                        "ob_low": c["open"],
                        "confirmation_high": last_closed["high"],
                        "confirmation_low": last_closed["low"],
                        "source_index": i
                    }

                break

    # ---------------------------------------
    # Bullish Setup (sell-side sweep first)
    # ---------------------------------------
    if direction == "sell_side":

        # find most recent bearish candle
        for i in range(len(candles) - 2, -1, -1):

            c = candles[i]

            if c["close"] < c["open"]:  # bearish candle

                # OB confirmed if last_closed closes above bearish open
                if last_closed["close"] > c["open"]:

                    return {
                        "type": "bullish_ob",
                        "confirmation_timestamp": last_closed["timestamp"],
                        "ob_candle_timestamp": c["timestamp"],
                        "ob_low": c["low"],
                        "ob_high": c["open"],
                        "confirmation_high": last_closed["high"],
                        "confirmation_low": last_closed["low"],
                        "source_index": i
                    }

                break

    return None

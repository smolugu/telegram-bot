from datetime import datetime, timedelta


def detect_30m_order_block(candles, candidate):

    # if not candidate.active:
    #     return None
    if candidate.ob_confirmed:
        return candidate.ob_data

    direction = candidate.side  # "buy_side" or "sell_side"

    if len(candles) < 2:
        return None

    # We evaluate the last closed candle
    last_closed = candles[-1]
    
    body = abs(last_closed["close"] - last_closed["open"])
    range_ = last_closed["high"] - last_closed["low"]
    strong_body = body/range_ > 0.6
    ob_body_range = body/range_

    # ---------------------------------------
    # Bearish Setup (buy-side sweep first)
    # ---------------------------------------
    if direction == "buy_side":

        # find most recent bullish candle
        for i in range(len(candles) - 2, -1, -1):

            c = candles[i]
            bullish_candle = False
            # this candle should be bullish
            if c["close"] > c["open"]: # bullish candle
                # OB confirmed if last_closed closes below bullish open
                if last_closed["close"] < c["open"]:
                    print("last_closed_candle: ", last_closed["high"], last_closed["low"], last_closed["open"], last_closed["close"])
                    print("last_closed body: ", abs(last_closed["close"] - last_closed["open"]))
                    print("swee_type: ", candidate.sweep_type)
                    print("sweep_candle: ", candidate.sweep_candle)
                    print("last_closed range: ", last_closed["high"] - last_closed["low"])
                    print("ob_body_range: ", ob_body_range)
                    # check if ob is valid
                    # valid ob is one which is followed by a sweep or an SMT (where there is sweep on correlating asset)
                    # breakout_sweep_ob = False
                    # breakout_sweep_ob = last_closed["close"] < candidate.sweep_candle["open"]
                    ob_found = {
                        "type": "bearish_ob",
                        "confirmation_timestamp": last_closed["timestamp"],
                        "ob_candle_timestamp": c["timestamp"],
                        "ob_high": c["high"],
                        "ob_low": c["open"],
                        "confirmation_high": last_closed["high"],
                        "confirmation_low": last_closed["low"],
                        "source_index": i,
                        "structure_break": last_closed["close"] < c["low"],
                        "strong_body_displacement": strong_body,
                        "ob_body_range": ob_body_range,
                        # "breakout_sweep_ob": breakout_sweep_ob
                    }
                    if candidate.sweep_type == "rejection":
                        return ob_found
                    elif candidate.sweep_type == "breakout" and last_closed["close"] < candidate.sweep_candle["open"]:
                        print("breakout sweep ob confirmed")
                        return ob_found
                    else:
                        return None

                break

    # ---------------------------------------
    # Bullish Setup (sell-side sweep first)
    # ---------------------------------------
    if direction == "sell_side":
        break_loop = True

        # find most recent bearish candle
        for i in range(len(candles) - 2, -1, -1):

            c = candles[i]
            # this candle should be bearish
            
            if c["close"] < c["open"]: # bearish candle

                # OB confirmed if last_closed closes above bearish open
                if last_closed["close"] > c["open"]:
                    print("last_closed_candle: ", last_closed["high"], last_closed["low"], last_closed["open"], last_closed["close"])
                    print("last_closed body: ", abs(last_closed["close"] - last_closed["open"]))
                    print("swee_type: ", candidate.sweep_type)
                    print("sweep_candle: ", candidate.sweep_candle)
                    print("last_closed range: ", last_closed["high"] - last_closed["low"])
                    print("ob_body_range: ", ob_body_range)
                    ob_found = {
                            "type": "bullish_ob",
                            "confirmation_timestamp": last_closed["timestamp"],
                            "ob_candle_timestamp": c["timestamp"],
                            "ob_low": c["low"],
                            "ob_high": c["open"],
                            "confirmation_high": last_closed["high"],
                            "confirmation_low": last_closed["low"],
                            "source_index": i,
                            "structure_break": last_closed["close"] > c["high"],
                            "strong_body_displacement": strong_body,
                            "ob_body_range": ob_body_range
                        }
                    
                    if candidate.sweep_type == "rejection":
                        return ob_found
                    elif candidate.sweep_type == "breakout" and last_closed["close"] > candidate.sweep_candle["open"]:
                        return ob_found
                    else:
                        return None
                    
                
                break

    return None

from datetime import datetime, timedelta


def detect_30m_order_block(candles, candidate, co_asset, co_asset_last_closed_candle):
    # We evaluate the last closed candle
    last_closed = candles[-1]
    disable_previous_ob = False
    direction = candidate.side  # "buy_side" or "sell_side"
    if direction == "sell_side" and candidate.ob_data is not None:
        if last_closed["low"] < candidate.ob_data["ob_low"]:
            disable_previous_ob = True
    elif direction == "buy_side" and candidate.ob_data is not None:
        if last_closed["high"] > candidate.ob_data["ob_high"]:
            disable_previous_ob = True

    if candidate.ob_confirmed and not disable_previous_ob:
        print("30m OB1: ", candidate.instrument)
        return candidate.ob_data

    if len(candles) < 2:
        print("30m OB2: ", candidate.instrument)
        return None

    # # We evaluate the last closed candle
    # last_closed = candles[-1]
    
    body = abs(last_closed["close"] - last_closed["open"])
    range_ = last_closed["high"] - last_closed["low"]
    strong_body = body/range_ > 0.6
    ob_body_range = body/range_

    # ---------------------------------------
    # Bearish Setup (buy-side sweep first)
    # ---------------------------------------
    if direction == "buy_side":
        print("30m OB3: ", candidate.instrument)

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
                    print("ob_level: ", c["open"])
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
                        "ob_level": c["open"]
                        # "breakout_sweep_ob": breakout_sweep_ob
                    }
                    if candidate.sweep_type == "rejection":
                        return ob_found
                    elif candidate.sweep_type == "breakout" and last_closed["close"] < candidate.sweep_candle["open"]:
                        print("breakout sweep ob confirmed")
                        return ob_found
                    elif co_asset.sweep_type == "rejection":
                        print("ggg")
                        return ob_found
                    elif co_asset.sweep_type == "breakout" and co_asset_last_closed_candle["close"] < co_asset.sweep_candle["open"]:
                        print("breakout sweep ob confirmed - ggg")
                        
                        return ob_found
                    
                    else:
                        print("lllll")
                        return None

                break

    # ---------------------------------------
    # Bullish Setup (sell-side sweep first)
    # ---------------------------------------
    elif direction == "sell_side":
        print("30m OB4: ", candidate.instrument)
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
                    print("ob_level: ", c["open"])
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
                            "ob_body_range": ob_body_range,
                            "ob_level": c["open"]
                        }
                    print("sweep_type: ", candidate.sweep_type, candidate.instrument)
                    if candidate.sweep_type == "rejection":
                        return ob_found
                    elif candidate.sweep_type == "breakout" and last_closed["close"] > candidate.sweep_candle["open"]:
                        return ob_found
                    elif co_asset.sweep_type == "rejection":
                        return ob_found
                    elif co_asset.sweep_type == "breakout" and co_asset_last_closed_candle["close"] > co_asset.sweep_candle["open"]:
                        return ob_found
                    else:
                        print("sweep NOOO: ", candidate.instrument)
                        return None
                    
                
                break
    else:
        print("sweep side not set: ", candidate.instrument )
    return None

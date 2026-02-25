def find_sweep_time_3m(inside_3m, swing_level, direction):

    for c in inside_3m:
        if direction == "buy_side":
            if c["high"] == swing_level:
                return c["timestamp"]

        elif direction == "sell_side":
            if c["low"] == swing_level:
                return c["timestamp"]

    return None
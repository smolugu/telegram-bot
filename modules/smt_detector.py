from helpers.time_windows import get_reversal_windows, is_in_reversal_window
from datetime import datetime, timedelta

def filter_unswept_highs(candles):
    """
    Keeps only highs that have NOT been swept by later candles
    """

    unswept = []

    for i in range(len(candles)):
        current_high = candles[i].high

        swept = False

        # Check if any future candle swept it
        for j in range(i + 1, len(candles)):
            if candles[j].high > current_high:
                swept = True
                break

        if not swept:
            unswept.append(candles[i])

    return unswept


def filter_unswept_lows(candles):
    unswept = []

    for i in range(len(candles)):
        current_low = candles[i].low

        swept = False

        for j in range(i + 1, len(candles)):
            if candles[j].low < current_low:
                swept = True
                break

        if not swept:
            unswept.append(candles[i])

    return unswept

def detect_htf_smt_precise(
    nq_candles,
    es_candles,
    lookback=3,
    time_tolerance=timedelta(minutes=5)
):
    bearish_smt = None
    bullish_smt = None
    if len(nq_candles) < lookback + 1:
        return None, None
    
    nq_current = nq_candles[-1]
    es_current = es_candles[-1]
    
    nq_prev = nq_candles[-(lookback+1):-1]
    es_prev = es_candles[-(lookback+1):-1]
    
    # -------------------------
    # Build ALL previous levels
    # -------------------------
    nq_unswept_highs = filter_unswept_highs(nq_prev)
    nq_prev_highs = [{"high": c.high, "timestamp": c.timestamp} for c in nq_unswept_highs]
    # print("nq prevv hihgs: ", nq_prev_highs)

    es_unswept_highs = filter_unswept_highs(es_prev)
    es_prev_highs = [{"high": c.high, "timestamp": c.timestamp} for c in es_unswept_highs]
    # print("es prevv hihgs: ", es_prev_highs)

    nq_unswept_lows = filter_unswept_lows(nq_prev)
    nq_prev_lows = [{"low": c.low, "timestamp": c.timestamp} for c in nq_unswept_lows]

    es_unswept_lows = filter_unswept_lows(es_prev)
    es_prev_lows = [{"low": c.low, "timestamp": c.timestamp} for c in es_unswept_lows]
    # print("NQ highs: ")
    # for high in nq_prev_highs:
    #     print(high["high"], end=", ")
    # print("NQ lows: ")
    # for low in nq_prev_lows:
    #     print(low["low"], end=", ")
    # print("ES highs: ")
    # for high in es_prev_highs:
    #     print(high["high"], end=", ")
    # print("ES lows: ")
    # for low in es_prev_lows:
    #     print(low["low"], end=", ")

    def find_match(ts, levels, time_tolerance=timedelta(minutes=5)):

        # ts_dt = datetime.fromisoformat(ts)
        ts_dt=None
        if isinstance(ts, str):
            ts_dt = datetime.fromisoformat(ts)
        else:
            ts_dt = ts

        for lvl in levels:
            # lvl_dt = datetime.fromisoformat(lvl["timestamp"])
            if isinstance(ts, str):
                lvl_dt = datetime.fromisoformat(lvl["timestamp"])
            else:
                lvl_dt = lvl["timestamp"]

            if abs(lvl_dt - ts_dt) <= time_tolerance:
                return lvl

        return None

    # -------------------------
    # Bearish SMT (high sweep mismatch)
    # -------------------------
    for nq_high in nq_prev_highs:

        # NQ sweeps THIS specific high
        if nq_current.high > nq_high["high"]:

            es_high = find_match(nq_high["timestamp"], es_prev_highs)
            if es_high is None:
                continue

            es_swept = es_current.high > es_high["high"]

            if not es_swept:
                bearish_smt = {
                    "type": "bearish_smt",
                    "sweeper": "nq",
                    "nq_level_price": nq_high["high"],
                    "es_level_price": es_high["high"],
                    "level_ts": nq_high["timestamp"]
                }

    # Reverse: ES sweeps, NQ doesn't
    for es_high in es_prev_highs:

        if es_current.high > es_high["high"]:

            nq_high = find_match(es_high["timestamp"], nq_prev_highs)
            if nq_high is None:
                continue

            nq_swept = nq_current.high > nq_high["high"]

            if not nq_swept:
                bearish_smt = {
                    "type": "bearish_smt",
                    "sweeper": "es",
                    "nq_level_price": nq_high["high"],
                    "es_level_price": es_high["high"],
                    "level_ts": es_high["timestamp"]
                }

    # -------------------------
    # Bullish SMT (low sweep mismatch)
    # -------------------------
    for nq_low in nq_prev_lows:

        if nq_current.low < nq_low["low"]:

            es_low = find_match(nq_low["timestamp"], es_prev_lows)
            if es_low is None:
                continue

            es_swept = es_current.low < es_low["low"]

            if not es_swept:
                bullish_smt = {
                    "type": "bullish_smt",
                    "sweeper": "nq",
                    "nq_level_price": nq_low["low"],
                    "es_level_price": es_low["low"],
                    "level_ts": nq_low["timestamp"]
                }

    for es_low in es_prev_lows:

        if es_current.low < es_low["low"]:

            nq_low = find_match(es_low["timestamp"], nq_prev_lows)
            if nq_low is None:
                continue

            nq_swept = nq_current.low < nq_low["low"]

            if not nq_swept:
                bullish_smt = {
                    "type": "bullish_smt",
                    "sweeper": "es",
                    "nq_level_price": nq_low["low"],
                    "es_level_price": es_low["low"],
                    "level_ts": es_low["timestamp"]
                }
            
    return bullish_smt, bearish_smt

def detect_htf_smt_liquidity(
    nq_candles,
    es_candles,
    lookback=30,
    time_tolerance=timedelta(minutes=5)
):
    bearish_smt = None
    bullish_smt = None
    if len(nq_candles) < lookback + 1:
        return None, None
    
    nq_current = nq_candles[-1]
    es_current = es_candles[-1]
    
    nq_prev = nq_candles[-(lookback+1):-1]
    es_prev = es_candles[-(lookback+1):-1]
    
    # -------------------------
    # Build ALL previous levels
    # -------------------------
    nq_unswept_highs = filter_unswept_highs(nq_prev)
    nq_prev_highs = [{"high": c.high, "timestamp": c.timestamp} for c in nq_unswept_highs]
    # print("nq prevv hihgs: ", nq_prev_highs)

    es_unswept_highs = filter_unswept_highs(es_prev)
    es_prev_highs = [{"high": c.high, "timestamp": c.timestamp} for c in es_unswept_highs]
    # print("es prevv hihgs: ", es_prev_highs)

    nq_unswept_lows = filter_unswept_lows(nq_prev)
    nq_prev_lows = [{"low": c.low, "timestamp": c.timestamp} for c in nq_unswept_lows]

    es_unswept_lows = filter_unswept_lows(es_prev)
    es_prev_lows = [{"low": c.low, "timestamp": c.timestamp} for c in es_unswept_lows]
    
    nq_buyside_remaining = len(nq_prev_highs)
    es_buyside_remaining = len(es_prev_highs)

    nq_sellside_remaining = len(nq_prev_lows)
    es_sellside_remaining = len(es_prev_lows)
    buy_diff = abs(nq_buyside_remaining - es_buyside_remaining)
    sell_diff = abs(nq_sellside_remaining - es_sellside_remaining)
    # -------------------------
    # Bearish SMT (high sweep mismatch)
    # -------------------------

    if buy_diff > 0:
        bearish_smt = {
            "type": "bearish_smt",
            "sweeper": "es" if nq_buyside_remaining > es_buyside_remaining else "nq",
        }
    if sell_diff > 0:
        bullish_smt = {
            "type": "bullish_smt",
            "sweeper": "es" if nq_sellside_remaining > es_sellside_remaining else "nq",
        }
            
    return bullish_smt, bearish_smt

def detect_daily_smt_precise(
    nq_candles,
    es_candles,
    nq_session = None,
    es_session = None,
    lookback=3,
    time_tolerance=timedelta(minutes=5)
):
    bearish_smt = None
    bullish_smt = None
    if len(nq_candles) < lookback + 1:
        return None, None
    
    nq_current = nq_candles[-1]
    es_current = es_candles[-1]
    
    nq_prev = nq_candles[-(lookback+1):-1]
    es_prev = es_candles[-(lookback+1):-1]
    
    # -------------------------
    # Build ALL previous levels
    # -------------------------
    nq_unswept_highs = filter_unswept_highs(nq_prev)
    nq_prev_highs = [{"high": c.high, "timestamp": c.timestamp} for c in nq_unswept_highs]
    # print("nq prevv hihgs: ", nq_prev_highs)

    es_unswept_highs = filter_unswept_highs(es_prev)
    es_prev_highs = [{"high": c.high, "timestamp": c.timestamp} for c in es_unswept_highs]
    # print("es prevv hihgs: ", es_prev_highs)

    nq_unswept_lows = filter_unswept_lows(nq_prev)
    nq_prev_lows = [{"low": c.low, "timestamp": c.timestamp} for c in nq_unswept_lows]

    es_unswept_lows = filter_unswept_lows(es_prev)
    es_prev_lows = [{"low": c.low, "timestamp": c.timestamp} for c in es_unswept_lows]
    # print("NQ highs: ")
    # for high in nq_prev_highs:
    #     print(high["high"], end=", ")
    # print("NQ lows: ")
    # for low in nq_prev_lows:
    #     print(low["low"], end=", ")
    # print("ES highs: ")
    # for high in es_prev_highs:
    #     print(high["high"], end=", ")
    # print("ES lows: ")
    # for low in es_prev_lows:
    #     print(low["low"], end=", ")

    def find_match(ts, levels, time_tolerance=timedelta(minutes=5)):

        # ts_dt = datetime.fromisoformat(ts)

        ts_dt=None
        if isinstance(ts, str):
            ts_dt = datetime.fromisoformat(ts)
        else:
            ts_dt = ts

        for lvl in levels:
            # lvl_dt = datetime.fromisoformat(lvl["timestamp"])
            if isinstance(ts, str):
                lvl_dt = datetime.fromisoformat(lvl["timestamp"])
            else:
                lvl_dt = lvl["timestamp"]

            if abs(lvl_dt - ts_dt) <= time_tolerance:
                return lvl

        return None

    # -------------------------
    # Bearish SMT (high sweep mismatch)
    # -------------------------
    for nq_high in nq_prev_highs:

        # NQ sweeps THIS specific high
        if nq_current.high > nq_high["high"]:

            es_high = find_match(nq_high["timestamp"], es_prev_highs)
            if es_high is None:
                continue

            es_swept = es_current.high > es_high["high"]

            if not es_swept:
                bearish_smt = {
                    "type": "bearish_smt",
                    "sweeper": "nq",
                    "nq_level_price": nq_high["high"],
                    "es_level_price": es_high["high"],
                    "level_ts": nq_high["timestamp"]
                }

    # Reverse: ES sweeps, NQ doesn't
    for es_high in es_prev_highs:

        if es_current.high > es_high["high"]:

            nq_high = find_match(es_high["timestamp"], nq_prev_highs)
            if nq_high is None:
                continue

            nq_swept = nq_current.high > nq_high["high"]

            if not nq_swept:
                bearish_smt = {
                    "type": "bearish_smt",
                    "sweeper": "es",
                    "nq_level_price": nq_high["high"],
                    "es_level_price": es_high["high"],
                    "level_ts": es_high["timestamp"]
                }

    # -------------------------
    # Bullish SMT (low sweep mismatch)
    # -------------------------
    for nq_low in nq_prev_lows:

        if nq_current.low < nq_low["low"]:

            es_low = find_match(nq_low["timestamp"], es_prev_lows)
            if es_low is None:
                continue

            es_swept = es_current.low < es_low["low"]

            if not es_swept:
                bullish_smt = {
                    "type": "bullish_smt",
                    "sweeper": "nq",
                    "nq_level_price": nq_low["low"],
                    "es_level_price": es_low["low"],
                    "level_ts": nq_low["timestamp"]
                }

    for es_low in es_prev_lows:

        if es_current.low < es_low["low"]:

            nq_low = find_match(es_low["timestamp"], nq_prev_lows)
            if nq_low is None:
                continue

            nq_swept = nq_current.low < nq_low["low"]

            if not nq_swept:
                bullish_smt = {
                    "type": "bullish_smt",
                    "sweeper": "es",
                    "nq_level_price": nq_low["low"],
                    "es_level_price": es_low["low"],
                    "level_ts": es_low["timestamp"]
                }
            
    return bullish_smt, bearish_smt



def detect_smt_key_levels(nq_swept, es_swept):

    nq_swept = nq_swept or []
    es_swept = es_swept or []

    # Convert to dict for fast lookup
    nq_map = {lvl["level_name"]: lvl for lvl in nq_swept}
    es_map = {lvl["level_name"]: lvl for lvl in es_swept}

    all_levels = set(nq_map.keys()) | set(es_map.keys())

    results = []

    for level in all_levels:

        nq_lvl = nq_map.get(level)
        es_lvl = es_map.get(level)

        # -------------------------
        # Only NQ swept this level
        # -------------------------
        if nq_lvl and not es_lvl:

            if nq_lvl["side"] == "sell_side":
                results.append({
                    "type": "bullish_smt",
                    "sweeper": "nq",
                    "level": level,
                    "details": nq_lvl
                })

            elif nq_lvl["side"] == "buy_side":
                results.append({
                    "type": "bearish_smt",
                    "sweeper": "nq",
                    "level": level,
                    "details": nq_lvl
                })

        # -------------------------
        # Only ES swept this level
        # -------------------------
        elif es_lvl and not nq_lvl:

            if es_lvl["side"] == "sell_side":
                results.append({
                    "type": "bullish_smt",
                    "sweeper": "es",
                    "level": level,
                    "details": es_lvl
                })

            elif es_lvl["side"] == "buy_side":
                results.append({
                    "type": "bearish_smt",
                    "sweeper": "es",
                    "level": level,
                    "details": es_lvl
                })

        # -------------------------
        # Both swept → NO SMT
        # -------------------------
        else:
            continue

    return results if results else None

def detect_bearish_smt_key_levels(nq_swept, es_swept):

    nq_swept = nq_swept or []
    es_swept = es_swept or []

    # Convert to dict for fast lookup
    nq_map = {lvl["level_name"]: lvl for lvl in nq_swept}
    es_map = {lvl["level_name"]: lvl for lvl in es_swept}

    all_levels = set(nq_map.keys()) | set(es_map.keys())

    results = []

    for level in all_levels:

        nq_lvl = nq_map.get(level)
        es_lvl = es_map.get(level)

        # -------------------------
        # Only NQ swept this level
        # -------------------------
        if nq_lvl and not es_lvl:

            if nq_lvl["side"] == "buy_side":
                results.append({
                    "type": "bearish_smt",
                    "sweeper": "nq",
                    "level": level,
                    "details": nq_lvl
                })

        # -------------------------
        # Only ES swept this level
        # -------------------------
        elif es_lvl and not nq_lvl:

            if es_lvl["side"] == "buy_side":
                results.append({
                    "type": "bearish_smt",
                    "sweeper": "es",
                    "level": level,
                    "details": es_lvl
                })

        # -------------------------
        # Both swept → NO SMT
        # -------------------------
        else:
            continue

    return results if results else None

def detect_bullish_smt_key_levels(nq_swept, es_swept):

    nq_swept = nq_swept or []
    es_swept = es_swept or []

    # Convert to dict for fast lookup
    nq_map = {lvl["level_name"]: lvl for lvl in nq_swept}
    es_map = {lvl["level_name"]: lvl for lvl in es_swept}

    all_levels = set(nq_map.keys()) | set(es_map.keys())

    results = []

    for level in all_levels:

        nq_lvl = nq_map.get(level)
        es_lvl = es_map.get(level)

        # -------------------------
        # Only NQ swept this level
        # -------------------------
        if nq_lvl and not es_lvl:

            if nq_lvl["side"] == "sell_side":
                results.append({
                    "type": "bullish_smt",
                    "sweeper": "nq",
                    "level": level,
                    "details": nq_lvl
                })

        # -------------------------
        # Only ES swept this level
        # -------------------------
        elif es_lvl and not nq_lvl:

            if es_lvl["side"] == "sell_side":
                results.append({
                    "type": "bullish_smt",
                    "sweeper": "es",
                    "level": level,
                    "details": es_lvl
                })


        # -------------------------
        # Both swept → NO SMT
        # -------------------------
        else:
            continue

    return results if results else None


def detect_30m_swing_smt(
    nq_swings_high,
    nq_swings_low,
    es_swings_high,
    es_swings_low,
    current_nq_candle,
    current_es_candle,
    time_tolerance=timedelta(minutes=5)
):
    bullish_smt = None
    bearish_smt = None
    
    # def find_matching_swing_old(target_ts, swings):
    #     for s in swings:
    #         # dt_target = datetime.fromisoformat(target_ts)
    #         dt_target = None
    #         if isinstance(target_ts, str):
    #             dt_target = datetime.fromisoformat(target_ts)
    #         else:
    #             dt_target = target_ts
    #         # dt = datetime.fromisoformat(s.timestamp)
    #         dt=None
    #         if isinstance(s.timestamp, str):
    #             dt = datetime.fromisoformat(s.timestamp)
    #         else:
    #             dt = s.timestamp
    #         # if abs(s["timestamp"] - target_ts) <= time_tolerance:
    #         if dt_target.hour == dt.hour and dt_target.minute == dt.minute:
    #             return s
    #     return None
    
    def find_matching_swing(target_ts, swings):
        if isinstance(target_ts, str):
            target_ts = datetime.fromisoformat(target_ts)

        for s in swings:
            dt = s.timestamp

            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt)

            if abs(dt - target_ts) <= time_tolerance:
                return s

        return None

    # -------------------------
    # Bullish SMT (lows)
    # -------------------------
    for nq_swing in nq_swings_low:

        es_swing = find_matching_swing(nq_swing.timestamp, es_swings_low)
        if es_swing is None:
            continue

        nq_swept = current_nq_candle.low < nq_swing.low
        es_swept = current_es_candle.low < es_swing.low

        # XOR condition → only one sweeps
        if nq_swept != es_swept:

            bullish_smt = {
                "type": "bullish_smt",
                "sweeper": "nq" if nq_swept else "es",
                "nq_swing": nq_swing,
                "es_swing": es_swing
            }

    # -------------------------
    # Bearish SMT (highs)
    # -------------------------
    for nq_swing in nq_swings_high:

        es_swing = find_matching_swing(nq_swing.timestamp, es_swings_high)
        if es_swing is None:
            continue

        nq_swept = current_nq_candle.high > nq_swing.high
        es_swept = current_es_candle.high > es_swing.high

        if nq_swept != es_swept:

            bearish_smt = {
                "type": "bearish_smt",
                "sweeper": "nq" if nq_swept else "es",
                "nq_swing": nq_swing,
                "es_swing": es_swing
            }

    return bullish_smt, bearish_smt

def detect_smt_dual(
    nq_30m,
    es_30m,
    nq_1h,
    es_1h,
    current_7h_open_iso,
    wick_window_minutes
):
  
    windows = get_reversal_windows(
        current_7h_open_iso,
        wick_window_minutes
    )

    result = _check_tf(nq_30m, es_30m, windows, "30m")
    if result["smt_confirmed"]:
        return result

    result = _check_tf(nq_1h, es_1h, windows, "1h")
    return result


def _check_tf(nq, es, windows, tf_name):

    nq_highs = _find_swing_highs(nq)
    nq_lows = _find_swing_lows(nq)
    es_highs = _find_swing_highs(es)
    es_lows = _find_swing_lows(es)
    # print("Swing High Count NQ:", len(nq_highs))
    # print("Swing High Count ES:", len(es_highs))


    # -------- Bearish SMT (High divergence) --------
    for nq_h in nq_highs:
        valid, window_name = is_in_reversal_window(
            nq_h.timestamp,
            windows
        )
        if not valid:
            continue

        for es_h in es_highs:

            if nq_h.high > es_h.high:
                # print("Bearish SMT FOUND at", nq_h["timestamp"])
                return {
                    "smt_confirmed": True,
                    "type": "bearish",
                    "sweeper": "NQ",
                    "trade_symbol": "NQ",
                    "trade_direction": "SHORT",
                    "tf": tf_name,
                    "window": window_name,
                    "timestamp": nq_h.timestamp
                }

            if es_h.high > nq_h.high:
                return {
                    "smt_confirmed": True,
                    "type": "bearish",
                    "sweeper": "ES",
                    "trade_symbol": "ES",
                    "trade_direction": "SHORT",
                    "tf": tf_name,
                    "window": window_name,
                    "timestamp": nq_h.timestamp
                }

    # -------- Bullish SMT (Low divergence) --------
    for nq_l in nq_lows:
        valid, window_name = is_in_reversal_window(
            nq_l.timestamp,
            windows
        )
        if not valid:
            continue

        for es_l in es_lows:

            if nq_l.low < es_l.low:
                return {
                    "smt_confirmed": True,
                    "type": "bullish",
                    "sweeper": "NQ",
                    "trade_symbol": "ES",
                    "trade_direction": "LONG",
                    "tf": tf_name,
                    "window": window_name,
                    "timestamp": nq_l.timestamp
                }

            if es_l.low < nq_l.low:
                return {
                    "smt_confirmed": True,
                    "type": "bullish",
                    "sweeper": "ES",
                    "trade_symbol": "NQ",
                    "trade_direction": "LONG",
                    "tf": tf_name,
                    "window": window_name,
                    "timestamp": nq_l.timestamp
                }

    return {"smt_confirmed": False}


def _find_swing_highs(candles):
    swings = []
    for i in range(1, len(candles) - 1):
        if candles[i]["high"] > candles[i-1]["high"] and candles[i]["high"] > candles[i+1]["high"]:
            swings.append(candles[i])
    return swings


def _find_swing_lows(candles):
    swings = []
    for i in range(1, len(candles) - 1):
        if candles[i]["low"] < candles[i-1]["low"] and candles[i]["low"] < candles[i+1]["low"]:
            swings.append(candles[i])
    return swings

def summary_smt(h7_bullish_smt_liquidity, h7_bearish_smt_liquidity, h4_bullish_smt_liquidity, h4_bearish_smt_liquidity, h1_bullish_smt_liquidity, h1_bearish_smt_liquidity, h1_bullish_smt, h1_bearish_smt, key_level_bullish_smt_result, key_level_bearish_smt_result, bullish_30m_swing_smt, bearish_30m_swing_smt):

    # # Priority 1: 1h SMT
    # if h1_bullish_smt:
    #     return "bullish", h1_bullish_smt
    # if h1_bearish_smt:
    #     return "bearish", h1_bearish_smt

    # # Priority 2: Key level sweep SMT
    # if key_level_bullish_smt_result:
    #     return "bullish", key_level_bullish_smt_result
    # if key_level_bearish_smt_result:
    #     return "bearish", key_level_bearish_smt_result

    # # Priority 3: 30m swing SMT
    # if bullish_30m_swing_smt:
    #     return "bullish", bullish_30m_swing_smt
    # if bearish_30m_swing_smt:
    #     return "bearish", bearish_30m_swing_smt

    return {
        "bullish_smt_1h": h1_bullish_smt,
        "bullish_smt_1h_liquidity": h1_bullish_smt_liquidity,
        "bullish_smt_4h_liquidity": h4_bullish_smt_liquidity,
        "bullish_smt_7h_liquidity": h7_bullish_smt_liquidity,
        "bullish_smt_30m_swing": bullish_30m_swing_smt,
        "bullish_smt_key_level": key_level_bullish_smt_result,
    }, {"bearish_smt_1h": h1_bearish_smt,
        "bearish_smt_1h_liquidity": h1_bearish_smt_liquidity,
        "bearish_smt_4h_liquidity": h4_bearish_smt_liquidity,
        "bearish_smt_7h_liquidity": h7_bearish_smt_liquidity,
        "bearish_smt_30m_swing": bearish_30m_swing_smt,
        "bearish_smt_key_level": key_level_bearish_smt_result}

# updated new smt functions - October 3, 2026
def get_latest_valid_swing(swings):
    if not swings:
        return None

    return max(
        swings,
        key=lambda s: s.timestamp
    )

def detect_short_term_smt(
    nq_30m_swings_high,
    nq_30m_swings_low,
    es_30m_swings_high,
    es_30m_swings_low,
    nq_1h_swings_high,
    nq_1h_swings_low,
    es_1h_swings_high,
    es_1h_swings_low,
    previous_3_nq_30m_candles,
    previous_3_es_30m_candles,
    previous_2_nq_1h_candles,
    previous_2_es_1h_candles,
    current_nq_candle,
    current_es_candle,
):
    bullish_smt = []
    bearish_smt = []
    
    # ---------------------------------------------------------
    # Most recent valid swings
    # ---------------------------------------------------------

    nq_30m_high = get_latest_valid_swing(nq_30m_swings_high)
    nq_30m_low = get_latest_valid_swing(nq_30m_swings_low)

    es_30m_high = get_latest_valid_swing(es_30m_swings_high)
    es_30m_low = get_latest_valid_swing(es_30m_swings_low)

    nq_1h_high = get_latest_valid_swing(nq_1h_swings_high)
    nq_1h_low = get_latest_valid_swing(nq_1h_swings_low)

    es_1h_high = get_latest_valid_swing(es_1h_swings_high)
    es_1h_low = get_latest_valid_swing(es_1h_swings_low)

    # ---------------------------------------------------------
    # Bearish SMT — 30m swing
    # ---------------------------------------------------------

    if nq_30m_high and es_30m_high:

        nq_swept = current_nq_candle.high > nq_30m_high.high
        es_swept = current_es_candle.high > es_30m_high.high

        if nq_swept != es_swept:
            bearish_smt.append({
                "type": "bearish_smt",
                "source": "30m_swing",
                "sweeper": "nq" if nq_swept else "es",
                "nq_level_price": nq_30m_high.high,
                "es_level_price": es_30m_high.high,
                "level_timestamp": nq_30m_high.timestamp,
                "sweep_timestamp": current_nq_candle.timestamp,
            }) 
            

    # ---------------------------------------------------------
    # Bullish SMT — 30m swing
    # ---------------------------------------------------------

    if nq_30m_low and es_30m_low:

        nq_swept = current_nq_candle.low < nq_30m_low.low
        es_swept = current_es_candle.low < es_30m_low.low

        if nq_swept != es_swept:
            bullish_smt.append({
                "type": "bullish_smt",
                "source": "30m_swing",
                "sweeper": "nq" if nq_swept else "es",
                "nq_level_price": nq_30m_low.low,
                "es_level_price": es_30m_low.low,
                "level_timestamp": nq_30m_low.timestamp,
                "sweep_timestamp": current_nq_candle.timestamp,
            }) 
            

    # ---------------------------------------------------------
    # Bearish SMT — 1h swing
    # ---------------------------------------------------------

    if nq_1h_high and es_1h_high:

        nq_swept = current_nq_candle.high > nq_1h_high.high
        es_swept = current_es_candle.high > es_1h_high.high

        if nq_swept != es_swept:
            bearish_smt.append({
                "type": "bearish_smt",
                "source": "1h_swing",
                "sweeper": "nq" if nq_swept else "es",
                "nq_level_price": nq_1h_high.high,
                "es_level_price": es_1h_high.high,
                "level_timestamp": nq_1h_high.timestamp,
                "sweep_timestamp": current_nq_candle.timestamp,
            })
            
    # ---------------------------------------------------------
    # Bullish SMT — 1h swing
    # ---------------------------------------------------------

    if nq_1h_low and es_1h_low:

        nq_swept = current_nq_candle.low < nq_1h_low.low
        es_swept = current_es_candle.low < es_1h_low.low

        if nq_swept != es_swept:
            bullish_smt.append({
                "type": "bullish_smt",
                "source": "1h_swing",
                "sweeper": "nq" if nq_swept else "es",
                "nq_level_price": nq_1h_low.low,
                "es_level_price": es_1h_low.low,
                "level_timestamp": nq_1h_low.timestamp,
                "sweep_timestamp": current_nq_candle.timestamp,
            })
            
    # ---------------------------------------------------------
    # Bearish SMT — previous 3 30m candle extreme
    # ---------------------------------------------------------

    for previous_nq_30m_candle, previous_es_30m_candle in zip(
        previous_3_nq_30m_candles,
        previous_3_es_30m_candles
    ):
        # Bearish SMT: one asset sweeps the previous high, the other does not
        nq_swept = current_nq_candle.high > previous_nq_30m_candle.high
        es_swept = current_es_candle.high > previous_es_30m_candle.high

        if nq_swept != es_swept:
            bearish_smt.append({
                "type": "bearish_smt",
                "source": "30m_extreme",
                "sweeper": "nq" if nq_swept else "es",
                "nq_level_price": previous_nq_30m_candle.high,
                "es_level_price": previous_es_30m_candle.high,
                "level_timestamp": previous_nq_30m_candle.timestamp,
                "sweep_timestamp": current_nq_candle.timestamp,
            })

        # Bullish SMT: one asset sweeps the previous low, the other does not
        nq_swept = current_nq_candle.low < previous_nq_30m_candle.low
        es_swept = current_es_candle.low < previous_es_30m_candle.low

        if nq_swept != es_swept:
            bullish_smt.append({
                "type": "bullish_smt",
                "source": "30m_extreme",
                "sweeper": "nq" if nq_swept else "es",
                "nq_level_price": previous_nq_30m_candle.low,
                "es_level_price": previous_es_30m_candle.low,
                "level_timestamp": previous_nq_30m_candle.timestamp,
                "sweep_timestamp": current_nq_candle.timestamp,
            })

    # ---------------------------------------------------------
    # Bearish SMT — previous 1h candle extreme
    # ---------------------------------------------------------
    # 1h candles
    recent_nq_1h = previous_2_nq_1h_candles[-1]
    prior_nq_1h = previous_2_nq_1h_candles[-2]

    recent_es_1h = previous_2_es_1h_candles[-1]
    prior_es_1h = previous_2_es_1h_candles[-2]

    # 1H extreme SMT
    #
    # Compare the most recent completed 1H candle
    # against the immediately preceding completed 1H candle.
    # This deliberately avoids the currently forming 1H candle.

    # Bearish SMT
    nq_swept = recent_nq_1h.high > prior_nq_1h.high
    es_swept = recent_es_1h.high > prior_es_1h.high

    if nq_swept != es_swept:
        bearish_smt.append({
            "type": "bearish_smt",
            "source": "1h_extreme",
            "sweeper": "nq" if nq_swept else "es",
            "nq_level_price": prior_nq_1h.high,
            "es_level_price": prior_es_1h.high,
            "level_timestamp": prior_nq_1h.timestamp,
            "sweep_timestamp": recent_nq_1h.timestamp,
        })


    # Bullish SMT
    nq_swept = recent_nq_1h.low < prior_nq_1h.low
    es_swept = recent_es_1h.low < prior_es_1h.low

    if nq_swept != es_swept:
        bullish_smt.append({
            "type": "bullish_smt",
            "source": "1h_extreme",
            "sweeper": "nq" if nq_swept else "es",
            "nq_level_price": prior_nq_1h.low,
            "es_level_price": prior_es_1h.low,
            "level_timestamp": prior_nq_1h.timestamp,
            "sweep_timestamp": recent_nq_1h.timestamp,
        })

    return bullish_smt, bearish_smt
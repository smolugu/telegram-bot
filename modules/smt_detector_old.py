from datetime import timedelta

def detect_smt(
    nq_swings_high,
    nq_swings_low,
    es_swings_high,
    es_swings_low,
    current_nq_candle,
    current_es_candle,
    time_tolerance=timedelta(minutes=5)
):

    def find_matching_swing(target_ts, swings):
        for s in swings:
            if abs(s["timestamp"] - target_ts) <= time_tolerance:
                return s
        return None

    # -------------------------
    # Bullish SMT (lows)
    # -------------------------
    for nq_swing in nq_swings_low:

        es_swing = find_matching_swing(nq_swing["timestamp"], es_swings_low)
        if es_swing is None:
            continue

        nq_swept = current_nq_candle["low"] < nq_swing["price"]
        es_swept = current_es_candle["low"] < es_swing["price"]

        # XOR condition → only one sweeps
        if nq_swept != es_swept:

            return {
                "type": "bullish_smt",
                "sweeper": "nq" if nq_swept else "es",
                "nq_swing": nq_swing,
                "es_swing": es_swing
            }

    # -------------------------
    # Bearish SMT (highs)
    # -------------------------
    for nq_swing in nq_swings_high:

        es_swing = find_matching_swing(nq_swing["timestamp"], es_swings_high)
        if es_swing is None:
            continue

        nq_swept = current_nq_candle["high"] > nq_swing["price"]
        es_swept = current_es_candle["high"] > es_swing["price"]

        if nq_swept != es_swept:

            return {
                "type": "bearish_smt",
                "sweeper": "nq" if nq_swept else "es",
                "nq_swing": nq_swing,
                "es_swing": es_swing
            }

    return None
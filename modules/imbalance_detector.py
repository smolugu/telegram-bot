# from datetime import timedelta, datetime

# def detect_3m_imbalance_inside_ob_candle(
#     candles_3m,
#     candidate
# ):

#     if not candidate.ob_confirmed:
#         return None

#     ob = candidate.ob_data

#     confirmation_ts = datetime.fromisoformat(ob["confirmation_timestamp"])
#     ob_candle_start = confirmation_ts - timedelta(minutes=30)
#     ob_candle_end = confirmation_ts

#     ob_high = ob["ob_high"]
#     ob_low = ob["ob_low"]

#     # 1️⃣ Extract 3m candles inside OB candle
#     inside = [
#         c for c in candles_3m
#         if ob_candle_start <= datetime.fromisoformat(c["timestamp"]) < ob_candle_end
#     ]

#     if len(inside) < 3:
#         return None

#     direction = candidate.side

#     candidates = []

#     # 2️⃣ Detect FVGs inside that 30m window
#     for i in range(2, len(inside)):

#         c1 = inside[i - 2]
#         c3 = inside[i]

#         # ---------------------------
#         # Bearish FVG (short setup)
#         # ---------------------------
#         if direction == "buy_side":

#             if c1["low"] > c3["high"]:

#                 fvg_high = c1["low"]
#                 fvg_low = c3["high"]

#                 if fvg_high <= ob_high and fvg_low >= ob_low:

#                     distance = abs(ob_high - fvg_low)

#                     candidates.append({
#                         "entry": fvg_low,
#                         "timestamp": c3["timestamp"],
#                         "distance": distance,
#                         "type": "bearish_fvg"
#                     })

#         # ---------------------------
#         # Bullish FVG (long setup)
#         # ---------------------------
#         if direction == "sell_side":

#             if c1["high"] < c3["low"]:

#                 fvg_low = c1["high"]
#                 fvg_high = c3["low"]

#                 if fvg_low >= ob_low and fvg_high <= ob_high:

#                     distance = abs(ob_low - fvg_high)

#                     candidates.append({
#                         "entry": fvg_high,
#                         "timestamp": c3["timestamp"],
#                         "distance": distance,
#                         "type": "bullish_fvg"
#                     })

#     if not candidates:
#         return None

#     # 3️⃣ Pick closest imbalance to OB boundary
#     best = min(candidates, key=lambda x: x["distance"])

#     return best

from datetime import timedelta, datetime

def detect_3m_imbalance_inside_ob_candle(
    candles_3m,
    candidate, instrument
):

    if not candidate.ob_confirmed:
        return None

    ob = candidate.ob_data

    confirmation_ts = datetime.fromisoformat(ob["confirmation_timestamp"])
    ob_candle_start = confirmation_ts
    ob_candle_end = confirmation_ts + timedelta(minutes=30)  # look for imbalances in the 30m window after OB confirmation, not just before
    sweep_time = datetime.fromisoformat(candidate.sweep_3m_timestamp)
    ob_high = ob["ob_high"]
    ob_low = ob["ob_low"]
    ce_ob = (ob_high + ob_low) / 2
    sweep_extreme_price = candidate.sweep_candle_extreme
    print("Ob high/low:", ob_high, ob_low, "| OB candle window:", ob_candle_start, "to", ob_candle_end)
    print("Sweep timestamp:", sweep_time)
    print("On end time: ", ob_candle_end)
    print("sweep extreme: ", candidate.sweep_candle_extreme)

    # 1️⃣ Extract 3m candles inside OB candle
    inside = [
        c for c in candles_3m
        if sweep_time <= datetime.fromisoformat(c["timestamp"]) < ob_candle_end
    ]
    # print("inside candles:", inside)

    if len(inside) < 2:
        return None

    direction = candidate.side
    candidates = []

    # 2️⃣ Detect Imbalances (FVG + Volume Imbalance)
    for i in range(1, len(inside)):

        prev = inside[i - 1]
        curr = inside[i]

        prev_close = prev["close"]
        curr_open = curr["open"]

        # ==========================================================
        # 🔴 BEARISH SETUP (buy_side sweep → looking for short)
        # ==========================================================
        if direction == "buy_side":

            # ---------------------------
            # 1️⃣ Bearish Volume Imbalance (strict)
            # ---------------------------
            prev_open = prev["open"]
            prev_close = prev["close"]
            curr_open = curr["open"]
            curr_close = curr["close"]

            if (
                prev_open > prev_close and      # previous bearish
                curr_open > curr_close and      # current bearish
                prev_close > curr_open          # body gap
            ):
                vi_high = prev_close
                vi_low = curr_open

                # if vi_high <= ob_high and vi_low >= ob_low:  # Vi should be inside OB, so vi_low >= ob_low is not required
                if vi_high <= ob_high:

                    # distance = abs(ob_high - vi_low)
                    distance = abs(sweep_extreme_price - vi_low)

                    candidates.append({
                        "entry": vi_low,
                        "timestamp": curr["timestamp"],
                        "distance": distance,
                        "type": "bearish_vi",
                        "instrument": instrument,
                        "ce_ob": ce_ob
                    })
            
            # ---------------------------
            # 2️⃣ Bearish FVG (3 candle logic)
            # ---------------------------
            if i >= 2:
                c1 = inside[i - 2]
                c3 = inside[i]

                if c1["low"] > c3["high"]:

                    fvg_high = c1["low"]
                    fvg_low = c3["high"]
                    print(f"Found bearish FVG candidate - FVG High: {fvg_high}, FVG Low: {fvg_low}")
                    # if fvg_high <= ob_high and fvg_low >= ob_low:
                    if fvg_high <= ob_high:

                        # distance = abs(ob_high - fvg_low)
                        distance = abs(sweep_extreme_price - fvg_low)

                        candidates.append({
                            "entry": fvg_low,
                            "timestamp": c3["timestamp"],
                            "distance": distance,
                            "type": "bearish_fvg",
                            "instrument": instrument,
                            "ce_ob": ce_ob  
                        })

        # ==========================================================
        # 🟢 BULLISH SETUP (sell_side sweep → looking for long)
        # ==========================================================
        if direction == "sell_side":

            # ---------------------------
            # 1️⃣ Bullish Volume Imbalance (strict)
            # ---------------------------
            prev_open = prev["open"]
            prev_close = prev["close"]
            curr_open = curr["open"]
            curr_close = curr["close"]

            if (
                prev_open < prev_close and      # previous bullish
                curr_open < curr_close and      # current bullish
                prev_close < curr_open          # body gap
            ):

                vi_low = prev_close
                vi_high = curr_open

                if vi_low >= ob_low:

                    # distance = abs(ob_low - vi_high)
                    distance = abs(sweep_extreme_price - vi_high)

                    candidates.append({
                        "entry": vi_high,
                        "timestamp": curr["timestamp"],
                        "distance": distance,
                        "type": "bullish_vi",
                        "instrument": instrument,
                        "ce_ob": ce_ob
                    })

            # ---------------------------
            # 2️⃣ Bullish FVG
            # ---------------------------
            if i >= 2:
                c1 = inside[i - 2]
                c3 = inside[i]

                if c1["high"] < c3["low"]:

                    fvg_low = c1["high"]
                    fvg_high = c3["low"]

                    if fvg_low >= ob_low:

                        # distance = abs(ob_low - fvg_high)
                        distance = abs(sweep_extreme_price - fvg_high)

                        candidates.append({
                            "entry": fvg_high,
                            "timestamp": c3["timestamp"],
                            "distance": distance,
                            "type": "bullish_fvg",
                            "instrument": instrument,
                            "ce_ob": ce_ob
                        })

    if not candidates:
        return None
    print("Imbalance candidates:", candidates)

    # 3️⃣ Pick closest imbalance to OB boundary
    best = max(candidates, key=lambda x: x["distance"])

    return best
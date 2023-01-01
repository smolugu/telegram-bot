
from datetime import timedelta, datetime

from data.models.candle import NY_TZ
from market_data.candle_builder.htf_candle_builder import UTC_TZ

def detect_9am_fvg(
    nq_contract,
    es_contract,
    candle_repo,
    end_utc: datetime,
):
    """
    At the beginning of the 9:00 AM NY 30m candle, inspect
    the completed 7:30, 8:00 and 8:30 30m candles.

    If an FVG exists, return it as a key liquidity level.

    Returns:
        {
            "NQ": fvg | None,
            "ES": fvg | None,
        }
    """

    results = {}

    # ---------------------------------------------------------
    # Convert current boundary to NY time
    # ---------------------------------------------------------
    end_ny = end_utc.astimezone(NY_TZ)

    # Only run at the beginning of the 9:00 AM 30m candle
    if not (
        end_ny.hour == 9
        and end_ny.minute == 0
    ):
        return results

    # ---------------------------------------------------------
    # 7:30 -> 9:00 NY
    # ---------------------------------------------------------
    start_ny = end_ny.replace(
        hour=7,
        minute=30,
        second=0,
        microsecond=0,
    )

    end_ny = end_ny.replace(
        hour=9,
        minute=0,
        second=0,
        microsecond=0,
    )

    start_utc = start_ny.astimezone(UTC_TZ)
    end_utc = end_ny.astimezone(UTC_TZ)

    for instrument, contract in [
        ("NQ", nq_contract),
        ("ES", es_contract),
    ]:

        # -----------------------------------------------------
        # Get 7:30, 8:00 and 8:30 candles
        # -----------------------------------------------------
        candles = candle_repo.get_between(
            contract=contract,
            timeframe=30,
            start=start_utc,
            end=end_utc - timedelta(minutes=30),
        )

        if len(candles) != 3:
            print(
                f">>> {instrument}: expected 3 candles "
                f"for 7:30–9:00, found {len(candles)}"
            )
            results[instrument] = None
            continue

        c1 = candles[0]   # 7:30
        c2 = candles[1]   # 8:00
        c3 = candles[2]   # 8:30

        print(
            f">>> {instrument} 9AM FVG check:"
            f"\n    7:30 H={c1.high} L={c1.low}"
            f"\n    8:00 H={c2.high} L={c2.low}"
            f"\n    8:30 H={c3.high} L={c3.low}"
        )

        fvg = None

        # -----------------------------------------------------
        # Bullish FVG
        #
        # Candle 1 high < Candle 3 low
        # -----------------------------------------------------
        if c1.high < c3.low:

            fvg = {
                "instrument": instrument,
                "type": "bullish",
                "low": c1.high,
                "high": c3.low,
                "timestamp": c3.timestamp,
                "source": "9am_fvg",
                "level": c3.low
            }

        # -----------------------------------------------------
        # Bearish FVG
        #
        # Candle 1 low > Candle 3 high
        # -----------------------------------------------------
        elif c1.low > c3.high:

            fvg = {
                "instrument": instrument,
                "type": "bearish",
                "low": c3.high,
                "high": c1.low,
                "timestamp": c3.timestamp,
                "source": "9am_fvg",
                "level": c3.high
            }

        results[instrument] = fvg

        if fvg:
            print(
                f">>> {instrument} 9AM FVG detected: "
                f"{fvg['type']} "
                f"{fvg['low']} → {fvg['high']}"
            )
        else:
            print(
                f">>> {instrument}: "
                f"no 9AM FVG"
            )

    return results

def detect_3m_imbalance_inside_ob_candle(
    candles_3m,
    candidate, instrument, last_closed_candle
):

    if not candidate.final_ob_confirmed:
        print("return none as final ob not confirmed")
        return None
    confirmation_ts=None
    if candidate.ob_data is not None:
        ob = candidate.ob_data
        # confirmation_ts = datetime.fromisoformat(ob["confirmation_timestamp"])
        
        if isinstance(ob["confirmation_timestamp"], str):
            confirmation_ts = datetime.fromisoformat(ob["confirmation_timestamp"])
        else:
            confirmation_ts = ob["confirmation_timestamp"]
        ob_high = ob["ob_high"]
        ob_low = ob["ob_low"]
        ce_ob = (ob_high + ob_low) / 2
    else:
        ob_high = last_closed_candle.high
        ob_low = last_closed_candle.low
        # confirmation_ts = datetime.fromisoformat(last_closed_candle.timestamp)
        if isinstance(last_closed_candle.timestamp, str):
            confirmation_ts = datetime.fromisoformat(last_closed_candle.timestamp)
        else:
            confirmation_ts = last_closed_candle.timestamp
        ce_ob = (ob_high + ob_low) / 2
    print("ob_low: ", ob_low)

    # we are detecting imbalances in the current candle which created the OB
    # last_closed_candle_ts = datetime.fromisoformat(last_closed_candle.timestamp)
    last_closed_candle_ts=None
    if isinstance(last_closed_candle.timestamp, str):
        last_closed_candle_ts = datetime.fromisoformat(last_closed_candle.timestamp)
    else:
        last_closed_candle_ts = last_closed_candle.timestamp
    
    if last_closed_candle_ts > confirmation_ts:
        confirmation_ts = last_closed_candle_ts
    ob_candle_start = confirmation_ts
    ob_candle_end = confirmation_ts + timedelta(minutes=30)  # look for imbalances in the 30m window after OB confirmation, not just before
    sweep_time = None
    if candidate.sweep_3m_timestamp is None:
        # sweep_time = datetime.fromisoformat(last_closed_candle.timestamp)
        sweep_time = last_closed_candle.timestamp
    else:
        # sweep_time = datetime.fromisoformat(candidate.sweep_3m_timestamp)
        sweep_time = candidate.sweep_3m_timestamp
    print("sweep time: ", sweep_time)
    # ob_high = ob["ob_high"]
    # ob_low = ob["ob_low"]
    # ce_ob = (ob_high + ob_low) / 2
    sweep_extreme_price = candidate.sweep_candle_extreme
    # print("Ob high/low:", ob_high, ob_low, "| OB candle window:", ob_candle_start, "to", ob_candle_end)
    # print("Sweep timestamp:", sweep_time)
    # print("On end time: ", ob_candle_end)
    # print("sweep extreme: ", candidate.sweep_candle_extreme)

    # 1️⃣ Extract 3m candles inside OB candle
    inside = [
        c for c in candles_3m
        if sweep_time <= c.timestamp < ob_candle_end
        # if sweep_time <= datetime.fromisoformat(c.timestamp) < ob_candle_end
    ]
    # print("inside candles:", inside)

    if len(inside) < 2:
        print("length of candles 2")
        return None

    direction = candidate.side
    if direction == "buy_side" and sweep_extreme_price == None:
        sweep_extreme_price = last_closed_candle.high
        candidate.sweep_candle_extreme = sweep_extreme_price
    if direction == "sell_side" and sweep_extreme_price == None:
        sweep_extreme_price = last_closed_candle.low
        candidate.sweep_candle_extreme = sweep_extreme_price
    candidates = []

    # 2️⃣ Detect Imbalances (FVG + Volume Imbalance)
    for i in range(1, len(inside)):
        prev = inside[i - 1]
        curr = inside[i]
        prev_close = prev.close
        curr_open = curr.open
        
        # ==========================================================
        # 🔴 BEARISH SETUP (buy_side sweep → looking for short)
        # ==========================================================
        if direction == "buy_side":

            # ---------------------------
            # 1️⃣ Bearish Volume Imbalance (strict)
            # ---------------------------
            prev_open = prev.open
            prev_close = prev.close
            curr_open = curr.open
            curr_close = curr.close
            
            if (
                prev_open > prev_close and      # previous bearish
                curr_open > curr_close and      # current bearish
                prev_close > curr_open          # body gap
            ):
                vi_high = prev_close
                vi_low = curr_open

                # if vi_high <= ob_high and vi_low >= ob_low:  # Vi should be inside OB, so vi_low >= ob_low is not required
                if vi_high <= ob_high or candidate.sweep_key_level:

                    # distance = abs(ob_high - vi_low)
                    distance = abs(sweep_extreme_price - vi_low)

                    candidates.append({
                        "entry": vi_low,
                        "timestamp": curr.timestamp,
                        "distance": distance,
                        "type": "bearish_vi",
                        "instrument": instrument,
                        "ce_ob": ce_ob
                    })
                    # print("candidates vi: ", candidates)
            
            # ---------------------------
            # 2️⃣ Bearish FVG (3 candle logic)
            # ---------------------------
            if i >= 2:
                c1 = inside[i - 2]
                c3 = inside[i]

                if c1.low > c3.high:

                    fvg_high = c1.low
                    fvg_low = c3.high
                    # print(f"Found bearish FVG candidate - FVG High: {fvg_high}, FVG Low: {fvg_low}")
                    # if fvg_high <= ob_high and fvg_low >= ob_low:
                    if fvg_high <= ob_high or candidate.sweep_key_level:

                        # distance = abs(ob_high - fvg_low)
                        distance = abs(sweep_extreme_price - fvg_low)

                        candidates.append({
                            "entry": fvg_low,
                            "timestamp": c3.timestamp,
                            "distance": distance,
                            "type": "bearish_fvg",
                            "instrument": instrument,
                            "ce_ob": ce_ob  
                        })
                        # print("candidates fvg: ", candidates)

        # ==========================================================
        # 🟢 BULLISH SETUP (sell_side sweep → looking for long)
        # ==========================================================
        if direction == "sell_side":

            # ---------------------------
            # 1️⃣ Bullish Volume Imbalance (strict)
            # ---------------------------
            prev_open = prev.open
            prev_close = prev.close
            curr_open = curr.open
            curr_close = curr.close

            if (
                prev_open < prev_close and      # previous bullish
                curr_open < curr_close and      # current bullish
                prev_close < curr_open          # body gap
            ):

                vi_low = prev_close
                vi_high = curr_open

                if vi_low >= ob_low or candidate.sweep_key_level:

                    # distance = abs(ob_low - vi_high)
                    distance = abs(sweep_extreme_price - vi_high)

                    candidates.append({
                        "entry": vi_high,
                        "timestamp": curr.timestamp,
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
                
                if c1.high < c3.low:
                
                    fvg_low = c1.high
                    fvg_high = c3.low
                    if fvg_low >= ob_low or candidate.sweep_key_level:

                        # distance = abs(ob_low - fvg_high)
                        distance = abs(sweep_extreme_price - fvg_high)

                        candidates.append({
                            "entry": fvg_high,
                            "timestamp": c3.timestamp,
                            "distance": distance,
                            "type": "bullish_fvg",
                            "instrument": instrument,
                            "ce_ob": ce_ob
                        })

    if not candidates:
        # print("no candidates")
        return None
    # print("Imbalance candidates:", candidates)

    # 3️⃣ Pick closest imbalance to OB boundary
    best = max(candidates, key=lambda x: x["distance"])

    return best
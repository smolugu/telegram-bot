from datetime import datetime, timedelta


def build_trade_alert(candidate):

    if not candidate.fvg_confirmed:
        return None
    time = candidate.ob_data["confirmation_timestamp"]
    dt = datetime.fromisoformat(time) + timedelta(minutes=30)
    time_formatted = dt.strftime("%b %d, %Y %I:%M %p")

    instrument = candidate.fvg_data["instrument"]
    side = candidate.side
    entry = candidate.fvg_data["entry"]
    risk = candidate.fvg_data["distance"]
    ce_ob = candidate.fvg_data["ce_ob"]
    ce_confirmation_candle_price = (candidate.ob_data["confirmation_high"] + candidate.ob_data["confirmation_low"]) / 2
    sweep_candle_extreme = candidate.sweep_candle_extreme
    tp = None
    if side == "buy_side" and entry < ce_confirmation_candle_price and risk > 50:
        entry = ce_confirmation_candle_price
        tp = entry - (risk * 1.5)
        # candidate.insert_trade_data = {
        #     "entry": entry,
        #     "side": side,
        #     "stop": sweep_candle_extreme,
        #     "confirmation_timestamp": time,
        #     "ce_confirmation_candle_price": ce_confirmation_candle_price,
        #     "entry_type": "CE_ADJUSTED",
        #     "tp": ce_confirmation_candle_price - (risk * 1.5)
        # }
    elif side == "sell_side" and entry > ce_confirmation_candle_price and risk > 50:
        entry = ce_confirmation_candle_price
        tp = entry + (risk * 1.5)
        # candidate.insert_trade_data = {
        #     "entry": entry,
        #     "side": side,
        #     "stop": sweep_candle_extreme,
        #     "confirmation_timestamp": time,
        #     "ce_confirmation_candle_price": ce_confirmation_candle_price,
        #     "entry_type": "CE_ADJUSTED",
        #     "tp": ce_confirmation_candle_price + (risk * 1.5)
        # }
    candidate.insert_trade_data = {
            "entry": entry,
            "side": side,
            "stop": sweep_candle_extreme,
            "confirmation_timestamp": time,
            "ce_confirmation_candle_price": ce_confirmation_candle_price,
            "entry_type": "CE_ADJUSTED",
            "tp": tp
        }

    

    # -----------------------------------
    # Determine Stop Loss
    # -----------------------------------
    if side == "buy_side":
        # bearish trade
        print("ce entry: ", entry)
        stop = sweep_candle_extreme
        bias = "Bearish"
        risk = stop - entry
        tp = entry - (risk * 1.5)

    elif side == "sell_side":
        # bullish trade
        stop = sweep_candle_extreme
        bias = "Bullish"
        risk = entry - stop
        tp = entry + (risk * 1.5)

    else:
        return None

    rr = 1.5

    alert_message = f"""
📍 TradeOnCall A++ Time

Instrument: {instrument}
Bias: {bias}
Time: {time_formatted}

Entry: {round(entry, 2)}
Stop Loss: {round(stop, 2)}
Take Profit (1.5R): {round(tp, 2)}

Risk: {round(risk, 2)}
RR: {rr}
"""

    return alert_message


# Model:
# Sweep → SMT → OB → {candidate.fvg_data["type"]}
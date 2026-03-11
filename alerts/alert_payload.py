from datetime import datetime, timedelta


def build_trade_alert(candidate):

    if not candidate.fvg_confirmed and not candidate.sweep_and_ob_confirmed:
        return None
    time = None
    if candidate.ob_data is None:
        time = None
    else:
        time = candidate.ob_data["confirmation_timestamp"]
    if candidate.sweep_and_ob_confirmation_timestamp is not None:
        time = candidate.sweep_and_ob_confirmation_timestamp
    dt = datetime.fromisoformat(time) + timedelta(minutes=30)
    time_formatted = dt.strftime("%b %d, %Y %I:%M %p")
    default_risk = None

    instrument = candidate.instrument
    if instrument == "NQ":
        default_risk = 80
    elif instrument == "ES":
        default_risk = 20
    else:
        default_risk = 50
    side = candidate.side
    entry = None
    risk = None
    ce_ob = None
    if candidate.fvg_data is not None:
        entry = candidate.fvg_data["entry"]
        risk = candidate.fvg_data["distance"]
        ce_ob = candidate.fvg_data["ce_ob"]
    ce_confirmation_candle_price = None
    if candidate.ob_data is not None:
        ce_confirmation_candle_price = (candidate.ob_data["confirmation_high"] + candidate.ob_data["confirmation_low"]) / 2
    sweep_candle_extreme = candidate.sweep_candle_extreme
    tp = None
    rr = 1
    if side == "buy_side" and candidate.sweep_and_ob_confirmed:
        if candidate.sweep_and_ob_ce_confirmed:
            entry = candidate.sweep_and_ob_ce_entry
            print("CE of Sweep and OB confirmed. Adjusting entry to:", entry)
            rr = 2
        else:
            entry = candidate.sweep_and_ob_entry - 1
            print("sweep and OB confirmed. Adjusting entry to:", entry)
            rr = 4
        risk = sweep_candle_extreme - entry
        tp = entry - (risk * rr)

    elif side == "buy_side" and entry < ce_confirmation_candle_price and risk > default_risk:
        entry = ce_confirmation_candle_price
        print("Adjusting entry to CE confirmation candle price:", entry)
        rr = 1.5
        tp = entry - (risk * rr)
        
        # candidate.insert_trade_data = {
        #     "entry": entry,
        #     "side": side,
        #     "stop": sweep_candle_extreme,
        #     "confirmation_timestamp": time,
        #     "ce_confirmation_candle_price": ce_confirmation_candle_price,
        #     "entry_type": "CE_ADJUSTED",
        #     "tp": ce_confirmation_candle_price - (risk * 1.5)
        # }
    elif side == "buy_side":
        rr = 1.5
        tp = entry - (risk * rr)
        print("Using original imbalance entry. TP adjusted to:", entry)
    elif side == "sell_side" and candidate.sweep_and_ob_confirmed:
        if candidate.sweep_and_ob_ce_confirmed:
            entry = candidate.sweep_and_ob_ce_entry
            print("CE OB confirmed. Adjusting entry to:", entry)
            rr = 2
        else:
            entry = candidate.sweep_and_ob_entry + 1
            print("sweep and OB confirmed. Adjusting entry to:", entry)
            rr = 4
        risk = entry - sweep_candle_extreme
        tp = entry + (risk * rr)
        
    elif side == "sell_side" and entry > ce_confirmation_candle_price and risk > default_risk:
        entry = ce_confirmation_candle_price
        print("Adjusting entry to CE confirmation candle price:", entry)
        rr = 1.5
        tp = entry + (risk * rr)
    elif side == "sell_side":
        rr = 1.5
        tp = entry + (risk * rr)
        print("Using original imbalance entry. TP adjusted to:", entry)
        
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
        # risk = stop - entry
        # tp = entry - (risk * 1.5)

    elif side == "sell_side":
        # bullish trade
        stop = sweep_candle_extreme
        bias = "Bullish"
        # risk = entry - stop
        # tp = entry + (risk * 1.5)

    else:
        return None

    # rr = 1.5

    alert_message = f"""
📍 TradeOnCall A++ Time

Instrument: {instrument}
Bias: {bias}
Time: {time_formatted}

Entry: {round(entry, 2)}
Stop Loss: {round(stop, 2)}
Take Profit - {rr} RR: {round(tp, 2)}

Risk: {round(risk, 2)}
RR: {rr}
"""

    return alert_message


# Model:
# Sweep → SMT → OB → {candidate.fvg_data["type"]}
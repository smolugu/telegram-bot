from datetime import datetime, timedelta

from data.models.profit_targets import get_tp_levels


def build_trade_alert(candidate, liquidity_map = None, daily_atr = None):

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
    tp1 = None
    # stop loss when we have rejection sweep at key level or swing point
    if candidate.sweep_type == "rejection":
        stop = sweep_candle_extreme
    elif candidate.sweep_type == "breakout" and candidate.ib_stop_loss is not None:
        stop = candidate.ib_stop_loss
        print("stop based on IB stop loss 1: ", stop)

    else:
        if candidate.ob_data is not None and candidate.ob_data["ob_high"] is not None:
            stop = candidate.ob_data["ob_high"] if side == "buy_side" else candidate.ob_data["ob_low"]
            if side == "buy_side":
                stop = candidate.ob_data["ob_high"] if candidate.ob_data["ob_high"] > candidate.ob_data["confirmation_high"] else candidate.ob_data["confirmation_high"]
            else:
                stop = candidate.ob_data["ob_low"] if candidate.ob_data["ob_low"] < candidate.ob_data["confirmation_low"] else candidate.ob_data["confirmation_low"]
            print("stop based on OB and confirmation candle high or low: ", stop)
        elif candidate.ib_stop_loss is not None:
            stop = candidate.ib_stop_loss
            print("stop based on IB: ", stop)
        else:
            stop = sweep_candle_extreme
    # get previous session context with bias, atr to calculate RR, entry levels
    
    rr = 1
    if side == "buy_side" and candidate.sweep_and_ob_confirmed:
        if candidate.sweep_and_ob_ce_confirmed:
            
            entry = candidate.sweep_and_ob_ce_entry
            print("entry1 buyside: ", entry)
            rr = 2
            print("CE of Sweep and OB confirmed. Adjusting entry to:", entry)
        else:
            if candidate.ob_data is not None:
                entry = candidate.ob_data["ob_low"]
                print("entry2 buyside: ", entry)
            else:
                entry = candidate.sweep_and_ob_entry
                print("entry3 buy side: ", entry)
            rr = 2
            print("sweep and OB confirmed. Adjusting entry to:", entry)
        # if candidate.sweep_and_ob_ce_confirmed:
        #     entry = candidate.sweep_and_ob_ce_entry
        #     print("CE of Sweep and OB confirmed. Adjusting entry to:", entry)
        #     rr = 2
        # else:
        #     entry = candidate.sweep_and_ob_entry - 1.5
        #     print("sweep and OB confirmed. Adjusting entry to:", entry)
        #     rr = 4
        risk = stop - entry
        tp1 = entry - (risk * rr)
        print("tp1: ", tp1)

    elif side == "buy_side" and entry < ce_confirmation_candle_price and risk > default_risk:
        entry = ce_confirmation_candle_price
        print("Adjusting entry to CE confirmation candle price:", entry)
        rr = 1.5
        tp1 = entry - (risk * rr)
        
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
        risk = abs(entry - stop)
        tp1 = entry - (risk * rr)
        print("Using original imbalance entry. TP adjusted to:", entry)
    elif side == "sell_side" and candidate.sweep_and_ob_confirmed:
        if candidate.sweep_and_ob_ce_confirmed:
            entry = candidate.sweep_and_ob_ce_entry
            print("entry1: ", entry)
            rr = 2
            print("CE of Sweep and OB confirmed. Adjusting entry to:", entry)
        else:
            if candidate.ob_data is not None:
                entry = candidate.ob_data["ob_high"]
                print("entry2: ", entry)
            else:
                entry = candidate.sweep_and_ob_entry
                print("entry3: ", entry)
            rr = 2
            print("sweep and OB confirmed. Adjusting entry to:", entry)
        # if candidate.sweep_and_ob_ce_confirmed:
        #     entry = candidate.sweep_and_ob_ce_entry
        #     print("CE OB confirmed. Adjusting entry to:", entry)
        #     rr = 2
        # else:
        #     entry = candidate.sweep_and_ob_entry + 1.5
        #     print("sweep and OB confirmed. Adjusting entry to:", entry)
        #     rr = 4
        risk = abs(entry - stop)
        tp1 = entry + (risk * rr)
        
    elif side == "sell_side" and entry > ce_confirmation_candle_price and risk > default_risk:
        entry = ce_confirmation_candle_price
        print("Adjusting entry to CE confirmation candle price:", entry)
        rr = 1.5
        tp1 = entry + (risk * rr)
    elif side == "sell_side":
        rr = 1.5
        risk = abs(entry - stop)
        tp1 = entry + (risk * rr)
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

    

    # set stop loss based on OB or IB high or low when we have sweep with displacement
    direction = "bearish" if side == "buy_side" else "bullish"
    tp1, tp2, tp3 = get_tp_levels(entry, stop, direction, liquidity_map, daily_atr, tp1)
    candidate.insert_trade_data = {
            "entry": entry,
            "side": side,
            "stop": stop,
            "confirmation_timestamp": time,
            "ce_confirmation_candle_price": ce_confirmation_candle_price,
            "entry_type": "CE_ADJUSTED",
            "tp": tp1,
            "tp2": tp2 if tp2 is not None else "N/A",
            "tp3": tp3 if tp3 is not None else "N/A",
        }

    

    # -----------------------------------
    # Determine Stop Loss
    # -----------------------------------
    if side == "buy_side":
        # bearish trade
        print("ce entry: ", entry)
        # stop = sweep_candle_extreme
        bias = "Bearish"
        # risk = stop - entry
        # tp = entry - (risk * 1.5)

    elif side == "sell_side":
        # bullish trade
        # stop = sweep_candle_extreme
        bias = "Bullish"
        # risk = entry - stop
        # tp = entry + (risk * 1.5)

    else:
        return None

    # rr = 1.5

    alert_message = f"""
 ⚡️Ping A++ Time

Instrument: {instrument}
Bias: {bias}
Time: {time_formatted}

Entry: {round(entry, 2)}
Stop Loss: {round(stop, 2)}
Take Profit 1 - {rr} RR: {round(tp1, 2)}
Take Profit 2 - Liquidity: {round(tp2, 2) if tp2 is not None else 'N/A'}
Take Profit 3 - ATR: {round(tp3, 2)}

Risk (tp1): {round(risk, 2)}
RR (tp1): {rr}
"""

    return alert_message


# Model:
# Sweep → SMT → OB → {candidate.fvg_data["type"]}
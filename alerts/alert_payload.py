def build_trade_alert(candidate):

    if not candidate.fvg_confirmed:
        return None

    instrument = candidate.fvg_data["instrument"]
    side = candidate.side
    entry = candidate.fvg_data["entry"]

    sweep_candle_extreme = candidate.sweep_candle_extreme

    # -----------------------------------
    # Determine Stop Loss
    # -----------------------------------
    if side == "buy_side":
        # bearish trade
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

Entry: {round(entry, 2)}
Stop Loss: {round(stop, 2)}
Take Profit (1.5R): {round(tp, 2)}

Risk: {round(risk, 2)}
RR: {rr}
"""

    return alert_message


# Model:
# Sweep → SMT → OB → {candidate.fvg_data["type"]}
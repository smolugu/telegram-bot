from datetime import datetime, timedelta, timezone

from framework.models.profit_targets import get_tp_levels

def build_trade_alert(candle_repo, contract_id, candidate, liquidity_map = None, daily_atr = None, current_time = None):

    if not candidate.fvg_confirmed and not candidate.sweep_and_ob_confirmed:
        return None
    time = None
    if candidate.ob_data is None:
        time = None
    else:
        time = candidate.ob_data["confirmation_timestamp"]
    if candidate.sweep_and_ob_confirmation_timestamp is not None:
        time = candidate.sweep_and_ob_confirmation_timestamp
    ts=None
    if isinstance(time, str):
        ts = datetime.fromisoformat(time)
    else:
        ts = time
    # dt = datetime.fromisoformat(time) + timedelta(minutes=30)
    dt = ts + timedelta(minutes=30)
    time_formatted = dt.strftime("%b %d, %Y %I:%M %p")
    dt2=None
    if isinstance(current_time, str):
        dt2 = datetime.fromisoformat(current_time)
    else:
        dt2 = current_time
    # dt2 = datetime.fromisoformat(current_time)
    time_formatted = dt2.strftime("%b %d, %Y %I:%M %p")
    default_risk = None

    instrument = candidate.instrument
    initial_target = candidate.initial_target_price
    final_target = candidate.final_target_price
    alert_message = ""
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
        # stop = sweep_candle_extreme
        sweep_timestamp_utc = candidate.sweep_timestamp.astimezone(timezone.utc)
        confirmation_timestamp_utc = candidate.confirmation_time.astimezone(timezone.utc)
        candles_between = candle_repo.get_between(
            contract=contract_id,
            timeframe=30,
            start=sweep_timestamp_utc,
            end=confirmation_timestamp_utc,
        )

        if candles_between:

            if side == "buy_side":
                stop = max(c.high for c in candles_between)
            else:
                stop = min(c.low for c in candles_between)

            print(
                "stop based on sweep -> OB extreme: ",
                stop,
            )

        else:
            stop = sweep_candle_extreme
            print(
                "no candles found between sweep and OB, "
                "using sweep candle extreme: ",
                stop,
            )
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
    
    # candidate.final_target_price is not None
    if side == "buy_side" and instrument == "ES":
        stop = stop + 4
    elif side == "sell_side" and instrument == "ES":
        stop = stop - 4
    
    if side == "buy_side" and instrument == "NQ":
        stop = stop + 10
    elif side == "sell_side" and instrument == "NQ":
        stop = stop - 10
    rr = 1
    if side == "buy_side" and candidate.sweep_and_ob_confirmed:
        print("alert Payload: initial target set 101")
        if candidate.sweep_and_ob_ce_confirmed:
            
            entry = candidate.sweep_and_ob_ce_entry
            print("alert Payload: initial target set 101-1")
            print("entry1 buyside: ", entry)
            rr = 2
            print("CE of Sweep and OB confirmed. Adjusting entry to:", entry)
        elif entry is None:
            if candidate.ob_data is not None:
                entry = candidate.ob_data["ob_low"]
                print("alert Payload: initial target set 101-2")
                print("entry2 buyside: ", entry)
            else:
                entry = candidate.sweep_and_ob_entry
                print("alert Payload: initial target set 101-3")
                print("entry3 buy side: ", entry)
            rr = 2
            print("sweep and OB confirmed. Adjusting entry to:", entry)
        
        risk = stop - entry
        if initial_target is not None:
            print("risk: ", risk)
            print("entry: ", entry)
            print("alert Payload: initial target set 101-4")
            print("initial_target: ", initial_target)
            rr_initial_target = abs(entry - initial_target) / risk
            rr_initial_target = round(rr_initial_target, 2)
            print("rr_in1: ", rr_initial_target)
        if (initial_target is not None and rr_initial_target < 1) or initial_target is None:
            tp1 = entry - (risk * rr)
            print("alert Payload: initial target set 101-5")
            print("tp1: ", tp1)
        else:
            rr = rr_initial_target
            print("alert Payload: initial target set 101-6")
            tp1 = initial_target
            print("tp1 based on initial target and rr_initial_targetxx: ", tp1, rr_initial_target)
            

    elif side == "buy_side" and entry < ce_confirmation_candle_price and risk > default_risk:
        entry = ce_confirmation_candle_price

        print("Adjusting entry to CE confirmation candle price:", entry)
        print("alert Payload: initial target set 102")
        rr = 1.5
        if initial_target is not None:
            print("risk: ", risk)
            print("entry: ", entry)
            print("alert Payload: initial target set 102-1")
            print("initial_target: ", initial_target)
            rr_initial_target = abs(entry - initial_target) / risk
            rr_initial_target = round(rr_initial_target, 2)
            print("rr_in2: ", rr_initial_target)
        if (initial_target is not None and rr_initial_target < 1) or initial_target is None:
            tp1 = entry - (risk * rr)
            print("alert Payload: initial target set 102-2")
            print("tp1 based on rr: ", tp1)
        else:
            rr = rr_initial_target
            tp1 = initial_target
            print("alert Payload: initial target set 102-3")
            print("tp1 based on initial target and rr_initial_target: ", tp1, rr_initial_target)

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
        print("alert Payload: initial target set 103")
        rr = 1.5
        risk = abs(entry - stop)
        if initial_target is not None:
            print("alert Payload: initial target set 103-1")
            print("risk: ", risk)
            print("entry: ", entry)
            print("initial_target: ", initial_target)
            rr_initial_target = abs(entry - initial_target) / risk
            rr_initial_target = round(rr_initial_target, 2)
            print("rr_in3: ", rr_initial_target)
        if (initial_target is not None and rr_initial_target < 1) or initial_target is None:
            tp1 = entry - (risk * rr)
            print("alert Payload: initial target set 103-2")
            print("Using original imbalance entry. TP adjusted to:", entry)
        else:
            rr = rr_initial_target
            tp1 = initial_target
            print("alert Payload: initial target set 103-3")
            print("tp1 based on initial target and rr_initial_target: ", tp1, rr_initial_target)
    
    # buy candidate
    elif side == "sell_side" and candidate.sweep_and_ob_confirmed:
        print("alert Payload: initial target set 104")
        if candidate.sweep_and_ob_ce_confirmed:
            entry = candidate.sweep_and_ob_ce_entry
            print("alert Payload: initial target set 104-1")
            print("entry1: ", entry)
            rr = 2
            print("CE of Sweep and OB confirmed. Adjusting entry to:", entry)
        elif entry is None:
            if candidate.ob_data is not None:
                entry = candidate.ob_data["ob_high"]
                print("entry2: ", entry)
                print("alert Payload: initial target set 104-2")
            else:
                entry = candidate.sweep_and_ob_entry
                print("entry3: ", entry)
                print("alert Payload: initial target set 104-3")
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
        if initial_target is not None:
            print("alert Payload: initial target set 104-4")
            rr_initial_target = abs(entry - initial_target) / risk
            rr_initial_target = round(rr_initial_target, 2)
        if (initial_target is not None and rr_initial_target < 1) or initial_target is None:
            tp1 = entry + (risk * rr)
            print("alert Payload: initial target set 104-5")
            print("tp1: ", tp1)
        else:
            rr = rr_initial_target
            tp1 = initial_target
            print("alert Payload: initial target set 104-6")
            print("tp1 based on initial target and rr_initial_target: ", tp1, rr_initial_target)
        
    elif side == "sell_side" and entry > ce_confirmation_candle_price and risk > default_risk:
        entry = ce_confirmation_candle_price
        print("alert Payload: initial target set 105")
        print("Adjusting entry to CE confirmation candle price:", entry)
        rr = 1.5
        if initial_target is not None:
            rr_initial_target = abs(entry - initial_target) / risk
            rr_initial_target = round(rr_initial_target, 2)
            print("alert Payload: initial target set 105-1")
        if (initial_target is not None and rr_initial_target < 1) or initial_target is None:
            tp1 = entry + (risk * rr)
            print("tp1 based on rr: ", tp1)
            print("alert Payload: initial target set 105-2")
        else:
            rr = rr_initial_target
            tp1 = initial_target
            print("alert Payload: initial target set 105-3")
            print("tp1 based on initial target and rr_initial_target: ", tp1, rr_initial_target)
    elif side == "sell_side":
        rr = 1.5
        risk = abs(entry - stop)
        print("alert Payload: initial target set 106")
        if initial_target is not None:
            print("alert Payload: initial target set 106-1")
            rr_initial_target = abs(entry - initial_target) / risk
            rr_initial_target = round(rr_initial_target, 2)
        if (initial_target is not None and rr_initial_target < 1) or initial_target is None:
            tp1 = entry + (risk * rr)
            print("alert Payload: initial target set 106-2")
            print("Using original imbalance entry. TP adjusted to:", entry)
        else:
            rr = rr_initial_target
            tp1 = initial_target
            print("alert Payload: initial target set 106-3")
            print("tp1 based on initial target and rr_initial_target: ", tp1, rr_initial_target)
        
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
    tp1, tp2, tp3 = get_tp_levels(entry, stop, direction, liquidity_map, daily_atr, tp1, instrument)

    print("tp levels from get_tp_levels: ", tp1, tp2, tp3)
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

    alert_type = "t1"
    if candidate.final_target == "ATR":
        print("alert_type: ", "t3")
        if instrument == "NQ":
            tp_spacing = 40.0
        elif instrument == "ES":
            tp_spacing = 10.0
        else:
            tp_spacing = 40.0
        alert_type = "t3"
        if final_target is not None:
            tp3 = final_target
        if side == "sell_side":
            if tp1 < tp2 < tp3:
                alert_type = "t3"
            elif tp1 < tp3 < tp2:
                alert_type = "t2"
                tp2 = tp3
            elif tp3 <= tp1:
                # alert_type = "t1"
                tp1 = tp3
                # TODO: change increments based on VIX
                tp2 = tp1 + tp_spacing
                tp3 = tp2 + tp_spacing

            elif tp3 <= tp2:
                alert_type = "t2"
                tp2 = tp3
                tp3 = None

            else:
                alert_type = "t3"
        
        if side == "buy_side":
            if tp1 > tp2 > tp3:
                alert_type = "t3"
            elif tp1 > tp3 > tp2:
                alert_type = "t2"
                tp2 = tp3
            elif tp3 >= tp1:
                # alert_type = "t1"
                # TODO: change increments based on VIX
                tp1 = tp3
                tp2 = tp1 - tp_spacing
                tp3 = tp2 - tp_spacing

            elif tp3 >= tp2:
                alert_type = "t2"
                tp2 = tp3
                tp3 = None

            else:
                alert_type = "t3"


        print("alert_type:", alert_type)
        
    elif candidate.final_target in ["DO", "MITL", "LIQUIDITY", "RL", "RH"]:
        alert_type = "t2"
        print("alert_type: ", "t2")
        print("tp1 xx: ", tp1, tp2, final_target)
        if final_target is not None and side == "buy_side":
            if tp1 < tp2 and tp1 < final_target:
                alert_type = "t1"
                print("alert_type sub2: ", "t1")
            elif tp1 > final_target > tp2:
                tp2 = final_target
                alert_type = "t2"
                print("alert_type sub2 100: ")
            elif tp1 > tp2 > final_target:
                # dont increse tp2 to final target
                alert_type = "t2"
                print("alert_type sub2 200: ")
            
        if final_target is not None and side == "sell_side":
            if tp1 > tp2 and tp1 > final_target:
                alert_type = "t1"
                print("alert_type sub2: ", "t1")
                print("alert_type sub2 300: ")
            elif tp1 < final_target < tp2:
                tp2 = final_target
                alert_type = "t2"
                print("alert_type sub2 400: ")
            elif tp1 < tp2 < final_target:
                # dont increse tp2 to final target
                alert_type = "t2"
                print("alert_type sub2 500: ")
                
    else:
        alert_type = "t1"
        print("alert_type sub2 600: ")
    
    zone = "Sell Zone"
    if side == "sell_side":
        zone = "Buy Zone"
    if side == "buy_side":
        zone_start = round(entry, 2)
        zone_end = round(stop, 2)
    else:
        zone_start = round(stop, 2)
        zone_end = round(entry, 2)

    # rr = 1.5
    # final_target = "MINI", "DO", "ATR", "MITL"
    if alert_type == "t3":
        rr_t3 = abs(entry - tp3) / risk
        rr_t3 = round(rr_t3, 2)
        alert_message = f"""
        ⚡️Ping Time - {candidate.ping_type}

        {instrument} • {bias}
        Time: {time_formatted} EST
        
        {zone}: {zone_start} - {zone_end}
        Sample Entry: {round(entry, 2)}
        Sample Stop: {round(stop, 2)}
        TP1 (1R): {round(tp1, 2)}
        TP2 (HTF Liquidity): {round(tp2, 2) if tp2 is not None else 'N/A'}
        TP3 (ATR): {round(tp3, 2)}
        
        Risk: {round(abs(entry-stop), 0)} pts
        Reward : Risk: {rr_t3} : 1
        """
        
        # alert_message = f"""
        # ⚡️Ping Time - {candidate.ping_type}

        # {instrument} • {bias}
        # {time_formatted} EST
        
        # {zone}
        # {round(entry, 2)} - {round(stop, 2)}
        
        # Sample Entry
        # {round(entry, 2)}
        
        # Sample Stop
        # {round(stop, 2)}
        
        # Take Profit 1
        # {round(tp1, 2)}
        
        # Take Profit 2
        # HTF Liquidity: {round(tp2, 2) if tp2 is not None else 'N/A'}
        
        # Take Profit 3
        # ATR: {round(tp3, 2)}

        # Risk
        # {round(abs(entry-stop), 0)} Pts
        
        # Reward : Risk
        # {rr_t3} : 1
        # """
    
    elif alert_type == "t2":
        rr_t2 = abs(entry - tp2) / risk
        rr_t2 = round(rr_t2, 2)

        alert_message = f"""
        ⚡️Ping Time - {candidate.ping_type}

        {instrument} • {bias}
        Time: {time_formatted} EST

        {zone}: {zone_start} - {zone_end}
        Sample Entry: {round(entry, 2)}
        Sample Stop: {round(stop, 2)}
        TP1 (1R): {round(tp1, 2)}
        TP2 (HTF Liquidity): {round(tp2, 2) if tp2 is not None else 'N/A'}
        
        Risk: {round(abs(entry-stop), 0)} pts
        Reward : Risk: {rr_t2} : 1
        """
        # alert_message = f"""
        # ⚡️Ping Time - {candidate.ping_type}

        # {instrument} • {bias}
        # {time_formatted} EST
        
        # {zone}
        # {round(entry, 2)} - {round(stop, 2)}
        
        # Sample Entry
        # {round(entry, 2)}
        
        # Sample Stop
        # {round(stop, 2)}
        
        # Take Profit 1
        # {round(tp1, 2)}
        
        # Take Profit 2
        # HTF Liquidity: {round(tp2, 2) if tp2 is not None else 'N/A'}
        
        # Risk
        # {round(abs(entry-stop), 0)} Pts
        
        # Reward : Risk
        # {rr_t2} : 1
        # """

    elif alert_type == "t1":
        rr_t1 = abs(entry - tp1) / risk
        rr_t1 = round(rr_t1, 2)
        alert_message = f"""
        ⚡️Ping Time - {candidate.ping_type}

        {instrument} • {bias}
        Time: {time_formatted} EST

        {zone}: {zone_start} - {zone_end}
        Sample Entry: {round(entry, 2)}
        Sample Stop: {round(stop, 2)}
        TP (1R): {round(tp1, 2)}
        
        Risk: {round(abs(entry-stop), 0)} pts
        Reward : Risk: {rr_t1} : 1
        """
        
        # alert_message = f"""
        # ⚡️Ping Time - {candidate.ping_type}

        # {instrument} • {bias}
        # {time_formatted} EST
        
        # {zone}
        # {round(entry, 2)} - {round(stop, 2)}
        
        # Sample Entry
        # {round(entry, 2)}
        
        # Sample Stop
        # {round(stop, 2)}
        
        # Take Profit
        # {round(tp1, 2)}
        
        # Risk
        # {round(abs(entry-stop), 0)} Pts
        
        # Reward : Risk
        # {rr_t1} : 1
        # """
    return alert_message



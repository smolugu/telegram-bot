from datetime import datetime, timedelta

from data.models.profit_targets import get_tp_levels


AUCTION_PRIORITY = {
    "waiting": 0,
    "compression": 0,
    "mid expansion": 1,
    "migration": 1,
    "early expansion": 2,
    "early_expansion": 2,
}


def build_summary_alert(
    nq_market_context,
    es_market_context,
    current_time
):

    lines = []
    # dt = datetime.fromisoformat(current_time) + timedelta(minutes=30)
    dt = datetime.fromisoformat(current_time)
    time_formatted = dt.strftime("%b %d, %Y %I:%M %p")

    lines.append("⚡️ Ping NY AM Summary")
    lines.append(f"  {time_formatted} EST\n")

    #
    # NQ
    #
    lines.append("🔹 NQ")
    lines.append(f"Market: {nq_market_context.structure["context_summary"]['market_state']}")
    lines.append(f"Expectation: {nq_market_context.structure["context_summary"]['expected_delivery']}")
    lines.append("")

    #
    # ES
    #
    lines.append("🔹 ES")
    lines.append(f"Market: {es_market_context.structure["context_summary"]["market_state"]}")
    lines.append(f"Expectation: {es_market_context.structure["context_summary"]["expected_delivery"]}")
    lines.append("")

    #
    # Preferred asset
    #
    nq_auction_phase = nq_market_context.structure["auction_phase"]
    es_auction_phase = es_market_context.structure["auction_phase"]
    nq_pqs = nq_market_context.structure["pqs"]
    es_pqs = es_market_context.structure["pqs"]
    nq_priority = AUCTION_PRIORITY.get(nq_auction_phase, 0)
    es_priority = AUCTION_PRIORITY.get(es_auction_phase, 0)

    if nq_priority > es_priority:
        preferred_asset = "NQ"
        reason = (
            f"NQ is in an earlier auction stage "
            f"({nq_auction_phase}) compared with ES ({es_auction_phase}), "
            "providing greater delivery potential."
        )

    elif es_priority > nq_priority:
        preferred_asset = "ES"
        reason = (
            f"ES is in an earlier auction stage "
            f"({es_auction_phase}) compared with NQ ({nq_auction_phase}), "
            "providing greater delivery potential."
        )

    else:

        if nq_pqs > es_pqs:
            preferred_asset = "NQ"
            reason = (
                f"Both markets are in the {nq_auction_phase} phase. "
                f"NQ has the stronger overnight structure "
                f"(PQS {nq_pqs} vs {es_pqs})."
            )

        elif es_pqs > nq_pqs:
            preferred_asset = "ES"
            reason = (
                f"Both markets are in the {es_auction_phase} phase. "
                f"ES has the stronger overnight structure "
                f"(PQS {es_pqs} vs {nq_pqs})."
            )

        else:
            preferred_asset = "Either"
            reason = (
                f"Both markets are in the {nq_auction_phase} phase "
                "with similar structure quality."
            )

    lines.append("🎯 Preferred Asset")
    lines.append(f"{preferred_asset}")
    lines.append(reason)

    return "\n".join(lines)

def build_trade_alert(candidate, liquidity_map = None, daily_atr = None, current_time = None):

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

    dt2 = datetime.fromisoformat(current_time)
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
        elif entry is None:
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
        if initial_target is not None:
            print("risk: ", risk)
            print("entry: ", entry)
            print("initial_target: ", initial_target)
            rr_initial_target = abs(entry - initial_target) / risk
            rr_initial_target = round(rr_initial_target, 2)
            print("rr_in1: ", rr_initial_target)
        if (initial_target is not None and rr_initial_target < 1) or initial_target is None:
            tp1 = entry - (risk * rr)
            print("tp1: ", tp1)
        else:
            rr = rr_initial_target
            tp1 = initial_target
            print("tp1 based on initial target and rr_initial_targetxx: ", tp1, rr_initial_target)
            

    elif side == "buy_side" and entry < ce_confirmation_candle_price and risk > default_risk:
        entry = ce_confirmation_candle_price
        print("Adjusting entry to CE confirmation candle price:", entry)
        rr = 1.5
        if initial_target is not None:
            print("risk: ", risk)
            print("entry: ", entry)
            print("initial_target: ", initial_target)
            rr_initial_target = abs(entry - initial_target) / risk
            rr_initial_target = round(rr_initial_target, 2)
            print("rr_in2: ", rr_initial_target)
        if (initial_target is not None and rr_initial_target < 1) or initial_target is None:
            tp1 = entry - (risk * rr)
            print("tp1 based on rr: ", tp1)
        else:
            rr = rr_initial_target
            tp1 = initial_target
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
        rr = 1.5
        risk = abs(entry - stop)
        if initial_target is not None:
            print("risk: ", risk)
            print("entry: ", entry)
            print("initial_target: ", initial_target)
            rr_initial_target = abs(entry - initial_target) / risk
            rr_initial_target = round(rr_initial_target, 2)
            print("rr_in3: ", rr_initial_target)
        if (initial_target is not None and rr_initial_target < 1) or initial_target is None:
            tp1 = entry - (risk * rr)
            print("Using original imbalance entry. TP adjusted to:", entry)
        else:
            rr = rr_initial_target
            tp1 = initial_target
            print("tp1 based on initial target and rr_initial_target: ", tp1, rr_initial_target)
    
    # buy candidate
    elif side == "sell_side" and candidate.sweep_and_ob_confirmed:
        if candidate.sweep_and_ob_ce_confirmed:
            entry = candidate.sweep_and_ob_ce_entry
            print("entry1: ", entry)
            rr = 2
            print("CE of Sweep and OB confirmed. Adjusting entry to:", entry)
        elif entry is None:
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
        if initial_target is not None:
            rr_initial_target = abs(entry - initial_target) / risk
            rr_initial_target = round(rr_initial_target, 2)
        if (initial_target is not None and rr_initial_target < 1) or initial_target is None:
            tp1 = entry + (risk * rr)
            print("tp1: ", tp1)
        else:
            rr = rr_initial_target
            tp1 = initial_target
            print("tp1 based on initial target and rr_initial_target: ", tp1, rr_initial_target)
        
    elif side == "sell_side" and entry > ce_confirmation_candle_price and risk > default_risk:
        entry = ce_confirmation_candle_price
        print("Adjusting entry to CE confirmation candle price:", entry)
        rr = 1.5
        if initial_target is not None:
            rr_initial_target = abs(entry - initial_target) / risk
            rr_initial_target = round(rr_initial_target, 2)
        if (initial_target is not None and rr_initial_target < 1) or initial_target is None:
            tp1 = entry + (risk * rr)
            print("tp1 based on rr: ", tp1)
        else:
            rr = rr_initial_target
            tp1 = initial_target
            print("tp1 based on initial target and rr_initial_target: ", tp1, rr_initial_target)
    elif side == "sell_side":
        rr = 1.5
        risk = abs(entry - stop)
        if initial_target is not None:
            rr_initial_target = abs(entry - initial_target) / risk
            rr_initial_target = round(rr_initial_target, 2)
        if (initial_target is not None and rr_initial_target < 1) or initial_target is None:
            tp1 = entry + (risk * rr)
            print("Using original imbalance entry. TP adjusted to:", entry)
        else:
            rr = rr_initial_target
            tp1 = initial_target
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
    tp1, tp2, tp3 = get_tp_levels(entry, stop, direction, liquidity_map, daily_atr, tp1)

    # candidate.final_target_price is not None
    if side == "buy_side" and instrument == "ES":
        stop = stop + 0.50
    elif side == "sell_side" and instrument == "ES":
        stop = stop - 0.05
    
    if side == "buy_side" and instrument == "NQ":
        stop = stop + 2
    elif side == "sell_side" and instrument == "NQ":
        stop = stop - 2


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
                tp2 = tp1 + 40.0
                tp3 = tp2 + 40.0

            elif tp3 <= tp2:
                alert_type = "t2"
                tp2 = tp3
                tp3 = None

            else:
                alert_type = "t3"
        
        if side == "buy_side":
            if tp1 > tp2 >= tp3:
                alert_type = "t3"
            elif tp1 > tp3 > tp2:
                alert_type = "t2"
                tp2 = tp3
            elif tp3 >= tp1:
                # alert_type = "t1"
                # TODO: change increments based on VIX
                tp1 = tp3
                tp2 = tp1 - 40.0
                tp3 = tp2 - 40.0

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
            elif tp1 > tp2 > final_target:
                # dont increse tp2 to final target
                alert_type = "t2"
            
        if final_target is not None and side == "sell_side":
            if tp1 > tp2 and tp1 > final_target:
                alert_type = "t1"
                print("alert_type sub2: ", "t1")
            elif tp1 < final_target < tp2:
                tp2 = final_target
                alert_type = "t2"
            elif tp1 < tp2 < final_target:
                # dont increse tp2 to final target
                alert_type = "t2"
                
    else:
        alert_type = "t1"
    
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


# Model:
# Sweep → SMT → OB → {candidate.fvg_data["type"]}
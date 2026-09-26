from datetime import datetime

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
    # dt = datetime.fromisoformat(current_time)
    dt=None
    if isinstance(current_time, str):
        dt = datetime.fromisoformat(current_time)
    else:
        dt = current_time
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
    nq_priority = AUCTION_PRIORITY.get(nq_auction_phase.value, 0)
    es_priority = AUCTION_PRIORITY.get(es_auction_phase.value, 0)

    if nq_priority > es_priority:
        preferred_asset = "NQ"
        reason = (
            f"NQ is in an earlier auction stage "
            f"({nq_auction_phase.value}) compared with ES ({es_auction_phase.value}), "
            "providing greater delivery potential."
        )

    elif es_priority > nq_priority:
        preferred_asset = "ES"
        reason = (
            f"ES is in an earlier auction stage "
            f"({es_auction_phase.value}) compared with NQ ({nq_auction_phase.value}), "
            "providing greater delivery potential."
        )

    else:

        if nq_pqs > es_pqs:
            preferred_asset = "NQ"
            reason = (
                f"Both markets are in the {nq_auction_phase.value} phase. "
                f"NQ has the stronger overnight structure "
                f"(PQS {nq_pqs} vs {es_pqs})."
            )

        elif es_pqs > nq_pqs:
            preferred_asset = "ES"
            reason = (
                f"Both markets are in the {es_auction_phase.value} phase. "
                f"ES has the stronger overnight structure "
                f"(PQS {es_pqs} vs {nq_pqs})."
            )

        else:
            preferred_asset = "Either"
            reason = (
                f"Both markets are in the {nq_auction_phase.value} phase "
                "with similar structure quality."
            )

    lines.append("🎯 Preferred Asset")
    lines.append(f"{preferred_asset}")
    lines.append(reason)

    return "\n".join(lines)
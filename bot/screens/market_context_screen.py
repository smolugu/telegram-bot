def market_context_screen(runtime_data):
    message = (
        "ℹ️ <b>Market Context</b>\n\n"
        f"<b>NQ: {runtime_data.nq_ny_market_context.structure["name"]}</b>\n"
        f"Daily ATR: {runtime_data.nq_market_context.daily_atr:.0f}\n"
        f"Daily ATR used: {runtime_data.nq_market_context.atr_usage:.2f}\n\n"
        "Market data will be connected next.\n\n"
        f"<b>ES: {runtime_data.es_ny_market_context.structure["name"]}</b>\n"
        f"Daily ATR: {runtime_data.es_market_context.daily_atr:.0f}\n"
        f"Daily ATR used: {runtime_data.es_market_context.atr_usage:.2f}\n\n"
        "Market data will be connected next."
    )

    return message
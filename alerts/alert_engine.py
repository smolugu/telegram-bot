from state.state_cache import should_alert


def handle_stage(result: dict, bot):

    stage = result["stage"]

    if stage == "NONE":
        return

    key = f"{stage}_{result.get('smt', {}).get('trade_symbol')}"

    if not should_alert(key):
        return

    message = build_message(result)

    send_alert(bot, message)


def build_message(result):

    if result["stage"] == "HEADS_UP":
        return "⚠ Sweep + SMT detected."

    if result["stage"] == "CONFIRMED":
        return "✅ OB Confirmed. Waiting for imbalance."

    if result["stage"] == "EXECUTION":
        ex = result["execution"]
        return (
            f"🚀 TRADE READY\n"
            f"Symbol: {result['smt']['trade_symbol']}\n"
            f"Direction: {ex['direction']}\n"
            f"Entry: {ex['entry']}\n"
            f"Stop: {ex['stop']}\n"
            f"Target: {ex['target']}"
        )


def send_alert(bot, message):
    # integrate with your Telegram broadcast logic
    bot.broadcast(message)

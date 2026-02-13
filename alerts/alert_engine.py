from state.state_cache import should_alert, update_active_window
from utils.time_utils import today_string

def handle_stage(result: dict, bot):

    if result["stage"] == "NONE":
        return

    window_name = result.get("smt", {}).get("window") \
        or result.get("sweep", {}).get("NQ", {}).get("window")

    window_key = f"{window_name}_{today_string()}"

    update_active_window(window_key)

    stage_key = f"{result['stage']}_{result.get('smt', {}).get('trade_symbol')}"

    if not should_alert(stage_key):
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

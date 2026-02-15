from state.state_cache import update_active_window, should_alert
from bot.broadcast import broadcast_message
from utils.time_utils import today_string


async def handle_stage(result, application):

    if result["stage"] == "NONE":
        return

    window_name = (
        result.get("smt", {}).get("window")
        or result.get("sweep", {}).get("NQ", {}).get("window")
        or "unknown"
    )

    window_key = f"{window_name}_{today_string()}"

    update_active_window(window_key)

    stage_key = f"{result['stage']}_{result.get('smt', {}).get('trade_symbol')}"

    if not should_alert(stage_key):
        return

    message = build_message(result)

    await broadcast_message(application, message)


def build_message(result):

    if result["stage"] == "HEADS_UP":
        return "⚠ Sweep + SMT detected."

    if result["stage"] == "CONFIRMED":
        return "✅ OB confirmed. Waiting for imbalance."

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

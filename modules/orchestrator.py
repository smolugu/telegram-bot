from daily_bias import get_daily_bias
from sweep_detector import detect_7h_wick_sweep
from ob_detector import detect_30m_order_block
from imbalance_detector import detect_3m_fvg
from execution_model import build_execution_plan


def evaluate_7h_setup(
    market_data: dict,
    seven_hour_open_ts: str
) -> dict:
    """
    Orchestrates the full setup evaluation pipeline:
    Daily Bias → Sweep → OB → Imbalance → Execution
    """

    # -------------------------
    # 1️⃣ Daily Bias
    # -------------------------
    daily_bias = get_daily_bias(
        daily_candles=market_data["daily"],
        current_price=market_data["current_price"]
    )

    if daily_bias["bias"] == "NEUTRAL":
        return _result("NONE", daily_bias=daily_bias)

    # -------------------------
    # 2️⃣ Sweep Detection (7H wick aware)
    # -------------------------
    sweep = detect_7h_wick_sweep(
        candles_30m=market_data["30m"],
        seven_hour_open_ts=seven_hour_open_ts
    )

    if not sweep["sweep_detected"]:
        return _result("NONE", daily_bias=daily_bias)

    # -------------------------
    # 3️⃣ 30m Order Block
    # -------------------------
    ob = detect_30m_order_block(
        candles_30m=market_data["30m"],
        sweep_info=sweep
    )

    if not ob["ob_found"]:
        return _result(
            "HEADS_UP",
            daily_bias=daily_bias,
            sweep=sweep
        )

    # -------------------------
    # 4️⃣ 3m Imbalance (FVG)
    # -------------------------
    imbalance = detect_3m_fvg(
        candles_3m=market_data["3m"],
        ob_high=ob["high"],
        ob_low=ob["low"],
        sweep_ts=sweep["timestamp"],
        direction=ob["direction"]
    )

    if not imbalance["imbalance_found"]:
        return _result(
            "CONFIRMED",
            daily_bias=daily_bias,
            sweep=sweep,
            order_block=ob
        )

    # -------------------------
    # 5️⃣ Execution Model
    # -------------------------
    execution = build_execution_plan(
        imbalance=imbalance,
        protected_high=market_data["protected_high"],
        protected_low=market_data["protected_low"],
        direction=ob["direction"]
    )

    if not execution["execution_ready"]:
        return _result(
            "CONFIRMED",
            daily_bias=daily_bias,
            sweep=sweep,
            order_block=ob,
            imbalance=imbalance
        )

    return _result(
        "EXECUTION",
        daily_bias=daily_bias,
        sweep=sweep,
        order_block=ob,
        imbalance=imbalance,
        execution=execution
    )


def _result(stage: str, **kwargs) -> dict:
    return {
        "stage": stage,
        "daily_bias": kwargs.get("daily_bias"),
        "sweep": kwargs.get("sweep"),
        "order_block": kwargs.get("order_block"),
        "imbalance": kwargs.get("imbalance"),
        "execution": kwargs.get("execution")
    }

from daily_bias import get_daily_bias
from sweep_detector import detect_dual_sweep
from smt_detector import detect_smt_dual
from ob_detector import detect_30m_order_block
from imbalance_detector import detect_3m_fvg
from execution_model import build_execution_plan


def evaluate_7h_setup(
    market_data: dict,
    seven_hour_open_ts: str
) -> dict:

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
    # 2️⃣ Dual Sweep Detection
    # -------------------------
    sweep = detect_dual_sweep(
        nq_30m=market_data["NQ"]["30m"],
        es_30m=market_data["ES"]["30m"],
        seven_hour_open_ts=seven_hour_open_ts
    )

    if not sweep["sweep_exists"]:
        return _result("NONE", daily_bias=daily_bias)

    # -------------------------
    # 3️⃣ SMT (Mandatory)
    # -------------------------
    smt = detect_smt_dual(
        nq_30m=market_data["NQ"]["30m"],
        es_30m=market_data["ES"]["30m"],
        nq_1h=market_data["NQ"]["1h"],
        es_1h=market_data["ES"]["1h"],
        seven_hour_open_ts=seven_hour_open_ts
    )

    if not smt["smt_confirmed"]:
        return _result(
            "NONE",
            daily_bias=daily_bias,
            sweep=sweep
        )

    trade_symbol = smt["trade_symbol"]
    trade_direction = smt["trade_direction"]

    # -------------------------
    # 4️⃣ Order Block (Chosen Symbol)
    # -------------------------
    ob = detect_30m_order_block(
        candles_30m=market_data[trade_symbol]["30m"],
        sweep_info=sweep[trade_symbol]
    )

    if not ob["ob_found"]:
        return _result(
            "HEADS_UP",
            daily_bias=daily_bias,
            sweep=sweep,
            smt=smt
        )

    # -------------------------
    # 5️⃣ 3m Imbalance
    # -------------------------
    imbalance = detect_3m_fvg(
        candles_3m=market_data[trade_symbol]["3m"],
        ob_high=ob["high"],
        ob_low=ob["low"],
        sweep_ts=sweep[trade_symbol]["timestamp"],
        direction=trade_direction
    )

    if not imbalance["imbalance_found"]:
        return _result(
            "CONFIRMED",
            daily_bias=daily_bias,
            sweep=sweep,
            smt=smt,
            order_block=ob
        )

    # -------------------------
    # 6️⃣ Execution Plan
    # -------------------------
    execution = build_execution_plan(
        imbalance=imbalance,
        protected_high=market_data[trade_symbol]["protected_high"],
        protected_low=market_data[trade_symbol]["protected_low"],
        direction=trade_direction
    )

    if not execution["execution_ready"]:
        return _result(
            "CONFIRMED",
            daily_bias=daily_bias,
            sweep=sweep,
            smt=smt,
            order_block=ob,
            imbalance=imbalance
        )

    return _result(
        "EXECUTION",
        daily_bias=daily_bias,
        sweep=sweep,
        smt=smt,
        order_block=ob,
        imbalance=imbalance,
        execution=execution
    )


def _result(stage: str, **kwargs) -> dict:
    return {
        "stage": stage,
        "daily_bias": kwargs.get("daily_bias"),
        "sweep": kwargs.get("sweep"),
        "smt": kwargs.get("smt"),
        "order_block": kwargs.get("order_block"),
        "imbalance": kwargs.get("imbalance"),
        "execution": kwargs.get("execution")
    }

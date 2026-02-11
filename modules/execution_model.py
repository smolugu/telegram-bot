def build_execution_plan(
    imbalance: dict,
    protected_high: float,
    protected_low: float,
    direction: str,   # "SHORT" or "LONG"
    rr: float = 2.0
) -> dict:
    """
    Builds execution plan from imbalance.

    ENTRY:
    - Taken directly from imbalance['entry']

    STOP:
    - SHORT → protected high
    - LONG  → protected low

    TARGET:
    - Fixed R multiple (default = 2R)
    """

    if not imbalance.get("imbalance_found"):
        return _no_execution("no_imbalance")

    entry = imbalance["entry"]

    # --- Stop logic ---
    if direction == "SHORT":
        stop = protected_high
        risk = stop - entry
    else:
        stop = protected_low
        risk = entry - stop

    if risk <= 0:
        return _no_execution("invalid_risk")

    # --- Target logic ---
    target = (
        entry - rr * risk
        if direction == "SHORT"
        else entry + rr * risk
    )

    return {
        "execution_ready": True,
        "direction": direction,
        "entry": entry,
        "stop": stop,
        "target": target,
        "rr": rr,
        "risk": risk
    }


def _no_execution(reason: str):
    return {
        "execution_ready": False,
        "reason": reason,
        "entry": None,
        "stop": None,
        "target": None,
        "rr": None,
        "risk": None
    }

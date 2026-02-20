

from datetime import datetime


def detect_3m_fvg(
    candles_3m: list[dict],
    ob_high: float,
    ob_low: float,
    sweep_ts: str,
    direction: str  # "SHORT" or "LONG"
) -> dict:
    """
    Detect ALL 3m FVGs after sweep, inside OB.
    Select the FVG whose ENTRY (first-tap boundary) is closest to OB boundary.

    ENTRY RULE (LOCKED):
    - SHORT → entry = fvg_low  (c3["high"])
    - LONG  → entry = fvg_high (c3["low"])

    Midpoint is optional metadata.
    """

    sweep_time = datetime.fromisoformat(sweep_ts)

    post_sweep = [
        c for c in candles_3m
        if datetime.fromisoformat(c["timestamp"]) >= sweep_time
    ]

    if len(post_sweep) < 3:
        return _no_imbalance()

    candidates = []

    for i in range(len(post_sweep) - 2):
        c1 = post_sweep[i]
        c3 = post_sweep[i + 2]

        # --- Bearish FVG ---
        if direction == "SHORT" and c1["low"] > c3["high"]:
            fvg_high = c1["low"]
            fvg_low = c3["high"]

            if _inside_ob(fvg_high, fvg_low, ob_high, ob_low):
                entry = fvg_low  # FIRST TAP on retrace (LOCKED)
                distance = abs(ob_low - entry)  # closeness to OB low on retrace
                candidates.append(
                    _fvg_obj(
                        direction="SHORT",
                        entry=entry,
                        fvg_high=fvg_high,
                        fvg_low=fvg_low,
                        midpoint=(fvg_high + fvg_low) / 2,
                        distance=distance
                    )
                )

        # --- Bullish FVG ---
        if direction == "LONG" and c1["high"] < c3["low"]:
            fvg_low = c1["high"]
            fvg_high = c3["low"]

            if _inside_ob(fvg_high, fvg_low, ob_high, ob_low):
                entry = fvg_high  # FIRST TAP on retrace (LOCKED)
                distance = abs(entry - ob_high)  # closeness to OB high on retrace
                candidates.append(
                    _fvg_obj(
                        direction="LONG",
                        entry=entry,
                        fvg_high=fvg_high,
                        fvg_low=fvg_low,
                        midpoint=(fvg_high + fvg_low) / 2,
                        distance=distance
                    )
                )

    if not candidates:
        return _no_imbalance()

    # Choose the FVG whose ENTRY is closest to the OB retrace boundary
    selected = min(candidates, key=lambda x: x["distance"])
    return selected


def _inside_ob(fvg_high, fvg_low, ob_high, ob_low) -> bool:
    return fvg_high <= ob_high and fvg_low >= ob_low


def _fvg_obj(direction, entry, fvg_high, fvg_low, midpoint, distance):
    return {
        "imbalance_found": True,
        "type": "FVG",
        "direction": direction,
        "entry": entry,          # 🔴 ACTUAL LIMIT ENTRY (LOCKED)
        "fvg_high": fvg_high,
        "fvg_low": fvg_low,
        "midpoint": midpoint,    # optional metadata
        "distance": distance
    }


def _no_imbalance():
    return {
        "imbalance_found": False,
        "type": None,
        "direction": None,
        "entry": None,
        "fvg_high": None,
        "fvg_low": None,
        "midpoint": None,
        "distance": None
    }

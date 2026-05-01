# def detect_compression(ib_18, ib_1, ib_8):
def detect_compression(seven_hour_builder_candles):
    """
    ib_x = {"high": ..., "low": ...}
    """

    def overlap(a, b):
        return not (a["ib_high"] < b["ib_low"] or b["ib_high"] < a["ib_low"])

    def inside(inner, outer):
        return inner["ib_high"] <= outer["ib_high"] and inner["ib_low"] >= outer["ib_low"]

    def engulfing(engulfing, engulfed):
        return engulfing["ib_high"] > engulfed["ib_high"] and engulfing["ib_low"] < engulfed["ib_low"]


    def sandwich(ib_18, ib_1, ib_8):
    # Step 1: ensure one is fully above the other
        ib18_above_ib1 = (
            ib_18["low"] > ib_1["low"] and
            ib_18["high"] > ib_1["high"]
        )

        ib18_below_ib1 = (
            ib_18["low"] < ib_1["low"] and
            ib_18["high"] < ib_1["high"]
        )

        if not (ib18_above_ib1 or ib18_below_ib1):
            return False

        # Step 2: IB_8 inside combined outer range
        lower_bound = min(ib_18["low"], ib_1["low"])
        upper_bound = max(ib_18["high"], ib_1["high"])

        return (
            ib_8["low"] > lower_bound and
            ib_8["high"] < upper_bound
        )
        
    compression_flags = {
        "nested_1_in_18": False,
        "engulfing_1_over_18": False,
        "overlap_1_18": False,
        "overlap_8_1": False,
        "nested_8_between_18_1": False,
        "multi_ib_compression": False
    }

    ib_18 = seven_hour_builder_candles["6PM"].values()
    ib_1 = seven_hour_builder_candles["1AM"].values()
    ib_8 = seven_hour_builder_candles["8AM"].values()
    # print("ib_1: ", ib_1)
    # print("ib_18: ", ib_18)
    compression_range = {"high": None, "low": None}

    if not ib_1["ib_ready"]:
        return False, compression_flags, compression_range  # Cannot determine compression without 1AM IB
    # -------------------------
    # 1AM vs 18:00
    # -------------------------
    if inside(ib_1, ib_18):
        compression_flags["nested_1_in_18"] = True
        compression_range = {"high": ib_18["ib_high"], "low": ib_18["ib_low"]}

    if overlap(ib_1, ib_18):
        compression_flags["overlap_1_18"] = True
        compression_range = {
            "high": max(ib_1["ib_high"], ib_18["ib_high"]),
            "low": min(ib_1["ib_low"], ib_18["ib_low"])
        }

    if engulfing(ib_1, ib_18):
        compression_flags["engulfing_1_over_18"] = True
        compression_range = {
            "high": ib_1["ib_high"],
            "low": ib_1["ib_low"]
        }
    # -------------------------
    # 8AM vs 1AM (optional)
    # -------------------------
    if ib_8["ib_ready"]:
        if overlap(ib_8, ib_1):
            compression_flags["overlap_8_1"] = True
            compression_range = {
                "high": max(ib_8["ib_high"], ib_1["ib_high"]),
                "low": min(ib_8["ib_low"], ib_1["ib_low"])
            }
        if sandwich(ib_18, ib_1, ib_8):
            compression_flags["nested_8_between_18_1"] = True
            compression_range = {
                "high": max(ib_18["ib_high"], ib_1["ib_high"], ib_8["ib_high"]),
                "low": min(ib_18["ib_low"], ib_1["ib_low"], ib_8["ib_low"])
            }

    # -------------------------
    # Multi compression
    # -------------------------
    if (
        compression_flags["overlap_1_18"]
        and compression_flags.get("overlap_8_1", False)
    ):
        compression_flags["multi_ib_compression"] = True

    # -------------------------
    # Final decision
    # -------------------------
    is_compression = any(compression_flags.values())

    return is_compression, compression_flags, compression_range
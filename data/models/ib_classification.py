def classify_ib_structure(
    ib18,
    ib1,
    ib8,
    overlap_threshold=0.10
):
    """
    =====================================================
    IB STRUCTURE CLASSIFIER
    =====================================================

    INPUT
    -----
    ib18, ib1, ib8:

    {
        "high": float,
        "low": float
    }

    overlap_threshold:
        % overlap threshold relative to smaller IB range

    RETURNS
    -------
    {
        "structure": str,
        "category": str,
        "direction": str,
        "note": str
    }

    =====================================================
    SUPPORTED STRUCTURES
    =====================================================

    TREND ACCEPTANCE
    ----------------
    staircase_gap_bullish
    staircase_gap_bearish
    staircase_overlap_bullish
    staircase_overlap_bearish

    RECOMPRESSION
    -------------
    bullish_recompression
    bearish_recompression

    REBALANCE
    ---------
    bullish_rebalance
    bearish_rebalance

    FAILED EXPANSION
    ----------------
    failed_bullish_expansion
    failed_bearish_expansion

    SANDWICH
    --------
    sandwich_gap_bullish
    sandwich_gap_bearish
    sandwich_overlap_bullish
    sandwich_overlap_bearish

    ENGULFING
    ---------
    ib1_engulf_ib18
    ib8_engulf_ib1
    ib8_engulf_ib18

    COMPRESSION
    -----------
    centered_compression
    dual_inside_compression

    DEFAULT
    -------
    mixed_overlap
    """

    # =====================================================
    # HELPERS
    # =====================================================

    def ib_range(ib):
        return ib["high"] - ib["low"]

    def overlaps(a, b):

        overlap = (
            min(a["high"], b["high"])
            - max(a["low"], b["low"])
        )

        if overlap <= 0:
            return False

        smaller = min(
            ib_range(a),
            ib_range(b)
        )

        return (
            overlap / smaller
        ) > overlap_threshold

    def a_inside_b(a, b):

        return (
            a["high"] <= b["high"]
            and a["low"] >= b["low"]
        )

    def a_engulfs_b(a, b):

        return (
            a["high"] > b["high"]
            and a["low"] < b["low"]
        )

    def a_above_b(a, b):

        return a["low"] > b["high"]

    def a_below_b(a, b):

        return a["high"] < b["low"]

    # =====================================================
    # BASIC RELATIONSHIPS
    # =====================================================

    ib1_inside_ib18 = a_inside_b(ib1, ib18)
    ib8_inside_ib1 = a_inside_b(ib8, ib1)
    ib8_inside_ib18 = a_inside_b(ib8, ib18)

    ib1_engulf_ib18 = a_engulfs_b(ib1, ib18)
    ib8_engulf_ib1 = a_engulfs_b(ib8, ib1)
    ib8_engulf_ib18 = a_engulfs_b(ib8, ib18)

    ib1_above_ib18 = a_above_b(ib1, ib18)
    ib1_below_ib18 = a_below_b(ib1, ib18)

    ib8_above_ib1 = a_above_b(ib8, ib1)
    ib8_below_ib1 = a_below_b(ib8, ib1)

    ib1_overlap_ib18 = overlaps(ib1, ib18)
    ib8_overlap_ib1 = overlaps(ib8, ib1)
    ib8_overlap_ib18 = overlaps(ib8, ib18)

    # =====================================================
    # ENGULFING (highest priority)
    # One Line Rule:
       # Decompression outside value suggests continuation — decompression through value suggests conflict
    # =====================================================
    # DECOMPRESSION SET 1
    # =====================================================
    # BULLISH DECOMPRESSION
    # =====================================================

    if (
        ib8_engulf_ib1
        and ib1_above_ib18
        and ib8["low"] > ib18["high"]
    ):

        return {
            "structure": "bullish_decompression",
            "category": "decompression",
            "direction": "bullish",

            "note_internal":
                "8AM IB engulfed 1AM IB above 18 IB. "
                "Bullish volatility expansion above prior value.",

            "note":
                "Bullish decompression before NY open. "
                "Higher pricing accepted."
        }
    # =====================================================
    # BEARISH DECOMPRESSION
    # =====================================================

    if (
        ib8_engulf_ib1
        and ib1_below_ib18
        and ib8["high"] < ib18["low"]
    ):

        return {
            "structure": "bearish_decompression",
            "category": "decompression",
            "direction": "bearish",

            "note_internal":
                "8AM IB engulfed 1AM IB below 18 IB. "
                "Bearish volatility expansion below prior value.",

            "note":
                "Bearish decompression before NY open. "
                "Lower pricing accepted."
        }
    # =====================================================
    # MIXED DECOMPRESSION
    # =====================================================

    if ib8_engulf_ib1:

        return {
            "structure": "mixed_decompression",
            "category": "decompression",
            "direction": "neutral",

            "note_internal":
                "8AM IB engulfed 1AM IB overlapping prior value. "
                "Continuation vs reversal unresolved.",

            "note":
                "Mixed decompression before NY open. "
                "Liquidity event likely before direction."
        }
    
    # =====================================================
    # Overnigh Range DECOMPRESSION
        # One Line Rule: Engulfing overnight value after directional separation suggests continuation 
        # — engulfing from balance suggests purge
    # =====================================================
    # # DECOMPRESSION SET 2
    # =====================================================
    # BULLISH MACRO DECOMPRESSION
        # sell-side inducement → continuation higher
    # =====================================================

    if (
        ib8_engulf_ib18
        and ib1_above_ib18
    ):

        return {
            "structure": "bullish_macro_decompression",
            "category": "decompression",
            "direction": "bullish",

            "note_internal":
                "8AM IB engulfed 18 IB after bullish separation. "
                "Large bullish decompression above overnight value.",

            "note":
                "Bullish decompression before NY open. "
                "Higher pricing aggressively accepted."
        }

    # =====================================================
    # BEARISH MACRO DECOMPRESSION
        # buy-side inducement → continuation higher
    # =====================================================

    if (
        ib8_engulf_ib18
        and ib1_below_ib18
    ):

        return {
            "structure": "bearish_macro_decompression",
            "category": "decompression",
            "direction": "bearish",

            "note_internal":
                "8AM IB engulfed 18 IB after bearish separation. "
                "Large bearish decompression below overnight value.",

            "note":
                "Bearish decompression before NY open. "
                "Lower pricing aggressively accepted."
        }

    # =====================================================
    # MIXED MACRO DECOMPRESSION
        # double-sided inducement → before picking direction
    # =====================================================

    if ib8_engulf_ib18:

        return {
            "structure": "mixed_macro_decompression",
            "category": "decompression",
            "direction": "neutral",

            "note_internal":
                "8AM IB engulfed 18 IB from mixed positioning. "
                "Large purge of overnight value.",

            "note":
                "Mixed decompression before NY open. "
                "Liquidity purge environment."
        }
    # =====================================================
    # ASIA RANGE DECOMPRESSION
        # One Line Rule: Engulfing overnight value after directional separation suggests continuation 
        # — engulfing from balance suggests purge
    # =====================================================
    # DECOMPRESSION SET 3
    # =====================================================
    # BULLISH EARLY DECOMPRESSION
    # =====================================================

    if (
        ib1_engulf_ib18
        and ib8_above_ib1
    ):

        return {
            "structure": "bullish_early_decompression",
            "category": "decompression",
            "direction": "bullish",

            "note_internal":
                "1AM IB engulfed 18 IB and 8AM continued higher. "
                "Early bullish volatility expansion accepted.",

            "note":
                "Bullish early expansion during London session. "
                "Higher pricing accepted before NY open."
        }

    # =====================================================
    # BEARISH EARLY DECOMPRESSION
    # =====================================================

    if (
        ib1_engulf_ib18
        and ib8_below_ib1
    ):

        return {
            "structure": "bearish_early_decompression",
            "category": "decompression",
            "direction": "bearish",

            "note_internal":
                "1AM IB engulfed 18 IB and 8AM continued lower. "
                "Early bearish volatility expansion accepted.",

            "note":
                "Bearish decompression during London session. "
                "Lower pricing accepted before NY open."
        }

    # =====================================================
    # MIXED EARLY DECOMPRESSION
    # =====================================================

    if ib1_engulf_ib18:

        return {
            "structure": "mixed_early_decompression",
            "category": "decompression",
            "direction": "neutral",

            "note_internal":
                "1AM IB engulfed 18 IB but 8AM did not confirm "
                "directional continuation.",

            "note":
                "Mixed decompression during London session. "
                "Liquidity event likely before direction."
        }

    # =====================================================
    # DUAL INSIDE COMPRESSION
    # =====================================================

    if (
        ib1_inside_ib18
        and ib8_inside_ib1
    ):

        return {
            "structure": "dual_inside_compression",
            "category": "compression",
            "direction": "neutral",
            "note":
                "Nested compression. "
                "IB1 inside IB18 and IB8 inside IB1."
        }

    # =====================================================
    # STAIRCASE GAP BULLISH
    # =====================================================

    if (
        ib18["high"] < ib1["low"]
        and ib1["high"] < ib8["low"]
    ):

        return {
            "structure": "staircase_gap_bullish",
            "category": "bullish_acceptance",
            "direction": "bullish",
            "note":
                "Strong bullish trend with small retracements. "
                "Market aggressively accepting higher pricing.",
            "note_internal":
                "Strong bullish staircase with gaps. "
                "Market aggressively accepting higher pricing."
        }

    # =====================================================
    # STAIRCASE GAP BEARISH
    # =====================================================

    if (
        ib18["low"] > ib1["high"]
        and ib1["low"] > ib8["high"]
    ):

        return {
            "structure": "staircase_gap_bearish",
            "category": "bearish_acceptance",
            "direction": "bearish",
            "note":
                "Strong bearish trend with small retracements. "
                "Market aggressively accepting higher pricing.",
            "note_internal":
                "Strong bearish staircase with gaps. "
                "Market aggressively accepting lower pricing."
        }

    # =====================================================
    # STAIRCASE OVERLAP BULLISH
    # =====================================================
    # here there could be no gaps or atmost one gap between ibs

    if (
        ib1["low"] >= ib18["low"]
        and ib8["low"] >= ib1["low"]
        and ib8["high"] > ib1["high"]
    ):

        return {
            "structure": "staircase_overlap_bullish",
            "category": "bullish_acceptance",
            "direction": "bullish",
            "note_internal":
                "Bullish staircase overlap. "
                "Higher pricing accepted with rebalance.",
            "note":
                "Bullish trend with deeper retracements. "
                "Higher pricing accepted with rebalance."
        }

    # =====================================================
    # STAIRCASE OVERLAP BEARISH
    # =====================================================
    # # here there could be no gaps or atmost one gap between ibs

    if (
        ib1["high"] <= ib18["high"]
        and ib8["high"] <= ib1["high"]
        and ib8["low"] < ib1["low"]
    ):

        return {
            "structure": "staircase_overlap_bearish",
            "category": "bearish_acceptance",
            "direction": "bearish",
            "note_internal":
                "Bearish staircase overlap. "
                "Lower pricing accepted with rebalance.",
            "note":
                "Bearish trend with deeper retracements. "
                "Lower pricing accepted with rebalance."    
        }

    # =====================================================
    # BULLISH RECOMPRESSION
    # =====================================================

    if (
        ib1_above_ib18
        and ib8_inside_ib1
    ):

        return {
            "structure": "bullish_recompression",
            "category": "bullish_acceptance",
            "direction": "bullish",
            "note_internal":
                "Bullish recompression after prior expansion.",
            "note":
                "Bullish redistribution after prior expansion."
        }

    # =====================================================
    # BEARISH RECOMPRESSION
    # =====================================================

    if (
        ib1_below_ib18
        and ib8_inside_ib1
    ):

        return {
            "structure": "bearish_recompression",
            "category": "bearish_acceptance",
            "direction": "bearish",
            "note_internal":
                "Bearish recompression after prior expansion.",
            "note":
                "Bearish redistribution after prior expansion."
        }

    # =====================================================
    # BULLISH REBALANCE
    # =====================================================

    if (
        ib1_above_ib18
        and ib8_inside_ib18
    ):

        return {
            "structure": "bullish_rebalance",
            "category": "rebalance",
            "direction": "bullish",
            "note_internal":
                "Bullish expansion weakened into rebalance.",
            "note":
                "Bullish expansion weakened into rebalance."    
        }

    # =====================================================
    # BEARISH REBALANCE
    # =====================================================

    if (
        ib1_below_ib18
        and ib8_inside_ib18
    ):

        return {
            "structure": "bearish_rebalance",
            "category": "rebalance",
            "direction": "bearish",
            "note_internal":
                "Bearish expansion weakened into rebalance.",
            "note":
                "Bearish expansion weakened into rebalance."
        }

    # =====================================================
    # FAILED BULLISH EXPANSION
    # =====================================================
    # failed bullish expansion also called bullish reintegration
    # reintegration is much deeper than rebalance such that the earlier bullish expansion failed.

    if (
        ib1_above_ib18
        and ib8_overlap_ib18
        and ib8["low"] <= ib18["low"]
    ):

        return {
            "structure": "failed_bullish_expansion",
            "category": "failure",
            "direction": "bearish",
            "note_internal":
                "Bullish expansion failed and reintegrated.",
            "note":
                "Bullish expansion failed and reintegrated."
        }

    # =====================================================
    # FAILED BEARISH EXPANSION
    # =====================================================

    if (
        ib1_below_ib18
        and ib8_overlap_ib18
        and ib8["high"] >= ib18["high"]
    ):

        return {
            "structure": "failed_bearish_expansion",
            "category": "failure",
            "direction": "bullish",
            "note_internal":
                "Bearish expansion failed and reintegrated.",
            "note":
                "Bearish expansion failed and reintegrated."
        }

    # =====================================================
    # SANDWICH COMPRESSION SETS
    # =====================================================
    # SANDWICH COMPRESSION SET 1
        # mid range compression, cleaner directional move after sweep of compression extremes
    # =====================================================
    # SANDWICH GAP BULLISH
    # =====================================================

    if (
        ib1_above_ib18
        and ib8["high"] < ib1["low"]
        and ib8["low"] > ib18["high"]
    ):

        return {
            "structure": "sandwich_gap_bullish",
            "category": "balanced_compression",
            "direction": "bullish",
            "note_internal":
                "Bullish sandwich compression between separated ranges.",
            "note":
                "Bullish compression at equilibrium of asia and longon range."
        }

    # =====================================================
    # SANDWICH GAP BEARISH
    # =====================================================

    if (
        ib1_below_ib18
        and ib8["low"] > ib1["high"]
        and ib8["high"] < ib18["low"]
    ):

        return {
            "structure": "sandwich_gap_bearish",
            "category": "balanced_compression",
            "direction": "bearish",
            "note_internal":
                "Bearish sandwich compression between separated ranges.",
            "note":
                "Bearish compression at equilibrium of asia and longon range."
        }
    # =====================================================
    # SANDWICH PARTIAL OVERLAP
    # =====================================================
    # SANDWICH COMPRESSION SET 2
        # deeper or shallow range compression, deeper rebalance cab be inducement
    # overlap can be with ib1 or ib18
    # overlap with ib18, deeper rebalance, posibily inducement
    # =====================================================
    # SANDWICH PARTIAL OVERLAP BULLISH
    # =====================================================
    
    if (
        ib1_above_ib18
        and  ib1["low"] < ib8["high"] < ib1["high"]
        and ib8["low"] > ib18["high"]
    ):

        return {
            "structure": "sandwich_partial_overlap_bullish",
            "category": "balanced_compression",
            "direction": "bullish",
            "is_deep_rebalance": False,
            "note_internal":
                "Bullish sandwich compression with shallow rebalance.",
            "note": 
                "Bullish compression with shallow rebalance into asia-london range"
        }
    if (
        ib1_above_ib18
        and  ib8["high"] < ib1["low"]
        and ib18["low"] < ib8["low"] <= ib18["high"]
    ):

        return {
            "structure": "sandwich_partial_overlap_bullish",
            "category": "balanced_compression",
            "direction": "bullish",
            "is_deep_rebalance": True,
            "note_internal":
                "Bullish sandwich compression with deeper rebalance.",
            "note": 
                "Bullish compression with deep rebalance into asia-london range"
        }
    # =====================================================
    # SANDWICH PARTIAL OVERLAP BEARISH
    # =====================================================
    
    if (
        ib1_below_ib18
        and  ib1["low"] < ib8["low"] < ib1["high"]
        and ib8["high"] < ib18["low"]
    ):

        return {
            "structure": "sandwich_partial_overlap_bearish",
            "category": "balanced_compression",
            "direction": "bearish",
            "is_deep_rebalance": False,
            "note_internal":
                "Bearish sandwich compression with shallow rebalance.",
            "note": 
                "Bearish compression with shallow rebalance into asia-london range"
        }
    if (
        ib1_below_ib18
        and  ib8["low"] < ib1["high"]
        and ib18["low"] <= ib8["high"] < ib18["high"]
    ):

        return {
            "structure": "sandwich_partial_overlap_bearish",
            "category": "balanced_compression",
            "direction": "bearish",
            "is_deep_rebalance": True,
            "note_internal":
                "Bearish sandwich compression with deeper rebalance.",
            "note": 
                "Bearish compression with deep rebalance into asia-london range"
        }

    # =====================================================
    # SANDWICH OVERLAP BULLISH
    # =====================================================

    if (
        ib1_above_ib18
        and ib8_inside_ib1
        and ib8_inside_ib18
    ):

        return {
            "structure": "sandwich_overlap_bullish",
            "category": "balanced_compression",
            "direction": "bullish",
            "note_internal":
                "Balanced bullish sandwich compression.",
            "note": 
                "Price is still at daily open with tight compression."
        }

    # =====================================================
    # SANDWICH OVERLAP BEARISH
    # =====================================================

    if (
        ib1_below_ib18
        and ib8_inside_ib1
        and ib8_inside_ib18
    ):

        return {
            "structure": "sandwich_overlap_bearish",
            "category": "balanced_compression",
            "direction": "bearish",
            "note":
                "Balanced bearish sandwich compression."
        }

    # =====================================================
    # CENTERED COMPRESSION
    # =====================================================

    ib18_mid = (
        ib18["high"] + ib18["low"]
    ) / 2

    ib1_mid = (
        ib1["high"] + ib1["low"]
    ) / 2

    if (
        ib1_inside_ib18
        and abs(ib1_mid - ib18_mid)
        < 0.15 * ib_range(ib18)
    ):

        return {
            "structure": "centered_compression",
            "category": "compression",
            "direction": "neutral",
            "note":
                "Centered compression inside larger range."
        }

    # =====================================================
    # DEFAULT
    # =====================================================

    return {
        "structure": "mixed_overlap",
        "category": "mixed",
        "direction": "neutral",
        "note":
            "Mixed overlap structure. "
            "Directional conviction unclear."
    }




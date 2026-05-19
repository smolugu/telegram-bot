# ====================================================
# One Line Rules
#  1. Direction describes where expansion began — category describes how healthy it still is
#  2. Reintegration revisits old value — value flip establishes new value on the opposite side
#  3. Early reversals migrate value or flip value — late reversals usually only rebalance or reintegrate value
#  4. Reintegration weakens direction — SMT determines whether continuation still survives

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
            "is_compression": False,
            "is_decompression": True,
            "compression_strength": None,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,

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
            "is_compression": False,
            "is_decompression": True,
            "compression_strength": None,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,

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
            "is_compression": False,
            "is_decompression": True,
            "compression_strength": None,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,

            "note_internal":

                "8AM IB engulfed 1AM IB overlapping prior value. "
                "Continuation vs reversal unresolved. ",
                "Mixed decompression before NY open."

            "note":
                "Early expansion before NY open with unresolved direction, continuation vs reversal. "
                "Liquidity event likely before direction."
        }
    
    # =====================================================
    # Overnigh Range DECOMPRESSION
        # One Line Rule: Engulfing overnight value after directional separation suggests continuation 
        # In decompression structures, direction describes expansion origin — not guaranteed continuation
        # — engulfing from balance suggests purge
    # =====================================================
    # # DECOMPRESSION SET 2
    # =====================================================
    # BULLISH MACRO DECOMPRESSION
        # bullish origin but decompression makes directional acceptanace unstable. need confirmation
        # for continuation or reversal after decompression, watch for SMT agreement or disagreement
        # sell-side inducement → continuation higher
        # or buy-side inducement → continuation lower
    # =====================================================

    if (
        ib8_engulf_ib18
        and ib1_above_ib18
    ):

        return {
            "structure": "bullish_macro_decompression",
            "category": "decompression",
            "direction": "bullish",
            "is_compression": False,
            "is_decompression": True,
            "compression_strength": None,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,

            "note_internal":
                "8AM IB engulfed 18 IB after bullish separation. "
                "Large bullish macro decompression over overnight value.",

            "note":
                "Bullish decompression before NY open. "
                "Market is in active price discovery."
        }

    # =====================================================
    # BEARISH MACRO DECOMPRESSION
        # bearish origin but decompression makes directional acceptanace unstable. need confirmation
        # for continuation or reversal after decompression, watch for SMT agreement or disagreement
        # buy-side inducement → continuation lower
        # or sell-side inducement → continuation higher
    # =====================================================

    if (
        ib8_engulf_ib18
        and ib1_below_ib18
    ):

        return {
            "structure": "bearish_macro_decompression",
            "category": "decompression",
            "direction": "bearish",
            "is_compression": False,
            "is_decompression": True,
            "compression_strength": None,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,

            "note_internal":
                "8AM IB engulfed 18 IB after bearish separation. "
                "Large bearish decompression below overnight value.",

            "note":
                "Bearish decompression before NY open. "
                "Market is in active price discovery."
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
            "is_compression": False,
            "compression_strength": None,

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
            "is_compression": False,
            "compression_strength": None,

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
            "is_compression": False,
            "compression_strength": None,

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
            "is_compression": False,
            "compression_strength": None,

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
            "is_compression": True,
            "compression_strength": "Strong",
            "note_internal":
                "Nested compression. "
                "IB1 inside IB18 and IB8 inside IB1.",
            "note":
                "Strong consolidation during asia and london. "
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
            "is_compression": False,
            "compression_strength": None,
            
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
            "is_compression": False,
            "compression_strength": None,
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
            "is_compression": False,
            "compression_strength": None,
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
            "is_compression": False,
            "compression_strength": None,
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
            "is_compression": True,
            "compression_strength": "Strong",
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
            "is_compression": True,
            "compression_strength": "Strong",
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
            "is_compression": True,
            "compression_strength": "Strong",
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
            "is_compression": True,
            "compression_strength": "Strong",
            "note_internal":
                "Bearish expansion weakened into rebalance.",
            "note":
                "Bearish expansion weakened into rebalance."
        }

    # =====================================================
    # BULLISH REINTEGRATION - WEAKENED BULLISH EXPANSION
    # Reintegration weakens prior acceptance — it does not automatically confirm reversal
    # Reintegration is much deeper than rebalance, making prior move much weaker
    # but necessarily does not confirm reversal, price could still go either way after reintegration, but prior move is much weaker
    # =====================================================
    # Reintegration weakens direction — SMT determines whether continuation still survives

    if (
        ib1_above_ib18
        and ib18["low"] < ib8["high"] < ib18["high"]
        and ib8["low"] < ib18["low"]
        # and ib8_overlap_ib18
        # and ib8["low"] <= ib18["low"]
    ):

        return {
            "structure": "bullish_reintegration",
            "category": "reintegration",
            "direction": "bullish",
            "is_compression": True,
            "is_reintegration": True,
            "is_rebalance": False,
            "compression_strength": "Weak",
            "note_internal":
                "Bullish expansion weakened into reintegration.",
            "note":
                "Bullish expansion weakened significantly. Need bullish SMT to confirm bullish continuation."
        }

    # =====================================================
    # BEARISH REINTEGRATION - WEAKENED BEARISH EXPANSION
    # Reintegration weakens prior acceptance — it does not automatically confirm reversal
    # Reintegration is much deeper than rebalance, making prior move much weaker
    # but necessarily does not confirm reversal, price could still go either way after reintegration, but prior move is much weaker
    # =====================================================

    if (
        ib1_below_ib18
        and ib18["high"] > ib8["low"] > ib18["low"]
        and ib8["high"] > ib18["high"]
        # and ib8_overlap_ib18
        # and ib8["high"] >= ib18["high"]
    ):

        return {
            "structure": "bearish_reintegration",
            "category": "reintegration",
            "direction": "bearish",
            "is_compression": True,
            "compression_strength": "Weak",
            "is_reintegration": True,
            "is_rebalance": False,
            "note_internal":
                "Bearish expansion weakened into reintegration.",
            "note":
                "Bearish expansion weakened significantly. Need bearish SMT to confirm bearishcontinuation."
        }
    
    # =====================================================
    # BULLISH VALUE FLIP - FAILED BULLISH EXPANSION
    # Value flip - strong directional transition already accepted. Continuation in new direction 
    # Value flip is deeper than Reintegration, flipping the direction
    # Clean trend in new direction (bearish) - prefer smt at 9:30 open for continuation in new direction
    # =====================================================
    

    if (
        ib1_above_ib18
        and ib8["high"] < ib18["low"]
    ):

        return {
            "structure": "bullish_value_flip",
            "category": "value_flip",
            "direction": "bearish",
            "is_compression": False,
            "compression_strength": None,
            "is_reintegration": False,
            "is_value_flip": True,
            "is_rebalance": False,
            "note_internal":
                "Bullish expansion failed with ib8 flipping value and transitioning direction.",
            "note":
                "Bullish expansion failed and bearish prices accepted."
        }

    # =====================================================
    # BEARISH VALUE FLIP - FAILED BEARISH EXPANSION
    # Value flip - strong directional transition already accepted. Continuation in new direction
    # Value flip is deeper than Reintegration, flipping the direction
    # Clean trend in new direction (bullish) - prefer smt at 9:30 open for continuation in new direction
    # =====================================================

    if (
        ib1_below_ib18
        and ib8["high"] > ib18["high"]
    ):

        return {
            "structure": "bearish_value_flip",
            "category": "value_flip",
            "direction": "bullish",
            "is_compression": False,
            "compression_strength": None,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": True,
            "note_internal":
                "Bearish expansion failed with ib8 flipping value and transitioning direction.",
            "note":
                "Bearish expansion failed and bullish prices accepted."
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
            "is_compression": True,
            "compression_strength": "Strong",
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
            "is_compression": True,
            "compression_strength": "Strong",
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
            "is_compression": True,
            "compression_strength": "Strong",
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
            "is_compression": True,
            "compression_strength": "Strong",
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
            "is_compression": True,
            "compression_strength": "Strong",
            "is_deep_rebalance": False,
            "note_internal":
                "Bearish sandwich compression with shallow rebalance.",
            "note": 
                "Bearish compression with shallow rebalance into asia-london range"
        }
    if (
        ib1_below_ib18
        and  ib8["low"] > ib1["high"]
        and ib18["low"] <= ib8["high"] < ib18["high"]
    ):

        return {
            "structure": "sandwich_partial_overlap_bearish",
            "category": "balanced_compression",
            "direction": "bearish",
            "is_compression": True,
            "compression_strength": "Strong",
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
        and ib1["low"] < ib8["high"] < ib1["high"]
        and ib18["high"] > ib8["low"] > ib18["low"]
    ):

        return {
            "structure": "sandwich_overlap_bullish",
            "category": "balanced_compression",
            "direction": "bullish",
            "is_compression": True,
            "compression_strength": "Strong",
            "note_internal":
                "Balanced bullish sandwich compression.",
            "note": 
                "Price is consolidating at eq of asia and london range after bullish separation."
        }

    # =====================================================
    # SANDWICH OVERLAP BEARISH
    # =====================================================
    if (
        ib1_below_ib18
        and ib1["low"] < ib8["low"] < ib1["high"]
        and ib18["high"] > ib8["high"] > ib18["low"]
        
    ):

        return {
            "structure": "sandwich_overlap_bearish",
            "category": "balanced_compression",
            "direction": "bearish",
            "is_compression": True,
            "compression_strength": "Strong",
            "note_internal":
                "Balanced bearish sandwich compression.",
            "note": 
                "Price is consolidating at eq of asia and london range after bearish separation."
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
            "is_compression": True,
            "compression_strength": "Strong",
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




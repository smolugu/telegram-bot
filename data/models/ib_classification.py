# ====================================================
# One Line Rules: Structure
#  1. Direction describes where expansion began — category describes how healthy it still is
#  2. Reintegration revisits old value — value flip establishes new value on the opposite side
#  3. Early reversals migrate value or flip value — late reversals usually only rebalance or reintegrate value
#  4. Reintegration weakens direction — SMT determines whether continuation still survives
#  5. Direction preserves migration origin — categories describe how stable that migration remains
# One Line Rules: Compression range and liquidity
#  1. When HTF pressure is strong, equilibrium liquidity alone can fuel expansion

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
            "compression_strength": None,
            "is_acceptance": True,
            "is_decompression": True,
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
            "compression_strength": None,
            "is_acceptance": True,
            "is_decompression": True,
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
            "compression_strength": None,
            "is_acceptance": False,
            "is_decompression": True,
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
            "compression_strength": None,
            "is_acceptance": False,
            "is_decompression": True,
            "is_rebalance": False,
            "is_reintegration": True,
            "is_value_flip": False,

            "note_internal":
                "8AM IB engulfed overnight value after bullish separation. "
                "Volatility expanded aggressively around prior value.",

            "note":
                "Large price swings developed before NY open. "
                "Expect volatile conditions until direction becomes clearer."
        }

    # =====================================================
    # BEARISH MACRO DECOMPRESSION
        # bearish origin but decompression makes directional acceptanace unstable. need confirmation
        # for continuation or reversal after decompression, watch for SMT agreement or disagreement
        # buy-side inducement → continuation lower
        # or sell-side inducement → continuation higher
        # subtle distinction between rebalance and reintegration which decompression at old value.

            # In bearish_macro_decompression:
            # - price DID return through overnight value
            # so reintegration behavior occurred.

            # But:
            # - price did not stabilize after reintegration
            # - it expanded aggressively through the entire value range

            # So:
            # - decompression remains the dominant category
            # - reintegration becomes an embedded behavior

            # Therefore the cleanest interpretation is probably:

            # "is_decompression": True,
            # "is_reintegration": True,
            # "is_rebalance": False

            # because:
            # - reintegration happened
            # - but equilibrium was not preserved afterward.
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
            "compression_strength": None,
            "is_acceptance": False,
            "is_decompression": True,
            "is_rebalance": False,
            "is_reintegration": True,
            "is_value_flip": False,

            "note_internal":
                "8AM IB engulfed overnight value after bearish separation. "
                "Volatility expanded aggressively around prior value.",

            "note":
                "Large price swings developed before NY open. "
                "Expect volatile conditions until direction becomes clearer."
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
            "is_acceptance": False,
            "is_decompression": True,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,

            "note_internal":
                "8AM IB engulfed 18 IB from mixed positioning. "
                "Large purge of overnight value.",

            "note":
                "Mixed bias and early signs of market expansion before NY open. "
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
            "is_acceptance": True,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,

            "note_internal":
                "1AM IB engulfed 18 IB and 8AM continued higher. "
                "Early bullish volatility expansion accepted.",

            "note":
                "Bullish early expansion during London session. "
                "Higher pricing accepted before NY open. Expect price to make shallow retracement towards london equilibrium or sweep of lows before continuation higher."
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
            "is_acceptance": True,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,

            "note_internal":
                "1AM IB engulfed 18 IB and 8AM continued lower. "
                "Early bearish volatility expansion accepted.",

            "note":
                "Bearish early expansion during London session. "
                "Lower pricing accepted before NY open. Expect price to make shallow retracement towards london equilibrium or sweep of highs before continuation lower."
        }

    # =====================================================
    # MIXED EARLY DECOMPRESSION
    # When compression forms inside decompression, the market is stabilizing after volatility expansion — not yet confirming direction
    # IB8 inside IB1. ib8 neither above or below ib1
    # =====================================================

    if ib1_engulf_ib18:
        compression_range = {"high": None, "low": None}
        equilibrium_range = {"high": None, "low": None}
        if ib8["high"] < ib1["high"] and ib8["low"] > ib1["low"]:
            compression_range = {
                "high": ib1["high"],
                "low": ib1["low"]
            },
            equilibrium_range = {
                "high": ib8["high"],
                "low": ib8["low"]
            },
        elif ib8["high"] > ib1["high"] and  ib1["high"] > ib8["low"] > ib1["low"]:
            compression_range = {
                "high": ib8["high"],
                "low": ib1["low"]
            },
            equilibrium_range = {
                "high": ib1["high"],
                "low": ib8["low"]
            },
        elif ib8["low"] < ib1["low"] and ib1["low"] < ib8["high"] < ib1["high"]:
            compression_range = {
                "high": ib1["high"],
                "low": ib8["low"]
            },
            equilibrium_range = {
                "high": ib8["high"],
                "low": ib1["low"]
            },
        

        return {
            "structure": "mixed_early_decompression",
            "category": "decompression",
            "direction": "neutral",
            "is_compression": True,
            "compression_strength": "Strong",
            "is_acceptance": False,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "compression_range": compression_range,
            "equilibrium_range": equilibrium_range,
            "note_internal":
                "1AM IB engulfed 18 IB but 8AM recompressed inside 1AM IB. ",

            "note":
                "Market stabilized after early expansion during London session. "
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
            "is_acceptance": False,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "compression_range": {
                "high": ib18["high"],
                "low": ib18["low"]
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib8["low"]
            },
            "note_internal":
                "Nested compression. "
                "IB1 inside IB18 and IB8 inside IB1.",
            "note":
                "Strong consolidation inside asia and london range with no directional bias. Expect volatility expansion after sweep of compression extremes."
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
            "is_acceptance": True,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "note_internal":
                "Strong bullish staircase with gaps. "
                "Market aggressively accepting higher pricing.",
            "note":
                "Strong bullish trend with small retracements. "
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
            "is_acceptance": True,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "note_internal":
                "Strong bearish staircase with gaps. "
                "Market aggressively accepting lower pricing.",
            "note":
                "Strong bearish trend with small retracements. "
                "Market aggressively accepting higher pricing."
        }

    # =====================================================
    # STAIRCASE OVERLAP BULLISH
    # =====================================================
    # here there could be no gaps or atmost one gap between ibs

    if (
        ib1["low"] > ib18["high"]
        and ib8["low"] >= ib1["low"]
        and ib8["high"] > ib1["high"]
    ):

        return {
            "structure": "staircase_overlap_bullish",
            "category": "bullish_acceptance",
            "direction": "bullish",
            "is_compression": True,
            "compression_strength": "Weak",
            "is_acceptance": True,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "compression_range": {
                "high": ib8["high"],
                "low": ib1["low"]
            },
            "equilibrium_range": {
                "high": ib1["high"],
                "low": ib8["low"]
            },
            "note_internal":
                "Bullish staircasing continued overnight, "
                "but premarket migration weakened slightly "
                "as price remained connected to prior value.",

            # "note":
            #     "Gradual bullish migration developed overnight. "
            #     "Premarket upside efficiency weakened slightly, "
            #     "which can create clean downside flush conditions "
            #     "if reversal confirms."
            # "note_internal":
            #     "Bullish staircase overlap. "
            #     "Higher pricing accepted with rebalance.",
            "note":
                "Gradual bullish migration during asia and london sessions with efficiency weakening slightly during premarket. "
        }

    # =====================================================
    # STAIRCASE OVERLAP BEARISH
    # =====================================================
    # # here there could be no gaps or atmost one gap between ibs

    if (
        ib1["high"] < ib18["low"]
        and ib8["high"] <= ib1["high"]
        and ib8["low"] < ib1["low"]
    ):

        return {
            "structure": "staircase_overlap_bearish",
            "category": "bearish_acceptance",
            "direction": "bearish",
            "is_compression": True,
            "compression_strength": "Weak",
            "is_acceptance": True,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "compression_range": {
                "high": ib1["high"],
                "low": ib8["low"]
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib1["low"]
            },
            "note_internal":
                "Bearish staircasing continued overnight, "
                "but premarket migration weakened slightly "
                "as price remained connected to prior value.",
            "note":
                "Gradual bearish migration during asia and london sessions with efficiency weakening slightly during premarket."
        }
    
    # =====================================================
    # STAIRCASE BULLISH
    # =====================================================
    # here there could be no gaps between ibs
    # this structure generates low resistance liquidity runs, most likely sweep upside and flush at atr exhaustion or with smt
    # ib8 > ib1 > ib18
    # compression and equilibrium ranges are from weak compression due to overlap of ib8 and ib1

    if (
        ib18["low"] < ib1["low"] < ib18["high"]
        and ib1["low"] < ib8["low"] < ib1["high"]
        and ib1["high"] < ib8["high"]
    ):

        return {
            "structure": "staircase_bullish",
            "category": "acceptance",
            "direction": "bullish",
            "is_compression": True,
            "compression_strength": "Weak",
            "is_acceptance": True,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "compression_range": {
                "high": ib8["high"],
                "low": ib1["low"]
            },
            "equilibrium_range": {
                "high": ib1["high"],
                "low": ib8["low"]
            },
            "note_internal":
                "Higher value continued being accepted overnight, "
                "but migration remained inefficient as price "
                "continued overlapping prior value.",

            # "note":
            #     "Orderly bullish staircasing formed overnight. "
            #     "Price continued accepting higher value while "
            #     "remaining connected to prior liquidity. "
            #     "If reversal confirms, downside flushes can "
            #     "accelerate quickly due to gradually engineered liquidity."
            
            "note":
                "Bullish trend accepting higher prices with less efficiency. "
        }
    
    # =====================================================
    # STAIRCASE BEARISH
    # =====================================================
    # here there could be no gaps between ibs
    # this structure generates low resistance liquidity runs, most likely sweep downside and rally (rocket) at atr exhaustion or with smt
    # ib8 < ib1 < ib18
    # compression and equilibrium ranges are from weak compression due to overlap of ib8 and ib1

    if (
        ib18["high"] > ib1["high"] > ib18["low"]
        and ib1["high"] > ib8["high"] > ib1["low"]
        and ib1["low"] > ib8["low"]
    ):

        return {
            "structure": "staircase_bearish",
            "category": "acceptance",
            "direction": "bearish",
            "is_compression": True,
            "compression_strength": "Weak",
            "is_acceptance": True,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "compression_range": {
                "high": ib1["high"],
                "low": ib8["low"]
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib1["low"]
            },
            "note_internal":
                "Lower value continued being accepted overnight, "
                "but migration remained inefficient as price "
                "continued overlapping prior value.",
            "note":
                "Bearish trend continued accepting lower prices with less efficiency. "
        }

    # =====================================================
    # BULLISH ACCEPTANCE COMPRESSION
    # =====================================================

    if (
        ib1_above_ib18
        and ib8_inside_ib1
    ):

        return {
            "structure": "bullish_acceptance_compression",
            "category": "bullish_acceptance",
            "direction": "bullish",
            "is_compression": True,
            "compression_strength": "Strong",
            "is_acceptance": True,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "compression_range": {
                "high": ib1["high"],
                "low": ib1["low"]
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib8["low"]
            },
            "note_internal":
                "Bullish acceptance and compression at new value after prior expansion.",
            "note":
                "Bullish redistribution after prior expansion. Expect sweep of lows before continuation higher."
        }

    # =====================================================
    # BEARISH ACCEPTANCE COMPRESSION
    # =====================================================

    if (
        ib1_below_ib18
        and ib8_inside_ib1
    ):

        return {
            "structure": "bearish_acceptance_compression",
            "category": "bearish_acceptance",
            "direction": "bearish",
            "is_compression": True,
            "compression_strength": "Strong",
            "is_acceptance": True,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "compression_range": {
                "high": ib1["high"],
                "low": ib1["low"]
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib8["low"]
            },
            "note_internal":
                "Bearish acceptance and compression at new value after prior expansion.",
            "note":
                "Bearish redistribution after prior expansion. Expect sweep of highs before continuation lower."
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
            "is_acceptance": False,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": True,
            "is_value_flip": False,
            "compression_range": {
                "high": ib18["high"],
                "low": ib18["low"]
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib8["low"]
            },
            "note_internal":
                "Bullish expansion weakened into rebalance.",
            "note":
                "Bullish expansion weakened into rebalance near daily open."    
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
            "is_acceptance": False,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": True,
            "is_value_flip": False,
            "compression_range": {
                "high": ib18["high"],
                "low": ib18["low"]
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib8["low"]
            },
            "note_internal":
                "Bearish expansion weakened into rebalance.",
            "note":
                "Bearish expansion weakened into rebalance at daily open."
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
    ):

        return {
            "structure": "bullish_reintegration",
            "category": "reintegration",
            "direction": "bullish",
            "is_compression": True,
            "compression_strength": "Weak",
            "is_acceptance": False,
            "is_reintegration": True,
            "is_rebalance": False,
            "is_decompression": False,
            "is_value_flip": False,
            "compression_range": {
                "high": ib18["high"],
                "low": ib8["low"]
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib18["low"]
            },
            
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
    ):

        return {
            "structure": "bearish_reintegration",
            "category": "reintegration",
            "direction": "bearish",
            "is_compression": True,
            "compression_strength": "Weak",
            "is_acceptance": False,
            "is_reintegration": True,
            "is_rebalance": False,
            "is_decompression": False,
            "is_value_flip": False,
            "compression_range": {
                "high": ib8["high"],
                "low": ib18["low"]
            },
            "equilibrium_range": {
                "high": ib18["high"],
                "low": ib8["low"]
            },
            "note_internal":
                "Bearish expansion weakened into reintegration.",
            "note":
                "Bearish expansion weakened significantly. Need bearish SMT to confirm bearish continuation."
        }
    
    # =====================================================
    # BULLISH VALUE FLIP - FAILED BULLISH EXPANSION
    # Value flip - strong directional transition already accepted. Continuation in new direction 
    # Value flip is deeper than Reintegration, flipping the direction
    # Clean trend in new direction (bearish) - prefer smt at 9:30 open for continuation in new direction
    # Reintegration weakens origin direction — value flip replaces origin direction
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
            "is_acceptance": True,
            "is_reintegration": False,
            "is_value_flip": True,
            "is_rebalance": False,
            "is_decompression": False,
            "note_internal":
                "Bullish expansion failed with ib8 flipping value and transitioning direction.",
            "note":
                "Bullish expansion during london failed and bearish prices accepted in premarket."
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
            "is_acceptance": True,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": True,
            "is_decompression": False,
            "note_internal":
                "Bearish expansion failed with ib8 flipping value and transitioning direction.",
            "note":
                "Bearish expansion during dondon failed and bullish prices accepted in premarket."
        }
    
    # =====================================================
    # SANDWICH COMPRESSION SETS
    # =====================================================
    # SANDWICH COMPRESSION SET 1
        # mid range compression, expect cleaner directional move after sweep of compression extremes
    # =====================================================
    # SANDWICH GAP BULLISH
    # =====================================================
    # for now treating ib8 range as compression and equilibrium range

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
            "is_acceptance": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "is_decompression": False,
            "compression_range": {
                "high": ib8["high"],
                "low": ib8["low"],
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib8["low"],
            },
            "note_internal":
                "Bullish sandwich compression between separated ranges.",
            "note":
                "Early bullish move followed by consolidation at equilibrium of asia and london range."
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
            "is_acceptance": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "is_decompression": False,
            "compression_range": {
                "high": ib8["high"],
                "low": ib8["low"],
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib8["low"],
            },
            "note_internal":
                "Bearish sandwich compression between separated ranges.",
            "note":
                "Early bearish move followed by consolidation at equilibrium of asia and london range."
        }
    # =====================================================
    # SANDWICH PARTIAL OVERLAP
    # =====================================================
    # SANDWICH COMPRESSION SET 2
        # deeper or shallow range compression, deeper rebalance cab be inducement
    # overlap can be with ib1 or ib18
    
    # =====================================================
    # SANDWICH PARTIAL OVERLAP BULLISH
    # overlap with ib18, deeper rebalance, posibily inducement
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
            "is_acceptance": True,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "is_decompression": False,
            "compression_range": {
                "high": ib1["high"],
                "low": ib8["low"],
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib1["low"],
            },
            "note_internal":
                "Bullish sandwich compression with acceptance weakeness.",
            "note": 
                "Consolidation inside asia-london range with weakness in accepting higher prices after early bullish move."
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
            "is_acceptance": False,
            "is_reintegration": False,
            "is_rebalance": True,
            "is_value_flip": False,
            "is_decompression": False,
            "compression_range": {
                "high": ib8["high"],
                "low": ib18["low"],
            },
            "equilibrium_range": {
                "high": ib18["high"],
                "low": ib8["low"],
            },
            "note_internal":
                "Bullish sandwich compression with rebalance.",
            "note": 
                "Consolidation inside asia-london range. Price tapped into deeper asia range, weakening earlier bullish move"
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
            "is_acceptance": True,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "is_decompression": False,
            "compression_range": {
                "high": ib8["high"],
                "low": ib1["low"],
            },
            "equilibrium_range": {
                "high": ib1["high"],
                "low": ib8["low"],
            },
            "note_internal":
                "Bearish sandwich compression with acceptance weakness.",
            "note": 
                "Consolidation inside asia-london range with weakness in accepting lower prices after early bearish move."
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
            "is_acceptance": False,
            "is_reintegration": False,
            "is_rebalance": True,
            "is_value_flip": False,
            "is_decompression": False,
            "compression_range": {
                "high": ib18["high"],
                "low": ib8["low"],
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib18["low"],
            },
            "note_internal":
                "Bearish sandwich compression with rebalance at daily open.",
            "note": 
                "Consolidation inside asia-london range. Price tapped into deeper asia range, weakening earlier bearish move"
        }

    # =====================================================
    # SANDWICH OVERLAP BULLISH
    # all ibs overlapping with each other, or gap between ib1 and ib18, with ib8 overlapping ib1 and ib18
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
            "is_acceptance": True,
            "is_reintegration": False,
            "is_rebalance": True,
            "is_value_flip": False,
            "is_decompression": False,
            "compression_range": {
                "high": ib1["high"],
                "low": ib18["low"],
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib8["low"],
            },
            "note_internal":
                "Balanced bullish sandwich compression.",
            "note": 
                "Price is consolidating at eq of asia-london range after bullish move in asia."
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
            "is_acceptance": True,
            "is_reintegration": False,
            "is_rebalance": True,
            "is_value_flip": False,
            "is_decompression": False,
            "compression_range": {
                "high": ib18["high"],
                "low": ib1["low"],
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib8["low"],
            },
            "note_internal":
                "Balanced bearish sandwich compression.",
            "note": 
                "Price is consolidating at eq of asia-london range after bearish move in asia."
        }
    # =====================================================
    # SANDWICH BULLISH
    # all ibs overlapping with each other with no gaps between them
    # tight and energetic compression with explosive move after sweep of compression extremes
    # =====================================================

    if (
        ib1["high"] >  ib18["high"] and ib18["low"] < ib1["low"] < ib18["high"]
        and ib1["low"] < ib8["high"] < ib1["high"]
        and ib18["high"] > ib8["low"] > ib18["low"]
    ):

        return {
            "structure": "sandwich_bullish",
            "category": "compression",
            "direction": "neutral",
            "is_compression": True,
            "compression_strength": "Strong",
            "is_acceptance": True,
            "is_rebalance": True,
            "is_reintegration": False,
            "is_value_flip": False,
            "is_decompression": False,
            "compression_range": {
                "high": ib1["high"],
                "low": ib18["low"]
            },
            "equilibrium_range": {
                "high": min(ib18["high"], ib1["high"]),
                "low": max(ib18["low"], ib1["low"])
            },
            "note_internal":
                "The market remained centered with acceptance of neither bullish nor bearish sentiment.",
            "note": 
                "The market is in a tight consolidation with no clear directional bias. Expect a strong directional move after sweep of consolidation range."
        }
    
    # =====================================================
    # SANDWICH BEARISH
    # all ibs overlapping with each other with no gaps between them
    # tight and energetic compression with explosive move after sweep of compression extremes
    # =====================================================

    if (
        ib18["high"] > ib1["high"] and ib1["low"] < ib18["low"] < ib1["high"]
        and ib18["low"] < ib8["high"] < ib18["high"]
        and ib1["high"] > ib8["low"] > ib1["low"]
    ):

        return {
            "structure": "sandwich_bearish",
            "category": "compression",
            "direction": "neutral",
            "is_compression": True,
            "compression_strength": "Strong",
            "is_acceptance": True,
            "is_rebalance": True,
            "is_reintegration": False,
            "is_value_flip": False,
            "is_decompression": False,
            "compression_range": {
                "high": ib18["high"],
                "low": ib1["low"]
            },
            "equilibrium_range": {
                "high": min(ib18["high"], ib1["high"]),
                "low": max(ib18["low"], ib1["low"])
            },
            "note_internal":
                "The market remained centered with acceptance of neither bullish nor bearish sentiment.",
            "note": 
                "The market is in a tight consolidation with no clear directional bias. Expect a strong directional move after sweep of consolidation range."
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
            "is_acceptance": False,
            "is_rebalance": False,
            "is_reintegration": False,
            "is_value_flip": False,
            "is_decompression": False,
            "notes_internal": "IB1 inside IB18 with midpoints within 15% of IB18 range.",
            "note":
                "Tight consolidation inside larger asia range."
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




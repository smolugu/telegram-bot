# ====================================================
# One Line Rules: Structure
#  1. Direction describes where expansion began — category describes how healthy it still is
#  2. Reintegration revisits old value — value flip establishes new value on the opposite side
#  3. Early reversals migrate value or flip value — late reversals usually only rebalance or reintegrate value
#  4. Reintegration weakens direction — SMT determines whether continuation still survives
#  5. Direction preserves migration origin — categories describe how stable that migration remains
#  6. Category describes value behavior — migration strength describes how forcefully price accepted that behavior
# One Line Rules: Compression range and liquidity and mitigation levels and equilibrium levels
#  1. When HTF pressure is strong, equilibrium liquidity alone can fuel expansion
#  2. When price migrates, the mitigation level will be the euilibrium level of the migration range
#  3. When price consolidates, the mitigation happens inside the range at equilibrium or at the extremes of compression range
#  4. For sandwich structures, The full compression range defines the battlefield — the IB8 range defines the immediate trigger zone. IB8 range becomes inducement zone, sweep zone, trigger zone, mitigation zone

# attributes
# compression range - range for compression zone
# range - migration range or overall range
# equilibrium_range - equilibrium or trigger zone inside macro compression range
# migration_strength - "very_strong", "strong", "moderate", "weak", "neutral". Used to anticipate retracement strength, shallow or deep
# mitigation_level - Equilibrium of displacement or migration range. (Or) break of structure level. (Or) equilibrium of compression when compression exists. (Or) None when no clear mitigation level exists.

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
        "structure_name": str,
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
    # bullish decompression after accepted migration
    # =====================================================
    # Aggressive bullish repricing occurred entirely above old value
    # This is active expansion, active migration, active displacement
    # Inside decompression, the engulfed IB becomes the equilibrium mitigation zone inside the larger displacement range

    if (
        ib8_engulf_ib1
        and ib1_above_ib18
        and ib8["low"] > ib18["high"]
    ):

        return {
            "structure_name": "bullish_decompression",
            "category": "decompression",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "neutral",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,

            "is_acceptance": True,
            "is_decompression": True,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "range": {
                "high": ib8["high"],
                "low": ib8["low"],
                "ce": (ib8["high"] + ib8["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib1["high"],
                "low": ib1["low"],
                "ce": (ib1["high"] + ib1["low"]) / 2
            },
            "mitigation_level": None,

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
            "structure_name": "bearish_decompression",
            "category": "decompression",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "neutral",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": True,
            "is_decompression": True,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "range": {
                "high": ib8["high"],
                "low": ib8["low"],
                "ce": (ib8["high"] + ib8["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib1["high"],
                "low": ib1["low"],
                "ce": (ib1["high"] + ib1["low"]) / 2
            },
            "mitigation_level": None,

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
            "structure_name": "mixed_decompression",
            "category": "decompression",
            "direction": "neutral",
            "is_staircase": False,
            "migration_strength": "neutral",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": False,
            "is_decompression": True,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "range": {
                "high": ib8["high"],
                "low": ib8["low"],
                "ce": (ib8["high"] + ib8["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib1["high"],
                "low": ib1["low"],
                "ce": (ib1["high"] + ib1["low"]) / 2
            },
            "mitigation_level": None,

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
            "structure_name": "bullish_macro_decompression",
            "category": "decompression",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "neutral",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": False,
            "is_decompression": True,
            "is_rebalance": False,
            "is_reintegration": True,
            "is_value_flip": False,
            # entire range from ib1 high to ib8 low
            "range": {
                "high": ib1["high"],
                "low": ib8["low"],
                "ce": (ib1["high"] + ib8["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib1["low"],
                "low": ib18["high"],
                "ce": (ib1["low"] + ib18["high"]) / 2
            },
            # mid point between ib1 and ib18
            "mitigation_level": (ib1["low"] + ib18["high"]) / 2,

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
            "structure_name": "bearish_macro_decompression",
            "category": "decompression",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "neutral",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": False,
            "is_decompression": True,
            "is_rebalance": False,
            "is_reintegration": True,
            "is_value_flip": False,
            "range": {
                "high": ib8["high"],
                "low": ib1["low"],
                "ce": (ib8["high"] + ib1["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib8["low"],
                "low": ib1["high"],
                "ce": (ib8["low"] + ib1["high"]) / 2
            },
            # mid point between ib1 and ib18
            "mitigation_level": (ib8["low"] + ib1["high"]) / 2,

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
            "structure_name": "mixed_macro_decompression",
            "category": "decompression",
            "direction": "neutral",
            "is_staircase": False,
            "migration_strength": "neutral",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": False,
            "is_decompression": True,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "range": {"high":ib8["high"], "low": ib8["low"], "ce": (ib8["high"] + ib8["low"]) / 2},
            "equilibrium_range": {"high":ib18["high"], "low": ib18["low"], "ce": (ib18["high"] + ib18["low"]) / 2},
            "mitigation_level": (ib18["high"] + ib18["low"]) / 2,

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
    # migration strength for decompression = "neutral" - active repricing / unstable migration, retracement depth unresolved
    # here migration strength == strong as decompression happened in london and migrated above with ib8 above ib1
    # engulfing or decompression encodes volatility expansion, not retracement quality

    if (
        ib1_engulf_ib18
        and ib8_above_ib1
    ):

        return {
            "structure_name": "bullish_early_decompression",
            "category": "decompression",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "strong",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": True,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "range": {"high": ib8["high"], "low": ib1["low"], "ce": (ib8["high"]+ ib1["low"]) / 2},
            "equilibrium_range": {"high": ib8["high"], "low": ib1["low"], "ce": (ib8["high"]+ ib1["low"]) / 2},
            "mitigation_level": (ib8["high"]+ ib1["low"])/2,

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
            "structure_name": "bearish_early_decompression",
            "category": "decompression",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "neutral",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": True,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "range": {"high": ib1["high"], "low": ib8["low"], "ce": (ib1["high"]+ ib8["low"]) / 2},
            "equilibrium_range": {"high": ib1["high"], "low": ib8["low"], "ce": (ib1["high"]+ ib8["low"]) / 2},
            "mitigation_level": (ib1["high"]+ ib8["low"])/2,

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
                "low": ib1["low"],
                "ce": (ib1["high"] + ib1["low"]) / 2
            },
            equilibrium_range = {
                "high": ib8["high"],
                "low": ib8["low"],
                "ce": (ib8["high"] + ib8["low"]) / 2
            },
        elif ib8["high"] > ib1["high"] and  ib1["high"] > ib8["low"] > ib1["low"]:
            compression_range = {
                "high": ib8["high"],
                "low": ib1["low"],
                "ce": (ib8["high"] + ib1["low"]) / 2
            },
            equilibrium_range = {
                "high": ib1["high"],
                "low": ib8["low"],
                "ce": (ib1["high"] + ib8["low"]) / 2
            },
        elif ib8["low"] < ib1["low"] and ib1["low"] < ib8["high"] < ib1["high"]:
            compression_range = {
                "high": ib1["high"],
                "low": ib8["low"],
                "ce": (ib1["high"] + ib8["low"]) / 2
            },
            equilibrium_range = {
                "high": ib8["high"],
                "low": ib1["low"],
                "ce": (ib8["high"] + ib1["low"]) / 2
            },
        

        return {
            "structure_name": "mixed_early_decompression",
            "category": "decompression",
            "direction": "neutral",
            "is_staircase": False,
            "migration_strength": "neutral",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": False,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "range": compression_range,
            "equilibrium_range": equilibrium_range,
            "mitigation_level": equilibrium_range["ce"],
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
            "structure_name": "dual_inside_compression",
            "category": "compression",
            "direction": "neutral",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": False,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "range": {
                "high": ib18["high"],
                "low": ib18["low"],
                "ce": (ib18["high"] + ib18["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib8["low"],
                "ce": (ib8["high"] + ib8["low"]) / 2
            },
            "mitigation_level": equilibrium_range["ce"],
            "note_internal":
                "Nested compression. "
                "IB1 inside IB18 and IB8 inside IB1.",
            "note":
                "Strong consolidation inside asia and london range with no directional bias. Expect volatility expansion after sweep of compression extremes."
        }

    # =====================================================
    # STAIRCASE GAP BULLISH
    # =====================================================
    # In staircase gap migration, the newest transition gap becomes the continuation mitigation battlefield

    if (
        ib18["high"] < ib1["low"]
        and ib1["high"] < ib8["low"]
    ):

        return {
            "structure_name": "staircase_gap_bullish",
            "category": "bullish_acceptance",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "very_strong",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": True,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "compression_range": {
                "high": None,
                "low": None,
                "ce": None
            },
            "range": {
                "high": ib8["high"],
                "low": ib18["low"],
                "ce": (ib8["high"] + ib18["low"]) / 2
            },

            "equilibrium_range": {
                "high": ib8["low"],
                "low": ib1["high"],
                "ce": (ib8["low"] + ib1["high"]) / 2
            },
            # mitigation level = closest imbalance
            "mitigation_level": (ib8["low"] + ib1["high"]) / 2,
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
            "structure_name": "staircase_gap_bearish",
            "category": "bearish_acceptance",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "very_strong",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": True,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "compression_range": {
                "high": None,
                "low": None,
                "ce": None
            },
            "range": {
                "high": ib18["high"],
                "low": ib8["low"],
                "ce": (ib18["high"] + ib8["low"]) / 2
            },

            "equilibrium_range": {
                "high": ib1["low"],
                "low": ib8["high"],
                "ce": (ib1["low"] + ib8["high"]) / 2
            },
            # mitigation level = closest imbalance
            "mitigation_level": (ib1["low"] + ib8["high"]) / 2,
            "note_internal":
                "Strong bearish staircase with gaps. "
                "Market aggressively accepting lower pricing.",
            "note":
                "Strong bearish trend with small retracements. "
                "Market aggressively accepting higher pricing."
        }

    # =====================================================
    # STAIRCASE EARLY OVERLAP BULLISH
    # Early overlap means migration strengthened later — late overlap means migration weakened later
    # =====================================================
    # here there could be no gaps or atmost one gap between ibs

    if (
        ib8["low"] > ib1["high"]
        and ib18["high"]  > ib1["low"] >= ib18["low"]
        and ib1["high"] > ib18["high"]
    ):

        return {
            "structure_name": "staircase_early_overlap_bullish",
            "category": "bullish_acceptance",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "strong",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": True,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            # compression is early in london, potential long in london
            "compression_range": {
                "high": ib1["high"],
                "low": ib18["low"],
                "ce": (ib1["high"] + ib18["low"]) / 2
            },
            "range": {
                "high": ib8["high"],
                "low": ib1["low"],
                "ce": (ib8["high"] + ib1["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib1["high"],
                "low": ib8["low"],
                "ce": (ib1["high"] + ib8["low"]) / 2
            },
            "mitigation_level": (ib8["high"] + ib1["low"]) / 2,
            "note_internal":
                "Bullish staircasing continued overnight, "
                "with strengthening migration during premarket",

            # "note":
            #     "Gradual bullish migration developed overnight. "
            #     "Premarket upside efficiency weakened slightly, "
            #     "which can create clean downside flush conditions "
            #     "if reversal confirms."
            # "note_internal":
            #     "Bullish staircase overlap. "
            #     "Higher pricing accepted with rebalance.",
            "note":
                "Gradual bullish migration during asia and london sessions with increased migration strength by premarket. "
        }

    # =====================================================
    # STAIRCASE LATE OVERLAP BULLISH
        # Environment - Bullish migration weakening slightly.
        # Default Direction - bullish favored
        # Default Ping Type - Rocket continuation
        # Required Confirmations
            # sweep of overlap equilibrium
            # bullish rejection
            # preserved migration
        # Notes
            # Can reverse if ATR exhausted.
            # Late overlap turns the newest overlap region into the continuation mitigation battlefield
            # Early overlap means migration strengthened later — late overlap means migration weakened later
            # ATR exhausted
                # Ping Flush
            # ATR not exhausted
                # mini shorts (not ping) if ib8 high is swepts before 9:30, expect price to move to equilibrium of ib18-ib8 range
                # if ib8 high not swept, look for continuation long (ping expansion) from equilibrium
    # =====================================================

    if (
        ib1["low"] > ib18["high"]
        and ib1["high"]  > ib8["low"] >= ib1["low"]
        and ib8["high"] > ib1["high"]
        
    ):

        return {
            "structure_name": "staircase_late_overlap_bullish",
            "category": "bullish_acceptance",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "moderate",
            "is_compression": True,
            "is_strong_compression": False,
            "compression_strength": "weak",
            "is_acceptance": True,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "compression_range": {
                "high": ib8["high"],
                "low": ib1["low"],
                "ce": (ib8["high"] + ib1["low"]) / 2
            },
            # migration range
            "range": {
                "high": ib8["high"],
                "low": ib18["low"],
                "ce": (ib8["high"] + ib18["low"]) / 2
            },
            # weak compression from ib8 overlap of ib1 high, so mitigation happens here, trigger zone
            "equilibrium_range": {
                "high": ib1["high"],
                "low": ib8["low"],
                "ce": (ib1["high"] + ib8["low"]) / 2
            },
            # retracement level from compression or trigger zone
            "mitigation_level": (ib8["high"] + ib18["low"]) / 2,
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
    # STAIRCASE EARLY OVERLAP BEARISH
    # =====================================================
    # # here there could be no gaps or atmost one gap between ibs

    if (
        ib1["low"] > ib8["high"]
        and ib18["low"] < ib1["high"] < ib18["high"]
        and ib1["low"] < ib18["low"]
    ):

        return {
            "structure_name": "staircase_early_overlap_bearish",
            "category": "bearish_acceptance",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "strong",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": True,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "compression_range": {
                "high": ib18["high"],
                "low": ib1["low"],
                "ce": (ib18["high"] + ib1["low"]) / 2
            },
            "range": {
                "high": ib1["high"],
                "low": ib8["low"],
                "ce": (ib1["high"] + ib8["low"]) / 2
            },
            # ib8 is detached from ib1, so assigning equilibrium range as IB8 range for now. update later
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib8["low"],
                "ce": (ib8["high"] + ib8["low"]) / 2
            },
            "mitigation_level": (ib1["high"] + ib8["low"]) / 2,
            "note_internal":
                "Bearish staircasing continued overnight, "
                "with strengthening migration during premarket",
                
            "note":
                "Gradual bearish migration during asia and london sessions with increased migration strength by premarket."
        }
    
    # =====================================================
    # STAIRCASE LATE OVERLAP BEARISH
        # Environment - Bearish migration weakening slightly.
        # Default Direction - bearish favored
        # Default Ping Type - Rocket continuation
        # Required Confirmations
            # sweep of overlap equilibrium
            # bearish equilibrium rejection
            # preserved migration
        # Notes
            # Can reverse if ATR exhausted.
            # Late overlap turns the newest overlap region into the continuation mitigation battlefield
            # Early overlap means migration strengthened later — late overlap means migration weakened later
            # ATR exhausted
                # Ping Rocket
            # ATR not exhausted
                # mini longs (not ping) if ib8 low is swept before 9:30, expect price to move to equilibrium of ib18-ib8 range
                # if ib8 low not swept, look for continuation short (ping flush) from equilibrium
    # =====================================================

    if (
        ib18["low"] > ib1["high"]
        and ib1["low"] < ib8["high"] < ib1["high"]
        and ib8["low"] < ib1["low"]
    ):

        return {
            "structure_name": "staircase_late_overlap_bearish",
            "category": "bearish_acceptance",
            "direction": "bearish",
            "is_staircase": False,
            "is_compression": True,
            "is_strong_compression": False,
            "compression_strength": "moderate",
            "is_acceptance": True,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "compression_range" : {
                "high": ib1["high"],
                "low": ib8["low"],
                "ce": (ib1["high"] + ib8["low"]) / 2
            },
            "range": {
                "high": ib18["high"],
                "low": ib8["low"],
                "ce": (ib18["high"] + ib8["low"]) / 2
            },
            # ib8 is attached to ib1 with weak compression, so assigning equilibrium range as overlapping range.
            # weak compression, mitigation happens in equilibrium zone
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib1["low"],
                "ce": (ib8["high"] + ib1["low"]) / 2
            },
            # retracemenet level
            "mitigation_level": (ib18["high"] + ib8["low"]) / 2,
            "note_internal":
                "Bearish staircasing continued overnight, "
                "with weakened migration strength by premarket",
                
            "note":
                "Gradual bearish migration during asia and london sessions with weakened migration strength by premarket."
        }
    
    # =====================================================
    # STAIRCASE BULLISH
    # =====================================================
    # here there could be no gaps between ibs
    # continuous overlap bullish migration and equilibrium constantly rebuilding upward
    # Continuous overlap migration favors exhaustion reversals more than explosive continuation
    # this structure generates low resistance liquidity runs, most likely sweep upside and flush at atr exhaustion or with smt
    # ib8 > ib1 > ib18
    # compression and equilibrium ranges are from weak compression due to overlap of ib8 and ib1
    # equilibrium or trigger zone: the latest overlap region between IB1 and IB8
    # The newest overlap region is where the next directional release gets decided

    if (
        ib18["low"] < ib1["low"] < ib18["high"] and ib1["high"] > ib18["high"]
        and ib1["low"] < ib8["low"] < ib1["high"]
        and ib1["high"] < ib8["high"]
    ):

        return {
            "structure_name": "staircase_bullish",
            "category": "acceptance",
            "direction": "bullish",
            "is_staircase": True,
            "migration_strength": "moderate",
            "is_compression": True,
            "is_strong_compression": False,
            "compression_strength": "weak",
            "is_acceptance": True,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "compression_range": {
                "high": ib8["high"],
                "low": ib1["low"],
                "ce": (ib8["high"] + ib1["low"]) / 2
            },
            "range": {
                "high": ib8["high"],
                "low": ib18["low"],
                "ce": (ib8["high"] + ib18["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib1["high"],
                "low": ib8["low"],
                "ce": (ib1["high"] + ib8["low"]) / 2
            },
            # mitigation happens at compression zone, here at overlap of ib1 and ib8
            "mitigation_level": (ib8["high"] + ib18["low"]) / 2,
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
    # In overlap migration structures, acceptance below transition equilibrium 
        #  often marks the shift from mitigation into migration
    if (
        ib18["high"] > ib1["high"] > ib18["low"] and ib1["low"] < ib18["low"]
        and ib1["high"] > ib8["high"] > ib1["low"]
        and ib1["low"] > ib8["low"]
    ):

        return {
            "structure_name": "staircase_bearish",
            "category": "acceptance",
            "direction": "bearish",
            "is_staircase": True,
            "migration_strength": "moderate",
            "is_compression": True,
            "is_strong_compression": False,
            "compression_strength": "weak",
            "is_acceptance": True,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "compression_range": {
                "high": ib1["high"],
                "low": ib8["low"],
                "ce": (ib1["high"] + ib8["low"]) / 2
            },
            "range": {
                "high": ib18["high"],
                "low": ib8["low"],
                "ce": (ib18["high"] + ib8["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib1["low"],
                "ce": (ib8["high"] + ib1["low"]) / 2
            },
            # mitigation happens at compression zone, here at overlap of ib1 and ib8
            "mitigation_level": (ib18["high"] + ib8["low"]) / 2,
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
    # Ongoing directional probing is weaker than late staricase overlap bullish structure

    if (
        ib1_above_ib18
        and ib8_inside_ib1
    ):

        return {
            "structure_name": "bullish_acceptance_compression",
            "category": "bullish_acceptance",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": True,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "compression_range": {
                "high": ib1["high"],
                "low": ib1["low"],
                "ce": (ib1["high"] + ib1["low"]) / 2
            },
            "range": {
                "high": ib1["high"],
                "low": ib18["low"],
                "ce": (ib1["high"] + ib18["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib8["low"],
                "ce": (ib8["high"] + ib8["low"]) / 2
            },
            # mitigation happens at compression zone, here at IB1 range which is the latest acceptance probe
            # mitigation at equilibrium and compression extremes
            "mitigation_level": (ib1["low"] + ib18["high"]) / 2,
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
            "structure_name": "bearish_acceptance_compression",
            "category": "bearish_acceptance",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": True,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "compression_range": {
                "high": ib1["high"],
                "low": ib1["low"],
                "ce": (ib1["high"] + ib1["low"]) / 2
            },
            "range": {
                "high": ib18["high"],
                "low": ib1["low"],
                "ce": (ib18["high"] + ib1["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib8["low"],
                "ce": (ib8["high"] + ib8["low"]) / 2
            },
            # mitigation happens at compression zone, here at IB1 range which is the latest acceptance probe
            "mitigation_level": (ib18["high"] + ib1["low"]) / 2,
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
            "structure_name": "bullish_rebalance_compression",
            "category": "rebalance",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "strong",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": False,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": True,
            "is_value_flip": False,
            "compression_range": {
                "high": ib18["high"],
                "low": ib18["low"],
                "ce": (ib18["high"] + ib18["low"]) / 2
            },
            "range": {
                "high": ib1["high"],
                "low": ib18["low"],
                "ce": (ib1["high"] + ib18["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib8["low"],
                "ce": (ib8["high"] + ib8["low"]) / 2
            },
            # mitigation is eq of migration level = mid of IB18 and IB1
            "mitigation_level": (ib1["high"] + ib18["low"]) / 2,
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
            "structure_name": "bearish_rebalance_compression",
            "category": "rebalance",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "strong",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": False,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": True,
            "is_value_flip": False,
            "compression_range": {
                "high": ib18["high"],
                "low": ib18["low"],
                "ce": (ib18["high"] + ib18["low"]) / 2
            },
            "range": {
                "high": ib18["high"],
                "low": ib1["low"],
                "ce": (ib18["high"] + ib1["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib8["low"],
                "ce": (ib8["high"] + ib8["low"]) / 2
            },
            "mitigation_level": (ib18["high"] + ib1["low"]) / 2,
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
        (ib1_above_ib18 or ib1["low"] <= ib18["high"] <= ib1["high"])
        and ib18["low"] < ib8["high"] < ib18["high"]
        and ib8["low"] < ib18["low"]
    ):

        return {
            "structure_name": "bullish_reintegration",
            "category": "reintegration",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "strong",
            "is_compression": True,
            "is_strong_compression": False,
            "compression_strength": "weak",
            "is_acceptance": False,
            "is_reintegration": True,
            "is_rebalance": False,
            "is_decompression": False,
            "is_value_flip": False,
            "compression_range": {
                "high": ib18["high"],
                "low": ib8["low"],
                "ce": (ib18["high"] + ib8["low"]) / 2
            },
            # range is migration range
            "range": {
                "high": ib1["high"],
                "low": ib8["low"],
                "ce": (ib1["high"] + ib8["low"]) / 2
            },
            # equilibrium range is the mitigation range. 
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib18["low"],
                "ce": (ib8["high"] + ib18["low"]) / 2
            },
            "mitigation_level": (ib1["high"] + ib8["low"]) / 2,
            
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
        (ib1_below_ib18 or ib1["high"] >= ib18["low"] >= ib1["low"])
        and ib18["high"] > ib8["low"] > ib18["low"]
        and ib8["high"] > ib18["high"]
    ):

        return {
            "structure_name": "bearish_reintegration",
            "category": "reintegration",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "strong",
            "is_compression": True,
            "is_strong_compression": False,
            "compression_strength": "weak",
            "is_acceptance": False,
            "is_reintegration": True,
            "is_rebalance": False,
            "is_decompression": False,
            "is_value_flip": False,
            
            # range is compression range is there is one, otherwise displacement or migration range
            "range": {
                "high": ib8["high"],
                "low": ib18["low"],
                "ce": (ib8["high"] + ib18["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib18["high"],
                "low": ib8["low"],
                "ce": (ib18["high"] + ib8["low"]) / 2
            },
            "mitigation_level": (ib18["high"] + ib8["low"]) / 2,
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
    # Value flip is not just reversal — it is completed opposite-side value migration
    # =====================================================
    

    if (
        ib1_above_ib18
        and ib8["high"] < ib18["low"]
    ):

        return {
            "structure_name": "bullish_value_flip",
            "category": "value_flip",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "very_strong",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": True,
            "is_reintegration": False,
            "is_value_flip": True,
            "is_rebalance": False,
            "is_decompression": False,
            "compression_range": {
                "high": None, 
                "low": None, 
                "ce": None
                },
            "range": {
                "high": ib1["high"], 
                "low": ib8["low"], 
                "ce": (ib1["high"] + ib8["low"]) / 2
                },
            "equilibrium_range": {
                "high": ib18["low"], 
                "low": ib8["high"], 
                "ce": (ib18["low"] + ib8["high"]) / 2
                },
            "mitigation_level": ib18["low"],
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
            "structure_name": "bearish_value_flip",
            "category": "value_flip",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "very_strong",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": True,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": True,
            "is_decompression": False,
            "compression_range": {"high": None, "low": None, "ce": None},
            "range": {"high": ib8["high"], "low": ib1["low"], "ce": (ib8["high"] + ib1["low"]) / 2},
            "equilibrium_range": {"high": ib8["low"], "low": ib18["high"], "ce": (ib8["low"] + ib18["high"]) / 2},
            "mitigation_level": ib18["high"],
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
    # In sandwich structures, IB8 defines the active compression range while the larger gap
        # defines migration equilibrium

    if (
        ib1_above_ib18
        and ib8["high"] < ib1["low"]
        and ib8["low"] > ib18["high"]
    ):

        return {
            "structure_name": "sandwich_gap_bullish",
            "category": "balanced_compression",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "is_decompression": False,
            "compression_range": {
                "high": ib8["high"],
                "low": ib8["low"],
                "ce": (ib8["high"] + ib8["low"]) / 2
            },
            "range": {
                "high": ib1["high"],
                "low": ib18["low"],
                "ce": (ib1["high"] + ib18["low"]) / 2
            },

            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib8["low"],
                "ce": (ib8["high"] + ib8["low"]) / 2

            },
            "mitigation_level": (ib1["high"] + ib18["low"]) / 2,
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
            "structure_name": "sandwich_gap_bearish",
            "category": "balanced_compression",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "is_decompression": False,
            "compression_range": {
                "high": ib8["high"],
                "low": ib8["low"],
                "ce": (ib8["high"] + ib8["low"]) / 2
            },
            "range": {
                "high": ib18["high"],
                "low": ib1["low"],
                "ce": (ib18["high"] + ib1["low"]) / 2
            },

            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib8["low"],
                "ce": (ib8["high"] + ib8["low"]) / 2

            },
            "mitigation_level": (ib18["high"] + ib1["low"]) / 2,
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
    # Partial overlap means equilibrium has already started accepting the higher value region
    # =====================================================
    
    if (
        ib1_above_ib18
        and  ib1["low"] < ib8["high"] < ib1["high"]
        and ib8["low"] > ib18["high"]
    ):

        return {
            "structure_name": "sandwich_partial_overlap_bullish",
            "category": "balanced_compression",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": True,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "is_decompression": False,
            "compression_range": {
                "high": ib1["high"],
                "low": ib8["low"],
                "ce": (ib1["high"] + ib8["low"]) / 2
            },
            "range": {
                "high": ib1["high"],
                "low": ib18["low"],
                "ce": (ib1["high"] + ib18["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib1["low"],
                "ce": (ib8["high"] + ib1["low"]) / 2
            },
            # mitigation is inside compression zone but our mitigation level is at migration equilibrium
            "mitigation_level": (ib1["high"] + ib18["low"]) / 2,
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
            "structure_name": "sandwich_partial_overlap_bullish",
            "category": "balanced_compression",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": False,
            "is_reintegration": False,
            "is_rebalance": True,
            "is_value_flip": False,
            "is_decompression": False,
            "compression_range": {
                "high": ib8["high"],
                "low": ib18["low"],
                "ce": (ib8["high"] + ib18["low"]) / 2
            },
            "range": {
                "high": ib1["high"],
                "low": ib18["low"],
                "ce": (ib1["high"] + ib18["low"]) / 2
            },
            # mitigation inside compression zone or trigger zone
            "equilibrium_range": {
                "high": ib18["high"],
                "low": ib8["low"],
                "ce": (ib18["high"] + ib8["low"]) / 2
            },
            # mitigation = migration eq
            "mitigation_level": (ib1["high"] + ib18["low"]) / 2,
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
            "structure_name": "sandwich_partial_overlap_bearish",
            "category": "balanced_compression",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": True,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "is_decompression": False,
            "compression_range": {
                "high": ib8["high"],
                "low": ib1["low"],
                "ce": (ib8["high"] + ib1["low"]) / 2
            },
            "range": {
                "high": ib18["high"],
                "low": ib1["low"],
                "ce": (ib18["high"] + ib1["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib1["high"],
                "low": ib8["low"],
                "ce": (ib1["high"] + ib8["low"]) / 2
            },
            "mitigation_level": (ib18["high"] + ib1["low"]) / 2,
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
            "structure_name": "sandwich_partial_overlap_bearish",
            "category": "balanced_compression",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": False,
            "is_reintegration": False,
            "is_rebalance": True,
            "is_value_flip": False,
            "is_decompression": False,
            "compression_range": {
                "high": ib18["high"],
                "low": ib8["low"],
                "ce": (ib18["high"] + ib8["low"]) / 2
            },
            "range": {
                "high": ib18["high"],
                "low": ib1["low"],
                "ce": (ib18["high"] + ib1["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib18["low"],
                "ce": (ib8["high"] + ib18["low"]) / 2
            },
            "mitigation_level": (ib18["high"] + ib1["low"]) / 2,
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
            "structure_name": "sandwich_overlap_bullish",
            "category": "balanced_compression",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": True,
            "is_reintegration": False,
            "is_rebalance": True,
            "is_value_flip": False,
            "is_decompression": False,
            "compression_range": {
                "high": ib1["high"],
                "low": ib18["low"],
                "ce": (ib1["high"] + ib18["low"]) / 2
            },
            "range": {
                "high": ib1["high"],
                "low": ib18["low"],
                "ce": (ib1["high"] + ib18["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib8["low"],
                "ce": (ib8["high"] + ib8["low"]) / 2
            },
            "mitigation_level": (ib8["high"] + ib8["low"]) / 2,
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
            "structure_name": "sandwich_overlap_bearish",
            "category": "balanced_compression",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": True,
            "is_reintegration": False,
            "is_rebalance": True,
            "is_value_flip": False,
            "is_decompression": False,
            "compression_range": {
                "high": ib18["high"],
                "low": ib1["low"],
                "ce": (ib18["high"] + ib1["low"]) / 2
            },
            "range": {
                "high": ib18["high"],
                "low": ib1["low"],
                "ce": (ib18["high"] + ib1["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib8["low"],
                "ce": (ib8["high"] + ib8["low"]) / 2
            },
            "mitigation_level": (ib18["high"] + ib1["low"]) / 2,
            "note_internal":
                "Balanced bearish sandwich compression.",
            "note": 
                "Price is consolidating at eq of asia-london range after bearish move in asia."
        }
    # =====================================================
    # SANDWICH BULLISH
    # all ibs overlapping with each other with no gaps between them
    # tight and energetic compression with explosive move after sweep of compression extremes
    # here the mitigation level is at the extremes of 8am ib range, 
    # =====================================================

    if (
        ib1["high"] >  ib18["high"] and ib18["low"] < ib1["low"] < ib18["high"]
        and ib1["low"] < ib8["high"] < ib1["high"]
        and ib18["high"] > ib8["low"] > ib18["low"]
    ):

        return {
            "structure_name": "sandwich_bullish",
            "category": "compression",
            "direction": "neutral",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": False,
            "compression_strength": "strong",
            "is_acceptance": True,
            "is_rebalance": True,
            "is_reintegration": False,
            "is_value_flip": False,
            "is_decompression": False,
            "range": {
                "high": ib1["high"],
                "low": ib18["low"],
                "ce": (ib1["high"] + ib18["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib8["low"],
                "ce": (ib8["high"] + ib8["low"]) / 2
            },
            "mitigation_level": (ib8["high"] + ib8["low"]) / 2,
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
            "structure_name": "sandwich_bearish",
            "category": "compression",
            "direction": "neutral",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": True,
            "is_rebalance": True,
            "is_reintegration": False,
            "is_value_flip": False,
            "is_decompression": False,
            "compression_range": {
                "high": ib18["high"],
                "low": ib1["low"],
                "ce": (ib18["high"] + ib1["low"]) / 2
            },
            "range": {
                "high": ib18["high"],
                "low": ib1["low"],
                "ce": (ib18["high"] + ib1["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib8["low"],
                "ce": (ib8["high"] + ib8["low"]) / 2
            },
            "mitigation_level": (ib18["high"] + ib1["low"]) / 2,
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
            "structure_name": "centered_compression",
            "category": "compression",
            "direction": "neutral",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": False,
            "is_rebalance": False,
            "is_reintegration": False,
            "is_value_flip": False,
            "is_decompression": False,
            "range": {"high": ib18["high"], "low": ib18["low"], "ce": (ib18["high"] + ib18["low"]) / 2},
            "equilibrium_range": {"high": ib1["high"], "low": ib1["low"], "ce": (ib1["high"] + ib1["low"]) / 2},
            "mitigation_level": (ib1["high"] + ib1["low"]) / 2,
            "notes_internal": "IB1 inside IB18 with midpoints within 15% of IB18 range.",
            "note":
                "Tight consolidation inside larger asia range."
        }

    # =====================================================
    # DEFAULT
    # =====================================================

    return {
        "structure_name": "mixed_overlap",
        "category": "mixed",
        "direction": "neutral",
        "is_staircase": False,
        "range": {"high": None, "low": None, "ce": None},
        "equilibrium_range": {"high": None, "low": None, "ce": None},
        "mitigation_level": None,
        "note":
            "Mixed overlap structure. "
            "Directional conviction unclear."
    }




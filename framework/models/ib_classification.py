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

    TODO: RECOMPRESSION
    -----------
    # recompression in london session after early decompression — weak migration strength
    #  but strong compression strength. need to define rules for this.

    DEFAULT
    -------
    mixed_overlap
    """

    # =====================================================
    # HELPERS
    # =====================================================
    def get_structure_phase(name):
        structure_name = name
        # Auction Phase (Compression → Early Expansion → Migration → Late Expansion)

        if structure_name in {
            # migrating weak compression
            "staircase_bullish",
            "staircase_bearish",

            "sandwich_bullish",
            "sandwich_bearish",

            "sandwich_gap_bullish",
            "sandwich_gap_bearish",

            "sandwich_overlap_bullish",
            "sandwich_overlap_bearish",

            "sandwich_partial_overlap_bullish",
            "sandwich_partial_overlap_bearish",

            "bullish_acceptance_compression",
            "bearish_acceptance_compression",

            "bullish_rebalance_compression",
            "bearish_rebalance_compression",

            "sandwich_neutral_recompression",
            
        }:
            return "compression"

        if structure_name in {
            "staircase_gap_bullish",
            "staircase_gap_bearish",

            "staircase_early_overlap_bullish",
            "staircase_early_overlap_bearish",

            "staircase_late_overlap_bullish",
            "staircase_late_overlap_bearish",
        }:
            return "migration"

        if structure_name in {

            "bullish_early_decompression",
            "bearish_early_decompression",
            "bullish_early_compression",
            "bearish_early_compression",
        }:
            return "migration"

        if structure_name in {
            "bullish_macro_decompression",
            "bearish_macro_decompression",
            "bullish_decompression",
            "bearish_decompression",
            "bullish_mixed_decompression",
            "bearish_mixed_decompression",
        }:
            return "early_expansion"

        if structure_name in {
            "bullish_reintegration",
            "bearish_reintegration",
        }:
            return "migration"

        if structure_name in {
            "bullish_value_flip",
            "bearish_value_flip",
        }:
            return "migration"
        
        return "compression"
    
    def get_auction_phase(name):
        structure_name = name
        # Auction Phase (Waiting → Early → Mid → Late → Completion)

        if structure_name in {
            
            "staircase_bullish",
            "staircase_bearish",

            "sandwich_bullish",
            "sandwich_bearish",

            "sandwich_gap_bullish",
            "sandwich_gap_bearish",

            "sandwich_overlap_bullish",
            "sandwich_overlap_bearish",

            "sandwich_partial_overlap_bullish",
            "sandwich_partial_overlap_bearish",

            "bullish_acceptance_compression",
            "bearish_acceptance_compression",

            "bullish_rebalance_compression",
            "bearish_rebalance_compression",

            "sandwich_neutral_recompression",
            
        }:
            return "waiting"

        if structure_name in {
            "staircase_gap_bullish",
            "staircase_gap_bearish",

            "staircase_early_overlap_bullish",
            "staircase_early_overlap_bearish",

            "staircase_late_overlap_bullish",
            "staircase_late_overlap_bearish",
        }:
            return "mid expansion"
        
        if structure_name in {
            "staircase_gap_bullish",
            "staircase_gap_bearish",

            "staircase_early_overlap_bullish",
            "staircase_early_overlap_bearish",

            "staircase_late_overlap_bullish",
            "staircase_late_overlap_bearish",
        }:
            return "mid expansion"

        if structure_name in {

            "bullish_early_decompression",
            "bearish_early_decompression",
            "bullish_early_compression",
            "bearish_early_compression",
        }:
            return "mid expansion"

        if structure_name in {
            "bullish_macro_decompression",
            "bearish_macro_decompression",
            "bullish_decompression",
            "bearish_decompression",
            "bullish_mixed_decompression",
            "bearish_mixed_decompression",
        }:
            return "early expansion"

        if structure_name in {
            "bullish_reintegration",
            "bearish_reintegration",
        }:
            return "mid expansion"

        if structure_name in {
            "bullish_value_flip",
            "bearish_value_flip",
        }:
            return "expansion mid"
        
        return "mid expansion"
    
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
    # NEUTRAL DIRECTIONAL STRUCTURES
    # =====================================================
    NEUTRAL_DIRECTION_STRUCTURES = {
        "sandwich_bullish",
        "sandwich_bearish",

        "sandwich_gap_bullish",
        "sandwich_gap_bearish",

        "sandwich_overlap_bullish",
        "sandwich_overlap_bearish",

        "sandwich_partial_overlap_bullish",
        "sandwich_partial_overlap_bearish",

        "bullish_rebalance_compression",
        "bearish_rebalance_compression",

        "sandwich_neutral_recompression"
    }

    # =====================================================
    # ENGULFING (highest priority)
    # One Line Rule:
       # Decompression outside value suggests continuation — decompression through value suggests conflict
        # Compression structures ask:
        # Which side will resolve first?
        # Decompression structures ask:
        # Which side still has room to expand?
        # That is a different question.
        # So your observation can be generalized:
        # A decompression structure should prefer the direction that still has meaningful delivery capacity.
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
        and (
            ib8["low"] > ib18["high"] or ib18["high"] > ib8["low"] > ib18["low"]
        )
    ):
        name = None
        group = "decompression"
        name = "bullish_decompression"
        doji_text = "The market has transitioned into early expansion after a accepting higher prices but direction remains unconfirmed. Expect the first qualified pre-market structure to establish the direction of today's expansion."
        expected_delivery = "Expect continuation in the direction of the pre-market displacement following a retracement into mitigation."
        
        if ib8["acceptance"] == "neutral":
            expected_delivery = doji_text
        
        return {
            "execution_edge": 90,
            "direction_score": 85,
            "migration_score": 90,
            "pqs": 89,
            "reaction_levels": {"Pre-market 30m Bullish OB", "Pre-market Lows", "Pre-market Gap"},
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "decompression",
            "category": "decompression",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "neutral",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,

            "is_acceptance": True,
            "is_decompression": True,
            "is_compression_resolution": True,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            
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
                "high": ib1["high"],
                "low": ib1["low"],
                "ce": (ib1["high"] + ib1["low"]) / 2
            },
            "mitigation_level": (ib8["high"] + ib18["low"]) / 2,

            "note_internal":
                "8AM IB engulfed 1AM IB above 18 IB. "
                "Bullish volatility expansion above prior value.",

            "note":
                "Bullish decompression before NY open. "
                "Higher pricing accepted.",
            "context_summary": {
                "market_state":
                    "Price migrated higher during London before returning into the London range. During the pre-market session both sides of London liquidity were swept, transitioning the market from compression into expansion.",

                "expected_delivery": expected_delivery,

                "trade_focus":
                    "Focus on 30m structure formed during the pre-market expansion and their mitigation levels."
            }
        }
    # =====================================================
    # BEARISH DECOMPRESSION
    # =====================================================

    if (
        ib8_engulf_ib1
        and ib1_below_ib18
        and (
            ib8["high"] < ib18["low"] 
            or ib18["low"] < ib8["high"] < ib18["high"]
            )
    ):
        name = None
        group = "decompression"
        name = "bearish_decompression"
        doji_text = "The market has transitioned into early expansion after a accepting lower prices but direction remains unconfirmed. Expect the first qualified pre-market structure to establish the direction of today's expansion."
        expected_delivery = "Expect continuation in the direction of the pre-market displacement following a retracement into mitigation."
        
        if ib8["acceptance"] == "neutral":
            expected_delivery = doji_text
        return {
            "execution_edge": 90,
            "direction_score": 85,
            "migration_score": 90,
            "pqs": 89,
            "reaction_levels": {"Pre-market 30m Bearish OB", "Pre-market Highs", "Pre-market Gap"},
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "decompression",
            "category": "decompression",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "neutral",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": True,
            "is_decompression": True,
            "is_compression_resolution": True,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            # no compression
            
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
                "high": ib1["high"],
                "low": ib1["low"],
                "ce": (ib1["high"] + ib1["low"]) / 2
            },
            "mitigation_level": (ib18["high"] + ib8["low"]) / 2,

            "note_internal":
                "8AM IB engulfed 1AM IB below 18 IB. "
                "Bearish volatility expansion below prior value.",

            "note":
                "Bearish decompression before NY open. "
                "Lower pricing accepted.",
            "context_summary": {
                "market_state":
                    "Price migrated lower during London before returning into the London range. During the pre-market session both sides of London liquidity were swept, transitioning the market from compression into expansion.",

                "expected_delivery": expected_delivery,

                "trade_focus":
                    "Focus on 30m structure formed during the pre-market expansion and their mitigation levels."
            }
        }
    # =====================================================
    # BULLISH MIXED DECOMPRESSION
    # =====================================================

    if (
        ib8_engulf_ib1 
        and ib18["low"] < ib1["low"] < ib18["high"] 
        and ib18["high"] < ib1["high"]
    ):
        name = None
        group = "decompression"
        name = "bullish_mixed_decompression"
        return {
            "execution_edge": 0,
            "direction_score": 0,
            "migration_score": 0,
            "pqs": 70,
            "reaction_levels": None,
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "decompression",
            "category": "decompression",
            "direction": "neutral",
            "is_staircase": False,
            "migration_strength": "neutral",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": False,
            "is_decompression": True,
            "is_compression_resolution": True,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "compression_range": {
                "high": ib8["high"],
                "low": ib18["low"],
                "ce": (ib8["high"] + ib18["low"]) / 2
            },
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
            "mitigation_level": (ib1["high"] + ib1["low"]) / 2,

            "note_internal":

                "8AM IB engulfed 1AM IB overlapping prior value. "
                "Continuation vs reversal unresolved. "
                "Mixed decompression before NY open.",

            "note":
                "Early expansion before NY open with unresolved direction, continuation vs reversal. "
                "Liquidity event likely before direction.",
            "context_summary": {
                "market_state":
                    "Price migrated higher during London before returning into the London range. During the pre-market session both sides of London liquidity were swept, transitioning the market from compression into expansion.",

                "expected_delivery":
                    "Expect retracements into pre-market mitigation levels before delivery continues in the direction of 30m structure",

                "trade_focus":
                    "Focus on 30m structure formed during the pre-market expansion and their mitigation levels."
            }
        }
    # =====================================================
    # BEARISH MIXED DECOMPRESSION
    # =====================================================

    if ib8_engulf_ib1 and ib18["low"] < ib1["high"] < ib18["high"] and ib18["low"] > ib1["low"]:

        name = None
        group = "decompression"
        name = "bearish_mixed_decompression"
        return {
            "execution_edge": 0,
            "direction_score": 0,
            "migration_score": 0,
            "pqs": 70,
            "reaction_levels": None,
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "decompression",
            "category": "decompression",
            "direction": "neutral",
            "is_staircase": False,
            "migration_strength": "neutral",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": False,
            "is_decompression": True,
            "is_compression_resolution": True,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            
            "compression_range": {
                "high": ib18["high"],
                "low": ib1["low"],
                "ce": (ib18["high"] + ib1["low"]) / 2
            },
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
            "mitigation_level": (ib1["high"] + ib1["low"]) / 2,

            "note_internal":

                "8AM IB engulfed 1AM IB overlapping prior value. "
                "Continuation vs reversal unresolved. ",
                "Mixed decompression before NY open."

            "note":
                "Early expansion before NY open with unresolved direction, continuation vs reversal. "
                "Liquidity event likely before direction.",
            
            "context_summary": {
                "market_state":
                    "Price migrated lower during London before returning into the London range. During the pre-market session both sides of London liquidity were swept, transitioning the market from compression into expansion.",

                "expected_delivery":
                    "Expect retracements into pre-market mitigation levels before delivery continues in the direction of 30m structure",

                "trade_focus":
                    "Focus on 30m structure formed during the pre-market expansion and their mitigation levels."
            }
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
        name = None
        group = "decompression"
        name = "bullish_macro_decompression"
        doji_text = "The market has transitioned into expansion after a complete rebalance of the overnight range. Direction remains unconfirmed. Expect the first qualified pre-market structure to establish the direction of today's expansion."
        expected_delivery = "The market has transitioned into early expansion after a complete rebalance of the overnight range. Expect continuation in the direction of the pre-market displacement following a retracement into mitigation."
        if ib8["acceptance"] == "neutral":
            expected_delivery = doji_text
        return {
            "execution_edge": 100,
            "direction_score": 55,
            "migration_score": 60,
            "pqs": 82,
            "reaction_levels": {"DO", "Pre-market Highs", "Pre-market 30m Bearish OB"},
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "decompression",
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
            "is_compression_resolution": True,
            "is_reintegration": True,
            "is_value_flip": False,
            
            "compression_range": {
                "high": None,
                "low": None,
                "ce": None
            },
            # entire range from ib1 high to ib8 low
            "range": {
                "high": ib1["high"],
                "low": ib8["low"],
                "ce": (ib1["high"] + ib8["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib18["low"],
                "low": ib18["high"],
                "ce": (ib18["low"] + ib18["high"]) / 2
            },
            # mid point between ib1 and ib18
            "mitigation_level": (ib1["low"] + ib18["high"]) / 2,

            "note_internal":
                "8AM IB engulfed overnight value after bullish separation. "
                "Volatility expanded aggressively around prior value.",

            "note":
                "Large price swings developed before NY open. "
                "Expect volatile conditions until direction becomes clearer.",
            "context_summary": {
                "market_state":
                    "Price migrated higher during London before the pre-market session expanded through both sides of the overnight range, rebalancing the earlier migration.",
                "expected_delivery": expected_delivery,
                "trade_focus":
                    "Focus on 30m structure formed during the pre-market expansion, overnight equilibrium and mitigation levels."
            }
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
            # "is_compression_resolution": False,
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

        name = None
        group = "decompression"
        name = "bearish_macro_decompression"
        doji_text = "The market has transitioned into expansion after a complete rebalance of the overnight range. Direction remains unconfirmed. Expect the first qualified pre-market structure to establish the direction of today's expansion."
        expected_delivery = "The market has transitioned into early expansion after a complete rebalance of the overnight range. Expect continuation in the direction of the pre-market displacement following a retracement into mitigation."
        if ib8["acceptance"] == "neutral":
            expected_delivery = doji_text
        
        return {
            "execution_edge": 100,
            "direction_score": 55,
            "migration_score": 60,
            "pqs": 82,
            "reaction_levels": {"DO", "Pre-market Lows", "Pre-market 30m Bullish OB"},
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "decompression",
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
            "is_compression_resolution": True,
            "is_reintegration": True,
            "is_value_flip": False,
            
            "compression_range": {
                "high": None,
                "low": None,
                "ce": None
            },
            "range": {
                "high": ib8["high"],
                "low": ib1["low"],
                "ce": (ib8["high"] + ib1["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib18["low"],
                "low": ib18["high"],
                "ce": (ib18["low"] + ib18["high"]) / 2
            },
            # mid point between ib1 and ib18
            "mitigation_level": (ib8["low"] + ib1["high"]) / 2,

            "note_internal":
                "8AM IB engulfed overnight value after bearish separation. "
                "Volatility expanded aggressively around prior value.",

            "note":
                "Large price swings developed before NY open. "
                "Expect volatile conditions until direction becomes clearer.",
            "context_summary": {
                "market_state":
                    "Price migrated lower during London before the pre-market session expanded through both sides of the overnight range, rebalancing the earlier migration.",
                "expected_delivery": expected_delivery,
                    
                "trade_focus":
                    "Focus on 30m structure formed during the pre-market expansion, overnight equilibrium and mitigation levels."
            }
        }

    # =====================================================
    # MIXED MACRO DECOMPRESSION
        # double-sided inducement → before picking direction
    # =====================================================
    # =====================================================
    # BULLISH MIXED MACRO DECOMPRESSION
    # =====================================================

    if ib8_engulf_ib18 and ib18["low"] < ib1["low"] < ib18["high"] and ib1["high"]> ib18["high"]:
        
        name = None
        group = "decompression"
        name = "bullish_mixed_macro_decompression"

        return {
            "execution_edge": 100,
            "direction_score": 60,
            "migration_score": 70,
            "pqs": 85,
            "reaction_levels": None,
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "decompression",
            "category": "decompression",
            "direction": "neutral",
            "is_staircase": False,
            "migration_strength": "neutral",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": False,
            "is_decompression": True,
            "is_compression_resolution": True,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            
            "compression_range": {
                "high": ib1["high"],
                "low": ib18["low"],
                "ce": (ib1["high"] + ib18["low"]) / 2
            },
            "range": {
                "high":ib8["high"],
                "low": ib8["low"],
                "ce": (ib8["high"] + ib8["low"]) / 2
            },
            "equilibrium_range": {
                "high":ib18["high"],
                "low": ib18["low"],
                "ce": (ib18["high"] + ib18["low"]) / 2
            },
            "mitigation_level": (ib18["high"] + ib18["low"]) / 2,
            # TODO: review notes
            "note_internal":
                "8AM IB engulfed 18 IB from mixed positioning. "
                "Large purge of overnight value.",

            "note":
                "Mixed bias and early signs of market expansion before NY open. "
                "Liquidity purge environment.",
            "context_summary": {
                "market_state":
                    "London attempted to migrate higher but failed to establish full acceptance above the overnight range. During the pre-market session both sides of overnight liquidity were swept, creating a large expansion range.",

                "expected_delivery":
                    "The market has transitioned into expansion after sweeping both sides of overnight liquidity. Expect retracements into mitigation levels before delivery continues in the direction of the 30m structure.",

                "trade_focus":
                    "Focus on 30m structure formed during the pre-market expansion, overnight equilibrium and mitigation levels."
            }
        }
    
    # =====================================================
    # BEARISH MIXED MACRO DECOMPRESSION
    # =====================================================

    if ib8_engulf_ib18 and ib18["high"] > ib1["high"] > ib18["low"] and ib1["low"] < ib18["low"]:
        
        name = None
        group = "decompression"
        name = "bearish_mixed_macro_decompression"
        return {
            "execution_edge": 100,
            "direction_score": 60,
            "migration_score": 70,
            "pqs": 85,
            "reaction_levels": None,
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "decompression",
            "category": "decompression",
            "direction": "neutral",
            "is_staircase": False,
            "migration_strength": "neutral",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": False,
            "is_decompression": True,
            "is_compression_resolution": True,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            
            "compression_range": {
                "high": ib18["high"],
                "low": ib1["low"],
                "ce": (ib18["high"] + ib1["low"]) / 2
            },
            "range": {
                "high":ib8["high"],
                "low": ib8["low"],
                "ce": (ib8["high"] + ib8["low"]) / 2
            },
            "equilibrium_range": {
                "high":ib18["high"],
                "low": ib18["low"],
                "ce": (ib18["high"] + ib18["low"]) / 2
            },
            "mitigation_level": (ib18["high"] + ib18["low"]) / 2,
            # TODO: review notes
            "note_internal":
                "8AM IB engulfed 18 IB from mixed positioning. "
                "Large purge of overnight value.",

            "note":
                "Mixed bias and early signs of market expansion before NY open. "
                "Liquidity purge environment.",
            "context_summary": {
                "market_state":
                    "London attempted to migrate lower but failed to establish full acceptance below the overnight range. During the pre-market session both sides of overnight liquidity were swept, creating a large expansion range.",

                "expected_delivery":
                    "The market has transitioned into expansion after sweeping both sides of overnight liquidity. Expect retracements into mitigation levels before delivery continues in the direction of the 30m structure.",

                "trade_focus":
                    "Focus on 30m structure formed during the pre-market expansion, overnight equilibrium and mitigation levels."
            }
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
        name = None
        group = "decompression"
        name = "bullish_early_decompression"
        return {
            "execution_edge": 92,
            "direction_score": 85,
            "migration_score": 85,
            "pqs": 89,
            "reaction_levels": {"London Range Eq", "Pre-market Lows", "Pre-market 30m Bullish OB"},
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "decompression",
            "category": "decompression",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "strong",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": True,
            "is_decompression": False,
            "is_compression_resolution": True,
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
                "low": ib1["low"],
                "ce": (ib8["high"]+ ib1["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib8["high"], 
                "low": ib1["low"], 
                "ce": (ib8["high"]+ ib1["low"]) / 2
            },
            "mitigation_level": (ib8["low"]+ ib1["high"])/2,

            "note_internal":
                "1AM IB engulfed 18 IB and 8AM continued higher. "
                "Early bullish volatility expansion accepted.",

            "note":
                "Bullish early expansion during London session. "
                "Higher pricing accepted before NY open. Expect price to make shallow retracement towards london equilibrium or sweep of lows before continuation higher.",
            "context_summary": {
                "market_state":
                    "The market transitioned into expansion during London and continued accepting higher prices into the pre-market session.",

                "expected_delivery":
                    "Expect retracements into pre-market imbalances or mitigation levels before bullish delivery resumes toward higher objectives.",

                "trade_focus":
                    "Focus on pre-market imbalances, bullish mitigation levels and 30m bullish structure formed during the ongoing expansion."
            }
        }

    # =====================================================
    # BEARISH EARLY DECOMPRESSION
    # =====================================================

    if (
        ib1_engulf_ib18
        and ib8_below_ib1
    ):
        name = None
        group = "decompression"
        name = "bearish_early_decompression"
        return {
            "execution_edge": 92,
            "direction_score": 85,
            "migration_score": 85,
            "pqs": 89,
            "reaction_levels": {"London Range Eq", "Pre-market Highs", "Pre-market 30m Bearish OB"},
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "decompression",
            "category": "decompression",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "neutral",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": True,
            "is_decompression": False,
            "is_compression_resolution": True,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            
            "compression_range": {
                "high": None,
                "low": None,
                "ce": None
            },
            "range": {
                "high": ib1["high"], 
                "low": ib8["low"],
                "ce": (ib1["high"]+ ib8["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib1["high"], 
                "low": ib8["low"], 
                "ce": (ib1["high"]+ ib8["low"]) / 2
            },
            "mitigation_level": (ib1["high"]+ ib8["low"])/2,

            "note_internal":
                "1AM IB engulfed 18 IB and 8AM continued lower. "
                "Early bearish volatility expansion accepted.",

            "note":
                "Bearish early expansion during London session. "
                "Lower pricing accepted before NY open. Expect price to make shallow retracement towards london equilibrium or sweep of highs before continuation lower.",
            
            "context_summary": {
                "market_state":
                    "The market transitioned into expansion during London and continued accepting lower prices into the pre-market session.",

                "expected_delivery":
                    "Expect retracements into pre-market imbalances or mitigation levels before bearish delivery resumes toward lower objectives.",

                "trade_focus":
                    "Focus on pre-market imbalances, bearish mitigation levels and 30m bearish structure formed during the ongoing expansion."
            }
        }

    # =====================================================
    # MIXED EARLY DECOMPRESSION
    # When compression forms inside decompression, the market is stabilizing after volatility expansion — not yet confirming direction
    # IB8 inside IB1. ib8 neither above or below ib1
    # =====================================================

    if ib1_engulf_ib18:
        compression_range = {"high": None, "low": None, "ce": None}
        equilibrium_range = {"high": None, "low": None, "ce": None}
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
        
        name = None
        group = "decompression"
        name = "mixed_early_decompression"
        return {
            # TODO: scores
            "execution_edge": 80,
            "direction_score": 20,
            "migration_score": 20,
            "pqs": 63,
            "reaction_levels": None,
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "category": "decompression",
            "market_phase": "decompression",
            "direction": "neutral",
            "is_staircase": False,
            "migration_strength": "neutral",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": False,
            "is_decompression": False,
            "is_compression_resolution": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            
            # "compression_range": compression_range,
            compression_range: {"high": None, "low": None, "ce": None},
            "range": compression_range,
            "equilibrium_range": equilibrium_range,
            "mitigation_level": equilibrium_range["ce"],
            "note_internal":
                "1AM IB engulfed 18 IB but 8AM recompressed inside 1AM IB. ",

            "note":
                "Market stabilized after early expansion during London session. "
                "Liquidity event likely before direction.",
            
            "context_summary": {
                "market_state":
                    "The market transitioned into expansion during London but failed to accept higher or lower prices into the pre-market session.",

                "expected_delivery":
                    "Expect retracements into pre-market imbalances or mitigation levels before picking a direction.",

                "trade_focus":
                    "Focus on pre-market imbalances, mitigation levels and 30m structure formed during the ongoing expansion."
            }
        }

    # =====================================================
    # DUAL INSIDE COMPRESSION
    # =====================================================
    if (
        ib1_inside_ib18
        and ib8_inside_ib1
    ):
        name = None
        group = "compression"
        name = "dual_inside_compression"
        return {
            "execution_edge": 100,
            "direction_score": 40,
            "migration_score": 40,
            "pqs": 73,
            "reaction_levels": {"Compression Highs", "Compression Lows", "Compression CE"},
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "category": "compression",
            "market_phase": "compression",
            "direction": "neutral",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": False,
            "is_decompression": False,
            "is_compression_resolution": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            
            "compression_range": {
                "high": ib8["high"],
                "low": ib8["low"],
                "ce": (ib8["high"] + ib8["low"]) / 2
            },
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
            "mitigation_level": (ib8["high"] + ib8["low"]) / 2,
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
        name = None
        group = "acceptance"
        name = "staircase_gap_bullish"
        return {
            "execution_edge": 75,
            "direction_score": 100,
            "migration_score": 100,
            "pqs": 85,
            "reaction_levels": {"Pre-market Gap", "Pre-market lows", "Pre-market 30m OB"},
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "migration",
            "category": "bullish_acceptance",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "very_strong",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": True,
            "is_decompression": False,
            # price is migration phase
            "is_compression_resolution": True,
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
                "Market aggressively accepting higher pricing.",
            "context_summary": {
                "market_state":
                    "Price continued accepting higher prices throughout Asia and London with minimal overlap between session ranges.",

                "expected_delivery":
                    "Expect shallow retracement into overnight imbalance followed by continuation higher.",

                "trade_focus":
                    "Look for Rocket setups from gap retests and mitigation levels."
            }    
        }

    # =====================================================
    # STAIRCASE GAP BEARISH
    # =====================================================

    if (
        ib18["low"] > ib1["high"]
        and ib1["low"] > ib8["high"]
    ):
        name = None
        group = "acceptance"
        name = "staircase_gap_bearish"
        return {
            "execution_edge": 75,
            "direction_score": 100,
            "migration_score": 100,
            "pqs": 85,
            "reaction_levels": {"Pre-market Gap", "Pre-market highs", "Pre-market 30m bearish OB"},
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "migration",
            "category": "bearish_acceptance",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "very_strong",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": True,
            "is_decompression": False,
            "is_compression_resolution": True,
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
                "high": ib1["high"],
                "low": ib8["low"],
                "ce": (ib8["low"] + ib1["high"]) / 2
            },
            # mitigation level = closest imbalance
            "mitigation_level": (ib8["low"] + ib1["high"]) / 2,
            "note_internal":
                "Strong bearish staircase with gaps. "
                "Market aggressively accepting lower pricing.",
            "note":
                "Strong bearish trend with small retracements. "
                "Market aggressively accepting lower pricing.",
            "context_summary": {
                "market_state":
                    "Price continued accepting lower prices throughout Asia and London with minimal overlap between session ranges.",
                "expected_delivery":
                    "Expect shallow retracement into overnight imbalance followed by continuation lower.",
                "trade_focus":
                    "Look for shorts from pre market highs, gap retests and mitigation levels."
            }
        }

    # =====================================================
    # STAIRCASE EARLY OVERLAP BULLISH
    # Early overlap means migration strengthened later — late overlap means migration weakened later
    # =====================================================
    # here there could be no gaps or atmost one gap between ibs
    # the below two possibilities are IB1 overlapping with top if ib18 and bottom of ib18

    if (
        (
            ib8["low"] > ib1["high"]
        and ib18["high"]  > ib1["low"] >= ib18["low"]
        and ib1["high"] > ib18["high"]
        ) or (
        ib8["low"] > ib1["high"]
        and ib18["low"] > ib1["high"] <= ib18["high"]
        and ib1["low"] < ib18["low"]
        )
    ):
        name = None
        group = "acceptance"
        name = "staircase_early_overlap_bullish"
        return {
            "execution_edge": 75,
            "direction_score": 100,
            "migration_score": 100,
            "pqs": 85,
            "reaction_levels": {"Pre-market Bullish OB", "Pre-market Gap", "Pre-market Lows"},
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "migration",
            "category": "bullish_acceptance",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "strong",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": True,
            "is_decompression": False,
            "is_compression_resolution": True,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            # compression is early in london, potential long in london
            # early compression zone is also used as a target in MMXM model
            "compression_range": {
                "high": max(ib1["high"], ib18["high"]),
                "low": min(ib1["low"], ib18["low"]),
                "ce": (max(ib1["high"], ib18["high"])+min(ib1["low"], ib18["low"])) / 2
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
                "Gradual bullish migration during asia and london sessions with increased migration strength by premarket. ",
            "context_summary": {
                "market_state":
                    "Price broke higher during London and maintained acceptance above the overnight range through the pre-market session.",

                "expected_delivery":
                    "Expect retracements into overnight inefficiencies, pre-market lows or mitigation levels before bullish delivery resumes.",

                "trade_focus":
                    "Focus on pre-market lows, overnight gaps, bullish mitigation levels and rejection from retracement zones. Look for continuation setups in the direction of the overnight migration. Once upside liquidity objectives are completed, monitor for Flush setups from ATR exhaustion, SMT and HTF support levels."
            }
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
        name = None
        group = "compression"
        name = "staircase_late_overlap_bullish"
        return {
            "execution_edge": 98,
            "direction_score": 75,
            "migration_score": 70,
            "pqs": 88,
            "reaction_levels": {"Pre-market Lows", "Pre-market Gap"},
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "compression",
            "category": "bullish_acceptance",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "moderate",
            "is_compression": True,
            "is_strong_compression": False,
            "compression_strength": "weak",
            "is_acceptance": True,
            "is_decompression": False,
            "is_compression_resolution": False,
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
                "Gradual bullish migration during asia and london sessions with efficiency weakening slightly during premarket. ",
            "context_summary": {
                "market_state":
                    "Price migrated higher with efficiency weakening slightly during premarket.",

                "expected_delivery":
                    "Expect sweep of pre market highs or lows before directional expansion.",

                "trade_focus":
                    "Focus on pre market highs and lows."
            }
        }

    # =====================================================
    # STAIRCASE EARLY OVERLAP BEARISH
    # =====================================================
    # # here there could be no gaps or atmost one gap between ibs

    if (
        (
            ib8["high"] < ib1["low"]
            and ib18["low"] < ib1["high"] < ib18["high"]
            and ib1["low"] < ib18["low"]
        ) 
        or 
        (
            ib8["high"] < ib18["low"]
            and ib18["high"] > ib1["low"] > ib18["low"]
            and ib1["high"] > ib18["high"]  
        )
    ):
        name = None
        group = "acceptance"
        name = "staircase_early_overlap_bearish"
        return {
            "execution_edge": 75,
            "direction_score": 100,
            "migration_score": 100,
            "pqs": 85,
            "reaction_levels": {"Pre-market Bearish OB", "Pre-market Gap", "Pre-market Highs"},
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "migration",
            "category": "bearish_acceptance",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "strong",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": True,
            "is_decompression": False,
            "is_compression_resolution": True,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "compression_range": {
                "high": max(ib18["high"], ib1["high"]),
                "low": min(ib18["low"], ib1["low"]),
                "ce": (max(ib18["high"], ib1["high"]) + min(ib18["low"], ib1["low"])) / 2 
            },
            # "compression_range": {
            #     "high": ib18["high"],
            #     "low": ib1["low"],
            #     "ce": (ib18["high"] + ib1["low"]) / 2
            # },
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
                "Gradual bearish migration during asia and london sessions with increased migration strength by premarket.",
            "context_summary": {
                "market_state":
                    "Price broke lower during London and maintained acceptance below the overnight range through the pre-market session.",

                "expected_delivery":
                    "Expect retracements into overnight inefficiencies, pre-market highs or mitigation levels before bearish delivery resumes.",

                "trade_focus":
                    "Focus on pre-market highs, overnight gaps, bearish mitigation levels and rejection from retracement zones. Look for continuation setups in the direction of the overnight migration. Once downside liquidity objectives are completed, monitor for Rocket setups from ATR exhaustion, SMT and HTF support levels."
            }
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
        name = None
        group = "compression"
        name = "staircase_late_overlap_bearish"
        return {
            "execution_edge": 98,
            "direction_score": 75,
            "migration_score": 70,
            "pqs": 88,
            "reaction_levels": {"Pre-market Highs", "Pre-market Gap"},
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "compression",
            "category": "bearish_acceptance",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "moderate",
            "is_compression": True,
            "is_strong_compression": False,
            "compression_strength": "moderate",
            "is_acceptance": True,
            "is_decompression": False,
            "is_compression_resolution": False,
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
                "Gradual bearish migration during asia and london sessions with weakened migration strength by premarket.",
            "context_summary": {
                "market_state":
                    "Price migrated lower during asia and london sessions, with efficiency weakening slightly during premarket.",

                "expected_delivery":
                    "Expect sweep of pre market highs or lows before directional expansion.",

                "trade_focus":
                    "Focus on pre market highs and lows."
            }
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
        name = None
        group = "compression"
        name = "staircase_bullish"
        return {
            "execution_edge": 95,
            "direction_score": 65,
            "migration_score": 60,
            "pqs": 83,
            "reaction_levels": {"Pre-market Lows", "London Range EQ", "Pre-market 30m Bullish OB"},
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "compression",
            "category": "acceptance",
            "direction": "bullish",
            "is_staircase": True,
            "migration_strength": "moderate",
            "is_compression": True,
            "is_strong_compression": False,
            "compression_strength": "weak",
            "is_acceptance": True,
            "is_decompression": False,
            "is_compression_resolution": False,
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
                "Bullish trend accepting higher prices with less efficiency. ",
            "context_summary": {
                "market_state":
                    "Price consistently accepted higher prices throughout the overnight session, forming a sequence of higher highs and higher lows.",

                "expected_delivery":
                    "Expect retracements into overnight inefficiencies or pre-market lows before bullish delivery resumes toward higher objectives.",

                "trade_focus":
                    "Focus on pre-market lows, overnight gaps, bullish mitigation levels and rejection from retracement levels. At 9:30 open look for continuation higher. Wait for Ping confirmation for Flush setup upon exhaustion of ATR"
            }
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
        name = None
        group = "compression"
        name = "staircase_bearish"
        return {
            "execution_edge": 95,
            "direction_score": 65,
            "migration_score": 60,
            "pqs": 83,
            "reaction_levels": {"Pre-market Highs", "London Range EQ", "Pre-market 30m Bearish OB"},
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "compression",
            "category": "acceptance",
            "direction": "bearish",
            "is_staircase": True,
            "migration_strength": "moderate",
            "is_compression": True,
            "is_strong_compression": False,
            "compression_strength": "weak",
            "is_acceptance": True,
            "is_decompression": False,
            "is_compression_resolution": False,
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
                "Bearish trend continued accepting lower prices with less efficiency. ",
            "context_summary": {
                "market_state":
                    "Price consistently accepted lower prices throughout the overnight session, forming a sequence of lower highs and lower lows.",

                "expected_delivery":
                    "Expect retracements into overnight inefficiencies or pre-market highs before bearish delivery resumes toward lower objectives.",

                "trade_focus":
                    "Focus on pre-market highs, overnight gaps, bearish mitigation levels and rejection from retracement levels. At 9:30 open look for continuation lower. Wait for Ping confirmation for a Rocket setup upon exhaustion of ATR"
            }
        }

    # =====================================================
    # BULLISH ACCEPTANCE COMPRESSION
    # =====================================================
    # Ongoing directional probing is weaker than late staircase overlap bullish structure

    if (
        ib1_above_ib18 
        and ib8_inside_ib1 
        and ib8["low"] > ib18["high"]
    ):
        name = None
        group = "compression"
        name = "bullish_acceptance_compression"
        return {
            "execution_edge": 100,
            "direction_score": 85,
            "migration_score": 75,
            "pqs": 92.5,
            "reaction_levels": {"Pre-market Consolidation Lows"},
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "compression",
            "category": "bullish_acceptance",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": True,
            "is_decompression": False,
            "is_compression_resolution": False,
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
                "Bullish redistribution after prior expansion. Expect sweep of lows before continuation higher.",
            "context_summary": {
                "market_state":
                    "Price accepted higher prices during London and is consolidating within the higher portion of the overnight range.",

                "expected_delivery":
                    "Expect a liquidity sweep before directional expansion develops. Sell-side liquidity may be sought before bullish delivery resumes.",

                "trade_focus":
                    "Focus on local highs, overnight gaps and reactions after liquidity sweeps. A sweep of sell-side liquidity followed by rejection may provide the foundation for bullish continuation."
            }
        }

    # =====================================================
    # BEARISH ACCEPTANCE COMPRESSION
    # =====================================================

    if (
        ib1_below_ib18
        and ib8_inside_ib1
    ):
        name = None
        group = "compression"
        name = "bearish_acceptance_compression"
        return {
            "execution_edge": 100,
            "direction_score": 85,
            "migration_score": 75,
            "pqs": 92.5,
            "reaction_levels": {"Pre-market Consolidation Highs"},
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "compression",
            "category": "bearish_acceptance",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": True,
            "is_decompression": False,
            "is_compression_resolution": False,
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
                "Bearish expansion followed by compression during pre market. Expect sweep of highs before continuation lower.",
            "context_summary": {
                "market_state":
                    "Price accepted lower prices during London and is consolidating within the lower portion of the overnight range.",

                "expected_delivery":
                    "Expect a liquidity sweep before directional expansion develops. Buy-side liquidity may be sought before bearish delivery resumes.",

                "trade_focus":
                    "Focus on local highs, overnight gaps and reactions after liquidity sweeps. A sweep of buy-side liquidity followed by rejection may provide the foundation for bearish continuation."
            }
        }

    # =====================================================
    # BULLISH REBALANCE
    # =====================================================

    if (
        (ib1_above_ib18 or ib18["low"] < ib1["low"] < ib18["high"])
        and ib8_inside_ib18
    ):
        name = None
        group = "rebalance"
        name = "bullish_rebalance_compression"
        return {
            "execution_edge": 100,
            "direction_score": 50,
            "migration_score": 45,
            "pqs": 79,
            "reaction_levels": {"Pre-market Consolidation Highs", "London Range Eq", "Consolidation Lows"},
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "compression",
            "category": "rebalance",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "strong",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": False,
            "is_decompression": False,
            "is_compression_resolution": False,
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
                "Bullish expansion weakened into rebalance near daily open."    ,
            "context_summary": {
                "market_state":
                    "Price migrated higher during London but later returned back into the broader overnight range, rebalancing a significant portion of the bullish move.",

                "expected_delivery":
                    "Expect liquidity sweeps at overnight extremes before directional expansion develops. The earlier bullish migration creates a slight upside bias if sell-side liquidity is collected.",

                "trade_focus":
                    "Focus on overnight range highs and lows, overnight equilibrium and reactions after liquidity sweeps. Wait for Ping confirmation before anticipating expansion."
            }
        }

    # =====================================================
    # BEARISH REBALANCE
    # =====================================================

    if (
        (ib1_below_ib18 or ib18["low"] < ib1["high"] < ib18["high"])
        and ib8_inside_ib18
    ):
        name = None
        group = "rebalance"
        name = "bearish_rebalance_compression"
        return {
            "execution_edge": 100,
            "direction_score": 50,
            "migration_score": 45,
            "pqs": 79,
            "reaction_levels": {"Pre-market Consolidation Highs", "London Range Eq", "Consolidation Lows"},
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "compression",
            "category": "rebalance",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "strong",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": False,
            "is_decompression": False,
            "is_compression_resolution": False,
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
                "Bearish expansion weakened into rebalance at daily open.",
            "context_summary": {
                "market_state":
                    "Price migrated lower during London but later returned back into the broader overnight range, rebalancing a significant portion of the bearish move.",

                "expected_delivery":
                    "Expect liquidity sweeps at overnight extremes before directional expansion develops. The earlier bearish migration creates a slight downside bias if buy-side liquidity is collected.",

                "trade_focus":
                    "Focus on overnight range highs and lows, overnight equilibrium and reactions after liquidity sweeps. Wait for Ping confirmation before anticipating expansion."
            }
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
        name = None
        group = "reintegration"
        name = "bullish_reintegration"
        compression_range = {}
        range = {}
        equilibrium_range = {}
        if ib1_above_ib18:
            compression_range = {
                "high": ib18["high"],
                "low": ib8["low"],
                "ce": (ib18["high"] + ib8["low"]) / 2
            }
            range = {
                "high": ib1["high"],
                "low": ib8["low"],
                "ce": (ib1["high"] + ib8["low"]) / 2
            }
            equilibrium_range = {
                "high": ib8["high"],
                "low": ib18["low"],
                "ce": (ib8["high"] + ib18["low"]) / 2
            }
        else:
            compression_range = {
                "high": ib1["high"],
                "low": ib8["low"],
                "ce": (ib1["high"] + ib8["low"]) / 2
            }
            range = {
                "high": ib1["high"],
                "low": ib8["low"],
                "ce": (ib1["high"] + ib8["low"]) / 2
            }
            equilibrium_range = {
                "high": ib1["low"],
                "low": ib8["high"],
                "ce": (ib8["high"] + ib8["low"]) / 2
            }

        return {
            "execution_edge": 95,
            "direction_score": 75,
            "migration_score": 75,
            "pqs": 86,
            "reaction_levels": None,
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "reintegration",
            "category": "reintegration",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "strong" if ib1_above_ib18 else "weak",
            "is_compression": True,
            "is_strong_compression": False if ib1_above_ib18 else True,
            "compression_strength": "weak" if ib1_above_ib18 else "strong",
            "is_acceptance": False,
            "is_compression_resolution": False,
            "is_reintegration": True,
            "is_rebalance": False,
            "is_decompression": False,
            "is_value_flip": False,
            
            "compression_range": compression_range,
            # range is migration range
            "range": range,
            # equilibrium range is the mitigation range. 
            "equilibrium_range": equilibrium_range,
            "mitigation_level": (ib1["high"] + ib8["low"]) / 2,
            
            "note_internal":
                "Bullish expansion weakened into reintegration.",
            "note":
                "Bullish expansion weakened significantly. Need bullish SMT to confirm bullish continuation.",
            "context_summary": {
                "market_state":
                    "Earlier bullish delivery weakened significantly and price returned back into value.",

                "expected_delivery":
                    "Expect liquidity sweeps at pre-market extremes before the next directional move develops.",

                "trade_focus":
                    "Focus on pre-market highs, pre-market lows and London session gaps."
            }
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
        name = None
        group = "reintegration"
        name = "bearish_reintegration"
        compression_range = {}
        range = {}
        equilibrium_range = {}
        if ib1_below_ib18:
            compression_range = {
                "high": ib8["high"],
                "low": ib18["low"],
                "ce": (ib8["high"] + ib18["low"]) / 2
            }
            range = {
                "high": ib8["high"],
                "low": ib18["low"],
                "ce": (ib8["high"] + ib18["low"]) / 2
            }
            equilibrium_range = {
                "high": ib18["high"],
                "low": ib8["low"],
                "ce": (ib18["high"] + ib8["low"]) / 2
            }
        else:
            compression_range = {
                "high": ib8["high"],
                "low": ib1["low"],
                "ce": (ib8["high"] + ib1["low"]) / 2
            }
            range = {
                "high": ib8["high"],
                "low": ib1["low"],
                "ce": (ib8["high"] + ib1["low"]) / 2
            }
            equilibrium_range = {
                "high": ib1["high"],
                "low": ib8["low"],
                "ce": (ib1["high"] + ib8["low"]) / 2
            }

        return {
            "execution_edge": 95,
            "direction_score": 75,
            "migration_score": 75,
            "pqs": 86,
            "reaction_levels": None,
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "reintegration",
            "category": "reintegration",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "strong" if ib1_below_ib18 else "weak",
            "is_compression": True,
            "is_strong_compression": False if ib1_below_ib18 else True,
            "compression_strength": "weak" if ib1_below_ib18 else "strong",
            "is_acceptance": False,
            "is_compression_resolution": False,
            "is_reintegration": True,
            "is_rebalance": False,
            "is_decompression": False,
            "is_value_flip": False,
            
            # range is compression range is there is one, otherwise displacement or migration range
            
            "compression_range": compression_range,
            "range": range,
            "equilibrium_range": equilibrium_range,
            "mitigation_level": (ib18["high"] + ib8["low"]) / 2,
            "note_internal":
                "Bearish expansion weakened into reintegration.",
            "note":
                "Bearish expansion weakened significantly. Need bearish SMT to confirm bearish continuation.",
            "context_summary": {
                "market_state":
                    "Earlier bearish delivery weakened significantly and price returned back into value.",

                "expected_delivery":
                    "Expect liquidity sweeps at pre-market extremes before the next directional move develops.",

                "trade_focus":
                    "Focus on pre-market highs, pre-market lows and London session gaps."
            }
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
        name = None
        group = "value_flip"
        name = "bullish_value_flip"
        return {
            "execution_edge": 95,
            "direction_score": 90,
            "migration_score": 90,
            "pqs": 92,
            "reaction_levels": {"Bearish 30m OB", "Pre-market Highs"},
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "value_flip",
            "category": "value_flip",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "very_strong",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": True,
            "is_compression_resolution": True,
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
            # mitigation is exisiting OB level
            "mitigation_level": (ib18["low"] + ib8["high"]) / 2,
            "note_internal":
                "Bullish expansion failed with ib8 flipping value and transitioning direction.",
            "note":
                "Bullish expansion during london failed and bearish prices accepted in premarket.",
            "context_summary": {
                "market_state":
                    "Market initially expanded higher, but the move failed as price migrated below the daily open and accepted lower prices.",

                "expected_delivery":
                    "Expect retracements to be sold and bearish delivery to continue toward lower objectives.",

                "trade_focus":
                    "Focus on overnight gaps, pre-market highs, bearish mitigation levels and continuation setups below the daily open."
            }
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
        name = None
        group = "value_flip"
        name = "bearish_value_flip"
        return {
            "execution_edge": 95,
            "direction_score": 90,
            "migration_score": 90,
            "pqs": 92,
            "reaction_levels": {"Bullish 30m OB", "Pre-market Lows"},
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "value_flip",
            "category": "value_flip",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "very_strong",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": True,
            "is_compression_resolution": True,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": True,
            "is_decompression": False,
            
            "compression_range": {
                "high": None,
                "low": None,
                "ce": None
            },
            "range": {
                "high": ib8["high"],
                "low": ib1["low"],
                "ce": (ib8["high"] + ib1["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib8["low"],
                "low": ib18["high"],
                "ce": (ib8["low"] + ib18["high"]) / 2
            },
            "mitigation_level": (ib8["low"] + ib18["high"]) / 2,
            "note_internal":
                "Bearish expansion failed with ib8 flipping value and transitioning direction.",
            "note":
                "Bearish expansion during dondon failed and bullish prices accepted in premarket.",
            "context_summary": {
                "market_state":
                    "Market initially expanded lower, but the move failed as price migrated above the daily open and accepted higher prices.",

                "expected_delivery":
                    "Expect retracements to be bought and bullish delivery to continue toward higher objectives.",

                "trade_focus":
                    "Focus on overnight gaps, pre-market lows, bullish mitigation levels and continuation setups above the daily open."
            }
        }
    # =====================================================
    # COMPRESSION SETS
    # =====================================================
    # EARLY COMPRESSION SET 1
    # Compression in london and migrating into ny am
    # =====================================================
    # =====================================================
    # BULLISH EARLY COMPRESSION
    # Compression early in london and expansion higher
    # =====================================================
    if (
        ib1_inside_ib18
        and ib8_above_ib1
    ):
        name = None
        group = "compression"
        name = "bullish_early_compression"
        return {
            "execution_edge": 92,
            "direction_score": 85,
            "migration_score": 85,
            "pqs": 89,
            "reaction_levels": {"London Range Eq", "Pre-market Lows", "Pre-market 30m Bullish OB"},
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "migration",
            "category": "migration",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "strong",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": True,
            "is_decompression": False,
            "is_compression_resolution": True,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            
            "compression_range": {
                "high": ib18["high"],
                "low": ib18["low"],
                "ce": (ib18["low"]+ ib18["high"])/2,
            },
            "range": {
                "high": ib8["high"], 
                "low": ib18["low"], 
                "ce": (ib8["high"]+ ib18["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib8["high"], 
                "low": ib18["low"],
                "ce": (ib8["high"]+ ib18["low"]) / 2
            },
            "mitigation_level": (ib8["low"]+ ib18["high"])/2,

            "note_internal":
                "1AM IB inside 18 IB and 8AM continued higher. "
                "Early bullish volatility expansion accepted.",

            "note":
                "Bullish early expansion during London session. "
                "Higher pricing accepted before NY open. Expect price to make shallow retracement towards london equilibrium or sweep of lows before continuation higher.",
            "context_summary": {
                "market_state":
                    "The market transitioned into expansion during London and continued accepting higher prices into the pre-market session.",

                "expected_delivery":
                    "Expect retracements into pre-market imbalances or mitigation levels before bullish delivery resumes toward higher objectives.",

                "trade_focus":
                    "Focus on pre-market imbalances, bullish mitigation levels and 30m bullish structure formed during the ongoing expansion."
            }
        }
    # =====================================================
    # BEARISH EARLY COMPRESSION
    # Compression early in london and expansion lower
    # =====================================================
    if (
        ib1_inside_ib18
        and ib8_below_ib1
    ):
        name = None
        group = "compression"
        name = "bearish_early_compression"
        return {
            "execution_edge": 92,
            "direction_score": 85,
            "migration_score": 85,
            "pqs": 89,
            "reaction_levels": {"London Range Eq", "Pre-market Highs", "Pre-market 30m Bearish OB"},
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "migration",
            "category": "migration",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "strong",
            "is_compression": False,
            "is_strong_compression": False,
            "compression_strength": None,
            "is_acceptance": True,
            "is_decompression": False,
            "is_compression_resolution": True,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            
            "compression_range": {
                "high": ib18["high"],
                "low": ib18["low"],
                "ce": (ib18["low"]+ ib18["high"])/2,
            },
            "range": {
                "high": ib18["high"], 
                "low": ib8["low"], 
                "ce": (ib18["high"]+ ib8["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib18["high"], 
                "low": ib8["low"],
                "ce": (ib18["high"]+ ib8["low"]) / 2
            },
            "mitigation_level": (ib18["low"]+ ib8["high"])/2,

            "note_internal":
                "1AM IB inside 18 IB and 8AM continued lower. "
                "Early bearish volatility expansion accepted.",

            "note":
                "Bearish early expansion during London session. "
                "Lower pricing accepted before NY open. Expect price to make shallow retracement towards london equilibrium or sweep of highs before continuation lower.",
            "context_summary": {
                "market_state":
                    "The market transitioned into expansion during London and continued accepting lower prices into the pre-market session.",

                "expected_delivery":
                    "Expect retracements into pre-market imbalances or mitigation levels before bearish delivery resumes toward lower objectives.",

                "trade_focus":
                    "Focus on pre-market imbalances, bearish mitigation levels and 30m bearish structure formed during the ongoing expansion."
            }
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
        name = None
        group = "compression"
        name = "sandwich_gap_bullish"
        return {
            "execution_edge": 90,
            "direction_score": 70,
            "migration_score": 40,
            "pqs": 77,
            "reaction_levels": None,
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "compression",
            "category": "balanced_compression",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": False,
            "is_compression_resolution": False,
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
                "Early bullish move followed by consolidation at equilibrium of asia and london range.",
            "context_summary": {
                "market_state":
                    "Market is consolidating near the equilibrium of the overnight range after early bullish move.",

                "expected_delivery":
                    "Expect a liquidity sweep at local highs or lows before a directional expansion emerges.",

                "trade_focus":
                    "Focus on local highs, local lows and overnight range extremes. Wait for Ping confirmation before trading the expansion."
            }
        }

    # =====================================================
    # SANDWICH GAP BEARISH
    # =====================================================

    if (
        ib1_below_ib18
        and ib8["low"] > ib1["high"]
        and ib8["high"] < ib18["low"]
    ):
        name = None
        group = "compression"
        name = "sandwich_gap_bearish"
        return {
            "execution_edge": 90,
            "direction_score": 70,
            "migration_score": 40,
            "pqs": 77,
            "reaction_levels": None,
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "compression",
            "category": "balanced_compression",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": False,
            "is_compression_resolution": False,
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
                "Early bearish move followed by consolidation at equilibrium of asia and london range.",
            "context_summary": {
                "market_state":
                    "Market is consolidating near the equilibrium of the overnight range after early bearish move.",

                "expected_delivery":
                    "Expect a liquidity sweep at local highs or lows before a directional expansion emerges.",

                "trade_focus":
                    "Focus on local highs, local lows and overnight range extremes. Wait for Ping confirmation before trading the expansion."
            }
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
    # TODO update condition for partial overlap bullish structures
    if (
        ib1_above_ib18 and ib1["low"] > ib18["high"]
        and  ib1["low"] < ib8["high"] < ib1["high"]
        and ib1["low"] > ib8["low"] > ib18["high"]
        
    ):  
        name = None
        group = "compression"
        name = "sandwich_partial_overlap_bullish"
        return {
            "execution_edge": 100,
            "direction_score": 70,
            "migration_score": 50,
            "pqs": 85,
            "reaction_levels": None,
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "compression",
            "category": "balanced_compression",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": True,
            "is_compression_resolution": False,
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
                "low": ib1["low"],
                "ce": (ib8["high"] + ib1["low"]) / 2
            },
            # mitigation is inside compression zone but our mitigation level is at migration equilibrium
            "mitigation_level": (ib1["high"] + ib18["low"]) / 2,
            "note_internal":
                "Bullish sandwich compression with acceptance weakeness.",
            "note": 
                "Consolidation inside asia-london range with weakness in accepting higher prices after early bullish move.",
            "context_summary": {
                "market_state":
                    "Market accepted higher prices earlier but has since transitioned into consolidation within the overnight range.",

                "expected_delivery":
                    "Expect liquidity sweep at lows before expansion as upside continuation remains possible while higher prices continue to be accepted.",

                "trade_focus":
                    "Focus on local lows, and gaps in asia range and reactions after liquidity sweeps. A sweep of sell-side liquidity may provide the foundation for bullish expansion."
            }
        }
    if (
        ib1_above_ib18
        and  ib8["high"] < ib1["low"]
        and ib18["low"] < ib8["low"] <= ib18["high"]
    ):
        name = None
        group = "compression"
        name = "sandwich_partial_overlap_bullish"
        return {
            "execution_edge": 90,
            "direction_score": 60,
            "migration_score": 40,
            "pqs": 75,
            "reaction_levels": None,
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "compression",
            "category": "balanced_compression",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": False,
            "is_compression_resolution": False,
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
                "Consolidation inside asia-london range. Price tapped into deeper asia range, weakening earlier bullish move",
            "context_summary": {
                "market_state": 
                    "Price initially accepted higher prices during the overnight session but later retraced back toward the earlier range, rebalancing a significant portion of the bullish migration.",
                "expected_delivery": 
                    "Expect liquidity sweeps at local highs or lows before directional expansion develops. The deeper retracement suggests the market is seeking equilibrium before choosing direction.",
                "trade_focus":
                    "Focus on local highs, local lows, overnight range equilibrium and gaps formed during London. Wait for a liquidity sweep and Ping confirmation before anticipating expansion."
            }
        }
    # =====================================================
    # SANDWICH PARTIAL OVERLAP BEARISH
    # =====================================================
    
    if (
        ib1_below_ib18
        and  ib1["low"] < ib8["low"] < ib1["high"]
        and ib8["high"] < ib18["low"]
    ):
        name = None
        group = "compression"
        name = "sandwich_partial_overlap_bearish"
        return {
            "execution_edge": 100,
            "direction_score": 70,
            "migration_score": 50,
            "pqs": 85,
            "reaction_levels": None,
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "compression",
            "category": "balanced_compression",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": True,
            "is_compression_resolution": False,
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
                "high": ib1["high"],
                "low": ib8["low"],
                "ce": (ib1["high"] + ib8["low"]) / 2
            },
            "mitigation_level": (ib18["high"] + ib1["low"]) / 2,
            "note_internal":
                "Bearish sandwich compression with acceptance weakness.",
            "note": 
                "Consolidation inside asia-london range with weakness in accepting lower prices after early bearish move.",
            "context_summary": {
                "market_state":
                    "Market accepted lower prices earlier but has since transitioned into consolidation within the overnight range.",

                "expected_delivery":
                    "Expect liquidity sweep at highs before expansion as downside continuation remains possible while lower prices continue to be accepted.",

                "trade_focus":
                    "Focus on local highs, and gaps in asia range and reactions after liquidity sweeps. A sweep of buy-side liquidity may provide the foundation for bearish expansion."
            }
        }
    if (
        ib1_below_ib18
        and  ib8["low"] > ib1["high"]
        and ib18["low"] <= ib8["high"] < ib18["high"]
    ):
        name = None
        group = "compression"
        name = "sandwich_partial_overlap_bearish"
        return {
            "execution_edge": 90,
            "direction_score": 60,
            "migration_score": 40,
            "pqs": 75,
            "reaction_levels": None,
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "compression",
            "category": "balanced_compression",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": False,
            "is_compression_resolution": False,
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
                "Consolidation inside asia-london range. Price tapped into deeper asia range, weakening earlier bearish move",
            "context_summary": {
                "market_state": 
                    "Price initially accepted lower prices during the overnight session but later retraced back toward the earlier range, rebalancing a significant portion of the bearish migration.",
                "expected_delivery": 
                    "Expect liquidity sweeps at local highs or lows before directional expansion develops. The deeper retracement suggests the market is seeking equilibrium before choosing direction.",
                "trade_focus":
                    "Focus on local highs, local lows, overnight range equilibrium and gaps formed during London. Wait for a liquidity sweep and Ping confirmation before anticipating expansion."
            }
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
        name = None
        group = "compression"
        name = "sandwich_overlap_bullish"
        return {
            "execution_edge": 100,
            "direction_score": 70,
            "migration_score": 50,
            "pqs": 85,
            "reaction_levels": None,
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "compression",
            "category": "balanced_compression",
            "direction": "bullish",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": True,
            "is_compression_resolution": False,
            "is_reintegration": False,
            "is_rebalance": True,
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
                "high": ib1["low"],
                "low": ib18["high"],
                "ce": (ib18["high"] + ib1["low"]) / 2
            },
            "mitigation_level": (ib18["high"] + ib1["low"]) / 2,
            "note_internal":
                "Balanced bullish sandwich compression.",
            "note": 
                "Price is consolidating at eq of asia-london range after bullish move in asia.",
            "context_summary": {
                "market_state":
                    "Price consolidated between the earlier overnight ranges, compressing after an initial bullish migration without fully accepting higher prices.",
                "expected_delivery":
                    "Expect a sweep of local highs or lows before directional expansion develops. Compression remains the dominant characteristic of the structure.",
                "trade_focus":
                    "Focus on compression highs, compression lows and overnight equilibrium. Wait for a liquidity sweep and Ping confirmation before trading the expansion."
            }
        }

    # =====================================================
    # SANDWICH OVERLAP BEARISH
    # =====================================================
    if (
        ib1_below_ib18
        and ib1["low"] < ib8["low"] < ib1["high"]
        and ib18["high"] > ib8["high"] > ib18["low"]
        
    ):
        name = None
        group = "compression"
        name = "sandwich_overlap_bearish"
        return {
            "execution_edge": 100,
            "direction_score": 70,
            "migration_score": 50,
            "pqs": 85,
            "reaction_levels": None,
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "compression",
            "category": "balanced_compression",
            "direction": "bearish",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": True,
            "is_compression_resolution": False,
            "is_reintegration": False,
            "is_rebalance": True,
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
                "high": ib18["low"],
                "low": ib1["high"],
                "ce": (ib1["high"] + ib18["low"]) / 2
            },
            "mitigation_level": (ib18["low"] + ib1["high"]) / 2,
            "note_internal":
                "Balanced bearish sandwich compression.",
            "note": 
                "Price is consolidating at eq of asia-london range after bearish move in asia.",
            "context_summary": {
                "market_state":
                    "Price consolidated between the earlier overnight ranges, compressing after an initial bearish migration without fully accepting lower prices.",
                "expected_delivery":
                    "Expect a sweep of local highs or lows before directional expansion develops. Compression remains the dominant characteristic of the structure.",
                "trade_focus":
                    "Focus on compression highs, compression lows and overnight equilibrium. Wait for a liquidity sweep and Ping confirmation before trading the expansion."
            }
        }
    # =====================================================
    # SANDWICH BULLISH
    # all ibs overlapping with each other with no gaps between them
    # tight and energetic compression with explosive move after sweep of compression extremes
    # here the mitigation level is at the extremes of 8am ib range, 
    # =====================================================

    if (
        ib1["high"] >  ib18["high"] and ib18["low"] < ib1["low"] < ib18["high"]
        # and ib1["low"] < ib8["high"] < ib1["high"]
        # and ib18["high"] > ib8["low"] > ib18["low"]
        and ib8["high"] < ib1["high"]
        and ib8["low"] > ib18["low"]
    ):
        name = None
        group = "compression"
        name = "sandwich_bullish"
        return {
            "execution_edge": 100,
            "direction_score": 45,
            "migration_score": 40,
            "pqs": 77,
            "reaction_levels": None,
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "compression",
            "category": "compression",
            "direction": "neutral",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": False,
            "compression_strength": "strong",
            "is_acceptance": True,
            "is_rebalance": True,
            "is_compression_resolution": False,
            "is_reintegration": False,
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
            "mitigation_level": (ib8["high"] + ib8["low"]) / 2,
            "note_internal":
                "The market remained centered with acceptance of neither bullish nor bearish sentiment.",
            "note": 
                "The market is in a tight consolidation with no clear directional bias. Expect a strong directional move after sweep of consolidation range.",
            "context_summary": {
                "market_state":
                    "Market remains in a tight overnight consolidation with liquidity building above and below the range.",

                "expected_delivery":
                    "Expect a liquidity sweep of the consolidation range before directional expansion develops.",

                "trade_focus":
                    "Focus on consolidation highs, consolidation lows and overnight equilibrium. Wait for a liquidity sweep and Ping confirmation before trading the expansion."
            }
        }
    
    # =====================================================
    # SANDWICH BEARISH
    # all ibs overlapping with each other with no gaps between them
    # tight and energetic compression with explosive move after sweep of compression extremes
    # =====================================================

    if (
        ib18["high"] > ib1["high"] and ib1["low"] < ib18["low"] < ib1["high"]
        # and ib18["low"] < ib8["high"] < ib18["high"]
        # and ib1["high"] > ib8["low"] > ib1["low"]
        and ib8["high"] < ib18["high"]
        and ib8["low"] > ib1["low"]
    ):
        name = None
        group = "compression"
        name = "sandwich_bearish"
        return {
            "execution_edge": 100,
            "direction_score": 45,
            "migration_score": 40,
            "pqs": 77,
            "reaction_levels": None,
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "compression",
            "category": "compression",
            "direction": "neutral",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": True,
            "is_rebalance": True,
            "is_compression_resolution": False,
            "is_reintegration": False,
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
            "mitigation_level": (ib8["high"] + ib8["low"]) / 2,
            "note_internal":
                "The market remained centered with acceptance of neither bullish nor bearish sentiment.",
            "note": 
                "The market is in a tight consolidation with no clear directional bias. Expect a strong directional move after sweep of consolidation range.",
            "context_summary": {
                "market_state":
                    "Market remains in a tight overnight consolidation with liquidity building above and below the range.",

                "expected_delivery":
                    "Expect a liquidity sweep of the consolidation range before directional expansion develops.",

                "trade_focus":
                    "Focus on consolidation highs, consolidation lows and overnight equilibrium. Wait for a liquidity sweep and Ping confirmation before trading the expansion."
            }
        }
    
    # =====================================================
    # SANDWICH NEUTRAL - Recompression
    # IB1 Engulfs IB18 and IB8 inside IB1
    # tight and energetic compression with explosive move after sweep of compression extremes
    # =====================================================

    if (
        ib1_engulf_ib18 and ib8_inside_ib1
    ):
        name = None
        group = "compression"
        name = "sandwich_neutral_recompression"
        return {
            "execution_edge": 100,
            "direction_score": 20,
            "migration_score": 30,
            "pqs": 70,
            "pqs": 83,
            "reaction_levels": None,
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "compression",
            "category": "compression",
            "direction": "neutral",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": True,
            "is_rebalance": True,
            "is_compression_resolution": False,
            "is_reintegration": False,
            "is_value_flip": False,
            "is_decompression": False,
            
            "compression_range": {
                "high": ib8["high"],
                "low": ib8["low"],
                "ce": (ib8["high"] + ib8["low"]) / 2
            },
            "range": {
                "high": ib1["high"],
                "low": ib1["low"],
                "ce": (ib1["high"] + ib1["low"]) / 2
            },
            "equilibrium_range": {
                "high": ib8["high"],
                "low": ib8["low"],
                "ce": (ib8["high"] + ib8["low"]) / 2
            },
            "mitigation_level": (ib1["high"] + ib1["low"]) / 2,
            "note_internal":
                "The market remained centered with acceptance of neither bullish nor bearish sentiment.",
            "note": 
                "The market is in a tight consolidation with no clear directional bias. Expect a strong directional move after sweep of consolidation range.",
            "context_summary": {
                "market_state":
                    "Market remains in a tight overnight consolidation with liquidity building above and below the range.",

                "expected_delivery":
                    "Expect a liquidity sweep of the consolidation range before directional expansion develops.",

                "trade_focus":
                    "Focus on consolidation highs, consolidation lows and overnight equilibrium. Wait for a liquidity sweep and Ping confirmation before trading the expansion."
            }
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
        name = None
        group = "compression"
        name = "centered_compression"
        return {
            "execution_edge": 0,
            "direction_score": 0,
            "migration_score": 0,
            "pqs": 70,
            "reaction_levels": None,
            "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
            "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
            "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
            "market_phase": "compression",
            "category": "compression",
            "direction": "neutral",
            "is_staircase": False,
            "migration_strength": "weak",
            "is_compression": True,
            "is_strong_compression": True,
            "compression_strength": "strong",
            "is_acceptance": False,
            "is_rebalance": False,
            "is_compression_resolution": False,
            "is_reintegration": False,
            "is_value_flip": False,
            "is_decompression": False,
            
            "compression_range": {"high": ib18["high"], "low": ib18["low"], "ce": (ib18["high"] + ib18["low"]) / 2},
            "range": {"high": ib18["high"], "low": ib18["low"], "ce": (ib18["high"] + ib18["low"]) / 2},
            "equilibrium_range": {"high": ib1["high"], "low": ib1["low"], "ce": (ib1["high"] + ib1["low"]) / 2},
            "mitigation_level": (ib1["high"] + ib1["low"]) / 2,
            "notes_internal": "IB1 inside IB18 with midpoints within 15% of IB18 range.",
            "note":
                "Tight consolidation inside larger asia range.",
            "note_internal":
                "Tight consolidation inside larger asia range.",
            "context_summary": {
                "market_state":
                    "Market remains in a tight overnight consolidation with liquidity building above and below the range.",

                "expected_delivery":
                    "Expect a liquidity sweep of the consolidation range before directional expansion develops.",

                "trade_focus":
                    "Focus on consolidation highs, consolidation lows and overnight equilibrium. Wait for a liquidity sweep and Ping confirmation before trading the expansion."
            }
        }

    # =====================================================
    # DEFAULT
    # =====================================================
    name = None
    group = "compression"
    name = "mixed_overlap"
    return {
        "execution_edge": 0,
        "direction_score": 0,
        "migration_score": 0,
        "pqs": 70,
        "reaction_levels": None,
        "structure_name": name,
            "structure_phase": get_structure_phase(name),
            "auction_phase": get_auction_phase(name),
        "structure_group": group,
            "execution_state": {
                "rocket": "waiting",      # waiting | ready | completed
                "flush": "waiting",       # waiting | ready | completed
            },
        "is_neutral_direction_structure": name in NEUTRAL_DIRECTION_STRUCTURES,
        "category": "mixed",
        "market_phase": "compression",
        "direction": "neutral",

        "is_staircase": False,
        "is_compression": True,
        "is_strong_compression": True,
        "migration_strength": None,
        "is_acceptance": False,
        "is_rebalance": False,
        "is_compression_resolution": False,
        "is_reintegration": False,
        "is_value_flip": False,
        "is_decompression": False,
        "compression_strength": None,
        "compression_range": {"high": max(ib1["high"], ib8["high"], ib18["high"]), "low": min(ib1["low"], ib8["low"], ib18["low"]), "ce": (max(ib1["high"], ib8["high"], ib18["high"]) + min(ib1["low"], ib8["low"], ib18["low"])) / 2},
        "range": {"high": max(ib1["high"], ib8["high"], ib18["high"]), "low": min(ib1["low"], ib8["low"], ib18["low"]), "ce": (max(ib1["high"], ib8["high"], ib18["high"]) + min(ib1["low"], ib8["low"], ib18["low"])) / 2},
        "equilibrium_range": {"high": max(ib1["high"], ib8["high"], ib18["high"]), "low": min(ib1["low"], ib8["low"], ib18["low"]), "ce": (max(ib1["high"], ib8["high"], ib18["high"]) + min(ib1["low"], ib8["low"], ib18["low"])) / 2},
        "mitigation_level": (max(ib1["high"], ib8["high"], ib18["high"]) + min(ib1["low"], ib8["low"], ib18["low"])) / 2,
        "note":
            "Mixed overlap structure. "
            "Directional conviction unclear.",
        "note_internal": 
            "Mixed overlap structure. "
            "Directional conviction unclear.",
        "context_summary": {
            "market_state":
                "",

            "expected_delivery":
                "",

            "trade_focus":
                ""
        }
    }




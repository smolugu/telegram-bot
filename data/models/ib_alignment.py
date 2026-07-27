def analyze_cross_asset_alignment(
    nq_structure,
    es_structure,
    nq_atr_exhausted=None,
    es_atr_exhausted=None,
):
    """
    ============================================================
    CROSS ASSET STRUCTURE ALIGNMENT ENGINE
    ============================================================

    PURPOSE
    -------
    Evaluates:
    - directional agreement
    - migration efficiency alignment
    - compression relationships
    - equilibrium state relationships
    - structural leadership
    - expansion quality

    IMPORTANT
    ---------
    This engine DOES NOT:
    - generate trade direction
    - generate long/short signals
    - override structure logic

    Structure blocks themselves define:
    - valid Rockets
    - valid Flushes

    This engine only provides:
    - contextual structural alignment
    - confidence modifiers
    - cross-asset state analysis

    ============================================================
    """

    result = {
        
        # ======================================================
        # STRUCTURE ALIGNMENT
        # ======================================================
        
        "structure_alignment": "same",

        # same
        # similar
        # conflicting

        # ======================================================
        # PHASE ALIGNMENT
        # ======================================================

        "phase_alignment": "same",
        # examples:
        # same
        # mixed
        # conflicting

        # ======================================================
        # VALUE STATE ALIGNMENT
        # ======================================================

        "value_state_alignment": "same",
        # examples:
        # same
        # mixed
        # conflicting

        # ======================================================
        # DIRECTIONAL AGREEMENT
        # ======================================================

        "alignment_state": "mixed_directional",

        # examples:
        # aligned_bullish
        # aligned_bearish
        # mixed_directional


        # ======================================================
        # MIGRATION RELATIONSHIP
        # ======================================================

        "migration_alignment": "neutral",

        # examples:
        # strong_alignment
        # weak_alignment
        # nq_stronger
        # es_stronger
        # compression_vs_migration
        # rebalance_vs_migration
        # migration_divergence
        # neutral


        # ======================================================
        # STRUCTURAL LEADERSHIP
        # ======================================================

        "dominant_asset": "neutral",

        # examples:
        # NQ
        # ES
        # neutral


        # ======================================================
        # COMPRESSION RELATIONSHIP
        # ======================================================

        "compression_alignment": "neutral",

        # examples:
        # both_compressing
        # broad_equilibrium
        # isolated_compression
        # post_compression
        # compression_vs_migration
        # neutral


        # ======================================================
        # EQUILIBRIUM RELATIONSHIP
        # ======================================================

        "equilibrium_state": "neutral",

        # examples:
        # both_acceptance
        # both_rebalance
        # reintegration_active
        # equilibrium_conflict
        # balanced_equilibrium
        # neutral


        # ======================================================
        # EXPANSION QUALITY
        # ======================================================

        "expansion_quality": "medium",

        # examples:
        # explosive
        # high
        # medium
        # weak
        # choppy
        # post_exhaustion
        # unstable


        # ======================================================
        # CONFIDENCE MODIFIER
        # ======================================================

        "confidence_modifier": 0,

        # suggested range:
        # -2 → +2


        # ======================================================
        # STRUCTURAL TAGS
        # ======================================================

        "tags": [],


        # ======================================================
        # RAW STRUCTURES
        # ======================================================

        "nq_structure": nq_structure["name"],
        "es_structure": es_structure["name"],
    }

    # ==========================================================
    # HELPERS
    # ==========================================================

    def migration_rank(structure):

        # strongest directional migration

        if (
            structure["is_staircase"]
            and structure["migration_strength"] == "strong"
        ):
            return 4

        # strong directional migration

        if (
            structure["migration_strength"] == "strong"
        ):
            return 3

        # medium migration

        if (
            structure["migration_strength"] == "medium"
        ):
            return 2

        # weak migration

        if (
            structure["migration_strength"] == "weak"
        ):
            return 1

        return 0

    nq_rank = migration_rank(nq_structure)
    es_rank = migration_rank(es_structure)

    # ==========================================================
    # STRUCTURE ALIGNMENT
    # ==========================================================

    result["structure_alignment"] = "conflicting"

    nq_name = nq_structure["name"]
    es_name = es_structure["name"]

    # ----------------------------------------------------------
    # SAME STRUCTURE
    # ----------------------------------------------------------

    if nq_name == es_name:

        result["structure_alignment"] = "same"

        result["tags"].append(
            "same_structure_alignment"
        )

    else:

        NEUTRAL_DIRECTION_STRUCTURES = {
            "sandwich_bullish",
            "sandwich_bearish",

            "sandwich_overlap_bullish",
            "sandwich_overlap_bearish",

            "sandwich_partial_overlap_bullish",
            "sandwich_partial_overlap_bearish",

            "bullish_rebalance_compression",
            "bearish_rebalance_compression",

            "sandwich_neutral"
        }

        # ======================================================
        # BULLISH STRUCTURE GROUPS
        # ======================================================

        bullish_staircase_structures = {

            "staircase_gap_bullish",
            "staircase_early_overlap_bullish",
            "staircase_late_overlap_bullish",
            "staircase_bullish",
            "bullish_early_compression"
        }

        bullish_sandwich_structures = {

            "sandwich_gap_bullish",
            "sandwich_partial_overlap_bullish",
            "sandwich_overlap_bullish",
            "sandwich_bullish",
        }

        bullish_compression_structures = {

            "bullish_acceptance_compression",
            "bullish_rebalance_compression",
        }

        bullish_decompression_structures ={
            "bullish_decompression",
            "bullish_early_decompression",
            "bullish_macro_decompression",
            "bullish_mixed_decompression",
            "bullish_mixed_macro_decompression",
        }
        bullish_reintegration_structures = {

            "bullish_reintegration",
        }

        bullish_value_flip_structures = {

            "bullish_value_flip",
        }

        # ======================================================
        # BEARISH STRUCTURE GROUPS
        # ======================================================

        bearish_staircase_structures = {

            "staircase_gap_bearish",
            "staircase_early_overlap_bearish",
            "staircase_late_overlap_bearish",
            "staircase_bearish",
            "bearish_early_compression",
        }

        bearish_sandwich_structures = {

            "sandwich_gap_bearish",
            "sandwich_partial_overlap_bearish",
            "sandwich_overlap_bearish",
            "sandwich_bearish",
        }

        bearish_compression_structures = {

            "bearish_acceptance_compression",
            "bearish_rebalance_compression",
        }

        bearish_decompression_structures = {

            "bearish_decompression",
            "bearish_early_decompression",
            "bearish_macro_decompression",
            "bearish_mixed_decompression",
            "bearish_mixed_macro_decompression",
        }

        bearish_reintegration_structures = {

            "bearish_reintegration",
        }

        bearish_value_flip_structures = {

            "bearish_value_flip",
        }

        # ======================================================
        # SAME FAMILY CHECKS
        # ======================================================

        same_bullish_staircase_family = (
            nq_name in bullish_staircase_structures
            and es_name in bullish_staircase_structures
        )

        same_bearish_staircase_family = (
            nq_name in bearish_staircase_structures
            and es_name in bearish_staircase_structures
        )

        same_bullish_sandwich_family = (
            nq_name in bullish_sandwich_structures
            and es_name in bullish_sandwich_structures
        )

        same_bearish_sandwich_family = (
            nq_name in bearish_sandwich_structures
            and es_name in bearish_sandwich_structures
        )

        same_bullish_compression_family = (
            nq_name in bullish_compression_structures
            and es_name in bullish_compression_structures
        )

        same_bearish_compression_family = (
            nq_name in bearish_compression_structures
            and es_name in bearish_compression_structures
        )
        same_bullish_decompression_family = (
            nq_name in bullish_decompression_structures
            and es_name in bullish_decompression_structures
        )

        same_bearish_decompression_family = (
            nq_name in bearish_decompression_structures
            and es_name in bearish_decompression_structures
        )

        same_bullish_reintegration_family = (
            nq_name in bullish_reintegration_structures
            and es_name in bullish_reintegration_structures
        )

        same_bearish_reintegration_family = (
            nq_name in bearish_reintegration_structures
            and es_name in bearish_reintegration_structures
        )

        same_bullish_value_flip_family = (
            nq_name in bullish_value_flip_structures
            and es_name in bullish_value_flip_structures
        )

        same_bearish_value_flip_family = (
            nq_name in bearish_value_flip_structures
            and es_name in bearish_value_flip_structures
        )

        # ======================================================
        # SIMILAR STRUCTURE
        # ======================================================

        if (

            same_bullish_staircase_family
            or same_bearish_staircase_family

            or same_bullish_sandwich_family
            or same_bearish_sandwich_family

            or same_bullish_compression_family
            or same_bearish_compression_family

            or same_bullish_reintegration_family
            or same_bearish_reintegration_family

            or same_bullish_value_flip_family
            or same_bearish_value_flip_family

            or same_bullish_decompression_family
            or same_bearish_decompression_family

        ):

            result["structure_alignment"] = "similar"
            
            result["tags"].append(
                "same_structure_family"
            )

        # ======================================================
        # CONFLICTING STRUCTURES
        # ======================================================

        else:

            result["structure_alignment"] = (
                "conflicting"
            )

            result["confidence_modifier"] -= 1

            result["tags"].append(
                "structural_conflict"
            )

            # --------------------------------------------------
            # ACCEPTANCE VS REBALANCE
            # --------------------------------------------------

            if (
                nq_structure["is_acceptance"]
                and es_structure["is_rebalance"]
            ) or (
                es_structure["is_acceptance"]
                and nq_structure["is_rebalance"]
            ):

                result["tags"].append(
                    "acceptance_vs_rebalance"
                )

            # --------------------------------------------------
            # REINTEGRATION VS ACCEPTANCE
            # --------------------------------------------------

            if (
                nq_structure["is_reintegration"]
                and es_structure["is_acceptance"]
            ) or (
                es_structure["is_reintegration"]
                and nq_structure["is_acceptance"]
            ):

                result["tags"].append(
                    "reintegration_vs_acceptance"
                )
            
            # --------------------------------------------------
            # REINTEGRATION VS REBALANCE
            # --------------------------------------------------

            if (
                nq_structure["is_reintegration"]
                and es_structure["is_rebalance"]
            ) or (
                es_structure["is_reintegration"]
                and nq_structure["is_rebalance"]
            ):

                result["tags"].append(
                    "reintegration_vs_rebalance"
                )

            # --------------------------------------------------
            # COMPRESSION VS DECOMPRESSION
            # --------------------------------------------------

            if (
                nq_structure["is_compression"]
                and es_structure["is_decompression"]
            ) or (
                es_structure["is_compression"]
                and nq_structure["is_decompression"]
            ):

                result["tags"].append(
                    "compression_vs_decompression"
                )

            # --------------------------------------------------
            # MIGRATION VS COMPRESSION
            # --------------------------------------------------

            if (
                not nq_structure["is_compression"]
                and es_structure["is_compression"]
            ) or (
                not es_structure["is_compression"]
                and nq_structure["is_compression"]
            ):

                result["tags"].append(
                    "migration_vs_compression"
                )

            # --------------------------------------------------
            # DIRECTIONAL STRUCTURAL CONFLICT
            # --------------------------------------------------

            if (
                nq_structure["direction"]
                != es_structure["direction"]
            ):

                result["tags"].append(
                    "bullish_bearish_conflict"
                )

    # ==========================================================
    # DIRECTIONAL AGREEMENT
    # ==========================================================

    if (
        nq_structure["direction"] == "bullish"
        and es_structure["direction"] == "bullish"
    ):

        result["alignment_state"] = "aligned_bullish"
        result["confidence_modifier"] += 1

    elif (
        nq_structure["direction"] == "bearish"
        and es_structure["direction"] == "bearish"
    ):

        result["alignment_state"] = "aligned_bearish"
        result["confidence_modifier"] += 1

    else:

        result["alignment_state"] = "mixed_directional"
        result["migration_alignment"] = (
            "migration_divergence"
        )

        result["confidence_modifier"] -= 2

        result["tags"].append("directional_conflict")

    # ==========================================================
    # MIGRATION ALIGNMENT
    # ==========================================================

    if (
        nq_structure["direction"]
        == es_structure["direction"]
    ):

        rank_diff = abs(nq_rank - es_rank)

        # ------------------------------------------------------
        # STRONG ALIGNMENT
        # ------------------------------------------------------

        if (
            nq_rank >= 3
            and es_rank >= 3
            and rank_diff <= 1
        ):

            result["migration_alignment"] = (
                "strong_alignment"
            )

            result["expansion_quality"] = "explosive"

            result["confidence_modifier"] += 2

            result["tags"].append(
                "strong_cross_asset_migration"
            )

        # ------------------------------------------------------
        # WEAK ALIGNMENT
        # ------------------------------------------------------

        elif rank_diff <= 1:

            result["migration_alignment"] = (
                "weak_alignment"
            )

            result["confidence_modifier"] += 1

        # ------------------------------------------------------
        # NQ LEADING
        # ------------------------------------------------------

        elif nq_rank > es_rank:

            result["migration_alignment"] = (
                "nq_stronger"
            )

            result["dominant_asset"] = "NQ"

            result["tags"].append("nq_leading")

        # ------------------------------------------------------
        # ES LEADING
        # ------------------------------------------------------

        elif es_rank > nq_rank:

            result["migration_alignment"] = (
                "es_stronger"
            )

            result["dominant_asset"] = "ES"

            result["tags"].append("es_leading")

    # ==========================================================
    # COMPRESSION ALIGNMENT
    # ==========================================================

    nq_compression = nq_structure["is_compression"]
    es_compression = es_structure["is_compression"]

    if nq_compression and es_compression:

        result["compression_alignment"] = (
            "both_compressing"
        )

        result["tags"].append("compression_active")

        # broad equilibrium/chop

        if (
            nq_structure["compression_strength"] == "strong"
            and es_structure["compression_strength"] == "strong"
        ):

            result["expansion_quality"] = "choppy"

            result["tags"].append(
                "broad_equilibrium"
            )

    elif (
        nq_compression
        and not es_compression
    ) or (
        es_compression
        and not nq_compression
    ):

        result["compression_alignment"] = (
            "compression_vs_migration"
        )

        result["tags"].append(
            "compression_migration_divergence"
        )
    
    # ==========================================================
    # MARKET PHASE ALIGNMENT
    # ==========================================================

    nq_phase = nq_structure.get("market_phase")
    es_phase = es_structure.get("market_phase")

    if nq_phase == es_phase:

        result["phase_alignment"] = "same_phase"

    elif {
        nq_phase,
        es_phase
    } == {"compression", "decompression"}:

        # opposite ends of delivery cycle
        result["phase_alignment"] = "conflicting_phase"

    else:

        # migration vs compression
        # migration vs reintegration
        # reintegration vs compression
        # value_flip vs compression
        # etc
        result["phase_alignment"] = "mixed_phase"

    # ==========================================================
    # VALUE STATE ALIGNMENT
    # ==========================================================

    def get_value_state(structure):

        if structure.get("is_acceptance"):
            return "acceptance"

        if structure.get("is_rebalance"):
            return "rebalance"

        if structure.get("is_reintegration"):
            return "reintegration"

        if structure.get("is_value_flip"):
            return "value_flip"

        return None


    nq_value_state = get_value_state(nq_structure)
    es_value_state = get_value_state(es_structure)

    if nq_value_state == es_value_state:

        result["value_state_alignment"] = "same"

    elif (
        nq_value_state is None
        or es_value_state is None
    ):

        # migration structures
        # pure decompression structures
        result["value_state_alignment"] = "mixed"

    else:

        result["value_state_alignment"] = "mixed"

    # ==========================================================
    # EQUILIBRIUM STATE
    # ==========================================================

    nq_acceptance = nq_structure["is_acceptance"]
    es_acceptance = es_structure["is_acceptance"]

    nq_rebalance = nq_structure["is_rebalance"]
    es_rebalance = es_structure["is_rebalance"]

    nq_reintegration = nq_structure["is_reintegration"]
    es_reintegration = es_structure["is_reintegration"]

    # ----------------------------------------------------------
    # ACCEPTANCE ALIGNMENT
    # ----------------------------------------------------------

    if nq_acceptance and es_acceptance:

        result["equilibrium_state"] = (
            "both_acceptance"
        )

        result["confidence_modifier"] += 1

    # ----------------------------------------------------------
    # REBALANCE ALIGNMENT
    # ----------------------------------------------------------

    elif nq_rebalance and es_rebalance:

        result["equilibrium_state"] = (
            "both_rebalance"
        )

        result["tags"].append("rebalance_active")

    # ----------------------------------------------------------
    # REINTEGRATION
    # ----------------------------------------------------------

    elif nq_reintegration or es_reintegration:

        result["equilibrium_state"] = (
            "reintegration_active"
        )

        result["tags"].append(
            "reintegration_present"
        )

    # ----------------------------------------------------------
    # EQUILIBRIUM CONFLICT
    # ----------------------------------------------------------

    elif (
        nq_acceptance and es_rebalance
    ) or (
        es_acceptance and nq_rebalance
    ):

        result["equilibrium_state"] = (
            "equilibrium_conflict"
        )

        result["confidence_modifier"] -= 1

        result["tags"].append(
            "equilibrium_disagreement"
        )

    # ==========================================================
    # ATR CONTEXT
    # ==========================================================

    if (
        nq_atr_exhausted
        and es_atr_exhausted
    ):

        result["expansion_quality"] = (
            "post_exhaustion"
        )

        result["tags"].append("atr_exhausted")

    elif (
        not nq_atr_exhausted
        and not es_atr_exhausted
    ):

        if result["expansion_quality"] != "choppy":
            result["expansion_quality"] = "high"

    # ==========================================================
    # DECOMPRESSION
    # ==========================================================

    if (
        nq_structure["is_decompression"]
        and es_structure["is_decompression"]
    ):

        result["expansion_quality"] = "explosive"

        result["confidence_modifier"] += 2

        result["tags"].append(
            "cross_asset_decompression"
        )

    return result


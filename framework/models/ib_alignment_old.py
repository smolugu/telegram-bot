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

        # ======================================================
        # BULLISH STRUCTURE GROUPS
        # ======================================================

        bullish_staircase_structures = {

            "staircase_gap_bullish",
            "staircase_early_overlap_bullish",
            "staircase_late_overlap_bullish",
            "staircase_bullish",
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


def classify_ib_alignment(
    nq_context,
    es_context,
    htf_bias="neutral"
):
    """
    =====================================================
    IB ALIGNMENT ENGINE
    =====================================================

    PURPOSE
    -------
    Determines:
    - whether NQ and ES are aligned
    - alignment quality
    - directional agreement
    - whether one index may be inducement
    - high level NY context

    IMPORTANT
    ---------
    This function:
    - does NOT predict Rocket/Flush
    - does NOT use ATR
    - does NOT use sweeps

    It ONLY evaluates:
    - structural alignment
    - directional agreement
    - HTF conflict resolution

    INPUT
    -----
    nq_context:
        output of classify_ib_structure()

    es_context:
        output of classify_ib_structure()

    htf_bias:
        bullish / bearish / neutral

    RETURNS
    -------
    {
        "aligned": bool,
        "alignment_type": str,
        "shared_direction": str,
        "inducement_side": str | None,
        "summary": str
    }
    """

    # =====================================================
    # EXTRACT
    # =====================================================

    nq_structure = nq_context["structure"]
    es_structure = es_context["structure"]

    nq_direction = nq_context["direction"]
    es_direction = es_context["direction"]

    nq_category = nq_context["category"]
    es_category = es_context["category"]
    nq_note = nq_context["note"]
    es_note = es_context["note"]

    # =====================================================
    # DEFAULTS
    # =====================================================

    aligned = False
    alignment_type = "mixed"
    shared_direction = "neutral"
    inducement_side = None
    summary = "Mixed structure."

    # =====================================================
    # PERFECT ALIGNMENT
    # =====================================================

    if nq_structure == es_structure:

        aligned = True
        alignment_type = "perfect"
        shared_direction = nq_direction
        shared_structure = nq_structure
        summary = (
            f"NQ and ES perfectly aligned. "
            f"{nq_note}."
        )

        return {
            "aligned": aligned,
            "alignment_type": alignment_type,
            "shared_direction": shared_direction,
            "inducement_side": inducement_side,
            "shared_structure": shared_structure,
            "summary": summary
        }

    # =====================================================
    # SAME DIRECTION ACCEPTANCE
    # =====================================================

    bullish_categories = [
        "bullish_acceptance"
    ]

    bearish_categories = [
        "bearish_acceptance"
    ]

    decompression_categories = [
        "decompression"
    ]

    balanced_categories = [
        "balanced_compression",
        "compression",
        "rebalance"
    ]

    # -----------------------------------------------------
    # STRONG BULLISH ALIGNMENT
    # -----------------------------------------------------

    if (
        nq_direction == "bullish"
        and es_direction == "bullish"
    ):

        aligned = True
        alignment_type = "bullish_alignment"
        shared_direction = "bullish"

        summary = (
            "NQ and ES both structurally bullish. "
            "Higher pricing accepted across indices."
        )

    # -----------------------------------------------------
    # STRONG BEARISH ALIGNMENT
    # -----------------------------------------------------

    elif (
        nq_direction == "bearish"
        and es_direction == "bearish"
    ):

        aligned = True
        alignment_type = "bearish_alignment"
        shared_direction = "bearish"

        summary = (
            "NQ and ES both structurally bearish. "
            "Lower pricing accepted across indices."
        )

    # =====================================================
    # MIXED ALIGNMENT
    # =====================================================

    else:

        aligned = False
        alignment_type = "mixed"
        summary = (
            "NQ and ES structurally out of sync. "
            "Liquidity behavior or inducement likely."
        )

    # =====================================================
    # HTF RESOLUTION
    # =====================================================

    if not aligned:

        # -------------------------------------------------
        # HTF BULLISH
        # -------------------------------------------------

        if htf_bias == "bullish":

            shared_direction = "bullish"

            if nq_direction == "bearish":
                inducement_side = "nq"

            elif es_direction == "bearish":
                inducement_side = "es"

            summary += (
                " HTF bullish context suggests "
                "weakness on {inducement_side} may be inducement."
            )

        # -------------------------------------------------
        # HTF BEARISH
        # -------------------------------------------------

        elif htf_bias == "bearish":

            shared_direction = "bearish"

            if nq_direction == "bullish":
                inducement_side = "nq"

            elif es_direction == "bullish":
                inducement_side = "es"

            summary += (
                " HTF bearish context suggests "
                "strength on {inducement_side} may be inducement."
            )

        # -------------------------------------------------
        # HTF NEUTRAL
        # -------------------------------------------------

        else:

            shared_direction = "neutral"

            summary += (
                " No strong HTF directional edge."
            )

    # =====================================================
    # DECOMPRESSION ALIGNMENT
    # =====================================================

    if (
        nq_category in decompression_categories
        and es_category in decompression_categories
    ):

        alignment_type = "decompression_alignment"

        summary += (
            " High volatility decompression "
            "environment across indices."
        )

    # =====================================================
    # BALANCED COMPRESSION ALIGNMENT
    # =====================================================

    if (
        nq_category in balanced_categories
        and es_category in balanced_categories
    ):

        if aligned:

            alignment_type = "balanced_alignment"

            summary += (
                " Compression/rebalance environment "
                "present across indices."
            )

    # =====================================================
    # RETURN
    # =====================================================

    return {

        "aligned": aligned,
        "alignment_type": alignment_type,
        "shared_direction": shared_direction,
        "inducement_side": inducement_side,
        "nq_structure": nq_structure,
        "es_structure": es_structure,
        "nq_direction": nq_direction,
        "es_direction": es_direction,
        "nq_category": nq_category,
        "es_category": es_category,
        "summary": summary
    }



def classify_ib_alignment_old(
    nq_structure,
    es_structure
):
    """
    =====================================================
    IB STRUCTURE ALIGNMENT ENGINE
    =====================================================

    Determines:
    - whether NQ and ES are aligned
    - alignment strength
    - shared structural intent
    - explanatory notes

    INPUT
    -----
    nq_structure : str
    es_structure : str

    RETURNS
    -------
    {
        "aligned": bool,
        "alignment_strength": str,
        "shared_category": str,
        "nq_structure": str,
        "es_structure": str,
        "nq_note": str,
        "es_note": str,
        "summary": str
    }
    """

    # =====================================================
    # STRUCTURE DATABASE
    # =====================================================

    STRUCTURES = {

        # =================================================
        # BULLISH ACCEPTANCE
        # =================================================

        "staircase_gap_bullish": {
            "category": "bullish_acceptance",
            "direction": "bullish",
            "note":
                "Strong bullish acceptance. "
                "IBs stair-stepping higher with gaps. "
                "Market accepting higher pricing aggressively."
        },

        "staircase_overlap_bullish": {
            "category": "bullish_acceptance",
            "direction": "bullish",
            "note":
                "Bullish continuation structure with overlap. "
                "Higher pricing accepted but with minor rebalance."
        },

        "bullish_recompression": {
            "category": "bullish_acceptance",
            "direction": "bullish",
            "note":
                "Bullish recompression. "
                "Market expanded higher earlier and is now compressing "
                "before possible continuation higher."
        },

        # =================================================
        # BEARISH ACCEPTANCE
        # =================================================

        "staircase_gap_bearish": {
            "category": "bearish_acceptance",
            "direction": "bearish",
            "note":
                "Strong bearish acceptance. "
                "IBs stair-stepping lower with gaps. "
                "Market aggressively accepting lower pricing."
        },

        "staircase_overlap_bearish": {
            "category": "bearish_acceptance",
            "direction": "bearish",
            "note":
                "Bearish continuation structure with overlap. "
                "Lower pricing accepted but with minor rebalance."
        },

        "bearish_recompression": {
            "category": "bearish_acceptance",
            "direction": "bearish",
            "note":
                "Bearish recompression. "
                "Market expanded lower earlier and is now compressing "
                "before possible continuation lower."
        },

        # =================================================
        # REBALANCE / WEAKENING
        # =================================================

        "bullish_rebalance": {
            "category": "rebalance",
            "direction": "bullish",
            "note":
                "Bullish expansion weakening into rebalance. "
                "Price returned back inside prior structure."
        },

        "bearish_rebalance": {
            "category": "rebalance",
            "direction": "bearish",
            "note":
                "Bearish expansion weakening into rebalance. "
                "Price returned back inside prior structure."
        },

        # =================================================
        # FAILED EXPANSION
        # =================================================

        "failed_bullish_expansion": {
            "category": "failure",
            "direction": "bearish",
            "note":
                "Bullish expansion failed. "
                "Price reintegrated deep into prior range. "
                "Reversal risk elevated."
        },

        "failed_bearish_expansion": {
            "category": "failure",
            "direction": "bullish",
            "note":
                "Bearish expansion failed. "
                "Price reintegrated deep into prior range. "
                "Bullish reversal risk elevated."
        },

        # =================================================
        # SANDWICH STRUCTURES
        # =================================================

        "sandwich_gap_bullish": {
            "category": "balanced_compression",
            "direction": "bullish",
            "note":
                "Bullish sandwich compression with gaps. "
                "Compression sitting between separated ranges."
        },

        "sandwich_gap_bearish": {
            "category": "balanced_compression",
            "direction": "bearish",
            "note":
                "Bearish sandwich compression with gaps. "
                "Compression sitting between separated ranges."
        },

        "sandwich_overlap_bullish": {
            "category": "balanced_compression",
            "direction": "bullish",
            "note":
                "Balanced bullish overlap compression. "
                "Likely liquidity delivery before expansion."
        },

        "sandwich_overlap_bearish": {
            "category": "balanced_compression",
            "direction": "bearish",
            "note":
                "Balanced bearish overlap compression. "
                "Likely liquidity delivery before expansion."
        },

        # =================================================
        # ENGULFING / DECOMPRESSION
        # =================================================

        "ib1_engulf_ib18": {
            "category": "decompression",
            "direction": "neutral",
            "note":
                "1AM IB engulfed 18 IB. "
                "Large volatility expansion already occurred. "
                "Continuation vs reversal must be determined."
        },

        "ib8_engulf_ib1": {
            "category": "decompression",
            "direction": "neutral",
            "note":
                "8AM IB engulfed 1AM IB. "
                "NY volatility expansion already developing."
        },

        "ib8_engulf_ib18": {
            "category": "decompression",
            "direction": "neutral",
            "note":
                "8AM IB engulfed 18 IB. "
                "Large decompression environment."
        },

        # =================================================
        # COMPRESSION
        # =================================================

        "centered_compression": {
            "category": "compression",
            "direction": "neutral",
            "note":
                "Small centered compression inside larger range. "
                "Likely chop before edge engagement."
        },

        "dual_inside_compression": {
            "category": "compression",
            "direction": "neutral",
            "note":
                "Strong nested compression. "
                "IB1 inside IB18 and IB8 inside IB1. "
                "High expansion potential later."
        },

        # =================================================
        # DEFAULT
        # =================================================

        "mixed_overlap": {
            "category": "mixed",
            "direction": "neutral",
            "note":
                "Mixed overlap structure. "
                "Directional conviction weak."
        }
    }

    # =====================================================
    # GET STRUCTURE INFO
    # =====================================================

    nq = STRUCTURES.get(
        nq_structure,
        STRUCTURES["mixed_overlap"]
    )

    es = STRUCTURES.get(
        es_structure,
        STRUCTURES["mixed_overlap"]
    )

    # =====================================================
    # ALIGNMENT LOGIC
    # =====================================================

    aligned = False
    alignment_strength = "weak"
    shared_category = None

    # -----------------------------------------------------
    # PERFECT MATCH
    # -----------------------------------------------------
    if nq_structure == es_structure:

        aligned = True
        alignment_strength = "perfect"
        shared_category = nq["category"]

    # -----------------------------------------------------
    # SAME CATEGORY + SAME DIRECTION
    # -----------------------------------------------------
    elif (
        nq["category"] == es["category"]
        and nq["direction"] == es["direction"]
    ):

        aligned = True
        alignment_strength = "strong"
        shared_category = nq["category"]

    # -----------------------------------------------------
    # SAME CATEGORY ONLY
    # -----------------------------------------------------
    elif nq["category"] == es["category"]:

        aligned = True
        alignment_strength = "moderate"
        shared_category = nq["category"]

    # -----------------------------------------------------
    # OPPOSITE DIRECTIONS
    # -----------------------------------------------------
    else:

        aligned = False
        alignment_strength = "conflicted"
        shared_category = (
            f"{nq['category']} vs {es['category']}"
        )

    # =====================================================
    # SUMMARY GENERATION
    # =====================================================

    if aligned:

        summary = (
            f"NQ and ES are aligned in "
            f"{shared_category}. "
            f"Alignment strength: {alignment_strength}."
        )

    else:

        summary = (
            f"NQ and ES are NOT aligned. "
            f"NQ shows {nq_structure} while ES shows "
            f"{es_structure}. "
            f"Expect liquidity games, inducement or "
            f"mixed delivery before expansion."
        )

    # =====================================================
    # RETURN
    # =====================================================

    return {

        "aligned": aligned,

        "alignment_strength": alignment_strength,

        "shared_category": shared_category,

        "nq_structure": nq_structure,

        "es_structure": es_structure,

        "nq_category": nq["category"],

        "es_category": es["category"],

        "nq_direction": nq["direction"],

        "es_direction": es["direction"],

        "nq_note": nq["note"],

        "es_note": es["note"],

        "summary": summary
    }
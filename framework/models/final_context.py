# upgrades: market_phase attribute - because eventually Ping decisions will be driven more 
    #  by market phase than by bullish/bearish labels.
    #  values: "aligned_expansion", "compression", "rebalance", "inducement", "post_compression" 
def determine_ping_direction(
    cross_alignment,
    nq_structure,
    es_structure,
    htf_bias,
):
    """
    ==========================================================
    PING DIRECTION ENGINE
    ==========================================================

    Converts:
    - cross asset alignment
    - structure relationships
    - HTF bias

    into:

    - preferred direction
    - confidence
    - inducement context
    - conflict context
    - preferred asset

    ATTRIBUTE PRIORITY BY GROUP
    ---------------------------
    - SAME STRUCUTRE: 
        - Compare in this order
        - Reason: same structure means phase comparison matters most
            1. is_acceptance
            2. is_rebalance
            3. is_reintegration
            4. migration_strength
            5. compression_strength
    - SIMILAR STRUCTURE:
        - Compare in this order
        - Reason: same family means maturity comparison matters most
            1. migration_strength 
            2. is_compression
            3. compression_strength
            4. is_acceptance
            5. is_rebalance
    - CONFLICTING STRUCTURE:
        - Compare in this order
        - Reason: HTF is tie breaker
            1. HTF bias
            2. direction
            3. migration_strength
            4. acceptance vs rebalance

    IMPORTANT
    ---------
    Does NOT:
    - create signals
    - create entries

    Structure blocks still decide:
    - Rocket validity
    - Flush validity
    """

    result = {

        # --------------------------------------------------
        # Direction
        # --------------------------------------------------

        "conflict_resolution_direction": "neutral",

        "confidence": "medium",

        "decision_source": "mixed",

        # --------------------------------------------------
        # Alignment Context
        # --------------------------------------------------

        "alignment_type": (
            cross_alignment["structure_alignment"]
        ),

        "structural_conflict": False,
        
        "true_directional_conflict": False,

        # --------------------------------------------------
        # Asset Leadership
        # --------------------------------------------------

        "leader": None,

        "laggard": None,

        "preferred_asset": None,

        # --------------------------------------------------
        # Inducement Context
        # --------------------------------------------------

        "inducement_risk": "none",

        "inducement_asset": None,

        "require_extra_confirmation": False,

        # --------------------------------------------------
        # Priorities
        # --------------------------------------------------

        "long_priority": 1,

        "short_priority": 1,

        # --------------------------------------------------
        # Diagnostics
        # --------------------------------------------------

        "reason": None,
    }

    # ======================================================
    # LEADER / LAGGARD
    # ======================================================

    migration_score = {
        "strong": 3,
        "moderate": 2,
        "weak": 1,
        None: 0,
    }

    nq_score = migration_score.get(
        nq_structure["migration_strength"],
        0,
    )

    es_score = migration_score.get(
        es_structure["migration_strength"],
        0,
    )

    if nq_score > es_score:

        result["leader"] = "NQ"
        result["laggard"] = "ES"

    elif es_score > nq_score:

        result["leader"] = "ES"
        result["laggard"] = "NQ"

    # ======================================================
    # SAME / SIMILAR STRUCTURES
    # ======================================================

    if (
        cross_alignment["structure_alignment"]
        in ["same", "similar"]
    ):

        result["decision_source"] = "structure"

        # ----------------------------------------------
        # Same directional regime
        # ----------------------------------------------

        if (
            nq_structure["direction"]
            == es_structure["direction"]
        ):

            direction = nq_structure["direction"]

            # result["conflict_resolution_direction"] = direction

            result["confidence"] = "high"

            if direction == "bullish":

                result["long_priority"] = 2
                result["short_priority"] = 0

            else:

                result["long_priority"] = 0
                result["short_priority"] = 2

        # ----------------------------------------------
        # Acceptance vs Rebalance
        # ----------------------------------------------

        if (
            nq_structure["is_acceptance"]
            and es_structure["is_rebalance"]
        ):

            if htf_bias == "bearish":

                result[
                    "inducement_asset"
                ] = "NQ"

                result[
                    "inducement_risk"
                ] = "high"

                result[
                    "require_extra_confirmation"
                ] = True

                result["reason"] = (
                    "acceptance_vs_rebalance"
                )

        elif (
            es_structure["is_acceptance"]
            and nq_structure["is_rebalance"]
        ):

            if htf_bias == "bearish":

                result[
                    "inducement_asset"
                ] = "ES"

                result[
                    "inducement_risk"
                ] = "high"

                result[
                    "require_extra_confirmation"
                ] = True

                result["reason"] = (
                    "acceptance_vs_rebalance"
                )

    # ======================================================
    # CONFLICTING STRUCTURES
    # ======================================================

    else:

        result["decision_source"] = "htf_bias"

        result["structural_conflict"] = True

        result[
            "require_extra_confirmation"
        ] = True

        result["reason"] = (
            "structural_conflict"
        )
        print("nq structure: ", nq_structure)
        result["true_directional_conflict"] = (
            not nq_structure["is_neutral_direction_structure"]
            and
            not es_structure["is_neutral_direction_structure"]
        )

        if htf_bias == "bullish":

            result[
                "conflict_resolution_direction"
            ] = "bullish"

            result["long_priority"] = 2
            result["short_priority"] = 0

        elif htf_bias == "bearish":

            result[
                "conflict_resolution_direction"
            ] = "bearish"

            result["long_priority"] = 0
            result["short_priority"] = 2

    # ======================================================
    # MIGRATION ALIGNMENT ADJUSTMENTS
    # ======================================================

    migration_alignment = (
        cross_alignment["migration_alignment"]
    )

    if migration_alignment == "strong_alignment":

        result["confidence"] = "very_high"

    elif migration_alignment == "weak_alignment":

        result["confidence"] = "high"

    elif migration_alignment in [

        "nq_stronger",
        "es_stronger",

    ]:

        result["confidence"] = "high"

    elif migration_alignment == (
        "compression_vs_migration"
    ):

        result["confidence"] = "medium"

    elif migration_alignment == (
        "migration_divergence"
    ):

        result["confidence"] = "low"

        result[
            "require_extra_confirmation"
        ] = True

    # ======================================================
    # PREFERRED ASSET
    # ======================================================

    #
    # Version 1:
    #
    # Use SMT engine later to override.
    #
    # For now:
    #

    if result["leader"] is not None:

        result["preferred_asset"] = (
            result["leader"]
        )

    # ======================================================
    # STRUCTURAL CONFLICT
    # ======================================================

    if (
        cross_alignment["structure_alignment"]
        == "conflicting"
    ):

        result["structural_conflict"] = True

    return result

def determine_ping_direction_old(
    cross_alignment,
    nq_structure,
    es_structure,
    htf_bias,
):
    """
    ==========================================================
    PING DIRECTION ENGINE
    ==========================================================

    PURPOSE
    -------
    Determines:

    - which side should be prioritized
    - which asset is leading
    - possible inducement asset
    - whether structure or HTF bias is driving
      the decision

    ATTRIBUTE PRIORITY BY GROUP
    ---------------------------
    - SAME STRUCUTRE: 
        - Compare in this order
        - Reason: same structure means phase comparison matters most
            1. is_acceptance
            2. is_rebalance
            3. is_reintegration
            4. migration_strength
            5. compression_strength
    - SIMILAR STRUCTURE:
        - Compare in this order
        - Reason: same family means maturity comparison matters most
            1. migration_strength 
            2. is_compression
            3. compression_strength
            4. is_acceptance
            5. is_rebalance
    - CONFLICTING STRUCTURE:
        - Compare in this order
        - Reason: HTF is tie breaker
            1. HTF bias
            2. direction
            3. migration_strength
            4. acceptance vs rebalance


    IMPORTANT
    ---------
    Does NOT:
    - create signals
    - create entries

    Structure blocks still decide:
    - Rocket validity
    - Flush validity
    """

    result = {

        "conflict_resolution_direction": None,

        "confidence": "medium",

        "decision_source": "mixed",

        "leader": None,

        "laggard": None,

        "possible_inducement_asset": None,

        "reason": None,

        # useful later
        "long_priority": 1,
        "short_priority": 1,
    }

    # ======================================================
    # STRUCTURE TAKES PRIORITY
    # ======================================================

    if cross_alignment["structure_alignment"] in [
        "same",
        "similar",
    ]:
        result["decision_source"] = "structure"

        # --------------------------------------------------
        # SAME DIRECTION
        # --------------------------------------------------

        if (
            nq_structure["direction"]
            == es_structure["direction"]
        ):

            direction = nq_structure["direction"]

            # result["preferred_direction"] = direction

            result["confidence"] = "high"

            result["reason"] = (
                "cross_asset_directional_alignment"
            )

            if direction == "bullish":

                result["long_priority"] = 2
                result["short_priority"] = 0

            else:

                result["long_priority"] = 0
                result["short_priority"] = 2

        # --------------------------------------------------
        # LEADER / LAGGARD
        # --------------------------------------------------

        migration_score = {
            "strong": 3,
            "moderate": 2,
            "weak": 1,
            None: 0,
        }

        nq_score = migration_score.get(
            nq_structure["migration_strength"],
            0,
        )

        es_score = migration_score.get(
            es_structure["migration_strength"],
            0,
        )

        if nq_score > es_score:

            result["leader"] = "NQ"
            result["laggard"] = "ES"

        elif es_score > nq_score:

            result["leader"] = "ES"
            result["laggard"] = "NQ"

        # --------------------------------------------------
        # ACCEPTANCE VS REBALANCE
        # --------------------------------------------------

        if (
            nq_structure["is_acceptance"]
            and es_structure["is_rebalance"]
        ):

            result["leader"] = "NQ"
            result["laggard"] = "ES"

            if htf_bias == "bearish":

                result[
                    "possible_inducement_asset"
                ] = "NQ"

                result["reason"] = (
                    "acceptance_vs_rebalance"
                )

        elif (
            es_structure["is_acceptance"]
            and nq_structure["is_rebalance"]
        ):

            result["leader"] = "ES"
            result["laggard"] = "NQ"

            if htf_bias == "bearish":

                result[
                    "possible_inducement_asset"
                ] = "ES"

                result["reason"] = (
                    "acceptance_vs_rebalance"
                )

    # ======================================================
    # CONFLICTING STRUCTURES
    # ======================================================

    else:

        result["decision_source"] = "htf_bias"

        result["confidence"] = "medium"

        result["conflict_resolution_direction"] = htf_bias

        result["reason"] = (
            "structural_conflict_htf_override"
        )

        if htf_bias == "bullish":

            result["long_priority"] = 2
            result["short_priority"] = 0

        elif htf_bias == "bearish":

            result["long_priority"] = 0
            result["short_priority"] = 2

    # ======================================================
    # CONFIDENCE ADJUSTMENTS
    # ======================================================

    if (
        cross_alignment["migration_alignment"]
        == "strong_alignment"
    ):

        result["confidence"] = "very_high"

    elif (
        cross_alignment["migration_alignment"]
        == "compression_vs_migration"
    ):

        if result["confidence"] == "very_high":
            result["confidence"] = "high"

    elif (
        cross_alignment["migration_alignment"]
        == "migration_divergence"
    ):

        result["confidence"] = "low"

    return result
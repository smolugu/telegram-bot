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
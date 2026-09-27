def get_preferred_trade_asset(
    nq_structure: str,
    es_structure: str,
    nq_atr_usage: float,
    es_atr_usage: float,
) -> str | None:
    """
    Determines the preferred asset to trade based on relative
    expansion phase and daily ATR consumption.

    Returns:
        "NQ"   -> NQ has greater expansion potential
        "ES"   -> ES has greater expansion potential
        None   -> no clear preference
    """

    # ---------------------------------------------------------
    # Normalize structure names
    # ---------------------------------------------------------

    nq_structure = nq_structure.lower()
    es_structure = es_structure.lower()

    # ---------------------------------------------------------
    # Define expansion phases
    # ---------------------------------------------------------

    nq_in_expansion = nq_structure in {
        "staircase_gap_bullish",
        "staircase_gap_bearish",
        "expansion_bullish",
        "expansion_bearish",
    }

    es_in_expansion = es_structure in {
        "staircase_gap_bullish",
        "staircase_gap_bearish",
        "expansion_bullish",
        "expansion_bearish",
    }

    nq_early = nq_structure in {
        "early_overlap_bullish",
        "early_overlap_bearish",
    }

    es_early = es_structure in {
        "early_overlap_bullish",
        "early_overlap_bearish",
    }

    # ---------------------------------------------------------
    # We only want a phase asymmetry:
    #
    # One asset already expanding while the other is still
    # in early expansion / waiting to resolve compression.
    # ---------------------------------------------------------

    nq_ahead = nq_in_expansion and es_early
    es_ahead = es_in_expansion and nq_early

    if not nq_ahead and not es_ahead:
        return None

    # ---------------------------------------------------------
    # ATR usage confirms which asset has already travelled more.
    # ---------------------------------------------------------

    if nq_ahead:
        if nq_atr_usage > es_atr_usage:
            return "ES"

    if es_ahead:
        if es_atr_usage > nq_atr_usage:
            return "NQ"

    return None
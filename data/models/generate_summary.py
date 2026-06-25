GROUP_NARRATIVES = {

    "compression": {
        "market_state":
            "Market remains in compression with clearly defined liquidity levels.",
        "expected_path":
            "Expect sweep of compression extremes before expansion.",
        "primary_setup":
            "Rocket / Flush from compression extremes",
        "invalidation":
            "Acceptance outside compression range."
    },

    "acceptance": {
        "market_state":
            "Market continues accepting directional prices with conviction.",
        "expected_path":
            "Expect shallow retracement followed by continuation.",
        "primary_setup":
            "Rocket from mitigation",
        "invalidation":
            "Failure to hold acceptance levels."
    },

    "decompression": {
        "market_state":
            "Market has transitioned into active delivery.",
        "expected_path":
            "Expect mitigation before continuation.",
        "primary_setup":
            "Rocket from mitigation levels",
        "invalidation":
            "Acceptance beyond decompression invalidation level."
    },

    "rebalance": {
        "market_state":
            "Market has rebalanced and may react strongly from known levels.",
        "expected_path":
            "Expect reaction from key levels before directional commitment.",
        "primary_setup":
            "Reaction trade from rebalance levels",
        "invalidation":
            "Acceptance beyond rebalance range."
    },

    "reintegration": {
        "market_state":
            "Previous delivery has weakened and price is reintegrating.",
        "expected_path":
            "Expect reaction from reintegration extremes.",
        "primary_setup":
            "Rocket / Flush from reintegration levels",
        "invalidation":
            "Failure to hold reintegration structure."
    },

    "value_flip": {
        "market_state":
            "Strong migration is already underway.",
        "expected_path":
            "Expect shallow retracement before continuation.",
        "primary_setup":
            "Retest and continuation",
        "invalidation":
            "Acceptance back into previous value."
    }
}


def determine_preferred_asset(nq, es):

    #
    # Compression structures get priority
    # because execution levels are known.
    #

    if nq["is_compression"] and not es["is_compression"]:
        return "NQ"

    if es["is_compression"] and not nq["is_compression"]:
        return "ES"

    #
    # Otherwise use PQS
    #

    return "NQ" if nq["pqs"] >= es["pqs"] else "ES"


def generate_summary(
    nq_structure,
    es_structure,
):

    preferred_asset = determine_preferred_asset(
        nq_structure,
        es_structure
    )

    preferred = (
        nq_structure
        if preferred_asset == "NQ"
        else es_structure
    )

    secondary = (
        es_structure
        if preferred_asset == "NQ"
        else nq_structure
    )

    #
    # Narrative
    #

    narrative = GROUP_NARRATIVES[
        preferred["structure_group"]
    ]

    #
    # Market State
    #

    market_state = (
        f"{preferred_asset} is exhibiting "
        f"{preferred['structure_group']} behaviour. "
        f"{narrative['market_state']}"
    )

    #
    # If assets differ significantly,
    # explain relationship.
    #

    if (
        preferred["structure_group"]
        != secondary["structure_group"]
    ):

        market_state += (
            f" {('ES' if preferred_asset == 'NQ' else 'NQ')} "
            f"remains in "
            f"{secondary['structure_group']}."
        )

    #
    # Key Levels
    #

    key_levels = []

    for level_name, level_value in preferred.get(
        "reaction_level_values",
        {}
    ).items():

        key_levels.append(
            f"{level_name}: {level_value}"
        )

    #
    # Confidence
    #

    confidence = preferred["pqs"]

    #
    # Trade Bias
    #

    bias = preferred["direction"].capitalize()

    #
    # Build Summary
    #

    summary = {
        "market_narrative": market_state,

        "preferred_asset": preferred_asset,

        "confidence": confidence,

        "trade_bias": bias,

        "expected_path":
            narrative["expected_path"],

        "primary_setup":
            narrative["primary_setup"],

        "key_levels":
            key_levels,

        "invalidation":
            narrative["invalidation"]
    }

    return summary
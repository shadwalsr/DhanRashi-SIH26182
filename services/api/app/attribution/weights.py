"""Versioned weights configuration and renormalization for Attribution Engine (FR-ATT-03, G2)."""

DEFAULT_WEIGHTS_VERSION = "v1.0.0"

DEFAULT_WEIGHTS: dict[str, float] = {
    "percentage_of_traced_funds": 0.25,
    "known_deposit_match": 0.20,
    "intelligence_provider_confidence": 0.15,
    "funds_reached": 0.10,
    "graph_distance": 0.08,
    "temporal_continuity": 0.07,
    "cluster_association": 0.05,
    "recency": 0.05,
    "transaction_frequency": 0.05,
    "cross_chain_evidence": 0.10,
}


def renormalize_weights(
    base_weights: dict[str, float],
    applicable_features: set[str],
) -> dict[str, float]:
    """Renormalizes weights across applicable features so that sum(weights) == 1.0 (G2).
    Inapplicable features receive weight 0.0.
    """
    applicable_sum = sum(base_weights.get(k, 0.0) for k in applicable_features)

    # If applicable sum is zero or empty, fall back to equal distribution among applicable
    if applicable_sum <= 0.0:
        if not applicable_features:
            return {k: 0.0 for k in base_weights}
        equal_weight = 1.0 / len(applicable_features)
        return {
            k: (equal_weight if k in applicable_features else 0.0)
            for k in base_weights
        }

    renormalized: dict[str, float] = {}
    for feature_name, w in base_weights.items():
        if feature_name in applicable_features:
            renormalized[feature_name] = w / applicable_sum
        else:
            renormalized[feature_name] = 0.0

    return renormalized

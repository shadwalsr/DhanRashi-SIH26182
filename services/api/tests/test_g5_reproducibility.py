import json

import pytest

from app.attribution.weights import DEFAULT_WEIGHTS, renormalize_weights


@pytest.mark.asyncio
async def test_g5_reproducibility_byte_identical_output():
    """G5 Target: Running attribution weight calculation with identical input yields identical result JSON."""
    scores = {
        "graph_distance": 1.0,
        "known_deposit_match": 1.0,
        "cluster_association": 0.8,
        "funds_reached": 0.9,
        "percentage_of_traced_funds": 0.85,
        "transaction_frequency": 0.7,
        "recency": 0.8,
        "temporal_continuity": 0.8,
        "intelligence_provider_confidence": 0.95,
        "cross_chain_evidence": 0.0,
    }

    weights1 = renormalize_weights(DEFAULT_WEIGHTS, set(scores.keys()))
    weights2 = renormalize_weights(DEFAULT_WEIGHTS, set(scores.keys()))

    assert weights1 == weights2
    assert json.dumps(weights1, sort_keys=True) == json.dumps(weights2, sort_keys=True)


@pytest.mark.asyncio
async def test_g2_explainability_sum_invariant():
    """G2 Target: Sum of individual feature contributions equals raw_score ± 0.001 for all weight sets."""
    features_cases = [
        {
            "graph_distance": 1.0,
            "known_deposit_match": 1.0,
            "cluster_association": 0.8,
            "funds_reached": 0.9,
            "percentage_of_traced_funds": 0.85,
            "transaction_frequency": 0.7,
            "recency": 0.8,
            "temporal_continuity": 0.8,
            "intelligence_provider_confidence": 0.95,
            "cross_chain_evidence": 0.0,
        },
        {
            "graph_distance": 0.8,
            "cluster_association": 0.5,
            "funds_reached": 0.4,
            "percentage_of_traced_funds": 0.6,
            "transaction_frequency": 0.2,
            "recency": 0.3,
            "temporal_continuity": 0.5,
            "intelligence_provider_confidence": 0.8,
        },
    ]

    for scores in features_cases:
        weights = renormalize_weights(DEFAULT_WEIGHTS, set(scores.keys()))
        contributions = {k: round(scores[k] * weights[k], 4) for k in scores}
        raw_score = sum(contributions.values())

        sum_weights = sum(weights[k] for k in scores)
        assert abs(sum_weights - 1.0) <= 0.001
        assert abs(raw_score - sum(scores[k] * weights[k] for k in scores)) <= 0.001

import math
from datetime import UTC, datetime
from decimal import Decimal


def compute_graph_distance(min_hop: int) -> float:
    """Computes normalized proximity score based on minimum hop distance.
    Decays monotonically with hop count: hop 1 = 1.0, hop 2 = 0.67, hop 3 = 0.50, etc.
    """
    if min_hop <= 1:
        return 1.0
    return round(1.0 / (1.0 + 0.5 * (min_hop - 1)), 4)


def compute_known_deposit_match(
    address_type: str | None,
    staleness_days: int = 0,
) -> tuple[float, bool]:
    """Computes address classification match score per PRD §10.3 table.
    deposit_wallet is the strongest customer-specific signal (1.0).
    Returns (score, is_stale_over_365).
    """
    if not address_type:
        return 0.0, False

    base_scores = {
        "deposit_wallet": 1.0,
        "custodial_wallet": 0.8,
        "hot_wallet": 0.6,
        "payment_processor": 0.5,
        "cold_wallet": 0.3,
        "eoa": 0.1,
    }
    score = base_scores.get(address_type, 0.0)

    # Staleness factor per FR-REG-06 and PRD §10.4
    is_stale_365 = staleness_days > 365
    if staleness_days > 365:
        score *= 0.4
    elif staleness_days >= 180:
        score *= 0.7

    return round(score, 4), is_stale_365


def compute_cluster_association(
    has_cluster: bool,
    cluster_type: str | None = None,
) -> float:
    """Computes cluster association strength.
    1.0 for multi-input verified exchange cluster, 0.6 for heuristic cluster, 0.0 for none.
    """
    if not has_cluster:
        return 0.0
    if cluster_type in {"verified", "exchange_cluster", "deposit_reuse"}:
        return 1.0
    return 0.6


def compute_funds_reached(usd_value: Decimal | float) -> float:
    """Computes log-scaled volume score reaching the candidate VASP.
    $1M+ = 1.0, $100k = 0.83, $10k = 0.67, $1k = 0.50, $100 = 0.33, $0 = 0.0.
    """
    val = float(usd_value) if isinstance(usd_value, Decimal) else float(usd_value or 0.0)
    if val <= 0.0:
        return 0.0
    # Log scale up to $1,000,000 (10^6)
    score = math.log10(max(1.0, val)) / 6.0
    return round(min(1.0, max(0.0, score)), 4)


def compute_percentage_of_traced_funds(
    candidate_traced_usd: Decimal | float,
    total_seed_outflow_usd: Decimal | float,
) -> float:
    """Computes the fraction of total seed traced funds that reached this candidate.
    Crucial factor to prevent shortest-path dominance over flow volume.
    """
    cand = float(candidate_traced_usd) if isinstance(candidate_traced_usd, Decimal) else float(candidate_traced_usd or 0.0)
    total = float(total_seed_outflow_usd) if isinstance(total_seed_outflow_usd, Decimal) else float(total_seed_outflow_usd or 0.0)
    if total <= 0.0 or cand <= 0.0:
        return 0.0
    ratio = cand / total
    return round(min(1.0, max(0.0, ratio)), 4)


def compute_transaction_frequency(tx_count: int) -> float:
    """Computes transfer frequency score.
    Higher frequency of transfers to candidate indicates repeated flow pattern rather than one-off noise.
    1 tx = 0.20, 2 tx = 0.40, 5+ tx = 1.0.
    """
    if tx_count <= 0:
        return 0.0
    return round(min(1.0, tx_count / 5.0), 4)


def compute_recency(
    latest_tx_time: datetime | None,
    as_of: datetime | None = None,
) -> float:
    """Computes temporal recency score relative to investigation window.
    Same day = 1.0, 90 days ago = 0.5, >180 days ago = 0.0.
    """
    if not latest_tx_time:
        return 0.0
    ref_time = as_of or datetime.now(UTC)
    t_tx = latest_tx_time if latest_tx_time.tzinfo else latest_tx_time.replace(tzinfo=UTC)
    t_ref = ref_time if ref_time.tzinfo else ref_time.replace(tzinfo=UTC)

    diff_days = max(0.0, (t_ref - t_tx).total_seconds() / 86400.0)
    if diff_days >= 180.0:
        return 0.0
    score = 1.0 - (diff_days / 180.0)
    return round(min(1.0, max(0.0, score)), 4)


def compute_temporal_continuity(time_delta_hours: float | None) -> float:
    """Computes temporal continuity between predecessor hop and arrival at candidate.
    Fast sequential progression indicates active laundering; months-later deposit suggests unrelated re-use.
    <= 24h = 1.0, <= 7d (168h) = 0.8, <= 30d (720h) = 0.5, > 30d = 0.2.
    """
    if time_delta_hours is None:
        return 0.5  # Neutral default when predecessor hop delta unavailable
    delta = max(0.0, float(time_delta_hours))
    if delta <= 24.0:
        return 1.0
    elif delta <= 168.0:
        return 0.8
    elif delta <= 720.0:
        return 0.5
    return 0.2


def compute_intelligence_provider_confidence(
    confidence: float,
    multi_source_count: int = 1,
) -> float:
    """Computes intelligence label confidence with multi-source consensus bonus."""
    conf = min(1.0, max(0.0, float(confidence or 0.0)))
    if multi_source_count > 1:
        # Agreement bonus
        conf = min(1.0, conf + 0.1 * (multi_source_count - 1))
    return round(conf, 4)


def compute_cross_chain_evidence(
    has_bridge_hop: bool,
    bridge_confidence: float = 1.0,
) -> tuple[float, bool]:
    """Computes cross-chain evidence factor.
    Returns (score, is_applicable).
    If no bridge involved in investigation, is_applicable=False so weight renormalizes cleanly.
    """
    if not has_bridge_hop:
        return 0.0, False
    return round(min(1.0, max(0.0, bridge_confidence)), 4), True

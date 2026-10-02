"""Attribution caps (CAP-01 to CAP-08) and tier assignment (FR-ATT-04)."""

from typing import Any

from app.domain.enums import AttributionTier
from app.domain.models import AppliedCap


def cap_01_minimum_evidence_gate(has_qualifying_evidence: bool) -> tuple[bool, float, str | None]:
    """CAP-01: No attribution without >= 1 qualifying evidence record (FR-ATT-05)."""
    if not has_qualifying_evidence:
        return True, 0.00, "INSUFFICIENT EVIDENCE: No qualifying registry or intelligence label found."
    return False, 1.00, None


def cap_02_high_degree_intermediary(traversed_high_degree_hub: bool) -> tuple[bool, float, str | None]:
    """CAP-02: Path traversed a high-degree intermediary/service hub."""
    if traversed_high_degree_hub:
        return True, 0.50, "CAP-02: Path traversed a high-degree service hub or mixing intermediary."
    return False, 1.00, None


def cap_03_unresolved_flow(unresolved_percentage: float) -> tuple[bool, float, str | None]:
    """CAP-03: More than 60% of total funds are unresolved/untraced."""
    if unresolved_percentage > 0.60:
        return True, 0.60, f"CAP-03: Dominant unresolved flow ({round(unresolved_percentage * 100, 1)}% untraced)."
    return False, 1.00, None


def cap_04_conflicting_or_disputed_labels(
    has_conflicting_labels: bool,
    is_disputed: bool,
) -> tuple[bool, float, str | None]:
    """CAP-04: Conflicting or disputed registry/intelligence labels (PRD §10.4)."""
    if has_conflicting_labels or is_disputed:
        reason = "CAP-04: Disputed label status." if is_disputed else "CAP-04: Conflicting VASP labels from multiple sources."
        return True, 0.50, reason
    return False, 1.00, None


def cap_05_ambiguous_cross_chain(
    is_cross_chain_ambiguous: bool,
    cross_chain_confidence: float = 1.0,
) -> tuple[bool, float, str | None]:
    """CAP-05: Ambiguous cross-chain bridge match (confidence < 0.80 or multiple candidates)."""
    if is_cross_chain_ambiguous or (cross_chain_confidence < 0.80 and cross_chain_confidence > 0.0):
        return True, 0.65, "CAP-05: Ambiguous cross-chain bridge match."
    return False, 1.00, None


def cap_06_incomplete_data(is_truncated_path: bool) -> tuple[bool, float, str | None]:
    """CAP-06: Incomplete blockchain data or branch truncation along supporting path (PRD §8.5, Row 14)."""
    if is_truncated_path:
        return True, 0.70, "CAP-06: Incomplete blockchain data or explosion truncation on supporting path."
    return False, 1.00, None


def cap_07_stale_label(is_stale_over_365: bool) -> tuple[bool, float, str | None]:
    """CAP-07: Stale label over 365 days since curator verification (PRD §10.4, FR-REG-06)."""
    if is_stale_over_365:
        return True, 0.60, "CAP-07: Stale intelligence label (last verified > 365 days ago)."
    return False, 1.00, None


def cap_08_low_flow_proportion(flow_percentage: float) -> tuple[bool, float, str | None]:
    """CAP-08: Percentage of traced funds reaching this candidate is below 10%."""
    if flow_percentage < 0.10:
        return True, 0.45, f"CAP-08: Low flow proportion ({round(flow_percentage * 100, 1)}% < 10%)."
    return False, 1.00, None


def evaluate_caps(
    raw_score: float,
    context: dict[str, Any],
) -> tuple[float, list[AppliedCap], list[str]]:
    """Evaluates CAP-01 through CAP-08, applying caps in descending restriction order.
    Returns (capped_score, list_of_applied_caps, limitations_statements).
    """
    applied_caps: list[AppliedCap] = []
    limitations: list[str] = []
    current_score = raw_score

    # Check all cap rules
    cap_rules = [
        ("CAP-01", cap_01_minimum_evidence_gate(context.get("has_qualifying_evidence", True))),
        ("CAP-02", cap_02_high_degree_intermediary(context.get("traversed_high_degree_hub", False))),
        ("CAP-03", cap_03_unresolved_flow(context.get("unresolved_percentage", 0.0))),
        ("CAP-04", cap_04_conflicting_or_disputed_labels(context.get("has_conflicting_labels", False), context.get("is_disputed", False))),
        ("CAP-05", cap_05_ambiguous_cross_chain(context.get("is_cross_chain_ambiguous", False), context.get("cross_chain_confidence", 1.0))),
        ("CAP-06", cap_06_incomplete_data(context.get("is_truncated_path", False))),
        ("CAP-07", cap_07_stale_label(context.get("is_stale_over_365", False))),
        ("CAP-08", cap_08_low_flow_proportion(context.get("flow_percentage", 1.0))),
    ]

    for cap_code, (triggered, max_allowed, reason) in cap_rules:
        if triggered:
            applied_caps.append(
                AppliedCap(
                    cap_code=cap_code,
                    max_score=max_allowed,
                    reason=reason or f"{cap_code} triggered.",
                )
            )
            limitations.append(reason or cap_code)
            current_score = min(current_score, max_allowed)

    # Additional contextual limitations (PRD §10.3)
    if context.get("is_payment_processor", False):
        limitations.append("Target address belongs to a payment processor; funds may represent merchant gateway processing rather than customer exchange accounts.")

    if context.get("is_hot_wallet", False):
        limitations.append("Target address is an operational hot wallet; funds may represent pooled internal exchange rebalancing rather than direct user deposit.")

    if current_score < 0.40:
        limitations.append("Score is below the 0.40 threshold. Do not use as sole basis for statutory disclosure request.")

    return round(current_score, 4), applied_caps, limitations


def assign_tier(score: float) -> str:
    """Assigns standard attribution tier per PRD §11.4."""
    if score >= 0.75:
        return AttributionTier.HIGH.value
    elif score >= 0.50:
        return AttributionTier.MEDIUM.value
    elif score >= 0.40:
        return AttributionTier.LOW.value
    return AttributionTier.INSUFFICIENT.value

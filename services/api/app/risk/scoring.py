from app.domain.enums import RiskTier
from app.domain.models import RiskSignal


def calculate_risk_score(signals: list[RiskSignal]) -> tuple[int, RiskTier, str]:
    """Aggregates risk signals into an overall risk score (0-100), tier, and summary (FR-RISK-02).

    Tiers:
    - LOW: 0 - 29
    - MEDIUM: 30 - 59
    - HIGH: 60 - 84  (Case 4 produces 72 / HIGH)
    - SEVERE: 85 - 100
    """
    if not signals:
        return 0, RiskTier.LOW, "No elevated risk signals detected across transaction flow."

    total_score = sum(s.score for s in signals)
    bounded_score = min(100, max(0, total_score))

    if bounded_score >= 85:
        tier = RiskTier.SEVERE
    elif bounded_score >= 60:
        tier = RiskTier.HIGH
    elif bounded_score >= 30:
        tier = RiskTier.MEDIUM
    else:
        tier = RiskTier.LOW

    signal_names = [s.name for s in signals]
    summary = f"Risk score {bounded_score}/100 ({tier.value}). Detected {len(signals)} signal(s): {'; '.join(signal_names)}."

    return bounded_score, tier, summary

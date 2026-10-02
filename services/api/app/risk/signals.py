from datetime import datetime
from decimal import Decimal
from typing import Any

from app.domain.enums import AddressType, RiskSignalCode
from app.domain.models import RiskSignal

MIXER_KEYWORDS = {"mixer", "tornado", "blender", "chipmixer", "railgun", "cyclone", "sinbad", "wasabi"}
HIGH_RISK_KEYWORDS = {"sanction", "darknet", "ransomware", "exploit", "hack", "scam", "phishing"}


def detect_mixer_interaction(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    seed_address: str,
) -> RiskSignal | None:
    """Detects direct or multi-hop interaction with cryptocurrency mixers (FR-RISK-01).

    Mixers obfuscate origin and trail; interaction confers 30 risk points.
    """
    mixer_nodes = []
    for n in nodes:
        addr = str(n.get("address", "")).lower()
        if addr == seed_address.lower():
            continue
        addr_type = str(n.get("address_type", "")).lower()
        node_type = str(n.get("node_type", "")).lower()
        label = str(n.get("label", "")).lower()

        is_mixer = (
            addr_type == AddressType.MIXER.value
            or node_type == "mixer"
            or any(kw in label for kw in MIXER_KEYWORDS)
        )
        if is_mixer:
            mixer_nodes.append(n)

    if not mixer_nodes:
        return None

    mixer_names = [str(n.get("label") or n.get("address") or "") for n in mixer_nodes]
    return RiskSignal(
        signal_code=RiskSignalCode.MIXER_INTERACTION.value,
        name="Mixer Interaction Detected",
        score=30,
        weight=0.30,
        description=f"Transaction graph interacts with known mixer/tumbler services: {', '.join(mixer_names[:3])}",
        metadata={"mixer_count": len(mixer_nodes), "mixers": mixer_names},
    )


def detect_peel_chain(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    seed_address: str,
) -> RiskSignal | None:
    """Detects peel chain pattern: successive transactions where funds are split,

    peeling off smaller/change amounts while passing the bulk forward (FR-RISK-01).
    Confers 24 risk points.
    """
    if len(edges) < 2:
        return None

    # Group outgoing edges by source
    out_by_source: dict[str, list[dict[str, Any]]] = {}
    for e in edges:
        src = str(e.get("source_key", "")).lower()
        out_by_source.setdefault(src, []).append(e)

    peel_hops = 0
    peel_details = []

    for src, out_edges in out_by_source.items():
        # A peel pattern typically has an intermediary splitting funds (1-to-2 or asymmetric transfers)
        if len(out_edges) >= 2:
            amounts = []
            for oe in out_edges:
                amt = oe.get("usd_value") or oe.get("amount") or 0
                amounts.append(float(amt))
            amounts.sort()
            # If one output is significantly smaller than the other (change peel)
            if amounts[0] > 0 and (amounts[-1] / amounts[0] >= 1.5):
                peel_hops += 1
                peel_details.append(src)

    # Alternatively, sequential hops where single intermediary hops continue
    hops_present = {e.get("hop") for e in edges if e.get("hop")}
    if len(hops_present) >= 2 and peel_hops >= 1:
        return RiskSignal(
            signal_code=RiskSignalCode.PEEL_CHAIN.value,
            name="Peel Chain Topology",
            score=24,
            weight=0.24,
            description=f"Identified structured peel chain behavior across {peel_hops} splitting intermediate nodes.",
            metadata={"peel_hops": peel_hops, "intermediaries": peel_details[:5]},
        )

    # Also detect if multiple hops exist with high hop depth and low fan-out
    if len(hops_present) >= 3 and len(edges) >= 3:
        return RiskSignal(
            signal_code=RiskSignalCode.PEEL_CHAIN.value,
            name="Peel Chain Topology",
            score=24,
            weight=0.24,
            description=f"Identified structured multi-hop sequential peel chain behavior over {len(hops_present)} hops.",
            metadata={"hops": sorted(hops_present)},
        )

    return None


def detect_rapid_movement(
    edges: list[dict[str, Any]],
    threshold_seconds: int = 900,  # 15 minutes
) -> RiskSignal | None:
    """Detects rapid movement of funds between successive hops (FR-RISK-01).

    Time interval < 15 minutes indicates automated hopping; confers 18 risk points.
    """
    if len(edges) < 2:
        return None

    # Sort edges chronologically
    valid_edges = []
    for e in edges:
        ts = e.get("timestamp")
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts)
            except ValueError:
                continue
        if isinstance(ts, datetime):
            valid_edges.append((ts, e))

    valid_edges.sort(key=lambda x: x[0])
    if len(valid_edges) < 2:
        return None

    rapid_transfers = 0
    min_delta = None

    for i in range(1, len(valid_edges)):
        prev_ts, prev_e = valid_edges[i - 1]
        curr_ts, curr_e = valid_edges[i]

        # Check if consecutive hops (e.g. destination of prev == source of curr or hop increased)
        prev_dest = str(prev_e.get("destination_key", "")).lower()
        curr_src = str(curr_e.get("source_key", "")).lower()

        delta = (curr_ts - prev_ts).total_seconds()
        if (0 <= delta <= threshold_seconds) and (prev_dest == curr_src or curr_e.get("hop", 0) > prev_e.get("hop", 0)):
            rapid_transfers += 1
            if min_delta is None or delta < min_delta:
                min_delta = delta

    if rapid_transfers > 0:
        return RiskSignal(
            signal_code=RiskSignalCode.RAPID_MOVEMENT.value,
            name="Rapid Automated Movement",
            score=18,
            weight=0.18,
            description=f"Detected rapid fund transfer across hops within {int(min_delta or 0)}s (< 15 min threshold).",
            metadata={"rapid_hop_count": rapid_transfers, "min_interval_seconds": min_delta},
        )

    return None


def detect_high_value_transfers(
    edges: list[dict[str, Any]],
    high_value_threshold: Decimal = Decimal("10000.00"),
    cumulative_threshold: Decimal = Decimal("50000.00"),
) -> RiskSignal | None:
    """Detects single high-value transfers (>= $10,000) or cumulative volume (>= $50,000) (FR-RISK-01).

    Confers 10 risk points.
    """
    high_val_count = 0
    total_usd = Decimal(0)

    for e in edges:
        usd = e.get("usd_value")
        if usd is not None:
            val = Decimal(str(usd))
            total_usd += val
            if val >= high_value_threshold:
                high_val_count += 1

    if high_val_count > 0 or total_usd >= cumulative_threshold:
        return RiskSignal(
            signal_code=RiskSignalCode.HIGH_VALUE_TRANSFERS.value,
            name="High-Value Transfers",
            score=10,
            weight=0.10,
            description=f"High-value transfers observed: {high_val_count} transfers >= ${high_value_threshold:,.0f} (total: ${total_usd:,.2f}).",
            metadata={"high_value_transfers": high_val_count, "total_traced_usd": float(total_usd)},
        )

    return None


def detect_high_risk_counterparty(
    nodes: list[dict[str, Any]],
    seed_address: str,
) -> RiskSignal | None:
    """Detects interaction with flagged illicit counterparties (FR-RISK-01).

    Sanctioned entities, exploit addresses, or darknet services; confers 25 risk points.
    """
    flagged = []
    for n in nodes:
        addr = str(n.get("address", "")).lower()
        if addr == seed_address.lower():
            continue
        label = str(n.get("label", "")).lower()
        addr_type = str(n.get("address_type", "")).lower()

        if any(kw in label for kw in HIGH_RISK_KEYWORDS) or addr_type in {"sanctioned", "darknet", "exploit"}:
            flagged.append(n)

    if flagged:
        names = [str(n.get("label") or n.get("address") or "") for n in flagged]
        return RiskSignal(
            signal_code=RiskSignalCode.HIGH_RISK_COUNTERPARTY.value,
            name="High-Risk Counterparty Association",
            score=25,
            weight=0.25,
            description=f"Direct or transitive association with flagged high-risk entities: {', '.join(names[:3])}",
            metadata={"flagged_count": len(flagged), "counterparties": names},
        )

    return None

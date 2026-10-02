from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.attribution.caps import assign_tier, evaluate_caps
from app.attribution.features import (
    compute_cluster_association,
    compute_cross_chain_evidence,
    compute_funds_reached,
    compute_graph_distance,
    compute_intelligence_provider_confidence,
    compute_known_deposit_match,
    compute_percentage_of_traced_funds,
    compute_recency,
    compute_temporal_continuity,
    compute_transaction_frequency,
)
from app.attribution.weights import DEFAULT_WEIGHTS, DEFAULT_WEIGHTS_VERSION, renormalize_weights
from app.db.models import (
    AttributionResultModel,
    GraphEdgeModel,
    GraphNodeModel,
    Investigation,
    Vasp,
    VaspAddress,
)
from app.domain.models import (
    AttributionFactor,
    AttributionResponse,
    CandidateAttribution,
)


class AttributionEngine:
    """Core Attribution Engine ranking candidate VASPs by explainable weighted features (PRD §11, FR-ATT-01..09)."""

    def __init__(self, db: AsyncSession, evidence_engine: Any | None = None):
        self.db = db
        self.evidence_engine = evidence_engine

    async def run(
        self,
        investigation_id: UUID,
        weights_version: str = DEFAULT_WEIGHTS_VERSION,
    ) -> AttributionResponse:
        """Executes candidate discovery, feature computation, weight renormalization,
        cap evaluation, and persists versioned results.
        """
        # 1. Fetch investigation record
        inv_stmt = select(Investigation).where(Investigation.id == investigation_id)
        inv_res = await self.db.execute(inv_stmt)
        inv = inv_res.scalar_one_or_none()
        if not inv:
            raise ValueError(f"Investigation {investigation_id} not found.")

        # 2. Fetch all graph nodes and edges
        nodes_stmt = select(GraphNodeModel).where(GraphNodeModel.investigation_id == investigation_id)
        nodes_res = await self.db.execute(nodes_stmt)
        all_nodes = nodes_res.scalars().all()

        edges_stmt = (
            select(GraphEdgeModel)
            .where(GraphEdgeModel.investigation_id == investigation_id)
            .order_by(GraphEdgeModel.timestamp.asc())
        )
        edges_res = await self.db.execute(edges_stmt)
        all_edges = edges_res.scalars().all()

        # 3. Candidate Discovery (FR-ATT-01):
        # Only nodes with vasp_id set. Mixers and bridges NEVER appear as candidates.
        excluded_types = {"mixer", "bridge"}
        vasp_nodes = [
            n for n in all_nodes
            if n.vasp_id
            and (n.address_type or "").lower() not in excluded_types
            and (n.node_type or "").lower() not in excluded_types
        ]

        # Group nodes by vasp_id
        vasp_node_groups: dict[str, list[GraphNodeModel]] = {}
        for n in vasp_nodes:
            assert n.vasp_id is not None
            vasp_node_groups.setdefault(n.vasp_id, []).append(n)

        # Total seed outflow (for percentage_of_traced_funds)
        seed_key = f"{inv.blockchain.lower()}:{inv.wallet_address.lower()}"
        seed_edges = [e for e in all_edges if e.source_key == seed_key]
        total_seed_outflow = sum((e.usd_value or Decimal(0) for e in seed_edges), start=Decimal(0))

        # Check evidence gate: if no VASP candidates found (FR-ATT-05, Failure Matrix Row 4)
        if not vasp_node_groups:
            return AttributionResponse(
                investigation_id=investigation_id,
                version=inv.run_no or 1,
                top_candidate=None,
                competing_candidates=False,
                margin=None,
                candidates=[],
                evidence_gate_passed=False,
                weights_version=weights_version,
                registry_snapshot_id=inv.registry_snapshot_id,
                calculated_at=datetime.now(UTC),
            )

        # Determine version for persistence (FR-ATT-08)
        last_ver_stmt = (
            select(func.max(AttributionResultModel.version))
            .where(AttributionResultModel.investigation_id == investigation_id)
        )
        last_version = await self.db.scalar(last_ver_stmt) or 0
        new_version = last_version + 1

        # Check graph truncation for CAP-06
        is_partial = inv.status == "PARTIAL" or bool(inv.partial_reasons)

        # 4. Score each candidate VASP
        candidates: list[CandidateAttribution] = []

        for vasp_id, nodes in vasp_node_groups.items():
            candidate_attr = await self._score_candidate(
                vasp_id=vasp_id,
                nodes=nodes,
                all_edges=all_edges,
                total_seed_outflow=total_seed_outflow,
                is_partial=is_partial,
                inv=inv,
                weights_version=weights_version,
            )
            candidates.append(candidate_attr)

        # 5. Rank candidates by final_score descending
        candidates.sort(key=lambda c: (c.final_score, c.raw_score), reverse=True)
        for i, c in enumerate(candidates, start=1):
            c.rank = i

        # 6. Competing Candidates Detection (FR-ATT-06):
        # Flag if margin between top 2 candidates is < 0.15
        competing = False
        margin: float | None = None
        if len(candidates) >= 2:
            margin = round(candidates[0].final_score - candidates[1].final_score, 4)
            if margin < 0.15:
                competing = True
                candidates[0].competing = True
                candidates[1].competing = True

        # 7. Persist to attribution_results (FR-ATT-08)
        for c in candidates:
            db_record = AttributionResultModel(
                id=uuid4(),
                investigation_id=investigation_id,
                version=new_version,
                candidate_vasp_id=c.vasp_id,
                candidate_vasp_name=c.vasp_name,
                rank=c.rank,
                score=c.final_score,
                tier=c.tier,
                competing_candidates=competing,
                evidence_gate_passed=c.evidence_gate_passed,
                disposition="pending",
                weights_version=weights_version,
                registry_snapshot_id=inv.registry_snapshot_id,
                factors_json={f.name: f.model_dump() for f in c.factors},
                caps_json=[cap.model_dump() for cap in c.caps_applied],
                limitations_json=c.limitations,
                supporting_addresses=c.supporting_addresses,
                evidence_references=c.evidence_references,
            )
            self.db.add(db_record)

        await self.db.commit()

        top_cand = candidates[0] if candidates else None

        return AttributionResponse(
            investigation_id=investigation_id,
            version=new_version,
            top_candidate=top_cand,
            competing_candidates=competing,
            margin=margin,
            candidates=candidates,
            evidence_gate_passed=True,
            weights_version=weights_version,
            registry_snapshot_id=inv.registry_snapshot_id,
            calculated_at=datetime.now(UTC),
        )

    async def _score_candidate(
        self,
        vasp_id: str,
        nodes: list[GraphNodeModel],
        all_edges: Sequence[GraphEdgeModel],
        total_seed_outflow: Decimal,
        is_partial: bool,
        inv: Investigation,
        weights_version: str,
    ) -> CandidateAttribution:
        """Computes 10 features, renormalizes weights, applies caps, and builds explanation."""
        # Query canonical VASP name from registry
        vasp_stmt = select(Vasp).where(Vasp.vasp_id == vasp_id)
        vasp_res = await self.db.execute(vasp_stmt)
        vasp_record = vasp_res.scalar_one_or_none()
        vasp_name = vasp_record.name if vasp_record else (nodes[0].label or vasp_id)

        node_keys = {n.node_key for n in nodes}
        supporting_addresses = list({n.address for n in nodes})

        # Edges directed into this candidate's nodes
        inflow_edges = [e for e in all_edges if e.destination_key in node_keys]
        traced_funds = sum((e.traced_usd for e in inflow_edges), start=Decimal(0))
        tx_count = len(inflow_edges)

        min_hop = min(n.hop for n in nodes)
        latest_tx_time = max((e.timestamp for e in inflow_edges), default=None)

        # Check address types & staleness
        addr_types = {n.address_type for n in nodes if n.address_type}
        is_deposit = "deposit_wallet" in addr_types
        is_payment_processor = "payment_processor" in addr_types
        is_hot = "hot_wallet" in addr_types

        # Check registry address details
        addr_stmt = select(VaspAddress).where(VaspAddress.address.in_(supporting_addresses))
        addr_res = await self.db.execute(addr_stmt)
        reg_addrs = addr_res.scalars().all()

        max_confidence = max((a.confidence for a in reg_addrs), default=1.0)
        has_cluster = any(a.cluster_id is not None for a in reg_addrs) or any(n.node_type == "cluster" for n in nodes)

        # Staleness computation
        staleness_days = 0
        is_disputed = False
        now_date = datetime.now(UTC).date()
        for a in reg_addrs:
            if a.status == "disputed":
                is_disputed = True
            if a.last_verified:
                days = (now_date - a.last_verified).days
                staleness_days = max(staleness_days, days)

        # Primary address type for scoring
        primary_addr_type = "deposit_wallet" if is_deposit else (
            "payment_processor" if is_payment_processor else (
                "hot_wallet" if is_hot else (nodes[0].address_type or "deposit_wallet")
            )
        )

        # 1. Compute 10 Features (FR-ATT-02)
        f_distance = compute_graph_distance(min_hop)
        f_deposit, is_stale_365 = compute_known_deposit_match(primary_addr_type, staleness_days)
        f_cluster = compute_cluster_association(has_cluster)
        f_funds_reached = compute_funds_reached(traced_funds)
        f_percentage = compute_percentage_of_traced_funds(traced_funds, total_seed_outflow)
        f_freq = compute_transaction_frequency(tx_count)
        f_recency = compute_recency(latest_tx_time, as_of=inv.created_at)
        f_continuity = compute_temporal_continuity(24.0)  # Sequential trace continuity
        f_intel_conf = compute_intelligence_provider_confidence(max_confidence, len(reg_addrs))
        f_cross_chain, is_xchain_applicable = compute_cross_chain_evidence(has_bridge_hop=False)

        raw_factor_values: dict[str, tuple[float, Any, bool, str]] = {
            "percentage_of_traced_funds": (f_percentage, f"{round(f_percentage * 100, 1)}%", True, "Fraction of total traced funds arriving at candidate"),
            "known_deposit_match": (f_deposit, primary_addr_type, True, "Address type classification match strength"),
            "intelligence_provider_confidence": (f_intel_conf, max_confidence, True, "Registry / intelligence source confidence"),
            "funds_reached": (f_funds_reached, f"${float(traced_funds):,.2f}", True, "Log-scaled absolute USD volume"),
            "graph_distance": (f_distance, f"{min_hop} hops", True, "Graph proximity decay from seed wallet"),
            "temporal_continuity": (f_continuity, "normal", True, "Chronological flow continuity from seed"),
            "cluster_association": (f_cluster, "cluster" if has_cluster else "none", True, "Associated wallet cluster membership"),
            "recency": (f_recency, latest_tx_time.isoformat() if latest_tx_time else "none", True, "Recency of transfer relative to analysis window"),
            "transaction_frequency": (f_freq, f"{tx_count} transfers", True, "Repeated flow frequency"),
            "cross_chain_evidence": (f_cross_chain, "none", is_xchain_applicable, "Cross-chain bridge connection"),
        }

        # 2. Renormalize weights across applicable features (FR-ATT-03, G2)
        applicable_names = {k for k, (_, _, app, _) in raw_factor_values.items() if app}
        effective_weights = renormalize_weights(DEFAULT_WEIGHTS, applicable_names)

        # 3. Compute contributions and raw score (G2: sum == score ± 0.001)
        factors: list[AttributionFactor] = []
        raw_score = 0.0

        for name, (norm_val, raw_val, applicable, desc) in raw_factor_values.items():
            w = effective_weights.get(name, 0.0)
            contrib = round(norm_val * w, 4)
            raw_score += contrib
            factors.append(
                AttributionFactor(
                    name=name,
                    raw_value=raw_val,
                    normalized_score=norm_val,
                    weight=round(w, 4),
                    contribution=contrib,
                    applicable=applicable,
                    description=desc,
                )
            )

        raw_score = round(raw_score, 4)

        # 4. Evaluate Caps CAP-01 through CAP-08 (FR-ATT-04)
        cap_context = {
            "has_qualifying_evidence": True,
            "traversed_high_degree_hub": False,
            "unresolved_percentage": 1.0 - f_percentage,
            "has_conflicting_labels": False,
            "is_disputed": is_disputed,
            "is_cross_chain_ambiguous": False,
            "cross_chain_confidence": 1.0,
            "is_truncated_path": is_partial,
            "is_stale_over_365": is_stale_365,
            "flow_percentage": f_percentage,
            "is_payment_processor": is_payment_processor,
            "is_hot_wallet": is_hot,
        }

        final_score, caps_applied, limitations = evaluate_caps(raw_score, cap_context)
        tier = assign_tier(final_score)

        # Collect or create evidence references (FR-EVD-01)
        evidence_refs: list[str] = []
        if self.evidence_engine is not None:
            ev_rec = await self.evidence_engine.record_vasp_evidence(
                investigation_id=inv.id,
                vasp_id=vasp_id,
                vasp_name=vasp_name,
                address=supporting_addresses[0] if supporting_addresses else "unknown",
                chain=inv.blockchain,
                address_type=primary_addr_type,
                confidence=float(max_confidence),
            )
            evidence_refs.append(str(ev_rec.id))
        else:
            evidence_refs.append(f"REG-{vasp_id}")

        return CandidateAttribution(
            vasp_id=vasp_id,
            vasp_name=vasp_name,
            rank=1,  # will be assigned during sorting
            raw_score=raw_score,
            final_score=final_score,
            tier=tier,
            competing=False,
            evidence_gate_passed=True,
            factors=factors,
            caps_applied=caps_applied,
            limitations=limitations,
            supporting_addresses=supporting_addresses,
            evidence_references=evidence_refs,
        )

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundException
from app.db.models import GraphEdgeModel, GraphNodeModel, Investigation, RiskAssessmentModel
from app.domain.enums import EvidenceType, ProvenanceClass
from app.domain.models import RiskAssessmentRunResponse, RiskSignal
from app.evidence.engine import EvidenceEngine
from app.risk.scoring import calculate_risk_score
from app.risk.signals import (
    detect_high_risk_counterparty,
    detect_high_value_transfers,
    detect_mixer_interaction,
    detect_peel_chain,
    detect_rapid_movement,
)


class RiskEngine:
    """Independent risk scoring engine evaluating laundering patterns and illicit counterparties (FR-RISK-01..04)."""

    def __init__(self, db: AsyncSession, evidence_engine: EvidenceEngine | None = None):
        self.db = db
        self.evidence_engine = evidence_engine or EvidenceEngine(db)

    async def run(
        self,
        investigation_id: UUID,
        version: int | None = None,
    ) -> RiskAssessmentRunResponse:
        """Executes risk analysis for the specified investigation (FR-RISK-01, FR-RISK-02)."""
        inv_stmt = select(Investigation).where(Investigation.id == investigation_id)
        inv_res = await self.db.execute(inv_stmt)
        inv = inv_res.scalar_one_or_none()
        if not inv:
            raise NotFoundException(f"Investigation {investigation_id} not found.")

        # 1. Fetch graph nodes and edges
        nodes_stmt = select(GraphNodeModel).where(GraphNodeModel.investigation_id == investigation_id)
        nodes_res = await self.db.execute(nodes_stmt)
        raw_nodes = list(nodes_res.scalars().all())

        edges_stmt = (
            select(GraphEdgeModel)
            .where(GraphEdgeModel.investigation_id == investigation_id)
            .order_by(GraphEdgeModel.timestamp.asc())
        )
        edges_res = await self.db.execute(edges_stmt)
        raw_edges = list(edges_res.scalars().all())

        # Format node and edge dictionaries for signal evaluation
        nodes_dict: list[dict] = []
        for n in raw_nodes:
            # INVARIANT FR-RISK-04: VASP nodes never carry a risk score
            # We record node attributes for graph topology analysis
            nodes_dict.append({
                "address": n.address,
                "node_type": n.node_type,
                "address_type": n.address_type,
                "vasp_id": n.vasp_id,
                "label": n.label,
                "hop": n.hop,
            })

        edges_dict: list[dict] = []
        for e in raw_edges:
            edges_dict.append({
                "id": str(e.id),
                "source_key": e.source_key,
                "destination_key": e.destination_key,
                "amount": float(e.amount),
                "usd_value": float(e.usd_value) if e.usd_value is not None else None,
                "timestamp": e.timestamp,
                "hop": e.hop,
            })

        seed_addr = inv.wallet_address

        # 2. Evaluate all 5 P0 Risk Signals (FR-RISK-01)
        signals: list[RiskSignal] = []

        # Signal 1: Mixer Interaction (30 pts)
        s_mixer = detect_mixer_interaction(nodes_dict, edges_dict, seed_addr)
        if s_mixer:
            signals.append(s_mixer)

        # Signal 2: Peel Chain Topology (24 pts)
        s_peel = detect_peel_chain(nodes_dict, edges_dict, seed_addr)
        if s_peel:
            signals.append(s_peel)

        # Signal 3: Rapid Movement (18 pts)
        s_rapid = detect_rapid_movement(edges_dict)
        if s_rapid:
            signals.append(s_rapid)

        # Signal 4: High Value Transfers (10 pts)
        s_val = detect_high_value_transfers(edges_dict)
        if s_val:
            signals.append(s_val)

        # Signal 5: High-Risk Counterparty Association (25 pts)
        s_party = detect_high_risk_counterparty(nodes_dict, seed_addr)
        if s_party:
            signals.append(s_party)

        # 3. Aggregate Score and assign Tier (FR-RISK-02)
        overall_score, tier, summary = calculate_risk_score(signals)

        # 4. Generate Evidence Records for detected signals (FR-EVD-01)
        evidence_refs: list[str] = []
        for sig in signals:
            ev_rec = await self.evidence_engine.add_evidence(
                investigation_id=investigation_id,
                evidence_type=EvidenceType.RISK_SIGNAL,
                provenance_class=ProvenanceClass.DERIVED,
                source="engine:risk",
                source_ref=f"signal:{sig.signal_code}",
                data_payload={
                    "signal_code": sig.signal_code,
                    "name": sig.name,
                    "score": sig.score,
                    "weight": sig.weight,
                    "description": sig.description,
                    "metadata": sig.metadata,
                },
            )
            sig.evidence_ids.append(str(ev_rec.id))
            evidence_refs.append(str(ev_rec.id))

        # 5. Persist Risk Assessment with versioning
        if version is None:
            max_ver_stmt = (
                select(RiskAssessmentModel.version)
                .where(RiskAssessmentModel.investigation_id == investigation_id)
                .order_by(RiskAssessmentModel.version.desc())
                .limit(1)
            )
            max_ver_res = await self.db.execute(max_ver_stmt)
            curr_ver = max_ver_res.scalar_one_or_none()
            ver = (curr_ver or 0) + 1
        else:
            ver = version

        signals_json = [s.model_dump() for s in signals]
        assessment_model = RiskAssessmentModel(
            id=uuid4(),
            investigation_id=investigation_id,
            version=ver,
            target_address=inv.wallet_address,
            chain=inv.blockchain,
            overall_score=overall_score,
            tier=tier.value,
            signals_json=signals_json,
            summary=summary,
            evidence_references=evidence_refs,
        )
        self.db.add(assessment_model)
        await self.db.flush()

        now = datetime.now(UTC)
        return RiskAssessmentRunResponse(
            investigation_id=investigation_id,
            target_address=inv.wallet_address,
            chain=inv.blockchain,
            overall_score=overall_score,
            tier=tier.value,
            signals=signals,
            summary=summary,
            evidence_references=evidence_refs,
            calculated_at=now,
        )

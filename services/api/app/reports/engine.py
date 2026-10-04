"""Report Engine: Generates reports, verifies epistemic fact labeling, and manages approval workflows (FR-RPT-01..04, FR-AI-02)."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit_event
from app.core.errors import NotFoundException, PermissionDeniedException
from app.db.models import (
    AttributionResultModel,
    Case,
    CrossChainEventModel,
    EvidenceModel,
    GraphEdgeModel,
    GraphNodeModel,
    Investigation,
    ReportModel,
    RiskAssessmentModel,
    User,
)
from app.domain.enums import AuditOutcome
from app.reports.narrative import generate_template_narrative
from app.reports.pdf import generate_investigation_pdf

VALID_PROVENANCE_CLASSES = {
    "OBSERVED",
    "THIRD-PARTY INTELLIGENCE",
    "DERIVED",
    "INFERENCE",
}

MANDATORY_DISCLAIMER = (
    "Attribution scores represent mathematical correlation over observed blockchain topologies and "
    "intelligence registries. They are investigative leads and do not constitute legal proof of wallet "
    "ownership or criminal culpability. Scores below 0.40 must not be used as the sole basis for statutory disclosure requests."
)


class ReportEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_report(
        self,
        case_id: UUID,
        investigation_id: UUID,
        title: str,
        author: User,
    ) -> ReportModel:
        """Assembles data, verifies epistemic fact labeling, generates PDF, and creates a Report record."""
        # 1. Fetch Case & Investigation
        case_res = await self.db.execute(select(Case).where(Case.id == case_id))
        case = case_res.scalar_one_or_none()
        if not case:
            raise NotFoundException(f"Case {case_id} not found")

        inv_res = await self.db.execute(select(Investigation).where(Investigation.id == investigation_id))
        inv = inv_res.scalar_one_or_none()
        if not inv:
            raise NotFoundException(f"Investigation {investigation_id} not found")

        # 2. Fetch Attribution Top Candidate
        attr_stmt = (
            select(AttributionResultModel)
            .where(AttributionResultModel.investigation_id == investigation_id)
            .order_by(AttributionResultModel.version.desc(), AttributionResultModel.rank.asc())
        )
        attr_res = await self.db.execute(attr_stmt)
        top_attr = attr_res.scalars().first()

        # 3. Fetch Risk Assessment
        risk_stmt = (
            select(RiskAssessmentModel)
            .where(RiskAssessmentModel.investigation_id == investigation_id)
            .order_by(RiskAssessmentModel.version.desc())
        )
        risk_res = await self.db.execute(risk_stmt)
        risk = risk_res.scalars().first()

        # 4. Fetch Evidence Ledger
        ev_stmt = (
            select(EvidenceModel)
            .where(EvidenceModel.investigation_id == investigation_id)
            .order_by(EvidenceModel.sequence_num.asc())
        )
        ev_res = await self.db.execute(ev_stmt)
        evidence_list = ev_res.scalars().all()

        # 5. Fetch Cross-Chain Events
        xchain_stmt = (
            select(CrossChainEventModel)
            .where(CrossChainEventModel.investigation_id == investigation_id)
        )
        xchain_res = await self.db.execute(xchain_stmt)
        xchain_events = xchain_res.scalars().all()

        # 6. Fetch Graph Counts & Traced Funds
        edge_stmt = select(GraphEdgeModel).where(GraphEdgeModel.investigation_id == investigation_id)
        edge_res = await self.db.execute(edge_stmt)
        edges = edge_res.scalars().all()
        traced_usd = sum((e.traced_usd for e in edges), start=Decimal("0.0")) if edges else 0.0

        node_stmt = select(GraphNodeModel).where(GraphNodeModel.investigation_id == investigation_id)
        node_res = await self.db.execute(node_stmt)
        nodes = node_res.scalars().all()

        # 7. Assemble and Validate Facts Table (FR-RPT-02: Automated Check)
        evidence_facts: list[dict[str, Any]] = []
        for ev in evidence_list:
            # Automated check: every fact MUST have a valid provenance class
            if not ev.provenance_class or ev.provenance_class not in VALID_PROVENANCE_CLASSES:
                raise ValueError(
                    f"FR-RPT-02 violation: Evidence row {ev.id} (seq {ev.sequence_num}) has missing or invalid "
                    f"provenance_class: '{ev.provenance_class}'"
                )

            desc = ev.data_payload.get("description") or ev.data_payload.get("note") or ev.evidence_type
            evidence_facts.append({
                "sequence_num": ev.sequence_num,
                "evidence_type": ev.evidence_type,
                "provenance_class": ev.provenance_class,
                "source": ev.source,
                "description": desc,
                "evidence_hash": ev.evidence_hash,
            })

        # Mandatory limitations (FR-RPT-03: cannot be disabled)
        limitations: list[str] = [MANDATORY_DISCLAIMER]
        if top_attr and top_attr.limitations_json:
            for lim in top_attr.limitations_json:
                if lim not in limitations:
                    limitations.append(lim)

        # Build Structured Report Data
        top_cand_dict = {
            "vasp_id": top_attr.candidate_vasp_id if top_attr else "UNKNOWN",
            "vasp_name": top_attr.candidate_vasp_name if top_attr else "No Candidate Found",
            "rank": top_attr.rank if top_attr else 1,
            "raw_score": float(top_attr.score) if top_attr else 0.0,
            "final_score": float(top_attr.score) if top_attr else 0.0,
            "tier": top_attr.tier if top_attr else "INSUFFICIENT",
            "factors": list(top_attr.factors_json.values()) if top_attr and top_attr.factors_json else [],
            "caps_applied": top_attr.caps_json if top_attr and top_attr.caps_json else [],
        }

        risk_dict = {
            "risk_score": risk.overall_score if risk else 0,
            "risk_tier": risk.tier if risk else "LOW",
            "signals": risk.signals_json if risk and risk.signals_json else [],
        }

        xchain_list = [
            {
                "bridge_id": ev.bridge_id,
                "source_chain": ev.source_chain,
                "destination_chain": ev.destination_chain,
                "confidence": ev.confidence,
                "is_ambiguous": ev.is_ambiguous,
            }
            for ev in xchain_events
        ]

        now_utc = datetime.now(UTC)
        report_data = {
            "case_reference": case.reference_number,
            "case_title": case.title,
            "target_wallet": inv.wallet_address,
            "blockchain": inv.blockchain,
            "created_at": now_utc.strftime("%Y-%m-%d %H:%M:%S"),
            "author_email": author.email,
            "author_role": author.role.name if author.role else "INV",
            "status": "PENDING_APPROVAL",
            "approved_by_email": None,
            "top_candidate": top_cand_dict,
            "risk_assessment": risk_dict,
            "cross_chain_events": xchain_list,
            "evidence_facts": evidence_facts,
            "limitations": limitations,
            "traced_usd": f"{float(traced_usd):,.2f}",
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        }

        # 8. Generate Deterministic Template Narrative (FR-AI-02)
        narrative_text = generate_template_narrative({
            "case_reference": case.reference_number,
            "case_title": case.title,
            "target_wallet": inv.wallet_address,
            "blockchain": inv.blockchain,
            "created_at": now_utc.strftime("%Y-%m-%d %H:%M:%S"),
            "top_vasp_name": top_cand_dict["vasp_name"],
            "top_vasp_id": top_cand_dict["vasp_id"],
            "final_score": top_cand_dict["final_score"],
            "tier": top_cand_dict["tier"],
            "raw_score": top_cand_dict["raw_score"],
            "applied_caps": top_cand_dict["caps_applied"],
            "limitations": limitations,
            "risk_score": risk_dict["risk_score"],
            "risk_tier": risk_dict["risk_tier"],
            "triggered_signals": [
                s for s in (risk_dict["signals"] if isinstance(risk_dict["signals"], list) else [])
                if isinstance(s, dict) and s.get("triggered")
            ],
            "cross_chain_events": xchain_list,
            "traced_usd": report_data["traced_usd"],
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        })

        # 9. Generate PDF & compute SHA-256 Checksum (FR-RPT-01)
        _pdf_bytes, pdf_hash = generate_investigation_pdf(report_data)

        # 10. Persist ReportModel
        report = ReportModel(
            id=uuid4(),
            case_id=case_id,
            investigation_id=investigation_id,
            title=title,
            status="PENDING_APPROVAL",
            pdf_hash=pdf_hash,
            pdf_path=f"reports/{investigation_id}_{pdf_hash[:12]}.pdf",
            data_payload=report_data,
            limitations=limitations,
            narrative=narrative_text,
            created_by=author.id,
        )
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)

        await log_audit_event(
            session=self.db,
            action="REPORT_GENERATE",
            resource_type="report",
            outcome=AuditOutcome.ALLOW,
            user_id=author.id,
            resource_id=str(report.id),
            details={
                "pdf_hash": pdf_hash,
                "facts_count": len(evidence_facts),
                "case_id": str(case_id),
                "investigation_id": str(investigation_id),
            },
        )
        await self.db.commit()

        return report

    async def approve_report(
        self,
        report_id: UUID,
        approver: User,
        comment: str,
    ) -> ReportModel:
        """Approves report enforcing separation of duties (FR-RPT-04). Author cannot approve own report."""
        rep_stmt = select(ReportModel).where(ReportModel.id == report_id)
        rep_res = await self.db.execute(rep_stmt)
        report = rep_res.scalar_one_or_none()
        if not report:
            raise NotFoundException(f"Report {report_id} not found")

        # Separation of duties (FR-RPT-04): creator cannot approve
        if report.created_by == approver.id:
            await log_audit_event(
                session=self.db,
                action="REPORT_APPROVE",
                resource_type="report",
                outcome=AuditOutcome.DENY,
                user_id=approver.id,
                resource_id=str(report.id),
                details={"reason": "Separation of duties violation: Author cannot approve their own report"},
            )
            await self.db.commit()
            raise PermissionDeniedException(
                "Separation of duties violation: Report author cannot approve their own report (FR-RPT-04)."
            )

        # Update approval status
        now_utc = datetime.now(UTC)
        report.status = "APPROVED"
        report.approved_by = approver.id
        report.approval_comment = comment
        report.approved_at = now_utc

        # Update data payload with approval signature & regenerate PDF with new signature
        data = dict(report.data_payload)
        data["status"] = "APPROVED"
        data["approved_by_email"] = approver.email
        _pdf_bytes, new_pdf_hash = generate_investigation_pdf(data)
        report.pdf_hash = new_pdf_hash
        report.data_payload = data

        await self.db.commit()
        await self.db.refresh(report)

        await log_audit_event(
            session=self.db,
            action="REPORT_APPROVE",
            resource_type="report",
            outcome=AuditOutcome.ALLOW,
            user_id=approver.id,
            resource_id=str(report.id),
            details={"approved_by": str(approver.id), "pdf_hash": new_pdf_hash},
        )
        await self.db.commit()

        return report

"""MockSahyogProvider implementing all 7 operations, status transitions, and separation of duties (FR-SAH-01..05)."""

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit_event
from app.core.errors import NotFoundException, PermissionDeniedException
from app.db.models import (
    Case,
    ReportModel,
    SahyogRequestModel,
    SahyogStatusHistoryModel,
    User,
    Vasp,
)
from app.domain.enums import AuditOutcome
from app.sahyog.builder import SahyogRequestBuilder


class MockSahyogProvider:
    """Mock SAHYOG provider implementing the 7 statutory operations for MVP / demo mode (FR-SAH-01).
    All outputs are explicitly flagged is_mock=True.
    """

    name = "MockSahyogProvider"
    is_mock = True

    def __init__(self, db: AsyncSession):
        self.db = db

    # Operation 1: Create Disclosure Request
    async def create_disclosure_request(
        self,
        payload: dict[str, Any],
        author: User,
    ) -> SahyogRequestModel:
        """Operation 1: Create a statutory disclosure request draft with completeness validation (FR-SAH-02)."""
        is_valid, validation_errors = SahyogRequestBuilder.validate_request_data(payload)
        status = "DRAFT"

        # Lookup case ref
        case_id = payload.get("case_id")
        case_res = await self.db.execute(select(Case).where(Case.id == case_id))
        case = case_res.scalar_one_or_none()
        case_ref = case.reference_number if case else "CASE"

        ref_no = payload.get("reference_number") or SahyogRequestBuilder.build_reference_number(
            case_ref, payload.get("target_vasp_id", "VASP")
        )

        # Check existing ref
        existing_res = await self.db.execute(
            select(SahyogRequestModel).where(SahyogRequestModel.reference_number == ref_no)
        )
        if existing_res.scalar_one_or_none():
            ref_no = f"{ref_no}-{uuid4().hex[:4].upper()}"

        req = SahyogRequestModel(
            id=uuid4(),
            case_id=case_id,
            investigation_id=payload.get("investigation_id"),
            report_id=payload.get("report_id"),
            reference_number=ref_no,
            target_vasp_id=payload.get("target_vasp_id", "UNKNOWN"),
            target_vasp_name=payload.get("target_vasp_name", "Unknown VASP"),
            target_wallet_address=payload.get("target_wallet_address", ""),
            reason=payload.get("reason", ""),
            statutory_basis=payload.get("statutory_basis", "Section 91 CrPC / Section 94 BNSS"),
            officer_name=payload.get("officer_name", author.email),
            officer_designation=payload.get("officer_designation", "Superintendent of Police / Lead Investigator"),
            request_type=payload.get("request_type", "disclosure"),
            status=status,
            is_mock=True,
            attachments=[],
            validation_errors=validation_errors,
            drafted_by=author.id,
        )
        self.db.add(req)

        # Record initial status history
        hist = SahyogStatusHistoryModel(
            id=uuid4(),
            request_id=req.id,
            from_status="NONE",
            to_status="DRAFT",
            changed_by=author.id,
            comment="Initial statutory request draft created.",
            timestamp=datetime.now(UTC),
        )
        self.db.add(hist)
        await self.db.commit()
        await self.db.refresh(req)

        await log_audit_event(
            session=self.db,
            action="SAHYOG_DRAFT_CREATE",
            resource_type="sahyog_request",
            user_id=author.id,
            resource_id=str(req.id),
            outcome=AuditOutcome.ALLOW,
            details={"reference_number": req.reference_number, "is_valid": is_valid},
        )
        await self.db.commit()

        return req

    # Operation 2: Create Freeze Request
    async def create_freeze_request(
        self,
        payload: dict[str, Any],
        author: User,
    ) -> SahyogRequestModel:
        """Operation 2: Issue an emergency debit freeze directive."""
        freeze_payload = dict(payload)
        freeze_payload["request_type"] = "freeze"
        freeze_payload["statutory_basis"] = payload.get(
            "freeze_statutory_basis",
            payload.get("statutory_basis") if payload.get("statutory_basis") and "102" in payload.get("statutory_basis", "") else "Section 102 CrPC / Section 106 BNSS (Emergency Seizure Directive)",
        )
        return await self.create_disclosure_request(freeze_payload, author)

    # Operation 3: Get Request Status
    async def get_request_status(self, reference_number: str) -> dict[str, Any]:
        """Operation 3: Query current tracking status of a submitted request."""
        stmt = select(SahyogRequestModel).where(SahyogRequestModel.reference_number == reference_number)
        res = await self.db.execute(stmt)
        req = res.scalar_one_or_none()
        if not req:
            raise NotFoundException(f"SAHYOG request {reference_number} not found")

        # Fetch status history
        hist_stmt = (
            select(SahyogStatusHistoryModel)
            .where(SahyogStatusHistoryModel.request_id == req.id)
            .order_by(SahyogStatusHistoryModel.timestamp.asc())
        )
        hist_res = await self.db.execute(hist_stmt)
        history = [
            {
                "from_status": h.from_status,
                "to_status": h.to_status,
                "comment": h.comment,
                "timestamp": h.timestamp.isoformat(),
            }
            for h in hist_res.scalars().all()
        ]

        return {
            "reference_number": req.reference_number,
            "status": req.status,
            "target_vasp_id": req.target_vasp_id,
            "target_vasp_name": req.target_vasp_name,
            "submitted_at": req.submitted_at.isoformat() if req.submitted_at else None,
            "acknowledged_at": req.acknowledged_at.isoformat() if req.acknowledged_at else None,
            "is_mock": True,
            "history": history,
            "notice": "MOCK — NOT TRANSMITTED TO ANY AUTHORITY",
        }

    # Operation 4: List Requests
    async def list_requests(self, filters: dict[str, Any] | None = None) -> list[SahyogRequestModel]:
        """Operation 4: List all requests for the organization unit."""
        stmt = select(SahyogRequestModel).order_by(SahyogRequestModel.created_at.desc())
        if filters and filters.get("case_id"):
            stmt = stmt.where(SahyogRequestModel.case_id == filters["case_id"])
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    # Operation 5: Upload Attachment
    async def upload_attachment(
        self,
        reference_number: str,
        filename: str,
        content: bytes,
        sha256_hash: str,
    ) -> dict[str, Any]:
        """Operation 5: Upload supporting legal orders or approved report PDFs with SHA-256 integrity verification."""
        stmt = select(SahyogRequestModel).where(SahyogRequestModel.reference_number == reference_number)
        res = await self.db.execute(stmt)
        req = res.scalar_one_or_none()
        if not req:
            raise NotFoundException(f"SAHYOG request {reference_number} not found")

        # Verify hash matches content
        calc_hash = hashlib.sha256(content).hexdigest()
        if calc_hash.lower() != sha256_hash.lower():
            raise ValueError(f"Attachment hash mismatch: provided {sha256_hash} != calculated {calc_hash}")

        att = {
            "attachment_id": f"ATT-{uuid4().hex[:8].upper()}",
            "filename": filename,
            "sha256_hash": calc_hash,
            "bytes_size": len(content),
            "uploaded_at": datetime.now(UTC).isoformat(),
        }
        current_atts = list(req.attachments)
        current_atts.append(att)
        req.attachments = current_atts
        await self.db.commit()

        return att

    # Operation 6: Cancel Request
    async def cancel_request(
        self,
        reference_number: str,
        reason: str,
        actor: User,
    ) -> dict[str, Any]:
        """Operation 6: Cancel or withdraw a pending statutory request."""
        stmt = select(SahyogRequestModel).where(SahyogRequestModel.reference_number == reference_number)
        res = await self.db.execute(stmt)
        req = res.scalar_one_or_none()
        if not req:
            raise NotFoundException(f"SAHYOG request {reference_number} not found")

        prev_status = req.status
        req.status = "CANCELLED"

        hist = SahyogStatusHistoryModel(
            id=uuid4(),
            request_id=req.id,
            from_status=prev_status,
            to_status="CANCELLED",
            changed_by=actor.id,
            comment=f"Request withdrawn/cancelled: {reason}",
            timestamp=datetime.now(UTC),
        )
        self.db.add(hist)
        await self.db.commit()

        return {"reference_number": reference_number, "status": "CANCELLED", "reason": reason}

    # Operation 7: Get VASP Compliance Info
    async def get_vasp_compliance_info(self, vasp_id: str) -> dict[str, Any]:
        """Operation 7: Query VASP nodal officer, grievance contacts, and supported statutory formats."""
        vasp_stmt = select(Vasp).where(Vasp.vasp_id == vasp_id)
        vasp_res = await self.db.execute(vasp_stmt)
        vasp = vasp_res.scalar_one_or_none()

        name = vasp.name if vasp else vasp_id
        jurisdiction = vasp.jurisdiction if vasp else "IN"

        return {
            "vasp_id": vasp_id,
            "name": name,
            "jurisdiction": jurisdiction,
            "nodal_officer_email": f"nodal-compliance@{vasp_id.lower().replace('_', '-')}.compliance.gov.in",
            "grievance_officer": f"Chief Compliance Officer, {name}",
            "physical_address": f"VASP Legal Operations Center, {jurisdiction}",
            "supported_requests": [
                "Section 91 CrPC (Customer Account Records & IP Logs)",
                "Section 94 BNSS (Statutory Document Production)",
                "Section 102 CrPC (Emergency Debit Freeze)",
                "PMLA / FIU-IND STR Inquiries",
            ],
            "response_sla_hours": 24 if "BINANCE" in vasp_id.upper() or "KRAKEN" in vasp_id.upper() else 48,
            "is_mock": True,
            "notice": "MOCK COMPLIANCE PROFILE — NOT A REAL NODAL ENTITY",
        }

    # Submission & State Machine (FR-SAH-04, Separation of Duties)
    async def submit_request(
        self,
        request_id: UUID,
        submitter: User,
        comment: str | None = None,
    ) -> SahyogRequestModel:
        """Submits request: enforces separation of duties and approved report, transitions SUBMITTED -> ACKNOWLEDGED."""
        stmt = select(SahyogRequestModel).where(SahyogRequestModel.id == request_id)
        res = await self.db.execute(stmt)
        req = res.scalar_one_or_none()
        if not req:
            raise NotFoundException(f"SAHYOG request {request_id} not found")

        # 1. Validation check
        if req.validation_errors:
            raise ValueError(
                f"Cannot submit invalid request: {'; '.join(req.validation_errors)}"
            )

        # 2. Separation of duties: Submitter != Drafter (PRD §5 J3)
        if req.drafted_by == submitter.id:
            await log_audit_event(
                session=self.db,
                action="SAHYOG_SUBMIT",
                resource_type="sahyog_request",
                user_id=submitter.id,
                resource_id=str(req.id),
                outcome=AuditOutcome.DENY,
                details={"reason": "Separation of duties violation: Request drafter cannot submit the request"},
            )
            await self.db.commit()
            raise PermissionDeniedException(
                "Separation of duties violation: The user who drafted the SAHYOG request cannot submit it. "
                "A supervisor must review and submit."
            )

        # 3. Report Approval check: Report MUST be APPROVED
        rep_stmt = select(ReportModel).where(ReportModel.id == req.report_id)
        rep_res = await self.db.execute(rep_stmt)
        report = rep_res.scalar_one_or_none()
        if not report or report.status != "APPROVED":
            raise ValueError(
                "Cannot submit SAHYOG request without an APPROVED attribution report. "
                f"Current report status is '{report.status if report else 'MISSING'}'."
            )

        # 4. Transition SUBMITTED -> ACKNOWLEDGED
        now_utc = datetime.now(UTC)
        req.status = "ACKNOWLEDGED"
        req.submitted_by = submitter.id
        req.submitted_at = now_utc
        req.acknowledged_at = now_utc + timedelta(seconds=1)

        # Persist SUBMITTED history
        hist1 = SahyogStatusHistoryModel(
            id=uuid4(),
            request_id=req.id,
            from_status="DRAFT",
            to_status="SUBMITTED",
            changed_by=submitter.id,
            comment=comment or "Submitted by supervisory authority.",
            timestamp=now_utc,
        )
        self.db.add(hist1)

        # Persist ACKNOWLEDGED history
        hist2 = SahyogStatusHistoryModel(
            id=uuid4(),
            request_id=req.id,
            from_status="SUBMITTED",
            to_status="ACKNOWLEDGED",
            changed_by=None,
            comment="Automated mock acknowledgment: Nodal Officer ticket issued.",
            timestamp=now_utc + timedelta(seconds=1),
        )
        self.db.add(hist2)

        await self.db.commit()
        await self.db.refresh(req)

        await log_audit_event(
            session=self.db,
            action="SAHYOG_SUBMIT",
            resource_type="sahyog_request",
            user_id=submitter.id,
            resource_id=str(req.id),
            outcome=AuditOutcome.ALLOW,
            details={"reference_number": req.reference_number, "status": req.status},
        )
        await self.db.commit()

        return req

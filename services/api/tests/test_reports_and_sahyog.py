import hashlib
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import PermissionDeniedException
from app.core.security import create_access_token
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
    SahyogRequestModel,
    User,
    Vasp,
)
from app.domain.enums import UserRole
from app.reports.engine import ReportEngine
from app.reports.narrative import (
    LLMValidationError,
    generate_template_narrative,
    validate_llm_grounding,
)
from app.reports.pdf import generate_investigation_pdf
from app.sahyog.builder import SahyogRequestBuilder
from app.sahyog.mock import MockSahyogProvider


def get_auth_headers(user: User) -> dict:
    role_enum = UserRole(user.role.name)
    token = create_access_token(
        subject=str(user.id),
        email=user.email,
        role=role_enum,
        org_id=str(user.org_id),
    )
    return {"Authorization": f"Bearer {token}"}


# -----------------------------------------------------------------------------
# 1. PDF Generator & Checksum Tests (FR-RPT-01, FR-RPT-03)
# -----------------------------------------------------------------------------


def test_pdf_generation_and_sha256_checksum():
    """FR-RPT-01: Verifies PDF generation produces valid PDF bytes and valid SHA-256 hash."""
    sample_data = {
        "case_reference": "CASE-TEST-001",
        "case_title": "Operation Sovereign Shield",
        "target_wallet": "0x1111111111111111111111111111111111111111",
        "blockchain": "ethereum",
        "created_at": "2026-10-03 02:00:00",
        "author_email": "inv@dhanrashi.local",
        "author_role": "INV",
        "status": "APPROVED",
        "approved_by_email": "sup@dhanrashi.local",
        "top_candidate": {
            "vasp_id": "VASP-BINANCE",
            "vasp_name": "Binance International",
            "tier": "HIGH",
            "raw_score": 0.8845,
            "final_score": 0.8845,
            "factors": [
                {
                    "name": "percentage_of_traced_funds",
                    "raw_value": "88.0%",
                    "normalized_score": 0.88,
                    "weight": 0.25,
                    "contribution": 0.22,
                    "applicable": True,
                },
                {
                    "name": "known_deposit_match",
                    "raw_value": "deposit_wallet",
                    "normalized_score": 1.0,
                    "weight": 0.20,
                    "contribution": 0.20,
                    "applicable": True,
                },
            ],
        },
        "risk_assessment": {
            "risk_score": 24,
            "risk_tier": "LOW",
            "signals": [{"name": "rapid_movement", "score": 18, "triggered": True}],
        },
        "evidence_facts": [
            {
                "sequence_num": 1,
                "provenance_class": "OBSERVED",
                "evidence_type": "onchain_transfer",
                "source": "ethereum-fixture",
                "description": "Observed deposit transfer into Binance wallet",
                "evidence_hash": "a" * 64,
            },
            {
                "sequence_num": 2,
                "provenance_class": "THIRD-PARTY INTELLIGENCE",
                "evidence_type": "vasp_attribution",
                "source": "internal_curation",
                "description": "Binance verified customer deposit wallet",
                "evidence_hash": "b" * 64,
            },
        ],
        "limitations": ["Attribution lead is indicative, not legal proof."],
    }

    pdf_bytes, sha256_hash = generate_investigation_pdf(sample_data)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")  # Valid PDF magic bytes

    # Verify SHA-256 checksum
    calc_hash = hashlib.sha256(pdf_bytes).hexdigest()
    assert sha256_hash == calc_hash


# -----------------------------------------------------------------------------
# 2. Epistemic Fact Labeling Invariant Test (FR-RPT-02)
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fr_rpt_02_automated_check_rejects_unlabeled_facts(db_session: AsyncSession, seeded_entities):
    """FR-RPT-02: Automated check must ensure no unlabeled fact rows exist in evidence ledger."""
    inv_user = seeded_entities["users"]["INV"]
    case = Case(reference_number="CASE-FACT-01", title="Epistemic Fact Test", org_id=inv_user.org_id, owner_id=inv_user.id)
    db_session.add(case)
    await db_session.flush()

    inv = Investigation(case_id=case.id, wallet_address="0x1111111111111111111111111111111111111111", blockchain="ethereum")
    db_session.add(inv)
    await db_session.flush()

    # Seed an evidence row with INVALID / UNLABELED provenance class
    invalid_ev = EvidenceModel(
        id=uuid4(),
        investigation_id=inv.id,
        sequence_num=1,
        evidence_type="test_event",
        provenance_class="INVALID_PROVENANCE_LABEL",  # Illegal provenance class!
        source="unit_test",
        source_ref="test_ref",
        raw_hash="0" * 64,
        evidence_hash="1" * 64,
        prev_evidence_hash="0" * 64,
        data_payload={"note": "unlabeled fact"},
        created_by_id=inv_user.id,
    )
    db_session.add(invalid_ev)
    await db_session.commit()

    engine = ReportEngine(db_session)
    with pytest.raises(ValueError, match="FR-RPT-02 violation"):
        await engine.generate_report(case.id, inv.id, "Test Report", inv_user)


# -----------------------------------------------------------------------------
# 3. Report Approval & Separation of Duties (FR-RPT-04)
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_report_approval_workflow_and_separation_of_duties(db_session: AsyncSession, seeded_entities):
    """FR-RPT-04: Separation of duties requires that the author cannot approve their own report."""
    inv_user = seeded_entities["users"]["INV"]
    sup_user = seeded_entities["users"]["SUP"]

    case = Case(reference_number="CASE-APP-01", title="Approval Test", org_id=inv_user.org_id, owner_id=inv_user.id)
    db_session.add(case)
    await db_session.flush()

    inv = Investigation(case_id=case.id, wallet_address="0x1111111111111111111111111111111111111111", blockchain="ethereum")
    db_session.add(inv)
    await db_session.flush()

    # Add valid evidence row
    valid_ev = EvidenceModel(
        id=uuid4(),
        investigation_id=inv.id,
        sequence_num=1,
        evidence_type="onchain_transfer",
        provenance_class="OBSERVED",
        source="unit_test",
        source_ref="test_ref",
        raw_hash="0" * 64,
        evidence_hash="1" * 64,
        prev_evidence_hash="0" * 64,
        data_payload={"note": "observed transfer"},
        created_by_id=inv_user.id,
    )
    db_session.add(valid_ev)
    await db_session.commit()

    engine = ReportEngine(db_session)
    # Generate report as INV
    report = await engine.generate_report(case.id, inv.id, "Approval Workflow Report", inv_user)
    assert report.status == "PENDING_APPROVAL"
    assert report.pdf_hash is not None

    # Test separation of duties: Author INV cannot approve own report
    with pytest.raises(PermissionDeniedException, match="Separation of duties violation"):
        await engine.approve_report(report.id, inv_user, "Self-approval attempt")

    # Supervisor SUP approves report
    approved_report = await engine.approve_report(report.id, sup_user, "Formal supervisor clearance granted.")
    assert approved_report.status == "APPROVED"
    assert approved_report.approved_by == sup_user.id
    assert approved_report.approval_comment == "Formal supervisor clearance granted."
    assert approved_report.approved_at is not None


# -----------------------------------------------------------------------------
# 4. Deterministic Narrative & LLM Grounding Validator (FR-AI-01, FR-AI-02, LLM-03)
# -----------------------------------------------------------------------------


def test_deterministic_template_narrative_and_llm_grounding_validator():
    """FR-AI-02 and test LLM-03: Deterministic narrative generates with LLM off.
    LLM output validator rejects hallucinated addresses, hashes, or VASPs.
    """
    context = {
        "case_reference": "CASE-DEMO-02",
        "case_title": "Ranking Demonstration",
        "target_wallet": "0x1111111111111111111111111111111111111111",
        "blockchain": "ethereum",
        "created_at": "2026-10-03 02:00:00",
        "top_vasp_name": "Kraken",
        "top_vasp_id": "VASP-KRAKEN",
        "final_score": 0.88,
        "tier": "HIGH",
        "raw_score": 0.88,
        "applied_caps": [],
        "limitations": ["Lead is indicative."],
        "risk_score": 18,
        "risk_tier": "LOW",
        "triggered_signals": [],
        "cross_chain_events": [],
        "traced_usd": "5,000.00",
        "total_nodes": 4,
        "total_edges": 3,
    }

    # FR-AI-02: Generates clean text with LLM disabled
    narrative = generate_template_narrative(context)
    assert "EXECUTIVE INVESTIGATION NARRATIVE" in narrative
    assert "Kraken" in narrative
    assert "VASP-KRAKEN" in narrative
    assert "5,000.00" in narrative

    # Test LLM-03: Valid narrative passes grounding check
    grounding_ctx = {
        "valid_addresses": ["0x1111111111111111111111111111111111111111", "0x2222222222222222222222222222222222222222"],
        "valid_hashes": ["0x" + "a" * 64],
        "valid_vasps": ["VASP-KRAKEN", "VASP-BINANCE"],
    }

    clean_llm_text = (
        "Investigation traced funds from 0x1111111111111111111111111111111111111111 "
        "to 0x2222222222222222222222222222222222222222 at VASP-KRAKEN via 0x" + "a" * 64
    )
    validate_llm_grounding(clean_llm_text, grounding_ctx)

    # Hallucinated address test: raises LLMValidationError
    hallucinated_addr_text = (
        "Funds were routed through darknet address 0x9999999999999999999999999999999999999999 to VASP-KRAKEN."
    )
    with pytest.raises(LLMValidationError, match="Grounding violation"):
        validate_llm_grounding(hallucinated_addr_text, grounding_ctx)

    # Hallucinated VASP test: raises LLMValidationError
    hallucinated_vasp_text = "Target deposited funds into illicit exchange VASP-UNREGULATED-MIXER."
    with pytest.raises(LLMValidationError, match="Grounding violation"):
        validate_llm_grounding(hallucinated_vasp_text, grounding_ctx)


# -----------------------------------------------------------------------------
# 5. All 7 SAHYOG Operations on MockSahyogProvider (FR-SAH-01..05)
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sahyog_all_7_operations_and_submission(db_session: AsyncSession, seeded_entities):
    """FR-SAH-01..05: Tests all 7 operations, completeness validation, and submission transitions."""
    inv_user = seeded_entities["users"]["INV"]
    sup_user = seeded_entities["users"]["SUP"]

    case = Case(reference_number="CASE-SAH-01", title="SAHYOG Unit Test", org_id=inv_user.org_id, owner_id=inv_user.id)
    db_session.add(case)
    await db_session.flush()

    inv = Investigation(case_id=case.id, wallet_address="0x1111111111111111111111111111111111111111", blockchain="ethereum")
    db_session.add(inv)
    await db_session.flush()

    # Seed an APPROVED report
    approved_report = ReportModel(
        id=uuid4(),
        case_id=case.id,
        investigation_id=inv.id,
        title="Approved Report for SAHYOG",
        status="APPROVED",
        pdf_hash="f" * 64,
        data_payload={},
        limitations=[],
        created_by=inv_user.id,
        approved_by=sup_user.id,
        approved_at=datetime.now(UTC),
    )
    db_session.add(approved_report)

    # Also seed a DRAFT report for testing rejection
    draft_report = ReportModel(
        id=uuid4(),
        case_id=case.id,
        investigation_id=inv.id,
        title="Unapproved Draft Report",
        status="DRAFT",
        data_payload={},
        limitations=[],
        created_by=inv_user.id,
    )
    db_session.add(draft_report)
    await db_session.commit()

    provider = MockSahyogProvider(db_session)

    # Op 1: create_disclosure_request (with completeness check)
    # Test missing mandatory field: keeps DRAFT with validation errors
    incomplete_payload = {
        "case_id": case.id,
        "investigation_id": inv.id,
        "report_id": approved_report.id,
        # missing target_vasp_id, reason, statutory_basis, etc.
    }
    draft_incomplete = await provider.create_disclosure_request(incomplete_payload, inv_user)
    assert draft_incomplete.status == "DRAFT"
    assert len(draft_incomplete.validation_errors) > 0

    # Complete payload
    complete_payload = {
        "case_id": case.id,
        "investigation_id": inv.id,
        "report_id": approved_report.id,
        "target_vasp_id": "VASP-BINANCE",
        "target_vasp_name": "Binance",
        "target_wallet_address": "0x1111111111111111111111111111111111111111",
        "reason": "Investigation into cyber fraud fund laundering",
        "statutory_basis": "Section 91 CrPC / Section 94 BNSS",
        "officer_name": "Inspector Vikram",
        "officer_designation": "Lead Investigator",
    }
    req = await provider.create_disclosure_request(complete_payload, inv_user)
    assert req.status == "DRAFT"
    assert len(req.validation_errors) == 0
    assert req.is_mock is True

    # Op 2: create_freeze_request
    freeze_req = await provider.create_freeze_request(complete_payload, inv_user)
    assert freeze_req.request_type == "freeze"
    assert "Section 102" in freeze_req.statutory_basis

    # Op 3: get_request_status
    status_info = await provider.get_request_status(req.reference_number)
    assert status_info["status"] == "DRAFT"
    assert status_info["is_mock"] is True
    assert "MOCK" in status_info["notice"]

    # Op 4: list_requests
    all_reqs = await provider.list_requests({"case_id": case.id})
    assert len(all_reqs) >= 2

    # Op 5: upload_attachment (with hash verification)
    attachment_content = b"%PDF-mock-court-order-attachment-content"
    att_hash = hashlib.sha256(attachment_content).hexdigest()
    att_receipt = await provider.upload_attachment(req.reference_number, "court_order.pdf", attachment_content, att_hash)
    assert att_receipt["sha256_hash"] == att_hash

    # Op 7: get_vasp_compliance_info
    compliance_info = await provider.get_vasp_compliance_info("VASP-BINANCE")
    assert compliance_info["vasp_id"] == "VASP-BINANCE"
    assert "nodal-compliance" in compliance_info["nodal_officer_email"]
    assert compliance_info["is_mock"] is True

    # Op 6: cancel_request
    cancel_info = await provider.cancel_request(freeze_req.reference_number, "Withdrawn by IO", inv_user)
    assert cancel_info["status"] == "CANCELLED"

    # Submission & State Machine:
    # Test separation of duties: Drafter INV cannot submit
    with pytest.raises(PermissionDeniedException, match="Separation of duties"):
        await provider.submit_request(req.id, inv_user)

    # Test report approval requirement: Attempting to submit with unapproved report fails
    unapproved_payload = dict(complete_payload)
    unapproved_payload["report_id"] = draft_report.id
    req_unapproved = await provider.create_disclosure_request(unapproved_payload, inv_user)
    with pytest.raises(ValueError, match="without an APPROVED attribution report"):
        await provider.submit_request(req_unapproved.id, sup_user)

    # Valid submission by Supervisor SUP
    submitted_req = await provider.submit_request(req.id, sup_user, "Supervisor authorized submission.")
    assert submitted_req.status == "ACKNOWLEDGED"
    assert submitted_req.submitted_by == sup_user.id
    assert submitted_req.submitted_at is not None
    assert submitted_req.acknowledged_at is not None


# -----------------------------------------------------------------------------
# 6. REST API Endpoints Integration Test
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reports_and_sahyog_rest_api_endpoints(client: AsyncClient, db_session: AsyncSession, seeded_entities):
    """End-to-end REST API roundtrip for reports and SAHYOG."""
    inv_user = seeded_entities["users"]["INV"]
    sup_user = seeded_entities["users"]["SUP"]
    inv_headers = get_auth_headers(inv_user)
    sup_headers = get_auth_headers(sup_user)

    case = Case(reference_number="CASE-API-01", title="API Endpoints Test", org_id=inv_user.org_id, owner_id=inv_user.id)
    db_session.add(case)
    await db_session.flush()

    inv = Investigation(case_id=case.id, wallet_address="0x1111111111111111111111111111111111111111", blockchain="ethereum")
    db_session.add(inv)
    await db_session.flush()

    # Seed evidence and attribution
    ev = EvidenceModel(
        id=uuid4(),
        investigation_id=inv.id,
        sequence_num=1,
        evidence_type="onchain_transfer",
        provenance_class="OBSERVED",
        source="api_test",
        source_ref="tx_123",
        raw_hash="0" * 64,
        evidence_hash="1" * 64,
        prev_evidence_hash="0" * 64,
        data_payload={"note": "api test transfer"},
        created_by_id=inv_user.id,
    )
    attr = AttributionResultModel(
        id=uuid4(),
        investigation_id=inv.id,
        version=1,
        candidate_vasp_id="VASP-KRAKEN",
        candidate_vasp_name="Kraken",
        rank=1,
        score=0.85,
        tier="HIGH",
        factors_json={},
        caps_json=[],
        limitations_json=["Mandatory lead disclaimer."],
        supporting_addresses=["0x2222222222222222222222222222222222222222"],
        evidence_references=[str(ev.id)],
    )
    db_session.add_all([ev, attr])
    await db_session.commit()

    # 1. POST /api/v1/reports/generate
    res_gen = await client.post(
        "/api/v1/reports/generate",
        json={"case_id": str(case.id), "investigation_id": str(inv.id), "title": "API Generated Report"},
        headers=inv_headers,
    )
    assert res_gen.status_code == 201
    rep_data = res_gen.json()
    rep_id = rep_data["id"]
    assert rep_data["status"] == "PENDING_APPROVAL"
    assert rep_data["pdf_hash"] is not None

    # 2. GET /api/v1/reports/{id}/pdf
    res_pdf = await client.get(f"/api/v1/reports/{rep_id}/pdf", headers=inv_headers)
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert "X-Report-SHA256" in res_pdf.headers

    # 3. POST /api/v1/reports/{id}/approve (SUP user)
    res_app = await client.post(
        f"/api/v1/reports/{rep_id}/approve",
        json={"comment": "Supervisory approval for SAHYOG"},
        headers=sup_headers,
    )
    assert res_app.status_code == 200
    assert res_app.json()["status"] == "APPROVED"

    # 4. POST /api/v1/sahyog/draft
    sahyog_payload = {
        "case_id": str(case.id),
        "investigation_id": str(inv.id),
        "report_id": rep_id,
        "target_vasp_id": "VASP-KRAKEN",
        "target_vasp_name": "Kraken",
        "target_wallet_address": "0x2222222222222222222222222222222222222222",
        "reason": "Tracing illicit funds into Kraken deposit wallet",
        "statutory_basis": "Section 91 CrPC",
        "officer_name": "Inspector Vikram",
        "officer_designation": "Investigating Officer",
    }
    res_sah_draft = await client.post("/api/v1/sahyog/draft", json=sahyog_payload, headers=inv_headers)
    assert res_sah_draft.status_code == 201
    sah_data = res_sah_draft.json()
    sah_id = sah_data["id"]
    sah_ref = sah_data["reference_number"]
    assert sah_data["status"] == "DRAFT"

    # 5. GET /api/v1/sahyog/requests/{ref}/status
    res_status = await client.get(f"/api/v1/sahyog/requests/{sah_ref}/status", headers=inv_headers)
    assert res_status.status_code == 200
    assert res_status.json()["is_mock"] is True

    # 6. POST /api/v1/sahyog/requests/{id}/submit (SUP user)
    res_sah_sub = await client.post(
        f"/api/v1/sahyog/requests/{sah_id}/submit",
        json={"comment": "Authorized statutory submission"},
        headers=sup_headers,
    )
    assert res_sah_sub.status_code == 200
    assert res_sah_sub.json()["status"] == "ACKNOWLEDGED"

    # 7. GET /api/v1/sahyog/vasps/{vasp_id}/compliance
    res_comp = await client.get("/api/v1/sahyog/vasps/VASP-KRAKEN/compliance", headers=inv_headers)
    assert res_comp.status_code == 200
    assert res_comp.json()["vasp_id"] == "VASP-KRAKEN"

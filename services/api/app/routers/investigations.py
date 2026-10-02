from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit_event
from app.core.errors import NotFoundException
from app.core.rbac import check_case_authorization, require_permission
from app.core.validation import validate_wallet_address
from app.crosschain.engine import CrossChainEngine
from app.crosschain.registry import BridgeRegistry
from app.db.models import Case, Investigation, RiskAssessmentModel, User
from app.db.session import get_db
from app.domain.enums import AuditOutcome, InvestigationState
from app.domain.models import (
    AnalystNoteCreate,
    AttributionDispositionRequest,
    AttributionResponse,
    BridgeDefinition,
    CrossChainDetectionResponse,
    CrossChainEventRead,
    EvidenceChainVerificationResult,
    EvidenceRead,
    ExplainAttributionResponse,
    GraphResponse,
    InvestigationCreate,
    InvestigationRead,
    InvestigationStatusResponse,
    RiskAssessmentRead,
    RiskAssessmentRunResponse,
    RiskSignal,
)
from app.evidence.engine import EvidenceEngine
from app.risk.engine import RiskEngine

router = APIRouter(prefix="/investigations", tags=["Investigations"])


@router.post("/cases/{case_id}", response_model=InvestigationRead, status_code=status.HTTP_201_CREATED)
async def create_investigation(
    case_id: UUID,
    payload: InvestigationCreate,
    current_user: User = Depends(require_permission("investigation.run")),
    session: AsyncSession = Depends(get_db),
):
    """Creates a new wallet investigation within a case (FR-INV-01).
    Validates wallet address format and blockchain support immediately.
    """
    stmt = select(Case).where(Case.id == case_id, Case.org_id == current_user.org_id)
    result = await session.execute(stmt)
    case = result.scalar_one_or_none()

    if not case or not await check_case_authorization(case, current_user, session):
        raise NotFoundException("Case not found")

    # Validate wallet address format and blockchain enablement
    normalized_address = validate_wallet_address(
        address=payload.wallet_address,
        chain=payload.blockchain.value,
    )

    investigation = Investigation(
        case_id=case_id,
        wallet_address=normalized_address,
        blockchain=payload.blockchain.value,
        status=InvestigationState.CREATED.value,
        depth=payload.depth,
        min_usd_value=payload.min_usd_value,
        run_no=0,
        warnings=[],
        partial_reasons=[],
    )
    session.add(investigation)

    await log_audit_event(
        session=session,
        user_id=current_user.id,
        action="INVESTIGATION_CREATED",
        resource_type="investigation",
        resource_id=str(investigation.id),
        outcome=AuditOutcome.ALLOW,
        details={
            "wallet_address": normalized_address,
            "blockchain": payload.blockchain.value,
            "depth": payload.depth,
        },
    )
    await session.commit()
    await session.refresh(investigation)
    return investigation


@router.get("/cases/{case_id}", response_model=list[InvestigationRead])
async def list_investigations_for_case(
    case_id: UUID,
    current_user: User = Depends(require_permission("case.read")),
    session: AsyncSession = Depends(get_db),
):
    """Lists investigations for a given case."""
    stmt = select(Case).where(Case.id == case_id, Case.org_id == current_user.org_id)
    result = await session.execute(stmt)
    case = result.scalar_one_or_none()

    if not case or not await check_case_authorization(case, current_user, session):
        raise NotFoundException("Case not found")

    inv_stmt = select(Investigation).where(Investigation.case_id == case_id).order_by(Investigation.created_at.desc())
    inv_res = await session.execute(inv_stmt)
    return inv_res.scalars().all()


@router.get("/{investigation_id}", response_model=InvestigationRead)
async def get_investigation(
    investigation_id: UUID,
    current_user: User = Depends(require_permission("case.read")),
    session: AsyncSession = Depends(get_db),
):
    """Retrieves an investigation by ID."""
    stmt = select(Investigation).where(Investigation.id == investigation_id)
    result = await session.execute(stmt)
    investigation = result.scalar_one_or_none()

    if not investigation:
        raise NotFoundException("Investigation not found")

    case_stmt = select(Case).where(Case.id == investigation.case_id, Case.org_id == current_user.org_id)
    case_res = await session.execute(case_stmt)
    case = case_res.scalar_one_or_none()

    if not case or not await check_case_authorization(case, current_user, session):
        raise NotFoundException("Investigation not found")

    return investigation


@router.post("/{investigation_id}/run")
async def run_investigation(
    investigation_id: UUID,
    current_user: User = Depends(require_permission("investigation.run")),
    session: AsyncSession = Depends(get_db),
):
    """Executes multi-hop blockchain tracing, expansion, and flow propagation (FR-INV-01)."""
    from app.services.orchestrator import InvestigationOrchestrator

    inv_stmt = select(Investigation).where(Investigation.id == investigation_id)
    inv_res = await session.execute(inv_stmt)
    investigation = inv_res.scalar_one_or_none()
    if not investigation:
        raise NotFoundException("Investigation not found")

    case_stmt = select(Case).where(Case.id == investigation.case_id, Case.org_id == current_user.org_id)
    case_res = await session.execute(case_stmt)
    case = case_res.scalar_one_or_none()
    if not case or not await check_case_authorization(case, current_user, session):
        raise NotFoundException("Investigation not found")

    orchestrator = InvestigationOrchestrator(session)
    result = await orchestrator.run(investigation_id, user_id=current_user.id)
    return result


@router.get("/{investigation_id}/status", response_model=InvestigationStatusResponse)
async def get_investigation_status(
    investigation_id: UUID,
    current_user: User = Depends(require_permission("case.read")),
    session: AsyncSession = Depends(get_db),
) -> InvestigationStatusResponse:
    """Returns real-time progress and summary statistics for an investigation (FR-INV-04)."""
    from app.graph.postgres_engine import PostgresGraphEngine

    inv_stmt = select(Investigation).where(Investigation.id == investigation_id)
    inv_res = await session.execute(inv_stmt)
    investigation = inv_res.scalar_one_or_none()
    if not investigation:
        raise NotFoundException("Investigation not found")

    case_stmt = select(Case).where(Case.id == investigation.case_id, Case.org_id == current_user.org_id)
    case_res = await session.execute(case_stmt)
    case = case_res.scalar_one_or_none()
    if not case or not await check_case_authorization(case, current_user, session):
        raise NotFoundException("Investigation not found")

    graph_engine = PostgresGraphEngine(session)
    stats = await graph_engine.get_stats(investigation_id)

    return InvestigationStatusResponse(
        investigation_id=investigation.id,
        status=investigation.status,
        run_no=investigation.run_no,
        data_snapshot_id=investigation.data_snapshot_id,
        registry_snapshot_id=investigation.registry_snapshot_id,
        warnings=investigation.warnings,
        partial_reasons=investigation.partial_reasons,
        stats=stats,
    )


@router.get("/{investigation_id}/graph", response_model=GraphResponse)
async def get_investigation_graph(
    investigation_id: UUID,
    min_usd: Decimal | None = Query(None, description="Filter edges by minimum USD amount"),
    max_hop: int | None = Query(None, description="Filter nodes and edges by maximum hop depth"),
    current_user: User = Depends(require_permission("graph.view")),
    session: AsyncSession = Depends(get_db),
) -> GraphResponse:
    """Retrieves persisted graph nodes and edges for visualization (FR-GRAPH-07)."""
    from app.graph.postgres_engine import PostgresGraphEngine

    inv_stmt = select(Investigation).where(Investigation.id == investigation_id)
    inv_res = await session.execute(inv_stmt)
    investigation = inv_res.scalar_one_or_none()
    if not investigation:
        raise NotFoundException("Investigation not found")

    case_stmt = select(Case).where(Case.id == investigation.case_id, Case.org_id == current_user.org_id)
    case_res = await session.execute(case_stmt)
    case = case_res.scalar_one_or_none()
    if not case or not await check_case_authorization(case, current_user, session):
        raise NotFoundException("Investigation not found")

    graph_engine = PostgresGraphEngine(session)
    subgraph = await graph_engine.get_subgraph(investigation_id, min_usd=min_usd, max_hop=max_hop)

    return GraphResponse(
        investigation_id=investigation.id,
        nodes=subgraph["nodes"],
        edges=subgraph["edges"],
    )


@router.post("/{investigation_id}/cancel")
async def cancel_investigation(
    investigation_id: UUID,
    current_user: User = Depends(require_permission("investigation.cancel")),
    session: AsyncSession = Depends(get_db),
):
    """Cancels an in-flight investigation (FR-INV-03)."""
    from app.services.orchestrator import transition_state

    inv_stmt = select(Investigation).where(Investigation.id == investigation_id)
    inv_res = await session.execute(inv_stmt)
    investigation = inv_res.scalar_one_or_none()
    if not investigation:
        raise NotFoundException("Investigation not found")

    case_stmt = select(Case).where(Case.id == investigation.case_id, Case.org_id == current_user.org_id)
    case_res = await session.execute(case_stmt)
    case = case_res.scalar_one_or_none()
    if not case or not await check_case_authorization(case, current_user, session):
        raise NotFoundException("Investigation not found")

    await transition_state(session, investigation, InvestigationState.FAILED, user_id=current_user.id, reason="cancelled_by_user")
    await session.commit()
    return {"message": "Investigation cancelled successfully", "status": investigation.status}


@router.post("/{investigation_id}/attribution/run", response_model=AttributionResponse)
async def run_attribution(
    investigation_id: UUID,
    current_user: User = Depends(require_permission("investigation.run")),
    session: AsyncSession = Depends(get_db),
) -> AttributionResponse:
    """Executes explainable attribution ranking on an investigation (FR-ATT-01..08)."""
    from app.attribution.engine import AttributionEngine

    inv_stmt = select(Investigation).where(Investigation.id == investigation_id)
    inv_res = await session.execute(inv_stmt)
    investigation = inv_res.scalar_one_or_none()
    if not investigation:
        raise NotFoundException("Investigation not found")

    case_stmt = select(Case).where(Case.id == investigation.case_id, Case.org_id == current_user.org_id)
    case_res = await session.execute(case_stmt)
    case = case_res.scalar_one_or_none()
    if not case or not await check_case_authorization(case, current_user, session):
        raise NotFoundException("Investigation not found")

    attr_engine = AttributionEngine(session)
    result = await attr_engine.run(investigation_id)
    return result


@router.get("/{investigation_id}/attribution", response_model=AttributionResponse)
async def get_attribution(
    investigation_id: UUID,
    version: int | None = Query(None, description="Specific attribution version to retrieve"),
    current_user: User = Depends(require_permission("attribution.view")),
    session: AsyncSession = Depends(get_db),
) -> AttributionResponse:
    """Retrieves ranked attribution candidates and explainability summary (FR-ATT-07, FR-ATT-08)."""
    from datetime import UTC, datetime

    from sqlalchemy import func

    from app.db.models import AttributionResultModel
    from app.domain.models import AppliedCap, AttributionFactor, CandidateAttribution

    inv_stmt = select(Investigation).where(Investigation.id == investigation_id)
    inv_res = await session.execute(inv_stmt)
    investigation = inv_res.scalar_one_or_none()
    if not investigation:
        raise NotFoundException("Investigation not found")

    case_stmt = select(Case).where(Case.id == investigation.case_id, Case.org_id == current_user.org_id)
    case_res = await session.execute(case_stmt)
    case = case_res.scalar_one_or_none()
    if not case or not await check_case_authorization(case, current_user, session):
        raise NotFoundException("Investigation not found")

    # Determine target version
    if version is None:
        v_stmt = select(func.max(AttributionResultModel.version)).where(
            AttributionResultModel.investigation_id == investigation_id
        )
        target_version = await session.scalar(v_stmt) or 1
    else:
        target_version = version

    # Fetch rows
    stmt = (
        select(AttributionResultModel)
        .where(
            AttributionResultModel.investigation_id == investigation_id,
            AttributionResultModel.version == target_version,
        )
        .order_by(AttributionResultModel.rank.asc())
    )
    rows = (await session.execute(stmt)).scalars().all()

    if not rows:
        return AttributionResponse(
            investigation_id=investigation_id,
            version=target_version,
            top_candidate=None,
            competing_candidates=False,
            margin=None,
            candidates=[],
            evidence_gate_passed=False,
            weights_version="v1.0.0",
            registry_snapshot_id=investigation.registry_snapshot_id,
            calculated_at=datetime.now(UTC),
        )

    candidates: list[CandidateAttribution] = []
    for r in rows:
        factors = [
            AttributionFactor(
                name=f_name,
                raw_value=f_data.get("raw_value"),
                normalized_score=f_data.get("normalized_score", 0.0),
                weight=f_data.get("weight", 0.0),
                contribution=f_data.get("contribution", 0.0),
                applicable=f_data.get("applicable", True),
                description=f_data.get("description"),
            )
            for f_name, f_data in r.factors_json.items()
        ]
        caps = [
            AppliedCap(
                cap_code=c.get("cap_code", ""),
                max_score=c.get("max_score", 1.0),
                reason=c.get("reason", ""),
            )
            for c in r.caps_json
        ]
        candidates.append(
            CandidateAttribution(
                vasp_id=r.candidate_vasp_id,
                vasp_name=r.candidate_vasp_name,
                rank=r.rank,
                raw_score=r.score,  # preserved
                final_score=r.score,
                tier=r.tier,
                competing=r.competing_candidates,
                evidence_gate_passed=r.evidence_gate_passed,
                factors=factors,
                caps_applied=caps,
                limitations=r.limitations_json or [],
                supporting_addresses=r.supporting_addresses or [],
                evidence_references=r.evidence_references or [],
                disposition=r.disposition,
                disposition_notes=r.disposition_notes,
            )
        )

    margin = None
    if len(candidates) >= 2:
        margin = round(candidates[0].final_score - candidates[1].final_score, 4)

    return AttributionResponse(
        investigation_id=investigation_id,
        version=target_version,
        top_candidate=candidates[0] if candidates else None,
        competing_candidates=rows[0].competing_candidates if rows else False,
        margin=margin,
        candidates=candidates,
        evidence_gate_passed=True,
        weights_version=rows[0].weights_version if rows else "v1.0.0",
        registry_snapshot_id=rows[0].registry_snapshot_id if rows else None,
        calculated_at=rows[0].created_at if rows else datetime.now(UTC),
    )


@router.get(
    "/{investigation_id}/attribution/{candidate_vasp_id}/explain",
    response_model=ExplainAttributionResponse,
)
async def explain_attribution(
    investigation_id: UUID,
    candidate_vasp_id: str,
    version: int | None = Query(None, description="Specific attribution version"),
    current_user: User = Depends(require_permission("attribution.view")),
    session: AsyncSession = Depends(get_db),
) -> ExplainAttributionResponse:
    """Returns granular feature breakdown, caps, and limitations for a candidate (FR-ATT-07)."""
    from sqlalchemy import func

    from app.db.models import AttributionResultModel
    from app.domain.models import AppliedCap, AttributionFactor, CandidateAttribution

    inv_stmt = select(Investigation).where(Investigation.id == investigation_id)
    inv_res = await session.execute(inv_stmt)
    investigation = inv_res.scalar_one_or_none()
    if not investigation:
        raise NotFoundException("Investigation not found")

    case_stmt = select(Case).where(Case.id == investigation.case_id, Case.org_id == current_user.org_id)
    case_res = await session.execute(case_stmt)
    case = case_res.scalar_one_or_none()
    if not case or not await check_case_authorization(case, current_user, session):
        raise NotFoundException("Investigation not found")

    if version is None:
        v_stmt = select(func.max(AttributionResultModel.version)).where(
            AttributionResultModel.investigation_id == investigation_id
        )
        target_version = await session.scalar(v_stmt) or 1
    else:
        target_version = version

    stmt = select(AttributionResultModel).where(
        AttributionResultModel.investigation_id == investigation_id,
        AttributionResultModel.candidate_vasp_id == candidate_vasp_id,
        AttributionResultModel.version == target_version,
    )
    r = (await session.execute(stmt)).scalar_one_or_none()
    if not r:
        raise NotFoundException(f"Attribution result for VASP '{candidate_vasp_id}' not found.")

    factors = [
        AttributionFactor(
            name=f_name,
            raw_value=f_data.get("raw_value"),
            normalized_score=f_data.get("normalized_score", 0.0),
            weight=f_data.get("weight", 0.0),
            contribution=f_data.get("contribution", 0.0),
            applicable=f_data.get("applicable", True),
            description=f_data.get("description"),
        )
        for f_name, f_data in r.factors_json.items()
    ]
    caps = [
        AppliedCap(
            cap_code=c.get("cap_code", ""),
            max_score=c.get("max_score", 1.0),
            reason=c.get("reason", ""),
        )
        for c in r.caps_json
    ]

    candidate = CandidateAttribution(
        vasp_id=r.candidate_vasp_id,
        vasp_name=r.candidate_vasp_name,
        rank=r.rank,
        raw_score=r.score,
        final_score=r.score,
        tier=r.tier,
        competing=r.competing_candidates,
        evidence_gate_passed=r.evidence_gate_passed,
        factors=factors,
        caps_applied=caps,
        limitations=r.limitations_json or [],
        supporting_addresses=r.supporting_addresses or [],
        evidence_references=r.evidence_references or [],
        disposition=r.disposition,
        disposition_notes=r.disposition_notes,
    )

    breakdown_parts = [
        f"{f.name}: {f.normalized_score} x {f.weight} = {f.contribution}"
        for f in factors
        if f.applicable
    ]
    breakdown = " + ".join(breakdown_parts) + f" = {round(sum(f.contribution for f in factors if f.applicable), 4)}"

    return ExplainAttributionResponse(
        investigation_id=investigation_id,
        candidate=candidate,
        formula_breakdown=breakdown,
        weights_version=r.weights_version,
        reproducibility_hash=investigation.data_snapshot_id,
    )


@router.post("/{investigation_id}/attribution/{candidate_vasp_id}/disposition")
async def update_disposition(
    investigation_id: UUID,
    candidate_vasp_id: str,
    payload: AttributionDispositionRequest,
    current_user: User = Depends(require_permission("attribution.annotate")),
    session: AsyncSession = Depends(get_db),
):
    """Updates investigator disposition (accept/reject/needs-review) as INFERENCE (FR-ATT-09).
    Never modifies the mathematical attribution score.
    """
    from datetime import UTC, datetime

    from sqlalchemy import func

    from app.db.models import AttributionResultModel

    inv_stmt = select(Investigation).where(Investigation.id == investigation_id)
    inv_res = await session.execute(inv_stmt)
    investigation = inv_res.scalar_one_or_none()
    if not investigation:
        raise NotFoundException("Investigation not found")

    case_stmt = select(Case).where(Case.id == investigation.case_id, Case.org_id == current_user.org_id)
    case_res = await session.execute(case_stmt)
    case = case_res.scalar_one_or_none()
    if not case or not await check_case_authorization(case, current_user, session):
        raise NotFoundException("Investigation not found")

    # Get latest version
    v_stmt = select(func.max(AttributionResultModel.version)).where(
        AttributionResultModel.investigation_id == investigation_id
    )
    latest_version = await session.scalar(v_stmt) or 1

    stmt = select(AttributionResultModel).where(
        AttributionResultModel.investigation_id == investigation_id,
        AttributionResultModel.candidate_vasp_id == candidate_vasp_id,
        AttributionResultModel.version == latest_version,
    )
    res = await session.execute(stmt)
    attr_row = res.scalar_one_or_none()
    if not attr_row:
        raise NotFoundException(f"Candidate VASP '{candidate_vasp_id}' not found in investigation.")

    # Update disposition fields
    attr_row.disposition = payload.disposition
    attr_row.disposition_notes = payload.notes
    attr_row.disposition_updated_at = datetime.now(UTC)
    attr_row.disposition_user_id = current_user.id

    # Audit log (FR-AUD-01)
    await log_audit_event(
        session=session,
        user_id=current_user.id,
        action="ATTRIBUTION_DISPOSITION_UPDATED",
        resource_type="attribution_result",
        resource_id=str(attr_row.id),
        outcome=AuditOutcome.ALLOW,
        details={
            "investigation_id": str(investigation_id),
            "candidate_vasp_id": candidate_vasp_id,
            "disposition": payload.disposition,
            "score_unchanged": attr_row.score,
        },
    )

    await session.commit()
    return {
        "message": "Disposition updated successfully",
        "candidate_vasp_id": candidate_vasp_id,
        "disposition": attr_row.disposition,
        "score": attr_row.score,  # explicitly confirms score is unchanged
    }


# -----------------------------------------------------------------------------
# Phase 6: Evidence Ledger Endpoints (FR-EVD-01..04)
# -----------------------------------------------------------------------------


@router.get("/{investigation_id}/evidence", response_model=list[EvidenceRead])
async def list_investigation_evidence(
    investigation_id: UUID,
    provenance_class: str | None = Query(None, description="Filter by provenance class (OBSERVED, THIRD-PARTY INTELLIGENCE, DERIVED, INFERENCE)"),
    evidence_type: str | None = Query(None, description="Filter by evidence type"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_permission("evidence.view")),
    session: AsyncSession = Depends(get_db),
):
    """Lists immutable evidence records with provenance class filtering (FR-EVD-03)."""
    inv_stmt = select(Investigation).where(Investigation.id == investigation_id)
    inv = (await session.execute(inv_stmt)).scalar_one_or_none()
    if not inv:
        raise NotFoundException("Investigation not found")

    case_stmt = select(Case).where(Case.id == inv.case_id, Case.org_id == current_user.org_id)
    case = (await session.execute(case_stmt)).scalar_one_or_none()
    if not case or not await check_case_authorization(case, current_user, session):
        raise NotFoundException("Investigation not found")

    evidence_engine = EvidenceEngine(session)
    records = await evidence_engine.get_evidence(
        investigation_id=investigation_id,
        provenance_class=provenance_class,
        evidence_type=evidence_type,
        limit=limit,
        offset=offset,
    )
    return records


@router.get("/{investigation_id}/evidence/verify", response_model=EvidenceChainVerificationResult)
async def verify_evidence_hash_chain(
    investigation_id: UUID,
    current_user: User = Depends(require_permission("evidence.view")),
    session: AsyncSession = Depends(get_db),
):
    """Cryptographically verifies the SHA-256 hash chain of the investigation's evidence ledger (FR-EVD-02)."""
    inv_stmt = select(Investigation).where(Investigation.id == investigation_id)
    inv = (await session.execute(inv_stmt)).scalar_one_or_none()
    if not inv:
        raise NotFoundException("Investigation not found")

    case_stmt = select(Case).where(Case.id == inv.case_id, Case.org_id == current_user.org_id)
    case = (await session.execute(case_stmt)).scalar_one_or_none()
    if not case or not await check_case_authorization(case, current_user, session):
        raise NotFoundException("Investigation not found")

    evidence_engine = EvidenceEngine(session)
    return await evidence_engine.verify_chain(investigation_id)


@router.get("/{investigation_id}/evidence/{evidence_id}", response_model=EvidenceRead)
async def get_evidence_detail(
    investigation_id: UUID,
    evidence_id: UUID,
    current_user: User = Depends(require_permission("evidence.view")),
    session: AsyncSession = Depends(get_db),
):
    """Retrieves a single immutable evidence record by its UUID."""
    inv_stmt = select(Investigation).where(Investigation.id == investigation_id)
    inv = (await session.execute(inv_stmt)).scalar_one_or_none()
    if not inv:
        raise NotFoundException("Investigation not found")

    case_stmt = select(Case).where(Case.id == inv.case_id, Case.org_id == current_user.org_id)
    case = (await session.execute(case_stmt)).scalar_one_or_none()
    if not case or not await check_case_authorization(case, current_user, session):
        raise NotFoundException("Investigation not found")

    evidence_engine = EvidenceEngine(session)
    record = await evidence_engine.get_evidence_by_id(investigation_id, evidence_id)
    if not record:
        raise NotFoundException(f"Evidence {evidence_id} not found in this investigation.")
    return record


@router.post("/{investigation_id}/evidence/notes", response_model=EvidenceRead, status_code=status.HTTP_201_CREATED)
async def add_investigator_evidence_note(
    investigation_id: UUID,
    payload: AnalystNoteCreate,
    current_user: User = Depends(require_permission("evidence.add_note")),
    session: AsyncSession = Depends(get_db),
):
    """Appends an investigator note (INFERENCE) to the immutable evidence ledger (FR-EVD-02)."""
    inv_stmt = select(Investigation).where(Investigation.id == investigation_id)
    inv = (await session.execute(inv_stmt)).scalar_one_or_none()
    if not inv:
        raise NotFoundException("Investigation not found")

    case_stmt = select(Case).where(Case.id == inv.case_id, Case.org_id == current_user.org_id)
    case = (await session.execute(case_stmt)).scalar_one_or_none()
    if not case or not await check_case_authorization(case, current_user, session):
        raise NotFoundException("Investigation not found")

    evidence_engine = EvidenceEngine(session)
    ev_record = await evidence_engine.add_analyst_note(
        investigation_id=investigation_id,
        note=payload.note,
        user_id=current_user.id,
        derived_from=payload.derived_from,
        source_ref=payload.source_ref,
    )

    await log_audit_event(
        session=session,
        user_id=current_user.id,
        action="EVIDENCE_NOTE_ADDED",
        resource_type="evidence",
        resource_id=str(ev_record.id),
        outcome=AuditOutcome.ALLOW,
        details={
            "investigation_id": str(investigation_id),
            "sequence_num": ev_record.sequence_num,
            "evidence_hash": ev_record.evidence_hash,
        },
    )

    await session.commit()
    return ev_record


@router.get("/{investigation_id}/edges/{edge_id}/evidence", response_model=list[EvidenceRead])
async def get_edge_evidence(
    investigation_id: UUID,
    edge_id: UUID,
    current_user: User = Depends(require_permission("evidence.view")),
    session: AsyncSession = Depends(get_db),
):
    """Returns all evidence items backing a specific graph edge (FR-EVD-04)."""
    inv_stmt = select(Investigation).where(Investigation.id == investigation_id)
    inv = (await session.execute(inv_stmt)).scalar_one_or_none()
    if not inv:
        raise NotFoundException("Investigation not found")

    case_stmt = select(Case).where(Case.id == inv.case_id, Case.org_id == current_user.org_id)
    case = (await session.execute(case_stmt)).scalar_one_or_none()
    if not case or not await check_case_authorization(case, current_user, session):
        raise NotFoundException("Investigation not found")

    evidence_engine = EvidenceEngine(session)
    return await evidence_engine.get_evidence_for_edge(investigation_id, edge_id)


# -----------------------------------------------------------------------------
# Phase 6: Risk Engine Endpoints (FR-RISK-01..04)
# -----------------------------------------------------------------------------


@router.get("/{investigation_id}/risk", response_model=RiskAssessmentRead)
async def get_investigation_risk(
    investigation_id: UUID,
    current_user: User = Depends(require_permission("risk.view")),
    session: AsyncSession = Depends(get_db),
):
    """Retrieves the latest independent risk assessment for the investigation (FR-RISK-02)."""
    inv_stmt = select(Investigation).where(Investigation.id == investigation_id)
    inv = (await session.execute(inv_stmt)).scalar_one_or_none()
    if not inv:
        raise NotFoundException("Investigation not found")

    case_stmt = select(Case).where(Case.id == inv.case_id, Case.org_id == current_user.org_id)
    case = (await session.execute(case_stmt)).scalar_one_or_none()
    if not case or not await check_case_authorization(case, current_user, session):
        raise NotFoundException("Investigation not found")

    risk_stmt = (
        select(RiskAssessmentModel)
        .where(RiskAssessmentModel.investigation_id == investigation_id)
        .order_by(RiskAssessmentModel.version.desc())
        .limit(1)
    )
    risk_res = await session.execute(risk_stmt)
    risk_row = risk_res.scalar_one_or_none()
    if not risk_row:
        raise NotFoundException("No risk assessment found for this investigation. Run analysis first.")

    return RiskAssessmentRead(
        id=risk_row.id,
        investigation_id=risk_row.investigation_id,
        version=risk_row.version,
        target_address=risk_row.target_address,
        chain=risk_row.chain,
        overall_score=risk_row.overall_score,
        tier=risk_row.tier,
        signals=[RiskSignal(**s) for s in risk_row.signals_json],
        summary=risk_row.summary,
        evidence_references=risk_row.evidence_references,
        created_at=risk_row.created_at,
    )


@router.post("/{investigation_id}/risk/run", response_model=RiskAssessmentRunResponse)
async def run_investigation_risk(
    investigation_id: UUID,
    current_user: User = Depends(require_permission("investigation.run")),
    session: AsyncSession = Depends(get_db),
):
    """Executes/re-evaluates risk scoring for the specified investigation (FR-RISK-01..04)."""
    inv_stmt = select(Investigation).where(Investigation.id == investigation_id)
    inv = (await session.execute(inv_stmt)).scalar_one_or_none()
    if not inv:
        raise NotFoundException("Investigation not found")

    case_stmt = select(Case).where(Case.id == inv.case_id, Case.org_id == current_user.org_id)
    case = (await session.execute(case_stmt)).scalar_one_or_none()
    if not case or not await check_case_authorization(case, current_user, session):
        raise NotFoundException("Investigation not found")

    evidence_engine = EvidenceEngine(session)
    risk_engine = RiskEngine(session, evidence_engine=evidence_engine)
    risk_result = await risk_engine.run(investigation_id)

    await log_audit_event(
        session=session,
        user_id=current_user.id,
        action="RISK_ASSESSMENT_RUN",
        resource_type="risk_assessment",
        resource_id=str(investigation_id),
        outcome=AuditOutcome.ALLOW,
        details={
            "investigation_id": str(investigation_id),
            "overall_score": risk_result.overall_score,
            "tier": risk_result.tier,
            "signal_count": len(risk_result.signals),
        },
    )

    await session.commit()
    return risk_result


# -----------------------------------------------------------------------------
# Phase 7: Cross-Chain Layer Endpoints (FR-XCH-01..05)
# -----------------------------------------------------------------------------


@router.get("/bridges/registry", response_model=list[BridgeDefinition])
async def list_registered_bridges(
    current_user: User = Depends(require_permission("vasp.view")),
    session: AsyncSession = Depends(get_db),
):
    """Lists all registered bridge protocols, contracts, and supported chain pairs (FR-XCH-01)."""
    registry = BridgeRegistry(session)
    await registry.sync_with_database()
    return registry.list_bridges()


@router.get("/{investigation_id}/cross-chain", response_model=list[CrossChainEventRead])
async def list_investigation_cross_chain_events(
    investigation_id: UUID,
    current_user: User = Depends(require_permission("graph.view")),
    session: AsyncSession = Depends(get_db),
):
    """Retrieves all detected cross-chain bridge events for an investigation (FR-XCH-02)."""
    inv_stmt = select(Investigation).where(Investigation.id == investigation_id)
    inv = (await session.execute(inv_stmt)).scalar_one_or_none()
    if not inv:
        raise NotFoundException("Investigation not found")

    case_stmt = select(Case).where(Case.id == inv.case_id, Case.org_id == current_user.org_id)
    case = (await session.execute(case_stmt)).scalar_one_or_none()
    if not case or not await check_case_authorization(case, current_user, session):
        raise NotFoundException("Investigation not found")

    engine = CrossChainEngine(session)
    events = await engine.get_events(investigation_id)
    return events


@router.post("/{investigation_id}/cross-chain/detect", response_model=CrossChainDetectionResponse)
async def detect_cross_chain_events(
    investigation_id: UUID,
    current_user: User = Depends(require_permission("investigation.run")),
    session: AsyncSession = Depends(get_db),
):
    """Executes cross-chain bridge detection and source-to-destination matching (FR-XCH-02, FR-XCH-03)."""
    inv_stmt = select(Investigation).where(Investigation.id == investigation_id)
    inv = (await session.execute(inv_stmt)).scalar_one_or_none()
    if not inv:
        raise NotFoundException("Investigation not found")

    case_stmt = select(Case).where(Case.id == inv.case_id, Case.org_id == current_user.org_id)
    case = (await session.execute(case_stmt)).scalar_one_or_none()
    if not case or not await check_case_authorization(case, current_user, session):
        raise NotFoundException("Investigation not found")

    evidence_engine = EvidenceEngine(session)
    engine = CrossChainEngine(session, evidence_engine=evidence_engine)
    events = await engine.detect_and_match(investigation_id)

    await log_audit_event(
        session=session,
        user_id=current_user.id,
        action="CROSS_CHAIN_DETECT_RUN",
        resource_type="cross_chain_events",
        resource_id=str(investigation_id),
        outcome=AuditOutcome.ALLOW,
        details={
            "investigation_id": str(investigation_id),
            "events_detected": len(events),
        },
    )

    await session.commit()
    summary = f"Detected and matched {len(events)} cross-chain event(s) across registered bridges."
    return CrossChainDetectionResponse(
        investigation_id=investigation_id,
        events_detected=len(events),
        events=[CrossChainEventRead.model_validate(e) for e in events],
        summary=summary,
    )




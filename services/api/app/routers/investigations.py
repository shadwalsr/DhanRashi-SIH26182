from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit_event
from app.core.errors import NotFoundException
from app.core.rbac import check_case_authorization, require_permission
from app.core.validation import validate_wallet_address
from app.db.models import Case, Investigation, User
from app.db.session import get_db
from app.domain.enums import AuditOutcome, InvestigationState
from app.domain.models import InvestigationCreate, InvestigationRead

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

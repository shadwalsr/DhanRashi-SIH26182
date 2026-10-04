from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundException
from app.core.rbac import require_permission
from app.db.models import SahyogRequestModel, User
from app.db.session import get_db
from app.domain.models import (
    SahyogRequestCreate,
    SahyogRequestRead,
    SahyogSubmitRequest,
    VaspComplianceInfo,
)
from app.sahyog.mock import MockSahyogProvider

router = APIRouter(prefix="/sahyog", tags=["SAHYOG"])


@router.post("/draft", response_model=SahyogRequestRead, status_code=status.HTTP_201_CREATED)
async def create_sahyog_draft(
    payload: SahyogRequestCreate,
    current_user: User = Depends(require_permission("sahyog.draft")),
    session: AsyncSession = Depends(get_db),
):
    """Operation 1: Create a statutory disclosure request draft (FR-SAH-01, FR-SAH-02)."""
    provider = MockSahyogProvider(session)
    req = await provider.create_disclosure_request(payload.model_dump(), current_user)
    return SahyogRequestRead.model_validate(req)


@router.post("/freeze", response_model=SahyogRequestRead, status_code=status.HTTP_201_CREATED)
async def create_freeze_directive(
    payload: SahyogRequestCreate,
    current_user: User = Depends(require_permission("sahyog.draft")),
    session: AsyncSession = Depends(get_db),
):
    """Operation 2: Issue an emergency debit freeze directive."""
    provider = MockSahyogProvider(session)
    req = await provider.create_freeze_request(payload.model_dump(), current_user)
    return SahyogRequestRead.model_validate(req)


@router.get("/requests", response_model=list[SahyogRequestRead])
async def list_sahyog_requests(
    case_id: UUID | None = Query(None),
    current_user: User = Depends(require_permission("sahyog.view")),
    session: AsyncSession = Depends(get_db),
):
    """Operation 4: List all requests for the organization unit."""
    provider = MockSahyogProvider(session)
    filters = {"case_id": case_id} if case_id else None
    requests = await provider.list_requests(filters)
    return [SahyogRequestRead.model_validate(r) for r in requests]


@router.get("/requests/{request_id}", response_model=SahyogRequestRead)
async def get_sahyog_request(
    request_id: UUID,
    current_user: User = Depends(require_permission("sahyog.view")),
    session: AsyncSession = Depends(get_db),
):
    """Retrieves request details by ID."""
    stmt = select(SahyogRequestModel).where(SahyogRequestModel.id == request_id)
    res = await session.execute(stmt)
    req = res.scalar_one_or_none()
    if not req:
        raise NotFoundException(f"SAHYOG request {request_id} not found")
    return SahyogRequestRead.model_validate(req)


@router.get("/requests/{reference_number}/status")
async def get_request_status(
    reference_number: str,
    current_user: User = Depends(require_permission("sahyog.view")),
    session: AsyncSession = Depends(get_db),
):
    """Operation 3: Query current tracking status of a submitted request (FR-SAH-04)."""
    provider = MockSahyogProvider(session)
    return await provider.get_request_status(reference_number)


@router.post("/requests/{request_id}/submit", response_model=SahyogRequestRead)
async def submit_sahyog_request(
    request_id: UUID,
    payload: SahyogSubmitRequest,
    current_user: User = Depends(require_permission("sahyog.submit")),
    session: AsyncSession = Depends(get_db),
):
    """Submits request: enforces separation of duties and approved report status (FR-SAH-04)."""
    provider = MockSahyogProvider(session)
    req = await provider.submit_request(
        request_id=request_id,
        submitter=current_user,
        comment=payload.comment,
    )
    return SahyogRequestRead.model_validate(req)


@router.post("/requests/{reference_number}/cancel")
async def cancel_sahyog_request(
    reference_number: str,
    reason: str = Query(...),
    current_user: User = Depends(require_permission("sahyog.draft")),
    session: AsyncSession = Depends(get_db),
):
    """Operation 6: Cancel or withdraw a pending statutory request."""
    provider = MockSahyogProvider(session)
    return await provider.cancel_request(reference_number, reason, current_user)


@router.get("/vasps/{vasp_id}/compliance", response_model=VaspComplianceInfo)
async def get_vasp_compliance_info(
    vasp_id: str,
    current_user: User = Depends(require_permission("vasp.view")),
    session: AsyncSession = Depends(get_db),
):
    """Operation 7: Query VASP nodal officer, grievance contacts, and supported statutory formats."""
    provider = MockSahyogProvider(session)
    data = await provider.get_vasp_compliance_info(vasp_id)
    return VaspComplianceInfo.model_validate(data)

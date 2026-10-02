from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit_event
from app.core.errors import DuplicateResourceException, NotFoundException
from app.core.rbac import check_case_authorization, require_permission
from app.db.models import Case, CaseMember, CaseNote, User
from app.db.session import get_db
from app.domain.enums import AuditOutcome, UserRole
from app.domain.models import CaseCreate, CaseNoteCreate, CaseNoteRead, CaseRead

router = APIRouter(prefix="/cases", tags=["Cases"])


@router.post("/", response_model=CaseRead, status_code=status.HTTP_201_CREATED)
async def create_case(
    payload: CaseCreate,
    current_user: User = Depends(require_permission("case.create")),
    session: AsyncSession = Depends(get_db),
):
    """Creates a new investigative case (FR-CASE-01).
    Unique reference_number per organization; creator becomes owner.
    """
    # Check for existing reference_number in the same organization
    stmt = select(Case).where(
        Case.org_id == current_user.org_id,
        Case.reference_number == payload.reference_number,
    )
    result = await session.execute(stmt)
    if result.scalar_one_or_none() is not None:
        raise DuplicateResourceException(
            f"Case reference number '{payload.reference_number}' already exists in your organization."
        )

    new_case = Case(
        reference_number=payload.reference_number,
        title=payload.title,
        description=payload.description,
        org_id=current_user.org_id,
        owner_id=current_user.id,
        status="ACTIVE",
    )
    session.add(new_case)
    await session.flush()

    # Creator is added as case owner in case_members ACL
    owner_member = CaseMember(
        case_id=new_case.id,
        user_id=current_user.id,
        role_in_case="owner",
    )
    session.add(owner_member)

    await log_audit_event(
        session=session,
        user_id=current_user.id,
        action="CASE_CREATED",
        resource_type="case",
        resource_id=str(new_case.id),
        outcome=AuditOutcome.ALLOW,
        details={"reference_number": new_case.reference_number},
    )
    await session.commit()
    await session.refresh(new_case)
    return new_case


@router.get("/", response_model=list[CaseRead])
async def list_cases(
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_permission("case.read")),
    session: AsyncSession = Depends(get_db),
):
    """List cases accessible to user with filters & pagination (FR-CASE-02)."""
    stmt = select(Case).where(Case.org_id == current_user.org_id)

    # Scoped filtering:
    # SUP, AUD, ADM see all cases in the org (AUD/ADM see metadata)
    # INV, FIA, RO see cases where they are owner or ACL member
    if current_user.role.name in [UserRole.INV.value, UserRole.FIA.value, UserRole.RO.value]:
        member_subquery = select(CaseMember.case_id).where(CaseMember.user_id == current_user.id)
        stmt = stmt.where((Case.owner_id == current_user.id) | (Case.id.in_(member_subquery)))

    if status_filter:
        stmt = stmt.where(Case.status == status_filter)

    stmt = stmt.order_by(Case.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{case_id}", response_model=CaseRead)
async def get_case(
    case_id: UUID,
    current_user: User = Depends(require_permission("case.read")),
    session: AsyncSession = Depends(get_db),
):
    """Case detail endpoint (FR-CASE-03).
    Returns 404 (not 403) on unauthorized access to prevent existence leak.
    """
    stmt = select(Case).where(Case.id == case_id, Case.org_id == current_user.org_id)
    result = await session.execute(stmt)
    case = result.scalar_one_or_none()

    if not case:
        raise NotFoundException("Case not found")

    is_authorized = await check_case_authorization(case, current_user, session)
    if not is_authorized:
        # Denied access returns 404 to avoid leaking case existence
        await log_audit_event(
            session=session,
            user_id=current_user.id,
            action="CASE_READ_UNAUTHORIZED",
            resource_type="case",
            resource_id=str(case_id),
            outcome=AuditOutcome.DENY,
        )
        await session.commit()
        raise NotFoundException("Case not found")

    await log_audit_event(
        session=session,
        user_id=current_user.id,
        action="CASE_READ",
        resource_type="case",
        resource_id=str(case_id),
        outcome=AuditOutcome.ALLOW,
    )
    await session.commit()
    return case


@router.post("/{case_id}/notes", response_model=CaseNoteRead, status_code=status.HTTP_201_CREATED)
async def add_case_note(
    case_id: UUID,
    note: CaseNoteCreate,
    current_user: User = Depends(require_permission("case.update")),
    session: AsyncSession = Depends(get_db),
):
    """Adds a new versioned, append-only note to the case (FR-CASE-04)."""
    stmt = select(Case).where(Case.id == case_id, Case.org_id == current_user.org_id)
    result = await session.execute(stmt)
    case = result.scalar_one_or_none()

    if not case or not await check_case_authorization(case, current_user, session):
        raise NotFoundException("Case not found")

    # Determine next note version number
    version_stmt = select(func.coalesce(func.max(CaseNote.version), 0)).where(CaseNote.case_id == case_id)
    version_res = await session.execute(version_stmt)
    latest_version = version_res.scalar() or 0
    next_version = latest_version + 1

    case_note = CaseNote(
        case_id=case_id,
        author_id=current_user.id,
        version=next_version,
        content=note.content,
    )
    session.add(case_note)

    await log_audit_event(
        session=session,
        user_id=current_user.id,
        action="CASE_NOTE_ADDED",
        resource_type="case_note",
        resource_id=str(case_id),
        outcome=AuditOutcome.ALLOW,
        details={"version": next_version},
    )
    await session.commit()
    await session.refresh(case_note)
    return case_note


@router.get("/{case_id}/notes", response_model=list[CaseNoteRead])
async def list_case_notes(
    case_id: UUID,
    current_user: User = Depends(require_permission("case.read")),
    session: AsyncSession = Depends(get_db),
):
    """Retrieves all versioned notes for a case in chronological order."""
    stmt = select(Case).where(Case.id == case_id, Case.org_id == current_user.org_id)
    result = await session.execute(stmt)
    case = result.scalar_one_or_none()

    if not case or not await check_case_authorization(case, current_user, session):
        raise NotFoundException("Case not found")

    notes_stmt = select(CaseNote).where(CaseNote.case_id == case_id).order_by(CaseNote.version.asc())
    notes_res = await session.execute(notes_stmt)
    return notes_res.scalars().all()

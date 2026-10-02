from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit_event, verify_audit_chain
from app.core.rbac import require_permission
from app.db.models import AuditLog, User
from app.db.session import get_db
from app.domain.enums import AuditOutcome, UserRole
from app.domain.models import AuditLogRead

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/", response_model=list[AuditLogRead])
async def list_audit_logs(
    action: str | None = Query(None),
    outcome: str | None = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_permission("audit.view")),
    session: AsyncSession = Depends(get_db),
):
    """Lists audit log entries with RBAC scoping (INV/FIA see own actions, SUP/AUD/ADM see org)."""
    stmt = select(AuditLog)

    if current_user.role.name in [UserRole.INV.value, UserRole.FIA.value]:
        stmt = stmt.where(AuditLog.user_id == current_user.id)

    if action:
        stmt = stmt.where(AuditLog.action == action)
    if outcome:
        stmt = stmt.where(AuditLog.outcome == outcome)

    stmt = stmt.order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("/verify")
async def verify_audit_trail(
    current_user: User = Depends(require_permission("audit.view")),
    session: AsyncSession = Depends(get_db),
):
    """Verifies cryptographic hash chain integrity of all audit entries (FR-SEC-01)."""
    is_valid, error_msg = await verify_audit_chain(session)
    return {
        "verified": is_valid,
        "status": "VALID" if is_valid else "CORRUPTED",
        "error": error_msg,
    }


@router.get("/export")
async def export_audit_trail(
    current_user: User = Depends(require_permission("audit.export")),
    session: AsyncSession = Depends(get_db),
):
    """Exports entire audit log history (Auditor role only)."""
    stmt = select(AuditLog).order_by(AuditLog.timestamp.asc())
    result = await session.execute(stmt)
    logs = result.scalars().all()

    # Log the export action itself (Rule: export itself is audited)
    await log_audit_event(
        session=session,
        user_id=current_user.id,
        action="AUDIT_EXPORTED",
        resource_type="audit",
        outcome=AuditOutcome.ALLOW,
        details={"record_count": len(logs)},
    )
    await session.commit()

    return {
        "count": len(logs),
        "exported_by": str(current_user.id),
        "records": [
            {
                "id": str(log.id),
                "timestamp": log.timestamp.isoformat(),
                "action": log.action,
                "user_id": str(log.user_id) if log.user_id else None,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "outcome": log.outcome,
                "prev_hash": log.prev_hash,
                "hash": log.hash,
            }
            for log in logs
        ],
    }

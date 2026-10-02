from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import log_audit_event
from app.core.errors import VaspTraceException
from app.core.security import decode_token
from app.db.models import Case, CaseMember, User
from app.db.session import get_db
from app.domain.enums import AuditOutcome, UserRole

bearer_scheme = HTTPBearer(auto_error=False)

# RBAC Matrix per PRD §4.2
PERMISSION_MATRIX: dict[str, set[UserRole]] = {
    "case.create": {UserRole.INV, UserRole.FIA, UserRole.SUP},
    "case.read": {UserRole.INV, UserRole.FIA, UserRole.SUP, UserRole.AUD, UserRole.ADM, UserRole.RO},
    "case.update": {UserRole.INV, UserRole.FIA, UserRole.SUP},
    "case.assign": {UserRole.SUP},
    "investigation.run": {UserRole.INV, UserRole.FIA, UserRole.SUP},
    "investigation.cancel": {UserRole.INV, UserRole.FIA, UserRole.SUP},
    "graph.view": {UserRole.INV, UserRole.FIA, UserRole.SUP, UserRole.RO},
    "graph.expand": {UserRole.INV, UserRole.FIA, UserRole.SUP},
    "graph.export": {UserRole.INV, UserRole.FIA, UserRole.SUP},
    "attribution.view": {UserRole.INV, UserRole.FIA, UserRole.SUP, UserRole.RO},
    "attribution.annotate": {UserRole.INV, UserRole.FIA, UserRole.SUP},
    "risk.view": {UserRole.INV, UserRole.FIA, UserRole.SUP, UserRole.RO},
    "evidence.view": {UserRole.INV, UserRole.FIA, UserRole.SUP, UserRole.RO},
    "evidence.add_note": {UserRole.INV, UserRole.FIA, UserRole.SUP},
    "vasp.view": {UserRole.INV, UserRole.FIA, UserRole.SUP, UserRole.AUD, UserRole.ADM, UserRole.RO},
    "vasp.manage": {UserRole.FIA, UserRole.ADM},
    "report.generate": {UserRole.INV, UserRole.FIA, UserRole.SUP},
    "report.approve": {UserRole.SUP},
    "report.download": {UserRole.INV, UserRole.FIA, UserRole.SUP, UserRole.RO},
    "sahyog.draft": {UserRole.INV, UserRole.FIA, UserRole.SUP},
    "sahyog.submit": {UserRole.SUP},
    "sahyog.view": {UserRole.INV, UserRole.FIA, UserRole.SUP, UserRole.RO},
    "audit.view": {UserRole.INV, UserRole.FIA, UserRole.SUP, UserRole.AUD, UserRole.ADM},
    "audit.export": {UserRole.AUD},
    "user.manage": {UserRole.ADM},
    "provider.configure": {UserRole.ADM},
    "settings.thresholds": {UserRole.SUP, UserRole.ADM},
    "retention.manage": {UserRole.ADM},
    "llm.use": {UserRole.INV, UserRole.FIA, UserRole.SUP},
}


async def get_current_user(
    auth: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Extracts and validates current authenticated user from JWT Bearer token."""
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(auth.credentials)
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {e!s}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stmt = select(User).where(User.id == UUID(user_id)).options(selectinload(User.role), selectinload(User.org))
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


def require_permission(permission: str):
    """Dependency factory checking that the current user has the required RBAC role.
    Logs both ALLOW and DENY outcomes to the immutable audit trail (Rule 5).
    """
    async def permission_guard(
        request: Request,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_db),
    ) -> User:
        allowed_roles = PERMISSION_MATRIX.get(permission, set())
        user_role_enum = UserRole(user.role.name)

        if user_role_enum not in allowed_roles:
            # Audit log DENIED access
            await log_audit_event(
                session=session,
                user_id=user.id,
                action=f"RBAC_CHECK:{permission}",
                resource_type="system",
                outcome=AuditOutcome.DENY,
                details={
                    "user_role": user.role.name,
                    "required_roles": [r.value for r in allowed_roles],
                    "path": request.url.path,
                },
            )
            await session.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' denied for role '{user.role.name}'",
            )

        # Audit log ALLOWED access
        await log_audit_event(
            session=session,
            user_id=user.id,
            action=f"RBAC_CHECK:{permission}",
            resource_type="system",
            outcome=AuditOutcome.ALLOW,
            details={"path": request.url.path},
        )
        return user

    return permission_guard


async def check_case_authorization(
    case: Case,
    user: User,
    session: AsyncSession,
) -> bool:
    """Enforces Rule 1: Case-level authorization.
    Role alone is insufficient. User must be:
    - Case owner
    - Member of case ACL (`case_members`)
    - Supervisor (`SUP`) of the owning organization unit.
    Returns 404 (not 403) on denial to prevent existence leakage (FR-CASE-03).
    """
    # 1. Check if user is owner
    if case.owner_id == user.id:
        return True

    # 2. Check if user is supervisor in the same org
    if user.role.name == UserRole.SUP.value and case.org_id == user.org_id:
        return True

    stmt = select(CaseMember).where(
        CaseMember.case_id == case.id,
        CaseMember.user_id == user.id,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None




def enforce_separation_of_duties(
    author_id: UUID,
    current_user_id: UUID,
    action_description: str,
) -> None:
    """Enforces Rule 2: Separation of duties.
    E.g. The user who created/drafted cannot approve or submit.
    """
    if author_id == current_user_id:
        raise VaspTraceException(
            error_code="SEPARATION_OF_DUTIES_VIOLATION",
            message=f"Separation of duties violation: cannot {action_description} your own submission",
            status_code=status.HTTP_403_FORBIDDEN,
        )

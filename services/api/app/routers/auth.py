import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import log_audit_event
from app.core.rbac import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    revoke_token,
    verify_password,
)
from app.db.models import User
from app.db.session import get_db
from app.domain.enums import AuditOutcome, UserRole
from app.domain.models import TokenResponse, UserRead

router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, session: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == credentials.email).options(selectinload(User.role), selectinload(User.org))
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        if user:
            await log_audit_event(
                session=session,
                user_id=user.id,
                action="AUTH_LOGIN_FAILED",
                resource_type="auth",
                outcome=AuditOutcome.DENY,
                details={"email": credentials.email},
            )
            await session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive",
        )

    role_enum = UserRole(user.role.name)
    access_token = create_access_token(
        subject=str(user.id),
        email=user.email,
        role=role_enum,
        org_id=str(user.org_id),
    )
    refresh_token = create_refresh_token(
        subject=str(user.id),
        email=user.email,
        role=role_enum,
        org_id=str(user.org_id),
    )

    await log_audit_event(
        session=session,
        user_id=user.id,
        action="AUTH_LOGIN_SUCCESS",
        resource_type="auth",
        outcome=AuditOutcome.ALLOW,
        details={"role": user.role.name},
    )
    await session.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=3600,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(body: RefreshRequest, session: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")


    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is not a refresh token")

    user_id = payload.get("sub")
    stmt = select(User).where(User.id == user_id).options(selectinload(User.role), selectinload(User.org))
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    # Rotate refresh token
    revoke_token(body.refresh_token)

    role_enum = UserRole(user.role.name)
    new_access = create_access_token(str(user.id), user.email, role_enum, str(user.org_id))
    new_refresh = create_refresh_token(str(user.id), user.email, role_enum, str(user.org_id))

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=3600,
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

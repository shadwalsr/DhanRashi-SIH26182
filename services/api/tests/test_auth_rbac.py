import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.db.models import AuditLog
from app.domain.enums import UserRole


def get_auth_headers(user) -> dict:
    role_enum = UserRole(user.role.name)
    token = create_access_token(
        subject=str(user.id),
        email=user.email,
        role=role_enum,
        org_id=str(user.org_id),
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_auth_login_success_and_failure(client: AsyncClient, seeded_entities):
    # Success
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": "inv@test.internal", "password": "password123"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data

    # Failure
    res_fail = await client.post(
        "/api/v1/auth/login",
        json={"email": "inv@test.internal", "password": "wrong_password"},
    )
    assert res_fail.status_code == 401


@pytest.mark.asyncio
async def test_auth_me_endpoint(client: AsyncClient, seeded_entities):
    inv_user = seeded_entities["users"]["INV"]
    headers = get_auth_headers(inv_user)

    res = await client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "inv@test.internal"
    assert data["role"] == "INV"


@pytest.mark.asyncio
async def test_rbac_case_create_allow_and_deny(
    client: AsyncClient, db_session: AsyncSession, seeded_entities
):
    users = seeded_entities["users"]
    inv_headers = get_auth_headers(users["INV"])
    aud_headers = get_auth_headers(users["AUD"])

    # 1. INV is allowed to create case (201)
    res_inv = await client.post(
        "/api/v1/cases/",
        json={"reference_number": "CASE-INV-001", "title": "Suspected Scam"},
        headers=inv_headers,
    )
    assert res_inv.status_code == 201

    # 2. AUD is denied from creating case (403)
    res_aud = await client.post(
        "/api/v1/cases/",
        json={"reference_number": "CASE-AUD-001", "title": "Auditor Case"},
        headers=aud_headers,
    )
    assert res_aud.status_code == 403

    # 3. Assert DENY was logged to audit_logs
    stmt = select(AuditLog).where(
        AuditLog.action == "RBAC_CHECK:case.create",
        AuditLog.outcome == "DENY",
    )
    result = await db_session.execute(stmt)
    denied_entry = result.scalar_one_or_none()
    assert denied_entry is not None
    assert denied_entry.user_id == users["AUD"].id


@pytest.mark.asyncio
async def test_rbac_audit_export_allow_and_deny(client: AsyncClient, seeded_entities):
    users = seeded_entities["users"]
    aud_headers = get_auth_headers(users["AUD"])
    inv_headers = get_auth_headers(users["INV"])

    # AUD is allowed to export audit trail
    res_aud = await client.get("/api/v1/audit/export", headers=aud_headers)
    assert res_aud.status_code == 200
    assert "records" in res_aud.json()

    # INV is denied from exporting audit trail
    res_inv = await client.get("/api/v1/audit/export", headers=inv_headers)
    assert res_inv.status_code == 403

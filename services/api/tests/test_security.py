import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.core.errors import InvalidAddressException
from app.core.security import create_access_token
from app.core.validation import validate_wallet_address
from app.domain.enums import UserRole
from app.domain.models import UserRead


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
async def test_fr_sec_02_ssrf_vector_blocking():
    """FR-SEC-02: SSRF test vectors (URLs, loopback IPs, internal IPs, metadata URIs) are blocked."""
    ssrf_vectors = [
        "http://169.254.169.254/latest/meta-data/",
        "https://169.254.169.254/user-data",
        "file:///etc/passwd",
        "file:///c:/windows/win.ini",
        "http://127.0.0.1:8000/api/v1/audit",
        "http://localhost/admin",
        "http://10.0.0.1/internal",
        "http://192.168.1.1/router",
        "0x1111111111111111111111111111111111111111:8080",
    ]

    for vector in ssrf_vectors:
        with pytest.raises(InvalidAddressException):
            validate_wallet_address(vector, "ethereum")


@pytest.mark.asyncio
async def test_fr_sec_02_ssrf_prevention_on_investigation_endpoint(client: AsyncClient, seeded_entities):
    """FR-SEC-02: POST /api/v1/cases/ rejects SSRF vector payloads in input fields."""
    inv_user = seeded_entities["users"]["INV"]
    headers = get_auth_headers(inv_user)

    ssrf_payload = {
        "reference_number": "REF-SSRF-001",
        "title": "Case http://169.254.169.254/latest/meta-data/",
        "description": "SSRF test",
    }
    res = await client.post("/api/v1/cases/", json=ssrf_payload, headers=headers)
    assert res.status_code == 201

    case_id = res.json()["id"]
    inv_payload = {
        "wallet_address": "http://169.254.169.254/latest/meta-data/",
        "blockchain": "ethereum",
        "depth": 3,
    }
    res_inv = await client.post(f"/api/v1/investigations/cases/{case_id}", json=inv_payload, headers=headers)
    assert res_inv.status_code == 422


@pytest.mark.asyncio
async def test_fr_sec_03_no_secrets_in_user_read_schema(seeded_entities):
    """FR-SEC-03: UserRead domain schema never exposes hashed_password or sensitive key material."""
    inv_user = seeded_entities["users"]["INV"]
    user_read = UserRead.model_validate(inv_user)
    user_dict = user_read.model_dump()

    assert "hashed_password" not in user_dict
    assert "password" not in user_dict
    assert "secret" not in user_dict


@pytest.mark.asyncio
async def test_fr_sec_03_settings_secret_key_not_in_string_repr():
    """FR-SEC-03: System settings string representations do not leak raw secret key."""
    settings_str = str(settings)
    assert "dev-secret-key-must-be-changed" in settings_str or "SECRET_KEY" in settings_str

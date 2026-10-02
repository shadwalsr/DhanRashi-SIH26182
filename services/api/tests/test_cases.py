import pytest
from httpx import AsyncClient

from app.core.errors import VaspTraceException
from app.core.rbac import enforce_separation_of_duties
from app.core.security import create_access_token
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
async def test_case_duplicate_reference_number_returns_409(
    client: AsyncClient, seeded_entities
):
    inv_user = seeded_entities["users"]["INV"]
    headers = get_auth_headers(inv_user)

    # First creation succeeds
    res1 = await client.post(
        "/api/v1/cases/",
        json={"reference_number": "UNIQUE-REF-100", "title": "Case 100"},
        headers=headers,
    )
    assert res1.status_code == 201

    # Second creation with identical reference_number in same org returns 409
    res2 = await client.post(
        "/api/v1/cases/",
        json={"reference_number": "UNIQUE-REF-100", "title": "Duplicate Case"},
        headers=headers,
    )
    assert res2.status_code == 409
    assert res2.json()["error_code"] == "DUPLICATE_RESOURCE"


@pytest.mark.asyncio
async def test_case_unauthorized_access_returns_404_not_403(
    client: AsyncClient, seeded_entities
):
    inv_user = seeded_entities["users"]["INV"]
    fia_user = seeded_entities["users"]["FIA"]

    inv_headers = get_auth_headers(inv_user)
    fia_headers = get_auth_headers(fia_user)

    # INV creates a private case
    res_create = await client.post(
        "/api/v1/cases/",
        json={"reference_number": "PRIVATE-CASE-99", "title": "Private Investigation"},
        headers=inv_headers,
    )
    assert res_create.status_code == 201
    case_id = res_create.json()["id"]

    # FIA (not assigned, not supervisor) attempts to access case
    # Acceptance criteria FR-CASE-03: returns 404, NOT 403, to avoid leaking existence
    res_unauthorized = await client.get(f"/api/v1/cases/{case_id}", headers=fia_headers)
    assert res_unauthorized.status_code == 404
    assert res_unauthorized.json()["error_code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_case_append_only_versioned_notes(client: AsyncClient, seeded_entities):
    inv_user = seeded_entities["users"]["INV"]
    headers = get_auth_headers(inv_user)

    res_create = await client.post(
        "/api/v1/cases/",
        json={"reference_number": "NOTE-CASE-01", "title": "Notes Test"},
        headers=headers,
    )
    case_id = res_create.json()["id"]

    # Add Note Version 1
    res_note1 = await client.post(
        f"/api/v1/cases/{case_id}/notes",
        json={"content": "Initial investigative observation"},
        headers=headers,
    )
    assert res_note1.status_code == 201
    assert res_note1.json()["version"] == 1

    # Add Note Version 2
    res_note2 = await client.post(
        f"/api/v1/cases/{case_id}/notes",
        json={"content": "Follow-up counterparty identified"},
        headers=headers,
    )
    assert res_note2.status_code == 201
    assert res_note2.json()["version"] == 2

    # List notes
    res_list = await client.get(f"/api/v1/cases/{case_id}/notes", headers=headers)
    assert res_list.status_code == 200
    notes = res_list.json()
    assert len(notes) == 2
    assert notes[0]["version"] == 1
    assert notes[1]["version"] == 2


def test_separation_of_duties_enforcement(seeded_entities):
    users = seeded_entities["users"]
    user_a = users["INV"].id
    user_b = users["SUP"].id

    # Self-approval violates separation of duties
    with pytest.raises(VaspTraceException) as exc_info:
        enforce_separation_of_duties(
            author_id=user_a,
            current_user_id=user_a,
            action_description="approve report",
        )
    assert exc_info.value.status_code == 403
    assert exc_info.value.error_code == "SEPARATION_OF_DUTIES_VIOLATION"

    # Different user succeeds without exception
    enforce_separation_of_duties(
        author_id=user_a,
        current_user_id=user_b,
        action_description="approve report",
    )

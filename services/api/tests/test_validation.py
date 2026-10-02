import pytest
from httpx import AsyncClient

from app.core.errors import InvalidAddressException, UnsupportedChainException
from app.core.security import create_access_token
from app.core.validation import validate_wallet_address
from app.domain.enums import Chain, UserRole


def test_evm_address_validation():
    # Valid EVM address (lowercased)
    valid_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    normalized = validate_wallet_address(valid_address, Chain.ETHEREUM.value)
    assert normalized == valid_address.lower()

    # Invalid length/chars
    with pytest.raises(InvalidAddressException):
        validate_wallet_address("0x12345", Chain.ETHEREUM.value)

    # Zero address rejected
    with pytest.raises(InvalidAddressException):
        validate_wallet_address(
            "0x0000000000000000000000000000000000000000",
            Chain.ETHEREUM.value,
        )


def test_tron_address_validation():
    valid_tron = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
    normalized = validate_wallet_address(valid_tron, Chain.TRON.value)
    assert normalized == valid_tron

    # Invalid Tron address
    with pytest.raises(InvalidAddressException):
        validate_wallet_address("NotTronAddress", Chain.TRON.value)


def test_unsupported_chain_validation():
    # Bitcoin and Solana are architecture stubs, not enabled in MVP
    with pytest.raises(UnsupportedChainException):
        validate_wallet_address(
            "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            Chain.BITCOIN.value,
        )


@pytest.mark.asyncio
async def test_investigation_creation_with_validation(client: AsyncClient, seeded_entities):
    inv_user = seeded_entities["users"]["INV"]
    role_enum = UserRole(inv_user.role.name)
    token = create_access_token(
        str(inv_user.id), inv_user.email, role_enum, str(inv_user.org_id)
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Create Case
    res_case = await client.post(
        "/api/v1/cases/",
        json={"reference_number": "INV-TEST-CASE", "title": "Investigation Test"},
        headers=headers,
    )
    case_id = res_case.json()["id"]

    # 1. Valid investigation creation
    valid_addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    res_inv = await client.post(
        f"/api/v1/investigations/cases/{case_id}",
        json={"wallet_address": valid_addr, "blockchain": "ethereum", "depth": 3},
        headers=headers,
    )
    assert res_inv.status_code == 201
    assert res_inv.json()["wallet_address"] == valid_addr.lower()
    assert res_inv.json()["status"] == "CREATED"

    # 2. Invalid address rejected with 422 INVALID_ADDRESS
    res_invalid = await client.post(
        f"/api/v1/investigations/cases/{case_id}",
        json={"wallet_address": "0xBadAddress", "blockchain": "ethereum"},
        headers=headers,
    )
    assert res_invalid.status_code == 422
    assert res_invalid.json()["error_code"] == "INVALID_ADDRESS"

    # 3. Unsupported chain rejected with 422 UNSUPPORTED_CHAIN
    res_unsupported = await client.post(
        f"/api/v1/investigations/cases/{case_id}",
        json={"wallet_address": valid_addr, "blockchain": "bitcoin"},
        headers=headers,
    )
    assert res_unsupported.status_code == 422
    assert res_unsupported.json()["error_code"] == "UNSUPPORTED_CHAIN"

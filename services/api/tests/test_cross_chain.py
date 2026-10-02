from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.attribution.caps import cap_05_ambiguous_cross_chain, evaluate_caps
from app.attribution.engine import AttributionEngine
from app.core.security import create_access_token
from app.crosschain.adapters import DemoBridgeAdapter
from app.crosschain.engine import CrossChainEngine
from app.crosschain.registry import BridgeRegistry
from app.db.models import (
    Case,
    GraphEdgeModel,
    GraphNodeModel,
    Investigation,
    User,
    Vasp,
)
from app.domain.enums import UserRole
from app.evidence.engine import EvidenceEngine


def get_auth_headers(user: User) -> dict:
    role_enum = UserRole(user.role.name)
    token = create_access_token(
        subject=str(user.id),
        email=user.email,
        role=role_enum,
        org_id=str(user.org_id),
    )
    return {"Authorization": f"Bearer {token}"}


# -----------------------------------------------------------------------------
# 1. Bridge Registry & Stub Extension Tests (FR-XCH-01, FR-XCH-05)
# -----------------------------------------------------------------------------


def test_bridge_registry_contracts_and_chain_pairs():
    """FR-XCH-01: Verifies registry contains supported bridge definitions and addresses."""
    registry = BridgeRegistry()
    bridges = registry.list_bridges()
    bridge_ids = {b.bridge_id for b in bridges}

    assert "BRIDGE-DEMO-001" in bridge_ids
    assert "BRIDGE-STUB-001" in bridge_ids

    # Contract lookup test
    demo_adapter, role = registry.find_adapter_by_contract(
        "ethereum", "0x9999999999999999999999999999999999999998"
    )
    assert role == "source"
    assert demo_adapter.get_bridge_definition().bridge_id == "BRIDGE-DEMO-001"

    dest_adapter, role = registry.find_adapter_by_contract(
        "polygon", "0x8888888888888888888888888888888888888888"
    )
    assert role == "destination"
    assert dest_adapter.get_bridge_definition().bridge_id == "BRIDGE-DEMO-001"


def test_fr_xch_05_stub_adapter_extension_architecture():
    """FR-XCH-05: Proves that adding a new bridge requires zero changes to core engine."""
    registry = BridgeRegistry()
    stub_adapter = registry.get_adapter("BRIDGE-STUB-001")
    assert stub_adapter is not None

    b_def = stub_adapter.get_bridge_definition()
    assert b_def.source_chain == "ethereum"
    assert b_def.destination_chain == "bnb_chain"

    # Match test using stub adapter directly
    src = {"amount": 100, "timestamp": datetime.now(UTC)}
    cand = [{"transaction_hash": "0xstub_dest_tx", "destination": "0xdest_user", "amount": 99.9, "timestamp": datetime.now(UTC)}]
    res = stub_adapter.match(src, cand)
    assert res.is_matched is True
    assert res.confidence >= 0.90
    assert res.destination_tx_hash == "0xstub_dest_tx"


# -----------------------------------------------------------------------------
# 2. Source <-> Destination Matching and Ambiguity (FR-XCH-03, CAP-05)
# -----------------------------------------------------------------------------


def test_cross_chain_matcher_exact_and_heuristic_matching():
    """FR-XCH-03: Tests exact transfer ID matching and amount-tolerance heuristic matching."""
    adapter = DemoBridgeAdapter()
    t0 = datetime(2026, 10, 1, 14, 0, tzinfo=UTC)

    src = {
        "amount": Decimal("10.0"),
        "timestamp": t0,
        "bridge_tx_id": "BTX-12345",
    }

    # Case A: Exact bridge_tx_id match -> Confidence 0.98
    cand_exact = [
        {
            "transaction_hash": "0xdest_tx_1",
            "destination": "0xuser_dest",
            "amount": Decimal("9.98"),
            "timestamp": t0 + timedelta(minutes=5),
            "bridge_tx_id": "BTX-12345",
        }
    ]
    res_exact = adapter.match(src, cand_exact)
    assert res_exact.is_matched is True
    assert res_exact.confidence == 0.98
    assert res_exact.is_ambiguous is False

    # Case B: Amount & Timing matching (no explicit bridge ID) -> Confidence 0.88
    src_no_id = {
        "amount": Decimal("10.0"),
        "timestamp": t0,
        "bridge_tx_id": None,
    }
    cand_heuristic = [
        {
            "transaction_hash": "0xdest_tx_2",
            "destination": "0xuser_dest",
            "amount": Decimal("9.98"),
            "timestamp": t0 + timedelta(minutes=10),
            "bridge_tx_id": None,
        }
    ]
    res_heuristic = adapter.match(src_no_id, cand_heuristic)
    assert res_heuristic.is_matched is True
    assert res_heuristic.confidence == 0.88
    assert res_heuristic.is_ambiguous is False

    # Case C: Ambiguous matches (>1 plausible candidate) -> Confidence < 0.80 and is_ambiguous = True
    cand_ambiguous = [
        {
            "transaction_hash": "0xdest_tx_3a",
            "destination": "0xuser_dest_a",
            "amount": Decimal("9.98"),
            "timestamp": t0 + timedelta(minutes=8),
            "bridge_tx_id": None,
        },
        {
            "transaction_hash": "0xdest_tx_3b",
            "destination": "0xuser_dest_b",
            "amount": Decimal("9.98"),
            "timestamp": t0 + timedelta(minutes=12),
            "bridge_tx_id": None,
        },
    ]
    res_ambiguous = adapter.match(src_no_id, cand_ambiguous)
    assert res_ambiguous.is_matched is True
    assert res_ambiguous.confidence < 0.80
    assert res_ambiguous.is_ambiguous is True
    assert len(res_ambiguous.alternatives) == 2

    # Verify CAP-05 trigger on ambiguous match
    triggered, max_allowed, _ = cap_05_ambiguous_cross_chain(
        is_cross_chain_ambiguous=True,
        cross_chain_confidence=res_ambiguous.confidence,
    )
    assert triggered is True
    assert max_allowed == 0.65

    capped_score, caps_applied, _ = evaluate_caps(
        raw_score=0.82,
        context={
            "is_cross_chain_ambiguous": True,
            "cross_chain_confidence": res_ambiguous.confidence,
        },
    )
    assert capped_score == 0.65
    assert any(c.cap_code == "CAP-05" for c in caps_applied)


# -----------------------------------------------------------------------------
# 3. Case 5 Acceptance Oracle: Bridge Then Deposit (FR-XCH-02, FR-XCH-04)
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_case_5_cross_chain_bridge_then_deposit(db_session: AsyncSession, seeded_entities):
    """Case 5 Acceptance Oracle:

    Address bridges funds from Ethereum to Polygon, funds reach Kraken deposit on Polygon.
    Case 5 must produce exactly 1 CrossChainEvent and downstream VASP gets cross_chain_evidence factor.
    """
    inv_user = seeded_entities["users"]["INV"]
    case = Case(
        reference_number="CASE5-DEMO-01",
        title="Case 5: Cross-Chain Bridge Then Deposit",
        org_id=inv_user.org_id,
        owner_id=inv_user.id,
    )
    db_session.add(case)
    await db_session.flush()

    inv = Investigation(
        case_id=case.id,
        wallet_address="0x1111111111111111111111111111111111111111",
        blockchain="ethereum",
        depth=3,
    )
    db_session.add(inv)
    await db_session.flush()

    # Seed destination VASP on Polygon
    vasp = Vasp(vasp_id="VASP-KRAKEN", name="Kraken", jurisdiction="US")
    db_session.add(vasp)
    await db_session.flush()

    # 1. Seed Ethereum nodes & bridge deposit edge
    t0 = datetime(2026, 10, 1, 10, 0, tzinfo=UTC)
    n_seed = GraphNodeModel(
        investigation_id=inv.id,
        node_key="ethereum:0x1111111111111111111111111111111111111111",
        chain="ethereum",
        address="0x1111111111111111111111111111111111111111",
        node_type="wallet",
        hop=0,
    )
    # Bridge contract on Ethereum (Demo bridge source address)
    n_bridge = GraphNodeModel(
        investigation_id=inv.id,
        node_key="ethereum:0x9999999999999999999999999999999999999998",
        chain="ethereum",
        address="0x9999999999999999999999999999999999999998",
        node_type="bridge",
        address_type="bridge",
        label="Demo Bridge Contract",
        is_terminal=True,
        hop=1,
    )
    src_edge = GraphEdgeModel(
        id=uuid4(),
        investigation_id=inv.id,
        source_key="ethereum:0x1111111111111111111111111111111111111111",
        destination_key="ethereum:0x9999999999999999999999999999999999999998",
        chain="ethereum",
        edge_type="bridge_event",
        transaction_hash="0xsrc_tx_bridge_deposit_1234567890abcdef",
        block_number=19500000,
        timestamp=t0,
        asset="USDC",
        amount=Decimal("5000.00"),
        amount_raw="5000000000",
        usd_value=Decimal("5000.00"),
        traced_usd=Decimal("5000.00"),
        hop=1,
        provider="ethereum-fixture",
    )

    # 2. Seed Polygon destination payout node & edge into Kraken
    t1 = t0 + timedelta(minutes=15)
    dest_payout_addr = "0x2222222222222222222222222222222222222222"
    kraken_deposit_addr = "0x3333333333333333333333333333333333333333"

    n_dest = GraphNodeModel(
        investigation_id=inv.id,
        node_key=f"polygon:{dest_payout_addr}",
        chain="polygon",
        address=dest_payout_addr,
        node_type="wallet",
        hop=2,
    )
    n_kraken = GraphNodeModel(
        investigation_id=inv.id,
        node_key=f"polygon:{kraken_deposit_addr}",
        chain="polygon",
        address=kraken_deposit_addr,
        node_type="vasp",
        address_type="deposit_wallet",
        vasp_id="VASP-KRAKEN",
        label="Kraken Polygon Deposit",
        is_terminal=True,
        hop=3,
    )
    dest_edge = GraphEdgeModel(
        id=uuid4(),
        investigation_id=inv.id,
        source_key=f"polygon:{dest_payout_addr}",
        destination_key=f"polygon:{kraken_deposit_addr}",
        chain="polygon",
        edge_type="token_transfer",
        transaction_hash="0xdest_tx_kraken_payout_abcdef1234567890",
        block_number=45000000,
        timestamp=t1,
        asset="USDC",
        amount=Decimal("4990.00"),
        amount_raw="4990000000",
        usd_value=Decimal("4990.00"),
        traced_usd=Decimal("4990.00"),
        hop=3,
        provider="polygon-fixture",
    )

    db_session.add_all([n_seed, n_bridge, src_edge, n_dest, n_kraken, dest_edge])
    await db_session.commit()

    # 3. Run CrossChainEngine detection and matching
    evidence_engine = EvidenceEngine(db_session)
    xchain_engine = CrossChainEngine(db_session, evidence_engine=evidence_engine)

    candidates_map = {
        "0xsrc_tx_bridge_deposit_1234567890abcdef": [
            {
                "transaction_hash": "0xdest_tx_kraken_payout_abcdef1234567890",
                "destination": dest_payout_addr,
                "amount": Decimal("4990.00"),
                "timestamp": t1,
                "bridge_tx_id": "BTX-0xsrc_tx_b",
            }
        ]
    }

    events = await xchain_engine.detect_and_match(inv.id, candidate_dest_transfers_map=candidates_map)

    # Core Acceptance Oracle: Exactly 1 CrossChainEvent
    assert len(events) == 1
    ev = events[0]
    assert ev.bridge_id == "BRIDGE-DEMO-001"
    assert ev.source_chain == "ethereum"
    assert ev.destination_chain == "polygon"
    assert ev.confidence >= 0.85
    assert ev.status == "MATCHED"
    assert ev.is_ambiguous is False

    # Check FR-XCH-04: Destination edge tagged with via_cross_chain_event_id
    await db_session.refresh(dest_edge)
    assert dest_edge.via_cross_chain_event_id == str(ev.id)

    # 4. Run AttributionEngine and verify downstream VASP gets cross_chain_evidence factor
    attr_engine = AttributionEngine(db_session, evidence_engine=evidence_engine)
    attr_res = await attr_engine.run(inv.id)

    assert len(attr_res.candidates) == 1
    top = attr_res.top_candidate
    assert top is not None
    assert top.vasp_id == "VASP-KRAKEN"

    # Find cross_chain_evidence factor
    xchain_factor = next((f for f in top.factors if f.name == "cross_chain_evidence"), None)
    assert xchain_factor is not None
    assert xchain_factor.applicable is True
    assert xchain_factor.normalized_score >= 0.85
    assert xchain_factor.contribution > 0.0


# -----------------------------------------------------------------------------
# 4. Cross-Chain REST API Endpoints Tests
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cross_chain_api_endpoints(
    client: AsyncClient,
    db_session: AsyncSession,
    seeded_entities,
):
    """FR-XCH-01, FR-XCH-02: Tests bridges registry and cross-chain events REST endpoints."""
    inv_user = seeded_entities["users"]["INV"]
    headers = get_auth_headers(inv_user)

    # 1. List registered bridges
    bridges_res = await client.get("/api/v1/investigations/bridges/registry", headers=headers)
    assert bridges_res.status_code == 200
    bridges_data = bridges_res.json()
    assert len(bridges_data) >= 2
    bridge_ids = [b["bridge_id"] for b in bridges_data]
    assert "BRIDGE-DEMO-001" in bridge_ids

    # 2. Create case and investigation
    case_res = await client.post(
        "/api/v1/cases/",
        json={"reference_number": "API-XCH-01", "title": "Cross Chain API Case"},
        headers=headers,
    )
    case_id = case_res.json()["id"]

    inv_res = await client.post(
        f"/api/v1/investigations/cases/{case_id}",
        json={"wallet_address": "0x7777777777777777777777777777777777777777", "blockchain": "ethereum"},
        headers=headers,
    )
    inv_id = inv_res.json()["id"]

    # 3. Query cross-chain events (empty initially)
    events_res = await client.get(f"/api/v1/investigations/{inv_id}/cross-chain", headers=headers)
    assert events_res.status_code == 200
    assert len(events_res.json()) == 0

    # 4. Trigger detect endpoint
    detect_res = await client.post(f"/api/v1/investigations/{inv_id}/cross-chain/detect", headers=headers)
    assert detect_res.status_code == 200
    detect_data = detect_res.json()
    assert detect_data["investigation_id"] == inv_id
    assert "events_detected" in detect_data

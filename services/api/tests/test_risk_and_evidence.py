from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.attribution.engine import AttributionEngine
from app.core.security import create_access_token
from app.db.models import (
    Case,
    GraphEdgeModel,
    GraphNodeModel,
    Investigation,
    User,
    Vasp,
)
from app.domain.enums import (
    AddressType,
    EvidenceType,
    NodeType,
    ProvenanceClass,
    RiskSignalCode,
    RiskTier,
    UserRole,
)
from app.evidence.engine import EvidenceEngine
from app.risk.engine import RiskEngine
from app.risk.scoring import calculate_risk_score
from app.risk.signals import (
    detect_high_risk_counterparty,
    detect_high_value_transfers,
    detect_mixer_interaction,
    detect_peel_chain,
    detect_rapid_movement,
)


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
# 1. P0 Risk Signals Unit Tests (FR-RISK-01)
# -----------------------------------------------------------------------------


def test_detect_mixer_interaction_signal():
    """FR-RISK-01: Verifies detection of mixer contracts and service nodes."""
    seed = "0x1111111111111111111111111111111111111111"
    nodes = [
        {"address": seed, "node_type": "wallet", "address_type": "eoa", "label": None},
        {
            "address": "0x2222222222222222222222222222222222222222",
            "node_type": "service",
            "address_type": "mixer",
            "label": "Tornado.Cash: 100 ETH Pool",
        },
    ]
    edges = [
        {"source_key": f"ethereum:{seed}", "destination_key": "ethereum:0x2222", "amount": 100, "hop": 1}
    ]

    signal = detect_mixer_interaction(nodes, edges, seed)
    assert signal is not None
    assert signal.signal_code == RiskSignalCode.MIXER_INTERACTION.value
    assert signal.score == 30
    assert "Tornado.Cash" in signal.description


def test_detect_peel_chain_signal():
    """FR-RISK-01: Verifies detection of peel chain topologies where intermediate nodes split change."""
    seed = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    intermediary = "ethereum:0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    out1 = "ethereum:0xcccccccccccccccccccccccccccccccccccccccc"
    out2 = "ethereum:0xdddddddddddddddddddddddddddddddddddddddd"

    nodes = [
        {"address": seed, "node_type": "wallet", "address_type": "eoa", "label": None},
        {"address": "0xbbbb", "node_type": "wallet", "address_type": "eoa", "label": None},
        {"address": "0xcccc", "node_type": "wallet", "address_type": "eoa", "label": None},
        {"address": "0xdddd", "node_type": "wallet", "address_type": "eoa", "label": None},
    ]
    edges = [
        {"source_key": f"ethereum:{seed}", "destination_key": intermediary, "amount": 100, "usd_value": 200000, "hop": 1},
        {"source_key": intermediary, "destination_key": out1, "amount": 90, "usd_value": 180000, "hop": 2},
        {"source_key": intermediary, "destination_key": out2, "amount": 10, "usd_value": 20000, "hop": 2},
    ]

    signal = detect_peel_chain(nodes, edges, seed)
    assert signal is not None
    assert signal.signal_code == RiskSignalCode.PEEL_CHAIN.value
    assert signal.score == 24


def test_detect_rapid_movement_signal():
    """FR-RISK-01: Verifies detection of rapid automated movement (< 15 min between hops)."""
    t0 = datetime(2026, 10, 1, 10, 0, 0, tzinfo=UTC)
    t1 = t0 + timedelta(seconds=120)  # 2 minutes later (< 15 min threshold)

    edges = [
        {
            "id": "e1",
            "source_key": "ethereum:0x1111",
            "destination_key": "ethereum:0x2222",
            "timestamp": t0,
            "hop": 1,
        },
        {
            "id": "e2",
            "source_key": "ethereum:0x2222",
            "destination_key": "ethereum:0x3333",
            "timestamp": t1,
            "hop": 2,
        },
    ]

    signal = detect_rapid_movement(edges, threshold_seconds=900)
    assert signal is not None
    assert signal.signal_code == RiskSignalCode.RAPID_MOVEMENT.value
    assert signal.score == 18
    assert signal.metadata["min_interval_seconds"] == 120


def test_detect_high_value_transfers_signal():
    """FR-RISK-01: Verifies detection of high value transfers (>= $10,000 USD)."""
    edges = [
        {"usd_value": Decimal("500.00")},
        {"usd_value": Decimal("25000.00")},  # exceeds 10k threshold
    ]
    signal = detect_high_value_transfers(edges)
    assert signal is not None
    assert signal.signal_code == RiskSignalCode.HIGH_VALUE_TRANSFERS.value
    assert signal.score == 10


def test_detect_high_risk_counterparty_signal():
    """FR-RISK-01: Verifies detection of flagged illicit/sanctioned counterparties."""
    seed = "0x1111111111111111111111111111111111111111"
    nodes = [
        {"address": seed, "label": "Seed"},
        {"address": "0x3333", "label": "OFAC Sanctioned Hacker Wallet", "address_type": "sanctioned"},
    ]
    signal = detect_high_risk_counterparty(nodes, seed)
    assert signal is not None
    assert signal.signal_code == RiskSignalCode.HIGH_RISK_COUNTERPARTY.value
    assert signal.score == 25


# -----------------------------------------------------------------------------
# 2. Case 4 Score & Tier Acceptance Oracle (FR-RISK-02)
# -----------------------------------------------------------------------------


def test_case_4_exact_risk_score_and_tier():
    """FR-RISK-02 & PRD acceptance oracle: Case 4 must produce risk score 72 and HIGH tier.

    Case 4 combines:
    - Mixer interaction: 30 pts
    - Peel chain topology: 24 pts
    - Rapid movement: 18 pts
    Total = 72 / HIGH.
    """
    signals = [
        detect_mixer_interaction(
            nodes=[
                {"address": "0xseed", "node_type": "wallet", "address_type": "eoa", "label": None},
                {"address": "0xmixer", "node_type": "service", "address_type": "mixer", "label": "Tornado Cash"},
            ],
            edges=[],
            seed_address="0xseed",
        ),
        detect_peel_chain(
            nodes=[],
            edges=[
                {"hop": 1, "source_key": "ethereum:0xseed", "destination_key": "ethereum:0xmid", "usd_value": 100000},
                {"hop": 2, "source_key": "ethereum:0xmid", "destination_key": "ethereum:0xout1", "usd_value": 85000},
                {"hop": 2, "source_key": "ethereum:0xmid", "destination_key": "ethereum:0xout2", "usd_value": 15000},
            ],
            seed_address="0xseed",
        ),
        detect_rapid_movement(
            edges=[
                {
                    "source_key": "ethereum:0xseed",
                    "destination_key": "ethereum:0xmid",
                    "timestamp": datetime(2026, 10, 1, 12, 0, tzinfo=UTC),
                    "hop": 1,
                },
                {
                    "source_key": "ethereum:0xmid",
                    "destination_key": "ethereum:0xout1",
                    "timestamp": datetime(2026, 10, 1, 12, 5, tzinfo=UTC),
                    "hop": 2,
                },
            ]
        ),
    ]

    active_signals = [s for s in signals if s is not None]
    assert len(active_signals) == 3

    score, tier, summary = calculate_risk_score(active_signals)

    # Core PRD requirement: Exactly 72 / HIGH
    assert score == 72
    assert tier == RiskTier.HIGH
    assert "72/100" in summary
    assert "HIGH" in summary


# -----------------------------------------------------------------------------
# 3. FR-RISK-04 VASP Nodes Carry NO Risk Score
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fr_risk_04_vasp_nodes_carry_no_risk_score(db_session: AsyncSession, seeded_entities):
    """FR-RISK-04: Rule that VASP nodes never carry a risk score or illicit label."""
    inv_user = seeded_entities["users"]["INV"]
    case = Case(
        reference_number="RISK-VASP-RULE-01",
        title="VASP Risk Invariant Case",
        org_id=inv_user.org_id,
        owner_id=inv_user.id,
    )
    db_session.add(case)
    await db_session.flush()

    inv = Investigation(
        case_id=case.id,
        wallet_address="0x1111111111111111111111111111111111111111",
        blockchain="ethereum",
        depth=2,
    )
    db_session.add(inv)
    await db_session.flush()

    # Seed intermediate node and a terminal VASP node
    node_seed = GraphNodeModel(
        investigation_id=inv.id,
        node_key="ethereum:0x1111111111111111111111111111111111111111",
        chain="ethereum",
        address="0x1111111111111111111111111111111111111111",
        node_type="wallet",
        hop=0,
    )
    node_vasp = GraphNodeModel(
        investigation_id=inv.id,
        node_key="ethereum:0x9999999999999999999999999999999999999999",
        chain="ethereum",
        address="0x9999999999999999999999999999999999999999",
        node_type=NodeType.VASP.value,
        address_type=AddressType.DEPOSIT.value,
        vasp_id="VASP-KRAKEN",
        label="Kraken Deposit",
        is_terminal=True,
        hop=1,
    )
    db_session.add_all([node_seed, node_vasp])
    await db_session.commit()

    risk_engine = RiskEngine(db_session)
    result = await risk_engine.run(inv.id)

    # Risk result must apply to target wallet address, never Kraken
    assert result.target_address == "0x1111111111111111111111111111111111111111"
    # Verify no signal flags Kraken VASP as illicit
    for sig in result.signals:
        assert "Kraken" not in sig.name
        assert "VASP-KRAKEN" not in str(sig.metadata)


# -----------------------------------------------------------------------------
# 4. AT-12 Independence Invariant Test (FR-RISK-03)
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_at12_risk_attribution_strict_independence(db_session: AsyncSession, seeded_entities):
    """FR-RISK-03 / AT-12: Verifies that changing risk signals or running risk scoring

    produces zero change in attribution scores, ranks, and factors.
    """
    inv_user = seeded_entities["users"]["INV"]
    case = Case(
        reference_number="AT12-INDEP-01",
        title="AT-12 Independence Case",
        org_id=inv_user.org_id,
        owner_id=inv_user.id,
    )
    db_session.add(case)
    await db_session.flush()

    inv = Investigation(
        case_id=case.id,
        wallet_address="0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        blockchain="ethereum",
        depth=2,
    )
    db_session.add(inv)
    await db_session.flush()

    # Seed VASP
    vasp = Vasp(vasp_id="VASP-COINBASE", name="Coinbase", jurisdiction="US")
    db_session.add(vasp)
    await db_session.flush()

    # Seed nodes and edge
    n_seed = GraphNodeModel(
        investigation_id=inv.id,
        node_key="ethereum:0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        chain="ethereum",
        address="0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        node_type="wallet",
        hop=0,
    )
    n_cb = GraphNodeModel(
        investigation_id=inv.id,
        node_key="ethereum:0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        chain="ethereum",
        address="0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        node_type="vasp",
        address_type="deposit_wallet",
        vasp_id="VASP-COINBASE",
        label="Coinbase Deposit",
        is_terminal=True,
        hop=1,
    )
    edge = GraphEdgeModel(
        id=uuid4(),
        investigation_id=inv.id,
        source_key="ethereum:0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        destination_key="ethereum:0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        chain="ethereum",
        edge_type="native_transfer",
        transaction_hash="0x1111222233334444555566667777888899990000111122223333444455556666",
        block_number=18000000,
        timestamp=datetime.now(UTC),
        asset="ETH",
        amount=Decimal("5.0"),
        amount_raw="5000000000000000000",
        usd_value=Decimal("15000.00"),
        traced_usd=Decimal("15000.00"),
        hop=1,
        provider="ethereum-fixture",
    )
    db_session.add_all([n_seed, n_cb, edge])
    await db_session.commit()

    # Run Attribution baseline
    evidence_engine = EvidenceEngine(db_session)
    attr_engine = AttributionEngine(db_session, evidence_engine=evidence_engine)
    attr_baseline = await attr_engine.run(inv.id)
    baseline_score = attr_baseline.top_candidate.final_score
    baseline_rank = attr_baseline.top_candidate.rank

    # Now run Risk Engine (which inserts risk assessment and risk evidence)
    risk_engine = RiskEngine(db_session, evidence_engine=evidence_engine)
    risk_res = await risk_engine.run(inv.id)
    assert risk_res.overall_score >= 0

    # Rerun attribution; assert mathematical invariance
    attr_after_risk = await attr_engine.run(inv.id)
    assert attr_after_risk.top_candidate.final_score == baseline_score
    assert attr_after_risk.top_candidate.rank == baseline_rank


# -----------------------------------------------------------------------------
# 5. FR-EVD-01 Invariant: Every Attribution Result Links >= 1 Evidence Row
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fr_evd_01_attribution_links_at_least_one_evidence(db_session: AsyncSession, seeded_entities):
    """FR-EVD-01: Verifies that every candidate in attribution_results links to at least 1 evidence record in the DB."""
    inv_user = seeded_entities["users"]["INV"]
    case = Case(
        reference_number="EVD01-CASE-01",
        title="Evidence Gate Invariant Case",
        org_id=inv_user.org_id,
        owner_id=inv_user.id,
    )
    db_session.add(case)
    await db_session.flush()

    inv = Investigation(
        case_id=case.id,
        wallet_address="0xcccccccccccccccccccccccccccccccccccccccc",
        blockchain="ethereum",
        depth=1,
    )
    db_session.add(inv)
    await db_session.flush()

    vasp = Vasp(vasp_id="VASP-BINANCE", name="Binance", jurisdiction="MT")
    db_session.add(vasp)
    await db_session.flush()

    n_seed = GraphNodeModel(
        investigation_id=inv.id,
        node_key="ethereum:0xcccccccccccccccccccccccccccccccccccccccc",
        chain="ethereum",
        address="0xcccccccccccccccccccccccccccccccccccccccc",
        node_type="wallet",
        hop=0,
    )
    n_dest = GraphNodeModel(
        investigation_id=inv.id,
        node_key="ethereum:0xdddddddddddddddddddddddddddddddddddddddd",
        chain="ethereum",
        address="0xdddddddddddddddddddddddddddddddddddddddd",
        node_type="vasp",
        address_type="deposit_wallet",
        vasp_id="VASP-BINANCE",
        label="Binance Deposit",
        is_terminal=True,
        hop=1,
    )
    edge = GraphEdgeModel(
        id=uuid4(),
        investigation_id=inv.id,
        source_key="ethereum:0xcccccccccccccccccccccccccccccccccccccccc",
        destination_key="ethereum:0xdddddddddddddddddddddddddddddddddddddddd",
        chain="ethereum",
        edge_type="native_transfer",
        transaction_hash="0xabcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234",
        block_number=19000000,
        timestamp=datetime.now(UTC),
        asset="ETH",
        amount=Decimal("10.0"),
        amount_raw="10000000000000000000",
        usd_value=Decimal("30000.00"),
        traced_usd=Decimal("30000.00"),
        hop=1,
        provider="ethereum-fixture",
    )
    db_session.add_all([n_seed, n_dest, edge])
    await db_session.commit()

    evidence_engine = EvidenceEngine(db_session)
    attr_engine = AttributionEngine(db_session, evidence_engine=evidence_engine)
    attr_res = await attr_engine.run(inv.id)

    assert len(attr_res.candidates) >= 1
    for cand in attr_res.candidates:
        assert len(cand.evidence_references) >= 1, "Invariant FR-EVD-01: Candidate must link >= 1 evidence"
        # Check that the referenced evidence exists in the evidence table
        ev_id = UUID(cand.evidence_references[0])
        ev_record = await evidence_engine.get_evidence_by_id(inv.id, ev_id)
        assert ev_record is not None
        assert ev_record.provenance_class == ProvenanceClass.THIRD_PARTY_INTELLIGENCE.value


# -----------------------------------------------------------------------------
# 6. FR-EVD-02 Immutability & SHA-256 Hash Chain Verification
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fr_evd_02_evidence_hash_chain_and_tamper_detection(db_session: AsyncSession, seeded_entities):
    """FR-EVD-02: Verifies that evidence records form a valid hash chain and tampering is detected."""
    inv_user = seeded_entities["users"]["INV"]
    case = Case(
        reference_number="EVD02-CASE-01",
        title="Hash Chain Integrity Case",
        org_id=inv_user.org_id,
        owner_id=inv_user.id,
    )
    db_session.add(case)
    await db_session.flush()

    inv = Investigation(
        case_id=case.id,
        wallet_address="0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        blockchain="ethereum",
        depth=1,
    )
    db_session.add(inv)
    await db_session.flush()

    engine = EvidenceEngine(db_session)

    # 1. Add 3 sequential evidence records
    ev1 = await engine.add_evidence(
        investigation_id=inv.id,
        evidence_type=EvidenceType.DIRECT_TRANSFER,
        provenance_class=ProvenanceClass.OBSERVED,
        source="provider:fixture",
        source_ref="tx:0x1",
        data_payload={"tx": "0x1", "amount": 100},
    )
    ev2 = await engine.add_evidence(
        investigation_id=inv.id,
        evidence_type=EvidenceType.REGISTRY_ENTRY,
        provenance_class=ProvenanceClass.THIRD_PARTY_INTELLIGENCE,
        source="local_registry",
        source_ref="vasp:VASP-001",
        data_payload={"vasp_id": "VASP-001"},
    )
    ev3 = await engine.add_evidence(
        investigation_id=inv.id,
        evidence_type=EvidenceType.RISK_SIGNAL,
        provenance_class=ProvenanceClass.DERIVED,
        source="engine:risk",
        source_ref="signal:mixer",
        data_payload={"signal": "mixer_interaction", "score": 30},
        derived_from=[str(ev1.id)],
    )

    # 2. Verify hash chain is valid
    verify_res = await engine.verify_chain(inv.id)
    assert verify_res.is_valid is True
    assert verify_res.total_records == 3
    assert verify_res.latest_evidence_hash == ev3.evidence_hash

    # 3. Simulate tampering: alter ev2 payload raw_hash
    ev2.raw_hash = "tampered_hash_value_1234567890abcdef"
    await db_session.flush()

    tamper_res = await engine.verify_chain(inv.id)
    assert tamper_res.is_valid is False
    assert "tampering detected" in tamper_res.error_message.lower()


# -----------------------------------------------------------------------------
# 7. FR-EVD-03 & FR-EVD-04: API Endpoints (Ledger Filters & Edge Evidence)
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evidence_and_risk_api_endpoints(
    client: AsyncClient,
    db_session: AsyncSession,
    seeded_entities,
):
    """FR-EVD-03, FR-EVD-04, FR-RISK-01..02: Tests REST endpoints for evidence ledger,

    verification, edge-to-evidence queries, notes, and risk assessment.
    """
    inv_user = seeded_entities["users"]["INV"]
    headers = get_auth_headers(inv_user)

    # 1. Create Case and Investigation
    case_res = await client.post(
        "/api/v1/cases/",
        json={"reference_number": "API-EVD-01", "title": "Evidence API Case"},
        headers=headers,
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    inv_res = await client.post(
        f"/api/v1/investigations/cases/{case_id}",
        json={"wallet_address": "0x5555555555555555555555555555555555555555", "blockchain": "ethereum"},
        headers=headers,
    )
    assert inv_res.status_code == 201
    inv_id = inv_res.json()["id"]

    # 2. Add an analyst note (FR-EVD-02, append-only INFERENCE)
    note_res = await client.post(
        f"/api/v1/investigations/{inv_id}/evidence/notes",
        json={"note": "Investigator observed counterparty linked to known darknet market in local records."},
        headers=headers,
    )
    assert note_res.status_code == 201
    note_data = note_res.json()
    assert note_data["provenance_class"] == "INFERENCE"
    assert note_data["evidence_type"] == "analyst_note"
    note_id = note_data["id"]

    # 3. Verify hash chain via API (FR-EVD-02)
    verify_res = await client.get(
        f"/api/v1/investigations/{inv_id}/evidence/verify",
        headers=headers,
    )
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["is_valid"] is True
    assert verify_data["total_records"] == 1

    # 4. List evidence with provenance filter (FR-EVD-03)
    filter_res = await client.get(
        f"/api/v1/investigations/{inv_id}/evidence?provenance_class=INFERENCE",
        headers=headers,
    )
    assert filter_res.status_code == 200
    items = filter_res.json()
    assert len(items) == 1
    assert items[0]["id"] == note_id

    # Filter with non-matching provenance
    empty_res = await client.get(
        f"/api/v1/investigations/{inv_id}/evidence?provenance_class=OBSERVED",
        headers=headers,
    )
    assert empty_res.status_code == 200
    assert len(empty_res.json()) == 0

    # 5. Get detail of single evidence record
    detail_res = await client.get(
        f"/api/v1/investigations/{inv_id}/evidence/{note_id}",
        headers=headers,
    )
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == note_id

    # 6. Execute Risk Run via API (FR-RISK-01..02)
    risk_run_res = await client.post(
        f"/api/v1/investigations/{inv_id}/risk/run",
        headers=headers,
    )
    assert risk_run_res.status_code == 200
    risk_run_data = risk_run_res.json()
    assert "overall_score" in risk_run_data
    assert "tier" in risk_run_data

    # 7. Get Risk Assessment via API
    risk_get_res = await client.get(
        f"/api/v1/investigations/{inv_id}/risk",
        headers=headers,
    )
    assert risk_get_res.status_code == 200
    assert risk_get_res.json()["overall_score"] == risk_run_data["overall_score"]

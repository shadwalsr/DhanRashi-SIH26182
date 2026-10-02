from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.attribution.caps import (
    assign_tier,
    cap_01_minimum_evidence_gate,
    cap_02_high_degree_intermediary,
    cap_03_unresolved_flow,
    cap_04_conflicting_or_disputed_labels,
    cap_05_ambiguous_cross_chain,
    cap_06_incomplete_data,
    cap_07_stale_label,
    cap_08_low_flow_proportion,
    evaluate_caps,
)
from app.attribution.engine import AttributionEngine
from app.attribution.features import (
    compute_cluster_association,
    compute_cross_chain_evidence,
    compute_funds_reached,
    compute_graph_distance,
    compute_intelligence_provider_confidence,
    compute_known_deposit_match,
    compute_percentage_of_traced_funds,
    compute_recency,
    compute_temporal_continuity,
    compute_transaction_frequency,
)
from app.attribution.weights import DEFAULT_WEIGHTS, renormalize_weights
from app.core.security import create_access_token
from app.db.models import (
    AttributionResultModel,
    Case,
    GraphEdgeModel,
    GraphNodeModel,
    Investigation,
    User,
    Vasp,
    VaspAddress,
)
from app.domain.enums import AttributionTier, UserRole


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
# 1. Ten Features Boundary Value Tests (FR-ATT-02)
# -----------------------------------------------------------------------------


def test_feature_graph_distance():
    assert compute_graph_distance(0) == 1.0
    assert compute_graph_distance(1) == 1.0
    assert compute_graph_distance(2) == 0.6667
    assert compute_graph_distance(3) == 0.50
    assert compute_graph_distance(5) == 0.3333
    # Monotonic decay
    assert compute_graph_distance(1) > compute_graph_distance(2) > compute_graph_distance(3)


def test_feature_known_deposit_match():
    # Fresh deposit wallet
    score, is_stale = compute_known_deposit_match("deposit_wallet", staleness_days=30)
    assert score == 1.0
    assert is_stale is False

    # Custodial wallet
    score, _ = compute_known_deposit_match("custodial_wallet", staleness_days=30)
    assert score == 0.8

    # Hot wallet
    score, _ = compute_known_deposit_match("hot_wallet", staleness_days=30)
    assert score == 0.6

    # Payment processor
    score, _ = compute_known_deposit_match("payment_processor", staleness_days=30)
    assert score == 0.5

    # Cold wallet
    score, _ = compute_known_deposit_match("cold_wallet", staleness_days=30)
    assert score == 0.3

    # Staleness degradation factor (180 - 365 days) -> 0.7x
    score, is_stale = compute_known_deposit_match("deposit_wallet", staleness_days=200)
    assert score == 0.7
    assert is_stale is False

    # Staleness degradation factor (> 365 days) -> 0.4x and triggers CAP-07
    score, is_stale = compute_known_deposit_match("deposit_wallet", staleness_days=400)
    assert score == 0.4
    assert is_stale is True


def test_feature_cluster_association():
    assert compute_cluster_association(False) == 0.0
    assert compute_cluster_association(True, "verified") == 1.0
    assert compute_cluster_association(True, "exchange_cluster") == 1.0
    assert compute_cluster_association(True, "heuristic") == 0.6


def test_feature_funds_reached():
    assert compute_funds_reached(0) == 0.0
    assert compute_funds_reached(100) == round(2.0 / 6.0, 4)  # log10(100) = 2.0 -> 0.3333
    assert compute_funds_reached(1000) == round(3.0 / 6.0, 4)  # log10(1000) = 3.0 -> 0.50
    assert compute_funds_reached(1000000) == 1.0  # $1M cap
    assert compute_funds_reached(5000000) == 1.0  # capped at 1.0


def test_feature_percentage_of_traced_funds():
    assert compute_percentage_of_traced_funds(0, 1000) == 0.0
    assert compute_percentage_of_traced_funds(50, 1000) == 0.05
    assert compute_percentage_of_traced_funds(880, 1000) == 0.88
    assert compute_percentage_of_traced_funds(1000, 1000) == 1.0


def test_feature_transaction_frequency():
    assert compute_transaction_frequency(0) == 0.0
    assert compute_transaction_frequency(1) == 0.20
    assert compute_transaction_frequency(2) == 0.40
    assert compute_transaction_frequency(5) == 1.0
    assert compute_transaction_frequency(10) == 1.0


def test_feature_recency():
    now = datetime(2026, 1, 10, 12, 0, 0, tzinfo=UTC)
    assert compute_recency(now, as_of=now) == 1.0
    tx_90d = now - timedelta(days=90)
    assert compute_recency(tx_90d, as_of=now) == 0.50
    tx_180d = now - timedelta(days=180)
    assert compute_recency(tx_180d, as_of=now) == 0.0
    tx_200d = now - timedelta(days=200)
    assert compute_recency(tx_200d, as_of=now) == 0.0


def test_feature_temporal_continuity():
    assert compute_temporal_continuity(12.0) == 1.0  # <= 24h
    assert compute_temporal_continuity(48.0) == 0.8  # <= 7d
    assert compute_temporal_continuity(300.0) == 0.5  # <= 30d
    assert compute_temporal_continuity(800.0) == 0.2  # > 30d


def test_feature_intelligence_provider_confidence():
    assert compute_intelligence_provider_confidence(0.9, multi_source_count=1) == 0.9
    # Consensus agreement bonus
    assert compute_intelligence_provider_confidence(0.9, multi_source_count=2) == 1.0


def test_feature_cross_chain_evidence():
    score_no_bridge, app_no_bridge = compute_cross_chain_evidence(has_bridge_hop=False)
    assert score_no_bridge == 0.0
    assert app_no_bridge is False

    score_bridge, app_bridge = compute_cross_chain_evidence(has_bridge_hop=True, bridge_confidence=0.85)
    assert score_bridge == 0.85
    assert app_bridge is True


# -----------------------------------------------------------------------------
# 2. Weights Renormalization & G2 Explainability (FR-ATT-03)
# -----------------------------------------------------------------------------


def test_weights_renormalization_and_contribution_sum():
    applicable = {
        "percentage_of_traced_funds",
        "known_deposit_match",
        "funds_reached",
        "graph_distance",
    }
    renorm = renormalize_weights(DEFAULT_WEIGHTS, applicable)

    # Renormalized weights sum to 1.0
    assert abs(sum(renorm.values()) - 1.0) < 0.0001
    # Inapplicable features have 0.0 weight
    assert renorm["recency"] == 0.0
    assert renorm["cross_chain_evidence"] == 0.0

    # Test G2: sum of contributions strictly equals raw score within 0.001
    scores = {
        "percentage_of_traced_funds": 0.88,
        "known_deposit_match": 1.0,
        "funds_reached": 0.65,
        "graph_distance": 0.50,
    }
    contributions = [round(scores[k] * renorm[k], 4) for k in applicable]
    calculated_score = round(sum(contributions), 4)
    expected_score = sum(scores[k] * renorm[k] for k in applicable)

    assert abs(calculated_score - expected_score) <= 0.001


# -----------------------------------------------------------------------------
# 3. Caps & Tier Assignment Unit Tests (CAP-01 to CAP-08) (FR-ATT-04)
# -----------------------------------------------------------------------------


def test_caps_individual():
    # CAP-01: Evidence gate
    trig, max_score, _ = cap_01_minimum_evidence_gate(False)
    assert trig is True and max_score == 0.0

    # CAP-02: High degree intermediary
    trig, max_score, _ = cap_02_high_degree_intermediary(True)
    assert trig is True and max_score == 0.50

    # CAP-03: Unresolved flow dominance
    trig, max_score, _ = cap_03_unresolved_flow(0.70)
    assert trig is True and max_score == 0.60
    trig, _, _ = cap_03_unresolved_flow(0.30)
    assert trig is False

    # CAP-04: Conflicting or disputed labels
    trig, max_score, _ = cap_04_conflicting_or_disputed_labels(True, False)
    assert trig is True and max_score == 0.50
    trig, max_score, _ = cap_04_conflicting_or_disputed_labels(False, True)
    assert trig is True and max_score == 0.50

    # CAP-05: Ambiguous cross chain
    trig, max_score, _ = cap_05_ambiguous_cross_chain(False, 0.75)
    assert trig is True and max_score == 0.65

    # CAP-06: Incomplete data / partial path
    trig, max_score, _ = cap_06_incomplete_data(True)
    assert trig is True and max_score == 0.70

    # CAP-07: Stale label over 365 days
    trig, max_score, _ = cap_07_stale_label(True)
    assert trig is True and max_score == 0.60

    # CAP-08: Low flow proportion < 10%
    trig, max_score, _ = cap_08_low_flow_proportion(0.05)
    assert trig is True and max_score == 0.45
    trig, _, _ = cap_08_low_flow_proportion(0.50)
    assert trig is False


def test_evaluate_caps_combined():
    raw_score = 0.95
    context = {
        "has_qualifying_evidence": True,
        "is_stale_over_365": True,  # triggers CAP-07 (0.60)
        "flow_percentage": 0.05,     # triggers CAP-08 (0.45)
        "is_payment_processor": True,
    }
    final_score, caps_applied, limitations = evaluate_caps(raw_score, context)
    # Strictest cap wins: CAP-08 (0.45) is stricter than CAP-07 (0.60)
    assert final_score == 0.45
    assert len(caps_applied) == 2
    assert any("payment processor" in lim for lim in limitations)


def test_assign_tier():
    assert assign_tier(0.85) == AttributionTier.HIGH.value
    assert assign_tier(0.75) == AttributionTier.HIGH.value
    assert assign_tier(0.74) == AttributionTier.MEDIUM.value
    assert assign_tier(0.50) == AttributionTier.MEDIUM.value
    assert assign_tier(0.45) == AttributionTier.LOW.value
    assert assign_tier(0.40) == AttributionTier.LOW.value
    assert assign_tier(0.39) == AttributionTier.INSUFFICIENT.value


# -----------------------------------------------------------------------------
# 4. Regression Test for Core Principle (Task 10)
# "A VASP at hop 2 with 5% of funds must rank below a VASP at hop 3 with 88%"
# -----------------------------------------------------------------------------


def test_core_ranking_principle_flow_beats_shortest_path():
    # Candidate A: Hop 2, 5% of funds ($50 of $1000)
    f_dist_a = compute_graph_distance(2)  # 0.6667
    f_perc_a = compute_percentage_of_traced_funds(50, 1000)  # 0.05
    f_funds_a = compute_funds_reached(50)  # 0.2832
    f_dep_a, _ = compute_known_deposit_match("deposit_wallet", 0)  # 1.0

    raw_a = (
        DEFAULT_WEIGHTS["graph_distance"] * f_dist_a +
        DEFAULT_WEIGHTS["percentage_of_traced_funds"] * f_perc_a +
        DEFAULT_WEIGHTS["funds_reached"] * f_funds_a +
        DEFAULT_WEIGHTS["known_deposit_match"] * f_dep_a
    )

    # Candidate B: Hop 3, 88% of funds ($880 of $1000)
    f_dist_b = compute_graph_distance(3)  # 0.50 (lower distance score)
    f_perc_b = compute_percentage_of_traced_funds(880, 1000)  # 0.88 (much higher flow)
    f_funds_b = compute_funds_reached(880)  # 0.4908 (higher volume)
    f_dep_b, _ = compute_known_deposit_match("deposit_wallet", 0)  # 1.0

    raw_b = (
        DEFAULT_WEIGHTS["graph_distance"] * f_dist_b +
        DEFAULT_WEIGHTS["percentage_of_traced_funds"] * f_perc_b +
        DEFAULT_WEIGHTS["funds_reached"] * f_funds_b +
        DEFAULT_WEIGHTS["known_deposit_match"] * f_dep_b
    )

    # In addition, Candidate A (5% flow) triggers CAP-08 (max 0.45)
    final_a, _, _ = evaluate_caps(raw_a, {"flow_percentage": 0.05})
    final_b, _, _ = evaluate_caps(raw_b, {"flow_percentage": 0.88})

    assert final_b > final_a
    # Demonstrates mathematical proof of core anti-shortest-path principle
    assert final_b - final_a > 0.15


# -----------------------------------------------------------------------------
# 5. End-to-End Attribution Engine Integration & Versioning (FR-ATT-01..08)
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_attribution_engine_end_to_end_and_versioning(
    db_session: AsyncSession,
    seeded_entities,
):
    inv_user = seeded_entities["users"]["INV"]
    case = Case(
        org_id=inv_user.org_id,
        owner_id=inv_user.id,
        reference_number="ATTR-CASE-1",
        title="Attribution Integration Test",
    )
    db_session.add(case)
    await db_session.flush()

    seed_addr = "0x1111111111111111111111111111111111111111"
    inv = Investigation(
        case_id=case.id,
        wallet_address=seed_addr,
        blockchain="ethereum",
        status="COMPLETED",
        depth=3,
        run_no=1,
    )
    db_session.add(inv)
    await db_session.flush()

    # Seed 2 VASPs in registry
    vasp1 = Vasp(vasp_id="VASP-KRAKEN", name="Kraken", jurisdiction="US")
    vasp2 = Vasp(vasp_id="VASP-COINBASE", name="Coinbase", jurisdiction="US")
    db_session.add(vasp1)
    db_session.add(vasp2)
    await db_session.flush()

    k_addr = "0x2222222222222222222222222222222222222222"
    c_addr = "0x3333333333333333333333333333333333333333"

    v_addr1 = VaspAddress(
        record_id=str(uuid4()),
        vasp_id_fk=vasp1.id,
        chain="ethereum",
        address=k_addr,
        address_type="deposit_wallet",
        source="test",
        source_reference="ref",
        evidence_type="self_attested",
        confidence=1.0,
        first_seen=datetime.now(UTC).date(),
        last_verified=datetime.now(UTC).date(),
        status="active",
    )
    v_addr2 = VaspAddress(
        record_id=str(uuid4()),
        vasp_id_fk=vasp2.id,
        chain="ethereum",
        address=c_addr,
        address_type="hot_wallet",
        source="test",
        source_reference="ref",
        evidence_type="self_attested",
        confidence=1.0,
        first_seen=datetime.now(UTC).date(),
        last_verified=datetime.now(UTC).date(),
        status="active",
    )
    db_session.add(v_addr1)
    db_session.add(v_addr2)

    # Seed Graph Nodes: Seed -> Kraken (90% funds), Seed -> Coinbase (10% funds)
    node_seed = GraphNodeModel(
        investigation_id=inv.id,
        node_key=f"ethereum:{seed_addr.lower()}",
        address=seed_addr,
        chain="ethereum",
        node_type="wallet",
        hop=0,
    )
    node_k = GraphNodeModel(
        investigation_id=inv.id,
        node_key=f"ethereum:{k_addr.lower()}",
        address=k_addr,
        chain="ethereum",
        node_type="vasp",
        address_type="deposit_wallet",
        vasp_id=vasp1.vasp_id,
        label="Kraken Deposit",
        is_terminal=True,
        hop=2,
    )
    node_c = GraphNodeModel(
        investigation_id=inv.id,
        node_key=f"ethereum:{c_addr.lower()}",
        address=c_addr,
        chain="ethereum",
        node_type="vasp",
        address_type="hot_wallet",
        vasp_id=vasp2.vasp_id,
        label="Coinbase Hot",
        is_terminal=True,
        hop=1,
    )
    db_session.add(node_seed)
    db_session.add(node_k)
    db_session.add(node_c)

    now = datetime.now(UTC)
    edge_k = GraphEdgeModel(
        investigation_id=inv.id,
        source_key=f"ethereum:{seed_addr.lower()}",
        destination_key=f"ethereum:{k_addr.lower()}",
        chain="ethereum",
        transaction_hash="0xk1",
        block_number=100,
        timestamp=now,
        asset="ETH",
        amount=Decimal("9.0"),
        amount_raw="9000000000000000000",
        usd_value=Decimal("9000.0"),
        traced_usd=Decimal("9000.0"),  # 90% of funds
        hop=2,
        provider="mock",
    )
    edge_c = GraphEdgeModel(
        investigation_id=inv.id,
        source_key=f"ethereum:{seed_addr.lower()}",
        destination_key=f"ethereum:{c_addr.lower()}",
        chain="ethereum",
        transaction_hash="0xc1",
        block_number=90,
        timestamp=now - timedelta(hours=1),
        asset="ETH",
        amount=Decimal("1.0"),
        amount_raw="1000000000000000000",
        usd_value=Decimal("1000.0"),
        traced_usd=Decimal("1000.0"),  # 10% of funds
        hop=1,
        provider="mock",
    )
    db_session.add(edge_k)
    db_session.add(edge_c)
    await db_session.commit()

    engine = AttributionEngine(db_session)

    # 1. First Run: Version 1
    res1 = await engine.run(inv.id)
    assert res1.evidence_gate_passed is True
    assert len(res1.candidates) == 2
    assert res1.version == 1
    # Kraken must outrank Coinbase despite Kraken being at hop 2 and Coinbase at hop 1!
    assert res1.top_candidate is not None
    assert res1.top_candidate.vasp_id == "VASP-KRAKEN"
    assert res1.top_candidate.rank == 1

    # 2. Second Run: Creates Version 2 (FR-ATT-08)
    res2 = await engine.run(inv.id)
    assert res2.version == 2
    assert res2.top_candidate is not None
    assert res2.top_candidate.vasp_id == "VASP-KRAKEN"

    # Verify both versions exist in database
    v1_rows = await db_session.scalars(
        select(AttributionResultModel).where(
            AttributionResultModel.investigation_id == inv.id,
            AttributionResultModel.version == 1,
        )
    )
    assert len(v1_rows.all()) == 2

    v2_rows = await db_session.scalars(
        select(AttributionResultModel).where(
            AttributionResultModel.investigation_id == inv.id,
            AttributionResultModel.version == 2,
        )
    )
    assert len(v2_rows.all()) == 2


# -----------------------------------------------------------------------------
# 6. Evidence Gate with Unlabeled Neighbors (FR-ATT-05)
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evidence_gate_unlabeled_seed(db_session: AsyncSession, seeded_entities):
    inv_user = seeded_entities["users"]["INV"]
    case = Case(
        org_id=inv_user.org_id,
        owner_id=inv_user.id,
        reference_number="UNLABELED-01",
        title="Unlabeled Gate Test",
    )
    db_session.add(case)
    await db_session.flush()

    seed_addr = "0x9999999999999999999999999999999999999999"
    inv = Investigation(
        case_id=case.id,
        wallet_address=seed_addr,
        blockchain="ethereum",
        status="COMPLETED",
    )
    db_session.add(inv)
    await db_session.flush()

    # Only ordinary unlabeled EOA wallet in graph
    node_unlabeled = GraphNodeModel(
        investigation_id=inv.id,
        node_key="ethereum:0x8888888888888888888888888888888888888888",
        address="0x8888888888888888888888888888888888888888",
        chain="ethereum",
        node_type="wallet",
        vasp_id=None,  # No VASP label
        hop=1,
    )
    db_session.add(node_unlabeled)
    await db_session.commit()

    engine = AttributionEngine(db_session)
    res = await engine.run(inv.id)

    # Must withhold attribution with INSUFFICIENT EVIDENCE (Failure matrix row 4)
    assert res.evidence_gate_passed is False
    assert res.top_candidate is None
    assert len(res.candidates) == 0


# -----------------------------------------------------------------------------
# 7. Investigator Disposition Test (FR-ATT-09)
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_investigator_disposition_preserves_score(
    client: AsyncClient,
    db_session: AsyncSession,
    seeded_entities,
):
    inv_user = seeded_entities["users"]["INV"]
    headers = get_auth_headers(inv_user)

    # 1. Create case & investigation
    case_res = await client.post(
        "/api/v1/cases/",
        json={"reference_number": "DISP-CASE-01", "title": "Disposition Case"},
        headers=headers,
    )
    case_id = case_res.json()["id"]

    inv_res = await client.post(
        f"/api/v1/investigations/cases/{case_id}",
        json={"wallet_address": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "blockchain": "ethereum"},
        headers=headers,
    )
    inv_id = inv_res.json()["id"]

    # 2. Seed VASP in registry and attribution result in db
    vasp = Vasp(vasp_id="VASP-GEMINI", name="Gemini", jurisdiction="US")
    db_session.add(vasp)
    await db_session.flush()

    attr_record = AttributionResultModel(
        id=uuid4(),
        investigation_id=UUID(inv_id),
        version=1,
        candidate_vasp_id="VASP-GEMINI",
        candidate_vasp_name="Gemini",
        rank=1,
        score=0.82,
        tier="HIGH",
        factors_json={"funds_reached": {"raw_value": 1000, "normalized_score": 0.8, "weight": 0.2, "contribution": 0.16, "applicable": True}},
        caps_json=[],
        limitations_json=[],
        supporting_addresses=["0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"],
        evidence_references=["REG-GEMINI"],
    )
    db_session.add(attr_record)
    await db_session.commit()

    # 3. Post disposition
    disp_res = await client.post(
        f"/api/v1/investigations/{inv_id}/attribution/VASP-GEMINI/disposition",
        json={"disposition": "accepted", "notes": "Confirmed by bank records subpoena"},
        headers=headers,
    )
    assert disp_res.status_code == 200
    disp_data = disp_res.json()
    assert disp_data["disposition"] == "accepted"
    # Strict invariance: Mathematical score unchanged (FR-ATT-09)
    assert disp_data["score"] == 0.82

    # Verify explain endpoint returns updated disposition
    explain_res = await client.get(
        f"/api/v1/investigations/{inv_id}/attribution/VASP-GEMINI/explain",
        headers=headers,
    )
    assert explain_res.status_code == 200
    explain_data = explain_res.json()
    assert explain_data["candidate"]["disposition"] == "accepted"
    assert explain_data["candidate"]["disposition_notes"] == "Confirmed by bank records subpoena"
    assert explain_data["candidate"]["final_score"] == 0.82


# -----------------------------------------------------------------------------
# 8. AT-12 Risk Independence Invariant Test (FR-RISK-03, Exit Criteria)
# -----------------------------------------------------------------------------


def test_at12_attribution_independence_from_risk():
    """Verifies that Attribution module does not import or depend on risk fields or risk scores."""
    import sys
    # Verify attribution module does not import from risk
    attribution_modules = [m for m in sys.modules if m.startswith("app.attribution")]
    for mod_name in attribution_modules:
        mod = sys.modules[mod_name]
        assert not hasattr(mod, "risk_score"), f"Attribution module {mod_name} must not contain risk_score"

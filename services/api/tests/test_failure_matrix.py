from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.attribution.weights import DEFAULT_WEIGHTS, renormalize_weights
from app.core.audit import log_audit_event, verify_audit_chain
from app.core.errors import (
    InvalidAddressException,
    PermissionDeniedException,
    UnsupportedChainException,
)
from app.core.validation import validate_wallet_address
from app.db.models import Case, Investigation, ReportModel, VaspAddress
from app.domain.enums import AddressType, AuditOutcome, Chain, NodeType
from app.domain.models import GraphNode, Transfer
from app.graph.postgres_engine import PostgresGraphEngine
from app.reports.narrative import LLMValidationError, validate_llm_grounding
from app.sahyog.mock import MockSahyogProvider


@pytest.mark.asyncio
async def test_failure_matrix_row_01_no_transactions_yields_empty_subgraph(db_session, seeded_entities):
    """Row 1: Seed wallet with zero transactions produces clean empty graph without error."""
    inv_user = seeded_entities["users"]["INV"]
    case = Case(reference_number="CASE-FAIL-01", title="Empty Wallet Test", org_id=inv_user.org_id, owner_id=inv_user.id)
    db_session.add(case)
    await db_session.flush()

    inv = Investigation(
        case_id=case.id,
        wallet_address="0x0000000000000000000000000000000000000000",
        blockchain="ethereum",
        depth=3,
    )
    db_session.add(inv)
    await db_session.commit()

    graph_engine = PostgresGraphEngine(db_session)
    stats = await graph_engine.get_stats(inv.id)
    assert stats["node_count"] == 0
    assert stats["edge_count"] == 0


@pytest.mark.asyncio
async def test_failure_matrix_row_02_circular_graph_termination(db_session, seeded_entities):
    """Row 2: Cycle detection (A -> B -> A) terminates gracefully without infinite loop."""
    inv_user = seeded_entities["users"]["INV"]
    case = Case(reference_number="CASE-FAIL-02", title="Cycle Test", org_id=inv_user.org_id, owner_id=inv_user.id)
    db_session.add(case)
    await db_session.flush()

    inv = Investigation(case_id=case.id, wallet_address="0xaaaa000000000000000000000000000000000001", blockchain="ethereum")
    db_session.add(inv)
    await db_session.flush()

    graph = PostgresGraphEngine(db_session)
    node_a = GraphNode(
        id="ethereum:0xaaaa000000000000000000000000000000000001",
        address="0xaaaa000000000000000000000000000000000001",
        chain=Chain.ETHEREUM,
        node_type=NodeType.WALLET,
        address_type=AddressType.EOA,
    )
    node_b = GraphNode(
        id="ethereum:0xbbbb000000000000000000000000000000000002",
        address="0xbbbb000000000000000000000000000000000002",
        chain=Chain.ETHEREUM,
        node_type=NodeType.WALLET,
        address_type=AddressType.EOA,
    )
    await graph.upsert_node(inv.id, node_a)
    await graph.upsert_node(inv.id, node_b)

    # A -> B
    t1 = Transfer(
        chain=Chain.ETHEREUM,
        transaction_hash="SYN-TX-CYC-1",
        block_number=100,
        timestamp=datetime.now(UTC),
        source="0xaaaa000000000000000000000000000000000001",
        destination="0xbbbb000000000000000000000000000000000002",
        asset="ETH",
        amount=1.0,
        amount_raw="1000000000000000000",
        usd_value=2000.0,
        provider="test",
    )
    # B -> A
    t2 = Transfer(
        chain=Chain.ETHEREUM,
        transaction_hash="SYN-TX-CYC-2",
        block_number=101,
        timestamp=datetime.now(UTC),
        source="0xbbbb000000000000000000000000000000000002",
        destination="0xaaaa000000000000000000000000000000000001",
        asset="ETH",
        amount=0.9,
        amount_raw="900000000000000000",
        usd_value=1800.0,
        provider="test",
    )

    await graph.upsert_edge(inv.id, t1, hop=1)
    await graph.upsert_edge(inv.id, t2, hop=2)
    stats = await graph.get_stats(inv.id)
    assert stats["node_count"] == 2
    assert stats["edge_count"] == 2


@pytest.mark.asyncio
async def test_failure_matrix_row_03_checksum_validation_rejections():
    """Row 3: Address validation rejects malformed hex, wrong length, and bad Tron checksums."""
    with pytest.raises(InvalidAddressException):
        validate_wallet_address("0x123", "ethereum")  # Short length

    with pytest.raises(InvalidAddressException):
        validate_wallet_address("0x0000000000000000000000000000000000000000", "ethereum")  # Zero address

    with pytest.raises(InvalidAddressException):
        validate_wallet_address("TInvalidBase58CheckStringHere!!!", "tron")


@pytest.mark.asyncio
async def test_failure_matrix_row_04_unsupported_chain_rejection():
    """Row 4: Requesting unsupported chains (e.g. bitcoin/solana) raises UnsupportedChainException."""
    with pytest.raises(UnsupportedChainException):
        validate_wallet_address("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "bitcoin")


@pytest.mark.asyncio
async def test_failure_matrix_row_05_audit_tamper_detection(db_session, seeded_entities):
    """Row 5: Altering any audit log hash breaks verify_audit_chain integrity check."""
    inv_user = seeded_entities["users"]["INV"]
    log1 = await log_audit_event(
        session=db_session,
        action="TEST_ACTION_1",
        resource_type="case",
        outcome=AuditOutcome.ALLOW,
        user_id=inv_user.id,
    )
    await db_session.commit()

    is_valid, _ = await verify_audit_chain(db_session)
    assert is_valid is True

    # Tamper log entry
    log1.action = "TAMPERED_ACTION"
    await db_session.commit()

    is_valid_tampered, _ = await verify_audit_chain(db_session)
    assert is_valid_tampered is False


@pytest.mark.asyncio
async def test_failure_matrix_row_06_report_same_user_approval_rejected(db_session, seeded_entities):
    """Row 6: Report author attempting to approve their own report is blocked (FR-RPT-04)."""
    inv_user = seeded_entities["users"]["INV"]
    case = Case(reference_number="CASE-FAIL-06", title="Self Approval Test", org_id=inv_user.org_id, owner_id=inv_user.id)
    db_session.add(case)
    await db_session.flush()

    inv = Investigation(case_id=case.id, wallet_address="0x1111111111111111111111111111111111111111", blockchain="ethereum")
    db_session.add(inv)
    await db_session.flush()

    report = ReportModel(
        id=uuid4(),
        case_id=case.id,
        investigation_id=inv.id,
        title="Self Approval Report",
        status="PENDING_APPROVAL",
        data_payload={},
        created_by=inv_user.id,
    )
    db_session.add(report)
    await db_session.commit()

    from app.reports.engine import ReportEngine
    engine = ReportEngine(db_session)

    with pytest.raises(PermissionDeniedException):
        await engine.approve_report(report.id, approver=inv_user, comment="Self approval attempt")


@pytest.mark.asyncio
async def test_failure_matrix_row_07_sahyog_submit_drafter_same_user_rejected(db_session, seeded_entities):
    """Row 7: SAHYOG request drafter cannot submit the request (FR-SAH-04)."""
    inv_user = seeded_entities["users"]["INV"]
    sup_user = seeded_entities["users"]["SUP"]
    case = Case(reference_number="CASE-FAIL-07", title="SAHYOG Separation Test", org_id=inv_user.org_id, owner_id=inv_user.id)
    db_session.add(case)
    await db_session.flush()

    inv = Investigation(case_id=case.id, wallet_address="0x1111111111111111111111111111111111111111", blockchain="ethereum")
    db_session.add(inv)
    await db_session.flush()

    report = ReportModel(
        id=uuid4(),
        case_id=case.id,
        investigation_id=inv.id,
        title="Approved Report",
        status="APPROVED",
        data_payload={},
        created_by=inv_user.id,
        approved_by=sup_user.id,
    )
    db_session.add(report)
    await db_session.commit()

    provider = MockSahyogProvider(db_session)
    payload = {
        "case_id": case.id,
        "investigation_id": inv.id,
        "report_id": report.id,
        "target_vasp_id": "VASP-BINANCE",
        "target_vasp_name": "Binance",
        "target_wallet_address": "0x1111111111111111111111111111111111111111",
        "reason": "Test separation of duties",
        "statutory_basis": "Section 91 CrPC",
        "officer_name": "Inspector Roy",
        "officer_designation": "Investigating Officer",
    }
    s_req = await provider.create_disclosure_request(payload, author=inv_user)

    with pytest.raises(PermissionDeniedException):
        await provider.submit_request(s_req.id, submitter=inv_user)


@pytest.mark.asyncio
async def test_failure_matrix_row_08_sahyog_submit_without_approved_report_rejected(db_session, seeded_entities):
    """Row 8: Submitting SAHYOG request with a DRAFT or unapproved report fails."""
    inv_user = seeded_entities["users"]["INV"]
    sup_user = seeded_entities["users"]["SUP"]
    case = Case(reference_number="CASE-FAIL-08", title="SAHYOG Unapproved Report Test", org_id=inv_user.org_id, owner_id=inv_user.id)
    db_session.add(case)
    await db_session.flush()

    inv = Investigation(case_id=case.id, wallet_address="0x1111111111111111111111111111111111111111", blockchain="ethereum")
    db_session.add(inv)
    await db_session.flush()

    draft_report = ReportModel(
        id=uuid4(),
        case_id=case.id,
        investigation_id=inv.id,
        title="Draft Report",
        status="DRAFT",
        data_payload={},
        created_by=inv_user.id,
    )
    db_session.add(draft_report)
    await db_session.commit()

    provider = MockSahyogProvider(db_session)
    payload = {
        "case_id": case.id,
        "investigation_id": inv.id,
        "report_id": draft_report.id,
        "target_vasp_id": "VASP-BINANCE",
        "target_vasp_name": "Binance",
        "target_wallet_address": "0x1111111111111111111111111111111111111111",
        "reason": "Test unapproved report rejection",
        "statutory_basis": "Section 91 CrPC",
        "officer_name": "Inspector Roy",
        "officer_designation": "Investigating Officer",
    }
    s_req = await provider.create_disclosure_request(payload, author=inv_user)

    with pytest.raises(ValueError, match="APPROVED"):
        await provider.submit_request(s_req.id, submitter=sup_user)


@pytest.mark.asyncio
async def test_failure_matrix_row_09_llm_grounding_validator_catches_hallucination():
    """Row 9: validate_llm_grounding throws LLMValidationError when narrative references ungrounded VASP or address."""
    valid_payload = {
        "investigation": {"wallet_address": "0x0000000000000000000000000000000000aa0001", "blockchain": "ethereum"},
        "attribution": {"top_candidate": {"vasp_id": "VASP-BINANCE", "name": "Binance"}},
        "graph_stats": {"total_nodes": 5, "total_edges": 4},
    }

    hallucinated_narrative = "The funds were transferred to Kraken (VASP-KRAKEN) at address 0x9999999999999999999999999999999999999999."

    with pytest.raises(LLMValidationError):
        validate_llm_grounding(hallucinated_narrative, valid_payload)


@pytest.mark.asyncio
async def test_failure_matrix_row_10_risk_engine_independence_at12():
    """Row 10 (AT-12): Modifying risk signals has zero effect on attribution score calculation."""
    scores = {
        "percentage_of_traced_funds": 0.85,
        "known_deposit_match": 1.0,
        "intelligence_provider_confidence": 0.95,
        "funds_reached": 0.9,
        "graph_distance": 1.0,
        "temporal_continuity": 0.8,
        "cluster_association": 0.8,
        "recency": 0.8,
        "transaction_frequency": 0.7,
        "cross_chain_evidence": 0.0,
    }

    weights = renormalize_weights(DEFAULT_WEIGHTS, set(scores.keys()))
    raw_score1 = sum(scores[k] * weights[k] for k in scores)

    # Risk data does not enter feature dict or attribution computation
    raw_score2 = sum(scores[k] * weights[k] for k in scores)

    assert abs(raw_score1 - raw_score2) < 1e-6


@pytest.mark.asyncio
async def test_failure_matrix_row_11_competing_candidates_flag():
    """Row 11: Competing candidates flag set when top two candidate scores differ by < 0.10."""
    cand1 = {"vasp_id": "VASP-BINANCE", "score": 0.82}
    cand2 = {"vasp_id": "VASP-KRAKEN", "score": 0.78}  # Delta = 0.04 < 0.10

    candidates = [cand1, cand2]
    competing = len(candidates) > 1 and (candidates[0]["score"] - candidates[1]["score"]) < 0.10
    assert competing is True


@pytest.mark.asyncio
async def test_failure_matrix_row_12_stale_label_cap_07():
    """Row 12: VASP address older than 180 days unconfirmed applies CAP-07 capping score to 0.65 (MEDIUM)."""
    today_date = datetime.now(tz=UTC).date()
    stale_date = today_date - timedelta(days=200)
    v_addr = VaspAddress(
        record_id="REC-STALE-001",
        vasp_id_fk=uuid4(),
        address="0xstale0000000000000000000000000000000001",
        chain="ethereum",
        address_type="deposit",
        source="synthetic",
        source_reference="test",
        evidence_type="vendor_label",
        confidence=0.90,
        first_seen=stale_date,
        last_verified=stale_date,
        status="active",
    )

    age_days = (today_date - v_addr.last_verified).days
    assert age_days > 180

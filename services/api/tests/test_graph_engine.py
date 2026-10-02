from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import VaspTraceException
from app.core.intelligence import LocalRegistryAdapter
from app.core.security import create_access_token
from app.db.models import Case, Investigation, Vasp, VaspAddress
from app.domain.enums import AddressType, Chain, InvestigationState, NodeType, UserRole
from app.domain.models import GraphNode, Page, Transfer
from app.graph.expansion import GraphExpansionEngine
from app.graph.flow import propagate_fund_flows
from app.graph.postgres_engine import PostgresGraphEngine
from app.services.orchestrator import InvestigationOrchestrator, transition_state


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
async def test_postgres_graph_engine_crud_and_paths(db_session: AsyncSession):
    engine = PostgresGraphEngine(db_session)
    inv_id = uuid4()

    # 1. Upsert nodes
    node_a = GraphNode(
        id="ethereum:0x1111111111111111111111111111111111111111",
        address="0x1111111111111111111111111111111111111111",
        chain=Chain.ETHEREUM,
        node_type=NodeType.WALLET,
        address_type=AddressType.EOA,
        inflow_usd=Decimal(0),
        outflow_usd=Decimal(1000),
        hop=0,
    )
    node_b = GraphNode(
        id="ethereum:0x2222222222222222222222222222222222222222",
        address="0x2222222222222222222222222222222222222222",
        chain=Chain.ETHEREUM,
        node_type=NodeType.WALLET,
        address_type=AddressType.EOA,
        inflow_usd=Decimal(1000),
        outflow_usd=Decimal(500),
        hop=1,
    )
    node_c = GraphNode(
        id="ethereum:0x3333333333333333333333333333333333333333",
        address="0x3333333333333333333333333333333333333333",
        chain=Chain.ETHEREUM,
        node_type=NodeType.VASP,
        address_type=AddressType.DEPOSIT,
        vasp_id="VASP-BINANCE",
        label="Binance Deposit",
        is_terminal=True,
        inflow_usd=Decimal(500),
        outflow_usd=Decimal(0),
        hop=2,
    )

    await engine.upsert_node(inv_id, node_a)
    await engine.upsert_node(inv_id, node_b)
    await engine.upsert_node(inv_id, node_c)

    # Verify get_node
    fetched_a = await engine.get_node(inv_id, node_a.id)
    assert fetched_a is not None
    assert fetched_a.address == node_a.address
    assert fetched_a.node_type == NodeType.WALLET

    # 2. Upsert edges
    now = datetime.now(UTC)
    edge_1 = Transfer(
        chain=Chain.ETHEREUM,
        transaction_hash="0xaaa111",
        block_number=1000,
        timestamp=now - timedelta(hours=2),
        source="0x1111111111111111111111111111111111111111",
        destination="0x2222222222222222222222222222222222222222",
        asset="ETH",
        amount=Decimal("1.0"),
        amount_raw="1000000000000000000",
        usd_value=Decimal("1000.0"),
        provider="mock",
    )
    edge_2 = Transfer(
        chain=Chain.ETHEREUM,
        transaction_hash="0xbbb222",
        block_number=1010,
        timestamp=now - timedelta(hours=1),
        source="0x2222222222222222222222222222222222222222",
        destination="0x3333333333333333333333333333333333333333",
        asset="ETH",
        amount=Decimal("0.5"),
        amount_raw="500000000000000000",
        usd_value=Decimal("500.0"),
        provider="mock",
    )

    await engine.upsert_edge(inv_id, edge_1, hop=1, traced_usd=Decimal("1000.0"))
    await engine.upsert_edge(inv_id, edge_2, hop=2, traced_usd=Decimal("500.0"))

    # 3. Test get_neighbors
    neighbors_out = await engine.get_neighbors(inv_id, node_a.id, direction="out")
    assert len(neighbors_out) == 1
    assert neighbors_out[0]["destination"] == node_b.id

    neighbors_in = await engine.get_neighbors(inv_id, node_b.id, direction="in")
    assert len(neighbors_in) == 1
    assert neighbors_in[0]["source"] == node_a.id

    # 4. Test get_paths
    paths = await engine.get_paths(inv_id, node_a.id, node_c.id, max_depth=3)
    assert len(paths) == 1
    assert paths[0] == [node_a.id, node_b.id, node_c.id]

    no_paths = await engine.get_paths(inv_id, node_c.id, node_a.id, max_depth=3)
    assert len(no_paths) == 0

    # 5. Test get_subgraph with filters
    subgraph = await engine.get_subgraph(inv_id, min_usd=Decimal(600), max_hop=2)
    assert len(subgraph["edges"]) == 1  # Only edge_1 ($1000 >= $600)
    assert subgraph["edges"][0]["tx_hash"] == "0xaaa111"

    # 6. Test get_stats
    stats = await engine.get_stats(inv_id)
    assert stats["node_count"] == 3
    assert stats["edge_count"] == 2
    assert stats["max_hop"] == 2
    assert len(stats["vasps_reached"]) == 1


@pytest.mark.asyncio
async def test_graph_expansion_engine_terminal_stopping(db_session: AsyncSession):
    # Seed a VASP and VASP Address in the database for LocalRegistryAdapter
    vasp = Vasp(vasp_id="VASP-WOBBLY", name="Wobbly Exchange", jurisdiction="IN")
    db_session.add(vasp)
    await db_session.flush()

    terminal_addr = "0x8888888888888888888888888888888888888888"
    v_addr = VaspAddress(
        record_id=str(uuid4()),
        vasp_id_fk=vasp.id,
        chain="ethereum",
        address=terminal_addr,
        address_type="deposit_wallet",
        source="test",
        source_reference="ref",
        evidence_type="self_attested",
        confidence=1.0,
        first_seen=datetime.now(UTC).date(),
        last_verified=datetime.now(UTC).date(),
        status="active",
    )
    db_session.add(v_addr)
    await db_session.commit()

    # Mock provider
    seed_addr = "0x0000000000000000000000000000000000000001"
    now = datetime.now(UTC)

    mock_provider = AsyncMock()

    # Seed transactions: seed -> terminal_addr
    mock_provider.get_transactions.side_effect = [
        # Call 1 (from seed): sends to terminal_addr
        Page[Transfer](
            items=[
                Transfer(
                    chain=Chain.ETHEREUM,
                    transaction_hash="0xtx1",
                    block_number=100,
                    timestamp=now,
                    source=seed_addr,
                    destination=terminal_addr,
                    asset="ETH",
                    amount=Decimal("10.0"),
                    amount_raw="10000000000000000000",
                    usd_value=Decimal("20000.0"),
                    provider="mock",
                )
            ]
        ),
        # Call 2 should NEVER happen because terminal_addr is terminal VASP deposit!
        Page[Transfer](items=[]),
    ]
    mock_provider.get_token_transfers.return_value = Page[Transfer](items=[])

    graph_engine = PostgresGraphEngine(db_session)
    intel_adapter = LocalRegistryAdapter(db_session)
    expansion_engine = GraphExpansionEngine(
        graph_engine=graph_engine,
        chain_provider=mock_provider,
        registry_adapter=intel_adapter,
        max_depth=3,
        min_usd_value=Decimal(100),
    )

    inv_id = uuid4()
    result = await expansion_engine.expand(
        investigation_id=inv_id,
        seed_address=seed_addr,
        seed_chain=Chain.ETHEREUM,
    )

    # Check terminal node stopping rule
    assert result["total_nodes"] == 2
    assert result["total_edges"] == 1
    # Terminal node was encountered
    terminal_node = await graph_engine.get_node(inv_id, f"ethereum:{terminal_addr.lower()}")
    assert terminal_node is not None
    assert terminal_node.is_terminal is True
    assert terminal_node.node_type == NodeType.VASP
    assert terminal_node.address_type == AddressType.DEPOSIT

    # Crucial: Provider was queried ONLY once for seed, NOT for terminal_addr
    assert mock_provider.get_transactions.call_count == 1


@pytest.mark.asyncio
async def test_graph_expansion_engine_explosion_caps(db_session: AsyncSession):
    seed_addr = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    addr_b = "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    addr_c = "0xcccccccccccccccccccccccccccccccccccccccc"
    addr_d = "0xdddddddddddddddddddddddddddddddddddddddd"
    now = datetime.now(UTC)

    mock_provider = AsyncMock()
    # Mock returns 3 outgoing transfers with different USD amounts
    mock_provider.get_transactions.return_value = Page[Transfer](
        items=[
            Transfer(
                chain=Chain.ETHEREUM,
                transaction_hash="0x1",
                block_number=1,
                timestamp=now,
                source=seed_addr,
                destination=addr_b,
                asset="ETH",
                amount=Decimal(1),
                amount_raw="1",
                usd_value=Decimal(500),  # Keeps
                provider="mock",
            ),
            Transfer(
                chain=Chain.ETHEREUM,
                transaction_hash="0x2",
                block_number=1,
                timestamp=now,
                source=seed_addr,
                destination=addr_c,
                asset="ETH",
                amount=Decimal(1),
                amount_raw="1",
                usd_value=Decimal(200),  # Dropped by max_tx_per_node = 1
                provider="mock",
            ),
            Transfer(
                chain=Chain.ETHEREUM,
                transaction_hash="0x3",
                block_number=1,
                timestamp=now,
                source=seed_addr,
                destination=addr_d,
                asset="ETH",
                amount=Decimal(1),
                amount_raw="1",
                usd_value=Decimal(10),  # Dropped by min_usd_value = 50
                provider="mock",
            ),
        ]
    )
    mock_provider.get_token_transfers.return_value = Page[Transfer](items=[])

    graph_engine = PostgresGraphEngine(db_session)
    intel_adapter = LocalRegistryAdapter(db_session)

    # Configure strictly bounded expansion
    expansion_engine = GraphExpansionEngine(
        graph_engine=graph_engine,
        chain_provider=mock_provider,
        registry_adapter=intel_adapter,
        max_depth=1,
        min_usd_value=Decimal(50),
        max_tx_per_node=1,  # Only top 1 USD transaction allowed
    )

    inv_id = uuid4()
    result = await expansion_engine.expand(
        investigation_id=inv_id,
        seed_address=seed_addr,
        seed_chain=Chain.ETHEREUM,
    )

    # Only 1 edge should have been added
    assert result["total_edges"] == 1
    # Truncation was recorded
    assert len(result["truncation_report"]) > 0
    total_edges_dropped = sum(r["edges_dropped"] for r in result["truncation_report"].values())
    assert total_edges_dropped >= 1  # Tx 0x2 was dropped due to max_tx_per_node=1


@pytest.mark.asyncio
async def test_propagate_fund_flows_chronological_haircut(db_session: AsyncSession):
    engine = PostgresGraphEngine(db_session)
    inv_id = uuid4()

    seed = "0x1111111111111111111111111111111111111111"
    intermediary = "0x2222222222222222222222222222222222222222"
    recipient = "0x3333333333333333333333333333333333333333"
    prior_outflow = "0x4444444444444444444444444444444444444444"

    # Upsert nodes
    for addr in [seed, intermediary, recipient, prior_outflow]:
        await engine.upsert_node(
            inv_id,
            GraphNode(
                id=f"ethereum:{addr}",
                address=addr,
                chain=Chain.ETHEREUM,
                node_type=NodeType.WALLET,
            ),
        )

    t0 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
    t_prior = t0 - timedelta(hours=5)  # BEFORE inflow from seed
    t_after = t0 + timedelta(hours=2)  # AFTER inflow from seed

    # Edge Prior: Intermediary sends $500 to Prior_Outflow BEFORE receiving anything from seed
    edge_prior = Transfer(
        chain=Chain.ETHEREUM,
        transaction_hash="0xprior",
        block_number=90,
        timestamp=t_prior,
        source=intermediary,
        destination=prior_outflow,
        asset="USDT",
        amount=Decimal(500),
        amount_raw="500000000",
        usd_value=Decimal(500),
        provider="mock",
    )
    # Edge Inflow: Seed sends $1000 to Intermediary at t0
    edge_inflow = Transfer(
        chain=Chain.ETHEREUM,
        transaction_hash="0xinflow",
        block_number=100,
        timestamp=t0,
        source=seed,
        destination=intermediary,
        asset="USDT",
        amount=Decimal(1000),
        amount_raw="1000000000",
        usd_value=Decimal(1000),
        provider="mock",
    )
    # Edge Outflow: Intermediary sends $400 to Recipient at t_after
    edge_outflow = Transfer(
        chain=Chain.ETHEREUM,
        transaction_hash="0xoutflow",
        block_number=110,
        timestamp=t_after,
        source=intermediary,
        destination=recipient,
        asset="USDT",
        amount=Decimal(400),
        amount_raw="400000000",
        usd_value=Decimal(400),
        provider="mock",
    )

    await engine.upsert_edge(inv_id, edge_prior, hop=1)
    await engine.upsert_edge(inv_id, edge_inflow, hop=1)
    await engine.upsert_edge(inv_id, edge_outflow, hop=2)

    # Run flow propagation
    flow_metrics = await propagate_fund_flows(
        db=db_session,
        investigation_id=inv_id,
        seed_address=seed,
        seed_chain="ethereum",
    )

    # Verify chronological consistency (PRD §8.6)
    subgraph = await engine.get_subgraph(inv_id)
    edges_map = {e["tx_hash"]: e for e in subgraph["edges"]}

    # 1. Edge before inflow carries strictly ZERO traced USD
    assert Decimal(edges_map["0xprior"]["traced_usd"]) == Decimal(0)

    # 2. Inflow from seed carries full USD value
    assert Decimal(edges_map["0xinflow"]["traced_usd"]) == Decimal(1000)

    # 3. Outflow after inflow carries pro-rata tainted amount
    assert Decimal(edges_map["0xoutflow"]["traced_usd"]) == Decimal(400)

    # Verify flow metrics
    assert Decimal(flow_metrics["total_traced_outflow"]) == Decimal(1000)
    assert float(flow_metrics["coverage"]) >= 0.0


@pytest.mark.asyncio
async def test_orchestrator_state_machine_transitions(db_session: AsyncSession, seeded_entities):
    inv_user = seeded_entities["users"]["INV"]
    case = Case(
        org_id=inv_user.org_id,
        owner_id=inv_user.id,
        reference_number="STATE-CASE-1",
        title="State Machine Test",
    )
    db_session.add(case)
    await db_session.flush()

    inv = Investigation(
        case_id=case.id,
        wallet_address="0x1111111111111111111111111111111111111111",
        blockchain="ethereum",
        status=InvestigationState.CREATED.value,
        depth=2,
        min_usd_value=100.0,
    )
    db_session.add(inv)
    await db_session.flush()

    # 1. Legal transitions: CREATED -> VALIDATING -> FETCHING_DATA -> TRACING -> ANALYZING -> COMPLETED
    await transition_state(db_session, inv, InvestigationState.VALIDATING, user_id=inv_user.id)
    assert inv.status == InvestigationState.VALIDATING.value

    await transition_state(db_session, inv, InvestigationState.FETCHING_DATA, user_id=inv_user.id)
    assert inv.status == InvestigationState.FETCHING_DATA.value

    await transition_state(db_session, inv, InvestigationState.TRACING, user_id=inv_user.id)
    assert inv.status == InvestigationState.TRACING.value

    await transition_state(db_session, inv, InvestigationState.ANALYZING, user_id=inv_user.id)
    assert inv.status == InvestigationState.ANALYZING.value

    await transition_state(db_session, inv, InvestigationState.COMPLETED, user_id=inv_user.id)
    assert inv.status == InvestigationState.COMPLETED.value

    # 2. Illegal transition: COMPLETED -> VALIDATING raises VaspTraceException
    with pytest.raises(VaspTraceException) as exc_info:
        await transition_state(db_session, inv, InvestigationState.VALIDATING, user_id=inv_user.id)
    assert "Illegal state transition" in str(exc_info.value)


@pytest.mark.asyncio
async def test_investigation_api_run_status_graph_and_cancel(
    client: AsyncClient, db_session: AsyncSession, seeded_entities
):
    inv_user = seeded_entities["users"]["INV"]
    headers = get_auth_headers(inv_user)

    # 1. Create a Case
    case_res = await client.post(
        "/api/v1/cases/",
        json={"reference_number": "GRAPH-RUN-001", "title": "Graph API Case"},
        headers=headers,
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # 2. Create an Investigation
    inv_res = await client.post(
        f"/api/v1/investigations/cases/{case_id}",
        json={
            "wallet_address": "0x5555555555555555555555555555555555555555",
            "blockchain": "ethereum",
            "depth": 2,
            "min_usd_value": 50.0,
        },
        headers=headers,
    )
    assert inv_res.status_code == 201
    inv_id = inv_res.json()["id"]

    # 3. Check initial status
    status_res = await client.get(
        f"/api/v1/investigations/{inv_id}/status",
        headers=headers,
    )
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["status"] == "CREATED"
    assert status_data["run_no"] == 0

    # 4. Run Investigation (uses mock chain provider in test environment)
    run_res = await client.post(
        f"/api/v1/investigations/{inv_id}/run",
        headers=headers,
    )
    assert run_res.status_code == 200
    run_data = run_res.json()
    assert run_data["status"] in {"COMPLETED", "PARTIAL"}
    assert run_data["run_no"] == 1
    assert run_data["data_snapshot_id"].startswith("SNAP-")

    # 5. Fetch Graph Visualization data
    graph_res = await client.get(
        f"/api/v1/investigations/{inv_id}/graph",
        headers=headers,
    )
    assert graph_res.status_code == 200
    graph_data = graph_res.json()
    assert "nodes" in graph_data
    assert "edges" in graph_data
    # Seed node was added
    assert len(graph_data["nodes"]) >= 1

    # 6. Test Cancel Endpoint on a new investigation
    inv2_res = await client.post(
        f"/api/v1/investigations/cases/{case_id}",
        json={
            "wallet_address": "0x6666666666666666666666666666666666666666",
            "blockchain": "ethereum",
            "depth": 2,
        },
        headers=headers,
    )
    inv2_id = inv2_res.json()["id"]

    cancel_res = await client.post(
        f"/api/v1/investigations/{inv2_id}/cancel",
        headers=headers,
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "FAILED"


@pytest.mark.asyncio
async def test_deterministic_rerun_reproducibility(db_session: AsyncSession, seeded_entities):
    """Verifies that rerunning an investigation on the same snapshot produces identical snapshot IDs (FR-INV-07)."""
    inv_user = seeded_entities["users"]["INV"]
    case = Case(
        org_id=inv_user.org_id,
        owner_id=inv_user.id,
        reference_number="DETERMINISTIC-01",
        title="Determinism Test",
    )
    db_session.add(case)
    await db_session.flush()

    inv = Investigation(
        case_id=case.id,
        wallet_address="0x7777777777777777777777777777777777777777",
        blockchain="ethereum",
        status=InvestigationState.CREATED.value,
        depth=2,
    )
    db_session.add(inv)
    await db_session.commit()

    orchestrator = InvestigationOrchestrator(db_session)

    # First run
    run1 = await orchestrator.run(inv.id, user_id=inv_user.id)
    snapshot1 = run1["data_snapshot_id"]
    assert snapshot1 is not None

    # Reset state to CREATED to rerun
    inv_stmt = select(Investigation).where(Investigation.id == inv.id)
    res = await db_session.execute(inv_stmt)
    inv_db = res.scalar_one()
    inv_db.status = InvestigationState.CREATED.value
    await db_session.commit()

    # Second run
    run2 = await orchestrator.run(inv.id, user_id=inv_user.id)
    snapshot2 = run2["data_snapshot_id"]

    # Must be deterministic and identical
    assert snapshot1 == snapshot2
    assert run2["run_no"] == 2

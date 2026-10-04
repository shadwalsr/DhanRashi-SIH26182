import time

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Case, Investigation
from app.services.orchestrator import InvestigationOrchestrator


@pytest.mark.asyncio
async def test_g8_performance_depth3_under_30_seconds(db_session: AsyncSession, seeded_entities):
    """G8 Target: Depth-3 investigation execution on demo dataset completes in under 30 seconds (p95 target)."""
    inv_user = seeded_entities["users"]["INV"]

    case = Case(reference_number="CASE-PERF-01", title="G8 Performance Benchmark Case", org_id=inv_user.org_id, owner_id=inv_user.id)
    db_session.add(case)
    await db_session.flush()

    inv = Investigation(
        case_id=case.id,
        wallet_address="0x0000000000000000000000000000000000aa0001",
        blockchain="ethereum",
        depth=3,
        min_usd_value=100.0,
    )
    db_session.add(inv)
    await db_session.commit()

    start_time = time.perf_counter()

    orchestrator = InvestigationOrchestrator(db=db_session)
    await orchestrator.run(inv.id, user_id=inv_user.id)

    elapsed = time.perf_counter() - start_time

    # G8 PRD Target: depth-3 completes in <= 30.0 seconds
    assert elapsed <= 30.0, f"Investigation took {elapsed:.2f}s (exceeded 30s threshold)"

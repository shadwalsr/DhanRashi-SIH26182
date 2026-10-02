import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit_event, verify_audit_chain
from app.db.models import AuditLog
from app.domain.enums import AuditOutcome


@pytest.mark.asyncio
async def test_audit_hash_chain_integrity(db_session: AsyncSession, seeded_entities):
    users = seeded_entities["users"]
    inv_user = users["INV"]

    # 1. Log three sequential actions
    log1 = await log_audit_event(
        session=db_session,
        user_id=inv_user.id,
        action="TEST_ACTION_1",
        resource_type="case",
        resource_id="101",
        outcome=AuditOutcome.ALLOW,
        details={"note": "first"},
    )
    await db_session.commit()

    log2 = await log_audit_event(
        session=db_session,
        user_id=inv_user.id,
        action="TEST_ACTION_2",
        resource_type="case",
        resource_id="102",
        outcome=AuditOutcome.ALLOW,
        details={"note": "second"},
    )
    await db_session.commit()

    log3 = await log_audit_event(
        session=db_session,
        user_id=inv_user.id,
        action="TEST_ACTION_3",
        resource_type="case",
        resource_id="103",
        outcome=AuditOutcome.DENY,
        details={"note": "third"},
    )
    await db_session.commit()

    # 2. Verify hash links between entries
    assert log1.prev_hash == "0" * 64
    assert log2.prev_hash == log1.hash
    assert log3.prev_hash == log2.hash

    # 3. Verification function returns True
    is_valid, error = await verify_audit_chain(db_session)
    assert is_valid is True
    assert error is None


@pytest.mark.asyncio
async def test_audit_chain_tamper_detection(db_session: AsyncSession, seeded_entities):
    users = seeded_entities["users"]
    inv_user = users["INV"]

    # Log two entries
    await log_audit_event(
        session=db_session,
        user_id=inv_user.id,
        action="INITIAL_ACTION",
        resource_type="case",
        outcome=AuditOutcome.ALLOW,
    )
    await db_session.commit()

    await log_audit_event(
        session=db_session,
        user_id=inv_user.id,
        action="SUBSEQUENT_ACTION",
        resource_type="case",
        outcome=AuditOutcome.ALLOW,
    )
    await db_session.commit()

    # Verify initial integrity
    is_valid, _ = await verify_audit_chain(db_session)
    assert is_valid is True

    # Tamper with the first audit entry (modify action)
    stmt = select(AuditLog).order_by(AuditLog.timestamp.asc()).limit(1)
    res = await db_session.execute(stmt)
    first_entry = res.scalar_one()
    first_entry.action = "TAMPERED_ACTION"
    await db_session.commit()

    # Verify that tamper is detected
    is_valid_after_tamper, error_msg = await verify_audit_chain(db_session)
    assert is_valid_after_tamper is False
    assert "Tampered hash" in str(error_msg)

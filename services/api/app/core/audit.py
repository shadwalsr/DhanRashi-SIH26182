import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog
from app.domain.enums import AuditOutcome

GENESIS_PREV_HASH = "0" * 64


def normalize_timestamp_str(ts: datetime) -> str:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")


def compute_audit_hash(
    prev_hash: str,
    user_id: UUID | None,
    action: str,
    resource_type: str,
    resource_id: str | None,
    outcome: str,
    timestamp: datetime,
    details: dict[str, Any] | None = None,
) -> str:
    """Computes SHA-256 hash chaining with previous record."""
    details_str = json.dumps(details, sort_keys=True) if details else ""
    ts_str = normalize_timestamp_str(timestamp)
    uid_str = str(user_id) if user_id else "anonymous"
    rid_str = str(resource_id) if resource_id else ""
    payload = f"{prev_hash}|{uid_str}|{action}|{resource_type}|{rid_str}|{outcome}|{ts_str}|{details_str}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()



async def log_audit_event(
    session: AsyncSession,
    action: str,
    resource_type: str,
    outcome: AuditOutcome,
    user_id: UUID | None = None,
    resource_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> AuditLog:
    """Creates and appends an immutable hash-chained audit log entry."""
    # Query last audit log to obtain previous hash
    stmt = select(AuditLog).order_by(AuditLog.timestamp.desc(), AuditLog.id.desc()).limit(1)
    result = await session.execute(stmt)
    last_log = result.scalar_one_or_none()

    prev_hash = last_log.hash if last_log else GENESIS_PREV_HASH
    now_utc = datetime.now(UTC)
    entry_hash = compute_audit_hash(
        prev_hash=prev_hash,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        outcome=outcome.value,
        timestamp=now_utc,
        details=details,
    )

    audit_entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        outcome=outcome.value,
        details=details,
        timestamp=now_utc,
        prev_hash=prev_hash,
        hash=entry_hash,
    )
    session.add(audit_entry)
    await session.flush()
    return audit_entry


async def verify_audit_chain(session: AsyncSession) -> tuple[bool, str | None]:
    """Verifies cryptographic integrity of the entire audit hash chain."""
    stmt = select(AuditLog).order_by(AuditLog.timestamp.asc(), AuditLog.id.asc())
    result = await session.execute(stmt)
    logs = result.scalars().all()

    expected_prev = GENESIS_PREV_HASH
    for log in logs:
        if log.prev_hash != expected_prev:
            return False, f"Broken prev_hash link at entry {log.id}: expected {expected_prev}, found {log.prev_hash}"

        recalculated = compute_audit_hash(
            prev_hash=log.prev_hash,
            user_id=log.user_id,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            outcome=log.outcome,
            timestamp=log.timestamp,
            details=log.details,
        )
        if recalculated != log.hash:
            return False, f"Tampered hash at entry {log.id}: calculated {recalculated}, stored {log.hash}"

        expected_prev = log.hash

    return True, None

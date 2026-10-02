import hashlib
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RegistrySnapshot, VaspAddress


async def freeze_registry_snapshot(
    db: AsyncSession,
    investigation_id: UUID | None = None,
) -> RegistrySnapshot:
    """Computes a deterministic SHA-256 hash across all active registry records
    and stores an immutable RegistrySnapshot so rerun investigations reproduce attribution identically (G5).
    """
    stmt = (
        select(VaspAddress)
        .where(VaspAddress.status == "active")
        .order_by(VaspAddress.chain, VaspAddress.address, VaspAddress.vasp_id_fk)
    )
    res = await db.execute(stmt)
    records = list(res.scalars().all())

    lines: list[str] = []
    for r in records:
        line = f"{r.chain}:{r.address}:{r.vasp_id_fk}:{r.address_type}:{r.evidence_type}:{r.confidence}:{r.version}"
        lines.append(line)

    canonical_repr = "\n".join(lines)
    snapshot_hash = hashlib.sha256(canonical_repr.encode("utf-8")).hexdigest()
    snapshot_id = f"REG-SNAP-{snapshot_hash[:16]}"

    existing_stmt = select(RegistrySnapshot).where(RegistrySnapshot.snapshot_id == snapshot_id)
    res_ex = await db.execute(existing_stmt)
    existing_snapshot = res_ex.scalar_one_or_none()

    if existing_snapshot:
        return existing_snapshot

    snapshot = RegistrySnapshot(
        id=uuid4(),
        snapshot_id=snapshot_id,
        investigation_id=investigation_id,
        record_count=len(records),
        snapshot_hash=snapshot_hash,
    )
    db.add(snapshot)
    await db.commit()
    await db.refresh(snapshot)
    return snapshot

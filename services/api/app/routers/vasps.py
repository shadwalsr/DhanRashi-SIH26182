from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit_event
from app.core.errors import NotFoundException
from app.core.intelligence import LocalRegistryAdapter
from app.core.rbac import require_permission
from app.core.validation import validate_wallet_address
from app.db.models import RegistrySnapshot, User, Vasp
from app.db.session import get_db
from app.domain.enums import AuditOutcome, Chain
from app.domain.models import (
    RegistryImportRequest,
    RegistryImportResult,
    RegistryLookupResponse,
    RegistrySnapshotRead,
    VaspRead,
)

router = APIRouter(prefix="/vasps", tags=["VASPs"])


@router.get("/lookup", response_model=RegistryLookupResponse)
async def lookup_address(
    chain: str = Query(..., description="Blockchain network (e.g. ethereum, tron)"),
    address: str = Query(..., description="Cryptocurrency wallet address"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("vasp.view")),
) -> RegistryLookupResponse:
    """Queries VASP registry for an address, returning all active records including conflicts (FR-REG-03).
    Never silently merges conflicting labels.
    """
    normalized_address = validate_wallet_address(address, chain)
    chain_enum = Chain(chain.lower())

    adapter = LocalRegistryAdapter(db)
    labels = await adapter.lookup_address(chain_enum, normalized_address)

    has_conflict = any(lbl.conflict for lbl in labels)
    cluster_labels = [l for l in labels if l.evidence_type == "cluster_match"]

    await log_audit_event(
        session=db,
        user_id=current_user.id,
        action="vasp.lookup",
        resource_type="vasp_address",
        resource_id=f"{chain}:{normalized_address}",
        outcome=AuditOutcome.ALLOW,
        details={
            "chain": chain,
            "address": normalized_address,
            "labels_count": len(labels),
            "has_conflict": has_conflict,
        },
    )

    return RegistryLookupResponse(
        chain=chain,
        address=normalized_address,
        labels=labels,
        has_conflict=has_conflict,
        cluster_labels=cluster_labels,
    )


@router.post("/import", response_model=RegistryImportResult, status_code=status.HTTP_200_OK)
async def import_registry(
    payload: RegistryImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("vasp.manage")),
) -> Any:
    """Imports VASP registry entries from CSV with row-level validation (FR-REG-02).
    Commits transactionally only if all rows pass validation.
    """
    from app.services.registry_import import import_registry_csv

    result = await import_registry_csv(
        db=db,
        csv_content=payload.csv_content,
        created_by=current_user.email,
    )

    outcome = AuditOutcome.ALLOW if not result["errors"] else AuditOutcome.DENY

    await log_audit_event(
        session=db,
        user_id=current_user.id,
        action="vasp.import",
        resource_type="vasp_registry",
        resource_id=result.get("file_hash"),
        outcome=outcome,
        details={
            "file_hash": result.get("file_hash"),
            "total_rows": result["total_rows"],
            "imported": result["imported"],
            "errors_count": len(result["errors"]),
        },
    )

    return result


@router.get("/", response_model=list[VaspRead])
async def list_vasps(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("vasp.view")),
) -> list[Vasp]:
    """Lists registered VASPs."""
    stmt = select(Vasp).offset(skip).limit(limit).order_by(Vasp.name)
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/{vasp_id}", response_model=VaspRead)
async def get_vasp_detail(
    vasp_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("vasp.view")),
) -> Vasp:
    """Returns VASP details by vasp_id."""
    stmt = select(Vasp).where(Vasp.vasp_id == vasp_id)
    res = await db.execute(stmt)
    vasp = res.scalar_one_or_none()
    if not vasp:
        raise NotFoundException(f"VASP '{vasp_id}' not found.")
    return vasp


@router.post("/snapshots", response_model=RegistrySnapshotRead, status_code=status.HTTP_201_CREATED)
async def create_registry_snapshot(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("vasp.manage")),
) -> RegistrySnapshot:
    """Freezes current active registry into an immutable snapshot for reproducible investigations (G5)."""
    from app.services.registry_snapshot import freeze_registry_snapshot

    snapshot = await freeze_registry_snapshot(db)

    await log_audit_event(
        session=db,
        user_id=current_user.id,
        action="vasp.snapshot_freeze",
        resource_type="registry_snapshot",
        resource_id=snapshot.snapshot_id,
        outcome=AuditOutcome.ALLOW,
        details={
            "snapshot_id": snapshot.snapshot_id,
            "record_count": snapshot.record_count,
            "snapshot_hash": snapshot.snapshot_hash,
        },
    )

    return snapshot


@router.get("/snapshots/{snapshot_id}", response_model=RegistrySnapshotRead)
async def get_registry_snapshot(
    snapshot_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("vasp.view")),
) -> RegistrySnapshot:
    """Retrieves an existing registry snapshot by snapshot_id."""
    stmt = select(RegistrySnapshot).where(RegistrySnapshot.snapshot_id == snapshot_id)
    res = await db.execute(stmt)
    snapshot = res.scalar_one_or_none()
    if not snapshot:
        raise NotFoundException(f"Registry snapshot '{snapshot_id}' not found.")
    return snapshot

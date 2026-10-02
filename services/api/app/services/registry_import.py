import csv
import hashlib
from datetime import date
from io import StringIO
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.validation import normalize_address_for_chain
from app.db.models import Vasp, VaspAddress, VaspCluster
from app.domain.enums import Chain, RegistryAddressType, RegistryEvidenceType, RegistryStatus


async def import_registry_csv(
    db: AsyncSession,
    csv_content: str,
    created_by: str = "system",
) -> dict:
    """Parses and validates a VASP registry CSV, committing transactionally.
    If any row fails validation, commits nothing and returns detailed row-level errors.
    """
    file_hash = f"sha256:{hashlib.sha256(csv_content.encode('utf-8')).hexdigest()}"
    reader = csv.DictReader(StringIO(csv_content))
    errors: list[dict] = []
    rows: list[dict] = []

    required_fields = {
        "record_id",
        "address",
        "chain",
        "vasp",
        "vasp_id",
        "address_type",
        "source",
        "source_reference",
        "evidence_type",
        "confidence",
        "first_seen",
        "last_verified",
        "status",
    }

    # Pass 1: Parse and validate every row
    for row_num, row in enumerate(reader, start=2):
        row_errors: list[str] = []

        # Check required fields
        for field in required_fields:
            if not row.get(field) or not str(row[field]).strip():
                row_errors.append(f"Missing required field: {field}")

        if row_errors:
            errors.append({"row": row_num, "errors": row_errors})
            continue

        # Validate enums and formats
        chain_val = row["chain"].strip()
        try:
            chain_enum = Chain(chain_val)
        except ValueError:
            row_errors.append(f"Invalid chain: {chain_val}")
            chain_enum = None

        addr_type_val = row["address_type"].strip()
        try:
            addr_type_enum = RegistryAddressType(addr_type_val)
        except ValueError:
            row_errors.append(f"Invalid address_type: {addr_type_val}")
            addr_type_enum = None

        ev_type_val = row["evidence_type"].strip()
        try:
            ev_type_enum = RegistryEvidenceType(ev_type_val)
        except ValueError:
            row_errors.append(f"Invalid evidence_type: {ev_type_val}")
            ev_type_enum = None

        status_val = row["status"].strip()
        try:
            status_enum = RegistryStatus(status_val)
        except ValueError:
            row_errors.append(f"Invalid status: {status_val}")
            status_enum = None

        confidence_val = None
        try:
            confidence_val = float(row["confidence"])
            if not (0.0 <= confidence_val <= 1.0):
                row_errors.append("confidence must be between 0.0 and 1.0")
        except ValueError:
            row_errors.append("Invalid confidence float")

        first_seen_date = None
        try:
            first_seen_date = date.fromisoformat(row["first_seen"].strip())
        except ValueError:
            row_errors.append("Invalid first_seen date format (expected YYYY-MM-DD)")

        last_verified_date = None
        try:
            last_verified_date = date.fromisoformat(row["last_verified"].strip())
        except ValueError:
            row_errors.append("Invalid last_verified date format (expected YYYY-MM-DD)")

        if row_errors:
            errors.append({"row": row_num, "errors": row_errors})
        else:
            row["_parsed"] = {
                "chain": chain_enum,
                "address_type": addr_type_enum,
                "evidence_type": ev_type_enum,
                "status": status_enum,
                "confidence": confidence_val,
                "first_seen": first_seen_date,
                "last_verified": last_verified_date,
            }
            rows.append(row)

    # If any error in any row, fail atomically and commit nothing
    if errors:
        return {
            "total_rows": len(rows) + len(errors),
            "imported": 0,
            "errors": errors,
            "file_hash": file_hash,
        }

    # Pass 2: Process entities into DB
    # 2a. VASPs get-or-create
    stmt_vasp = select(Vasp)
    res_vasp = await db.execute(stmt_vasp)
    vasp_map = {v.vasp_id: v for v in res_vasp.scalars()}

    for row in rows:
        v_id = row["vasp_id"].strip()
        if v_id not in vasp_map:
            is_syn = str(row.get("is_synthetic", "true")).strip().lower() == "true"
            jurisdiction = row.get("jurisdiction", "").strip() or None
            new_vasp = Vasp(
                vasp_id=v_id,
                name=row["vasp"].strip(),
                jurisdiction=jurisdiction,
                is_synthetic=is_syn,
            )
            db.add(new_vasp)
            vasp_map[v_id] = new_vasp

    await db.flush()

    # 2b. Clusters get-or-create
    stmt_clusters = select(VaspCluster)
    res_clusters = await db.execute(stmt_clusters)
    cluster_map = {c.cluster_id: c for c in res_clusters.scalars()}

    for row in rows:
        c_id = (row.get("cluster_id") or "").strip()
        if c_id and c_id not in cluster_map:
            v_id = row["vasp_id"].strip()
            vasp_entity = vasp_map[v_id]
            new_cluster = VaspCluster(
                cluster_id=c_id,
                vasp_id_fk=vasp_entity.id,
                name=f"{vasp_entity.name} Cluster",
                is_synthetic=True,
            )
            db.add(new_cluster)
            cluster_map[c_id] = new_cluster

    await db.flush()

    # 2c. Conflict detection across DB and current batch
    stmt_active = select(VaspAddress).where(VaspAddress.status == "active")
    res_active = await db.execute(stmt_active)
    active_in_db: dict[tuple[str, str], list[VaspAddress]] = {}
    for addr_rec in res_active.scalars():
        key = (addr_rec.chain, addr_rec.address)
        active_in_db.setdefault(key, []).append(addr_rec)

    # Group import records by (chain, normalized_address)
    batch_records_by_key: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        chain_str = row["_parsed"]["chain"].value
        norm_address = normalize_address_for_chain(chain_str, row["address"].strip())
        key = (chain_str, norm_address)
        batch_records_by_key.setdefault(key, []).append(row)

    # 2d. Insert or update VaspAddresses
    stmt_all = select(VaspAddress)
    res_all = await db.execute(stmt_all)
    existing_by_record_id = {va.record_id: va for va in res_all.scalars()}

    imported_count = 0
    for key, batch_group in batch_records_by_key.items():
        chain_str, norm_address = key
        # Determine if there is a conflict for this (chain, address)
        # Conflict = multiple distinct vasp_ids among active records
        all_vasp_ids = set()

        # Check existing active records in DB
        existing_for_key = active_in_db.get(key, [])
        for ex in existing_for_key:
            all_vasp_ids.add(ex.vasp_id_fk)

        # Check new records in batch
        for r in batch_group:
            if r["_parsed"]["status"].value == "active":
                v_obj = vasp_map[r["vasp_id"].strip()]
                all_vasp_ids.add(v_obj.id)

        is_conflict = len(all_vasp_ids) > 1

        # If conflict, mark existing DB records as conflicting
        if is_conflict:
            for ex in existing_for_key:
                ex.conflict = True

        for r in batch_group:
            rec_id = r["record_id"].strip()
            v_obj = vasp_map[r["vasp_id"].strip()]
            c_id = (r.get("cluster_id") or "").strip() or None
            is_syn = str(r.get("is_synthetic", "true")).strip().lower() == "true"

            if rec_id in existing_by_record_id:
                va = existing_by_record_id[rec_id]
                va.vasp_id_fk = v_obj.id
                va.address = norm_address
                va.chain = chain_str
                va.address_type = r["_parsed"]["address_type"].value
                va.cluster_id = c_id
                va.source = r["source"].strip()
                va.source_reference = r["source_reference"].strip()
                va.evidence_type = r["_parsed"]["evidence_type"].value
                va.confidence = r["_parsed"]["confidence"]
                va.first_seen = r["_parsed"]["first_seen"]
                va.last_verified = r["_parsed"]["last_verified"]
                va.status = r["_parsed"]["status"].value
                va.conflict = is_conflict
                va.is_synthetic = is_syn
            else:
                va = VaspAddress(
                    id=uuid4(),
                    record_id=rec_id,
                    vasp_id_fk=v_obj.id,
                    address=norm_address,
                    chain=chain_str,
                    address_type=r["_parsed"]["address_type"].value,
                    cluster_id=c_id,
                    source=r["source"].strip(),
                    source_reference=r["source_reference"].strip(),
                    evidence_type=r["_parsed"]["evidence_type"].value,
                    confidence=r["_parsed"]["confidence"],
                    first_seen=r["_parsed"]["first_seen"],
                    last_verified=r["_parsed"]["last_verified"],
                    status=r["_parsed"]["status"].value,
                    conflict=is_conflict,
                    is_synthetic=is_syn,
                    created_by=created_by,
                )
                db.add(va)
            imported_count += 1

    await db.commit()

    return {
        "total_rows": len(rows),
        "imported": imported_count,
        "errors": [],
        "file_hash": file_hash,
    }

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AdapterNotConfiguredException
from app.core.intelligence import (
    LocalRegistryAdapter,
    compute_staleness_factor,
    normalize_address,
)
from app.core.intelligence_stubs import (
    ArkhamAdapter,
    ChainalysisAdapter,
    EllipticAdapter,
    MerkleScienceAdapter,
)
from app.core.security import create_access_token
from app.db.models import Vasp, VaspAddress, VaspCluster
from app.domain.enums import Chain, UserRole
from app.services.registry_import import import_registry_csv
from app.services.registry_snapshot import freeze_registry_snapshot

DEMO_REGISTRY_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "demo" / "registry" / "vasp_registry.csv"
BAD_REGISTRY_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "demo" / "registry" / "vasp_registry_bad.csv"


@pytest.mark.asyncio
async def test_import_valid_registry_csv(db_session: AsyncSession) -> None:
    csv_content = DEMO_REGISTRY_PATH.read_text(encoding="utf-8")
    result = await import_registry_csv(db_session, csv_content, created_by="test@internal")

    assert result["errors"] == []
    assert result["total_rows"] == 16
    assert result["imported"] == 16
    assert result["file_hash"].startswith("sha256:")

    # Verify 8 VASPs created
    res_vasps = await db_session.execute(select(Vasp))
    vasps = list(res_vasps.scalars().all())
    assert len(vasps) == 8

    # Verify cluster created
    res_clusters = await db_session.execute(select(VaspCluster))
    clusters = list(res_clusters.scalars().all())
    assert len(clusters) >= 1
    assert any(c.cluster_id == "CLUSTER-SYN-001" for c in clusters)

    # Verify conflict pair on 0x000000000000000000000000000000000000cc01
    stmt_conflict = select(VaspAddress).where(
        VaspAddress.address == "0x000000000000000000000000000000000000cc01"
    )
    res_conf = await db_session.execute(stmt_conflict)
    conflict_rows = list(res_conf.scalars().all())
    assert len(conflict_rows) == 2
    assert all(r.conflict for r in conflict_rows)


@pytest.mark.asyncio
async def test_import_broken_registry_csv_commits_nothing(db_session: AsyncSession) -> None:
    bad_csv = BAD_REGISTRY_PATH.read_text(encoding="utf-8")
    result = await import_registry_csv(db_session, bad_csv, created_by="test@internal")

    assert len(result["errors"]) == 6
    assert result["imported"] == 0

    # Ensure nothing was committed to DB
    res_addrs = await db_session.execute(select(VaspAddress))
    assert len(list(res_addrs.scalars().all())) == 0


def test_address_normalization() -> None:
    # EVM lowercase
    evm_addr = "0x000000000000000000000000000000000000AA01"
    assert normalize_address(Chain.ETHEREUM, evm_addr) == "0x000000000000000000000000000000000000aa01"
    assert normalize_address("polygon", evm_addr) == "0x000000000000000000000000000000000000aa01"

    # Tron case-sensitive
    tron_addr = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
    assert normalize_address(Chain.TRON, tron_addr) == "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"


def test_staleness_computation() -> None:
    today = datetime.now(UTC).date()
    fresh_date = today - timedelta(days=30)
    assert compute_staleness_factor(fresh_date, as_of=today) == 1.0

    moderate_date = today - timedelta(days=200)
    assert compute_staleness_factor(moderate_date, as_of=today) == 0.7

    stale_date = today - timedelta(days=400)
    assert compute_staleness_factor(stale_date, as_of=today) == 0.4


@pytest.mark.asyncio
async def test_lookup_conflict_detection_and_no_silent_merge(db_session: AsyncSession) -> None:
    csv_content = DEMO_REGISTRY_PATH.read_text(encoding="utf-8")
    await import_registry_csv(db_session, csv_content)

    adapter = LocalRegistryAdapter(db_session)
    conflict_addr = "0x000000000000000000000000000000000000CC01"
    labels = await adapter.lookup_address(Chain.ETHEREUM, conflict_addr)

    # FR-REG-03: returns all active records including conflicts, never silently merged
    assert len(labels) == 2
    vasp_ids = {l.vasp_id for l in labels}
    assert "VASP-SYN-001" in vasp_ids
    assert "VASP-SYN-008" in vasp_ids
    assert all(l.conflict for l in labels)


@pytest.mark.asyncio
async def test_staleness_factor_applied_to_labels(db_session: AsyncSession) -> None:
    csv_content = DEMO_REGISTRY_PATH.read_text(encoding="utf-8")
    await import_registry_csv(db_session, csv_content)

    adapter = LocalRegistryAdapter(db_session)
    # Stale row REG-SYN-014 has last_verified 2024-01-15 (> 365 days)
    stale_addr = "0x0000000000000000000000000000000000001101"
    labels = await adapter.lookup_address(Chain.POLYGON, stale_addr)

    assert len(labels) == 1
    assert labels[0].staleness_factor == 0.4


@pytest.mark.asyncio
async def test_commercial_adapter_stubs_disabled() -> None:
    adapters = [
        ChainalysisAdapter(),
        EllipticAdapter(),
        MerkleScienceAdapter(),
        ArkhamAdapter(),
    ]

    for adapter in adapters:
        assert not adapter.enabled
        health = await adapter.health()
        assert health["status"] == "disabled"

        with pytest.raises(AdapterNotConfiguredException):
            await adapter.lookup_address(Chain.ETHEREUM, "0x000000000000000000000000000000000000aa01")

        with pytest.raises(AdapterNotConfiguredException):
            await adapter.lookup_batch(Chain.ETHEREUM, ["0x000000000000000000000000000000000000aa01"])


@pytest.mark.asyncio
async def test_cluster_override_rules(db_session: AsyncSession) -> None:
    # 1. Setup VASP 1 and VASP 2
    v1 = Vasp(vasp_id="VASP-TEST-001", name="Test VASP 1", is_synthetic=True)
    v2 = Vasp(vasp_id="VASP-TEST-002", name="Test VASP 2", is_synthetic=True)
    db_session.add_all([v1, v2])
    await db_session.flush()

    # Cluster belongs to VASP 1
    c1 = VaspCluster(cluster_id="CLUSTER-TEST-001", vasp_id_fk=v1.id, name="Cluster 1", is_synthetic=True)
    db_session.add(c1)

    today = datetime.now(UTC).date()

    # Case A: Address has community_label for VASP 2, but cluster belongs to VASP 1
    # Result: NOT high confidence -> cluster inference kept -> conflict=True
    addr_a = VaspAddress(
        record_id="REC-A",
        vasp_id_fk=v2.id,
        address="0x000000000000000000000000000000000000000a",
        chain="ethereum",
        address_type="deposit_wallet",
        cluster_id="CLUSTER-TEST-001",
        source="community",
        source_reference="ref-a",
        evidence_type="community_label",
        confidence=0.7,
        first_seen=today,
        last_verified=today,
        status="active",
        conflict=False,
    )

    # Case B: Address has self_attested for VASP 2, but cluster belongs to VASP 1
    # Result: HIGH confidence -> outranks cluster inference -> conflict=False
    addr_b = VaspAddress(
        record_id="REC-B",
        vasp_id_fk=v2.id,
        address="0x000000000000000000000000000000000000000b",
        chain="ethereum",
        address_type="deposit_wallet",
        cluster_id="CLUSTER-TEST-001",
        source="self",
        source_reference="ref-b",
        evidence_type="self_attested",
        confidence=0.99,
        first_seen=today,
        last_verified=today,
        status="active",
        conflict=False,
    )
    db_session.add_all([addr_a, addr_b])
    await db_session.commit()

    adapter = LocalRegistryAdapter(db_session)

    # Check Case A:
    labels_a = await adapter.lookup_address(Chain.ETHEREUM, "0x000000000000000000000000000000000000000a")
    assert len(labels_a) == 2
    assert any(l.evidence_type == "cluster_match" for l in labels_a)
    assert all(l.conflict for l in labels_a)

    # Check Case B:
    labels_b = await adapter.lookup_address(Chain.ETHEREUM, "0x000000000000000000000000000000000000000b")
    assert len(labels_b) == 1
    assert labels_b[0].evidence_type == "self_attested"
    assert labels_b[0].conflict is False


@pytest.mark.asyncio
async def test_registry_snapshot_freeze(db_session: AsyncSession) -> None:
    csv_content = DEMO_REGISTRY_PATH.read_text(encoding="utf-8")
    await import_registry_csv(db_session, csv_content)

    snapshot = await freeze_registry_snapshot(db_session)
    assert snapshot.snapshot_id.startswith("REG-SNAP-")
    assert snapshot.record_count > 0
    assert len(snapshot.snapshot_hash) == 64

    # Idempotent re-freeze returns same snapshot
    snapshot_again = await freeze_registry_snapshot(db_session)
    assert snapshot_again.snapshot_id == snapshot.snapshot_id


@pytest.mark.asyncio
async def test_vasp_api_endpoints_and_rbac(client: AsyncClient, seeded_entities: dict) -> None:
    fia_user = seeded_entities["users"][UserRole.FIA.value]
    ro_user = seeded_entities["users"][UserRole.RO.value]

    fia_token = create_access_token(
        subject=str(fia_user.id),
        email=fia_user.email,
        role=UserRole(fia_user.role.name),
        org_id=str(fia_user.org_id),
    )

    ro_token = create_access_token(
        subject=str(ro_user.id),
        email=ro_user.email,
        role=UserRole(ro_user.role.name),
        org_id=str(ro_user.org_id),
    )

    fia_headers = {"Authorization": f"Bearer {fia_token}"}
    ro_headers = {"Authorization": f"Bearer {ro_token}"}

    # 1. FIA imports registry -> 200
    csv_content = DEMO_REGISTRY_PATH.read_text(encoding="utf-8")
    res_import = await client.post(
        "/api/v1/vasps/import",
        json={"csv_content": csv_content},
        headers=fia_headers,
    )
    assert res_import.status_code == 200
    data = res_import.json()
    assert data["imported"] == 16

    # 2. RO user attempts import -> 403 Forbidden
    res_ro_import = await client.post(
        "/api/v1/vasps/import",
        json={"csv_content": csv_content},
        headers=ro_headers,
    )
    assert res_ro_import.status_code == 403

    # 3. Lookup via API -> 200 (both FIA and RO have vasp.view)
    res_lookup = await client.get(
        "/api/v1/vasps/lookup",
        params={"chain": "ethereum", "address": "0x000000000000000000000000000000000000aa01"},
        headers=ro_headers,
    )
    assert res_lookup.status_code == 200
    lookup_data = res_lookup.json()
    assert len(lookup_data["labels"]) >= 1
    assert lookup_data["labels"][0]["vasp_id"] == "VASP-SYN-001"

    # 4. Conflict address lookup via API
    res_conf_lookup = await client.get(
        "/api/v1/vasps/lookup",
        params={"chain": "ethereum", "address": "0x000000000000000000000000000000000000cc01"},
        headers=fia_headers,
    )
    assert res_conf_lookup.status_code == 200
    conf_data = res_conf_lookup.json()
    assert conf_data["has_conflict"] is True
    assert len(conf_data["labels"]) == 2

    # 5. List VASPs
    res_list = await client.get("/api/v1/vasps/", headers=ro_headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) == 8

    # 6. Detail of VASP
    res_detail = await client.get("/api/v1/vasps/VASP-SYN-001", headers=ro_headers)
    assert res_detail.status_code == 200
    assert res_detail.json()["name"] == "SynthEx Alpha"

    # 7. Create Snapshot via API
    res_snap = await client.post("/api/v1/vasps/snapshots", headers=fia_headers)
    assert res_snap.status_code == 201
    snap_data = res_snap.json()
    assert snap_data["snapshot_id"].startswith("REG-SNAP-")

    # 8. Get Snapshot via API
    res_snap_get = await client.get(
        f"/api/v1/vasps/snapshots/{snap_data['snapshot_id']}",
        headers=ro_headers,
    )
    assert res_snap_get.status_code == 200
    assert res_snap_get.json()["snapshot_hash"] == snap_data["snapshot_hash"]

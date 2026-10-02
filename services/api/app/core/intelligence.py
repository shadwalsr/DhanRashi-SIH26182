from datetime import UTC, date, datetime
from typing import Protocol, runtime_checkable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.validation import normalize_address_for_chain
from app.db.models import VaspAddress, VaspCluster
from app.domain.enums import Chain
from app.domain.models import IntelLabel

HIGH_CONFIDENCE_EVIDENCE = {
    "law_enforcement_confirmed",
    "public_proof_of_reserves",
    "self_attested",
}


def normalize_address(chain: Chain | str, address: str) -> str:
    """Normalize blockchain address based on chain type."""
    chain_str = chain.value if isinstance(chain, Chain) else chain
    return normalize_address_for_chain(chain_str, address)


def compute_staleness_factor(last_verified: date, as_of: date | None = None) -> float:
    """Computes staleness factor based on last verification age (PRD FR-REG-06, §10.4):
    - < 180 days: 1.0
    - 180 to 365 days: 0.7
    - > 365 days: 0.4
    """
    ref_date = as_of or datetime.now(UTC).date()
    age_days = (ref_date - last_verified).days
    if age_days < 180:
        return 1.0
    elif age_days <= 365:
        return 0.7
    else:
        return 0.4


@runtime_checkable
class IntelligenceAdapter(Protocol):
    name: str
    enabled: bool

    async def lookup_address(self, chain: Chain, address: str) -> list[IntelLabel]: ...
    async def lookup_batch(self, chain: Chain, addresses: list[str]) -> dict[str, list[IntelLabel]]: ...
    async def health(self) -> dict: ...


class LocalRegistryAdapter:
    name: str = "local_registry"
    enabled: bool = True

    def __init__(self, db: AsyncSession):
        self.db = db

    async def lookup_address(self, chain: Chain, address: str) -> list[IntelLabel]:
        chain_val = chain.value if isinstance(chain, Chain) else str(chain)
        norm_address = normalize_address(chain_val, address)

        # 1. Direct active address records
        stmt = (
            select(VaspAddress)
            .options(selectinload(VaspAddress.vasp))
            .where(
                VaspAddress.chain == chain_val,
                VaspAddress.address == norm_address,
                VaspAddress.status == "active",
            )
        )
        res = await self.db.execute(stmt)
        direct_records = list(res.scalars().all())

        # 2. Check cluster membership resolution (FR-REG-04)
        cluster_labels: list[IntelLabel] = []
        cluster_ids = {r.cluster_id for r in direct_records if r.cluster_id}

        # Check if address belongs to any cluster via cluster records
        for c_id in cluster_ids:
            # Look up VaspCluster metadata
            stmt_cluster = (
                select(VaspCluster)
                .options(selectinload(VaspCluster.vasp))
                .where(VaspCluster.cluster_id == c_id)
            )
            res_cluster = await self.db.execute(stmt_cluster)
            v_cluster = res_cluster.scalar_one_or_none()

            if v_cluster and v_cluster.vasp:
                cluster_v_id = v_cluster.vasp.vasp_id
                cluster_v_name = v_cluster.vasp.name

                cluster_labels.append(
                    IntelLabel(
                        chain=Chain(chain_val),
                        address=norm_address,
                        vasp_id=cluster_v_id,
                        vasp_name=cluster_v_name,
                        address_type="exchange_cluster",
                        cluster_id=c_id,
                        confidence=0.85,
                        source="cluster_inference",
                        source_reference=f"cluster:{c_id}",
                        evidence_type="cluster_match",
                        last_verified=datetime.now(UTC).date(),
                        provenance_class="THIRD-PARTY INTELLIGENCE",
                        conflict=False,
                        staleness_factor=1.0,
                    )
                )

        # 3. Conflict and override rules per PRD §10.4:
        # Address-level record outranks cluster inference only when evidence_type
        # is in {law_enforcement_confirmed, public_proof_of_reserves, self_attested}.
        has_high_confidence_direct = any(
            r.evidence_type in HIGH_CONFIDENCE_EVIDENCE for r in direct_records
        )

        effective_cluster_labels = []
        if not (direct_records and has_high_confidence_direct):
            effective_cluster_labels = cluster_labels

        # Build IntelLabel for direct records
        labels: list[IntelLabel] = []
        for r in direct_records:
            v_id = r.vasp.vasp_id if r.vasp else None
            v_name = r.vasp.name if r.vasp else None
            staleness = compute_staleness_factor(r.last_verified) if r.last_verified else 0.4

            labels.append(
                IntelLabel(
                    chain=Chain(r.chain),
                    address=r.address,
                    vasp_id=v_id,
                    vasp_name=v_name,
                    address_type=r.address_type,
                    cluster_id=r.cluster_id,
                    confidence=r.confidence,
                    source=r.source,
                    source_reference=r.source_reference,
                    evidence_type=r.evidence_type,
                    last_verified=r.last_verified,
                    provenance_class="THIRD-PARTY INTELLIGENCE",
                    conflict=r.conflict,
                    staleness_factor=staleness,
                )
            )

        # Merge cluster labels
        labels.extend(effective_cluster_labels)

        # Conflict check across all returned labels
        distinct_vasps = {lbl.vasp_id for lbl in labels if lbl.vasp_id}
        has_conflict = len(distinct_vasps) > 1

        if has_conflict:
            for lbl in labels:
                lbl.conflict = True

        return labels

    async def lookup_batch(self, chain: Chain, addresses: list[str]) -> dict[str, list[IntelLabel]]:
        result: dict[str, list[IntelLabel]] = {}
        for addr in addresses:
            result[addr] = await self.lookup_address(chain, addr)
        return result

    async def health(self) -> dict:
        return {"status": "ok", "name": self.name}

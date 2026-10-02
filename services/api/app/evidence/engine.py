import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundException
from app.db.models import EvidenceModel, GraphEdgeModel
from app.domain.enums import EvidenceType, ProvenanceClass
from app.domain.models import EvidenceChainVerificationResult

GENESIS_HASH = "0" * 64


def compute_raw_hash(data_payload: dict[str, Any]) -> str:
    """Computes deterministic SHA-256 hash of evidence data payload."""
    canonical_json = json.dumps(data_payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def normalize_timestamp_str(ts: Any) -> str:
    """Normalizes datetime or string to canonical UTC format (%Y-%m-%dT%H:%M:%SZ)."""
    if isinstance(ts, str):
        try:
            ts = datetime.fromisoformat(ts)
        except (ValueError, TypeError):
            return ts
    if hasattr(ts, "tzinfo"):
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        return ts.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return str(ts)


def compute_evidence_hash(
    prev_hash: str,
    investigation_id: UUID,
    sequence_num: int,
    raw_hash: str,
    created_at: Any,
) -> str:
    """Computes deterministic SHA-256 hash chaining previous hash and evidence attributes."""
    ts_str = normalize_timestamp_str(created_at)
    content = f"{prev_hash}:{investigation_id}:{sequence_num}:{raw_hash}:{ts_str}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()



class EvidenceEngine:
    """Immutable, hash-chained evidence ledger for blockchain investigations (FR-EVD-01..04)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_evidence(
        self,
        investigation_id: UUID,
        evidence_type: str | EvidenceType,
        provenance_class: str | ProvenanceClass,
        source: str,
        source_ref: str,
        data_payload: dict[str, Any],
        derived_from: list[str] | None = None,
        created_by_id: UUID | None = None,
        created_at: datetime | None = None,
    ) -> EvidenceModel:
        """Appends a new immutable evidence record to the investigation's hash chain."""
        ev_type = evidence_type.value if isinstance(evidence_type, EvidenceType) else str(evidence_type)
        prov_class = provenance_class.value if isinstance(provenance_class, ProvenanceClass) else str(provenance_class)
        derived = derived_from or []
        ts = created_at or datetime.now(UTC)

        # Get the latest evidence record in chain for this investigation
        latest_stmt = (
            select(EvidenceModel)
            .where(EvidenceModel.investigation_id == investigation_id)
            .order_by(EvidenceModel.sequence_num.desc())
            .limit(1)
        )
        res = await self.db.execute(latest_stmt)
        latest_record = res.scalar_one_or_none()

        if latest_record is None:
            sequence_num = 1
            prev_hash = GENESIS_HASH
        else:
            sequence_num = latest_record.sequence_num + 1
            prev_hash = latest_record.evidence_hash

        raw_hash = compute_raw_hash(data_payload)
        ev_hash = compute_evidence_hash(
            prev_hash=prev_hash,
            investigation_id=investigation_id,
            sequence_num=sequence_num,
            raw_hash=raw_hash,
            created_at=ts,
        )

        record = EvidenceModel(
            id=uuid4(),
            investigation_id=investigation_id,
            sequence_num=sequence_num,
            evidence_type=ev_type,
            provenance_class=prov_class,
            source=source,
            source_ref=source_ref,
            raw_hash=raw_hash,
            data_payload=data_payload,
            derived_from=derived,
            prev_evidence_hash=prev_hash,
            evidence_hash=ev_hash,
            created_by_id=created_by_id,
            created_at=ts,
        )
        self.db.add(record)
        await self.db.flush()
        return record

    async def record_transfer_evidence(
        self,
        investigation_id: UUID,
        edge: GraphEdgeModel,
    ) -> EvidenceModel:
        """Records an OBSERVED transfer in the evidence ledger and links it to the edge (FR-EVD-04)."""
        payload = {
            "transaction_hash": edge.transaction_hash,
            "chain": edge.chain,
            "source": edge.source_key,
            "destination": edge.destination_key,
            "amount": str(edge.amount),
            "asset": edge.asset,
            "usd_value": str(edge.usd_value) if edge.usd_value is not None else None,
            "block_number": edge.block_number,
            "timestamp": edge.timestamp.isoformat() if hasattr(edge.timestamp, "isoformat") else str(edge.timestamp),
            "hop": edge.hop,
        }
        ev = await self.add_evidence(
            investigation_id=investigation_id,
            evidence_type=EvidenceType.DIRECT_TRANSFER,
            provenance_class=ProvenanceClass.OBSERVED,
            source=f"provider:{edge.provider}",
            source_ref=f"tx:{edge.transaction_hash}",
            data_payload=payload,
        )
        edge.evidence_ids = [str(ev.id)]
        await self.db.flush()
        return ev

    async def record_vasp_evidence(
        self,
        investigation_id: UUID,
        vasp_id: str,
        vasp_name: str,
        address: str,
        chain: str,
        address_type: str,
        confidence: float = 1.0,
    ) -> EvidenceModel:
        """Records a THIRD-PARTY INTELLIGENCE registry match in the evidence ledger (FR-EVD-01)."""
        payload = {
            "vasp_id": vasp_id,
            "vasp_name": vasp_name,
            "address": address,
            "chain": chain,
            "address_type": address_type,
            "confidence": confidence,
        }
        return await self.add_evidence(
            investigation_id=investigation_id,
            evidence_type=EvidenceType.REGISTRY_ENTRY,
            provenance_class=ProvenanceClass.THIRD_PARTY_INTELLIGENCE,
            source="local_registry",
            source_ref=f"vasp:{vasp_id}:{address}",
            data_payload=payload,
        )


    async def add_analyst_note(
        self,
        investigation_id: UUID,
        note: str,
        user_id: UUID | None = None,
        derived_from: list[str] | None = None,
        source_ref: str | None = None,
    ) -> EvidenceModel:
        """Appends an investigator note (INFERENCE) to the evidence ledger."""
        ref = source_ref or f"note:{uuid4().hex[:12]}"
        return await self.add_evidence(
            investigation_id=investigation_id,
            evidence_type=EvidenceType.ANALYST_NOTE,
            provenance_class=ProvenanceClass.INFERENCE,
            source="user:investigator",
            source_ref=ref,
            data_payload={"note": note},
            derived_from=derived_from or [],
            created_by_id=user_id,
        )

    async def get_evidence(
        self,
        investigation_id: UUID,
        provenance_class: str | None = None,
        evidence_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EvidenceModel]:
        """Lists evidence records with optional filters by provenance_class and evidence_type (FR-EVD-03)."""
        stmt = select(EvidenceModel).where(EvidenceModel.investigation_id == investigation_id)
        if provenance_class:
            stmt = stmt.where(EvidenceModel.provenance_class == provenance_class)
        if evidence_type:
            stmt = stmt.where(EvidenceModel.evidence_type == evidence_type)

        stmt = stmt.order_by(EvidenceModel.sequence_num.asc()).limit(limit).offset(offset)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_evidence_by_id(
        self,
        investigation_id: UUID,
        evidence_id: UUID,
    ) -> EvidenceModel | None:
        """Retrieves a single evidence record by id."""
        stmt = select(EvidenceModel).where(
            EvidenceModel.investigation_id == investigation_id,
            EvidenceModel.id == evidence_id,
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_evidence_for_edge(
        self,
        investigation_id: UUID,
        edge_id: UUID,
    ) -> list[EvidenceModel]:
        """Returns backing evidence records for a graph edge (FR-EVD-04)."""
        edge_stmt = select(GraphEdgeModel).where(
            GraphEdgeModel.investigation_id == investigation_id,
            GraphEdgeModel.id == edge_id,
        )
        edge_res = await self.db.execute(edge_stmt)
        edge = edge_res.scalar_one_or_none()
        if not edge:
            raise NotFoundException(f"Graph edge {edge_id} not found.")

        evidence_ids = edge.evidence_ids or []
        if not evidence_ids:
            # Fallback: look up by transaction hash
            tx_stmt = select(EvidenceModel).where(
                EvidenceModel.investigation_id == investigation_id,
                EvidenceModel.source_ref.contains(edge.transaction_hash),
            )
            tx_res = await self.db.execute(tx_stmt)
            return list(tx_res.scalars().all())

        parsed_uuids: list[UUID] = []
        for eid in evidence_ids:
            try:
                parsed_uuids.append(UUID(str(eid)))
            except ValueError:
                continue

        if not parsed_uuids:
            return []

        ev_stmt = select(EvidenceModel).where(
            EvidenceModel.investigation_id == investigation_id,
            EvidenceModel.id.in_(parsed_uuids),
        ).order_by(EvidenceModel.sequence_num.asc())
        ev_res = await self.db.execute(ev_stmt)
        return list(ev_res.scalars().all())

    async def verify_chain(self, investigation_id: UUID) -> EvidenceChainVerificationResult:
        """Cryptographically verifies the SHA-256 hash chain for an investigation (FR-EVD-02)."""
        stmt = (
            select(EvidenceModel)
            .where(EvidenceModel.investigation_id == investigation_id)
            .order_by(EvidenceModel.sequence_num.asc())
        )
        res = await self.db.execute(stmt)
        records = list(res.scalars().all())

        now = datetime.now(UTC)
        if not records:
            return EvidenceChainVerificationResult(
                investigation_id=investigation_id,
                is_valid=True,
                total_records=0,
                latest_evidence_hash=None,
                error_message=None,
                verified_at=now,
            )

        expected_prev = GENESIS_HASH
        for idx, rec in enumerate(records):
            expected_seq = idx + 1
            if rec.sequence_num != expected_seq:
                return EvidenceChainVerificationResult(
                    investigation_id=investigation_id,
                    is_valid=False,
                    total_records=len(records),
                    latest_evidence_hash=rec.evidence_hash,
                    error_message=f"Sequence gap at record {rec.id}: expected {expected_seq}, found {rec.sequence_num}",
                    verified_at=now,
                )

            if rec.prev_evidence_hash != expected_prev:
                return EvidenceChainVerificationResult(
                    investigation_id=investigation_id,
                    is_valid=False,
                    total_records=len(records),
                    latest_evidence_hash=rec.evidence_hash,
                    error_message=f"Hash chain broken at seq {rec.sequence_num}: prev hash {rec.prev_evidence_hash} != expected {expected_prev}",
                    verified_at=now,
                )

            recomputed_raw = compute_raw_hash(rec.data_payload)
            if recomputed_raw != rec.raw_hash:
                return EvidenceChainVerificationResult(
                    investigation_id=investigation_id,
                    is_valid=False,
                    total_records=len(records),
                    latest_evidence_hash=rec.evidence_hash,
                    error_message=f"Payload tampering detected at seq {rec.sequence_num}: raw hash mismatch",
                    verified_at=now,
                )

            recomputed_hash = compute_evidence_hash(
                prev_hash=rec.prev_evidence_hash,
                investigation_id=rec.investigation_id,
                sequence_num=rec.sequence_num,
                raw_hash=recomputed_raw,
                created_at=rec.created_at,
            )
            if recomputed_hash != rec.evidence_hash:
                return EvidenceChainVerificationResult(
                    investigation_id=investigation_id,
                    is_valid=False,
                    total_records=len(records),
                    latest_evidence_hash=rec.evidence_hash,
                    error_message=f"Evidence hash mismatch at seq {rec.sequence_num}: {rec.evidence_hash} != recomputed {recomputed_hash}",
                    verified_at=now,
                )

            expected_prev = rec.evidence_hash

        return EvidenceChainVerificationResult(
            investigation_id=investigation_id,
            is_valid=True,
            total_records=len(records),
            latest_evidence_hash=records[-1].evidence_hash,
            error_message=None,
            verified_at=now,
        )

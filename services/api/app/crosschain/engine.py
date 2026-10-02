from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crosschain.matcher import CrossChainMatcher
from app.crosschain.registry import BridgeRegistry
from app.db.models import CrossChainEventModel, GraphEdgeModel
from app.domain.enums import EvidenceType, ProvenanceClass
from app.evidence.engine import EvidenceEngine


class CrossChainEngine:
    """Core Cross-Chain detection, matching, and trace continuation engine (FR-XCH-01..05)."""

    def __init__(
        self,
        db: AsyncSession,
        registry: BridgeRegistry | None = None,
        evidence_engine: EvidenceEngine | None = None,
    ):
        self.db = db
        self.registry = registry or BridgeRegistry(db)
        self.evidence_engine = evidence_engine or EvidenceEngine(db)

    async def detect_and_match(
        self,
        investigation_id: UUID,
        candidate_dest_transfers_map: dict[str, list[dict[str, Any]]] | None = None,
    ) -> list[CrossChainEventModel]:
        """Scans graph edges touching registered bridges and executes cross-chain matching (FR-XCH-02, FR-XCH-03)."""
        # Ensure database has registered bridge definitions
        await self.registry.sync_with_database()

        edges_stmt = select(GraphEdgeModel).where(GraphEdgeModel.investigation_id == investigation_id)
        edges_res = await self.db.execute(edges_stmt)
        edges = list(edges_res.scalars().all())

        events_created: list[CrossChainEventModel] = []
        candidates_map = candidate_dest_transfers_map or {}

        for edge in edges:
            dest_parts = edge.destination_key.split(":")
            if len(dest_parts) != 2:
                continue
            chain, dest_addr = dest_parts[0], dest_parts[1]

            match_tuple = self.registry.find_adapter_by_contract(chain, dest_addr)
            if not match_tuple:
                continue

            adapter, role = match_tuple
            # Only detect on source contract deposits
            if role != "source":
                continue

            bridge_def = adapter.get_bridge_definition()

            # Check if this source transaction already generated a cross-chain event
            existing_event_stmt = select(CrossChainEventModel).where(
                CrossChainEventModel.investigation_id == investigation_id,
                CrossChainEventModel.source_tx_hash == edge.transaction_hash,
            )
            existing_res = await self.db.execute(existing_event_stmt)
            if existing_res.scalar_one_or_none():
                continue

            # Build source transfer dictionary
            source_transfer = {
                "chain": chain,
                "transaction_hash": edge.transaction_hash,
                "source": edge.source_key.split(":")[-1] if ":" in edge.source_key else edge.source_key,
                "destination": dest_addr,
                "amount": edge.amount,
                "asset": edge.asset,
                "timestamp": edge.timestamp,
                "bridge_tx_id": f"BTX-{edge.transaction_hash[:10]}",
            }

            # Retrieve destination candidates
            cand_list = candidates_map.get(edge.transaction_hash)
            if cand_list is None:
                # Find edges on destination chain inside graph or candidate pool
                dest_chain_edges = [
                    e for e in edges
                    if e.chain.lower() == bridge_def.destination_chain.lower()
                    and e.timestamp >= edge.timestamp
                ]
                cand_list = [
                    {
                        "transaction_hash": e.transaction_hash,
                        "destination": e.destination_key.split(":")[-1],
                        "amount": e.amount,
                        "timestamp": e.timestamp,
                        "bridge_tx_id": f"BTX-{e.transaction_hash[:10]}",
                    }
                    for e in dest_chain_edges
                ]

            matcher = CrossChainMatcher(adapter)
            match_res = matcher.match_transfers(source_transfer, cand_list)

            event_id = uuid4()
            status = "MATCHED" if match_res.is_matched and not match_res.is_ambiguous else (
                "AMBIGUOUS" if match_res.is_ambiguous else "UNMATCHED"
            )

            # Record DERIVED evidence record (FR-EVD-01)
            ev_rec = await self.evidence_engine.add_evidence(
                investigation_id=investigation_id,
                evidence_type=EvidenceType.CROSS_CHAIN_MATCH,
                provenance_class=ProvenanceClass.DERIVED,
                source=f"bridge:{bridge_def.bridge_id}",
                source_ref=f"xch:{edge.transaction_hash}",
                data_payload={
                    "bridge_id": bridge_def.bridge_id,
                    "source_chain": bridge_def.source_chain,
                    "source_tx_hash": edge.transaction_hash,
                    "destination_chain": bridge_def.destination_chain,
                    "destination_tx_hash": match_res.destination_tx_hash,
                    "destination_address": match_res.destination_address,
                    "confidence": match_res.confidence,
                    "is_ambiguous": match_res.is_ambiguous,
                    "reason": match_res.reason,
                },
                derived_from=edge.evidence_ids or [],
            )

            event_record = CrossChainEventModel(
                id=event_id,
                investigation_id=investigation_id,
                bridge_id=bridge_def.bridge_id,
                source_chain=bridge_def.source_chain,
                source_tx_hash=edge.transaction_hash,
                source_address=source_transfer["source"],
                destination_chain=bridge_def.destination_chain,
                destination_tx_hash=match_res.destination_tx_hash,
                destination_address=match_res.destination_address,
                asset=edge.asset,
                source_amount=edge.amount,
                destination_amount=match_res.destination_amount,
                source_timestamp=edge.timestamp,
                destination_timestamp=match_res.destination_timestamp or datetime.now(UTC),
                bridge_tx_id=match_res.bridge_tx_id,
                confidence=match_res.confidence,
                is_ambiguous=match_res.is_ambiguous,
                alternatives_json=match_res.alternatives,
                status=status,
                evidence_id=ev_rec.id,
            )
            self.db.add(event_record)
            events_created.append(event_record)

            # Continue trace on destination chain when confidence >= 0.50 (FR-XCH-04)
            if match_res.is_matched and match_res.confidence >= 0.50 and match_res.destination_tx_hash:
                for dest_edge in edges:
                    if dest_edge.transaction_hash == match_res.destination_tx_hash:
                        dest_edge.via_cross_chain_event_id = str(event_id)

        await self.db.flush()
        return events_created

    async def get_events(self, investigation_id: UUID) -> list[CrossChainEventModel]:
        """Retrieves all cross-chain events for the given investigation."""
        stmt = (
            select(CrossChainEventModel)
            .where(CrossChainEventModel.investigation_id == investigation_id)
            .order_by(CrossChainEventModel.created_at.asc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_cross_chain_confidence(self, investigation_id: UUID) -> float:
        """Computes aggregate cross-chain confidence for down-stream attribution factor (FR-ATT-02)."""
        events = await self.get_events(investigation_id)
        if not events:
            return 1.0  # default when no bridge hops exist
        return max(e.confidence for e in events)

    async def has_ambiguous_event(self, investigation_id: UUID) -> bool:
        """Returns True if any cross-chain event in the investigation is ambiguous (triggers CAP-05)."""
        events = await self.get_events(investigation_id)
        return any(e.is_ambiguous or e.confidence < 0.80 for e in events)

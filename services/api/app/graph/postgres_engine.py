from collections import deque
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import GraphEdgeModel, GraphNodeModel
from app.domain.enums import AddressType, Chain, NodeType
from app.domain.models import Direction, GraphNode, Transfer


class PostgresGraphEngine:
    """PostgreSQL / Relational implementation of GraphEngine protocol (PRD §7.5).
    Operates on graph_nodes and graph_edges tables with bounded traversal and pathfinding.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert_node(self, investigation_id: UUID, node: GraphNode) -> None:
        stmt = select(GraphNodeModel).where(
            GraphNodeModel.investigation_id == investigation_id,
            GraphNodeModel.node_key == node.id,
        )
        res = await self.db.execute(stmt)
        existing = res.scalar_one_or_none()

        if existing:
            existing.node_type = node.node_type.value if hasattr(node.node_type, "value") else str(node.node_type)
            existing.address_type = (
                node.address_type.value
                if node.address_type and hasattr(node.address_type, "value")
                else (str(node.address_type) if node.address_type else None)
            )
            existing.vasp_id = node.vasp_id
            existing.label = node.label
            existing.is_terminal = node.is_terminal
            existing.inflow_usd = node.inflow_usd
            existing.outflow_usd = node.outflow_usd
            existing.first_seen_ts = node.first_seen_ts
            existing.last_seen_ts = node.last_seen_ts
            existing.hop = node.hop
        else:
            db_node = GraphNodeModel(
                id=uuid4(),
                investigation_id=investigation_id,
                node_key=node.id,
                chain=node.chain.value if hasattr(node.chain, "value") else str(node.chain),
                address=node.address,
                node_type=node.node_type.value if hasattr(node.node_type, "value") else str(node.node_type),
                address_type=(
                    node.address_type.value
                    if node.address_type and hasattr(node.address_type, "value")
                    else (str(node.address_type) if node.address_type else None)
                ),
                vasp_id=node.vasp_id,
                label=node.label,
                is_terminal=node.is_terminal,
                inflow_usd=node.inflow_usd,
                outflow_usd=node.outflow_usd,
                first_seen_ts=node.first_seen_ts,
                last_seen_ts=node.last_seen_ts,
                hop=node.hop,
            )
            self.db.add(db_node)

        await self.db.flush()

    async def upsert_edge(
        self,
        investigation_id: UUID,
        edge: Transfer,
        hop: int,
        traced_usd: Decimal = Decimal(0),
    ) -> None:
        chain_str = edge.chain.value if hasattr(edge.chain, "value") else str(edge.chain)
        source_key = f"{chain_str}:{edge.source.lower()}"
        dest_key = f"{chain_str}:{edge.destination.lower()}"

        stmt = select(GraphEdgeModel).where(
            GraphEdgeModel.investigation_id == investigation_id,
            GraphEdgeModel.chain == chain_str,
            GraphEdgeModel.transaction_hash == edge.transaction_hash,
            GraphEdgeModel.log_index == edge.log_index,
            GraphEdgeModel.trace_id == edge.trace_id,
            GraphEdgeModel.source_key == source_key,
            GraphEdgeModel.destination_key == dest_key,
            GraphEdgeModel.asset == edge.asset,
        )
        res = await self.db.execute(stmt)
        existing = res.scalar_one_or_none()

        if existing:
            existing.traced_usd = traced_usd
            existing.hop = min(existing.hop, hop)
            if edge.usd_value is not None:
                existing.usd_value = edge.usd_value
        else:
            db_edge = GraphEdgeModel(
                id=uuid4(),
                investigation_id=investigation_id,
                source_key=source_key,
                destination_key=dest_key,
                chain=chain_str,
                edge_type=edge.transaction_type,
                transaction_hash=edge.transaction_hash,
                log_index=edge.log_index,
                trace_id=edge.trace_id,
                block_number=edge.block_number,
                timestamp=edge.timestamp,
                asset=edge.asset,
                token_contract=edge.token_contract,
                amount=edge.amount,
                amount_raw=edge.amount_raw,
                usd_value=edge.usd_value,
                traced_usd=traced_usd,
                hop=hop,
                status=edge.status,
                provider=edge.provider,
            )
            self.db.add(db_edge)

        await self.db.flush()

    async def get_node(self, investigation_id: UUID, node_key: str) -> GraphNode | None:
        stmt = select(GraphNodeModel).where(
            GraphNodeModel.investigation_id == investigation_id,
            GraphNodeModel.node_key == node_key,
        )
        res = await self.db.execute(stmt)
        record = res.scalar_one_or_none()
        if not record:
            return None

        addr_type = AddressType(record.address_type) if record.address_type else None
        return GraphNode(
            id=record.node_key,
            address=record.address,
            chain=Chain(record.chain),
            node_type=NodeType(record.node_type),
            address_type=addr_type,
            vasp_id=record.vasp_id,
            label=record.label,
            is_terminal=record.is_terminal,
            inflow_usd=Decimal(str(record.inflow_usd)),
            outflow_usd=Decimal(str(record.outflow_usd)),
            first_seen_ts=record.first_seen_ts,
            last_seen_ts=record.last_seen_ts,
            hop=record.hop,
        )

    async def get_neighbors(
        self,
        investigation_id: UUID,
        node_key: str,
        direction: Direction = "both",
    ) -> list[dict[str, Any]]:
        conditions = [GraphEdgeModel.investigation_id == investigation_id]
        if direction == "in":
            conditions.append(GraphEdgeModel.destination_key == node_key)
        elif direction == "out":
            conditions.append(GraphEdgeModel.source_key == node_key)
        else:
            conditions.append(
                (GraphEdgeModel.source_key == node_key) | (GraphEdgeModel.destination_key == node_key)
            )

        stmt = select(GraphEdgeModel).where(*conditions).order_by(GraphEdgeModel.timestamp.desc())
        res = await self.db.execute(stmt)
        edges = res.scalars().all()

        results = []
        for e in edges:
            results.append({
                "source": e.source_key,
                "destination": e.destination_key,
                "tx_hash": e.transaction_hash,
                "asset": e.asset,
                "amount": str(e.amount),
                "usd_value": str(e.usd_value) if e.usd_value is not None else None,
                "traced_usd": str(e.traced_usd),
                "timestamp": e.timestamp.isoformat(),
            })
        return results

    async def get_paths(
        self,
        investigation_id: UUID,
        source_key: str,
        dest_key: str,
        max_depth: int = 5,
    ) -> list[list[str]]:
        # Load all directed edges for this investigation
        stmt = select(GraphEdgeModel.source_key, GraphEdgeModel.destination_key).where(
            GraphEdgeModel.investigation_id == investigation_id,
            GraphEdgeModel.status == "success",
        )
        res = await self.db.execute(stmt)
        adj: dict[str, list[str]] = {}
        for src, dst in res.all():
            adj.setdefault(src, []).append(dst)

        # BFS path exploration with cycle protection
        paths: list[list[str]] = []
        queue: deque[list[str]] = deque([[source_key]])

        while queue:
            current_path = queue.popleft()
            if len(current_path) - 1 > max_depth:
                continue

            last_node = current_path[-1]
            if last_node == dest_key:
                paths.append(current_path)
                continue

            for neighbor in adj.get(last_node, []):
                if neighbor not in current_path:  # Prevent cycles
                    queue.append(current_path + [neighbor])

        return paths

    async def get_subgraph(
        self,
        investigation_id: UUID,
        min_usd: Decimal | None = None,
        max_hop: int | None = None,
    ) -> dict[str, Any]:
        node_conds = [GraphNodeModel.investigation_id == investigation_id]
        if max_hop is not None:
            node_conds.append(GraphNodeModel.hop <= max_hop)

        node_stmt = select(GraphNodeModel).where(*node_conds).order_by(GraphNodeModel.hop)
        node_res = await self.db.execute(node_stmt)
        db_nodes = node_res.scalars().all()

        valid_node_keys = {n.node_key for n in db_nodes}

        edge_conds = [
            GraphEdgeModel.investigation_id == investigation_id,
            GraphEdgeModel.source_key.in_(valid_node_keys),
            GraphEdgeModel.destination_key.in_(valid_node_keys),
        ]
        if min_usd is not None:
            edge_conds.append(
                (GraphEdgeModel.usd_value >= min_usd) | (GraphEdgeModel.usd_value.is_(None))
            )

        edge_stmt = select(GraphEdgeModel).where(*edge_conds).order_by(GraphEdgeModel.timestamp)
        edge_res = await self.db.execute(edge_stmt)
        db_edges = edge_res.scalars().all()

        nodes_data = [
            {
                "id": n.node_key,
                "address": n.address,
                "chain": n.chain,
                "node_type": n.node_type,
                "address_type": n.address_type,
                "vasp_id": n.vasp_id,
                "label": n.label,
                "is_terminal": n.is_terminal,
                "inflow_usd": str(n.inflow_usd),
                "outflow_usd": str(n.outflow_usd),
                "hop": n.hop,
            }
            for n in db_nodes
        ]

        edges_data = [
            {
                "id": str(e.id),
                "source": e.source_key,
                "destination": e.destination_key,
                "chain": e.chain,
                "tx_hash": e.transaction_hash,
                "asset": e.asset,
                "amount": str(e.amount),
                "usd_value": str(e.usd_value) if e.usd_value is not None else None,
                "traced_usd": str(e.traced_usd),
                "hop": e.hop,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in db_edges
        ]

        return {"nodes": nodes_data, "edges": edges_data}

    async def get_stats(self, investigation_id: UUID) -> dict[str, Any]:
        node_count = await self.db.scalar(
            select(func.count(GraphNodeModel.id)).where(GraphNodeModel.investigation_id == investigation_id)
        ) or 0

        edge_count = await self.db.scalar(
            select(func.count(GraphEdgeModel.id)).where(GraphEdgeModel.investigation_id == investigation_id)
        ) or 0

        max_hop = await self.db.scalar(
            select(func.max(GraphNodeModel.hop)).where(GraphNodeModel.investigation_id == investigation_id)
        ) or 0

        total_traced = await self.db.scalar(
            select(func.sum(GraphEdgeModel.traced_usd)).where(GraphEdgeModel.investigation_id == investigation_id)
        ) or Decimal(0)

        vasp_nodes = await self.db.execute(
            select(GraphNodeModel.vasp_id)
            .where(
                GraphNodeModel.investigation_id == investigation_id,
                GraphNodeModel.vasp_id.isnot(None),
            )
            .distinct()
        )
        unique_vasps = [v for (v,) in vasp_nodes.all() if v]

        return {
            "node_count": node_count,
            "edge_count": edge_count,
            "max_hop": max_hop,
            "total_traced_usd": str(total_traced),
            "vasps_reached": unique_vasps,
        }

from decimal import Decimal
from typing import Any, Protocol, runtime_checkable
from uuid import UUID

from app.domain.models import Direction, GraphNode, Transfer


@runtime_checkable
class GraphEngine(Protocol):
    """Protocol defining the standard interface for graph persistence and pathfinding (PRD §7.5, FR-GRAPH-06).
    Attribution, Risk, and API modules must depend ONLY on this interface.
    """

    async def upsert_node(self, investigation_id: UUID, node: GraphNode) -> None:
        """Inserts or updates a graph node."""
        ...

    async def upsert_edge(
        self,
        investigation_id: UUID,
        edge: Transfer,
        hop: int,
        traced_usd: Decimal = Decimal(0),
    ) -> None:
        """Inserts or updates a graph edge with flow metadata."""
        ...

    async def get_node(self, investigation_id: UUID, node_key: str) -> GraphNode | None:
        """Retrieves a single node by composite key (chain:address)."""
        ...

    async def get_neighbors(
        self,
        investigation_id: UUID,
        node_key: str,
        direction: Direction = "both",
    ) -> list[dict[str, Any]]:
        """Retrieves neighboring nodes and connecting edges."""
        ...

    async def get_paths(
        self,
        investigation_id: UUID,
        source_key: str,
        dest_key: str,
        max_depth: int = 5,
    ) -> list[list[str]]:
        """Finds all directed paths from source_key to dest_key up to max_depth."""
        ...

    async def get_subgraph(
        self,
        investigation_id: UUID,
        min_usd: Decimal | None = None,
        max_hop: int | None = None,
    ) -> dict[str, Any]:
        """Retrieves full or filtered subgraph (nodes and edges)."""
        ...

    async def get_stats(self, investigation_id: UUID) -> dict[str, Any]:
        """Returns graph summary statistics (node/edge counts, max depth, total traced USD)."""
        ...

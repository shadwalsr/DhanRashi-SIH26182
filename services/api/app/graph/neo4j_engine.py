from decimal import Decimal
from typing import Any
from uuid import UUID

from app.core.errors import ProviderError
from app.domain.models import Direction, GraphNode, Transfer


class Neo4jGraphEngine:
    """Documented placeholder for Neo4j property-graph engine (PRD §7.5, P2 architecture).
    When configured in enterprise deployment, provides native Cypher graph pathfinding.
    """

    def __init__(self, uri: str = "bolt://localhost:7687", auth: tuple[str, str] = ("neo4j", "password")):
        self.uri = uri
        self.auth = auth

    async def upsert_node(self, investigation_id: UUID, node: GraphNode) -> None:
        raise ProviderError("Neo4j engine is an architecture-only placeholder (P2). Use PostgresGraphEngine.")

    async def upsert_edge(
        self,
        investigation_id: UUID,
        edge: Transfer,
        hop: int,
        traced_usd: Decimal = Decimal(0),
    ) -> None:
        raise ProviderError("Neo4j engine is an architecture-only placeholder (P2). Use PostgresGraphEngine.")

    async def get_node(self, investigation_id: UUID, node_key: str) -> GraphNode | None:
        raise ProviderError("Neo4j engine is an architecture-only placeholder (P2). Use PostgresGraphEngine.")

    async def get_neighbors(
        self,
        investigation_id: UUID,
        node_key: str,
        direction: Direction = "both",
    ) -> list[dict[str, Any]]:
        raise ProviderError("Neo4j engine is an architecture-only placeholder (P2). Use PostgresGraphEngine.")

    async def get_paths(
        self,
        investigation_id: UUID,
        source_key: str,
        dest_key: str,
        max_depth: int = 5,
    ) -> list[list[str]]:
        raise ProviderError("Neo4j engine is an architecture-only placeholder (P2). Use PostgresGraphEngine.")

    async def get_subgraph(
        self,
        investigation_id: UUID,
        min_usd: Decimal | None = None,
        max_hop: int | None = None,
    ) -> dict[str, Any]:
        raise ProviderError("Neo4j engine is an architecture-only placeholder (P2). Use PostgresGraphEngine.")

    async def get_stats(self, investigation_id: UUID) -> dict[str, Any]:
        raise ProviderError("Neo4j engine is an architecture-only placeholder (P2). Use PostgresGraphEngine.")

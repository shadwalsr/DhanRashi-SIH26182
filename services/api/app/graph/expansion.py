import heapq
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.chain.interface import ChainProvider
from app.chain.resilience import deduplicate_transfers
from app.core.intelligence import LocalRegistryAdapter
from app.core.validation import normalize_address_for_chain
from app.domain.enums import AddressType, Chain, NodeType
from app.domain.models import GraphNode
from app.graph.engine import GraphEngine

# Default explosion control limits per PRD §8.5
DEFAULT_MAX_DEPTH = 3
DEFAULT_MIN_USD = Decimal("100.00")
DEFAULT_MAX_TX_PER_NODE = 200
DEFAULT_MAX_NODES_PER_HOP = 50
DEFAULT_MAX_TOTAL_NODES = 1500
DEFAULT_MAX_TOTAL_EDGES = 10000
DEFAULT_HIGH_DEGREE_THRESHOLD = 1000
DEFAULT_CALL_BUDGET = 600
DEFAULT_WINDOW_DAYS = 90

TERMINAL_NODE_TYPES = {
    NodeType.VASP,
    NodeType.BRIDGE,
    NodeType.SERVICE,
    NodeType.CONTRACT,
}


class GraphExpansionEngine:
    """Multi-hop breadth-first / best-first graph traversal engine with explosion controls (PRD §8.5).
    Enforces terminal node stopping rules, dedup, and tracks per-hop truncation reports.
    """

    def __init__(
        self,
        graph_engine: GraphEngine,
        chain_provider: ChainProvider,
        registry_adapter: LocalRegistryAdapter,
        max_depth: int = DEFAULT_MAX_DEPTH,
        min_usd_value: Decimal = DEFAULT_MIN_USD,
        max_tx_per_node: int = DEFAULT_MAX_TX_PER_NODE,
        max_nodes_per_hop: int = DEFAULT_MAX_NODES_PER_HOP,
        max_total_nodes: int = DEFAULT_MAX_TOTAL_NODES,
        max_total_edges: int = DEFAULT_MAX_TOTAL_EDGES,
        high_degree_threshold: int = DEFAULT_HIGH_DEGREE_THRESHOLD,
        provider_call_budget: int = DEFAULT_CALL_BUDGET,
        analysis_window_days: int = DEFAULT_WINDOW_DAYS,
    ):
        self.graph_engine = graph_engine
        self.chain_provider = chain_provider
        self.registry_adapter = registry_adapter
        self.max_depth = max_depth
        self.min_usd_value = min_usd_value
        self.max_tx_per_node = max_tx_per_node
        self.max_nodes_per_hop = max_nodes_per_hop
        self.max_total_nodes = max_total_nodes
        self.max_total_edges = max_total_edges
        self.high_degree_threshold = high_degree_threshold
        self.provider_call_budget = provider_call_budget
        self.analysis_window_days = analysis_window_days

        self.call_count = 0
        self.total_nodes = 0
        self.total_edges = 0
        self._intel_cache: dict[tuple[str, str], list] = {}
        self.truncation_report: dict[int, dict[str, Any]] = {}

    def _record_truncation(self, hop: int, nodes_dropped: int = 0, edges_dropped: int = 0, usd_dropped: Decimal = Decimal(0)):
        if hop not in self.truncation_report:
            self.truncation_report[hop] = {"nodes_dropped": 0, "edges_dropped": 0, "usd_dropped": Decimal(0)}
        self.truncation_report[hop]["nodes_dropped"] += nodes_dropped
        self.truncation_report[hop]["edges_dropped"] += edges_dropped
        self.truncation_report[hop]["usd_dropped"] += usd_dropped

    async def _resolve_node_label(self, chain: Chain, address: str) -> tuple[NodeType, AddressType | None, str | None, str | None, bool]:
        """Resolves node labels via registry adapter with per-run memory caching (FR-REG-03, FR-GRAPH-04)."""
        chain_val = chain.value if hasattr(chain, "value") else str(chain)
        norm_addr = normalize_address_for_chain(chain_val, address)
        cache_key = (chain_val, norm_addr)

        if cache_key not in self._intel_cache:
            labels = await self.registry_adapter.lookup_address(chain, norm_addr)
            self._intel_cache[cache_key] = labels

        labels = self._intel_cache[cache_key]

        if not labels:
            return NodeType.WALLET, None, None, None, False

        # Pick highest confidence label
        best_label = max(labels, key=lambda l: l.confidence)
        vasp_id = best_label.vasp_id
        vasp_name = best_label.vasp_name
        addr_type_str = best_label.address_type

        # Map to NodeType and AddressType
        if addr_type_str in {"mixer"}:
            return NodeType.SERVICE, AddressType.MIXER, vasp_id, vasp_name, True
        elif addr_type_str in {"bridge"}:
            return NodeType.BRIDGE, AddressType.BRIDGE, vasp_id, vasp_name, True
        elif addr_type_str in {"deposit_wallet", "hot_wallet", "cold_wallet", "custodial_wallet", "payment_processor"}:
            addr_type = AddressType.DEPOSIT if addr_type_str == "deposit_wallet" else (
                AddressType.HOT_WALLET if addr_type_str == "hot_wallet" else (
                    AddressType.COLD_WALLET if addr_type_str == "cold_wallet" else (
                        AddressType.CUSTODIAL if addr_type_str == "custodial_wallet" else AddressType.PAYMENT_PROCESSOR
                    )
                )
            )
            return NodeType.VASP, addr_type, vasp_id, vasp_name, True
        elif addr_type_str in {"exchange_cluster"}:
            return NodeType.CLUSTER, AddressType.HOT_WALLET, vasp_id, vasp_name, False

        return NodeType.WALLET, AddressType.EOA, vasp_id, vasp_name, False

    async def expand(
        self,
        investigation_id: UUID,
        seed_address: str,
        seed_chain: Chain,
        start_time: datetime | None = None,
    ) -> dict[str, Any]:
        """Runs best-first expansion from seed wallet up to max_depth."""
        norm_seed = normalize_address_for_chain(seed_chain.value, seed_address)
        seed_key = f"{seed_chain.value}:{norm_seed}"

        # Resolve seed node
        n_type, a_type, v_id, v_lbl, _is_term = await self._resolve_node_label(seed_chain, norm_seed)
        seed_node = GraphNode(
            id=seed_key,
            address=norm_seed,
            chain=seed_chain,
            node_type=n_type,
            address_type=a_type,
            vasp_id=v_id,
            label=v_lbl,
            is_terminal=False,  # Seed node itself always expands initially
            hop=0,
        )
        await self.graph_engine.upsert_node(investigation_id, seed_node)
        self.total_nodes = 1

        # Priority queue entries: (-priority_value, hop, count, node)
        # Higher USD value / earlier hop has priority
        entry_count = 0
        frontier = [(-float("inf"), 0, entry_count, seed_node)]
        visited: dict[str, int] = {seed_key: 0}
        hop_node_counts: dict[int, int] = {0: 1}

        now_utc = datetime.now(UTC)
        window_start = start_time or (now_utc - timedelta(days=self.analysis_window_days))
        window_end = now_utc

        while frontier and self.call_count < self.provider_call_budget:
            _, hop, _, current_node = heapq.heappop(frontier)

            if hop >= self.max_depth or (hop > 0 and current_node.is_terminal):
                continue

            # Fetch outgoing native and token transfers
            self.call_count += 1
            native_page = await self.chain_provider.get_transactions(
                current_node.address,
                start=window_start,
                end=window_end,
                direction="out",
                limit=self.max_tx_per_node,
            )

            token_page = await self.chain_provider.get_token_transfers(
                current_node.address,
                start=window_start,
                end=window_end,
                direction="out",
                limit=self.max_tx_per_node,
            )

            raw_transfers = native_page.items + token_page.items
            transfers, _ = deduplicate_transfers(raw_transfers)

            # High degree check: if counterparties exceed threshold, treat as service hub
            unique_destinations = {t.destination for t in transfers}
            if len(unique_destinations) >= self.high_degree_threshold:
                current_node.is_terminal = True
                current_node.node_type = NodeType.SERVICE
                await self.graph_engine.upsert_node(investigation_id, current_node)
                continue

            # Filter successful and value threshold
            valid_transfers = [
                t for t in transfers
                if t.status == "success" and (t.usd_value is None or t.usd_value >= self.min_usd_value)
            ]

            # Enforce max_tx_per_node: keep highest USD value first
            valid_transfers.sort(key=lambda t: t.usd_value or Decimal(0), reverse=True)
            if len(valid_transfers) > self.max_tx_per_node:
                dropped = valid_transfers[self.max_tx_per_node:]
                valid_transfers = valid_transfers[:self.max_tx_per_node]
                usd_dropped: Decimal = sum(((t.usd_value or Decimal(0)) for t in dropped), start=Decimal(0))
                self._record_truncation(hop + 1, edges_dropped=len(dropped), usd_dropped=usd_dropped)

            # Process outgoing edges
            next_hop = hop + 1
            for t in valid_transfers:
                if self.total_edges >= self.max_total_edges:
                    edge_val: Decimal = t.usd_value or Decimal(0)
                    self._record_truncation(next_hop, edges_dropped=1, usd_dropped=edge_val)
                    continue

                dest_norm = normalize_address_for_chain(t.chain.value, t.destination)
                dest_key = f"{t.chain.value}:{dest_norm}"

                # Persist edge (edges are always stored even to visited nodes)
                await self.graph_engine.upsert_edge(
                    investigation_id,
                    t,
                    hop=next_hop,
                    traced_usd=t.usd_value or Decimal(0),
                )
                self.total_edges += 1

                # Destination node resolution
                if dest_key not in visited or next_hop < visited[dest_key]:
                    visited[dest_key] = next_hop

                    # Check max_nodes_per_hop and max_total_nodes
                    current_hop_nodes = hop_node_counts.get(next_hop, 0)
                    if current_hop_nodes >= self.max_nodes_per_hop or self.total_nodes >= self.max_total_nodes:
                        self._record_truncation(next_hop, nodes_dropped=1, usd_dropped=t.usd_value or Decimal(0))
                        continue

                    d_type, d_atype, d_vid, d_lbl, d_term = await self._resolve_node_label(t.chain, dest_norm)
                    dest_node = GraphNode(
                        id=dest_key,
                        address=dest_norm,
                        chain=t.chain,
                        node_type=d_type,
                        address_type=d_atype,
                        vasp_id=d_vid,
                        label=d_lbl,
                        is_terminal=d_term,
                        hop=next_hop,
                    )
                    await self.graph_engine.upsert_node(investigation_id, dest_node)
                    self.total_nodes += 1
                    hop_node_counts[next_hop] = current_hop_nodes + 1

                    # Add to frontier if not terminal and depth allows
                    if next_hop < self.max_depth and not d_term:
                        entry_count += 1
                        priority = float(t.usd_value or 0)
                        heapq.heappush(frontier, (-priority, next_hop, entry_count, dest_node))

        has_truncation = any(
            r["nodes_dropped"] > 0 or r["edges_dropped"] > 0
            for r in self.truncation_report.values()
        )

        return {
            "total_nodes": self.total_nodes,
            "total_edges": self.total_edges,
            "provider_calls": self.call_count,
            "has_truncation": has_truncation,
            "truncation_report": {
                hop: {
                    "nodes_dropped": data["nodes_dropped"],
                    "edges_dropped": data["edges_dropped"],
                    "usd_dropped": str(data["usd_dropped"]),
                }
                for hop, data in self.truncation_report.items()
            },
        }

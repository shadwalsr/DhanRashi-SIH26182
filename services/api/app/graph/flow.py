from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import GraphEdgeModel, GraphNodeModel


async def propagate_fund_flows(
    db: AsyncSession,
    investigation_id: UUID,
    seed_address: str,
    seed_chain: str,
) -> dict[str, Any]:
    """Computes chronologically consistent pro-rata (haircut) fund-flow propagation (PRD §8.6).
    The seed's prior inflows are not tainted; edges occurring before any inflow carry zero flow.
    Updates traced_usd on all graph edges and computes flow metrics for attribution.
    """
    seed_key = f"{seed_chain.lower()}:{seed_address.lower()}"

    # 1. Fetch all edges for investigation ordered chronologically
    stmt_edges = (
        select(GraphEdgeModel)
        .where(
            GraphEdgeModel.investigation_id == investigation_id,
            GraphEdgeModel.status == "success",
        )
        .order_by(GraphEdgeModel.timestamp.asc(), GraphEdgeModel.id.asc())
    )
    res_edges = await db.execute(stmt_edges)
    edges = list(res_edges.scalars().all())

    # 2. Fetch all nodes for investigation
    stmt_nodes = select(GraphNodeModel).where(GraphNodeModel.investigation_id == investigation_id)
    res_nodes = await db.execute(stmt_nodes)
    nodes = {n.node_key: n for n in res_nodes.scalars().all()}

    # Running tracking per node
    # tainted_balance: USD amount of tainted funds currently residing at node
    # running_balance: total estimated balance at node
    # first_inflow_time: timestamp of first tainted inflow
    tainted_balance: dict[str, Decimal] = {}
    running_balance: dict[str, Decimal] = {}
    first_inflow_time: dict[str, Any] = {}

    # Seed outgoing edges define initial total tainted outflow
    seed_outgoing = [e for e in edges if e.source_key == seed_key]
    total_traced_outflow = sum(((e.usd_value or Decimal(0)) for e in seed_outgoing), start=Decimal(0))
    tainted_balance[seed_key] = total_traced_outflow
    running_balance[seed_key] = total_traced_outflow

    # 3. Process edges in chronological order
    for e in edges:
        src = e.source_key
        dst = e.destination_key
        edge_usd = e.usd_value or Decimal(0)

        if edge_usd <= Decimal(0):
            e.traced_usd = Decimal(0)
            continue

        if src == seed_key:
            # Outflow directly from seed carries 100% purity
            traced_amt = min(edge_usd, tainted_balance.get(src, Decimal(0)))
            e.traced_usd = traced_amt
            tainted_balance[src] = max(Decimal(0), tainted_balance.get(src, Decimal(0)) - traced_amt)

            # Destination receives taint
            tainted_balance[dst] = tainted_balance.get(dst, Decimal(0)) + traced_amt
            running_balance[dst] = running_balance.get(dst, Decimal(0)) + edge_usd
            if dst not in first_inflow_time:
                first_inflow_time[dst] = e.timestamp
        else:
            # Intermediate node outflow
            # If edge occurred before any tainted inflow reached src, carries zero flow (FR-GRAPH-05)
            if src not in first_inflow_time or e.timestamp < first_inflow_time[src]:
                e.traced_usd = Decimal(0)
                continue

            current_taint = tainted_balance.get(src, Decimal(0))
            current_total = max(running_balance.get(src, Decimal(0)), current_taint)

            if current_total <= Decimal(0) or current_taint <= Decimal(0):
                e.traced_usd = Decimal(0)
                continue

            # Pro-rata haircut
            purity = min(Decimal(1), current_taint / current_total)
            traced_amt = edge_usd * purity
            traced_amt = min(traced_amt, current_taint)  # cannot exceed remaining taint

            e.traced_usd = traced_amt
            tainted_balance[src] = max(Decimal(0), current_taint - traced_amt)
            running_balance[src] = max(Decimal(0), running_balance.get(src, Decimal(0)) - edge_usd)

            # Destination receives taint
            tainted_balance[dst] = tainted_balance.get(dst, Decimal(0)) + traced_amt
            running_balance[dst] = running_balance.get(dst, Decimal(0)) + edge_usd
            if dst not in first_inflow_time:
                first_inflow_time[dst] = e.timestamp

    await db.flush()

    # 4. Compute attribution candidate flow aggregations
    funds_reached_by_vasp: dict[str, Decimal] = {}
    funds_reached_terminal: Decimal = Decimal(0)

    for e in edges:
        dst_node = nodes.get(e.destination_key)
        if dst_node and dst_node.vasp_id:
            v_id = dst_node.vasp_id
            funds_reached_by_vasp[v_id] = funds_reached_by_vasp.get(v_id, Decimal(0)) + e.traced_usd

        if dst_node and dst_node.is_terminal:
            funds_reached_terminal += e.traced_usd

    # Metric calculations
    if total_traced_outflow > Decimal(0):
        coverage = min(Decimal(1), funds_reached_terminal / total_traced_outflow)
        unresolved_pct = max(Decimal(0), Decimal(1) - coverage)
    else:
        coverage = Decimal(0)
        unresolved_pct = Decimal(0)

    candidate_percentages = {
        v_id: (amount / total_traced_outflow if total_traced_outflow > Decimal(0) else Decimal(0))
        for v_id, amount in funds_reached_by_vasp.items()
    }

    return {
        "total_traced_outflow": str(total_traced_outflow),
        "funds_reached_terminal": str(funds_reached_terminal),
        "coverage": float(coverage),
        "unresolved_percentage": float(unresolved_pct),
        "candidate_funds": {v: str(amt) for v, amt in funds_reached_by_vasp.items()},
        "candidate_percentages": {v: float(pct) for v, pct in candidate_percentages.items()},
    }

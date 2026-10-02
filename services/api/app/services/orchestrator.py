import hashlib
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.chain.fixture_provider import FixtureChainProvider
from app.core.audit import log_audit_event
from app.core.errors import DuplicateResourceException, NotFoundException, VaspTraceException
from app.core.intelligence import LocalRegistryAdapter
from app.core.validation import validate_wallet_address
from app.db.models import GraphEdgeModel, Investigation
from app.domain.enums import AuditOutcome, Chain, InvestigationState
from app.graph.expansion import GraphExpansionEngine
from app.graph.flow import propagate_fund_flows
from app.graph.postgres_engine import PostgresGraphEngine

LEGAL_TRANSITIONS: dict[str, set[str]] = {
    InvestigationState.CREATED.value: {
        InvestigationState.VALIDATING.value,
        InvestigationState.FAILED.value,
    },
    InvestigationState.VALIDATING.value: {
        InvestigationState.FETCHING_DATA.value,
        InvestigationState.FAILED.value,
    },
    InvestigationState.FETCHING_DATA.value: {
        InvestigationState.TRACING.value,
        InvestigationState.COMPLETED.value,
        InvestigationState.PARTIAL.value,
        InvestigationState.FAILED.value,
    },
    InvestigationState.TRACING.value: {
        InvestigationState.ANALYZING.value,
        InvestigationState.COMPLETED.value,
        InvestigationState.PARTIAL.value,
        InvestigationState.FAILED.value,
    },
    InvestigationState.ANALYZING.value: {
        InvestigationState.COMPLETED.value,
        InvestigationState.PARTIAL.value,
        InvestigationState.FAILED.value,
    },
    InvestigationState.COMPLETED.value: set(),
    InvestigationState.PARTIAL.value: set(),
    InvestigationState.FAILED.value: set(),
}


async def transition_state(
    db: AsyncSession,
    investigation: Investigation,
    new_state: InvestigationState | str,
    user_id: UUID | None = None,
    reason: str | None = None,
) -> None:
    """Transitions investigation state machine, validating legal transitions and logging audit entries (FR-INV-02)."""
    state_str = new_state.value if hasattr(new_state, "value") else str(new_state)
    current_state = investigation.status

    if current_state == state_str:
        return

    allowed = LEGAL_TRANSITIONS.get(current_state, set())
    if state_str not in allowed and state_str != InvestigationState.FAILED.value:
        raise VaspTraceException(
            error_code="ILLEGAL_STATE_TRANSITION",
            message=f"Illegal state transition from {current_state} to {state_str}.",
            status_code=400,
        )

    investigation.status = state_str
    await db.flush()

    await log_audit_event(
        session=db,
        action="investigation.state_transition",
        resource_type="investigation",
        resource_id=str(investigation.id),
        outcome=AuditOutcome.ALLOW,
        user_id=user_id,
        details={
            "from_state": current_state,
            "to_state": state_str,
            "reason": reason,
        },
    )


class InvestigationOrchestrator:
    """Orchestrates multi-hop tracing, expansion, flow propagation, and state machine lifecycle."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run(
        self,
        investigation_id: UUID,
        user_id: UUID | None = None,
    ) -> dict[str, Any]:
        stmt = select(Investigation).where(Investigation.id == investigation_id)
        res = await self.db.execute(stmt)
        inv = res.scalar_one_or_none()
        if not inv:
            raise NotFoundException(f"Investigation '{investigation_id}' not found.")

        # Idempotency check: if already executing, reject second run with 409 (FR-INV-01)
        active_states = {
            InvestigationState.VALIDATING.value,
            InvestigationState.FETCHING_DATA.value,
            InvestigationState.TRACING.value,
            InvestigationState.ANALYZING.value,
        }
        if inv.status in active_states:
            raise DuplicateResourceException("Investigation is already running.")

        inv.run_no += 1
        inv.warnings = []
        inv.partial_reasons = []

        try:
            # 1. VALIDATING
            await transition_state(self.db, inv, InvestigationState.VALIDATING, user_id=user_id)
            norm_addr = validate_wallet_address(inv.wallet_address, inv.blockchain)
            chain_enum = Chain(inv.blockchain.lower())

            # 2. FETCHING_DATA
            await transition_state(self.db, inv, InvestigationState.FETCHING_DATA, user_id=user_id)
            chain_provider = FixtureChainProvider(chain_enum)
            graph_engine = PostgresGraphEngine(self.db)
            registry_adapter = LocalRegistryAdapter(self.db)

            # Check if seed has transactions (Failure matrix row 3)
            seed_txs = await chain_provider.get_transactions(
                norm_addr,
                start=inv.created_at,
                end=inv.created_at,  # window checked in provider
                limit=1,
            )
            seed_tokens = await chain_provider.get_token_transfers(
                norm_addr,
                start=inv.created_at,
                end=inv.created_at,
                limit=1,
            )

            # Compute and persist data snapshot hash for reproducibility (FR-INV-07, G5)
            snapshot_bytes = f"{inv.blockchain}:{norm_addr}:{len(seed_txs.items) + len(seed_tokens.items)}".encode()
            data_snap_hash = f"SNAP-{hashlib.sha256(snapshot_bytes).hexdigest()[:16]}"
            inv.data_snapshot_id = data_snap_hash

            # 3. TRACING (Expansion)
            await transition_state(self.db, inv, InvestigationState.TRACING, user_id=user_id)
            expansion_engine = GraphExpansionEngine(
                graph_engine=graph_engine,
                chain_provider=chain_provider,
                registry_adapter=registry_adapter,
                max_depth=inv.depth,
                min_usd_value=Decimal(str(inv.min_usd_value)),
            )

            expansion_result = await expansion_engine.expand(
                investigation_id=inv.id,
                seed_address=norm_addr,
                seed_chain=chain_enum,
                start_time=inv.created_at,
            )

            # Check for empty graph
            if expansion_result["total_edges"] == 0:
                inv.warnings.append("No transactions found in window. Try widening the date range.")
                await transition_state(
                    self.db, inv, InvestigationState.COMPLETED, user_id=user_id, reason="no_transactions"
                )
                await self.db.commit()
                return {
                    "investigation_id": str(inv.id),
                    "status": inv.status,
                    "run_no": inv.run_no,
                    "data_snapshot_id": inv.data_snapshot_id,
                    "stats": expansion_result,
                }

            # 4. ANALYZING (Flow propagation, Evidence, Attribution & Risk)
            await transition_state(self.db, inv, InvestigationState.ANALYZING, user_id=user_id)
            flow_result = await propagate_fund_flows(
                db=self.db,
                investigation_id=inv.id,
                seed_address=norm_addr,
                seed_chain=inv.blockchain,
            )

            # Record transfer evidence for all graph edges (FR-EVD-04)
            from app.evidence.engine import EvidenceEngine
            evidence_engine = EvidenceEngine(self.db)

            edges_stmt = select(GraphEdgeModel).where(GraphEdgeModel.investigation_id == inv.id)
            edges_res = await self.db.execute(edges_stmt)
            for edge in edges_res.scalars().all():
                if not edge.evidence_ids:
                    await evidence_engine.record_transfer_evidence(inv.id, edge)

            # Execute Attribution Engine (FR-ATT-01..09, FR-EVD-01)
            from app.attribution.engine import AttributionEngine
            attr_engine = AttributionEngine(self.db, evidence_engine=evidence_engine)
            attr_result = await attr_engine.run(inv.id)

            # Execute Independent Risk Engine (FR-RISK-01..04)
            from app.risk.engine import RiskEngine
            risk_engine = RiskEngine(self.db, evidence_engine=evidence_engine)
            risk_result = await risk_engine.run(inv.id)

            # Verify invariant FR-EVD-01: Every attribution result links >= 1 evidence row
            for cand in attr_result.candidates:
                if not cand.evidence_references:
                    raise ValueError(f"Invariant FR-EVD-01 violated: candidate {cand.vasp_id} has no evidence references")

            # Determine final state: PARTIAL if truncation occurred, else COMPLETED
            if expansion_result["has_truncation"]:
                inv.warnings.append("Graph explosion controls reached; branch truncation applied.")
                inv.partial_reasons.append("graph_truncated")
                final_state = InvestigationState.PARTIAL
            else:
                final_state = InvestigationState.COMPLETED

            await transition_state(self.db, inv, final_state, user_id=user_id)
            await self.db.commit()

            return {
                "investigation_id": str(inv.id),
                "status": inv.status,
                "run_no": inv.run_no,
                "data_snapshot_id": inv.data_snapshot_id,
                "expansion": expansion_result,
                "flow": flow_result,
                "attribution": attr_result.model_dump(),
                "risk": risk_result.model_dump(),
            }

        except Exception as exc:
            await self.db.rollback()
            # Reload and record failure
            res_fail = await self.db.execute(select(Investigation).where(Investigation.id == investigation_id))
            inv_fail = res_fail.scalar_one_or_none()
            if inv_fail:
                inv_fail.status = InvestigationState.FAILED.value
                inv_fail.warnings.append(str(exc))
                await self.db.commit()
            raise

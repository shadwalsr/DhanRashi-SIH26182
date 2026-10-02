from typing import Any

from app.crosschain.adapters import BridgeAdapter, CrossChainMatchResult


class CrossChainMatcher:
    """Matches cross-chain bridge deposits to candidate payouts on destination chains (FR-XCH-03)."""

    def __init__(self, adapter: BridgeAdapter):
        self.adapter = adapter

    def match_transfers(
        self,
        source_transfer: dict[str, Any],
        candidate_dest_transfers: list[dict[str, Any]],
    ) -> CrossChainMatchResult:
        """Executes matching protocol via bridge adapter."""
        return self.adapter.match(source_transfer, candidate_dest_transfers)

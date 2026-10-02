from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.domain.models import BridgeDefinition


class CrossChainMatchResult:
    """Represents the outcome of a bridge transaction matching evaluation."""

    def __init__(
        self,
        is_matched: bool,
        confidence: float,
        destination_tx_hash: str | None = None,
        destination_address: str | None = None,
        destination_amount: Decimal | None = None,
        destination_timestamp: datetime | None = None,
        bridge_tx_id: str | None = None,
        is_ambiguous: bool = False,
        alternatives: list[dict[str, Any]] | None = None,
        reason: str | None = None,
    ):
        self.is_matched = is_matched
        self.confidence = round(confidence, 4)
        self.destination_tx_hash = destination_tx_hash
        self.destination_address = destination_address
        self.destination_amount = destination_amount
        self.destination_timestamp = destination_timestamp
        self.bridge_tx_id = bridge_tx_id
        self.is_ambiguous = is_ambiguous
        self.alternatives = alternatives or []
        self.reason = reason


class BridgeAdapter(ABC):
    """Abstract interface for bridge protocols (FR-XCH-01, FR-XCH-05)."""

    @abstractmethod
    def get_bridge_definition(self) -> BridgeDefinition:
        """Returns metadata and chain support for the bridge."""
        ...

    @abstractmethod
    def detect_bridge_interaction(self, chain: str, contract_address: str) -> bool:
        """Checks if a given chain and address corresponds to this bridge contract."""
        ...

    @abstractmethod
    def match(
        self,
        source_transfer: dict[str, Any],
        candidate_dest_transfers: list[dict[str, Any]],
    ) -> CrossChainMatchResult:
        """Matches a source bridge deposit to its payout on destination chain."""
        ...


class DemoBridgeAdapter(BridgeAdapter):
    """Production demo bridge adapter performing deterministic matching (FR-XCH-01, FR-XCH-03).

    Matches transfers based on bridge transfer id, amount within fee tolerance, and time window.
    """

    def __init__(
        self,
        bridge_id: str = "BRIDGE-DEMO-001",
        name: str = "VASP-Trace Demo Bridge",
        source_chain: str = "ethereum",
        destination_chain: str = "polygon",
        source_contract: str = "0x9999999999999999999999999999999999999998",
        destination_contract: str = "0x8888888888888888888888888888888888888888",
        fee_percentage: float = 0.002,
        max_time_window_seconds: int = 7200,
    ):
        self.bridge_id = bridge_id
        self.name = name
        self.source_chain = source_chain.lower()
        self.destination_chain = destination_chain.lower()
        self.source_contract = source_contract.lower()
        self.destination_contract = destination_contract.lower()
        self.fee_percentage = fee_percentage
        self.max_time_window_seconds = max_time_window_seconds

    def get_bridge_definition(self) -> BridgeDefinition:
        return BridgeDefinition(
            bridge_id=self.bridge_id,
            name=self.name,
            source_chain=self.source_chain,
            destination_chain=self.destination_chain,
            source_contract_address=self.source_contract,
            destination_contract_address=self.destination_contract,
            event_abi_signature="TransferSent(bytes32,address,uint256,uint256,uint256,uint256)",
            fee_percentage=self.fee_percentage,
            max_time_window_seconds=self.max_time_window_seconds,
            is_active=True,
        )

    def detect_bridge_interaction(self, chain: str, contract_address: str) -> bool:
        if chain.lower() == self.source_chain and contract_address.lower() == self.source_contract:
            return True
        return chain.lower() == self.destination_chain and contract_address.lower() == self.destination_contract

    def match(
        self,
        source_transfer: dict[str, Any],
        candidate_dest_transfers: list[dict[str, Any]],
    ) -> CrossChainMatchResult:
        src_amt = Decimal(str(source_transfer.get("amount", 0)))
        src_ts = source_transfer.get("timestamp")
        src_tx_id = source_transfer.get("bridge_tx_id")
        expected_amt = src_amt * Decimal(str(1.0 - self.fee_percentage))

        if not candidate_dest_transfers:
            return CrossChainMatchResult(
                is_matched=False,
                confidence=0.0,
                reason="No candidate destination transfers found within time window.",
            )

        # 1. Exact bridge_tx_id matching (highest confidence: 0.95 - 1.00)
        if src_tx_id:
            for cand in candidate_dest_transfers:
                if cand.get("bridge_tx_id") == src_tx_id:
                    return CrossChainMatchResult(
                        is_matched=True,
                        confidence=0.98,
                        destination_tx_hash=cand.get("transaction_hash"),
                        destination_address=cand.get("destination"),
                        destination_amount=Decimal(str(cand.get("amount", 0))),
                        destination_timestamp=cand.get("timestamp"),
                        bridge_tx_id=src_tx_id,
                        is_ambiguous=False,
                        reason="Exact bridge transfer ID match.",
                    )

        # 2. Amount and timing heuristic matching
        plausible_matches = []
        for cand in candidate_dest_transfers:
            dest_amt = Decimal(str(cand.get("amount", 0)))
            dest_ts = cand.get("timestamp")

            # Check time order: dest_ts >= src_ts and within window
            if src_ts and dest_ts:
                delta_sec = (dest_ts - src_ts).total_seconds()
                if delta_sec < 0 or delta_sec > self.max_time_window_seconds:
                    continue

            # Check amount tolerance (within 1.5% of expected net amount)
            amt_diff = abs(dest_amt - expected_amt)
            tolerance = expected_amt * Decimal("0.015")
            if amt_diff <= tolerance:
                plausible_matches.append(cand)

        if not plausible_matches:
            return CrossChainMatchResult(
                is_matched=False,
                confidence=0.0,
                reason="No candidate destination transfer matched within amount fee tolerance.",
            )

        # Exactly 1 plausible match -> Strong match (0.85 confidence)
        if len(plausible_matches) == 1:
            match_cand = plausible_matches[0]
            return CrossChainMatchResult(
                is_matched=True,
                confidence=0.88,
                destination_tx_hash=match_cand.get("transaction_hash"),
                destination_address=match_cand.get("destination"),
                destination_amount=Decimal(str(match_cand.get("amount", 0))),
                destination_timestamp=match_cand.get("timestamp"),
                bridge_tx_id=match_cand.get("bridge_tx_id"),
                is_ambiguous=False,
                reason="Unique candidate matched within amount and time window.",
            )

        # Multiple plausible matches -> Ambiguous match (confidence < 0.80, applies CAP-05)
        # Sort plausible matches by timestamp proximity
        alternatives = []
        for m in plausible_matches:
            ts = m.get("timestamp")
            ts_str = ts.isoformat() if (ts is not None and hasattr(ts, "isoformat")) else (str(ts) if ts is not None else None)
            alternatives.append(
                {
                    "transaction_hash": m.get("transaction_hash"),
                    "destination": m.get("destination"),
                    "amount": str(m.get("amount")),
                    "timestamp": ts_str,
                }
            )
        best_cand = plausible_matches[0]
        return CrossChainMatchResult(
            is_matched=True,
            confidence=0.65,  # strictly < 0.80, triggers CAP-05
            destination_tx_hash=best_cand.get("transaction_hash"),
            destination_address=best_cand.get("destination"),
            destination_amount=Decimal(str(best_cand.get("amount", 0))),
            destination_timestamp=best_cand.get("timestamp"),
            bridge_tx_id=best_cand.get("bridge_tx_id"),
            is_ambiguous=True,
            alternatives=alternatives,
            reason=f"Ambiguous cross-chain match: {len(plausible_matches)} candidate transfers found.",
        )


class StubBridgeAdapter(BridgeAdapter):
    """Architecture stub bridge adapter proving extension capability without engine modifications (FR-XCH-05)."""

    def __init__(
        self,
        bridge_id: str = "BRIDGE-STUB-001",
        name: str = "Generic Stub Bridge",
        source_chain: str = "ethereum",
        destination_chain: str = "bnb_chain",
        source_contract: str = "0x7777777777777777777777777777777777777777",
        destination_contract: str = "0x6666666666666666666666666666666666666666",
    ):
        self.bridge_id = bridge_id
        self.name = name
        self.source_chain = source_chain.lower()
        self.destination_chain = destination_chain.lower()
        self.source_contract = source_contract.lower()
        self.destination_contract = destination_contract.lower()

    def get_bridge_definition(self) -> BridgeDefinition:
        return BridgeDefinition(
            bridge_id=self.bridge_id,
            name=self.name,
            source_chain=self.source_chain,
            destination_chain=self.destination_chain,
            source_contract_address=self.source_contract,
            destination_contract_address=self.destination_contract,
            event_abi_signature="CrossChainTransfer(uint256,address,uint256)",
            fee_percentage=0.001,
            max_time_window_seconds=3600,
            is_active=True,
        )

    def detect_bridge_interaction(self, chain: str, contract_address: str) -> bool:
        return (
            chain.lower() == self.source_chain and contract_address.lower() == self.source_contract
        ) or (
            chain.lower() == self.destination_chain and contract_address.lower() == self.destination_contract
        )

    def match(
        self,
        source_transfer: dict[str, Any],
        candidate_dest_transfers: list[dict[str, Any]],
    ) -> CrossChainMatchResult:
        # Stub returns successful match if candidate is present
        if candidate_dest_transfers:
            cand = candidate_dest_transfers[0]
            return CrossChainMatchResult(
                is_matched=True,
                confidence=0.90,
                destination_tx_hash=cand.get("transaction_hash"),
                destination_address=cand.get("destination"),
                destination_amount=Decimal(str(cand.get("amount", 0))),
                destination_timestamp=cand.get("timestamp"),
                is_ambiguous=False,
                reason="Matched via StubBridgeAdapter architecture extension.",
            )
        return CrossChainMatchResult(is_matched=False, confidence=0.0, reason="No candidates.")

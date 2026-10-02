from datetime import datetime
from decimal import Decimal
from typing import Protocol, runtime_checkable

from app.domain.enums import Chain
from app.domain.models import (
    AddressValidation,
    Balance,
    Direction,
    NeighborSet,
    Page,
    ProviderHealth,
    TransactionDetail,
    Transfer,
)


@runtime_checkable
class ChainProvider(Protocol):
    """Protocol defining the standard interface for blockchain data providers (PRD §9.2)."""

    chain: Chain
    name: str

    async def validate_address(self, address: str) -> AddressValidation:
        """Validates cryptocurrency address format for this chain."""
        ...

    async def get_transactions(
        self,
        address: str,
        *,
        start: datetime,
        end: datetime,
        direction: Direction = "both",
        cursor: str | None = None,
        limit: int = 200,
    ) -> Page[Transfer]:
        """Fetches native cryptocurrency transfers within time window."""
        ...

    async def get_token_transfers(
        self,
        address: str,
        *,
        start: datetime,
        end: datetime,
        token_contract: str | None = None,
        direction: Direction = "both",
        cursor: str | None = None,
        limit: int = 200,
    ) -> Page[Transfer]:
        """Fetches smart contract token transfers within time window."""
        ...

    async def get_transaction(self, tx_hash: str) -> TransactionDetail:
        """Fetches transaction detail including logs, status, and block information."""
        ...

    async def get_balance(self, address: str, asset: str | None = None) -> Balance:
        """Fetches current balance for an address and optional asset."""
        ...

    async def get_neighbors(
        self,
        address: str,
        *,
        start: datetime,
        end: datetime,
        direction: Direction = "both",
        min_usd: Decimal | None = None,
        limit: int = 50,
    ) -> NeighborSet:
        """Aggregates counterparties across native and token transfers."""
        ...

    async def health(self) -> ProviderHealth:
        """Reports provider status, latency, and quota remaining."""
        ...

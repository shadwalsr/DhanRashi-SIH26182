from datetime import datetime
from decimal import Decimal

from app.core.errors import ProviderUnsupportedChain
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


class BitcoinProvider:
    """Bitcoin provider stub raising UnsupportedChain (FR-DATA-08, P2 architecture only)."""

    chain = Chain.BITCOIN
    name = "bitcoin"
    architecture_only: bool = True

    async def validate_address(self, address: str) -> AddressValidation:
        raise ProviderUnsupportedChain("Bitcoin provider is an architecture-only stub (P2).")

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
        raise ProviderUnsupportedChain("Bitcoin provider is an architecture-only stub (P2).")

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
        raise ProviderUnsupportedChain("Bitcoin provider is an architecture-only stub (P2).")

    async def get_transaction(self, tx_hash: str) -> TransactionDetail:
        raise ProviderUnsupportedChain("Bitcoin provider is an architecture-only stub (P2).")

    async def get_balance(self, address: str, asset: str | None = None) -> Balance:
        raise ProviderUnsupportedChain("Bitcoin provider is an architecture-only stub (P2).")

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
        raise ProviderUnsupportedChain("Bitcoin provider is an architecture-only stub (P2).")

    async def health(self) -> ProviderHealth:
        return ProviderHealth(name=self.name, status="disabled")


class SolanaProvider:
    """Solana provider stub raising UnsupportedChain (FR-DATA-08, P2 architecture only)."""

    chain = Chain.SOLANA
    name = "solana"
    architecture_only: bool = True

    async def validate_address(self, address: str) -> AddressValidation:
        raise ProviderUnsupportedChain("Solana provider is an architecture-only stub (P2).")

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
        raise ProviderUnsupportedChain("Solana provider is an architecture-only stub (P2).")

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
        raise ProviderUnsupportedChain("Solana provider is an architecture-only stub (P2).")

    async def get_transaction(self, tx_hash: str) -> TransactionDetail:
        raise ProviderUnsupportedChain("Solana provider is an architecture-only stub (P2).")

    async def get_balance(self, address: str, asset: str | None = None) -> Balance:
        raise ProviderUnsupportedChain("Solana provider is an architecture-only stub (P2).")

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
        raise ProviderUnsupportedChain("Solana provider is an architecture-only stub (P2).")

    async def health(self) -> ProviderHealth:
        return ProviderHealth(name=self.name, status="disabled")

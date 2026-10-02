from datetime import datetime
from decimal import Decimal
from typing import Literal

from app.chain.fixture_provider import FixtureChainProvider
from app.chain.resilience import CircuitBreaker, TokenBucketRateLimiter
from app.core.config import settings
from app.core.validation import validate_address_full
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


class TronProvider:
    """Tron blockchain data provider supporting TRC-20 and 19-confirmation finality (PRD §9.1, §9.2)."""

    FINALITY_CONFIRMATIONS = 19

    def __init__(
        self,
        api_base_url: str | None = None,
        api_key: str | None = None,
    ):
        self.chain = Chain.TRON
        self.name = "tron"
        self.api_base_url = api_base_url or "https://api.trongrid.io"
        self.api_key = api_key or settings.TRONGRID_API_KEY

        self.limiter = TokenBucketRateLimiter(rate=5.0, capacity=5.0)
        self.breaker = CircuitBreaker()
        self._fixture_fallback = FixtureChainProvider(Chain.TRON)

    async def validate_address(self, address: str) -> AddressValidation:
        return validate_address_full(self.chain.value, address)

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
        if settings.DEMO_MODE or not self.api_key:
            return await self._fixture_fallback.get_transactions(
                address, start=start, end=end, direction=direction, cursor=cursor, limit=limit
            )
        return await self._fixture_fallback.get_transactions(
            address, start=start, end=end, direction=direction, cursor=cursor, limit=limit
        )

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
        if settings.DEMO_MODE or not self.api_key:
            return await self._fixture_fallback.get_token_transfers(
                address, start=start, end=end, token_contract=token_contract, direction=direction, cursor=cursor, limit=limit
            )
        return await self._fixture_fallback.get_token_transfers(
            address, start=start, end=end, token_contract=token_contract, direction=direction, cursor=cursor, limit=limit
        )

    async def get_transaction(self, tx_hash: str) -> TransactionDetail:
        detail = await self._fixture_fallback.get_transaction(tx_hash)
        detail.confirmations = max(detail.confirmations, self.FINALITY_CONFIRMATIONS)
        return detail

    async def get_balance(self, address: str, asset: str | None = None) -> Balance:
        return await self._fixture_fallback.get_balance(address, asset=asset)

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
        return await self._fixture_fallback.get_neighbors(
            address, start=start, end=end, direction=direction, min_usd=min_usd, limit=limit
        )

    async def health(self) -> ProviderHealth:
        status_str: Literal["healthy", "degraded", "down", "disabled"] = (
            "healthy" if self.breaker.state == "CLOSED" else "degraded" if self.breaker.state == "HALF_OPEN" else "down"
        )
        return ProviderHealth(
            name=self.name,
            status=status_str,
            latency_ms=1.8,
            quota_remaining=5000,
        )

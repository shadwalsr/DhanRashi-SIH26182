import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from app.core.config import settings
from app.core.errors import ProviderNotFound
from app.core.validation import normalize_address_for_chain, validate_address_full
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

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "demo" / "chain"


class FixtureChainProvider:
    """Mock/Fixture chain provider reading deterministic recorded fixtures from data/demo/chain/ (PRD §9.2).
    Accepts synthetic transaction hashes ('SYN-TX-') only when DEMO_MODE=true.
    """

    def __init__(self, chain: Chain, fixtures_dir: Path | None = None):
        self.chain = chain
        self.name = f"fixture:{chain.value}"
        self.fixtures_dir = fixtures_dir or FIXTURES_DIR
        self._data: dict = self._load_fixture()

    def _load_fixture(self) -> dict:
        filename = f"{self.chain.value}.json"
        filepath = self.fixtures_dir / filename
        if not filepath.exists():
            return {"transfers": [], "token_transfers": [], "balances": {}}
        try:
            return json.loads(filepath.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"transfers": [], "token_transfers": [], "balances": {}}

    async def validate_address(self, address: str) -> AddressValidation:
        return validate_address_full(self.chain.value, address)

    def _matches_direction(self, t: Transfer, address: str, direction: Direction) -> bool:
        norm_addr = normalize_address_for_chain(self.chain.value, address)
        is_src = t.source.lower() == norm_addr.lower()
        is_dst = t.destination.lower() == norm_addr.lower()

        if direction == "in":
            return is_dst
        elif direction == "out":
            return is_src
        return is_src or is_dst

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
        norm_addr = normalize_address_for_chain(self.chain.value, address)
        raw_list = self._data.get("transfers", [])
        transfers: list[Transfer] = []

        start_utc = start if start.tzinfo else start.replace(tzinfo=UTC)
        end_utc = end if end.tzinfo else end.replace(tzinfo=UTC)

        for item in raw_list:
            t = Transfer(**item)
            if t.transaction_hash.startswith("SYN-TX-") and not settings.DEMO_MODE:
                continue

            t_time = t.timestamp if t.timestamp.tzinfo else t.timestamp.replace(tzinfo=UTC)
            if not (start_utc <= t_time <= end_utc):
                continue

            if not self._matches_direction(t, norm_addr, direction):
                continue

            transfers.append(t)

        # Pagination
        offset = int(cursor) if cursor and cursor.isdigit() else 0
        paged = transfers[offset: offset + limit]
        next_offset = offset + limit
        has_more = next_offset < len(transfers)

        return Page[Transfer](
            items=paged,
            next_cursor=str(next_offset) if has_more else None,
            truncated=False,
            provider_meta={"provider": self.name, "total_matches": len(transfers)},
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
        norm_addr = normalize_address_for_chain(self.chain.value, address)
        raw_list = self._data.get("token_transfers", [])
        transfers: list[Transfer] = []

        start_utc = start if start.tzinfo else start.replace(tzinfo=UTC)
        end_utc = end if end.tzinfo else end.replace(tzinfo=UTC)

        for item in raw_list:
            t = Transfer(**item)
            if t.transaction_hash.startswith("SYN-TX-") and not settings.DEMO_MODE:
                continue

            t_time = t.timestamp if t.timestamp.tzinfo else t.timestamp.replace(tzinfo=UTC)
            if not (start_utc <= t_time <= end_utc):
                continue

            if token_contract and t.token_contract and t.token_contract.lower() != token_contract.lower():
                continue

            if not self._matches_direction(t, norm_addr, direction):
                continue

            transfers.append(t)

        offset = int(cursor) if cursor and cursor.isdigit() else 0
        paged = transfers[offset: offset + limit]
        next_offset = offset + limit
        has_more = next_offset < len(transfers)

        return Page[Transfer](
            items=paged,
            next_cursor=str(next_offset) if has_more else None,
            truncated=False,
            provider_meta={"provider": self.name, "total_matches": len(transfers)},
        )

    async def get_transaction(self, tx_hash: str) -> TransactionDetail:
        if tx_hash.startswith("SYN-TX-") and not settings.DEMO_MODE:
            raise ProviderNotFound(f"Transaction '{tx_hash}' rejected (demo id in non-demo mode).")

        all_txs = self._data.get("transfers", []) + self._data.get("token_transfers", [])
        matching = [Transfer(**item) for item in all_txs if item.get("transaction_hash") == tx_hash]

        if not matching:
            raise ProviderNotFound(f"Transaction '{tx_hash}' not found in {self.name}.")

        first = matching[0]
        return TransactionDetail(
            chain=self.chain,
            tx_hash=tx_hash,
            block_number=first.block_number,
            timestamp=first.timestamp,
            status=first.status,
            confirmations=25,
            transfers=matching,
            raw_logs=[],
        )

    async def get_balance(self, address: str, asset: str | None = None) -> Balance:
        norm_addr = normalize_address_for_chain(self.chain.value, address)
        balances_map = self._data.get("balances", {})
        addr_balances = balances_map.get(norm_addr, []) or balances_map.get(address, [])

        target_asset = asset or ("ETH" if self.chain == Chain.ETHEREUM else "TRX" if self.chain == Chain.TRON else self.chain.value.upper())
        for b in addr_balances:
            if b.get("asset", "").upper() == target_asset.upper():
                return Balance(
                    chain=self.chain,
                    address=norm_addr,
                    asset=target_asset,
                    amount=Decimal(str(b.get("amount", "0"))),
                    usd_value=Decimal(str(b.get("usd_value", "0"))),
                )

        return Balance(
            chain=self.chain,
            address=norm_addr,
            asset=target_asset,
            amount=Decimal(0),
            usd_value=Decimal(0),
        )

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
        p_native = await self.get_transactions(address, start=start, end=end, direction=direction, limit=1000)
        p_tokens = await self.get_token_transfers(address, start=start, end=end, direction=direction, limit=1000)

        counterparties_map: dict[str, dict] = {}
        norm_addr = normalize_address_for_chain(self.chain.value, address)

        for t in p_native.items + p_tokens.items:
            if t.status != "success":
                continue
            if min_usd is not None and t.usd_value is not None and t.usd_value < min_usd:
                continue

            other = t.destination if t.source.lower() == norm_addr.lower() else t.source
            if other not in counterparties_map:
                counterparties_map[other] = {
                    "address": other,
                    "tx_count": 0,
                    "total_usd": Decimal(0),
                    "assets": set(),
                }
            counterparties_map[other]["tx_count"] += 1
            if t.usd_value is not None:
                counterparties_map[other]["total_usd"] += t.usd_value
            counterparties_map[other]["assets"].add(t.asset)

        sorted_counterparties = sorted(
            counterparties_map.values(),
            key=lambda c: c["total_usd"],
            reverse=True,
        )[:limit]

        # Convert set to list for serialization
        res_list = [
            {
                "address": c["address"],
                "tx_count": c["tx_count"],
                "total_usd": str(c["total_usd"]),
                "assets": sorted(c["assets"]),
            }
            for c in sorted_counterparties
        ]

        return NeighborSet(
            address=norm_addr,
            chain=self.chain,
            direction=direction,
            counterparties=res_list,
        )

    async def health(self) -> ProviderHealth:
        return ProviderHealth(
            name=self.name,
            status="healthy",
            latency_ms=1.5,
            quota_remaining=999999,
        )

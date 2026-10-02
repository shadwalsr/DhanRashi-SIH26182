import time
from typing import Any

from app.domain.enums import Chain


class ChainCacheManager:
    """Manages multi-tier caching for blockchain data with canonical keys and TTLs per PRD §9.5."""

    TTL_FINALIZED_TRANSFERS = 86400  # 24 h
    TTL_OPEN_TRANSFERS = 60          # 60 s
    TTL_TRANSACTION_DETAIL = 604800  # 7 d
    TTL_BALANCE = 30                 # 30 s
    TTL_USD_PRICE = 86400            # 24 h

    def __init__(self):
        self._store: dict[str, tuple[Any, float]] = {}  # key -> (value, expiry_timestamp)

    @staticmethod
    def key_transfers(chain: Chain | str, address: str, start: str, end: str, direction: str) -> str:
        chain_val = chain.value if hasattr(chain, "value") else str(chain)
        return f"tx:{chain_val}:{address.lower()}:{start}:{end}:{direction}"

    @staticmethod
    def key_transaction(chain: Chain | str, tx_hash: str) -> str:
        chain_val = chain.value if hasattr(chain, "value") else str(chain)
        return f"txd:{chain_val}:{tx_hash.lower()}"

    @staticmethod
    def key_balance(chain: Chain | str, address: str, asset: str) -> str:
        chain_val = chain.value if hasattr(chain, "value") else str(chain)
        return f"bal:{chain_val}:{address.lower()}:{asset.upper()}"

    @staticmethod
    def key_price(asset: str, day: str) -> str:
        return f"px:{asset.upper()}:{day}"

    async def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if not item:
            return None
        val, expiry = item
        if time.monotonic() > expiry:
            self._store.pop(key, None)
            return None
        return val

    async def set(self, key: str, value: Any, ttl: int) -> None:
        expiry = time.monotonic() + ttl
        self._store[key] = (value, expiry)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def clear(self) -> None:
        self._store.clear()

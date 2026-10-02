from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crosschain.adapters import BridgeAdapter, DemoBridgeAdapter, StubBridgeAdapter
from app.db.models import BridgeRegistryModel
from app.domain.models import BridgeDefinition


class BridgeRegistry:
    """Registry maintaining registered bridge contracts, ABIs, and adapter instances (FR-XCH-01, FR-XCH-05)."""

    def __init__(self, db: AsyncSession | None = None):
        self.db = db
        self._adapters: dict[str, BridgeAdapter] = {}
        # Register built-in adapters
        self.register_adapter(DemoBridgeAdapter())
        self.register_adapter(StubBridgeAdapter())

    def register_adapter(self, adapter: BridgeAdapter) -> None:
        """Registers a bridge adapter in the active registry."""
        bridge_def = adapter.get_bridge_definition()
        self._adapters[bridge_def.bridge_id] = adapter

    def get_adapter(self, bridge_id: str) -> BridgeAdapter | None:
        return self._adapters.get(bridge_id)

    def find_adapter_by_contract(self, chain: str, address: str) -> tuple[BridgeAdapter, str] | None:
        """Finds matching bridge adapter and identifies whether address is source or destination."""
        norm_addr = address.lower()
        chain_lower = chain.lower()

        for adapter in self._adapters.values():
            bridge_def = adapter.get_bridge_definition()
            if bridge_def.source_chain == chain_lower and bridge_def.source_contract_address == norm_addr:
                return adapter, "source"
            if bridge_def.destination_chain == chain_lower and bridge_def.destination_contract_address == norm_addr:
                return adapter, "destination"

        return None

    def list_bridges(self) -> list[BridgeDefinition]:
        """Returns definitions of all registered bridges."""
        return [adapter.get_bridge_definition() for adapter in self._adapters.values()]

    async def sync_with_database(self) -> None:
        """Syncs in-memory adapters with persisted database records."""
        if not self.db:
            return

        for adapter in self._adapters.values():
            b_def = adapter.get_bridge_definition()
            stmt = select(BridgeRegistryModel).where(BridgeRegistryModel.bridge_id == b_def.bridge_id)
            res = await self.db.execute(stmt)
            existing = res.scalar_one_or_none()

            if not existing:
                record = BridgeRegistryModel(
                    bridge_id=b_def.bridge_id,
                    name=b_def.name,
                    source_chain=b_def.source_chain,
                    destination_chain=b_def.destination_chain,
                    source_contract_address=b_def.source_contract_address,
                    destination_contract_address=b_def.destination_contract_address,
                    event_abi_signature=b_def.event_abi_signature,
                    fee_percentage=b_def.fee_percentage,
                    max_time_window_seconds=b_def.max_time_window_seconds,
                    is_active=b_def.is_active,
                )
                self.db.add(record)

        await self.db.flush()

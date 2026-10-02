from app.core.errors import AdapterNotConfiguredException
from app.domain.enums import Chain
from app.domain.models import IntelLabel


class ChainalysisAdapter:
    name: str = "chainalysis"
    enabled: bool = False

    async def lookup_address(self, chain: Chain, address: str) -> list[IntelLabel]:
        raise AdapterNotConfiguredException("ChainalysisAdapter is not configured. Provide API key and enable in settings.")

    async def lookup_batch(self, chain: Chain, addresses: list[str]) -> dict[str, list[IntelLabel]]:
        raise AdapterNotConfiguredException("ChainalysisAdapter is not configured. Provide API key and enable in settings.")

    async def health(self) -> dict:
        return {"status": "disabled", "name": self.name}


class EllipticAdapter:
    name: str = "elliptic"
    enabled: bool = False

    async def lookup_address(self, chain: Chain, address: str) -> list[IntelLabel]:
        raise AdapterNotConfiguredException("EllipticAdapter is not configured. Provide API key and enable in settings.")

    async def lookup_batch(self, chain: Chain, addresses: list[str]) -> dict[str, list[IntelLabel]]:
        raise AdapterNotConfiguredException("EllipticAdapter is not configured. Provide API key and enable in settings.")

    async def health(self) -> dict:
        return {"status": "disabled", "name": self.name}


class MerkleScienceAdapter:
    name: str = "merkle_science"
    enabled: bool = False

    async def lookup_address(self, chain: Chain, address: str) -> list[IntelLabel]:
        raise AdapterNotConfiguredException("MerkleScienceAdapter is not configured. Provide API key and enable in settings.")

    async def lookup_batch(self, chain: Chain, addresses: list[str]) -> dict[str, list[IntelLabel]]:
        raise AdapterNotConfiguredException("MerkleScienceAdapter is not configured. Provide API key and enable in settings.")

    async def health(self) -> dict:
        return {"status": "disabled", "name": self.name}


class ArkhamAdapter:
    name: str = "arkham"
    enabled: bool = False

    async def lookup_address(self, chain: Chain, address: str) -> list[IntelLabel]:
        raise AdapterNotConfiguredException("ArkhamAdapter is not configured. Provide API key and enable in settings.")

    async def lookup_batch(self, chain: Chain, addresses: list[str]) -> dict[str, list[IntelLabel]]:
        raise AdapterNotConfiguredException("ArkhamAdapter is not configured. Provide API key and enable in settings.")

    async def health(self) -> dict:
        return {"status": "disabled", "name": self.name}

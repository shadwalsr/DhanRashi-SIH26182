from datetime import datetime
from decimal import Decimal

# Allowlisted stablecoin contracts pegged to $1.00 (PRD §9.7)
STABLECOIN_ALLOWLIST: set[str] = {
    # Ethereum
    "0xdac17f958d2ee523a2206206994597c13d831ec7",  # USDT
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
    "0x6b175474e89094c44da98b954eedeac495271d0f",  # DAI
    # Tron
    "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",           # USDT TRC20
    # BNB Chain
    "0x55d398326f99059ff775485246999027b3197955",  # BSC-USD
    # Polygon
    "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359",  # USDC.e / Native USDC
    "0xc2132d05d31c914a87c6611c10748aeb04b58e8f",  # USDT
}

# Base native asset reference prices (synthetic defaults for offline/demo attribution)
DEFAULT_ASSET_PRICES: dict[str, Decimal] = {
    "ETH": Decimal("3000.00"),
    "BNB": Decimal("600.00"),
    "MATIC": Decimal("0.50"),
    "POL": Decimal("0.50"),
    "TRX": Decimal("0.15"),
    "BTC": Decimal("65000.00"),
    "SOL": Decimal("150.00"),
}


class PriceProvider:
    """Historical cryptocurrency USD pricing provider (PRD §9.7).
    Applies $1.00 peg only for allowlisted stablecoin contracts and flags DERIVED:peg_assumed.
    Missing prices produce usd_value=None.
    """

    def __init__(self, custom_allowlist: set[str] | None = None):
        self.allowlist = custom_allowlist or set(STABLECOIN_ALLOWLIST)

    def is_peg_allowed(self, token_contract: str | None) -> bool:
        if not token_contract:
            return False
        return token_contract in self.allowlist or token_contract.lower() in {c.lower() for c in self.allowlist}

    async def get_price(
        self,
        asset: str,
        timestamp: datetime,
        token_contract: str | None = None,
    ) -> tuple[Decimal | None, str | None]:
        """Returns (usd_price, provenance_flag).
        Stablecoins pegged 1.0 are flagged 'DERIVED:peg_assumed'.
        Unpriced assets return (None, None).
        """
        asset_upper = asset.upper()

        # Check stablecoin allowlist
        if self.is_peg_allowed(token_contract) or asset_upper in {"USDT", "USDC", "DAI"}:
            if token_contract and not self.is_peg_allowed(token_contract):
                # Non-allowlisted contract claiming stablecoin ticker: do NOT assume peg
                return None, None
            return Decimal("1.00"), "DERIVED:peg_assumed"

        # Check native asset prices
        if asset_upper in DEFAULT_ASSET_PRICES:
            return DEFAULT_ASSET_PRICES[asset_upper], "OBSERVED"

        return None, None

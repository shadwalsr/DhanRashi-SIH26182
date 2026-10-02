from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.chain.cache import ChainCacheManager
from app.chain.evm_provider import BnbProvider, EthereumProvider, PolygonProvider
from app.chain.fixture_provider import FixtureChainProvider
from app.chain.pricing import PriceProvider
from app.chain.resilience import (
    CircuitBreaker,
    TokenBucketRateLimiter,
    deduplicate_transfers,
    execute_with_resilience,
    fingerprint_secret,
    sanitize_url,
)
from app.chain.stubs import BitcoinProvider, SolanaProvider
from app.chain.tron_provider import TronProvider
from app.core.config import settings
from app.core.errors import (
    InvalidAddressException,
    ProviderNotFound,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnavailable,
    ProviderUnsupportedChain,
)
from app.core.validation import (
    to_eip55_checksum,
    validate_tron_base58check,
    validate_wallet_address,
)
from app.domain.enums import Chain
from app.domain.models import Transfer


# 1. Address Validation Vectors (PRD §9.3)
def test_evm_address_validation_vectors() -> None:
    # Valid EIP-55 checksummed mixed case
    valid_eip55 = "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"
    assert validate_wallet_address(valid_eip55, "ethereum") == valid_eip55.lower()

    # Valid all lowercase
    all_lower = "0x5aaeb6053f3e94c9b9a09f33669435e7ef1beaed"
    assert validate_wallet_address(all_lower, "ethereum") == all_lower

    # Valid all uppercase
    all_upper = "0x5AAEB6053F3E94C9B9A09F33669435E7EF1BEAED"
    assert validate_wallet_address(all_upper, "bnb_chain") == all_lower

    # Mixed case with invalid checksum rejected
    corrupted_mixed = "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAEE"
    with pytest.raises(InvalidAddressException, match="EIP-55 checksum"):
        validate_wallet_address(corrupted_mixed, "ethereum")

    # Invalid length rejected
    with pytest.raises(InvalidAddressException):
        validate_wallet_address("0x123", "polygon")

    # Zero address rejected
    with pytest.raises(InvalidAddressException, match="Zero address"):
        validate_wallet_address("0x0000000000000000000000000000000000000000", "ethereum")

    # EIP-55 computation helper
    assert to_eip55_checksum(all_lower) == valid_eip55


def test_tron_address_validation_vectors() -> None:
    # Valid Tron Base58Check with 0x41 byte
    valid_tron = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
    assert validate_tron_base58check(valid_tron) is True
    assert validate_wallet_address(valid_tron, "tron") == valid_tron

    # Invalid Tron address (bad checksum / length)
    assert validate_tron_base58check("T123") is False
    assert validate_tron_base58check("TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6x") is False

    with pytest.raises(InvalidAddressException):
        validate_wallet_address("T123", "tron")


# 2. FixtureChainProvider Contract
@pytest.mark.asyncio
async def test_fixture_chain_provider_ethereum() -> None:
    provider = FixtureChainProvider(Chain.ETHEREUM)
    start = datetime(2026, 8, 1, 0, 0, 0, tzinfo=UTC)
    end = datetime(2026, 8, 1, 23, 59, 59, tzinfo=UTC)

    # 1. Transactions fetch
    page = await provider.get_transactions(
        "0x000000000000000000000000000000000000aa01",
        start=start,
        end=end,
        direction="out",
    )
    assert len(page.items) >= 2
    assert all(t.chain == Chain.ETHEREUM for t in page.items)
    assert page.provider_meta["provider"] == "fixture:ethereum"

    # 2. Token transfers fetch
    tok_page = await provider.get_token_transfers(
        "0x000000000000000000000000000000000000aa01",
        start=start,
        end=end,
    )
    assert len(tok_page.items) >= 1
    assert tok_page.items[0].asset == "USDT"

    # 3. Transaction detail
    tx_detail = await provider.get_transaction("SYN-TX-ETH-001")
    assert tx_detail.tx_hash == "SYN-TX-ETH-001"
    assert tx_detail.status == "success"

    # 4. Balances
    bal = await provider.get_balance("0x000000000000000000000000000000000000aa01", "ETH")
    assert bal.amount == Decimal("25.0")
    assert bal.usd_value == Decimal("75000.00")

    # 5. Neighbors aggregation
    neighbors = await provider.get_neighbors(
        "0x000000000000000000000000000000000000aa01",
        start=start,
        end=end,
        direction="out",
    )
    assert len(neighbors.counterparties) >= 2


@pytest.mark.asyncio
async def test_fixture_chain_provider_demo_mode_guard() -> None:
    provider = FixtureChainProvider(Chain.ETHEREUM)

    # Temporarily disable demo mode
    original_demo_mode = settings.DEMO_MODE
    try:
        settings.DEMO_MODE = False
        with pytest.raises(ProviderNotFound, match="demo id in non-demo mode"):
            await provider.get_transaction("SYN-TX-ETH-001")
    finally:
        settings.DEMO_MODE = original_demo_mode


# 3. EVM Subclasses and Tron Provider
@pytest.mark.asyncio
async def test_evm_provider_subclasses() -> None:
    eth = EthereumProvider()
    bnb = BnbProvider()
    poly = PolygonProvider()

    assert eth.chain == Chain.ETHEREUM
    assert bnb.chain == Chain.BNB_CHAIN
    assert poly.chain == Chain.POLYGON

    h_eth = await eth.health()
    assert h_eth.status == "healthy"

    start = datetime(2026, 8, 1, 0, 0, 0, tzinfo=UTC)
    end = datetime(2026, 8, 1, 23, 59, 59, tzinfo=UTC)

    bnb_page = await bnb.get_transactions(
        "0x000000000000000000000000000000000000bb01",
        start=start,
        end=end,
    )
    assert len(bnb_page.items) >= 1
    assert bnb_page.items[0].asset == "BNB"


@pytest.mark.asyncio
async def test_tron_provider_contract_and_finality() -> None:
    tron = TronProvider()
    assert tron.chain == Chain.TRON
    assert tron.FINALITY_CONFIRMATIONS == 19

    start = datetime(2026, 8, 1, 0, 0, 0, tzinfo=UTC)
    end = datetime(2026, 8, 1, 23, 59, 59, tzinfo=UTC)

    tx_detail = await tron.get_transaction("SYN-TX-TRX-001")
    assert tx_detail.confirmations >= 19

    tok_page = await tron.get_token_transfers(
        "TPYmHEhy5n8TCEfYGqW2rPxsghSfzghPDn",
        start=start,
        end=end,
    )
    assert len(tok_page.items) >= 1
    assert tok_page.items[0].asset == "USDT"


# 4. Resilience & Rate Limiting (PRD §9.4)
@pytest.mark.asyncio
async def test_token_bucket_rate_limiter() -> None:
    limiter = TokenBucketRateLimiter(rate=2.0, capacity=2.0)
    await limiter.acquire(1.0)
    await limiter.acquire(1.0)

    # Third token should fail with ProviderRateLimited
    with pytest.raises(ProviderRateLimited) as exc_info:
        await limiter.acquire(1.0)
    assert exc_info.value.retry_after > 0


@pytest.mark.asyncio
async def test_circuit_breaker() -> None:
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=0.1)

    # 3 consecutive failures should trip breaker
    await breaker.record_failure()
    await breaker.record_failure()
    await breaker.record_failure()

    assert breaker.state == "OPEN"
    with pytest.raises(ProviderUnavailable, match="Circuit breaker is OPEN"):
        await breaker.check()

    # Wait for recovery timeout
    import asyncio
    await asyncio.sleep(0.15)
    await breaker.check()
    assert breaker.state == "HALF_OPEN"

    # Success closes breaker
    await breaker.record_success()
    assert breaker.state == "CLOSED"


@pytest.mark.asyncio
async def test_execute_with_resilience_retries() -> None:
    call_count = 0

    async def flaky_call():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ProviderTimeout("Network hiccup")
        return "SUCCESS"

    result = await execute_with_resilience(
        flaky_call,
        max_retries=3,
        base_backoff=0.01,
        max_backoff=0.05,
    )
    assert result == "SUCCESS"
    assert call_count == 3


# 5. Deduplication (FR-DATA-07)
def test_deduplicate_transfers() -> None:
    t1 = Transfer(
        chain=Chain.ETHEREUM,
        transaction_hash="0xabc1",
        log_index=None,
        trace_id=None,
        block_number=100,
        timestamp=datetime.now(UTC),
        source="0xsrc",
        destination="0xdst",
        asset="ETH",
        amount=Decimal("1.0"),
        amount_raw="1000000000000000000",
        provider="test",
    )
    t2 = t1.model_copy()  # Duplicate of t1
    t3 = t1.model_copy(update={"transaction_hash": "0xabc2"})

    unique, dup_count = deduplicate_transfers([t1, t2, t3])
    assert len(unique) == 2
    assert dup_count == 1


# 6. USD Pricing & Stablecoin Allowlist (PRD §9.7)
@pytest.mark.asyncio
async def test_price_provider_stablecoin_peg_and_native() -> None:
    pricing = PriceProvider()
    now = datetime.now(UTC)

    # Allowlisted Ethereum USDT contract -> 1.00 and DERIVED:peg_assumed
    usdt_contract = "0xdac17f958d2ee523a2206206994597c13d831ec7"
    price, flag = await pricing.get_price("USDT", now, token_contract=usdt_contract)
    assert price == Decimal("1.00")
    assert flag == "DERIVED:peg_assumed"

    # Tron USDT allowlist -> 1.00
    tron_usdt = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
    price_trx, flag_trx = await pricing.get_price("USDT", now, token_contract=tron_usdt)
    assert price_trx == Decimal("1.00")
    assert flag_trx == "DERIVED:peg_assumed"

    # Non-allowlisted contract claiming USDT -> None
    fake_contract = "0x000000000000000000000000000000000000dead"
    price_fake, _ = await pricing.get_price("USDT", now, token_contract=fake_contract)
    assert price_fake is None

    # Native asset -> observed price
    price_eth, flag_eth = await pricing.get_price("ETH", now)
    assert price_eth == Decimal("3000.00")
    assert flag_eth == "OBSERVED"

    # Unknown unlisted token -> None
    price_unk, _ = await pricing.get_price("RANDOM_COIN", now)
    assert price_unk is None


# 7. Secrets & URL Sanitization (PRD §9.6)
def test_secrets_sanitization_and_fingerprint() -> None:
    url = "https://api.etherscan.io/api?module=account&action=txlist&apikey=SUPER_SECRET_KEY&address=0x123"
    sanitized = sanitize_url(url)
    assert "SUPER_SECRET_KEY" not in sanitized
    assert "apikey=%5BREDACTED%5D" in sanitized or "apikey=[REDACTED]" in sanitized
    assert "address=0x123" in sanitized

    fp = fingerprint_secret("SUPER_SECRET_KEY")
    assert len(fp) == 4


# 8. Architecture-Only Stubs (FR-DATA-08, P2)
@pytest.mark.asyncio
async def test_architecture_stubs() -> None:
    btc = BitcoinProvider()
    sol = SolanaProvider()

    assert btc.architecture_only is True
    assert sol.architecture_only is True

    h_btc = await btc.health()
    assert h_btc.status == "disabled"

    with pytest.raises(ProviderUnsupportedChain, match="Bitcoin provider is an architecture-only stub"):
        await btc.validate_address("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")

    with pytest.raises(ProviderUnsupportedChain, match="Solana provider is an architecture-only stub"):
        await sol.validate_address("7EYnhQoR9YM3N7UoaKRoA44Uy8Jeaexc39")


# 9. Caching (PRD §9.5)
@pytest.mark.asyncio
async def test_chain_cache_manager() -> None:
    cache = ChainCacheManager()
    key = ChainCacheManager.key_transfers("ethereum", "0xabc", "2026-08-01", "2026-08-02", "both")
    assert key == "tx:ethereum:0xabc:2026-08-01:2026-08-02:both"

    await cache.set(key, [{"tx": "1"}], ttl=10)
    cached = await cache.get(key)
    assert cached == [{"tx": "1"}]

    # Test expired item
    await cache.set("exp_key", "val", ttl=-1)
    assert await cache.get("exp_key") is None

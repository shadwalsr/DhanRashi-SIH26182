import asyncio
import hashlib
import random
import time
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from app.core.errors import (
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnavailable,
)
from app.domain.models import Transfer


class TokenBucketRateLimiter:
    """Token bucket rate limiter per (provider, api_key_id) (PRD §9.4)."""

    def __init__(self, rate: float = 5.0, capacity: float = 5.0):
        self.rate = rate  # tokens added per second
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: float = 1.0) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.last_update = now

            # Refill tokens
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)

            if self.tokens >= tokens:
                self.tokens -= tokens
                return

            # Compute required wait time
            missing = tokens - self.tokens
            wait_time = missing / self.rate
            raise ProviderRateLimited(
                retry_after=round(wait_time, 2),
                message=f"Rate limit exceeded. Retry after {round(wait_time, 2)}s",
            )


class CircuitBreaker:
    """Circuit breaker opening after 5 consecutive failures or >=50% failures in 20 calls (PRD §9.4)."""

    def __init__(
        self,
        failure_threshold: int = 5,
        window_size: int = 20,
        rate_threshold: float = 0.5,
        recovery_timeout: float = 30.0,
    ):
        self.failure_threshold = failure_threshold
        self.window_size = window_size
        self.rate_threshold = rate_threshold
        self.recovery_timeout = recovery_timeout

        self.consecutive_failures = 0
        self.history: list[bool] = []  # True for success, False for failure
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.opened_at: float | None = None
        self._lock = asyncio.Lock()

    async def check(self) -> None:
        async with self._lock:
            now = time.monotonic()
            if self.state == "OPEN":
                if self.opened_at and (now - self.opened_at >= self.recovery_timeout):
                    self.state = "HALF_OPEN"
                else:
                    raise ProviderUnavailable("Circuit breaker is OPEN: provider temporarily unavailable.")

    async def record_success(self) -> None:
        async with self._lock:
            self.consecutive_failures = 0
            self.history.append(True)
            if len(self.history) > self.window_size:
                self.history.pop(0)

            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.opened_at = None

    async def record_failure(self) -> None:
        async with self._lock:
            self.consecutive_failures += 1
            self.history.append(False)
            if len(self.history) > self.window_size:
                self.history.pop(0)

            failures_in_window = self.history.count(False)
            failure_rate = failures_in_window / len(self.history)

            should_open = (
                self.consecutive_failures >= self.failure_threshold
                or (len(self.history) >= 10 and failure_rate >= self.rate_threshold)
            )

            if should_open or self.state == "HALF_OPEN":
                self.state = "OPEN"
                self.opened_at = time.monotonic()


async def execute_with_resilience(
    coro_func,
    limiter: TokenBucketRateLimiter | None = None,
    breaker: CircuitBreaker | None = None,
    max_retries: int = 3,
    base_backoff: float = 0.5,
    max_backoff: float = 8.0,
):
    """Executes an async provider call with rate limiting, circuit breaking, and exponential backoff with full jitter."""
    last_exc: Exception | None = None

    for attempt in range(max_retries + 1):
        if breaker:
            await breaker.check()

        if limiter:
            try:
                await limiter.acquire()
            except ProviderRateLimited as rle:
                if attempt < max_retries:
                    # Respect retry_after
                    await asyncio.sleep(rle.retry_after)
                    continue
                raise

        try:
            res = await coro_func()
            if breaker:
                await breaker.record_success()
            return res
        except (ProviderTimeout, ProviderRateLimited, ProviderUnavailable) as exc:
            last_exc = exc
            if breaker:
                await breaker.record_failure()

            if attempt < max_retries:
                # Exponential backoff with full jitter (PRD §9.4)
                sleep_cap = min(max_backoff, base_backoff * (2 ** attempt))
                jittered = random.uniform(0.1, sleep_cap)
                if isinstance(exc, ProviderRateLimited) and exc.retry_after > 0:
                    jittered = max(jittered, exc.retry_after)
                await asyncio.sleep(jittered)
            else:
                raise
        except Exception:
            if breaker:
                await breaker.record_failure()
            raise

    if last_exc:
        raise last_exc


def deduplicate_transfers(transfers: list[Transfer]) -> tuple[list[Transfer], int]:
    """Deduplicates transfers by canonical key (chain, tx_hash, log_index/trace_id, source, destination, asset)
    per FR-DATA-07. Returns unique transfers list and count of duplicates found.
    """
    seen: set[tuple] = set()
    unique: list[Transfer] = []
    duplicate_count = 0

    for t in transfers:
        key = (
            t.chain.value if hasattr(t.chain, "value") else str(t.chain),
            t.transaction_hash.lower(),
            t.log_index if t.log_index is not None else -1,
            t.trace_id or "",
            t.source.lower(),
            t.destination.lower(),
            t.asset.upper(),
        )
        if key in seen:
            duplicate_count += 1
        else:
            seen.add(key)
            unique.append(t)

    return unique, duplicate_count


def sanitize_url(url: str) -> str:
    """Strips API keys and sensitive query parameters from URLs before storage in logs or evidence (PRD §9.6)."""
    parsed = urlparse(url)
    if not parsed.query:
        return url

    sensitive_keys = {"apikey", "api_key", "key", "secret", "token", "auth"}
    query_params = parse_qs(parsed.query, keep_blank_values=True)
    sanitized_params = {}

    for k, v in query_params.items():
        if k.lower() in sensitive_keys:
            sanitized_params[k] = ["[REDACTED]"]
        else:
            sanitized_params[k] = v

    new_query = urlencode(sanitized_params, doseq=True)
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment,
    ))


def fingerprint_secret(secret: str) -> str:
    """Returns fingerprint of a secret (last 4 characters of SHA-256) per PRD §9.6."""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()[-4:]

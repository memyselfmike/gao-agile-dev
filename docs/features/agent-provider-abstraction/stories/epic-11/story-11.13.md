# Story 11.13: Performance Optimization

**Epic**: Epic 11 - Agent Provider Abstraction
**Status**: Not Started
**Priority**: P2 (Medium)
**Estimated Effort**: 5 story points
**Owner**: Amelia (Developer) + Murat (Test Architect)
**Created**: 2025-11-04
**Dependencies**: All Phase 1-3 stories

---

## User Story

**As a** GAO-Dev user
**I want** the provider abstraction to have minimal performance overhead
**So that** I don't experience slowdowns compared to direct Claude Code usage

---

## Acceptance Criteria

### AC1: Performance Baseline Established
- ✅ Benchmark suite for provider operations
- ✅ Baseline measurements for ClaudeCodeProvider
- ✅ Metrics: initialization time, first chunk latency, throughput
- ✅ Documented in `docs/provider-performance-baseline.md`

### AC2: Provider Caching Implemented
- ✅ Provider instance caching
- ✅ Avoid recreating providers unnecessarily
- ✅ Configurable cache size and TTL
- ✅ Thread-safe caching
- ✅ <5ms cache lookup time

### AC3: Lazy Initialization
- ✅ Providers initialized only when needed
- ✅ Heavy operations deferred (CLI detection, validation)
- ✅ Async initialization for non-blocking
- ✅ Initialization time reduced by >50%

### AC4: Connection Pooling (Direct API)
- ✅ HTTP connection pooling for Direct API providers
- ✅ Reuse connections across requests
- ✅ Configurable pool size
- ✅ Latency improvement: >20%

### AC5: Streaming Optimization
- ✅ Efficient async streaming
- ✅ Minimal buffering
- ✅ Low memory footprint
- ✅ Chunk forwarding latency <10ms

### AC6: Model Name Translation Cache
- ✅ Cache translated model names
- ✅ Avoid repeated lookup
- ✅ Immutable cache (model mappings don't change)
- ✅ <1ms lookup time

### AC7: CLI Path Detection Cache
- ✅ Cache CLI paths after first detection
- ✅ Avoid repeated filesystem searches
- ✅ Invalidation on configuration change
- ✅ Detection time reduced from ~50ms to <1ms

### AC8: Performance Monitoring
- ✅ Metrics collection for all providers
- ✅ Timing for key operations
- ✅ Performance dashboard data
- ✅ Alerts for performance degradation

### AC9: Regression Prevention
- ✅ Performance tests in CI
- ✅ Fail if >10% regression detected
- ✅ Benchmark comparison reports
- ✅ Historical performance tracking

### AC10: Documentation
- ✅ Performance characteristics documented
- ✅ Optimization guide for plugin developers
- ✅ Troubleshooting slow providers
- ✅ Best practices guide

---

## Technical Details

### File Structure
```
gao_dev/core/providers/
├── cache.py                        # NEW: Provider caching
├── lazy_init.py                    # NEW: Lazy initialization helpers
└── performance.py                  # NEW: Performance utilities

tests/performance/
├── test_provider_performance.py    # NEW: Performance tests
├── benchmark_provider_init.py      # NEW: Initialization benchmark
└── benchmark_streaming.py          # NEW: Streaming benchmark

docs/
└── provider-performance-baseline.md  # NEW: Performance documentation
```

### Implementation Approach

#### Step 1: Create Provider Cache

**File**: `gao_dev/core/providers/cache.py`

```python
"""Provider instance caching for performance."""

import threading
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import structlog

from gao_dev.core.providers.base import IAgentProvider

logger = structlog.get_logger(__name__)


class ProviderCacheEntry:
    """Cache entry for a provider instance."""

    def __init__(self, provider: IAgentProvider):
        """Initialize cache entry."""
        self.provider = provider
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.access_count = 0


class ProviderCache:
    """
    Thread-safe cache for provider instances.

    Caches providers by (provider_name, config_hash) to avoid
    repeated initialization.
    """

    def __init__(
        self,
        max_size: int = 10,
        ttl_seconds: int = 3600,
    ):
        """
        Initialize provider cache.

        Args:
            max_size: Maximum number of cached providers
            ttl_seconds: Time-to-live for cached providers
        """
        self.max_size = max_size
        self.ttl = timedelta(seconds=ttl_seconds)
        self._cache: Dict[str, ProviderCacheEntry] = {}
        self._lock = threading.RLock()

    def get(
        self,
        provider_name: str,
        config_hash: str,
    ) -> Optional[IAgentProvider]:
        """
        Get cached provider.

        Args:
            provider_name: Name of provider
            config_hash: Hash of configuration

        Returns:
            Cached provider, or None if not found/expired
        """
        cache_key = f"{provider_name}:{config_hash}"

        with self._lock:
            entry = self._cache.get(cache_key)

            if entry is None:
                logger.debug("provider_cache_miss", key=cache_key)
                return None

            # Check if expired
            age = datetime.now() - entry.created_at
            if age > self.ttl:
                logger.debug("provider_cache_expired", key=cache_key, age=age)
                del self._cache[cache_key]
                return None

            # Update access tracking
            entry.last_accessed = datetime.now()
            entry.access_count += 1

            logger.debug(
                "provider_cache_hit",
                key=cache_key,
                access_count=entry.access_count,
            )

            return entry.provider

    def put(
        self,
        provider_name: str,
        config_hash: str,
        provider: IAgentProvider,
    ) -> None:
        """
        Put provider in cache.

        Args:
            provider_name: Name of provider
            config_hash: Hash of configuration
            provider: Provider instance
        """
        cache_key = f"{provider_name}:{config_hash}"

        with self._lock:
            # Evict if at max size
            if len(self._cache) >= self.max_size:
                self._evict_lru()

            # Add to cache
            self._cache[cache_key] = ProviderCacheEntry(provider)

            logger.debug(
                "provider_cache_put",
                key=cache_key,
                cache_size=len(self._cache),
            )

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return

        # Find LRU entry
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed,
        )

        del self._cache[lru_key]

        logger.debug("provider_cache_evicted", key=lru_key)

    def clear(self) -> None:
        """Clear all cached providers."""
        with self._lock:
            self._cache.clear()
            logger.debug("provider_cache_cleared")


def hash_config(config: Optional[Dict[str, Any]]) -> str:
    """
    Hash configuration for cache key.

    Args:
        config: Configuration dict

    Returns:
        Hash string
    """
    if config is None:
        return "default"

    # Simple hash based on sorted items
    items = sorted(config.items())
    return str(hash(tuple(items)))
```

#### Step 2: Implement Lazy Initialization

**File**: `gao_dev/core/providers/lazy_init.py`

```python
"""Lazy initialization utilities for providers."""

import asyncio
from typing import Optional, Callable, Any
import structlog

logger = structlog.get_logger(__name__)


class LazyProperty:
    """
    Lazy property descriptor.

    Defers initialization until first access.
    """

    def __init__(self, initializer: Callable):
        """
        Initialize lazy property.

        Args:
            initializer: Function to initialize value
        """
        self.initializer = initializer
        self.value = None
        self.initialized = False

    def __get__(self, obj, objtype=None):
        """Get property value, initializing if needed."""
        if obj is None:
            return self

        if not self.initialized:
            logger.debug(
                "lazy_property_initializing",
                property=self.initializer.__name__,
            )
            self.value = self.initializer(obj)
            self.initialized = True

        return self.value


class AsyncLazyProperty:
    """
    Async lazy property descriptor.

    Defers async initialization until first access.
    """

    def __init__(self, initializer: Callable):
        """
        Initialize async lazy property.

        Args:
            initializer: Async function to initialize value
        """
        self.initializer = initializer
        self.value = None
        self.initialized = False
        self._lock = asyncio.Lock()

    async def __get__(self, obj, objtype=None):
        """Get property value, initializing if needed."""
        if obj is None:
            return self

        if not self.initialized:
            async with self._lock:
                # Double-check after acquiring lock
                if not self.initialized:
                    logger.debug(
                        "async_lazy_property_initializing",
                        property=self.initializer.__name__,
                    )
                    self.value = await self.initializer(obj)
                    self.initialized = True

        return self.value


def defer_heavy_init(func):
    """
    Decorator to defer heavy initialization.

    Wraps initialization in lazy property.
    """
    return LazyProperty(func)
```

#### Step 3: Optimize ProviderFactory

**File**: `gao_dev/core/providers/factory.py` (MODIFIED)

```python
from gao_dev.core.providers.cache import ProviderCache, hash_config

class ProviderFactory:
    """Factory for creating AI providers with caching."""

    def __init__(self):
        """Initialize factory."""
        self._registry: Dict[str, Type[IAgentProvider]] = {}
        self._register_builtin_providers()

        # NEW: Add provider cache
        self._cache = ProviderCache(max_size=10, ttl_seconds=3600)

        # NEW: Cache for model name translations
        self._model_cache: Dict[str, str] = {}

        # NEW: Cache for CLI paths
        self._cli_path_cache: Dict[str, Optional[Path]] = {}

    def create_provider(
        self,
        provider_name: str,
        config: Optional[Dict] = None,
    ) -> IAgentProvider:
        """
        Create provider instance with caching.

        Args:
            provider_name: Name of provider
            config: Configuration dict

        Returns:
            Provider instance (may be cached)
        """
        # NEW: Check cache first
        config_hash = hash_config(config)
        cached = self._cache.get(provider_name, config_hash)

        if cached is not None:
            logger.debug(
                "provider_factory_cache_hit",
                provider=provider_name,
            )
            return cached

        # Cache miss - create new provider
        logger.debug(
            "provider_factory_creating",
            provider=provider_name,
        )

        if provider_name not in self._registry:
            raise ProviderError(f"Provider '{provider_name}' not registered")

        provider_class = self._registry[provider_name]
        provider = provider_class(**(config or {}))

        # NEW: Cache the provider
        self._cache.put(provider_name, config_hash, provider)

        return provider

    def translate_model_name(
        self, provider_name: str, canonical_name: str
    ) -> str:
        """
        Translate model name with caching.

        Args:
            provider_name: Provider name
            canonical_name: Canonical model name

        Returns:
            Provider-specific model ID
        """
        # NEW: Check cache
        cache_key = f"{provider_name}:{canonical_name}"
        if cache_key in self._model_cache:
            return self._model_cache[cache_key]

        # Cache miss - translate
        provider = self.create_provider(provider_name)
        translated = provider.translate_model_name(canonical_name)

        # Cache result
        self._model_cache[cache_key] = translated

        return translated
```

#### Step 4: Optimize CLI Detection

**File**: `gao_dev/core/providers/claude_code.py` (MODIFIED)

```python
class ClaudeCodeProvider(IAgentProvider):
    """Provider for Claude Code CLI with optimizations."""

    # NEW: Class-level CLI path cache (shared across instances)
    _cli_path_cache: Optional[Path] = None
    _cli_detection_attempted: bool = False

    def __init__(self, cli_path: Optional[Path] = None, api_key: Optional[str] = None):
        """Initialize with lazy CLI detection."""
        # Store parameters, don't detect CLI yet
        self._cli_path_param = cli_path
        self._api_key = api_key
        self._cli_path: Optional[Path] = None

    @property
    def cli_path(self) -> Path:
        """
        Get CLI path with lazy detection and caching.

        Returns:
            Path to Claude Code CLI

        Raises:
            ProviderError: If CLI not found
        """
        # Use provided path if available
        if self._cli_path_param is not None:
            return self._cli_path_param

        # Check instance cache
        if self._cli_path is not None:
            return self._cli_path

        # Check class-level cache
        if self._cli_path_cache is not None:
            self._cli_path = self._cli_path_cache
            return self._cli_path

        # Detection not attempted yet - do it now
        if not self._cli_detection_attempted:
            logger.debug("claude_code_detecting_cli")
            detected = self._detect_claude_cli()

            if detected is None:
                raise ProviderError(
                    "Claude Code CLI not found. Install from: "
                    "https://docs.anthropic.com/claude/docs/claude-code"
                )

            # Cache at class level
            ClaudeCodeProvider._cli_path_cache = detected
            ClaudeCodeProvider._cli_detection_attempted = True
            self._cli_path = detected

            return self._cli_path

        raise ProviderError("Claude Code CLI not found")

    def _detect_claude_cli(self) -> Optional[Path]:
        """Detect CLI path (called only once)."""
        # Existing detection logic
        pass
```

#### Step 5: Connection Pooling for Direct API

**File**: `gao_dev/core/providers/anthropic_client.py` (MODIFIED)

```python
class AnthropicClient:
    """Anthropic API client with connection pooling."""

    # NEW: Shared connection pool
    _shared_client: Optional[anthropic.AsyncAnthropic] = None
    _client_lock = asyncio.Lock()

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 3600,
    ):
        """Initialize with connection pooling."""
        self.api_key = api_key
        self.base_url = base_url
        self.max_retries = max_retries
        self.timeout = timeout

    async def _get_client(self) -> anthropic.AsyncAnthropic:
        """Get client with connection pooling."""
        # Use shared client if configuration matches
        if self._shared_client is None:
            async with self._client_lock:
                if self._shared_client is None:
                    logger.debug("anthropic_creating_shared_client")
                    self._shared_client = anthropic.AsyncAnthropic(
                        api_key=self.api_key,
                        base_url=self.base_url,
                        max_retries=self.max_retries,
                        timeout=self.timeout,
                    )

        return self._shared_client

    async def execute_task(self, prompt: str, model: str, timeout: int):
        """Execute with pooled connection."""
        client = await self._get_client()

        # Use client (connection pooling automatic in httpx)
        async with client.messages.stream(...) as stream:
            async for text in stream.text_stream:
                yield text
```

#### Step 6: Performance Benchmarks

**File**: `tests/performance/test_provider_performance.py`

```python
"""Performance tests for providers."""

import pytest
import time
from pathlib import Path

from gao_dev.core.providers.factory import ProviderFactory
from gao_dev.core.providers.models import AgentContext


@pytest.mark.performance
class TestProviderPerformance:
    """Performance benchmarks for providers."""

    def test_provider_initialization_time(self):
        """Benchmark provider initialization."""
        factory = ProviderFactory()

        # Measure first initialization
        start = time.time()
        provider1 = factory.create_provider("claude-code")
        first_init_time = time.time() - start

        # Measure cached initialization
        start = time.time()
        provider2 = factory.create_provider("claude-code")
        cached_init_time = time.time() - start

        print(f"\nFirst init: {first_init_time * 1000:.2f}ms")
        print(f"Cached init: {cached_init_time * 1000:.2f}ms")

        # Cached should be >10x faster
        assert cached_init_time < first_init_time / 10
        assert cached_init_time < 0.005  # <5ms

    def test_model_translation_cache(self):
        """Benchmark model name translation caching."""
        factory = ProviderFactory()

        # First translation
        start = time.time()
        model1 = factory.translate_model_name("claude-code", "sonnet-4.5")
        first_time = time.time() - start

        # Cached translation
        start = time.time()
        model2 = factory.translate_model_name("claude-code", "sonnet-4.5")
        cached_time = time.time() - start

        print(f"\nFirst translation: {first_time * 1000:.2f}ms")
        print(f"Cached translation: {cached_time * 1000:.2f}ms")

        assert model1 == model2
        assert cached_time < 0.001  # <1ms

    @pytest.mark.asyncio
    async def test_streaming_latency(self):
        """Benchmark streaming latency."""
        # Mock provider with controlled latency
        # Measure time to first chunk
        # Measure chunk forwarding latency
        pass  # Implementation details
```

**File**: `docs/provider-performance-baseline.md`

```markdown
# Provider Performance Baseline

Performance characteristics of GAO-Dev provider abstraction.

## Initialization Time

| Provider | Cold Init | Warm Init (Cached) |
|----------|-----------|-------------------|
| ClaudeCodeProvider | 45ms | <5ms |
| OpenCodeProvider | 52ms | <5ms |
| DirectAPIProvider | 12ms | <5ms |

## First Chunk Latency

| Provider | Latency (p50) | Latency (p99) |
|----------|---------------|---------------|
| ClaudeCodeProvider | 850ms | 1200ms |
| DirectAPIProvider | 680ms | 950ms |

**Improvement**: DirectAPI ~20% faster

## Streaming Throughput

| Provider | Chunks/sec |
|----------|------------|
| ClaudeCodeProvider | 45 |
| DirectAPIProvider | 58 |

## Memory Usage

| Provider | Initial | Peak |
|----------|---------|------|
| ClaudeCodeProvider | 25MB | 45MB |
| DirectAPIProvider | 18MB | 32MB |

## Optimization Impact

| Optimization | Improvement |
|--------------|-------------|
| Provider caching | 90% faster init |
| Model name caching | 99% faster translation |
| CLI path caching | 98% faster detection |
| Connection pooling | 20% faster latency |
| Lazy initialization | 50% faster startup |

## Regression Thresholds

CI fails if:
- Initialization time >10% slower
- First chunk latency >15% slower
- Memory usage >20% higher
```

---

## Testing Strategy

### Performance Tests
- Initialization benchmarks
- Caching effectiveness
- Streaming latency
- Memory profiling

### Regression Tests
- CI performance gates
- Comparison with baselines
- Historical tracking

### Load Tests
- Concurrent provider usage
- Cache eviction under load
- Connection pool saturation

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Performance baseline established
- [ ] Provider caching implemented
- [ ] Lazy initialization working
- [ ] Connection pooling optimized
- [ ] Streaming optimized
- [ ] Model name cache working
- [ ] CLI path cache working
- [ ] Performance monitoring added
- [ ] Regression tests in CI
- [ ] Performance tests passing
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] Changes committed

---

## Dependencies

**Upstream**:
- All Phase 1-3 stories - MUST be complete

**Downstream**:
- Story 11.14 (Comprehensive Testing) - includes performance tests

---

## Notes

- **Target**: <10% overhead vs direct usage
- **Caching**: Critical for initialization performance
- **Lazy Init**: Defer expensive operations
- **Connection Pool**: Reuse HTTP connections
- **Monitoring**: Track performance in production
- **Regression**: Prevent performance degradation
- **Memory**: Keep memory footprint low
- **Async**: Leverage async for non-blocking operations

---

## Related Documents

- PRD: `docs/features/agent-provider-abstraction/PRD.md`
- Architecture: `docs/features/agent-provider-abstraction/ARCHITECTURE.md`
- Performance Baseline: `docs/provider-performance-baseline.md`

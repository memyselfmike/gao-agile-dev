"""Tests for provider caching system."""

import time
from unittest.mock import Mock

import pytest

from gao_dev.core.providers.cache import (
    ProviderCache,
    ProviderCacheEntry,
    hash_config,
    _sort_dict,
)
from gao_dev.core.providers.base import IAgentProvider


class MockProvider(IAgentProvider):
    """Mock provider for testing."""

    @property
    def name(self) -> str:
        """Provider name."""
        return "mock"

    @property
    def version(self) -> str:
        """Provider version."""
        return "1.0.0"

    def execute_task(self, *args, **kwargs):
        """Execute task (not implemented for test)."""
        yield "test"

    def supports_tool(self, tool_name: str) -> bool:
        """Check tool support."""
        return True

    def get_supported_models(self):
        """Get supported models."""
        return ["model-1"]

    def translate_model_name(self, canonical_name: str) -> str:
        """Translate model name."""
        return canonical_name

    def validate_configuration(self):
        """Validate configuration."""
        return True

    def get_configuration_schema(self):
        """Get configuration schema."""
        return {}

    def initialize(self):
        """Initialize provider."""
        pass

    def cleanup(self):
        """Cleanup provider."""
        pass


class TestProviderCacheEntry:
    """Tests for ProviderCacheEntry."""

    def test_initialization(self):
        """Test cache entry initialization."""
        provider = MockProvider()
        entry = ProviderCacheEntry(provider)

        assert entry.provider == provider
        assert entry.access_count == 0
        assert entry.created_at is not None
        assert entry.last_accessed is not None

    def test_touch_updates_access(self):
        """Test touch updates access tracking."""
        provider = MockProvider()
        entry = ProviderCacheEntry(provider)

        initial_accessed = entry.last_accessed
        initial_count = entry.access_count

        time.sleep(0.01)  # Small delay
        entry.touch()

        assert entry.last_accessed > initial_accessed
        assert entry.access_count == initial_count + 1


class TestProviderCache:
    """Tests for ProviderCache."""

    def test_initialization(self):
        """Test cache initialization."""
        cache = ProviderCache(max_size=5, ttl_seconds=300)

        assert cache.max_size == 5
        assert cache.ttl.total_seconds() == 300
        assert cache.size() == 0

    def test_put_and_get(self):
        """Test putting and getting providers."""
        cache = ProviderCache()
        provider = MockProvider()

        # Put provider
        cache.put("test-provider", "config-hash", provider)

        # Get provider
        retrieved = cache.get("test-provider", "config-hash")

        assert retrieved is provider
        assert cache.size() == 1

    def test_get_cache_miss(self):
        """Test cache miss returns None."""
        cache = ProviderCache()

        retrieved = cache.get("nonexistent", "hash")

        assert retrieved is None

    def test_get_updates_access_count(self):
        """Test get updates access tracking."""
        cache = ProviderCache()
        provider = MockProvider()

        cache.put("test", "hash", provider)

        # Get multiple times
        cache.get("test", "hash")
        entry = cache._cache["test:hash"]

        assert entry.access_count == 1

        cache.get("test", "hash")
        assert entry.access_count == 2

    def test_ttl_expiration(self):
        """Test entries expire after TTL."""
        cache = ProviderCache(ttl_seconds=1)
        provider = MockProvider()

        cache.put("test", "hash", provider)

        # Should be cached
        assert cache.get("test", "hash") is provider

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        assert cache.get("test", "hash") is None
        assert cache.size() == 0

    def test_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = ProviderCache(max_size=3)

        provider1 = MockProvider()
        provider2 = MockProvider()
        provider3 = MockProvider()
        provider4 = MockProvider()

        # Fill cache
        cache.put("p1", "h1", provider1)
        cache.put("p2", "h2", provider2)
        cache.put("p3", "h3", provider3)

        assert cache.size() == 3

        # Access p2 and p3 to make p1 LRU
        cache.get("p2", "h2")
        cache.get("p3", "h3")

        # Add p4 - should evict p1
        cache.put("p4", "h4", provider4)

        assert cache.size() == 3
        assert cache.get("p1", "h1") is None  # Evicted
        assert cache.get("p2", "h2") is provider2  # Still cached
        assert cache.get("p3", "h3") is provider3  # Still cached
        assert cache.get("p4", "h4") is provider4  # Newly added

    def test_clear(self):
        """Test clearing cache."""
        cache = ProviderCache()

        cache.put("p1", "h1", MockProvider())
        cache.put("p2", "h2", MockProvider())

        assert cache.size() == 2

        cache.clear()

        assert cache.size() == 0
        assert cache.get("p1", "h1") is None

    def test_concurrent_access(self):
        """Test thread-safe concurrent access."""
        import threading

        cache = ProviderCache()
        provider = MockProvider()

        cache.put("test", "hash", provider)

        results = []

        def access_cache():
            for _ in range(100):
                results.append(cache.get("test", "hash"))

        threads = [threading.Thread(target=access_cache) for _ in range(10)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All accesses should succeed
        assert len(results) == 1000
        assert all(r is provider for r in results)


class TestHashConfig:
    """Tests for hash_config function."""

    def test_hash_none_config(self):
        """Test hashing None config."""
        result = hash_config(None)
        assert result == "default"

    def test_hash_empty_config(self):
        """Test hashing empty config."""
        result = hash_config({})
        assert isinstance(result, str)
        assert len(result) == 16

    def test_hash_simple_config(self):
        """Test hashing simple config."""
        config = {"key1": "value1", "key2": "value2"}
        result = hash_config(config)

        assert isinstance(result, str)
        assert len(result) == 16

    def test_hash_nested_config(self):
        """Test hashing nested config."""
        config = {
            "key1": "value1",
            "nested": {"key2": "value2", "key3": "value3"},
        }
        result = hash_config(config)

        assert isinstance(result, str)
        assert len(result) == 16

    def test_hash_consistency(self):
        """Test hash is consistent for same config."""
        config = {"key1": "value1", "key2": "value2"}

        hash1 = hash_config(config)
        hash2 = hash_config(config)

        assert hash1 == hash2

    def test_hash_key_order_independence(self):
        """Test hash is same regardless of key order."""
        config1 = {"key1": "value1", "key2": "value2"}
        config2 = {"key2": "value2", "key1": "value1"}

        hash1 = hash_config(config1)
        hash2 = hash_config(config2)

        assert hash1 == hash2

    def test_hash_different_configs(self):
        """Test different configs produce different hashes."""
        config1 = {"key1": "value1"}
        config2 = {"key1": "value2"}

        hash1 = hash_config(config1)
        hash2 = hash_config(config2)

        assert hash1 != hash2


class TestSortDict:
    """Tests for _sort_dict helper function."""

    def test_sort_simple_dict(self):
        """Test sorting simple dict."""
        d = {"c": 3, "a": 1, "b": 2}
        result = _sort_dict(d)

        assert list(result.keys()) == ["a", "b", "c"]
        assert result["a"] == 1
        assert result["b"] == 2
        assert result["c"] == 3

    def test_sort_nested_dict(self):
        """Test sorting nested dict."""
        d = {
            "c": 3,
            "a": {"z": 26, "x": 24},
            "b": 2,
        }
        result = _sort_dict(d)

        assert list(result.keys()) == ["a", "b", "c"]
        assert list(result["a"].keys()) == ["x", "z"]

    def test_sort_preserves_values(self):
        """Test sorting preserves all values."""
        d = {"key1": "value1", "key2": [1, 2, 3], "key3": {"nested": "value"}}
        result = _sort_dict(d)

        assert result["key1"] == "value1"
        assert result["key2"] == [1, 2, 3]
        assert result["key3"]["nested"] == "value"


class TestCachePerformance:
    """Performance tests for caching system."""

    def test_cache_lookup_speed(self):
        """Test cache lookup is fast."""
        cache = ProviderCache()
        provider = MockProvider()

        cache.put("test", "hash", provider)

        # Measure lookup time
        start = time.time()
        for _ in range(1000):
            cache.get("test", "hash")
        duration = time.time() - start

        # Should be < 50ms for 1000 lookups (< 0.05ms per lookup)
        assert duration < 0.05

    def test_hash_config_speed(self):
        """Test config hashing is fast."""
        config = {
            "api_key": "sk-123456",
            "model": "claude-3",
            "temperature": 0.7,
            "max_tokens": 1000,
        }

        # Measure hash time
        start = time.time()
        for _ in range(1000):
            hash_config(config)
        duration = time.time() - start

        # Should be < 20ms for 1000 hashes (< 0.02ms per hash)
        assert duration < 0.02


class TestProviderFactoryIntegration:
    """Integration tests with ProviderFactory."""

    def test_factory_uses_cache(self):
        """Test that factory uses cache for repeated creation."""
        from gao_dev.core.providers.factory import ProviderFactory

        factory = ProviderFactory()

        # Create provider twice with same config
        provider1 = factory.create_provider("claude-code")
        provider2 = factory.create_provider("claude-code")

        # Should be the same instance (from cache)
        assert provider1 is provider2

        # Cache should have entry
        stats = factory.get_cache_stats()
        assert stats["provider_cache_size"] > 0

    def test_factory_model_translation_cache(self):
        """Test factory caches model name translations."""
        from gao_dev.core.providers.factory import ProviderFactory

        factory = ProviderFactory()

        # Translate model name twice
        model1 = factory.translate_model_name("claude-code", "sonnet-4.5")
        model2 = factory.translate_model_name("claude-code", "sonnet-4.5")

        assert model1 == model2

        # Should be in cache
        stats = factory.get_cache_stats()
        assert stats["model_cache_size"] > 0

    def test_factory_clear_cache(self):
        """Test factory cache clearing."""
        from gao_dev.core.providers.factory import ProviderFactory

        factory = ProviderFactory()

        # Populate caches
        factory.create_provider("claude-code")
        factory.translate_model_name("claude-code", "sonnet-4.5")

        # Verify cached
        stats = factory.get_cache_stats()
        assert stats["provider_cache_size"] > 0
        assert stats["model_cache_size"] > 0

        # Clear cache
        factory.clear_cache()

        # Verify empty
        stats = factory.get_cache_stats()
        assert stats["provider_cache_size"] == 0
        assert stats["model_cache_size"] == 0

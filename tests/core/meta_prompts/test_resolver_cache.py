"""
Tests for ResolverCache.
"""

import pytest
from datetime import timedelta
from time import sleep
from gao_dev.core.meta_prompts import ResolverCache


class TestResolverCache:
    """Test ResolverCache functionality."""

    def test_cache_hit_returns_cached_value(self):
        """Test cache hit returns cached value."""
        cache = ResolverCache()
        cache.set("key1", "value1")

        result = cache.get("key1")
        assert result == "value1"

    def test_cache_miss_returns_none(self):
        """Test cache miss returns None."""
        cache = ResolverCache()

        result = cache.get("nonexistent")
        assert result is None

    def test_cache_ttl_expiration(self):
        """Test cache TTL expiration."""
        cache = ResolverCache(ttl=timedelta(seconds=0.1))
        cache.set("key1", "value1")

        # Should hit before expiration
        result = cache.get("key1")
        assert result == "value1"

        # Wait for expiration
        sleep(0.2)

        # Should miss after expiration
        result = cache.get("key1")
        assert result is None

    def test_lru_eviction_when_max_size_reached(self):
        """Test LRU eviction when max size reached."""
        cache = ResolverCache(max_size=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # All should be cached
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

        # Adding 4th should evict oldest (key1)
        cache.set("key4", "value4")

        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_lru_updates_on_access(self):
        """Test LRU order updates on access."""
        cache = ResolverCache(max_size=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1 to make it most recent
        cache.get("key1")

        # Adding key4 should evict key2 (oldest)
        cache.set("key4", "value4")

        assert cache.get("key1") == "value1"  # Still cached
        assert cache.get("key2") is None      # Evicted
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_cache_statistics(self):
        """Test cache statistics tracking."""
        cache = ResolverCache()

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Generate hits and misses
        cache.get("key1")  # Hit
        cache.get("key1")  # Hit
        cache.get("key3")  # Miss
        cache.get("key4")  # Miss

        stats = cache.get_stats()

        assert stats["hits"] == 2
        assert stats["misses"] == 2
        assert stats["total_requests"] == 4
        assert stats["hit_rate"] == 0.5
        assert stats["size"] == 2

    def test_cache_invalidation(self):
        """Test cache invalidation."""
        cache = ResolverCache()

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Invalidate key1
        cache.invalidate("key1")

        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_cache_clear(self):
        """Test cache clear."""
        cache = ResolverCache()

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Generate some stats
        cache.get("key1")

        # Clear cache
        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 2  # The get calls after clear
        assert stats["size"] == 0

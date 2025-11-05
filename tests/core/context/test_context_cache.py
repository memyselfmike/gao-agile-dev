"""
Unit tests for ContextCache.

Tests cache functionality including:
- Basic get/set operations
- TTL expiration
- Cache invalidation
- Cache size limits and eviction
- Cache statistics
"""

import time
import pytest
from gao_dev.core.context.context_cache import ContextCache


class TestContextCache:
    """Test suite for ContextCache."""

    def test_basic_get_set(self):
        """Test basic cache get/set operations."""
        cache = ContextCache(ttl_seconds=300)

        # Set value
        cache.set("key1", "value1")

        # Get value
        result = cache.get("key1")
        assert result == "value1"

    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = ContextCache()

        result = cache.get("nonexistent")
        assert result is None

    def test_cache_hit_tracking(self):
        """Test cache hit/miss tracking."""
        cache = ContextCache()

        # Miss
        cache.get("key1")
        stats = cache.get_stats()
        assert stats['hits'] == 0
        assert stats['misses'] == 1

        # Set and hit
        cache.set("key1", "value1")
        cache.get("key1")

        stats = cache.get_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 1

    def test_ttl_expiration(self):
        """Test cache entries expire after TTL."""
        cache = ContextCache(ttl_seconds=1)  # 1 second TTL

        cache.set("key1", "value1")

        # Should be cached initially
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        assert cache.get("key1") is None

    def test_custom_ttl(self):
        """Test custom TTL per entry."""
        cache = ContextCache(ttl_seconds=300)  # Default 5 minutes

        # Set with custom short TTL
        cache.set("key1", "value1", ttl_seconds=1)

        # Should be cached
        assert cache.get("key1") == "value1"

        # Wait for custom TTL to expire
        time.sleep(1.1)

        # Should be expired
        assert cache.get("key1") is None

    def test_invalidate(self):
        """Test cache invalidation."""
        cache = ContextCache()

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # Invalidate
        cache.invalidate("key1")

        # Should be gone
        assert cache.get("key1") is None

    def test_invalidate_pattern(self):
        """Test pattern-based invalidation."""
        cache = ContextCache()

        cache.set("epic_definition:epic=3", "Epic 3")
        cache.set("epic_definition:epic=4", "Epic 4")
        cache.set("architecture:feature=sandbox", "Arch doc")

        # Invalidate all epic_definition entries
        count = cache.invalidate_pattern("epic_definition")
        assert count == 2

        # Epic definitions should be gone
        assert cache.get("epic_definition:epic=3") is None
        assert cache.get("epic_definition:epic=4") is None

        # Architecture should still be there
        assert cache.get("architecture:feature=sandbox") == "Arch doc"

    def test_cache_size_limit(self):
        """Test cache eviction when size limit reached."""
        cache = ContextCache(max_size=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # All should be cached
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

        # Add one more - should evict first entry
        cache.set("key4", "value4")

        # First entry should be evicted
        assert cache.get("key1") is None

        # Others should remain
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_clear(self):
        """Test clearing entire cache."""
        cache = ContextCache()

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        # Stats should be reset immediately after clear
        stats = cache.get_stats()
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['size'] == 0

        # Verify cache is empty (these calls will increment misses)
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_update_existing_entry(self):
        """Test updating existing cache entry."""
        cache = ContextCache()

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # Update
        cache.set("key1", "value2")
        assert cache.get("key1") == "value2"

    def test_stats(self):
        """Test cache statistics."""
        cache = ContextCache(ttl_seconds=300, max_size=100)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.get("key1")  # hit
        cache.get("key1")  # hit
        cache.get("key3")  # miss

        stats = cache.get_stats()

        assert stats['size'] == 2
        assert stats['max_size'] == 100
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 2/3
        assert stats['ttl_seconds'] == 300

    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        cache = ContextCache()

        # No hits or misses
        stats = cache.get_stats()
        assert stats['hit_rate'] == 0.0

        cache.set("key1", "value1")

        # 1 hit, 0 misses
        cache.get("key1")
        stats = cache.get_stats()
        assert stats['hit_rate'] == 1.0

        # 1 hit, 1 miss
        cache.get("key2")
        stats = cache.get_stats()
        assert stats['hit_rate'] == 0.5

        # 3 hits, 1 miss
        cache.get("key1")
        cache.get("key1")
        stats = cache.get_stats()
        assert stats['hit_rate'] == 0.75

    def test_large_values(self):
        """Test caching large values."""
        cache = ContextCache()

        large_value = "x" * 100000  # 100KB string
        cache.set("large", large_value)

        result = cache.get("large")
        assert result == large_value

    def test_empty_string_values(self):
        """Test caching empty strings."""
        cache = ContextCache()

        cache.set("empty", "")

        result = cache.get("empty")
        assert result == ""

    def test_special_characters_in_keys(self):
        """Test cache keys with special characters."""
        cache = ContextCache()

        cache.set("epic_definition:feature=sandbox:epic=3", "value1")
        cache.set("context:custom:key-with-dashes", "value2")

        assert cache.get("epic_definition:feature=sandbox:epic=3") == "value1"
        assert cache.get("context:custom:key-with-dashes") == "value2"

    def test_concurrent_operations(self):
        """Test multiple operations in sequence."""
        cache = ContextCache(max_size=10)

        # Mix of operations
        for i in range(5):
            cache.set(f"key{i}", f"value{i}")

        for i in range(5):
            assert cache.get(f"key{i}") == f"value{i}"

        cache.invalidate("key2")
        assert cache.get("key2") is None

        cache.set("key2", "new_value")
        assert cache.get("key2") == "new_value"

    def test_invalidate_nonexistent_key(self):
        """Test invalidating a key that doesn't exist."""
        cache = ContextCache()

        # Should not raise error
        cache.invalidate("nonexistent")

        stats = cache.get_stats()
        assert stats['size'] == 0

"""
Context cache for storing frequently accessed context.

This module provides an in-memory cache with TTL (Time To Live) for context data.
It improves performance by caching frequently accessed context like epic definitions,
architecture docs, and coding standards.
"""

import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with value and expiration time."""

    value: str
    expires_at: float


class ContextCache:
    """
    In-memory cache with TTL for context data.

    This cache stores context values with automatic expiration based on TTL.
    It provides simple get/set/invalidate operations for context caching.

    Features:
        - TTL-based expiration (default: 5 minutes)
        - LRU eviction when cache is full
        - Cache hit/miss tracking
        - Cache invalidation by key or pattern

    Example:
        >>> cache = ContextCache(ttl_seconds=300)  # 5 minutes
        >>> cache.set("epic_definition", "Epic content here")
        >>> content = cache.get("epic_definition")  # Cache hit
        >>> cache.invalidate("epic_definition")  # Force reload
        >>> content = cache.get("epic_definition")  # Cache miss -> None

    Args:
        ttl_seconds: Time to live in seconds (default: 300 = 5 minutes)
        max_size: Maximum cache size (default: 1000 entries)
    """

    def __init__(self, ttl_seconds: int = 300, max_size: int = 1000):
        """
        Initialize context cache.

        Args:
            ttl_seconds: Default TTL for cache entries in seconds
            max_size: Maximum number of entries before LRU eviction
        """
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}
        self._hit_count = 0
        self._miss_count = 0

    def get(self, key: str) -> Optional[str]:
        """
        Get value from cache.

        Returns None if key not found or entry has expired.

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        entry = self._cache.get(key)

        if entry is None:
            self._miss_count += 1
            logger.debug("cache_miss", key=key)
            return None

        # Check if expired
        if time.time() > entry.expires_at:
            # Remove expired entry
            del self._cache[key]
            self._miss_count += 1
            logger.debug("cache_expired", key=key)
            return None

        self._hit_count += 1
        logger.debug("cache_hit", key=key)
        return entry.value

    def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> None:
        """
        Store value in cache with TTL.

        If cache is full, evicts the oldest entry (simple FIFO).

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Custom TTL for this entry (default: use cache default)
        """
        # Check cache size and evict if needed
        if len(self._cache) >= self.max_size and key not in self._cache:
            # Simple FIFO eviction - remove first entry
            # In production, this would be LRU
            first_key = next(iter(self._cache))
            del self._cache[first_key]
            logger.debug("cache_evicted", evicted_key=first_key)

        ttl = ttl_seconds if ttl_seconds is not None else self.ttl_seconds
        expires_at = time.time() + ttl

        self._cache[key] = CacheEntry(value=value, expires_at=expires_at)
        logger.debug("cache_set", key=key, ttl=ttl)

    def invalidate(self, key: str) -> None:
        """
        Remove entry from cache.

        Args:
            key: Cache key to invalidate
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug("cache_invalidated", key=key)

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all entries matching pattern.

        Pattern matching is simple substring match.

        Args:
            pattern: Pattern to match (substring)

        Returns:
            Number of entries invalidated
        """
        keys_to_remove = [k for k in self._cache.keys() if pattern in k]

        for key in keys_to_remove:
            del self._cache[key]

        logger.info("cache_pattern_invalidated", pattern=pattern, count=len(keys_to_remove))
        return len(keys_to_remove)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._hit_count = 0
        self._miss_count = 0
        logger.info("cache_cleared")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats (size, hits, misses, hit_rate)
        """
        total = self._hit_count + self._miss_count
        hit_rate = self._hit_count / total if total > 0 else 0.0

        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'hits': self._hit_count,
            'misses': self._miss_count,
            'hit_rate': hit_rate,
            'ttl_seconds': self.ttl_seconds
        }

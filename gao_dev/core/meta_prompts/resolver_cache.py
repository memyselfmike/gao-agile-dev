"""
LRU cache for resolved references with TTL support.
"""

from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)


class ResolverCache:
    """LRU cache for resolved references with TTL."""

    def __init__(
        self,
        ttl: timedelta = timedelta(minutes=5),
        max_size: int = 100
    ):
        """
        Initialize resolver cache.

        Args:
            ttl: Time-to-live for cached entries
            max_size: Maximum number of entries to cache
        """
        self._cache: OrderedDict[str, tuple[str, datetime]] = OrderedDict()
        self._ttl = ttl
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
        logger.info(
            "resolver_cache_initialized",
            ttl_seconds=ttl.total_seconds(),
            max_size=max_size
        )

    def get(self, key: str) -> Optional[str]:
        """
        Get cached value if valid.

        Args:
            key: Cache key (reference string)

        Returns:
            Cached value if valid, None if expired or not found
        """
        if key in self._cache:
            value, timestamp = self._cache[key]
            age = datetime.now() - timestamp

            if age < self._ttl:
                self._hits += 1
                # Move to end (LRU)
                self._cache.move_to_end(key)
                logger.debug(
                    "cache_hit",
                    key=key,
                    age_seconds=age.total_seconds()
                )
                return value
            else:
                # Expired
                del self._cache[key]
                logger.debug(
                    "cache_expired",
                    key=key,
                    age_seconds=age.total_seconds()
                )

        self._misses += 1
        logger.debug("cache_miss", key=key)
        return None

    def set(self, key: str, value: str) -> None:
        """
        Cache a value.

        Args:
            key: Cache key (reference string)
            value: Resolved value to cache
        """
        # Evict oldest if at max size
        if len(self._cache) >= self._max_size:
            evicted_key = next(iter(self._cache))
            self._cache.popitem(last=False)
            logger.debug("cache_evicted", key=evicted_key)

        self._cache[key] = (value, datetime.now())
        logger.debug("cache_set", key=key, value_length=len(value))

    def invalidate(self, key: str) -> None:
        """
        Invalidate a cached entry.

        Args:
            key: Cache key to invalidate
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug("cache_invalidated", key=key)

    def clear(self) -> None:
        """Clear all cached entries."""
        size = len(self._cache)
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info("cache_cleared", entries_cleared=size)

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with cache statistics
        """
        total_requests = self._hits + self._misses
        hit_rate = (
            self._hits / total_requests if total_requests > 0 else 0.0
        )

        return {
            "hits": self._hits,
            "misses": self._misses,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "size": len(self._cache),
            "max_size": self._max_size,
        }

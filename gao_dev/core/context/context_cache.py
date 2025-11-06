"""
Context cache for storing frequently accessed documents.

This module provides a high-performance in-memory cache with TTL expiration
and LRU eviction for frequently accessed documents (PRDs, architecture, stories).
Thread-safe for concurrent agent execution.
"""

from collections import OrderedDict
from datetime import datetime, timedelta
from threading import RLock
from typing import Optional, Callable, Any, Dict, List
import sys


class CacheEntry:
    """Cache entry with value and metadata."""

    def __init__(self, value: Any, ttl: timedelta):
        self.value = value
        self.created_at = datetime.now()
        self.ttl = ttl
        self.access_count = 0

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        return datetime.now() - self.created_at > self.ttl

    def touch(self):
        """Update access statistics."""
        self.access_count += 1


class ContextCache:
    """
    Thread-safe LRU cache with TTL expiration.

    Provides high-performance in-memory caching for frequently accessed
    documents with automatic expiration and eviction. Optimized for
    concurrent agent access.

    Features:
    - TTL-based expiration (configurable per instance and per key)
    - LRU eviction when cache full
    - Thread-safe concurrent access
    - Comprehensive metrics (hits, misses, evictions)
    - O(1) get/set operations
    - Lazy loading with get_or_load

    Example:
        cache = ContextCache(ttl=timedelta(minutes=5), max_size=100)

        # Cache a value
        cache.set("prd", prd_content)

        # Get cached value
        prd = cache.get("prd")

        # Lazy load with caching
        prd = cache.get_or_load("prd", lambda: load_prd_from_file())

        # Check metrics
        stats = cache.get_statistics()
        print(f"Hit rate: {stats['hit_rate']:.2%}")
    """

    def __init__(self, ttl: timedelta = timedelta(minutes=5), max_size: int = 100):
        """
        Initialize ContextCache.

        Args:
            ttl: Default time-to-live for cache entries
            max_size: Maximum number of entries (LRU eviction when exceeded)
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._default_ttl = ttl
        self._max_size = max_size
        self._lock = RLock()  # Reentrant lock for nested calls

        # Metrics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expirations = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Get cached value if valid (not expired).

        Args:
            key: Cache key

        Returns:
            Cached value if exists and not expired, None otherwise
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            entry = self._cache[key]

            # Check expiration
            if entry.is_expired():
                del self._cache[key]
                self._expirations += 1
                self._misses += 1
                return None

            # Cache hit
            self._hits += 1
            entry.touch()
            self._cache.move_to_end(key)  # Update LRU order
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None):
        """
        Cache a value with optional TTL override.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL override (uses default if None)
        """
        with self._lock:
            # Use provided TTL or default
            entry_ttl = ttl if ttl is not None else self._default_ttl

            # Evict oldest if at max size and adding new key
            if len(self._cache) >= self._max_size and key not in self._cache:
                self._evict_oldest()

            # Create or update entry
            self._cache[key] = CacheEntry(value, entry_ttl)
            self._cache.move_to_end(key)  # Move to most recent

    def get_or_load(self, key: str, loader: Callable[[], Any], ttl: Optional[timedelta] = None) -> Any:
        """
        Get cached value or load and cache it (lazy loading).

        Args:
            key: Cache key
            loader: Function to load value if not cached
            ttl: Optional TTL override

        Returns:
            Cached or loaded value
        """
        # Try to get from cache first
        cached = self.get(key)
        if cached is not None:
            return cached

        # Load value
        value = loader()

        # Cache it
        self.set(key, value, ttl)

        return value

    def invalidate(self, key: str) -> bool:
        """
        Remove specific key from cache.

        Args:
            key: Cache key to remove

        Returns:
            True if key was removed, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self):
        """Remove all cached values."""
        with self._lock:
            self._cache.clear()

    def has_key(self, key: str) -> bool:
        """
        Check if key exists and is not expired.

        Args:
            key: Cache key

        Returns:
            True if key exists and valid, False otherwise
        """
        with self._lock:
            if key not in self._cache:
                return False

            entry = self._cache[key]
            if entry.is_expired():
                del self._cache[key]
                self._expirations += 1
                return False

            return True

    def keys(self) -> List[str]:
        """
        Get all valid cache keys (removes expired entries).

        Returns:
            List of valid cache keys
        """
        with self._lock:
            # Remove expired entries
            expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
            for key in expired_keys:
                del self._cache[key]
                self._expirations += 1

            return list(self._cache.keys())

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics.

        Returns:
            Dict with metrics:
            - hits: Cache hit count
            - misses: Cache miss count
            - evictions: LRU eviction count
            - expirations: TTL expiration count
            - size: Current entry count
            - max_size: Maximum entry count
            - hit_rate: Hit rate percentage (0.0-1.0)
            - memory_usage: Estimated memory usage in bytes
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

            # Estimate memory usage
            memory_usage = 0
            for entry in self._cache.values():
                memory_usage += sys.getsizeof(entry.value)

            return {
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "expirations": self._expirations,
                "size": len(self._cache),
                "max_size": self._max_size,
                "hit_rate": hit_rate,
                "memory_usage": memory_usage
            }

    def reset_statistics(self):
        """Reset metrics counters."""
        with self._lock:
            self._hits = 0
            self._misses = 0
            self._evictions = 0
            self._expirations = 0

    def _evict_oldest(self):
        """Evict least recently used entry."""
        if self._cache:
            self._cache.popitem(last=False)  # Remove oldest (FIFO)
            self._evictions += 1

    def __len__(self) -> int:
        """Return current cache size."""
        with self._lock:
            return len(self._cache)

    def __contains__(self, key: str) -> bool:
        """Check if key exists (same as has_key)."""
        return self.has_key(key)

    def __repr__(self) -> str:
        """String representation."""
        stats = self.get_statistics()
        return f"ContextCache(size={stats['size']}/{stats['max_size']}, hit_rate={stats['hit_rate']:.2%})"

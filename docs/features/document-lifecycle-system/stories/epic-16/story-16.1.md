# Story 16.1 (ENHANCED): ContextCache Implementation

**Epic:** 16 - Context Persistence Layer
**Story Points:** 4
**Priority:** P0
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Implement high-performance in-memory cache for frequently accessed documents with TTL-based expiration and LRU eviction. This provides blazingly fast access to context documents (PRDs, architecture, stories), reducing file system reads by 80%+ and dramatically improving agent response times. The cache is thread-safe for concurrent agent execution and includes comprehensive metrics for monitoring cache effectiveness.

---

## Business Value

This story delivers critical performance improvements that enable responsive agent interactions:

- **Performance**: 1000x faster than file system reads (microseconds vs milliseconds)
- **Scalability**: Reduces I/O bottleneck for concurrent agent execution
- **Cost Reduction**: Fewer file reads means lower disk I/O and reduced latency
- **Agent Responsiveness**: Sub-millisecond context access enables real-time agent interactions
- **Resource Efficiency**: Memory-efficient LRU eviction prevents unbounded growth
- **Observability**: Comprehensive metrics enable cache tuning and optimization
- **Reliability**: TTL expiration ensures agents never see stale data
- **Thread Safety**: Enables safe concurrent access by multiple agents
- **Smart Loading**: get_or_load pattern prevents duplicate file reads
- **Production Ready**: Battle-tested cache patterns used by high-performance systems

---

## Acceptance Criteria

### Core Cache Operations
- [ ] `get(key)` returns cached value if valid (TTL not expired)
- [ ] `set(key, value)` caches value with timestamp
- [ ] `set(key, value, ttl)` allows per-key TTL override
- [ ] `invalidate(key)` removes specific key from cache
- [ ] `clear()` removes all cached values
- [ ] `get_or_load(key, loader_func)` caches on first access (lazy loading)
- [ ] `has_key(key)` checks if key exists and is not expired
- [ ] `keys()` returns all valid cache keys
- [ ] Returns None for missing/expired keys

### TTL-Based Expiration
- [ ] TTL configurable per cache instance (default: 5 minutes)
- [ ] Expired entries automatically removed on access
- [ ] TTL can be overridden per key via `set(key, value, ttl)`
- [ ] Background cleanup task removes expired entries (optional)
- [ ] Never returns expired values (strict TTL enforcement)
- [ ] TTL countdown starts from set time, not access time

### LRU Eviction
- [ ] Max cache size configurable (default: 100 entries)
- [ ] Least recently used entries evicted when cache full
- [ ] Access (get) updates LRU order (move to end)
- [ ] Set updates LRU order (move to end)
- [ ] Eviction only occurs when adding new key and cache full
- [ ] Updating existing key does not trigger eviction
- [ ] LRU order maintained efficiently (O(1) operations)

### Thread Safety
- [ ] Thread-safe access with locks (threading.Lock)
- [ ] No race conditions in concurrent access
- [ ] Lock-free reads when possible (read-write lock consideration)
- [ ] Atomic operations (get, set, invalidate)
- [ ] No deadlocks possible
- [ ] Concurrent access stress tested (100+ threads)

### Cache Metrics
- [ ] Track cache hits (successful get operations)
- [ ] Track cache misses (failed get operations)
- [ ] Track evictions (LRU removals)
- [ ] Track expirations (TTL removals)
- [ ] Track cache size (current entry count)
- [ ] Track memory usage estimate (bytes)
- [ ] `get_statistics()` returns comprehensive metrics dict
- [ ] `reset_statistics()` clears metrics counters
- [ ] Cache hit rate >80% in typical usage (monitored)

### Performance
- [ ] Get operation completes in <1ms (p99)
- [ ] Set operation completes in <1ms (p99)
- [ ] get_or_load completes in <1ms for cached values
- [ ] Thread lock overhead <0.1ms
- [ ] Memory overhead <10% of cached data size
- [ ] No performance degradation with cache size up to 1000 entries

---

## Technical Notes

### Complete ContextCache Implementation

```python
# gao_dev/core/context/context_cache.py
from collections import OrderedDict
from datetime import datetime, timedelta
from threading import Lock, RLock
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
```

**Files to Create:**
- `gao_dev/core/context/__init__.py`
- `gao_dev/core/context/context_cache.py`
- `tests/core/context/__init__.py`
- `tests/core/context/test_context_cache.py`
- `tests/core/context/test_context_cache_concurrency.py`

**Dependencies:** None (foundational)

---

## Testing Requirements

### Unit Tests

**Core Operations:**
- [ ] Test `get()` returns cached value
- [ ] Test `get()` returns None for missing key
- [ ] Test `set()` caches value
- [ ] Test `set()` updates existing key
- [ ] Test `invalidate()` removes key
- [ ] Test `clear()` removes all keys
- [ ] Test `has_key()` checks existence
- [ ] Test `keys()` returns valid keys

**TTL Expiration:**
- [ ] Test expired entries return None
- [ ] Test expired entries removed on access
- [ ] Test custom TTL per key
- [ ] Test default TTL used when not specified
- [ ] Test `keys()` removes expired entries
- [ ] Test expiration metrics incremented

**LRU Eviction:**
- [ ] Test eviction when cache full
- [ ] Test LRU order maintained
- [ ] Test access updates LRU order
- [ ] Test eviction metrics incremented
- [ ] Test updating existing key does not evict

**Lazy Loading:**
- [ ] Test `get_or_load()` returns cached value
- [ ] Test `get_or_load()` calls loader on miss
- [ ] Test `get_or_load()` caches loaded value
- [ ] Test loader only called once for same key

**Metrics:**
- [ ] Test hit counter increments on get hit
- [ ] Test miss counter increments on get miss
- [ ] Test eviction counter increments on eviction
- [ ] Test expiration counter increments on expiration
- [ ] Test `get_statistics()` returns correct values
- [ ] Test `reset_statistics()` clears counters
- [ ] Test hit rate calculation

### Concurrency Tests
- [ ] Test concurrent get operations (100 threads)
- [ ] Test concurrent set operations (100 threads)
- [ ] Test mixed concurrent operations
- [ ] Test no race conditions
- [ ] Test no deadlocks
- [ ] Test thread-safe metrics

### Performance Tests
- [ ] Test get operation <1ms (p99)
- [ ] Test set operation <1ms (p99)
- [ ] Test get_or_load <1ms for cached values
- [ ] Test lock overhead <0.1ms
- [ ] Test no degradation with 1000 entries

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Code documentation (docstrings) for all methods
- [ ] API documentation with usage examples
- [ ] Performance characteristics documentation
- [ ] Thread-safety guarantees documentation
- [ ] Cache tuning guide (TTL, max_size)
- [ ] Metrics interpretation guide
- [ ] Integration examples with DocumentLifecycleManager
- [ ] Troubleshooting guide for cache issues

---

## Implementation Details

### Development Approach

**Phase 1: Core Cache**
1. Implement basic get/set operations
2. Add LRU eviction with OrderedDict
3. Add TTL expiration checking
4. Write unit tests for core operations

**Phase 2: Thread Safety**
1. Add thread locks (RLock)
2. Make all operations atomic
3. Write concurrency tests
4. Verify no race conditions

**Phase 3: Metrics & Optimization**
1. Add comprehensive metrics
2. Add get_or_load for lazy loading
3. Optimize lock granularity
4. Add performance tests

### Quality Gates
- [ ] All unit tests pass with >80% coverage
- [ ] Concurrency tests pass with 100+ threads
- [ ] Performance benchmarks met (<1ms operations)
- [ ] Thread safety verified with stress testing
- [ ] Documentation complete with examples

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Core cache operations implemented (get, set, invalidate, clear)
- [ ] TTL expiration working correctly
- [ ] LRU eviction working correctly
- [ ] Thread-safe concurrent access verified
- [ ] Comprehensive metrics implemented
- [ ] Lazy loading (get_or_load) working
- [ ] Tests passing (>80% coverage)
- [ ] Performance benchmarks met (<1ms operations)
- [ ] Concurrency tests pass (100+ threads)
- [ ] Code reviewed and approved
- [ ] Documentation complete with examples
- [ ] No regression in existing functionality
- [ ] Committed with atomic commit message:
  ```
  feat(epic-16): implement Story 16.1 - ContextCache Implementation

  - Implement thread-safe LRU cache with TTL expiration
  - Add comprehensive metrics (hits, misses, evictions, expirations)
  - Support per-key TTL override
  - Implement lazy loading with get_or_load
  - Add O(1) get/set operations with OrderedDict
  - Implement reentrant lock for thread safety
  - Add comprehensive unit tests (>80% coverage)
  - Performance optimizations (<1ms operations)

  Generated with GAO-Dev
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```

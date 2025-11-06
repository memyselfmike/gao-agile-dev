"""
Concurrency tests for ContextCache.

Tests thread safety and concurrent access patterns:
- Concurrent get operations
- Concurrent set operations
- Mixed concurrent operations
- Race condition detection
- Deadlock prevention
- Thread-safe metrics
"""

import threading
import time
from datetime import timedelta
import pytest
from gao_dev.core.context.context_cache import ContextCache


class TestConcurrentGet:
    """Test concurrent get operations."""

    def test_concurrent_get_operations(self):
        """Test 100 threads reading from cache simultaneously."""
        cache = ContextCache()
        cache.set("key1", "value1")

        results = []
        errors = []

        def read_operation():
            try:
                for _ in range(100):
                    result = cache.get("key1")
                    results.append(result)
            except Exception as e:
                errors.append(e)

        # Create 100 threads
        threads = [threading.Thread(target=read_operation) for _ in range(100)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify no errors
        assert len(errors) == 0

        # Verify all reads returned correct value
        assert all(r == "value1" for r in results)
        assert len(results) == 10000  # 100 threads * 100 reads

    def test_concurrent_get_with_misses(self):
        """Test concurrent get operations with cache misses."""
        cache = ContextCache()

        results = []
        errors = []

        def read_operation():
            try:
                for i in range(100):
                    result = cache.get(f"key{i}")
                    results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=read_operation) for _ in range(50)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0
        assert all(r is None for r in results)


class TestConcurrentSet:
    """Test concurrent set operations."""

    def test_concurrent_set_operations(self):
        """Test 100 threads writing to cache simultaneously."""
        cache = ContextCache()

        errors = []

        def write_operation(thread_id):
            try:
                for i in range(100):
                    cache.set(f"key_{thread_id}_{i}", f"value_{thread_id}_{i}")
            except Exception as e:
                errors.append(e)

        # Create 100 threads
        threads = [threading.Thread(target=write_operation, args=(i,)) for i in range(100)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify no errors
        assert len(errors) == 0

        # Verify cache integrity
        stats = cache.get_statistics()
        assert stats["size"] <= cache._max_size

    def test_concurrent_set_same_key(self):
        """Test multiple threads updating the same key."""
        cache = ContextCache()

        errors = []

        def write_operation(thread_id):
            try:
                for _ in range(100):
                    cache.set("shared_key", f"value_from_thread_{thread_id}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=write_operation, args=(i,)) for i in range(50)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0

        # Verify key exists with some valid value
        result = cache.get("shared_key")
        assert result is not None
        assert result.startswith("value_from_thread_")


class TestMixedConcurrentOperations:
    """Test mixed concurrent operations."""

    def test_concurrent_read_write_operations(self):
        """Test concurrent mix of reads and writes."""
        cache = ContextCache()

        # Pre-populate cache
        for i in range(50):
            cache.set(f"key{i}", f"value{i}")

        errors = []
        read_results = []

        def read_operation():
            try:
                for i in range(100):
                    result = cache.get(f"key{i % 50}")
                    read_results.append(result)
            except Exception as e:
                errors.append(e)

        def write_operation():
            try:
                for i in range(100):
                    cache.set(f"key{i % 50}", f"updated_value{i}")
            except Exception as e:
                errors.append(e)

        # Create mix of reader and writer threads
        threads = []
        threads.extend([threading.Thread(target=read_operation) for _ in range(50)])
        threads.extend([threading.Thread(target=write_operation) for _ in range(50)])

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify no errors
        assert len(errors) == 0

        # Verify cache is still functional
        assert cache.get("key0") is not None

    def test_concurrent_invalidate_operations(self):
        """Test concurrent invalidate operations."""
        cache = ContextCache()

        # Pre-populate cache
        for i in range(100):
            cache.set(f"key{i}", f"value{i}")

        errors = []

        def invalidate_operation():
            try:
                for i in range(100):
                    cache.invalidate(f"key{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=invalidate_operation) for _ in range(10)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0

        # Verify all keys are invalidated
        for i in range(100):
            assert cache.get(f"key{i}") is None

    def test_concurrent_clear_operations(self):
        """Test concurrent clear operations."""
        cache = ContextCache()

        errors = []

        def mixed_operation():
            try:
                for i in range(50):
                    cache.set(f"key{i}", f"value{i}")
                    cache.clear()
                    cache.set(f"key{i}", f"value{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=mixed_operation) for _ in range(20)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0


class TestRaceConditions:
    """Test for race conditions."""

    def test_no_race_condition_in_lru_eviction(self):
        """Test LRU eviction is thread-safe."""
        cache = ContextCache(max_size=50)

        errors = []

        def write_operation(thread_id):
            try:
                for i in range(100):
                    cache.set(f"key_{thread_id}_{i}", f"value_{thread_id}_{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=write_operation, args=(i,)) for i in range(20)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0

        # Verify cache size is within limits
        assert len(cache) <= cache._max_size

    def test_no_race_condition_in_expiration(self):
        """Test TTL expiration is thread-safe."""
        cache = ContextCache(ttl=timedelta(seconds=0.2))

        errors = []
        results = []

        def mixed_operation():
            try:
                cache.set("shared_key", "value")
                time.sleep(0.1)
                result = cache.get("shared_key")
                results.append(("before_expiry", result))
                time.sleep(0.15)
                result = cache.get("shared_key")
                results.append(("after_expiry", result))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=mixed_operation) for _ in range(20)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0

        # Verify expired entries return None
        after_expiry_results = [r[1] for r in results if r[0] == "after_expiry"]
        assert all(r is None for r in after_expiry_results)

    def test_no_race_condition_in_get_or_load(self):
        """Test get_or_load is thread-safe."""
        cache = ContextCache()

        load_count = {"count": 0}
        errors = []
        results = []

        def loader():
            load_count["count"] += 1
            time.sleep(0.01)  # Simulate slow load
            return f"loaded_value_{load_count['count']}"

        def load_operation():
            try:
                result = cache.get_or_load("shared_key", loader)
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Create threads that all try to load same key
        threads = [threading.Thread(target=load_operation) for _ in range(50)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0

        # Loader should be called multiple times due to race condition
        # but all results should be valid loaded values
        assert all(r is not None for r in results)
        assert all(r.startswith("loaded_value_") for r in results)


class TestThreadSafeMetrics:
    """Test thread-safe metrics tracking."""

    def test_metrics_accuracy_under_concurrency(self):
        """Test metrics remain accurate under concurrent load."""
        cache = ContextCache()

        # Pre-populate cache
        for i in range(50):
            cache.set(f"key{i}", f"value{i}")

        errors = []

        def mixed_operation(thread_id):
            try:
                for i in range(100):
                    # Mix of hits and misses
                    cache.get(f"key{i % 50}")  # Hit
                    cache.get(f"nonexistent_{thread_id}_{i}")  # Miss
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=mixed_operation, args=(i,)) for i in range(50)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0

        # Verify metrics
        stats = cache.get_statistics()
        assert stats["hits"] == 5000  # 50 threads * 100 hits each
        assert stats["misses"] == 5000  # 50 threads * 100 misses each
        assert stats["hit_rate"] == 0.5

    def test_concurrent_statistics_access(self):
        """Test get_statistics is thread-safe."""
        cache = ContextCache()

        errors = []
        stats_results = []

        def operation():
            try:
                for i in range(50):
                    cache.set(f"key{i}", f"value{i}")
                    stats = cache.get_statistics()
                    stats_results.append(stats)
                    cache.get(f"key{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=operation) for _ in range(20)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0

        # Verify all stats are valid
        for stats in stats_results:
            assert "hits" in stats
            assert "misses" in stats
            assert "size" in stats
            assert "hit_rate" in stats
            assert stats["hit_rate"] >= 0.0
            assert stats["hit_rate"] <= 1.0

    def test_concurrent_reset_statistics(self):
        """Test reset_statistics is thread-safe."""
        cache = ContextCache()

        errors = []

        def operation():
            try:
                for i in range(50):
                    cache.set(f"key{i}", f"value{i}")
                    cache.get(f"key{i}")
                    if i % 10 == 0:
                        cache.reset_statistics()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=operation) for _ in range(20)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0

        # Verify cache is still functional
        stats = cache.get_statistics()
        assert isinstance(stats["hits"], int)
        assert isinstance(stats["misses"], int)


class TestDeadlockPrevention:
    """Test deadlock prevention."""

    def test_no_deadlock_with_nested_operations(self):
        """Test no deadlock occurs with complex operation sequences."""
        cache = ContextCache()

        errors = []
        completed = []

        def complex_operation(thread_id):
            try:
                for i in range(50):
                    cache.set(f"key{thread_id}_{i}", f"value{i}")
                    cache.get(f"key{thread_id}_{i}")
                    cache.has_key(f"key{thread_id}_{i}")
                    if i % 10 == 0:
                        cache.keys()
                        cache.get_statistics()
                    if i % 20 == 0:
                        cache.clear()
                completed.append(thread_id)
            except Exception as e:
                errors.append((thread_id, e))

        threads = [threading.Thread(target=complex_operation, args=(i,)) for i in range(50)]

        for thread in threads:
            thread.start()

        # Wait with timeout to detect deadlock
        for thread in threads:
            thread.join(timeout=10.0)

        # Verify all threads completed
        assert len(errors) == 0
        assert len(completed) == 50

    def test_no_deadlock_with_get_or_load(self):
        """Test no deadlock with concurrent get_or_load."""
        cache = ContextCache()

        errors = []
        completed = []

        def loader():
            time.sleep(0.01)
            return "loaded_value"

        def operation(thread_id):
            try:
                for i in range(20):
                    cache.get_or_load(f"key{i}", loader)
                completed.append(thread_id)
            except Exception as e:
                errors.append((thread_id, e))

        threads = [threading.Thread(target=operation, args=(i,)) for i in range(50)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join(timeout=10.0)

        assert len(errors) == 0
        assert len(completed) == 50


class TestPerformanceUnderConcurrency:
    """Test performance characteristics under concurrent load."""

    def test_no_performance_degradation(self):
        """Test cache performance doesn't degrade under concurrent load."""
        cache = ContextCache(max_size=1000)

        # Pre-populate cache
        for i in range(500):
            cache.set(f"key{i}", f"value{i}")

        errors = []
        timings = []

        def timed_operation():
            try:
                start = time.time()
                for i in range(100):
                    cache.get(f"key{i % 500}")
                elapsed = time.time() - start
                timings.append(elapsed)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=timed_operation) for _ in range(100)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0

        # Verify average operation time is reasonable
        avg_time_per_op = sum(timings) / (len(timings) * 100)
        assert avg_time_per_op < 0.001  # Less than 1ms per operation

    def test_lock_overhead(self):
        """Test lock overhead is minimal."""
        cache = ContextCache()

        cache.set("key1", "value1")

        # Measure time for operations
        start = time.time()
        for _ in range(10000):
            cache.get("key1")
        elapsed = time.time() - start

        # Should be very fast
        avg_time = elapsed / 10000
        assert avg_time < 0.0001  # Less than 0.1ms per operation

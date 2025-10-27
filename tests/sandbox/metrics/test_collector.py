"""Tests for metrics collector.

Tests the central MetricsCollector class including singleton pattern,
thread safety, and all collection methods.
"""

import pytest
import time
import threading

from gao_dev.sandbox.metrics.collector import MetricsCollector


@pytest.fixture
def collector():
    """Create a fresh collector for testing."""
    collector = MetricsCollector()
    collector.reset()
    yield collector
    collector.reset()


class TestMetricsCollector:
    """Tests for MetricsCollector class."""

    def test_singleton_pattern(self):
        """Test MetricsCollector is singleton."""
        collector1 = MetricsCollector()
        collector2 = MetricsCollector()

        assert collector1 is collector2
        assert id(collector1) == id(collector2)

    def test_start_stop_collection(self, collector):
        """Test collection lifecycle."""
        assert not collector.is_collecting()

        collector.start_collection("test-project", "test-benchmark")

        assert collector.is_collecting()
        assert collector.project_name == "test-project"
        assert collector.benchmark_name == "test-benchmark"
        assert collector.run_id is not None

        metrics = collector.stop_collection()

        assert not collector.is_collecting()
        assert metrics.project_name == "test-project"
        assert metrics.benchmark_name == "test-benchmark"

    def test_timer_operations(self, collector):
        """Test start/stop timer."""
        collector.start_collection("test", "test")

        collector.start_timer("test_operation")
        time.sleep(0.1)  # Sleep for 100ms
        elapsed = collector.stop_timer("test_operation")

        assert elapsed >= 0.1
        assert elapsed < 0.2  # Should not be too long

        # Check that timer value was recorded
        assert collector.get_value("test_operation_time") is not None

    def test_counter_operations(self, collector):
        """Test increment counter."""
        collector.start_collection("test", "test")

        # Increment by 1
        collector.increment_counter("test_counter")
        assert collector.get_counter("test_counter") == 1

        # Increment by 5
        collector.increment_counter("test_counter", 5)
        assert collector.get_counter("test_counter") == 6

        # Get non-existent counter with default
        assert collector.get_counter("nonexistent", 99) == 99

    def test_value_operations(self, collector):
        """Test set/get value."""
        collector.start_collection("test", "test")

        # Set and get value
        collector.set_value("test_value", 42)
        assert collector.get_value("test_value") == 42

        # Set string value
        collector.set_value("test_string", "hello")
        assert collector.get_value("test_string") == "hello"

        # Get non-existent value with default
        assert collector.get_value("nonexistent", "default") == "default"

    def test_event_recording(self, collector):
        """Test record event."""
        collector.start_collection("test", "test")

        collector.record_event("test_event", {"key": "value", "number": 123})

        assert len(collector.events) == 1
        event = collector.events[0]
        assert event["type"] == "test_event"
        assert event["data"]["key"] == "value"
        assert event["data"]["number"] == 123
        assert "timestamp" in event

    def test_get_current_metrics(self, collector):
        """Test metrics snapshot."""
        collector.start_collection("snapshot-test", "snapshot-bench")

        # Set some values
        collector.increment_counter("test_counter", 10)
        collector.set_value("test_value", "test")
        collector.start_timer("phase_1")
        time.sleep(0.05)
        collector.stop_timer("phase_1")

        metrics = collector.get_current_metrics()

        assert metrics.run_id == collector.run_id
        assert metrics.project_name == "snapshot-test"
        assert metrics.benchmark_name == "snapshot-bench"
        assert metrics.performance.total_time_seconds > 0
        assert "phase_1" in metrics.performance.phase_times
        assert metrics.metadata["counters"]["test_counter"] == 10

    def test_reset(self, collector):
        """Test reset clears all data."""
        collector.start_collection("test", "test")

        # Add some data
        collector.increment_counter("counter", 5)
        collector.set_value("value", 42)
        collector.record_event("event", {"data": "test"})
        collector.start_timer("timer")

        # Reset
        collector.reset()

        # Verify everything is cleared
        assert collector.get_counter("counter") == 0
        assert collector.get_value("value") is None
        assert len(collector.events) == 0
        assert not collector.is_collecting()

    def test_context_manager(self, collector):
        """Test using as context manager."""
        with collector as c:
            c.start_collection("context-test", "context-bench")
            c.increment_counter("test")
            assert c.is_collecting()

        # After context, collection should be stopped
        assert not collector.is_collecting()

    def test_thread_safety_counters(self, collector):
        """Test concurrent counter increments."""
        collector.start_collection("thread-test", "thread-bench")

        def increment_many():
            for _ in range(100):
                collector.increment_counter("shared_counter")

        # Start 10 threads
        threads = []
        for _ in range(10):
            t = threading.Thread(target=increment_many)
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Should be exactly 1000 (10 threads * 100 increments)
        assert collector.get_counter("shared_counter") == 1000

    def test_thread_safety_values(self, collector):
        """Test concurrent value sets."""
        collector.start_collection("thread-test", "thread-bench")

        def set_values(thread_id):
            for i in range(50):
                collector.set_value(f"value_{thread_id}", i)

        # Start 5 threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=set_values, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Verify all thread values exist
        for i in range(5):
            value = collector.get_value(f"value_{i}")
            assert value is not None
            assert 0 <= value < 50

    def test_thread_safety_events(self, collector):
        """Test concurrent event recording."""
        collector.start_collection("thread-test", "thread-bench")

        def record_events(thread_id):
            for i in range(20):
                collector.record_event("test_event", {"thread": thread_id, "index": i})

        # Start 5 threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=record_events, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Should have exactly 100 events (5 threads * 20 events)
        assert len(collector.events) == 100

    def test_stop_timer_nonexistent(self, collector):
        """Test stopping timer that was never started."""
        collector.start_collection("test", "test")

        elapsed = collector.stop_timer("never_started")

        assert elapsed == 0.0

    def test_multiple_timers(self, collector):
        """Test multiple concurrent timers."""
        collector.start_collection("test", "test")

        collector.start_timer("timer1")
        time.sleep(0.05)
        collector.start_timer("timer2")
        time.sleep(0.05)
        elapsed1 = collector.stop_timer("timer1")
        elapsed2 = collector.stop_timer("timer2")

        assert elapsed1 >= 0.10  # timer1 ran for ~0.10s
        assert elapsed2 >= 0.05  # timer2 ran for ~0.05s
        assert elapsed1 > elapsed2

    def test_reset_between_runs(self, collector):
        """Test reset clears previous run data."""
        # First run
        collector.start_collection("run1", "bench1")
        collector.increment_counter("counter", 10)
        run1_id = collector.run_id
        metrics1 = collector.stop_collection()

        # Second run
        collector.start_collection("run2", "bench2")
        run2_id = collector.run_id
        metrics2 = collector.stop_collection()

        # Run IDs should be different
        assert run1_id != run2_id
        assert metrics1.run_id != metrics2.run_id

        # Counter should be reset
        assert collector.get_counter("counter") == 0

    def test_phase_times_in_metrics(self, collector):
        """Test that phase times are included in metrics."""
        collector.start_collection("test", "test")

        collector.start_timer("phase_planning")
        time.sleep(0.05)
        collector.stop_timer("phase_planning")

        collector.start_timer("phase_implementation")
        time.sleep(0.05)
        collector.stop_timer("phase_implementation")

        metrics = collector.get_current_metrics()

        assert "phase_planning" in metrics.performance.phase_times
        assert "phase_implementation" in metrics.performance.phase_times
        assert metrics.performance.phase_times["phase_planning"] >= 0.05
        assert metrics.performance.phase_times["phase_implementation"] >= 0.05

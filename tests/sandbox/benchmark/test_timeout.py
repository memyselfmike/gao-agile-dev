"""Tests for timeout management."""

import pytest
import time
import threading
from datetime import datetime
from unittest.mock import Mock, MagicMock

from gao_dev.sandbox.benchmark.timeout import (
    TimeoutManager,
    TimeoutInfo,
    TimeoutStatus,
    TimeoutContext,
)


class TestTimeoutStatus:
    """Tests for TimeoutStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert TimeoutStatus.ACTIVE.value == "active"
        assert TimeoutStatus.COMPLETED.value == "completed"
        assert TimeoutStatus.TIMEOUT.value == "timeout"
        assert TimeoutStatus.CANCELLED.value == "cancelled"


class TestTimeoutInfo:
    """Tests for TimeoutInfo."""

    def test_creation(self):
        """Test creating timeout info."""
        start = datetime.now()
        info = TimeoutInfo(
            name="test",
            timeout_seconds=60,
            start_time=start,
            grace_period_seconds=30,
        )
        assert info.name == "test"
        assert info.timeout_seconds == 60
        assert info.start_time == start
        assert info.status == TimeoutStatus.ACTIVE
        assert info.grace_period_seconds == 30

    def test_elapsed_seconds(self):
        """Test calculating elapsed seconds."""
        start = datetime.now()
        info = TimeoutInfo(
            name="test", timeout_seconds=60, start_time=start
        )
        time.sleep(0.1)
        elapsed = info.elapsed_seconds
        assert elapsed > 0.09
        assert elapsed < 1.0

    def test_remaining_seconds(self):
        """Test calculating remaining seconds."""
        start = datetime.now()
        info = TimeoutInfo(
            name="test", timeout_seconds=10, start_time=start
        )
        remaining = info.remaining_seconds
        assert 9.0 < remaining <= 10.0

    def test_is_timeout(self):
        """Test checking if timeout reached."""
        start = datetime.now()

        # Not timed out
        info = TimeoutInfo(
            name="test", timeout_seconds=10, start_time=start
        )
        assert info.is_timeout is False

        # Timed out (simulate by setting start time in past)
        from datetime import timedelta
        past = start - timedelta(seconds=11)
        info = TimeoutInfo(
            name="test", timeout_seconds=10, start_time=past
        )
        assert info.is_timeout is True


class TestTimeoutManager:
    """Tests for TimeoutManager."""

    def test_manager_creation(self):
        """Test creating TimeoutManager."""
        manager = TimeoutManager()
        assert manager is not None
        assert len(manager.timeouts) == 0

    def test_start_timeout(self):
        """Test starting a timeout."""
        manager = TimeoutManager()
        info = manager.start_timeout("test", 60)

        assert info.name == "test"
        assert info.timeout_seconds == 60
        assert info.status == TimeoutStatus.ACTIVE
        assert "test" in manager.timeouts

    def test_start_duplicate_timeout_raises(self):
        """Test that starting duplicate timeout raises error."""
        manager = TimeoutManager()
        manager.start_timeout("test", 60)

        with pytest.raises(ValueError, match="already exists"):
            manager.start_timeout("test", 30)

    def test_complete_timeout(self):
        """Test completing a timeout successfully."""
        manager = TimeoutManager()
        manager.start_timeout("test", 60)

        manager.complete_timeout("test")

        timeout_info = manager.timeouts["test"]
        assert timeout_info.status == TimeoutStatus.COMPLETED
        assert timeout_info.end_time is not None

    def test_cancel_timeout(self):
        """Test cancelling a timeout."""
        manager = TimeoutManager()
        manager.start_timeout("test", 60)

        manager.cancel_timeout("test")

        timeout_info = manager.timeouts["test"]
        assert timeout_info.status == TimeoutStatus.CANCELLED
        assert timeout_info.end_time is not None

    def test_get_remaining_time(self):
        """Test getting remaining time."""
        manager = TimeoutManager()
        manager.start_timeout("test", 10)

        remaining = manager.get_remaining_time("test")
        assert 9.0 < remaining <= 10.0

    def test_get_remaining_time_nonexistent(self):
        """Test getting remaining time for nonexistent timeout."""
        manager = TimeoutManager()
        remaining = manager.get_remaining_time("nonexistent")
        assert remaining == 0.0

    def test_is_timeout(self):
        """Test checking if timeout reached."""
        manager = TimeoutManager()
        manager.start_timeout("test", 10)

        assert manager.is_timeout("test") is False

    def test_is_timeout_nonexistent(self):
        """Test checking timeout for nonexistent timeout."""
        manager = TimeoutManager()
        assert manager.is_timeout("nonexistent") is False

    def test_get_status(self):
        """Test getting timeout status."""
        manager = TimeoutManager()
        manager.start_timeout("test", 60)

        status = manager.get_status("test")
        assert status == TimeoutStatus.ACTIVE

        manager.complete_timeout("test")
        status = manager.get_status("test")
        assert status == TimeoutStatus.COMPLETED

    def test_get_status_nonexistent(self):
        """Test getting status for nonexistent timeout."""
        manager = TimeoutManager()
        status = manager.get_status("nonexistent")
        assert status is None

    def test_timeout_reached(self):
        """Test timeout detection when time expires."""
        manager = TimeoutManager()
        handler = Mock()

        manager.start_timeout("test", 1, on_timeout=handler)

        # Wait for timeout to trigger
        time.sleep(2.0)

        # Check status
        timeout_info = manager.timeouts["test"]
        assert timeout_info.status == TimeoutStatus.TIMEOUT

        # Handler should have been called
        handler.assert_called_once()

    def test_timeout_handler_called(self):
        """Test that timeout handler is called on timeout."""
        manager = TimeoutManager()
        handler = Mock()

        manager.start_timeout("test", 1, on_timeout=handler)

        # Wait for timeout
        time.sleep(2.0)

        handler.assert_called_once()

    def test_timeout_handler_error_handled(self):
        """Test that handler errors don't crash monitoring."""
        manager = TimeoutManager()
        handler = Mock(side_effect=Exception("Handler error"))

        manager.start_timeout("test", 1, on_timeout=handler)

        # Wait for timeout
        time.sleep(2.0)

        # Should still mark as timeout even if handler failed
        timeout_info = manager.timeouts["test"]
        assert timeout_info.status == TimeoutStatus.TIMEOUT

    def test_concurrent_timeouts(self):
        """Test multiple concurrent timeouts."""
        manager = TimeoutManager()

        manager.start_timeout("test1", 60)
        manager.start_timeout("test2", 120)
        manager.start_timeout("test3", 180)

        assert len(manager.timeouts) == 3
        assert manager.get_status("test1") == TimeoutStatus.ACTIVE
        assert manager.get_status("test2") == TimeoutStatus.ACTIVE
        assert manager.get_status("test3") == TimeoutStatus.ACTIVE

    def test_cleanup(self):
        """Test cleanup cancels active timeouts."""
        manager = TimeoutManager()

        manager.start_timeout("test1", 60)
        manager.start_timeout("test2", 120)

        manager.cleanup()

        # Both should be cancelled
        assert manager.get_status("test1") == TimeoutStatus.CANCELLED
        assert manager.get_status("test2") == TimeoutStatus.CANCELLED

    def test_graceful_shutdown_success(self):
        """Test graceful shutdown of process."""
        manager = TimeoutManager()
        manager.start_timeout("test", 60, grace_period_seconds=5)

        # Mock process
        process = Mock()
        process.wait = Mock(return_value=None)

        result = manager.graceful_shutdown("test", process)

        assert result is True
        process.terminate.assert_called_once()
        process.wait.assert_called_once()

    def test_graceful_shutdown_forced_kill(self):
        """Test forced kill when grace period expires."""
        manager = TimeoutManager()
        manager.start_timeout("test", 60, grace_period_seconds=1)

        # Mock process that doesn't terminate gracefully
        process = Mock()
        process.wait = Mock(side_effect=Exception("Timeout"))

        result = manager.graceful_shutdown("test", process)

        assert result is False
        process.terminate.assert_called_once()
        process.kill.assert_called_once()

    def test_graceful_shutdown_no_timeout(self):
        """Test graceful shutdown with nonexistent timeout."""
        manager = TimeoutManager()

        process = Mock()
        result = manager.graceful_shutdown("nonexistent", process)

        assert result is False


class TestTimeoutContext:
    """Tests for TimeoutContext context manager."""

    def test_context_manager_success(self):
        """Test context manager with successful completion."""
        manager = TimeoutManager()

        with TimeoutContext(manager, "test", 60):
            time.sleep(0.1)

        # Should be completed
        status = manager.get_status("test")
        assert status == TimeoutStatus.COMPLETED

    def test_context_manager_with_exception(self):
        """Test context manager with exception."""
        manager = TimeoutManager()

        with pytest.raises(ValueError):
            with TimeoutContext(manager, "test", 60):
                raise ValueError("Test error")

        # Should be cancelled
        status = manager.get_status("test")
        assert status == TimeoutStatus.CANCELLED

    def test_context_manager_with_handler(self):
        """Test context manager with timeout handler."""
        manager = TimeoutManager()
        handler = Mock()

        with TimeoutContext(manager, "test", 1, on_timeout=handler):
            # Wait for timeout to occur
            time.sleep(2.0)

        # Handler should have been called
        handler.assert_called_once()

        # Even though timeout occurred, context exited normally so marked as completed
        status = manager.get_status("test")
        assert status == TimeoutStatus.COMPLETED

    def test_context_manager_nested(self):
        """Test nested context managers."""
        manager = TimeoutManager()

        with TimeoutContext(manager, "outer", 60):
            with TimeoutContext(manager, "inner", 30):
                time.sleep(0.1)

        # Both should be completed
        assert manager.get_status("outer") == TimeoutStatus.COMPLETED
        assert manager.get_status("inner") == TimeoutStatus.COMPLETED

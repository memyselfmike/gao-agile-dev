"""Tests for provider performance tracker."""

import pytest

from gao_dev.core.providers.performance_tracker import ProviderPerformanceTracker


class TestProviderPerformanceTracker:
    """Test performance tracker."""

    def test_initialization(self):
        """Test tracker initializes correctly."""
        tracker = ProviderPerformanceTracker()

        assert tracker._execution_times is not None

    def test_records_execution_time(self):
        """Test records execution time."""
        tracker = ProviderPerformanceTracker()

        tracker.record_execution_time("claude-code", "sonnet-4.5", 1.5)

        avg_time = tracker.get_avg_execution_time("claude-code", "sonnet-4.5")
        assert avg_time == 1.5

    def test_calculates_average_execution_time(self):
        """Test calculates average of multiple recordings."""
        tracker = ProviderPerformanceTracker()

        tracker.record_execution_time("claude-code", "sonnet-4.5", 1.0)
        tracker.record_execution_time("claude-code", "sonnet-4.5", 2.0)
        tracker.record_execution_time("claude-code", "sonnet-4.5", 3.0)

        avg_time = tracker.get_avg_execution_time("claude-code", "sonnet-4.5")
        assert avg_time == 2.0

    def test_returns_infinity_for_no_data(self):
        """Test returns infinity if no performance data."""
        tracker = ProviderPerformanceTracker()

        avg_time = tracker.get_avg_execution_time("unknown", "unknown")

        assert avg_time == float("inf")

    def test_tracks_multiple_providers(self):
        """Test tracks multiple providers independently."""
        tracker = ProviderPerformanceTracker()

        tracker.record_execution_time("claude-code", "sonnet-4.5", 1.0)
        tracker.record_execution_time("opencode", "sonnet-4.5", 2.0)

        claude_avg = tracker.get_avg_execution_time("claude-code", "sonnet-4.5")
        opencode_avg = tracker.get_avg_execution_time("opencode", "sonnet-4.5")

        assert claude_avg == 1.0
        assert opencode_avg == 2.0

    def test_tracks_multiple_models(self):
        """Test tracks multiple models independently."""
        tracker = ProviderPerformanceTracker()

        tracker.record_execution_time("claude-code", "sonnet-4.5", 1.0)
        tracker.record_execution_time("claude-code", "haiku-3", 0.5)

        sonnet_avg = tracker.get_avg_execution_time("claude-code", "sonnet-4.5")
        haiku_avg = tracker.get_avg_execution_time("claude-code", "haiku-3")

        assert sonnet_avg == 1.0
        assert haiku_avg == 0.5

    def test_get_all_stats(self):
        """Test gets all performance statistics."""
        tracker = ProviderPerformanceTracker()

        tracker.record_execution_time("claude-code", "sonnet-4.5", 1.0)
        tracker.record_execution_time("claude-code", "sonnet-4.5", 2.0)
        tracker.record_execution_time("opencode", "sonnet-4.5", 3.0)

        stats = tracker.get_all_stats()

        assert "claude-code" in stats
        assert "opencode" in stats
        assert stats["claude-code"]["sonnet-4.5"]["avg"] == 1.5
        assert stats["claude-code"]["sonnet-4.5"]["min"] == 1.0
        assert stats["claude-code"]["sonnet-4.5"]["max"] == 2.0
        assert stats["claude-code"]["sonnet-4.5"]["count"] == 2

    def test_clear(self):
        """Test clears all performance data."""
        tracker = ProviderPerformanceTracker()

        tracker.record_execution_time("claude-code", "sonnet-4.5", 1.0)

        tracker.clear()

        avg_time = tracker.get_avg_execution_time("claude-code", "sonnet-4.5")
        assert avg_time == float("inf")

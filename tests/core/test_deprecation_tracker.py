"""Tests for the deprecation tracker module."""

import json
import os
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from gao_dev.core.deprecation_tracker import (
    DeprecationTracker,
    get_tracker,
    track_deprecated_command,
)


class TestDeprecationTracker:
    """Tests for DeprecationTracker class."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self) -> None:
        """Reset singleton before each test."""
        DeprecationTracker.reset_singleton()
        yield
        DeprecationTracker.reset_singleton()

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        """Create a temporary storage path."""
        return tmp_path / "deprecation_events.json"

    def test_tracker_singleton_pattern(self, temp_storage: Path) -> None:
        """Test that tracker uses singleton pattern."""
        tracker1 = DeprecationTracker(temp_storage)
        tracker2 = DeprecationTracker(temp_storage)

        assert tracker1 is tracker2

    def test_track_usage_logs_event(self, temp_storage: Path) -> None:
        """Test that track_usage logs an event."""
        tracker = DeprecationTracker(temp_storage)

        tracker.track_usage(
            command="gao-dev init",
            replacement="gao-dev start",
            removal_version="v3.0",
        )

        stats = tracker.get_usage_stats()
        assert stats["total_calls"] == 1
        assert stats["commands"]["gao-dev init"] == 1

    def test_track_usage_multiple_commands(self, temp_storage: Path) -> None:
        """Test tracking multiple different commands."""
        tracker = DeprecationTracker(temp_storage)

        tracker.track_usage("gao-dev init", "gao-dev start", "v3.0")
        tracker.track_usage("gao-dev web start", "gao-dev start", "v3.0")
        tracker.track_usage("gao-dev init", "gao-dev start", "v3.0")

        stats = tracker.get_usage_stats()
        assert stats["total_calls"] == 3
        assert stats["commands"]["gao-dev init"] == 2
        assert stats["commands"]["gao-dev web start"] == 1

    def test_track_usage_with_context(self, temp_storage: Path) -> None:
        """Test tracking with additional context."""
        tracker = DeprecationTracker(temp_storage)

        context = {"project_name": "test-project", "user_id": "test-user"}
        tracker.track_usage(
            command="gao-dev init",
            replacement="gao-dev start",
            removal_version="v3.0",
            context=context,
        )

        events = tracker.get_events()
        assert len(events) == 1
        assert events[0]["context"]["project_name"] == "test-project"
        assert events[0]["context"]["user_id"] == "test-user"

    def test_get_usage_stats_empty(self, temp_storage: Path) -> None:
        """Test stats with no events."""
        tracker = DeprecationTracker(temp_storage)

        stats = tracker.get_usage_stats()
        assert stats["total_calls"] == 0
        assert stats["commands"] == {}
        assert stats["first_seen"] is None
        assert stats["last_seen"] is None
        assert stats["ci_percentage"] == 0.0

    def test_get_usage_stats_timestamps(self, temp_storage: Path) -> None:
        """Test that stats include first and last seen timestamps."""
        tracker = DeprecationTracker(temp_storage)

        tracker.track_usage("gao-dev init", "gao-dev start")
        tracker.track_usage("gao-dev web start", "gao-dev start")

        stats = tracker.get_usage_stats()
        assert stats["first_seen"] is not None
        assert stats["last_seen"] is not None
        assert stats["first_seen"] <= stats["last_seen"]

    def test_get_events_all(self, temp_storage: Path) -> None:
        """Test getting all events."""
        tracker = DeprecationTracker(temp_storage)

        for i in range(5):
            tracker.track_usage(f"command-{i}", "replacement")

        events = tracker.get_events()
        assert len(events) == 5

    def test_get_events_filter_by_command(self, temp_storage: Path) -> None:
        """Test filtering events by command."""
        tracker = DeprecationTracker(temp_storage)

        tracker.track_usage("gao-dev init", "gao-dev start")
        tracker.track_usage("gao-dev web start", "gao-dev start")
        tracker.track_usage("gao-dev init", "gao-dev start")

        events = tracker.get_events(command="gao-dev init")
        assert len(events) == 2
        assert all(e["command"] == "gao-dev init" for e in events)

    def test_get_events_filter_by_since(self, temp_storage: Path) -> None:
        """Test filtering events by timestamp."""
        tracker = DeprecationTracker(temp_storage)

        # Track some events
        tracker.track_usage("old-command", "new-command")

        # Get events since future (should be empty)
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        events = tracker.get_events(since=future)
        assert len(events) == 0

        # Get events since past (should include all)
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        events = tracker.get_events(since=past)
        assert len(events) == 1

    def test_get_events_limit(self, temp_storage: Path) -> None:
        """Test event limit."""
        tracker = DeprecationTracker(temp_storage)

        for i in range(20):
            tracker.track_usage(f"command-{i}", "replacement")

        events = tracker.get_events(limit=5)
        assert len(events) == 5

    def test_get_events_sorted_by_timestamp(self, temp_storage: Path) -> None:
        """Test events are sorted by timestamp (most recent first)."""
        tracker = DeprecationTracker(temp_storage)

        tracker.track_usage("first", "replacement")
        tracker.track_usage("second", "replacement")
        tracker.track_usage("third", "replacement")

        events = tracker.get_events()
        assert events[0]["command"] == "third"
        assert events[2]["command"] == "first"

    def test_persistence_save_and_load(self, temp_storage: Path) -> None:
        """Test that events are persisted to storage."""
        tracker = DeprecationTracker(temp_storage)
        tracker.track_usage("gao-dev init", "gao-dev start", "v3.0")

        # Reset singleton and create new tracker with same path
        DeprecationTracker.reset_singleton()
        tracker2 = DeprecationTracker(temp_storage)

        stats = tracker2.get_usage_stats()
        assert stats["total_calls"] == 1
        assert stats["commands"]["gao-dev init"] == 1

    def test_persistence_file_created(self, temp_storage: Path) -> None:
        """Test that storage file is created."""
        tracker = DeprecationTracker(temp_storage)
        tracker.track_usage("gao-dev init", "gao-dev start")

        assert temp_storage.exists()

        with open(temp_storage, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert "events" in data
            assert "stats" in data
            assert "last_updated" in data

    def test_clear_events(self, temp_storage: Path) -> None:
        """Test clearing all events."""
        tracker = DeprecationTracker(temp_storage)

        tracker.track_usage("gao-dev init", "gao-dev start")
        tracker.track_usage("gao-dev web start", "gao-dev start")

        tracker.clear_events()

        stats = tracker.get_usage_stats()
        assert stats["total_calls"] == 0
        assert stats["commands"] == {}
        assert not temp_storage.exists()

    def test_event_structure(self, temp_storage: Path) -> None:
        """Test that events have the correct structure."""
        tracker = DeprecationTracker(temp_storage)
        tracker.track_usage(
            command="gao-dev init",
            replacement="gao-dev start",
            removal_version="v3.0",
        )

        events = tracker.get_events()
        event = events[0]

        assert "timestamp" in event
        assert "command" in event
        assert "replacement" in event
        assert "removal_version" in event
        assert "context" in event
        assert "environment" in event

        env = event["environment"]
        assert "platform" in env
        assert "cwd" in env
        assert "headless" in env
        assert "ci" in env

    @patch.dict(os.environ, {"CI": "true"})
    def test_ci_detection_github_actions(self, temp_storage: Path) -> None:
        """Test CI environment detection."""
        DeprecationTracker.reset_singleton()
        tracker = DeprecationTracker(temp_storage)
        tracker.track_usage("gao-dev init", "gao-dev start")

        events = tracker.get_events()
        assert events[0]["environment"]["ci"] is True

        stats = tracker.get_usage_stats()
        assert stats["ci_percentage"] == 100.0

    @patch.dict(os.environ, {"GITHUB_ACTIONS": "true"})
    def test_ci_detection_various_environments(self, temp_storage: Path) -> None:
        """Test CI detection for various CI environments."""
        DeprecationTracker.reset_singleton()
        tracker = DeprecationTracker(temp_storage)
        tracker.track_usage("gao-dev init", "gao-dev start")

        events = tracker.get_events()
        assert events[0]["environment"]["ci"] is True

    def test_no_ci_environment(self, temp_storage: Path) -> None:
        """Test that non-CI environment is detected correctly."""
        # Clear all CI env vars
        env_vars_to_clear = [
            "CI", "CONTINUOUS_INTEGRATION", "GITHUB_ACTIONS",
            "GITLAB_CI", "JENKINS_URL", "CIRCLECI", "TRAVIS",
            "BUILDKITE", "AZURE_PIPELINES", "TF_BUILD"
        ]

        clean_env = {k: v for k, v in os.environ.items() if k not in env_vars_to_clear}

        with patch.dict(os.environ, clean_env, clear=True):
            DeprecationTracker.reset_singleton()
            tracker = DeprecationTracker(temp_storage)
            tracker.track_usage("gao-dev init", "gao-dev start")

            events = tracker.get_events()
            assert events[0]["environment"]["ci"] is False

    def test_thread_safety(self, temp_storage: Path) -> None:
        """Test thread safety of tracker."""
        import threading

        tracker = DeprecationTracker(temp_storage)
        threads = []

        def track_command(n: int) -> None:
            for _ in range(10):
                tracker.track_usage(f"command-{n}", "replacement")

        # Start multiple threads
        for i in range(5):
            t = threading.Thread(target=track_command, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        stats = tracker.get_usage_stats()
        assert stats["total_calls"] == 50  # 5 threads * 10 calls

    def test_corrupted_storage_handling(self, temp_storage: Path) -> None:
        """Test handling of corrupted storage file."""
        # Create corrupted JSON file
        temp_storage.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_storage, "w") as f:
            f.write("not valid json {{{")

        tracker = DeprecationTracker(temp_storage)

        # Should handle gracefully
        stats = tracker.get_usage_stats()
        assert stats["total_calls"] == 0

        # Should still be able to track new events
        tracker.track_usage("gao-dev init", "gao-dev start")
        stats = tracker.get_usage_stats()
        assert stats["total_calls"] == 1


class TestGetTracker:
    """Tests for get_tracker function."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self) -> None:
        """Reset singleton before each test."""
        DeprecationTracker.reset_singleton()
        yield
        DeprecationTracker.reset_singleton()

    def test_get_tracker_returns_singleton(self) -> None:
        """Test that get_tracker returns the singleton instance."""
        tracker1 = get_tracker()
        tracker2 = get_tracker()

        assert tracker1 is tracker2

    def test_get_tracker_with_custom_path(self, tmp_path: Path) -> None:
        """Test get_tracker with custom storage path."""
        custom_path = tmp_path / "custom.json"
        tracker = get_tracker(custom_path)

        tracker.track_usage("test", "replacement")

        assert custom_path.exists()


class TestTrackDeprecatedCommand:
    """Tests for track_deprecated_command convenience function."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self, tmp_path: Path) -> None:
        """Reset singleton and set temp storage."""
        DeprecationTracker.reset_singleton()
        # Create tracker with temp storage
        self.temp_storage = tmp_path / "deprecation.json"
        yield
        DeprecationTracker.reset_singleton()

    def test_track_deprecated_command_basic(self, tmp_path: Path) -> None:
        """Test basic usage of convenience function."""
        storage_path = tmp_path / "deprecation.json"
        tracker = DeprecationTracker(storage_path)

        track_deprecated_command(
            "gao-dev init",
            "gao-dev start",
            "v3.0",
        )

        stats = tracker.get_usage_stats()
        assert stats["total_calls"] == 1
        assert stats["commands"]["gao-dev init"] == 1

    def test_track_deprecated_command_with_context(self, tmp_path: Path) -> None:
        """Test convenience function with context."""
        storage_path = tmp_path / "deprecation.json"
        tracker = DeprecationTracker(storage_path)

        track_deprecated_command(
            "gao-dev init",
            "gao-dev start",
            "v3.0",
            context={"source": "cli"},
        )

        events = tracker.get_events()
        assert events[0]["context"]["source"] == "cli"

    def test_track_deprecated_command_default_version(self, tmp_path: Path) -> None:
        """Test that default removal version is v3.0."""
        storage_path = tmp_path / "deprecation.json"
        tracker = DeprecationTracker(storage_path)

        track_deprecated_command("gao-dev init", "gao-dev start")

        events = tracker.get_events()
        assert events[0]["removal_version"] == "v3.0"


class TestDeprecationTrackerIntegration:
    """Integration tests for deprecation tracking."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self) -> None:
        """Reset singleton before each test."""
        DeprecationTracker.reset_singleton()
        yield
        DeprecationTracker.reset_singleton()

    def test_full_workflow(self, tmp_path: Path) -> None:
        """Test full tracking workflow."""
        storage_path = tmp_path / "deprecation.json"

        # Create tracker and track several commands
        tracker = DeprecationTracker(storage_path)

        # Simulate multiple users over time
        tracker.track_usage("gao-dev init", "gao-dev start", "v3.0")
        tracker.track_usage("gao-dev web start", "gao-dev start", "v3.0")
        tracker.track_usage("gao-dev init", "gao-dev start", "v3.0")

        # Get statistics
        stats = tracker.get_usage_stats()
        assert stats["total_calls"] == 3
        assert stats["commands"]["gao-dev init"] == 2
        assert stats["commands"]["gao-dev web start"] == 1

        # Reset and reload from storage
        DeprecationTracker.reset_singleton()
        tracker2 = DeprecationTracker(storage_path)

        # Verify persistence
        stats2 = tracker2.get_usage_stats()
        assert stats2["total_calls"] == 3

        # Add more events
        tracker2.track_usage("gao-dev init", "gao-dev start", "v3.0")

        stats3 = tracker2.get_usage_stats()
        assert stats3["total_calls"] == 4

    def test_analyze_migration_progress(self, tmp_path: Path) -> None:
        """Test analyzing migration progress from events."""
        storage_path = tmp_path / "deprecation.json"
        tracker = DeprecationTracker(storage_path)

        # Simulate usage over time
        for _ in range(10):
            tracker.track_usage("gao-dev init", "gao-dev start", "v3.0")

        for _ in range(3):
            tracker.track_usage("gao-dev web start", "gao-dev start", "v3.0")

        # Analyze
        stats = tracker.get_usage_stats()

        # Calculate percentages
        total = stats["total_calls"]
        init_pct = (stats["commands"]["gao-dev init"] / total) * 100
        web_pct = (stats["commands"]["gao-dev web start"] / total) * 100

        assert total == 13
        assert init_pct == pytest.approx(76.9, rel=0.1)
        assert web_pct == pytest.approx(23.1, rel=0.1)

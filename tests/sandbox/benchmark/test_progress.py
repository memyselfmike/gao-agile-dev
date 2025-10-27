"""Tests for progress tracking."""

import pytest
import threading
import time
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock

from gao_dev.sandbox.benchmark.progress import (
    ProgressTracker,
    ProgressEvent,
    ProgressEventType,
    ConsoleProgressObserver,
    LogProgressObserver,
    FileProgressObserver,
)


class TestProgressEventType:
    """Tests for ProgressEventType enum."""

    def test_event_type_values(self):
        """Test event type enum values."""
        assert ProgressEventType.BENCHMARK_STARTED.value == "benchmark_started"
        assert ProgressEventType.PHASE_STARTED.value == "phase_started"
        assert ProgressEventType.PHASE_PROGRESS.value == "phase_progress"
        assert ProgressEventType.PHASE_COMPLETED.value == "phase_completed"
        assert ProgressEventType.BENCHMARK_COMPLETED.value == "benchmark_completed"


class TestProgressEvent:
    """Tests for ProgressEvent."""

    def test_creation(self):
        """Test creating progress event."""
        event = ProgressEvent(
            event_type=ProgressEventType.PHASE_STARTED,
            timestamp=datetime.now(),
            message="Phase started",
            context={"phase_name": "test"},
        )
        assert event.event_type == ProgressEventType.PHASE_STARTED
        assert event.message == "Phase started"
        assert event.context["phase_name"] == "test"

    def test_to_dict(self):
        """Test converting event to dictionary."""
        now = datetime.now()
        event = ProgressEvent(
            event_type=ProgressEventType.BENCHMARK_STARTED,
            timestamp=now,
            message="Benchmark started",
            context={"benchmark_name": "test", "total_phases": 5},
        )

        data = event.to_dict()
        assert isinstance(data, dict)
        assert data["type"] == "benchmark_started"
        assert data["message"] == "Benchmark started"
        assert data["context"]["benchmark_name"] == "test"
        assert data["context"]["total_phases"] == 5
        assert "timestamp" in data


class TestProgressTracker:
    """Tests for ProgressTracker."""

    def test_tracker_creation(self):
        """Test creating ProgressTracker."""
        tracker = ProgressTracker()
        assert tracker is not None
        assert len(tracker.observers) == 0
        assert tracker.current_phase is None
        assert tracker.total_phases == 0
        assert tracker.completed_phases == 0

    def test_add_observer(self):
        """Test adding observers."""
        tracker = ProgressTracker()
        observer = Mock()

        tracker.add_observer(observer)
        assert len(tracker.observers) == 1
        assert observer in tracker.observers

    def test_remove_observer(self):
        """Test removing observers."""
        tracker = ProgressTracker()
        observer = Mock()

        tracker.add_observer(observer)
        assert len(tracker.observers) == 1

        tracker.remove_observer(observer)
        assert len(tracker.observers) == 0
        assert observer not in tracker.observers

    def test_remove_nonexistent_observer(self):
        """Test removing observer that doesn't exist."""
        tracker = ProgressTracker()
        observer = Mock()

        # Should not raise error
        tracker.remove_observer(observer)
        assert len(tracker.observers) == 0

    def test_benchmark_started_event(self):
        """Test benchmark started event."""
        tracker = ProgressTracker()
        observer = Mock()
        tracker.add_observer(observer)

        tracker.benchmark_started("test-benchmark", 5)

        assert tracker.total_phases == 5
        assert tracker.completed_phases == 0
        assert tracker.start_time is not None

        observer.on_progress.assert_called_once()
        call_args = observer.on_progress.call_args[0][0]
        assert call_args.event_type == ProgressEventType.BENCHMARK_STARTED
        assert "test-benchmark" in call_args.message
        assert call_args.context["total_phases"] == 5

    def test_phase_started_event(self):
        """Test phase started event."""
        tracker = ProgressTracker()
        observer = Mock()
        tracker.add_observer(observer)

        tracker.phase_started("planning")

        assert tracker.current_phase == "planning"

        observer.on_progress.assert_called_once()
        call_args = observer.on_progress.call_args[0][0]
        assert call_args.event_type == ProgressEventType.PHASE_STARTED
        assert call_args.context["phase_name"] == "planning"

    def test_phase_progress_event(self):
        """Test phase progress event."""
        tracker = ProgressTracker()
        observer = Mock()
        tracker.add_observer(observer)

        tracker.current_phase = "planning"
        tracker.phase_progress(50.0)

        observer.on_progress.assert_called_once()
        call_args = observer.on_progress.call_args[0][0]
        assert call_args.event_type == ProgressEventType.PHASE_PROGRESS
        assert call_args.context["percentage"] == 50.0
        assert call_args.context["phase_name"] == "planning"

    def test_phase_completed_event(self):
        """Test phase completed event."""
        tracker = ProgressTracker()
        tracker.total_phases = 5
        observer = Mock()
        tracker.add_observer(observer)

        tracker.phase_completed("planning", success=True)

        assert tracker.completed_phases == 1

        observer.on_progress.assert_called_once()
        call_args = observer.on_progress.call_args[0][0]
        assert call_args.event_type == ProgressEventType.PHASE_COMPLETED
        assert call_args.context["success"] is True
        assert call_args.context["completed_phases"] == 1

    def test_benchmark_completed_event(self):
        """Test benchmark completed event."""
        tracker = ProgressTracker()
        tracker.start_time = datetime.now()
        tracker.total_phases = 5
        tracker.completed_phases = 5
        observer = Mock()
        tracker.add_observer(observer)

        tracker.benchmark_completed(success=True)

        observer.on_progress.assert_called_once()
        call_args = observer.on_progress.call_args[0][0]
        assert call_args.event_type == ProgressEventType.BENCHMARK_COMPLETED
        assert call_args.context["success"] is True
        assert "duration_seconds" in call_args.context

    def test_multiple_observers(self):
        """Test notifying multiple observers."""
        tracker = ProgressTracker()
        observer1 = Mock()
        observer2 = Mock()

        tracker.add_observer(observer1)
        tracker.add_observer(observer2)

        tracker.phase_started("test")

        observer1.on_progress.assert_called_once()
        observer2.on_progress.assert_called_once()

    def test_observer_error_handling(self):
        """Test that observer errors don't break notification."""
        tracker = ProgressTracker()
        failing_observer = Mock()
        failing_observer.on_progress.side_effect = Exception("Observer error")
        working_observer = Mock()

        tracker.add_observer(failing_observer)
        tracker.add_observer(working_observer)

        # Should not raise error
        tracker.phase_started("test")

        # Working observer should still be called
        working_observer.on_progress.assert_called_once()

    def test_get_progress_percentage(self):
        """Test getting progress percentage."""
        tracker = ProgressTracker()
        tracker.total_phases = 10

        tracker.completed_phases = 0
        assert tracker.get_progress_percentage() == 0.0

        tracker.completed_phases = 5
        assert tracker.get_progress_percentage() == 50.0

        tracker.completed_phases = 10
        assert tracker.get_progress_percentage() == 100.0

    def test_get_progress_percentage_no_phases(self):
        """Test progress percentage when no phases."""
        tracker = ProgressTracker()
        tracker.total_phases = 0
        assert tracker.get_progress_percentage() == 0.0

    def test_estimate_remaining_time(self):
        """Test estimating remaining time."""
        tracker = ProgressTracker()
        tracker.total_phases = 10

        # No estimate without start time
        assert tracker.estimate_remaining_time() is None

        # No estimate without completed phases
        tracker.start_time = datetime.now()
        assert tracker.estimate_remaining_time() is None

        # With completed phases
        tracker.completed_phases = 5
        time.sleep(0.1)  # Small delay
        remaining = tracker.estimate_remaining_time()
        assert remaining is not None
        assert remaining > 0

    def test_thread_safety(self):
        """Test thread-safe updates."""
        tracker = ProgressTracker()
        observer = Mock()
        tracker.add_observer(observer)

        def update_progress():
            for i in range(10):
                tracker.phase_started(f"phase-{i}")
                tracker.phase_completed(f"phase-{i}", True)

        # Run multiple threads
        threads = [threading.Thread(target=update_progress) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Should have called observer many times without error
        assert observer.on_progress.call_count == 60  # 3 threads * 10 phases * 2 events


class TestConsoleProgressObserver:
    """Tests for ConsoleProgressObserver."""

    def test_observer_creation(self):
        """Test creating console observer."""
        observer = ConsoleProgressObserver()
        assert observer is not None
        assert observer.current_phase is None
        assert observer.total_phases == 0

    def test_benchmark_started(self, capsys):
        """Test benchmark started display."""
        observer = ConsoleProgressObserver()
        event = ProgressEvent(
            event_type=ProgressEventType.BENCHMARK_STARTED,
            timestamp=datetime.now(),
            message="Starting test",
            context={"total_phases": 5},
        )

        observer.on_progress(event)

        captured = capsys.readouterr()
        assert "BENCHMARK" in captured.out
        assert "Starting test" in captured.out

    def test_phase_events(self, capsys):
        """Test phase event display."""
        observer = ConsoleProgressObserver()

        # Phase started
        event = ProgressEvent(
            event_type=ProgressEventType.PHASE_STARTED,
            timestamp=datetime.now(),
            message="Phase: planning",
            context={"phase_name": "planning"},
        )
        observer.on_progress(event)

        captured = capsys.readouterr()
        assert "PHASE" in captured.out
        assert "planning" in captured.out


class TestLogProgressObserver:
    """Tests for LogProgressObserver."""

    def test_observer_creation(self):
        """Test creating log observer."""
        observer = LogProgressObserver()
        assert observer is not None

    def test_logs_events(self):
        """Test that events are logged."""
        observer = LogProgressObserver()
        event = ProgressEvent(
            event_type=ProgressEventType.PHASE_STARTED,
            timestamp=datetime.now(),
            message="Test phase",
            context={"phase_name": "test"},
        )

        # Should not raise error
        observer.on_progress(event)


class TestFileProgressObserver:
    """Tests for FileProgressObserver."""

    def test_observer_creation(self, tmp_path):
        """Test creating file observer."""
        file_path = tmp_path / "progress.json"
        observer = FileProgressObserver(file_path)
        assert observer is not None
        assert observer.file_path == file_path

    def test_saves_events(self, tmp_path):
        """Test that events are saved to file."""
        file_path = tmp_path / "progress.json"
        observer = FileProgressObserver(file_path)

        event = ProgressEvent(
            event_type=ProgressEventType.BENCHMARK_STARTED,
            timestamp=datetime.now(),
            message="Test benchmark",
            context={"benchmark_name": "test"},
        )

        observer.on_progress(event)

        assert file_path.exists()
        import json

        with open(file_path) as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]["type"] == "benchmark_started"
        assert data[0]["message"] == "Test benchmark"

    def test_appends_events(self, tmp_path):
        """Test that multiple events are appended."""
        file_path = tmp_path / "progress.json"
        observer = FileProgressObserver(file_path)

        for i in range(3):
            event = ProgressEvent(
                event_type=ProgressEventType.PHASE_STARTED,
                timestamp=datetime.now(),
                message=f"Phase {i}",
                context={"phase_name": f"phase-{i}"},
            )
            observer.on_progress(event)

        import json

        with open(file_path) as f:
            data = json.load(f)

        assert len(data) == 3

    def test_thread_safe_writes(self, tmp_path):
        """Test thread-safe file writes."""
        file_path = tmp_path / "progress.json"
        observer = FileProgressObserver(file_path)

        def write_events():
            for i in range(5):
                event = ProgressEvent(
                    event_type=ProgressEventType.PHASE_STARTED,
                    timestamp=datetime.now(),
                    message=f"Event {i}",
                    context={},
                )
                observer.on_progress(event)

        # Run multiple threads
        threads = [threading.Thread(target=write_events) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Should have all events
        import json

        with open(file_path) as f:
            data = json.load(f)

        assert len(data) == 15  # 3 threads * 5 events

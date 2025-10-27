# Story 4.5: Progress Tracking

**Epic**: Epic 4 - Benchmark Runner
**Status**: Ready
**Priority**: P1 (High)
**Estimated Effort**: 3 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27

---

## User Story

**As a** developer running benchmarks
**I want** real-time progress tracking and status updates
**So that** I can monitor long-running benchmarks and debug issues

---

## Acceptance Criteria

### AC1: ProgressTracker Class
- [ ] ProgressTracker class implemented
- [ ] Tracks overall benchmark progress
- [ ] Tracks phase-level progress
- [ ] Can estimate time remaining
- [ ] Thread-safe for concurrent updates

### AC2: Progress Events
- [ ] BenchmarkStarted event
- [ ] PhaseStarted event
- [ ] PhaseProgress event (percentage)
- [ ] PhaseCompleted event
- [ ] BenchmarkCompleted event
- [ ] All events include timestamp and context

### AC3: Progress Observers
- [ ] Observer pattern for progress notifications
- [ ] ConsoleProgressObserver (prints to stdout)
- [ ] LogProgressObserver (structured logging)
- [ ] FileProgressObserver (saves to JSON file)
- [ ] Can register multiple observers

### AC4: Console Display
- [ ] Progress bar for current phase
- [ ] Overall progress indicator
- [ ] Current phase name and status
- [ ] Estimated time remaining
- [ ] Updates in place (no scrolling spam)

### AC5: Progress Persistence
- [ ] Progress saved to `.progress.json` file
- [ ] Can resume viewing from saved progress
- [ ] Includes all phase timings
- [ ] Includes current status
- [ ] Updated in real-time

---

## Technical Details

### Implementation Approach

**New Module**: `gao_dev/sandbox/benchmark/progress.py`

```python
"""Progress tracking for benchmark runs."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional, Protocol
import json
import threading
import structlog
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.console import Console


logger = structlog.get_logger()


class ProgressEventType(Enum):
    """Types of progress events."""
    BENCHMARK_STARTED = "benchmark_started"
    PHASE_STARTED = "phase_started"
    PHASE_PROGRESS = "phase_progress"
    PHASE_COMPLETED = "phase_completed"
    BENCHMARK_COMPLETED = "benchmark_completed"


@dataclass
class ProgressEvent:
    """A progress event."""

    event_type: ProgressEventType
    timestamp: datetime
    message: str
    context: Dict[str, Any] = field(default_factory=dict)


class ProgressObserver(Protocol):
    """Protocol for progress observers."""

    def on_progress(self, event: ProgressEvent) -> None:
        """Handle progress event."""
        ...


class ConsoleProgressObserver:
    """Displays progress to console using rich."""

    def __init__(self):
        self.console = Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=self.console
        )
        self.task_id: Optional[int] = None
        self.started = False

    def on_progress(self, event: ProgressEvent) -> None:
        """Handle progress event."""
        if event.event_type == ProgressEventType.BENCHMARK_STARTED:
            if not self.started:
                self.progress.start()
                self.started = True
            total = event.context.get("total_phases", 100)
            self.task_id = self.progress.add_task(
                event.message,
                total=total
            )

        elif event.event_type == ProgressEventType.PHASE_STARTED:
            if self.task_id is not None:
                self.progress.update(self.task_id, description=event.message)

        elif event.event_type == ProgressEventType.PHASE_PROGRESS:
            if self.task_id is not None:
                completed = event.context.get("completed", 0)
                self.progress.update(self.task_id, completed=completed)

        elif event.event_type == ProgressEventType.PHASE_COMPLETED:
            if self.task_id is not None:
                self.progress.update(self.task_id, advance=1)

        elif event.event_type == ProgressEventType.BENCHMARK_COMPLETED:
            if self.started:
                self.progress.stop()
                self.console.print(f"[green]{event.message}[/green]")


class LogProgressObserver:
    """Logs progress events using structured logging."""

    def __init__(self):
        self.logger = logger.bind(component="ProgressObserver")

    def on_progress(self, event: ProgressEvent) -> None:
        """Handle progress event."""
        self.logger.info(
            "progress_event",
            event_type=event.event_type.value,
            message=event.message,
            **event.context
        )


class FileProgressObserver:
    """Saves progress to JSON file."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.events: List[Dict[str, Any]] = []
        self.lock = threading.Lock()

    def on_progress(self, event: ProgressEvent) -> None:
        """Handle progress event."""
        with self.lock:
            event_data = {
                "type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "message": event.message,
                "context": event.context
            }
            self.events.append(event_data)
            self._save()

    def _save(self) -> None:
        """Save events to file."""
        with open(self.file_path, 'w') as f:
            json.dump(self.events, f, indent=2)


class ProgressTracker:
    """
    Tracks and reports benchmark progress.

    Thread-safe progress tracking with observer pattern for
    notifying multiple listeners about progress events.
    """

    def __init__(self):
        self.observers: List[ProgressObserver] = []
        self.lock = threading.Lock()
        self.current_phase: Optional[str] = None
        self.total_phases: int = 0
        self.completed_phases: int = 0
        self.start_time: Optional[datetime] = None

    def add_observer(self, observer: ProgressObserver) -> None:
        """Add a progress observer."""
        with self.lock:
            self.observers.append(observer)

    def remove_observer(self, observer: ProgressObserver) -> None:
        """Remove a progress observer."""
        with self.lock:
            self.observers.remove(observer)

    def benchmark_started(self, benchmark_name: str, total_phases: int) -> None:
        """Report benchmark started."""
        self.start_time = datetime.now()
        self.total_phases = total_phases
        self.completed_phases = 0

        event = ProgressEvent(
            event_type=ProgressEventType.BENCHMARK_STARTED,
            timestamp=datetime.now(),
            message=f"Starting benchmark: {benchmark_name}",
            context={"benchmark_name": benchmark_name, "total_phases": total_phases}
        )
        self._notify_observers(event)

    def phase_started(self, phase_name: str) -> None:
        """Report phase started."""
        self.current_phase = phase_name

        event = ProgressEvent(
            event_type=ProgressEventType.PHASE_STARTED,
            timestamp=datetime.now(),
            message=f"Phase: {phase_name}",
            context={"phase_name": phase_name}
        )
        self._notify_observers(event)

    def phase_progress(self, percentage: float) -> None:
        """Report phase progress."""
        event = ProgressEvent(
            event_type=ProgressEventType.PHASE_PROGRESS,
            timestamp=datetime.now(),
            message=f"Progress: {percentage:.1f}%",
            context={
                "phase_name": self.current_phase,
                "percentage": percentage,
                "completed": self.completed_phases
            }
        )
        self._notify_observers(event)

    def phase_completed(self, phase_name: str, success: bool) -> None:
        """Report phase completed."""
        self.completed_phases += 1

        event = ProgressEvent(
            event_type=ProgressEventType.PHASE_COMPLETED,
            timestamp=datetime.now(),
            message=f"Completed: {phase_name} ({'success' if success else 'failed'})",
            context={
                "phase_name": phase_name,
                "success": success,
                "completed_phases": self.completed_phases,
                "total_phases": self.total_phases
            }
        )
        self._notify_observers(event)

    def benchmark_completed(self, success: bool) -> None:
        """Report benchmark completed."""
        duration = None
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()

        event = ProgressEvent(
            event_type=ProgressEventType.BENCHMARK_COMPLETED,
            timestamp=datetime.now(),
            message=f"Benchmark completed ({'success' if success else 'failed'})",
            context={
                "success": success,
                "duration_seconds": duration,
                "completed_phases": self.completed_phases,
                "total_phases": self.total_phases
            }
        )
        self._notify_observers(event)

    def _notify_observers(self, event: ProgressEvent) -> None:
        """Notify all observers of an event."""
        with self.lock:
            for observer in self.observers:
                try:
                    observer.on_progress(event)
                except Exception as e:
                    logger.error("observer_error", observer=type(observer).__name__, error=str(e))
```

---

## Dependencies

- Story 4.3 (Benchmark Runner Core)

---

## Definition of Done

- [ ] ProgressTracker class implemented
- [ ] ProgressEvent model implemented
- [ ] ProgressEventType enum defined
- [ ] ConsoleProgressObserver implemented (using rich)
- [ ] LogProgressObserver implemented
- [ ] FileProgressObserver implemented
- [ ] Observer pattern working
- [ ] Thread-safe updates
- [ ] Console displays progress bars
- [ ] Progress saved to file
- [ ] Type hints for all methods
- [ ] Unit tests written (>80% coverage)
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Documentation updated

---

## Test Strategy

### Unit Tests

**Test File**: `tests/sandbox/benchmark/test_progress.py`

```python
def test_progress_tracker_creation():
    """Test creating ProgressTracker."""

def test_add_remove_observers():
    """Test adding and removing observers."""

def test_benchmark_started_event():
    """Test benchmark started event."""

def test_phase_events():
    """Test phase started/progress/completed events."""

def test_benchmark_completed_event():
    """Test benchmark completed event."""

def test_console_observer():
    """Test ConsoleProgressObserver."""

def test_log_observer():
    """Test LogProgressObserver."""

def test_file_observer():
    """Test FileProgressObserver saves to file."""

def test_thread_safety():
    """Test thread-safe updates."""
```

---

## Notes

- Use `rich` library for beautiful console progress bars
- Keep observers simple and focused
- Progress file useful for debugging failed runs
- Consider adding webhook observer in future for remote monitoring

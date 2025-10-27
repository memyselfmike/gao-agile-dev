"""Progress tracking for benchmark runs."""

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional, Protocol
import structlog


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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
            "context": self.context,
        }


class ProgressObserver(Protocol):
    """Protocol for progress observers."""

    def on_progress(self, event: ProgressEvent) -> None:
        """Handle progress event."""
        ...


class ConsoleProgressObserver:
    """Displays progress to console with simple text output."""

    def __init__(self):
        self.current_phase: Optional[str] = None
        self.total_phases: int = 0
        self.completed_phases: int = 0

    def on_progress(self, event: ProgressEvent) -> None:
        """Handle progress event."""
        if event.event_type == ProgressEventType.BENCHMARK_STARTED:
            self.total_phases = event.context.get("total_phases", 0)
            self.completed_phases = 0
            print(f"\n[BENCHMARK] {event.message}")
            print(f"[BENCHMARK] Total phases: {self.total_phases}")

        elif event.event_type == ProgressEventType.PHASE_STARTED:
            self.current_phase = event.context.get("phase_name")
            print(f"\n[PHASE] {event.message}")

        elif event.event_type == ProgressEventType.PHASE_PROGRESS:
            percentage = event.context.get("percentage", 0)
            print(f"[PROGRESS] {self.current_phase}: {percentage:.1f}%", end="\r")

        elif event.event_type == ProgressEventType.PHASE_COMPLETED:
            self.completed_phases += 1
            success = event.context.get("success", True)
            status = "SUCCESS" if success else "FAILED"
            print(
                f"\n[PHASE] {event.message} - {status} "
                f"({self.completed_phases}/{self.total_phases})"
            )

        elif event.event_type == ProgressEventType.BENCHMARK_COMPLETED:
            success = event.context.get("success", True)
            duration = event.context.get("duration_seconds", 0)
            status = "SUCCESS" if success else "FAILED"
            print(f"\n[BENCHMARK] {event.message} - {status}")
            print(f"[BENCHMARK] Duration: {duration:.2f}s")
            print(f"[BENCHMARK] Completed: {self.completed_phases}/{self.total_phases}")


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
            **event.context,
        )


class FileProgressObserver:
    """Saves progress to JSON file."""

    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        self.events: List[Dict[str, Any]] = []
        self.lock = threading.Lock()

    def on_progress(self, event: ProgressEvent) -> None:
        """Handle progress event."""
        with self.lock:
            self.events.append(event.to_dict())
            self._save()

    def _save(self) -> None:
        """Save events to file."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, "w") as f:
                json.dump(self.events, f, indent=2)
        except Exception as e:
            logger.error("progress_file_save_error", error=str(e))


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
            if observer in self.observers:
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
            context={"benchmark_name": benchmark_name, "total_phases": total_phases},
        )
        self._notify_observers(event)

    def phase_started(self, phase_name: str) -> None:
        """Report phase started."""
        self.current_phase = phase_name

        event = ProgressEvent(
            event_type=ProgressEventType.PHASE_STARTED,
            timestamp=datetime.now(),
            message=f"Phase: {phase_name}",
            context={"phase_name": phase_name},
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
                "completed": self.completed_phases,
            },
        )
        self._notify_observers(event)

    def phase_completed(self, phase_name: str, success: bool) -> None:
        """Report phase completed."""
        self.completed_phases += 1

        event = ProgressEvent(
            event_type=ProgressEventType.PHASE_COMPLETED,
            timestamp=datetime.now(),
            message=f"Completed: {phase_name}",
            context={
                "phase_name": phase_name,
                "success": success,
                "completed_phases": self.completed_phases,
                "total_phases": self.total_phases,
            },
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
            message="Benchmark completed",
            context={
                "success": success,
                "duration_seconds": duration,
                "completed_phases": self.completed_phases,
                "total_phases": self.total_phases,
            },
        )
        self._notify_observers(event)

    def get_progress_percentage(self) -> float:
        """
        Get overall progress percentage.

        Returns:
            Progress percentage (0-100)
        """
        if self.total_phases == 0:
            return 0.0
        return (self.completed_phases / self.total_phases) * 100

    def estimate_remaining_time(self) -> Optional[float]:
        """
        Estimate remaining time in seconds.

        Returns:
            Estimated seconds remaining, or None if cannot estimate
        """
        if not self.start_time or self.completed_phases == 0:
            return None

        elapsed = (datetime.now() - self.start_time).total_seconds()
        avg_time_per_phase = elapsed / self.completed_phases
        remaining_phases = self.total_phases - self.completed_phases

        return avg_time_per_phase * remaining_phases

    def _notify_observers(self, event: ProgressEvent) -> None:
        """Notify all observers of an event."""
        with self.lock:
            for observer in self.observers[:]:  # Copy list to avoid modification during iteration
                try:
                    observer.on_progress(event)
                except Exception as e:
                    logger.error(
                        "observer_error", observer=type(observer).__name__, error=str(e)
                    )

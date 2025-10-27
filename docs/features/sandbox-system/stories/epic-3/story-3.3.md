# Story 3.3: Metrics Collector Implementation

**Epic**: Epic 3 - Metrics Collection System
**Status**: Ready
**Priority**: P0 (Critical)
**Estimated Effort**: 3 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27

---

## User Story

**As a** developer integrating metrics collection
**I want** a central MetricsCollector class
**So that** I can easily track metrics during benchmark runs

---

## Acceptance Criteria

### AC1: MetricsCollector Class
- [ ] MetricsCollector class implemented
- [ ] Singleton pattern for single instance per run
- [ ] Methods for starting/stopping collection
- [ ] Methods for recording events
- [ ] Thread-safe operations

### AC2: Event Recording
- [ ] record_event() method for tracking events
- [ ] start_timer() / stop_timer() for timing operations
- [ ] increment_counter() for counting operations
- [ ] set_value() for setting metric values
- [ ] add_metadata() for additional context

### AC3: Metrics Aggregation
- [ ] get_current_metrics() returns BenchmarkMetrics
- [ ] Automatic calculation of derived metrics
- [ ] Metrics validation before returning
- [ ] Clear/reset functionality

### AC4: Integration Points
- [ ] Easy integration with SandboxManager
- [ ] Minimal performance overhead (<5%)
- [ ] Context manager support
- [ ] Error handling doesn't break main flow

---

## Technical Details

### Implementation Approach

**New Module**: `gao_dev/sandbox/metrics/collector.py`

```python
"""Central metrics collection system."""

import time
import threading
from datetime import datetime
from typing import Optional, Any, Dict
from uuid import uuid4

from .models import BenchmarkMetrics, PerformanceMetrics, AutonomyMetrics, QualityMetrics, WorkflowMetrics


class MetricsCollector:
    """
    Central collector for benchmark metrics.
    Singleton pattern ensures one instance per run.
    """

    _instance: Optional["MetricsCollector"] = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize metrics collector."""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self.reset()

    def reset(self) -> None:
        """Reset all metrics for new run."""
        self.run_id = str(uuid4())
        self.start_time = datetime.utcnow()
        self.timers: Dict[str, float] = {}
        self.counters: Dict[str, int] = {}
        self.values: Dict[str, Any] = {}
        self.events: list = []
        self._is_collecting = False

    def start_collection(self, project_name: str, benchmark_name: str) -> None:
        """Start metrics collection for a benchmark run."""
        self.reset()
        self.project_name = project_name
        self.benchmark_name = benchmark_name
        self._is_collecting = True
        self.collection_start_time = time.time()

    def stop_collection(self) -> BenchmarkMetrics:
        """Stop collection and return final metrics."""
        self._is_collecting = False
        return self.get_current_metrics()

    def start_timer(self, name: str) -> None:
        """Start a named timer."""
        self.timers[f"{name}_start"] = time.time()

    def stop_timer(self, name: str) -> float:
        """Stop a named timer and return elapsed time."""
        start_key = f"{name}_start"
        if start_key not in self.timers:
            return 0.0
        elapsed = time.time() - self.timers[start_key]
        self.values[f"{name}_time"] = elapsed
        return elapsed

    def increment_counter(self, name: str, amount: int = 1) -> None:
        """Increment a named counter."""
        self.counters[name] = self.counters.get(name, 0) + amount

    def set_value(self, name: str, value: Any) -> None:
        """Set a named value."""
        self.values[name] = value

    def record_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Record an event with timestamp."""
        self.events.append({
            "timestamp": datetime.utcnow().isoformat(),
            "type": event_type,
            "data": data
        })

    def get_current_metrics(self) -> BenchmarkMetrics:
        """Get current metrics snapshot."""
        total_time = time.time() - self.collection_start_time if hasattr(self, "collection_start_time") else 0.0

        metrics = BenchmarkMetrics(
            run_id=self.run_id,
            timestamp=self.start_time.isoformat(),
            project_name=getattr(self, "project_name", "unknown"),
            benchmark_name=getattr(self, "benchmark_name", "unknown"),
            performance=PerformanceMetrics(
                total_time_seconds=total_time
            ),
            autonomy=AutonomyMetrics(),
            quality=QualityMetrics(),
            workflow=WorkflowMetrics(),
            metadata={
                "events_count": len(self.events),
                "timers": list(self.timers.keys()),
                "counters": dict(self.counters),
            }
        )

        return metrics

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._is_collecting:
            self.stop_collection()
        return False
```

### Usage Example

```python
# In SandboxManager or BenchmarkRunner
collector = MetricsCollector()
collector.start_collection("todo-app", "basic-benchmark")

# During execution
collector.start_timer("phase_planning")
# ... do work ...
collector.stop_timer("phase_planning")

collector.increment_counter("stories_created")
collector.set_value("token_usage", 15000)

# At the end
final_metrics = collector.stop_collection()
```

---

## Testing Requirements

### Unit Tests

**File**: `tests/sandbox/metrics/test_collector.py`

```python
def test_singleton_pattern():
    """Test MetricsCollector is singleton."""
    pass


def test_start_stop_collection():
    """Test collection lifecycle."""
    pass


def test_timer_operations():
    """Test start/stop timer."""
    pass


def test_counter_operations():
    """Test increment counter."""
    pass


def test_value_operations():
    """Test set value."""
    pass


def test_event_recording():
    """Test record event."""
    pass


def test_get_current_metrics():
    """Test metrics snapshot."""
    pass


def test_reset():
    """Test reset clears all data."""
    pass


def test_context_manager():
    """Test using as context manager."""
    pass


def test_thread_safety():
    """Test concurrent access."""
    pass
```

---

## Definition of Done

- [ ] MetricsCollector class implemented
- [ ] Singleton pattern working
- [ ] All collection methods implemented
- [ ] Thread-safe operations
- [ ] Unit tests passing (>90% coverage)
- [ ] Performance overhead <5%
- [ ] No type errors (MyPy strict)
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] Committed with proper message

---

## Dependencies

- **Requires**: Story 3.1 (data models exist)
- **Blocks**: Story 3.4, 3.5, 3.6, 3.7

---

## Notes

- Keep overhead minimal
- Thread-safe for concurrent operations
- Easy to use API
- Consider async operations if needed

---

*Created as part of Epic 3: Metrics Collection System*

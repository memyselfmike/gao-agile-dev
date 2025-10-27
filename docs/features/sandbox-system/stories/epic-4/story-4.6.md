# Story 4.6: Timeout Management

**Epic**: Epic 4 - Benchmark Runner
**Status**: Ready
**Priority**: P1 (High)
**Estimated Effort**: 3 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27

---

## User Story

**As a** benchmark runner
**I want** comprehensive timeout management
**So that** benchmarks don't run indefinitely and resources are properly managed

---

## Acceptance Criteria

### AC1: TimeoutManager Class
- [ ] TimeoutManager class implemented
- [ ] Supports multiple concurrent timers
- [ ] Thread-safe timeout tracking
- [ ] Can cancel timers
- [ ] Provides time remaining queries

### AC2: Hierarchical Timeouts
- [ ] Overall benchmark timeout
- [ ] Per-phase timeouts
- [ ] Per-command timeouts
- [ ] Child timeout inherits from parent
- [ ] Timeout violation triggers cleanup

### AC3: Timeout Actions
- [ ] On timeout: cancel current operation
- [ ] On timeout: log timeout event
- [ ] On timeout: update status to TIMEOUT
- [ ] On timeout: save partial results
- [ ] On timeout: run cleanup handlers

### AC4: Graceful Shutdown
- [ ] Give processes time to cleanup (grace period)
- [ ] Force kill after grace period
- [ ] Save all collected data before shutdown
- [ ] Mark as TIMEOUT not FAILED
- [ ] Include timeout info in results

### AC5: Timeout Configuration
- [ ] Default timeouts defined
- [ ] Per-benchmark timeout overrides
- [ ] Per-phase timeout overrides
- [ ] Grace period configurable
- [ ] Can disable timeouts for debugging

---

## Technical Details

### Implementation Approach

**New Module**: `gao_dev/sandbox/benchmark/timeout.py`

```python
"""Timeout management for benchmark runs."""

import asyncio
import signal
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional, Callable, Any
import structlog


logger = structlog.get_logger()


class TimeoutStatus(Enum):
    """Status of a timeout."""
    ACTIVE = "active"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class TimeoutInfo:
    """Information about a timeout."""

    name: str
    timeout_seconds: int
    start_time: datetime
    end_time: Optional[datetime] = None
    status: TimeoutStatus = TimeoutStatus.ACTIVE
    grace_period_seconds: int = 30

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds."""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

    @property
    def remaining_seconds(self) -> float:
        """Get remaining time in seconds."""
        return max(0, self.timeout_seconds - self.elapsed_seconds)

    @property
    def is_timeout(self) -> bool:
        """Check if timeout has been reached."""
        return self.elapsed_seconds >= self.timeout_seconds


class TimeoutManager:
    """
    Manages timeouts for benchmark operations.

    Supports hierarchical timeouts with parent/child relationships
    and graceful shutdown with configurable grace periods.
    """

    def __init__(self):
        self.timeouts: Dict[str, TimeoutInfo] = {}
        self.lock = threading.Lock()
        self.logger = logger.bind(component="TimeoutManager")
        self.shutdown_handlers: Dict[str, Callable] = {}

    def start_timeout(
        self,
        name: str,
        timeout_seconds: int,
        grace_period_seconds: int = 30,
        on_timeout: Optional[Callable] = None
    ) -> TimeoutInfo:
        """
        Start a new timeout.

        Args:
            name: Unique name for this timeout
            timeout_seconds: Timeout duration in seconds
            grace_period_seconds: Grace period for cleanup
            on_timeout: Optional callback when timeout occurs

        Returns:
            TimeoutInfo object

        Raises:
            ValueError: If timeout with this name already exists
        """
        with self.lock:
            if name in self.timeouts:
                raise ValueError(f"Timeout '{name}' already exists")

            timeout_info = TimeoutInfo(
                name=name,
                timeout_seconds=timeout_seconds,
                start_time=datetime.now(),
                grace_period_seconds=grace_period_seconds
            )

            self.timeouts[name] = timeout_info

            if on_timeout:
                self.shutdown_handlers[name] = on_timeout

            self.logger.info(
                "timeout_started",
                name=name,
                timeout_seconds=timeout_seconds
            )

            # Start monitoring in background thread
            threading.Thread(
                target=self._monitor_timeout,
                args=(name,),
                daemon=True
            ).start()

            return timeout_info

    def complete_timeout(self, name: str) -> None:
        """
        Mark a timeout as completed successfully.

        Args:
            name: Name of the timeout
        """
        with self.lock:
            if name in self.timeouts:
                timeout_info = self.timeouts[name]
                timeout_info.status = TimeoutStatus.COMPLETED
                timeout_info.end_time = datetime.now()

                self.logger.info(
                    "timeout_completed",
                    name=name,
                    elapsed=timeout_info.elapsed_seconds
                )

    def cancel_timeout(self, name: str) -> None:
        """
        Cancel a timeout.

        Args:
            name: Name of the timeout
        """
        with self.lock:
            if name in self.timeouts:
                timeout_info = self.timeouts[name]
                timeout_info.status = TimeoutStatus.CANCELLED
                timeout_info.end_time = datetime.now()

                self.logger.info("timeout_cancelled", name=name)

    def get_remaining_time(self, name: str) -> float:
        """
        Get remaining time for a timeout.

        Args:
            name: Name of the timeout

        Returns:
            Remaining seconds (0 if timeout reached or doesn't exist)
        """
        with self.lock:
            if name in self.timeouts:
                return self.timeouts[name].remaining_seconds
            return 0.0

    def is_timeout(self, name: str) -> bool:
        """
        Check if timeout has been reached.

        Args:
            name: Name of the timeout

        Returns:
            True if timeout reached, False otherwise
        """
        with self.lock:
            if name in self.timeouts:
                return self.timeouts[name].is_timeout
            return False

    def _monitor_timeout(self, name: str) -> None:
        """
        Monitor a timeout in background thread.

        Args:
            name: Name of the timeout to monitor
        """
        while True:
            with self.lock:
                if name not in self.timeouts:
                    break

                timeout_info = self.timeouts[name]

                # If completed or cancelled, stop monitoring
                if timeout_info.status in (TimeoutStatus.COMPLETED, TimeoutStatus.CANCELLED):
                    break

                # Check if timeout reached
                if timeout_info.is_timeout:
                    timeout_info.status = TimeoutStatus.TIMEOUT
                    timeout_info.end_time = datetime.now()

                    self.logger.warning(
                        "timeout_reached",
                        name=name,
                        elapsed=timeout_info.elapsed_seconds
                    )

                    # Call timeout handler
                    if name in self.shutdown_handlers:
                        try:
                            handler = self.shutdown_handlers[name]
                            handler()
                        except Exception as e:
                            self.logger.error(
                                "timeout_handler_error",
                                name=name,
                                error=str(e)
                            )

                    break

            # Sleep briefly before next check
            threading.Event().wait(1.0)

    def graceful_shutdown(self, name: str, process: Any) -> bool:
        """
        Perform graceful shutdown of a process.

        Args:
            name: Name of the operation
            process: Process to shutdown

        Returns:
            True if gracefully shutdown, False if forced kill
        """
        timeout_info = self.timeouts.get(name)
        if not timeout_info:
            return False

        self.logger.info(
            "graceful_shutdown_started",
            name=name,
            grace_period=timeout_info.grace_period_seconds
        )

        try:
            # Try SIGTERM first
            if hasattr(process, 'terminate'):
                process.terminate()

                # Wait for grace period
                try:
                    process.wait(timeout=timeout_info.grace_period_seconds)
                    self.logger.info("graceful_shutdown_success", name=name)
                    return True
                except:
                    # Grace period expired, force kill
                    if hasattr(process, 'kill'):
                        process.kill()
                        self.logger.warning("forced_kill", name=name)
                        return False

        except Exception as e:
            self.logger.error("shutdown_error", name=name, error=str(e))
            return False

        return True


class TimeoutContext:
    """
    Context manager for timeout operations.

    Usage:
        with TimeoutContext(manager, "my_operation", 300):
            # Do work that might timeout
            pass
    """

    def __init__(
        self,
        manager: TimeoutManager,
        name: str,
        timeout_seconds: int,
        on_timeout: Optional[Callable] = None
    ):
        self.manager = manager
        self.name = name
        self.timeout_seconds = timeout_seconds
        self.on_timeout = on_timeout

    def __enter__(self):
        self.manager.start_timeout(
            self.name,
            self.timeout_seconds,
            on_timeout=self.on_timeout
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.manager.complete_timeout(self.name)
        else:
            self.manager.cancel_timeout(self.name)
        return False
```

---

## Dependencies

- Story 4.3 (Benchmark Runner Core)

---

## Definition of Done

- [ ] TimeoutManager class implemented
- [ ] TimeoutInfo model implemented
- [ ] TimeoutStatus enum defined
- [ ] TimeoutContext context manager implemented
- [ ] Hierarchical timeout support
- [ ] Graceful shutdown implemented
- [ ] Background monitoring working
- [ ] Thread-safe operations
- [ ] Type hints for all methods
- [ ] Unit tests written (>80% coverage)
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Documentation updated

---

## Test Strategy

### Unit Tests

**Test File**: `tests/sandbox/benchmark/test_timeout.py`

```python
def test_timeout_manager_creation():
    """Test creating TimeoutManager."""

def test_start_timeout():
    """Test starting a timeout."""

def test_complete_timeout():
    """Test completing a timeout successfully."""

def test_cancel_timeout():
    """Test cancelling a timeout."""

def test_timeout_reached():
    """Test timeout detection when time expires."""

def test_get_remaining_time():
    """Test getting remaining time."""

def test_timeout_handler_called():
    """Test that timeout handler is called on timeout."""

def test_graceful_shutdown():
    """Test graceful shutdown process."""

def test_timeout_context_manager():
    """Test TimeoutContext context manager."""

def test_concurrent_timeouts():
    """Test multiple concurrent timeouts."""
```

---

## Notes

- Use threading for timeout monitoring to avoid blocking
- Graceful shutdown important for clean test runs
- Consider using asyncio for better async support in future
- Timeout hierarchy helps manage complex benchmarks

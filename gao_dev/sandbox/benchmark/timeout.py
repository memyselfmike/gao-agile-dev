"""Timeout management for benchmark runs."""

import threading
from dataclasses import dataclass
from datetime import datetime
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
        self.monitor_threads: Dict[str, threading.Thread] = {}

    def start_timeout(
        self,
        name: str,
        timeout_seconds: int,
        grace_period_seconds: int = 30,
        on_timeout: Optional[Callable] = None,
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
                grace_period_seconds=grace_period_seconds,
            )

            self.timeouts[name] = timeout_info

            if on_timeout:
                self.shutdown_handlers[name] = on_timeout

            self.logger.info(
                "timeout_started", name=name, timeout_seconds=timeout_seconds
            )

            # Start monitoring in background thread
            monitor_thread = threading.Thread(
                target=self._monitor_timeout, args=(name,), daemon=True
            )
            monitor_thread.start()
            self.monitor_threads[name] = monitor_thread

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
                    elapsed=timeout_info.elapsed_seconds,
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

    def get_status(self, name: str) -> Optional[TimeoutStatus]:
        """
        Get status of a timeout.

        Args:
            name: Name of the timeout

        Returns:
            TimeoutStatus or None if not found
        """
        with self.lock:
            if name in self.timeouts:
                return self.timeouts[name].status
            return None

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
                if timeout_info.status in (
                    TimeoutStatus.COMPLETED,
                    TimeoutStatus.CANCELLED,
                ):
                    break

                # Check if timeout reached
                if timeout_info.is_timeout:
                    timeout_info.status = TimeoutStatus.TIMEOUT
                    timeout_info.end_time = datetime.now()

                    self.logger.warning(
                        "timeout_reached",
                        name=name,
                        elapsed=timeout_info.elapsed_seconds,
                    )

                    # Call timeout handler
                    if name in self.shutdown_handlers:
                        try:
                            handler = self.shutdown_handlers[name]
                            handler()
                        except Exception as e:
                            self.logger.error(
                                "timeout_handler_error", name=name, error=str(e)
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
            grace_period=timeout_info.grace_period_seconds,
        )

        try:
            # Try terminate first (SIGTERM)
            if hasattr(process, "terminate"):
                process.terminate()

                # Wait for grace period
                try:
                    if hasattr(process, "wait"):
                        process.wait(timeout=timeout_info.grace_period_seconds)
                        self.logger.info("graceful_shutdown_success", name=name)
                        return True
                except Exception:
                    # Grace period expired, force kill
                    if hasattr(process, "kill"):
                        process.kill()
                        self.logger.warning("forced_kill", name=name)
                        return False

        except Exception as e:
            self.logger.error("shutdown_error", name=name, error=str(e))
            return False

        return True

    def cleanup(self) -> None:
        """Clean up all timeouts and monitoring threads."""
        # Cancel all active timeouts first
        with self.lock:
            for name in list(self.timeouts.keys()):
                if self.timeouts[name].status == TimeoutStatus.ACTIVE:
                    timeout_info = self.timeouts[name]
                    timeout_info.status = TimeoutStatus.CANCELLED
                    timeout_info.end_time = datetime.now()

        # Give threads a moment to notice cancellation
        threading.Event().wait(0.5)

        # Wait for monitor threads to finish (with short timeout)
        for thread in list(self.monitor_threads.values()):
            if thread.is_alive():
                thread.join(timeout=0.5)


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
        on_timeout: Optional[Callable] = None,
    ):
        self.manager = manager
        self.name = name
        self.timeout_seconds = timeout_seconds
        self.on_timeout = on_timeout

    def __enter__(self):
        self.manager.start_timeout(
            self.name, self.timeout_seconds, on_timeout=self.on_timeout
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.manager.complete_timeout(self.name)
        else:
            self.manager.cancel_timeout(self.name)
        return False

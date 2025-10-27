"""Central metrics collection system.

This module provides the MetricsCollector class, which acts as a central
hub for collecting all metrics during benchmark runs. It uses a singleton
pattern to ensure only one collector instance exists per run.
"""

import time
import threading
from datetime import datetime, UTC
from typing import Optional, Any, Dict
from uuid import uuid4

from .models import (
    BenchmarkMetrics,
    PerformanceMetrics,
    AutonomyMetrics,
    QualityMetrics,
    WorkflowMetrics,
)


class MetricsCollector:
    """
    Central collector for benchmark metrics.

    Singleton pattern ensures one instance per run. Provides thread-safe
    methods for recording events, timers, counters, and values.

    Example:
        collector = MetricsCollector()
        collector.start_collection("my-project", "basic-benchmark")

        collector.start_timer("planning_phase")
        # ... do work ...
        collector.stop_timer("planning_phase")

        metrics = collector.stop_collection()
    """

    _instance: Optional["MetricsCollector"] = None
    _lock = threading.Lock()

    def __new__(cls):
        """
        Singleton implementation.

        Returns:
            The single MetricsCollector instance
        """
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
        self.start_time = datetime.now(UTC)
        self.timers: Dict[str, float] = {}
        self.counters: Dict[str, int] = {}
        self.values: Dict[str, Any] = {}
        self.events: list = []
        self._is_collecting = False
        self.project_name = ""
        self.benchmark_name = ""

    def start_collection(self, project_name: str, benchmark_name: str) -> None:
        """
        Start metrics collection for a benchmark run.

        Args:
            project_name: Name of the project being benchmarked
            benchmark_name: Name of the benchmark configuration
        """
        self.reset()
        self.project_name = project_name
        self.benchmark_name = benchmark_name
        self._is_collecting = True
        self.collection_start_time = time.time()

    def stop_collection(self) -> BenchmarkMetrics:
        """
        Stop collection and return final metrics.

        Returns:
            BenchmarkMetrics object containing all collected metrics
        """
        self._is_collecting = False
        return self.get_current_metrics()

    def start_timer(self, name: str) -> None:
        """
        Start a named timer.

        Args:
            name: Timer name/identifier
        """
        self.timers[f"{name}_start"] = time.time()

    def stop_timer(self, name: str) -> float:
        """
        Stop a named timer and return elapsed time.

        Args:
            name: Timer name/identifier

        Returns:
            Elapsed time in seconds
        """
        start_key = f"{name}_start"
        if start_key not in self.timers:
            return 0.0
        elapsed = time.time() - self.timers[start_key]
        self.values[f"{name}_time"] = elapsed
        return elapsed

    def increment_counter(self, name: str, amount: int = 1) -> None:
        """
        Increment a named counter.

        Args:
            name: Counter name/identifier
            amount: Amount to increment by (default: 1)
        """
        with self._lock:
            self.counters[name] = self.counters.get(name, 0) + amount

    def set_value(self, name: str, value: Any) -> None:
        """
        Set a named value.

        Args:
            name: Value name/identifier
            value: Value to set
        """
        with self._lock:
            self.values[name] = value

    def get_value(self, name: str, default: Any = None) -> Any:
        """
        Get a named value.

        Args:
            name: Value name/identifier
            default: Default value if not found

        Returns:
            The value, or default if not found
        """
        return self.values.get(name, default)

    def get_counter(self, name: str, default: int = 0) -> int:
        """
        Get a named counter value.

        Args:
            name: Counter name/identifier
            default: Default value if not found

        Returns:
            The counter value, or default if not found
        """
        return self.counters.get(name, default)

    def record_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Record an event with timestamp.

        Args:
            event_type: Type/category of event
            data: Event data dictionary
        """
        with self._lock:
            self.events.append(
                {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "type": event_type,
                    "data": data,
                }
            )

    def get_current_metrics(self) -> BenchmarkMetrics:
        """
        Get current metrics snapshot.

        Returns:
            BenchmarkMetrics object with current state
        """
        total_time = (
            time.time() - self.collection_start_time
            if hasattr(self, "collection_start_time")
            else 0.0
        )

        # Extract phase times from timers
        phase_times = {}
        for key, value in self.values.items():
            if key.endswith("_time"):
                phase_name = key.replace("_time", "")
                phase_times[phase_name] = value

        metrics = BenchmarkMetrics(
            run_id=self.run_id,
            timestamp=self.start_time.isoformat(),
            project_name=self.project_name or "unknown",
            benchmark_name=self.benchmark_name or "unknown",
            performance=PerformanceMetrics(
                total_time_seconds=total_time, phase_times=phase_times
            ),
            autonomy=AutonomyMetrics(),
            quality=QualityMetrics(),
            workflow=WorkflowMetrics(),
            metadata={
                "events_count": len(self.events),
                "timers_count": len([k for k in self.timers if k.endswith("_start")]),
                "counters": dict(self.counters),
                "is_collecting": self._is_collecting,
            },
        )

        return metrics

    def is_collecting(self) -> bool:
        """
        Check if currently collecting metrics.

        Returns:
            True if collecting, False otherwise
        """
        return self._is_collecting

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._is_collecting:
            self.stop_collection()
        return False

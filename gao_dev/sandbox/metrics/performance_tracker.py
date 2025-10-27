"""Performance metrics tracking.

This module provides the PerformanceTracker class, which wraps MetricsCollector
to provide convenient context managers and methods for tracking performance metrics
during benchmark runs.

It handles:
- Phase-level timing with context managers
- Token usage tracking and cost calculation
- Claude API pricing for different models
- Thread-safe operations with minimal overhead
"""

import time
import threading
from typing import Optional, Dict
from contextlib import contextmanager

from .collector import MetricsCollector


class PerformanceTracker:
    """
    Tracks performance metrics during benchmark execution.

    Wraps MetricsCollector to provide convenient methods for tracking:
    - Phase execution times
    - Token usage by agent and operation
    - API costs based on Claude pricing

    Designed to have minimal performance overhead (<5%) and be thread-safe.

    Example:
        tracker = PerformanceTracker()

        # Track phase timing
        with tracker.track_phase("planning"):
            # Execute planning phase
            pass

        # Track token usage
        tracker.track_tokens(
            agent_name="john",
            input_tokens=1000,
            output_tokens=500,
            model="claude-sonnet-4-5"
        )

        # Get total cost
        total_cost = tracker.get_total_cost()
    """

    # Claude API pricing ($ per 1M tokens)
    # Source: https://www.anthropic.com/api (as of 2025-01-27)
    PRICING = {
        "claude-sonnet-4-5": {"input": 3.0, "output": 15.0},
        "claude-opus-4": {"input": 15.0, "output": 75.0},
        "claude-haiku-4": {"input": 0.25, "output": 1.25},
    }

    def __init__(self, collector: Optional[MetricsCollector] = None):
        """
        Initialize performance tracker.

        Args:
            collector: Optional MetricsCollector instance. If None, uses singleton.
        """
        self.collector = collector or MetricsCollector()
        self._lock = threading.Lock()

    @contextmanager
    def track_phase(self, phase_name: str):
        """
        Context manager for tracking phase execution time.

        Automatically starts a timer when entering the context and stops it
        when exiting, recording the elapsed time. Thread-safe and handles
        exceptions properly.

        Args:
            phase_name: Name of the phase being tracked (e.g., "planning", "implementation")

        Yields:
            None

        Example:
            with tracker.track_phase("planning"):
                # Do planning work
                create_prd()
                create_stories()
            # Elapsed time automatically recorded
        """
        timer_name = f"phase_{phase_name}"
        start = time.time()
        self.collector.start_timer(timer_name)

        try:
            yield
        finally:
            elapsed = time.time() - start
            self.collector.stop_timer(timer_name)
            # Also set explicit value for easy retrieval
            self.collector.set_value(f"{timer_name}_seconds", elapsed)

    def track_tokens(
        self,
        agent_name: str,
        input_tokens: int,
        output_tokens: int,
        model: str = "claude-sonnet-4-5",
    ) -> None:
        """
        Track token usage and calculate cost.

        Records token usage by agent and calculates API cost based on model pricing.
        Thread-safe and updates multiple counters atomically.

        Args:
            agent_name: Name of the agent that used the tokens (e.g., "john", "amelia")
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            model: Model identifier for pricing (default: "claude-sonnet-4-5")

        Example:
            tracker.track_tokens(
                agent_name="amelia",
                input_tokens=5000,
                output_tokens=2000,
                model="claude-sonnet-4-5"
            )
        """
        total_tokens = input_tokens + output_tokens

        # Track tokens with thread safety
        with self._lock:
            # Total token usage
            self.collector.increment_counter("tokens_total", total_tokens)
            self.collector.increment_counter("tokens_input", input_tokens)
            self.collector.increment_counter("tokens_output", output_tokens)

            # Per-agent token usage
            self.collector.increment_counter(f"tokens_{agent_name}", total_tokens)
            self.collector.increment_counter(f"tokens_{agent_name}_input", input_tokens)
            self.collector.increment_counter(f"tokens_{agent_name}_output", output_tokens)

            # API call tracking
            self.collector.increment_counter("api_calls", 1)
            self.collector.increment_counter(f"api_calls_{agent_name}", 1)

            # Calculate and accumulate cost
            cost = self._calculate_cost(input_tokens, output_tokens, model)
            current_cost = self.collector.get_value("api_cost_total", 0.0)
            self.collector.set_value("api_cost_total", current_cost + cost)

            # Per-agent cost
            agent_cost_key = f"api_cost_{agent_name}"
            agent_current_cost = self.collector.get_value(agent_cost_key, 0.0)
            self.collector.set_value(agent_cost_key, agent_current_cost + cost)

            # Per-model cost
            model_cost_key = f"api_cost_{model}"
            model_current_cost = self.collector.get_value(model_cost_key, 0.0)
            self.collector.set_value(model_cost_key, model_current_cost + cost)

    def track_operation(
        self,
        operation_name: str,
        input_tokens: int,
        output_tokens: int,
        model: str = "claude-sonnet-4-5",
    ) -> None:
        """
        Track token usage for a specific operation.

        Similar to track_tokens but for tracking operations instead of agents.
        Useful for tracking specific tool usage or workflow steps.

        Args:
            operation_name: Name of the operation (e.g., "code_review", "test_generation")
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            model: Model identifier for pricing (default: "claude-sonnet-4-5")

        Example:
            tracker.track_operation(
                operation_name="code_review",
                input_tokens=8000,
                output_tokens=1500,
                model="claude-sonnet-4-5"
            )
        """
        total_tokens = input_tokens + output_tokens

        with self._lock:
            # Per-operation token tracking
            self.collector.increment_counter(f"tokens_op_{operation_name}", total_tokens)
            self.collector.increment_counter(
                f"tokens_op_{operation_name}_input", input_tokens
            )
            self.collector.increment_counter(
                f"tokens_op_{operation_name}_output", output_tokens
            )

            # Cost for this operation
            cost = self._calculate_cost(input_tokens, output_tokens, model)
            op_cost_key = f"api_cost_op_{operation_name}"
            op_current_cost = self.collector.get_value(op_cost_key, 0.0)
            self.collector.set_value(op_cost_key, op_current_cost + cost)

    def _calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """
        Calculate API cost based on tokens and model.

        Uses pricing from PRICING dict. Defaults to Sonnet 4.5 pricing if model
        is not found.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model identifier

        Returns:
            Cost in USD

        Example:
            >>> tracker = PerformanceTracker()
            >>> cost = tracker._calculate_cost(1000000, 500000, "claude-sonnet-4-5")
            >>> assert cost == 10.5  # $3 + $7.5
        """
        # Get pricing for model, default to Sonnet 4.5
        pricing = self.PRICING.get(model, self.PRICING["claude-sonnet-4-5"])

        # Calculate costs per million tokens
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def get_total_cost(self) -> float:
        """
        Get total API cost accumulated so far.

        Returns:
            Total cost in USD

        Example:
            >>> tracker = PerformanceTracker()
            >>> tracker.track_tokens("amelia", 1000, 500)
            >>> cost = tracker.get_total_cost()
            >>> assert cost > 0
        """
        return self.collector.get_value("api_cost_total", 0.0)

    def get_agent_cost(self, agent_name: str) -> float:
        """
        Get API cost for a specific agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Cost in USD for this agent

        Example:
            >>> tracker = PerformanceTracker()
            >>> tracker.track_tokens("amelia", 1000, 500)
            >>> cost = tracker.get_agent_cost("amelia")
            >>> assert cost > 0
        """
        return self.collector.get_value(f"api_cost_{agent_name}", 0.0)

    def get_total_tokens(self) -> int:
        """
        Get total tokens used across all operations.

        Returns:
            Total token count

        Example:
            >>> tracker = PerformanceTracker()
            >>> tracker.track_tokens("amelia", 1000, 500)
            >>> tokens = tracker.get_total_tokens()
            >>> assert tokens == 1500
        """
        return self.collector.get_counter("tokens_total", 0)

    def get_agent_tokens(self, agent_name: str) -> int:
        """
        Get total tokens used by a specific agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Token count for this agent

        Example:
            >>> tracker = PerformanceTracker()
            >>> tracker.track_tokens("amelia", 1000, 500)
            >>> tokens = tracker.get_agent_tokens("amelia")
            >>> assert tokens == 1500
        """
        return self.collector.get_counter(f"tokens_{agent_name}", 0)

    def get_api_calls(self) -> int:
        """
        Get total number of API calls made.

        Returns:
            Total API call count

        Example:
            >>> tracker = PerformanceTracker()
            >>> tracker.track_tokens("amelia", 1000, 500)
            >>> calls = tracker.get_api_calls()
            >>> assert calls == 1
        """
        return self.collector.get_counter("api_calls", 0)

    def get_phase_time(self, phase_name: str) -> float:
        """
        Get elapsed time for a specific phase.

        Args:
            phase_name: Name of the phase

        Returns:
            Elapsed time in seconds, or 0.0 if phase not tracked

        Example:
            >>> tracker = PerformanceTracker()
            >>> with tracker.track_phase("planning"):
            ...     time.sleep(0.1)
            >>> elapsed = tracker.get_phase_time("planning")
            >>> assert elapsed >= 0.1
        """
        return self.collector.get_value(f"phase_{phase_name}_seconds", 0.0)

    def get_performance_summary(self) -> Dict[str, any]:
        """
        Get a summary of all performance metrics.

        Returns:
            Dictionary containing:
                - total_cost: Total API cost in USD
                - total_tokens: Total token count
                - api_calls: Total API calls made
                - phases: Dict of phase names to elapsed times

        Example:
            >>> tracker = PerformanceTracker()
            >>> with tracker.track_phase("planning"):
            ...     tracker.track_tokens("john", 1000, 500)
            >>> summary = tracker.get_performance_summary()
            >>> assert "total_cost" in summary
            >>> assert "total_tokens" in summary
        """
        # Get all phase times
        phases = {}
        for key, value in self.collector.values.items():
            if key.startswith("phase_") and key.endswith("_seconds"):
                phase_name = key.replace("phase_", "").replace("_seconds", "")
                phases[phase_name] = value

        return {
            "total_cost": self.get_total_cost(),
            "total_tokens": self.get_total_tokens(),
            "api_calls": self.get_api_calls(),
            "phases": phases,
        }

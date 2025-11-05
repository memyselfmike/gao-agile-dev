"""Provider performance tracking."""

from typing import Dict
from collections import defaultdict
import structlog

logger = structlog.get_logger(__name__)


class ProviderPerformanceTracker:
    """Tracks performance metrics for each provider."""

    def __init__(self):
        """Initialize tracker."""
        # provider_name -> model -> list of execution times
        self._execution_times: Dict[str, Dict[str, list[float]]] = defaultdict(
            lambda: defaultdict(list)
        )

    def record_execution_time(
        self, provider_name: str, model: str, execution_time: float
    ):
        """
        Record execution time for provider/model.

        Args:
            provider_name: Name of provider
            model: Model name
            execution_time: Execution time in seconds
        """
        self._execution_times[provider_name][model].append(execution_time)

        logger.debug(
            "performance_recorded",
            provider=provider_name,
            model=model,
            execution_time=execution_time,
        )

    def get_avg_execution_time(
        self, provider_name: str, model: str
    ) -> float:
        """
        Get average execution time for provider/model.

        Args:
            provider_name: Name of provider
            model: Model name

        Returns:
            Average execution time, or infinity if no data
        """
        times = self._execution_times.get(provider_name, {}).get(model, [])

        if not times:
            return float("inf")

        return sum(times) / len(times)

    def get_all_stats(self) -> Dict[str, Dict[str, Dict[str, float]]]:
        """
        Get all performance statistics.

        Returns:
            Nested dict of provider -> model -> stats
        """
        stats = {}

        for provider_name, models in self._execution_times.items():
            stats[provider_name] = {}

            for model, times in models.items():
                if times:
                    stats[provider_name][model] = {
                        "avg": sum(times) / len(times),
                        "min": min(times),
                        "max": max(times),
                        "count": len(times),
                    }

        return stats

    def clear(self):
        """Clear all performance data."""
        self._execution_times.clear()
        logger.debug("performance_tracker_cleared")

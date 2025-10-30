"""Resource monitoring for plugins.

This module provides resource monitoring to track plugin CPU and memory usage
and enforce resource limits.
"""

import time
from typing import Dict, Optional
import structlog

from .models import ResourceUsage
from .exceptions import ResourceLimitError

logger = structlog.get_logger(__name__)


class ResourceMonitor:
    """Monitors plugin resource usage and enforces limits.

    The ResourceMonitor tracks CPU and memory usage for each plugin and
    can check against configured limits.

    Example:
        ```python
        monitor = ResourceMonitor()

        # Start monitoring
        monitor.start_monitoring("my-plugin")

        # Check usage
        usage = monitor.get_usage("my-plugin")
        print(f"Memory: {usage.memory_mb}MB")

        # Check against limits
        if not monitor.check_limits("my-plugin", max_memory_mb=500):
            print("Plugin exceeded memory limit")

        # Stop monitoring
        monitor.stop_monitoring("my-plugin")
        ```

    Attributes:
        _usage: Dictionary mapping plugin names to ResourceUsage
    """

    def __init__(self):
        """Initialize resource monitor with empty usage tracking."""
        self._usage: Dict[str, ResourceUsage] = {}

        logger.info("resource_monitor_initialized")

    def start_monitoring(self, plugin_name: str) -> None:
        """Start monitoring resource usage for a plugin.

        Creates a ResourceUsage entry for the plugin with current timestamp.

        Args:
            plugin_name: Name of plugin to monitor

        Example:
            ```python
            monitor.start_monitoring("my-plugin")
            ```
        """
        self._usage[plugin_name] = ResourceUsage(
            cpu_percent=0.0,
            memory_mb=0.0,
            start_time=time.time(),
        )

        logger.debug(
            "resource_monitoring_started",
            plugin=plugin_name,
        )

    def stop_monitoring(self, plugin_name: str) -> Optional[ResourceUsage]:
        """Stop monitoring resource usage for a plugin.

        Removes the ResourceUsage entry and returns the final usage metrics.

        Args:
            plugin_name: Name of plugin to stop monitoring

        Returns:
            Final ResourceUsage metrics, or None if not monitored

        Example:
            ```python
            final_usage = monitor.stop_monitoring("my-plugin")
            if final_usage:
                print(f"Peak memory: {final_usage.memory_mb}MB")
            ```
        """
        usage = self._usage.pop(plugin_name, None)

        if usage:
            logger.debug(
                "resource_monitoring_stopped",
                plugin=plugin_name,
                memory_mb=usage.memory_mb,
                cpu_percent=usage.cpu_percent,
            )

        return usage

    def get_usage(self, plugin_name: str) -> Optional[ResourceUsage]:
        """Get current resource usage for a plugin.

        Args:
            plugin_name: Name of plugin

        Returns:
            Current ResourceUsage, or None if not monitored

        Example:
            ```python
            usage = monitor.get_usage("my-plugin")
            if usage:
                print(f"CPU: {usage.cpu_percent}%")
            ```
        """
        return self._usage.get(plugin_name)

    def update_usage(
        self,
        plugin_name: str,
        cpu_percent: Optional[float] = None,
        memory_mb: Optional[float] = None,
    ) -> None:
        """Update resource usage metrics for a plugin.

        Args:
            plugin_name: Name of plugin
            cpu_percent: CPU usage percentage (0-100)
            memory_mb: Memory usage in megabytes

        Example:
            ```python
            monitor.update_usage(
                "my-plugin",
                cpu_percent=45.0,
                memory_mb=128.5
            )
            ```
        """
        if plugin_name not in self._usage:
            logger.warning(
                "update_usage_plugin_not_monitored",
                plugin=plugin_name,
            )
            return

        if cpu_percent is not None:
            self._usage[plugin_name].cpu_percent = cpu_percent

        if memory_mb is not None:
            self._usage[plugin_name].memory_mb = memory_mb

    def check_limits(
        self,
        plugin_name: str,
        max_memory_mb: float = 500.0,
        max_cpu_percent: float = 80.0,
    ) -> bool:
        """Check if plugin is within resource limits.

        Logs warnings if limits are exceeded but does not raise exceptions.
        Callers can use enforce_limits() to raise on violations.

        Args:
            plugin_name: Name of plugin to check
            max_memory_mb: Maximum memory in MB (default 500)
            max_cpu_percent: Maximum CPU percentage (default 80)

        Returns:
            True if within limits, False if exceeded

        Example:
            ```python
            if not monitor.check_limits("my-plugin", max_memory_mb=250):
                print("Memory limit exceeded")
            ```
        """
        usage = self._usage.get(plugin_name)
        if not usage:
            return True

        within_limits = True

        if usage.memory_mb > max_memory_mb:
            logger.warning(
                "plugin_memory_exceeded",
                plugin=plugin_name,
                memory_mb=usage.memory_mb,
                limit=max_memory_mb,
            )
            within_limits = False

        if usage.cpu_percent > max_cpu_percent:
            logger.warning(
                "plugin_cpu_exceeded",
                plugin=plugin_name,
                cpu_percent=usage.cpu_percent,
                limit=max_cpu_percent,
            )
            within_limits = False

        return within_limits

    def enforce_limits(
        self,
        plugin_name: str,
        max_memory_mb: float = 500.0,
        max_cpu_percent: float = 80.0,
    ) -> None:
        """Enforce resource limits on a plugin.

        Raises ResourceLimitError if limits are exceeded.

        Args:
            plugin_name: Name of plugin to check
            max_memory_mb: Maximum memory in MB (default 500)
            max_cpu_percent: Maximum CPU percentage (default 80)

        Raises:
            ResourceLimitError: If resource limits exceeded

        Example:
            ```python
            # Raises if limits exceeded
            monitor.enforce_limits("my-plugin", max_memory_mb=250)
            ```
        """
        usage = self._usage.get(plugin_name)
        if not usage:
            return

        if usage.memory_mb > max_memory_mb:
            raise ResourceLimitError(
                f"Plugin '{plugin_name}' exceeded memory limit: "
                f"{usage.memory_mb}MB > {max_memory_mb}MB"
            )

        if usage.cpu_percent > max_cpu_percent:
            raise ResourceLimitError(
                f"Plugin '{plugin_name}' exceeded CPU limit: "
                f"{usage.cpu_percent}% > {max_cpu_percent}%"
            )

    def get_all_usage(self) -> Dict[str, ResourceUsage]:
        """Get resource usage for all monitored plugins.

        Returns:
            Dictionary mapping plugin names to ResourceUsage

        Example:
            ```python
            all_usage = monitor.get_all_usage()
            for name, usage in all_usage.items():
                print(f"{name}: {usage.memory_mb}MB")
            ```
        """
        return dict(self._usage)

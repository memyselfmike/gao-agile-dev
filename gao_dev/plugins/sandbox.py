"""Plugin sandboxing and security enforcement.

This module provides the PluginSandbox class which orchestrates all plugin
security features including permissions, validation, timeouts, and resource limits.
"""

import asyncio
from pathlib import Path
from typing import Any, Callable
import structlog

from .models import PluginMetadata, PluginPermission, ValidationResult
from .permission_manager import PermissionManager
from .resource_monitor import ResourceMonitor
from .exceptions import PluginTimeoutError

logger = structlog.get_logger(__name__)


class PluginSandbox:
    """Enforces security and resource limits for plugins.

    The PluginSandbox provides comprehensive security controls including:
    - Permission management
    - Code validation (static analysis)
    - Timeout enforcement
    - Resource monitoring

    Example:
        ```python
        sandbox = PluginSandbox()

        # Validate plugin before loading
        result = sandbox.validate_plugin(metadata)
        if not result.valid:
            print(f"Validation failed: {result.errors}")

        # Check permission before operation
        if sandbox.check_permission("my-plugin", PluginPermission.FILE_READ):
            # Perform file read
            pass

        # Execute with timeout
        result = await sandbox.execute_with_timeout(
            my_function,
            timeout_seconds=30
        )
        ```

    Attributes:
        _permission_manager: Manages plugin permissions
        _resource_monitor: Monitors resource usage
    """

    def __init__(self):
        """Initialize plugin sandbox with default configuration."""
        self._permission_manager = PermissionManager()
        self._resource_monitor = ResourceMonitor()

        logger.info("plugin_sandbox_initialized")

    def validate_plugin(self, metadata: PluginMetadata) -> ValidationResult:
        """Validate plugin for security issues.

        Performs static analysis of plugin code looking for:
        - Dangerous imports (os.system, subprocess, eval, exec)
        - File system manipulation
        - Network access
        - Invalid entry points

        Args:
            metadata: Plugin metadata to validate

        Returns:
            ValidationResult with errors and warnings

        Example:
            ```python
            result = sandbox.validate_plugin(metadata)
            if not result.valid:
                print("Validation failed:", result.errors)
            for warning in result.warnings:
                print("Warning:", warning)
            ```
        """
        errors = []
        warnings = []

        # Validate entry point format
        if not self._is_valid_entry_point(metadata.entry_point):
            errors.append(f"Invalid entry point format: {metadata.entry_point}")

        # Validate permissions
        for perm_str in metadata.permissions:
            try:
                PluginPermission(perm_str)
            except ValueError:
                errors.append(f"Invalid permission: {perm_str}")

        # Scan plugin code for security issues
        if metadata.plugin_path.exists():
            code_warnings = self._scan_plugin_code(metadata.plugin_path)
            warnings.extend(code_warnings)

        result = ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

        if not result.valid:
            logger.error(
                "plugin_validation_failed",
                plugin=metadata.name,
                errors=errors,
            )
        elif warnings:
            logger.warning(
                "plugin_validation_warnings",
                plugin=metadata.name,
                warnings=warnings,
            )
        else:
            logger.info(
                "plugin_validation_passed",
                plugin=metadata.name,
            )

        return result

    def check_permission(
        self,
        plugin_name: str,
        operation: PluginPermission,
    ) -> bool:
        """Check if plugin has permission for operation.

        Args:
            plugin_name: Name of plugin
            operation: Permission being checked

        Returns:
            True if permitted, False otherwise

        Example:
            ```python
            if sandbox.check_permission("my-plugin", PluginPermission.FILE_WRITE):
                # Perform file write
                pass
            ```
        """
        return self._permission_manager.has_permission(plugin_name, operation)

    def enforce_permission(
        self,
        plugin_name: str,
        operation: PluginPermission,
    ) -> None:
        """Enforce that plugin has permission.

        Args:
            plugin_name: Name of plugin
            operation: Permission being enforced

        Raises:
            PermissionDeniedError: If permission not granted
        """
        self._permission_manager.enforce_permission(plugin_name, operation)

    async def execute_with_timeout(
        self,
        func: Callable,
        timeout_seconds: float,
        *args,
        **kwargs,
    ) -> Any:
        """Execute function with timeout limit.

        Supports both synchronous and asynchronous functions.

        Args:
            func: Function to execute
            timeout_seconds: Timeout in seconds
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            PluginTimeoutError: If execution exceeds timeout

        Example:
            ```python
            result = await sandbox.execute_with_timeout(
                my_function,
                30.0,
                arg1="value"
            )
            ```
        """
        try:
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds,
                )
            else:
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, func, *args, **kwargs),
                    timeout=timeout_seconds,
                )
            return result

        except asyncio.TimeoutError:
            logger.error(
                "plugin_timeout",
                function=func.__name__,
                timeout=timeout_seconds,
            )
            raise PluginTimeoutError(
                f"Plugin execution exceeded timeout of {timeout_seconds}s"
            )

    def grant_permissions(
        self,
        plugin_name: str,
        permissions: list[str],
    ) -> None:
        """Grant permissions to plugin.

        Args:
            plugin_name: Name of plugin
            permissions: List of permission strings
        """
        self._permission_manager.grant_permissions(plugin_name, permissions)

    def revoke_all_permissions(self, plugin_name: str) -> int:
        """Revoke all permissions from plugin.

        Args:
            plugin_name: Name of plugin

        Returns:
            Number of permissions revoked
        """
        return self._permission_manager.revoke_all_permissions(plugin_name)

    def start_monitoring(self, plugin_name: str) -> None:
        """Start monitoring resource usage for plugin.

        Args:
            plugin_name: Name of plugin
        """
        self._resource_monitor.start_monitoring(plugin_name)

    def stop_monitoring(self, plugin_name: str) -> None:
        """Stop monitoring resource usage for plugin.

        Args:
            plugin_name: Name of plugin
        """
        self._resource_monitor.stop_monitoring(plugin_name)

    def check_resource_limits(
        self,
        plugin_name: str,
        max_memory_mb: float = 500.0,
        max_cpu_percent: float = 80.0,
    ) -> bool:
        """Check if plugin is within resource limits.

        Args:
            plugin_name: Name of plugin
            max_memory_mb: Maximum memory in MB
            max_cpu_percent: Maximum CPU percentage

        Returns:
            True if within limits, False otherwise
        """
        return self._resource_monitor.check_limits(
            plugin_name,
            max_memory_mb=max_memory_mb,
            max_cpu_percent=max_cpu_percent,
        )

    def _is_valid_entry_point(self, entry_point: str) -> bool:
        """Check if entry point format is valid.

        Args:
            entry_point: Entry point string (e.g., "module.Class")

        Returns:
            True if valid format
        """
        parts = entry_point.split(".")
        if len(parts) < 2:
            return False

        # Check each part is valid Python identifier
        return all(part.isidentifier() for part in parts)

    def _scan_plugin_code(self, plugin_path: Path) -> list[str]:
        """Scan plugin code for security issues.

        Performs simple pattern matching to detect suspicious code.
        This is not a comprehensive security analysis.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            List of warning messages
        """
        warnings = []

        # Dangerous patterns to check for
        dangerous_patterns = {
            "os.system": "Uses os.system for command execution",
            "subprocess.call": "Uses subprocess for command execution",
            "subprocess.run": "Uses subprocess for command execution",
            "subprocess.Popen": "Uses subprocess for command execution",
            "eval(": "Uses eval() for dynamic code execution",
            "exec(": "Uses exec() for dynamic code execution",
            "__import__": "Uses __import__() for dynamic imports",
            "shutil.rmtree": "Uses shutil.rmtree() for recursive deletion",
            "os.remove": "Uses os.remove() for file deletion",
            "os.unlink": "Uses os.unlink() for file deletion",
            "urllib.request": "Makes network requests",
            "requests.": "Makes network requests",
            "socket.": "Uses raw sockets",
        }

        for py_file in plugin_path.glob("**/*.py"):
            try:
                code = py_file.read_text(encoding="utf-8")

                for pattern, description in dangerous_patterns.items():
                    if pattern in code:
                        warnings.append(
                            f"{py_file.name}: {description} ({pattern})"
                        )

            except Exception as e:
                logger.warning(
                    "code_scan_failed",
                    file=str(py_file),
                    error=str(e),
                )

        return warnings

    @property
    def permission_manager(self) -> PermissionManager:
        """Get permission manager instance."""
        return self._permission_manager

    @property
    def resource_monitor(self) -> ResourceMonitor:
        """Get resource monitor instance."""
        return self._resource_monitor

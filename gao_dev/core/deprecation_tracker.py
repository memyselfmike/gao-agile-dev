"""Deprecation tracking for GAO-Dev commands.

This module provides telemetry tracking for deprecated command usage,
enabling monitoring of migration progress and planning for removal.
"""

import os
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import structlog

logger = structlog.get_logger(__name__)


class DeprecationTracker:
    """Track usage of deprecated commands for telemetry.

    This class logs deprecation events and optionally persists them
    to a file for analysis. It is thread-safe and can be used from
    multiple CLI commands simultaneously.

    Example:
        >>> tracker = DeprecationTracker()
        >>> tracker.track_usage("gao-dev init", "gao-dev start", "v3.0")
        >>> stats = tracker.get_usage_stats()
        >>> print(stats["total_calls"])
    """

    _instance: Optional["DeprecationTracker"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, storage_path: Optional[Path] = None) -> "DeprecationTracker":
        """Singleton pattern for consistent tracking across the application."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        """Initialize the deprecation tracker.

        Args:
            storage_path: Optional path to persist deprecation events.
                         Defaults to .gao-dev/deprecation_events.json
        """
        if getattr(self, "_initialized", False):
            return

        self._storage_path = storage_path
        self._events: list[dict[str, Any]] = []
        self._stats: dict[str, int] = {}
        self._initialized = True

        # Load existing events if storage exists
        self._load_events()

    def _get_storage_path(self) -> Path:
        """Get the storage path for deprecation events.

        Returns:
            Path to the deprecation events JSON file.
        """
        if self._storage_path:
            return self._storage_path

        # Default to .gao-dev in current directory
        gao_dev_dir = Path.cwd() / ".gao-dev"
        if not gao_dev_dir.exists():
            # Try project root detection
            current = Path.cwd()
            while current != current.parent:
                candidate = current / ".gao-dev"
                if candidate.exists():
                    gao_dev_dir = candidate
                    break
                current = current.parent
            else:
                # Fall back to temp directory
                import tempfile
                gao_dev_dir = Path(tempfile.gettempdir()) / ".gao-dev"

        return gao_dev_dir / "deprecation_events.json"

    def _load_events(self) -> None:
        """Load existing events from storage."""
        storage_path = self._get_storage_path()

        if storage_path.exists():
            try:
                with open(storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._events = data.get("events", [])
                    self._stats = data.get("stats", {})
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(
                    "failed_to_load_deprecation_events",
                    error=str(e),
                    path=str(storage_path),
                )
                self._events = []
                self._stats = {}

    def _save_events(self) -> None:
        """Save events to storage."""
        storage_path = self._get_storage_path()

        try:
            # Ensure directory exists
            storage_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "events": self._events,
                "stats": self._stats,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }

            with open(storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)

        except IOError as e:
            logger.warning(
                "failed_to_save_deprecation_events",
                error=str(e),
                path=str(storage_path),
            )

    def track_usage(
        self,
        command: str,
        replacement: Optional[str] = None,
        removal_version: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log deprecation usage event.

        Args:
            command: The deprecated command that was used.
            replacement: The new command to use instead.
            removal_version: Version when command will be removed.
            context: Additional context about the usage.
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        event = {
            "timestamp": timestamp,
            "command": command,
            "replacement": replacement,
            "removal_version": removal_version,
            "context": context or {},
            "environment": {
                "platform": os.sys.platform,
                "cwd": str(Path.cwd()),
                "headless": os.environ.get("GAO_DEV_HEADLESS", "false").lower() == "true",
                "ci": self._detect_ci_environment(),
            },
        }

        # Log the event
        logger.warning(
            "deprecated_command_usage",
            command=command,
            replacement=replacement,
            removal_version=removal_version,
            ci_environment=event["environment"]["ci"],
        )

        # Update in-memory tracking
        with self._lock:
            self._events.append(event)

            # Update stats
            if command not in self._stats:
                self._stats[command] = 0
            self._stats[command] += 1

            # Persist to storage
            self._save_events()

    def get_usage_stats(self) -> dict[str, Any]:
        """Get deprecation usage statistics.

        Returns:
            Dictionary containing:
                - total_calls: Total number of deprecated command calls
                - commands: Per-command usage counts
                - first_seen: Timestamp of first deprecated command usage
                - last_seen: Timestamp of most recent usage
                - ci_percentage: Percentage of calls from CI environments
        """
        with self._lock:
            if not self._events:
                return {
                    "total_calls": 0,
                    "commands": {},
                    "first_seen": None,
                    "last_seen": None,
                    "ci_percentage": 0.0,
                }

            ci_calls = sum(
                1 for event in self._events
                if event.get("environment", {}).get("ci", False)
            )

            return {
                "total_calls": len(self._events),
                "commands": self._stats.copy(),
                "first_seen": self._events[0]["timestamp"] if self._events else None,
                "last_seen": self._events[-1]["timestamp"] if self._events else None,
                "ci_percentage": (ci_calls / len(self._events)) * 100 if self._events else 0.0,
            }

    def get_events(
        self,
        command: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get deprecation events with optional filtering.

        Args:
            command: Filter by specific command.
            since: Filter events after this timestamp.
            limit: Maximum number of events to return.

        Returns:
            List of deprecation events.
        """
        with self._lock:
            events = self._events.copy()

        if command:
            events = [e for e in events if e["command"] == command]

        if since:
            since_iso = since.isoformat()
            events = [e for e in events if e["timestamp"] >= since_iso]

        # Return most recent events first
        events = sorted(events, key=lambda e: e["timestamp"], reverse=True)

        return events[:limit]

    def clear_events(self) -> None:
        """Clear all stored deprecation events.

        This is primarily for testing purposes.
        """
        with self._lock:
            self._events = []
            self._stats = {}

            storage_path = self._get_storage_path()
            if storage_path.exists():
                try:
                    storage_path.unlink()
                except IOError as e:
                    logger.warning(
                        "failed_to_clear_deprecation_events",
                        error=str(e),
                    )

    def _detect_ci_environment(self) -> bool:
        """Detect if running in a CI environment.

        Returns:
            True if running in CI, False otherwise.
        """
        ci_env_vars = [
            "CI",
            "CONTINUOUS_INTEGRATION",
            "GITHUB_ACTIONS",
            "GITLAB_CI",
            "JENKINS_URL",
            "CIRCLECI",
            "TRAVIS",
            "BUILDKITE",
            "AZURE_PIPELINES",
            "TF_BUILD",
        ]

        return any(os.environ.get(var) for var in ci_env_vars)

    @classmethod
    def reset_singleton(cls) -> None:
        """Reset the singleton instance.

        This is primarily for testing purposes.
        """
        with cls._lock:
            cls._instance = None


def get_tracker(storage_path: Optional[Path] = None) -> DeprecationTracker:
    """Get the deprecation tracker singleton.

    Args:
        storage_path: Optional custom storage path.

    Returns:
        The DeprecationTracker singleton instance.
    """
    return DeprecationTracker(storage_path)


def track_deprecated_command(
    command: str,
    replacement: str,
    removal_version: str = "v3.0",
    context: Optional[dict[str, Any]] = None,
) -> None:
    """Convenience function to track deprecated command usage.

    Args:
        command: The deprecated command that was used.
        replacement: The new command to use instead.
        removal_version: Version when command will be removed.
        context: Additional context about the usage.

    Example:
        >>> track_deprecated_command(
        ...     "gao-dev init",
        ...     "gao-dev start",
        ...     "v3.0",
        ...     {"project_name": "my-project"}
        ... )
    """
    tracker = get_tracker()
    tracker.track_usage(command, replacement, removal_version, context)

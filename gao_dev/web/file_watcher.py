"""File system watcher for real-time file change detection.

Monitors project directories and emits WebSocket events for file changes.

Epic: 39.4 - File Management
Story: 39.13 - Real-Time File Updates from Agents
"""

import asyncio
import time
from pathlib import Path
from typing import Optional, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import structlog

from .event_bus import WebEventBus
from .events import EventType

logger = structlog.get_logger(__name__)

# Tracked directories to monitor
TRACKED_DIRECTORIES = {"docs", "src", "gao_dev", "tests"}


class FileChangeHandler(FileSystemEventHandler):
    """Handler for file system events."""

    def __init__(self, event_bus: WebEventBus, project_root: Path, loop: asyncio.AbstractEventLoop):
        """Initialize handler.

        Args:
            event_bus: WebEventBus for publishing events
            project_root: Root directory of project
            loop: asyncio event loop for async operations
        """
        super().__init__()
        self.event_bus = event_bus
        self.project_root = project_root
        self.loop = loop
        self.logger = logger.bind(handler="file_change_handler")

    def _should_process(self, path: str) -> bool:
        """Check if file should be processed.

        Args:
            path: Absolute path to file/directory

        Returns:
            True if should process, False otherwise
        """
        file_path = Path(path)

        # Ignore hidden files/directories
        if any(part.startswith('.') for part in file_path.parts):
            return False

        # Check if in tracked directory
        try:
            rel_path = file_path.relative_to(self.project_root)
            first_part = rel_path.parts[0] if rel_path.parts else None
            return first_part in TRACKED_DIRECTORIES
        except (ValueError, IndexError):
            return False

    def _get_relative_path(self, path: str) -> str:
        """Get relative path from project root.

        Args:
            path: Absolute path

        Returns:
            Relative path as string with forward slashes
        """
        try:
            return str(Path(path).relative_to(self.project_root)).replace('\\', '/')
        except ValueError:
            return path

    def _emit_event(self, event_type: str, path: str, is_directory: bool = False) -> None:
        """Emit file event to WebSocket clients.

        Args:
            event_type: Type of event (created, modified, deleted)
            path: Absolute path to file/directory
            is_directory: Whether path is a directory
        """
        if not self._should_process(path):
            return

        rel_path = self._get_relative_path(path)

        # Map string event type to EventType enum
        event_type_map = {
            "created": EventType.FILE_CREATED,
            "modified": EventType.FILE_MODIFIED,
            "deleted": EventType.FILE_DELETED,
        }

        event_enum = event_type_map.get(event_type)
        if not event_enum:
            self.logger.error("unknown_event_type", event_type=event_type)
            return

        # Publish to event bus (async call from sync context)
        data = {
            "path": rel_path,
            "isDirectory": is_directory,
            "timestamp": time.time()
        }

        try:
            asyncio.run_coroutine_threadsafe(
                self.event_bus.publish(event_enum, data),
                self.loop
            )
        except Exception as e:
            self.logger.error("event_publish_failed", error=str(e), event_type=event_type)

        self.logger.debug(
            f"file_{event_type}",
            path=rel_path,
            is_directory=is_directory
        )

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file/directory creation.

        Args:
            event: File system event
        """
        self._emit_event("created", event.src_path, event.is_directory)

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file/directory modification.

        Args:
            event: File system event
        """
        # Ignore directory modifications (too noisy)
        if not event.is_directory:
            self._emit_event("modified", event.src_path, False)

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file/directory deletion.

        Args:
            event: File system event
        """
        self._emit_event("deleted", event.src_path, event.is_directory)


class FileSystemWatcher:
    """Watches file system for changes and emits events."""

    def __init__(self, project_root: Path, event_bus: WebEventBus):
        """Initialize file system watcher.

        Args:
            project_root: Root directory of project to watch
            event_bus: WebEventBus for publishing events
        """
        self.project_root = Path(project_root)
        self.event_bus = event_bus
        self.observer: Optional[Observer] = None
        self.logger = logger.bind(service="file_system_watcher")

    def start(self) -> None:
        """Start watching file system."""
        if self.observer is not None:
            self.logger.warning("file_watcher_already_started")
            return

        # Get or create event loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, try to get or create one
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # Python 3.10+ doesn't auto-create event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

        self.observer = Observer()
        handler = FileChangeHandler(self.event_bus, self.project_root, loop)

        # Watch each tracked directory
        watched_dirs: Set[Path] = set()
        for tracked_dir in TRACKED_DIRECTORIES:
            dir_path = self.project_root / tracked_dir
            if dir_path.exists() and dir_path.is_dir():
                self.observer.schedule(handler, str(dir_path), recursive=True)
                watched_dirs.add(dir_path)

        self.observer.start()
        self.logger.info(
            "file_watcher_started",
            watched_directories=[str(d) for d in watched_dirs]
        )

    def stop(self) -> None:
        """Stop watching file system."""
        if self.observer is None:
            return

        self.observer.stop()
        self.observer.join()
        self.observer = None
        self.logger.info("file_watcher_stopped")

    def is_running(self) -> bool:
        """Check if watcher is running.

        Returns:
            True if running, False otherwise
        """
        return self.observer is not None and self.observer.is_alive()

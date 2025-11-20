"""Session lock management for exclusive write access control.

Provides thread-safe session locking mechanism to prevent concurrent write
operations between CLI and web interface while allowing observability through
read-only mode.

Key Features:
- Write lock exclusive (only one interface can hold)
- Read lock non-blocking (multiple readers allowed)
- Stale lock detection using PID validation
- Cross-platform compatibility (Windows, macOS, Linux)
- Atomic file operations to prevent race conditions
"""

import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import structlog

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore

logger = structlog.get_logger(__name__)


class SessionLock:
    """Manages session lock for exclusive write access control.

    Attributes:
        lock_file: Path to .gao-dev/session.lock
        current_mode: Current lock mode ("read", "write", "none")
        _lock: Thread lock for atomic operations
    """

    def __init__(self, project_root: Path):
        """Initialize session lock manager.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root
        self.lock_file = project_root / ".gao-dev" / "session.lock"
        self.current_mode: str = "none"
        self._lock = threading.Lock()

        # NOTE: Do NOT create .gao-dev directory here!
        # Creating it prematurely interferes with project state detection.
        # The directory will be created when first lock is acquired.

        logger.info("session_lock_initialized", lock_file=str(self.lock_file))

    def acquire(self, interface: str, mode: str = "write") -> bool:
        """Acquire session lock.

        Args:
            interface: Interface name ("cli" or "web")
            mode: Lock mode ("read" or "write")

        Returns:
            True if lock acquired, False if denied

        Raises:
            ValueError: If interface or mode is invalid
        """
        if interface not in ["cli", "web"]:
            raise ValueError(f"Invalid interface: {interface}. Must be 'cli' or 'web'")

        if mode not in ["read", "write"]:
            raise ValueError(f"Invalid mode: {mode}. Must be 'read' or 'write'")

        with self._lock:
            return self._acquire_internal(interface, mode)

    def _acquire_internal(self, interface: str, mode: str) -> bool:
        """Internal lock acquisition logic (not thread-safe).

        Args:
            interface: Interface name
            mode: Lock mode

        Returns:
            True if acquired, False if denied
        """
        # Read mode always succeeds (observability only)
        if mode == "read":
            self.current_mode = "read"
            logger.info("read_lock_acquired", interface=interface)
            return True

        # Write mode requires exclusive lock
        if self.lock_file.exists():
            try:
                lock_data = json.loads(self.lock_file.read_text(encoding="utf-8"))

                # Check if we already hold the lock
                if lock_data.get("pid") == os.getpid():
                    logger.info("write_lock_already_held", interface=interface)
                    self.current_mode = "write"
                    return True

                # Check if lock holder is alive
                if self.is_process_alive(lock_data["pid"]):
                    logger.warning(
                        "write_lock_denied",
                        holder=lock_data["interface"],
                        holder_pid=lock_data["pid"],
                        requester=interface,
                    )
                    return False
                else:
                    # Stale lock, remove it
                    logger.info(
                        "removing_stale_lock",
                        pid=lock_data["pid"],
                        interface=lock_data.get("interface", "unknown"),
                    )
                    self.lock_file.unlink()

            except (json.JSONDecodeError, KeyError) as e:
                # Corrupted lock file, remove it
                logger.warning("corrupted_lock_file", error=str(e))
                self.lock_file.unlink()

        # Acquire write lock
        lock_data = {
            "interface": interface,
            "mode": "write",
            "pid": os.getpid(),
            "timestamp": datetime.now().isoformat(),
        }

        # Ensure .gao-dev directory exists before writing lock file
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write using temporary file + rename
        temp_file = self.lock_file.with_suffix(".tmp")
        try:
            temp_file.write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
            # Atomic rename (platform-specific behavior)
            if os.name == "nt":  # Windows
                if self.lock_file.exists():
                    self.lock_file.unlink()
            temp_file.rename(self.lock_file)

            self.current_mode = "write"
            logger.info("write_lock_acquired", interface=interface, pid=os.getpid())
            return True

        except Exception as e:
            logger.error("write_lock_acquisition_failed", error=str(e))
            if temp_file.exists():
                temp_file.unlink()
            return False

    def release(self) -> None:
        """Release session lock.

        Safe to call even if no lock is held.
        """
        with self._lock:
            if self.lock_file.exists():
                try:
                    lock_data = json.loads(self.lock_file.read_text(encoding="utf-8"))
                    # Only remove if we hold the lock
                    if lock_data.get("pid") == os.getpid():
                        self.lock_file.unlink()
                        logger.info("lock_released", mode=self.current_mode)
                    else:
                        logger.warning(
                            "lock_release_denied",
                            our_pid=os.getpid(),
                            lock_pid=lock_data.get("pid"),
                        )
                except Exception as e:
                    logger.error("lock_release_failed", error=str(e))

            self.current_mode = "none"

    def upgrade(self, interface: str) -> bool:
        """Upgrade from read lock to write lock.

        Args:
            interface: Interface name

        Returns:
            True if upgraded, False if denied
        """
        logger.info("lock_upgrade_requested", interface=interface, current_mode=self.current_mode)
        return self.acquire(interface, mode="write")

    def downgrade(self, interface: str) -> bool:
        """Downgrade from write lock to read lock.

        Args:
            interface: Interface name

        Returns:
            True if downgraded, False if failed
        """
        with self._lock:
            if self.current_mode != "write":
                logger.warning("downgrade_denied", current_mode=self.current_mode)
                return False

            # Release write lock if we hold it
            if self.lock_file.exists():
                try:
                    lock_data = json.loads(self.lock_file.read_text(encoding="utf-8"))
                    if lock_data.get("pid") == os.getpid():
                        self.lock_file.unlink()
                        logger.info("write_lock_released_for_downgrade")
                except Exception as e:
                    logger.error("downgrade_failed", error=str(e))
                    return False

            # Switch to read mode
            self.current_mode = "read"
            logger.info("lock_downgraded", interface=interface)
            return True

    def is_write_locked_by_other(self) -> bool:
        """Check if another process holds write lock.

        Returns:
            True if another process holds write lock, False otherwise
        """
        with self._lock:
            if not self.lock_file.exists():
                return False

            try:
                lock_data = json.loads(self.lock_file.read_text(encoding="utf-8"))

                # We hold the lock
                if lock_data.get("pid") == os.getpid():
                    return False

                # Check if lock holder is alive
                return self.is_process_alive(lock_data["pid"])

            except (json.JSONDecodeError, KeyError) as e:
                logger.warning("lock_check_failed", error=str(e))
                return False

    def get_lock_state(self) -> Dict[str, Optional[str]]:
        """Get current lock state.

        Returns:
            Dictionary with mode, holder, and timestamp
        """
        with self._lock:
            if not self.lock_file.exists():
                return {"mode": "write", "holder": None, "timestamp": None}

            try:
                lock_data = json.loads(self.lock_file.read_text(encoding="utf-8"))

                # We hold the lock
                if lock_data.get("pid") == os.getpid():
                    return {
                        "mode": "write",
                        "holder": lock_data.get("interface"),
                        "timestamp": lock_data.get("timestamp"),
                    }

                # Check if lock holder is alive
                if self.is_process_alive(lock_data["pid"]):
                    return {
                        "mode": "read",
                        "holder": lock_data.get("interface"),
                        "timestamp": lock_data.get("timestamp"),
                    }

                # Stale lock
                return {"mode": "write", "holder": None, "timestamp": None}

            except (json.JSONDecodeError, KeyError) as e:
                logger.warning("get_lock_state_failed", error=str(e))
                return {"mode": "write", "holder": None, "timestamp": None}

    @staticmethod
    def is_process_alive(pid: int) -> bool:
        """Check if process with given PID is running.

        Args:
            pid: Process ID

        Returns:
            True if process is running, False otherwise
        """
        if psutil is None:
            logger.warning("psutil_not_available", fallback="basic_check")
            # Fallback: Basic OS-level check
            try:
                os.kill(pid, 0)
                return True
            except (OSError, PermissionError):
                return False

        return bool(psutil.pid_exists(pid))

    def force_unlock(self) -> bool:
        """Force remove lock file (admin operation).

        Returns:
            True if unlocked, False if failed

        Raises:
            RuntimeError: If lock holder is still alive
        """
        with self._lock:
            if not self.lock_file.exists():
                logger.info("force_unlock_no_lock")
                return True

            try:
                lock_data = json.loads(self.lock_file.read_text(encoding="utf-8"))

                # Validate that process is actually dead
                if self.is_process_alive(lock_data["pid"]):
                    raise RuntimeError(
                        f"Cannot force unlock: Process {lock_data['pid']} "
                        f"({lock_data.get('interface', 'unknown')}) is still running. "
                        f"Terminate the process first."
                    )

                # Remove lock
                self.lock_file.unlink()
                logger.warning(
                    "force_unlock_successful",
                    pid=lock_data["pid"],
                    interface=lock_data.get("interface", "unknown"),
                )
                return True

            except RuntimeError:
                # Re-raise RuntimeError for live process
                raise

            except json.JSONDecodeError:
                # Corrupted lock file, safe to remove
                self.lock_file.unlink()
                logger.warning("force_unlock_corrupted_lock")
                return True

            except Exception as e:
                logger.error("force_unlock_failed", error=str(e))
                return False

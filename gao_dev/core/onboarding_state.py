"""Onboarding state persistence and recovery.

This module provides state management for onboarding wizards, allowing users
to resume interrupted onboarding sessions.

Epic 41: Streamlined Onboarding
Story 41.5: Onboarding State Persistence and Recovery

State is saved to ~/.gao-dev/onboarding_state.yaml after each step and can be
resumed if interrupted. State expires after 24 hours and must match the current
project path.

Security:
- Atomic file writes (write-to-temp-then-rename)
- User-only file permissions (600)
- Graceful handling of corrupted state
"""

import os
import platform
import stat
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import structlog
import yaml

logger = structlog.get_logger()


# All onboarding steps in order
ONBOARDING_STEPS = ["project", "git", "provider", "credentials"]


class OnboardingStateError(Exception):
    """Base exception for onboarding state errors."""

    pass


class StateCorruptedError(OnboardingStateError):
    """Raised when state file is corrupted or invalid."""

    def __init__(self, path: Path, reason: str):
        self.path = path
        self.reason = reason
        message = f"Onboarding state file corrupted at {path}: {reason}"
        super().__init__(message)


class StateExpiredError(OnboardingStateError):
    """Raised when state has expired."""

    def __init__(self, hours_old: float):
        self.hours_old = hours_old
        message = f"Onboarding state expired (was {hours_old:.1f} hours old)"
        super().__init__(message)


class ResumeInfo:
    """Information for displaying resume prompt to user.

    Attributes:
        steps_completed: List of completed step names
        next_step: Name of the next step to execute
        minutes_ago: How many minutes since last update
        is_expired: Whether state is older than expiry threshold
        project_path: Path to the project
    """

    def __init__(
        self,
        steps_completed: list[str],
        next_step: str,
        minutes_ago: int,
        is_expired: bool,
        project_path: Path,
    ):
        self.steps_completed = steps_completed
        self.next_step = next_step
        self.minutes_ago = minutes_ago
        self.is_expired = is_expired
        self.project_path = project_path

    def format_steps_completed(self) -> str:
        """Format completed steps for display.

        Returns:
            Comma-separated list of step names (capitalized)
        """
        if not self.steps_completed:
            return "None"
        return ", ".join(s.title() for s in self.steps_completed)

    def format_time_ago(self) -> str:
        """Format time since last update for display.

        Returns:
            Human-readable time string
        """
        if self.minutes_ago < 1:
            return "just now"
        elif self.minutes_ago < 60:
            return f"{self.minutes_ago} minute{'s' if self.minutes_ago != 1 else ''} ago"
        else:
            hours = self.minutes_ago // 60
            return f"{hours} hour{'s' if hours != 1 else ''} ago"


class OnboardingStateManager:
    """Persist onboarding progress for recovery after interruption.

    Manages onboarding state by:
    - Saving progress after each step
    - Detecting incomplete onboarding for resume
    - Checking expiry (24 hour threshold)
    - Providing resume information for prompts
    - Cleaning up after completion

    State is stored in YAML format with atomic writes and secure permissions.

    Attributes:
        state_file: Path to the state file
        expiry_hours: Hours after which state expires (default 24)

    Example:
        ```python
        manager = OnboardingStateManager()

        # Start new onboarding
        manager.start_onboarding(project_path)

        # Save after each step
        manager.save_step("project", {"name": "my-app"})
        manager.save_step("git", {"name": "Alex"})

        # Later, check if can resume
        if manager.can_resume(project_path):
            info = manager.get_resume_info()
            # Show prompt to user
            next_step, data = manager.resume()

        # After completion
        manager.mark_complete()
        manager.clear()
        ```
    """

    STATE_FILE = "onboarding_state.yaml"
    STATE_VERSION = "1.0"
    EXPIRY_HOURS = 24

    def __init__(
        self,
        config_path: Optional[Path] = None,
        expiry_hours: int = 24,
    ):
        """Initialize OnboardingStateManager.

        Args:
            config_path: Path to config directory (defaults to ~/.gao-dev/)
            expiry_hours: Hours after which state expires (default 24)
        """
        if config_path:
            self._config_path = config_path
        else:
            self._config_path = Path.home() / ".gao-dev"

        self.state_file = self._config_path / self.STATE_FILE
        self.expiry_hours = expiry_hours
        self._logger = logger.bind(component="onboarding_state")

    def start_onboarding(self, project_path: Path) -> None:
        """Initialize a new onboarding session.

        Creates initial state with empty steps completed and timestamps.

        Args:
            project_path: Path to the project being set up
        """
        now = datetime.now(timezone.utc)
        state = {
            "version": self.STATE_VERSION,
            "completed": False,
            "project_path": str(project_path.resolve()),
            "steps_completed": [],
            "step_data": {},
            "started_at": now.isoformat(),
            "last_updated": now.isoformat(),
        }
        self._save_state(state)
        self._logger.info(
            "onboarding_started",
            project_path=str(project_path),
        )

    def save_step(self, step: str, data: dict) -> None:
        """Save progress after completing a step.

        Args:
            step: Step name (e.g., 'project', 'git', 'provider', 'credentials')
            data: Data collected during the step

        Raises:
            OnboardingStateError: If no onboarding is in progress
        """
        state = self._load_state()

        if state is None:
            raise OnboardingStateError("No onboarding in progress")

        # Add step if not already completed
        if step not in state.get("steps_completed", []):
            state.setdefault("steps_completed", []).append(step)

        # Store step data
        state.setdefault("step_data", {})[step] = data

        # Update timestamp
        state["last_updated"] = datetime.now(timezone.utc).isoformat()

        self._save_state(state)
        self._logger.info(
            "step_saved",
            step=step,
            total_completed=len(state["steps_completed"]),
        )

    def can_resume(self, project_path: Path) -> bool:
        """Check if there's valid incomplete onboarding to resume.

        Validates:
        - State file exists
        - Not already completed
        - Project path matches
        - Not expired (24 hours)

        Args:
            project_path: Current project path

        Returns:
            True if resume is possible, False otherwise
        """
        state = self._load_state()

        if state is None:
            return False

        # Check not completed
        if state.get("completed", False):
            self._logger.debug("cannot_resume", reason="already_completed")
            return False

        # Check same project
        state_path = state.get("project_path", "")
        current_path = str(project_path.resolve())
        if state_path != current_path:
            self._logger.debug(
                "cannot_resume",
                reason="path_mismatch",
                state_path=state_path,
                current_path=current_path,
            )
            return False

        # Check not expired (but still allow resume with warning)
        # Return True even if expired - caller should check is_expired() for warning
        return True

    def is_expired(self) -> bool:
        """Check if state is older than expiry threshold.

        Returns:
            True if state is older than expiry_hours
        """
        state = self._load_state()

        if state is None:
            return False

        last_updated_str = state.get("last_updated")
        if not last_updated_str:
            return True

        try:
            last_updated = datetime.fromisoformat(last_updated_str)
            # Ensure timezone awareness
            if last_updated.tzinfo is None:
                last_updated = last_updated.replace(tzinfo=timezone.utc)

            age = datetime.now(timezone.utc) - last_updated
            return age > timedelta(hours=self.expiry_hours)
        except (ValueError, TypeError):
            return True

    def get_hours_old(self) -> float:
        """Get how many hours old the state is.

        Returns:
            Hours since last update, or 0 if state doesn't exist
        """
        state = self._load_state()

        if state is None:
            return 0.0

        last_updated_str = state.get("last_updated")
        if not last_updated_str:
            return 0.0

        try:
            last_updated = datetime.fromisoformat(last_updated_str)
            if last_updated.tzinfo is None:
                last_updated = last_updated.replace(tzinfo=timezone.utc)

            age = datetime.now(timezone.utc) - last_updated
            return age.total_seconds() / 3600
        except (ValueError, TypeError):
            return 0.0

    def resume(self) -> tuple[str, dict]:
        """Get the next step and accumulated data for resume.

        Returns:
            Tuple of (next_step_name, accumulated_step_data)

        Raises:
            OnboardingStateError: If no state to resume
        """
        state = self._load_state()

        if state is None:
            raise OnboardingStateError("No onboarding state to resume")

        steps_completed = state.get("steps_completed", [])
        step_data = state.get("step_data", {})

        # Find next step
        next_step = self._get_next_step(steps_completed)

        self._logger.info(
            "resuming_onboarding",
            steps_completed=steps_completed,
            next_step=next_step,
        )

        return next_step, step_data

    def _get_next_step(self, steps_completed: list[str]) -> str:
        """Get the next step to execute.

        Args:
            steps_completed: List of already completed steps

        Returns:
            Name of the next step
        """
        for step in ONBOARDING_STEPS:
            if step not in steps_completed:
                return step

        # All steps complete
        return "complete"

    def get_resume_info(self) -> Optional[ResumeInfo]:
        """Get information for displaying resume prompt.

        Returns:
            ResumeInfo with formatted resume information, or None if no state
        """
        state = self._load_state()

        if state is None:
            return None

        steps_completed = state.get("steps_completed", [])
        next_step = self._get_next_step(steps_completed)

        # Calculate time ago
        last_updated_str = state.get("last_updated", "")
        minutes_ago = 0
        if last_updated_str:
            try:
                last_updated = datetime.fromisoformat(last_updated_str)
                if last_updated.tzinfo is None:
                    last_updated = last_updated.replace(tzinfo=timezone.utc)
                age = datetime.now(timezone.utc) - last_updated
                minutes_ago = int(age.total_seconds() / 60)
            except (ValueError, TypeError):
                pass

        project_path = Path(state.get("project_path", "."))

        return ResumeInfo(
            steps_completed=steps_completed,
            next_step=next_step,
            minutes_ago=minutes_ago,
            is_expired=self.is_expired(),
            project_path=project_path,
        )

    def mark_complete(self) -> None:
        """Mark the onboarding as successfully completed.

        Sets the completed flag to True.
        """
        state = self._load_state()

        if state is None:
            return

        state["completed"] = True
        state["last_updated"] = datetime.now(timezone.utc).isoformat()

        self._save_state(state)
        self._logger.info("onboarding_marked_complete")

    def clear(self) -> None:
        """Remove state file after completion.

        Deletes the state file. Safe to call if file doesn't exist.
        """
        if self.state_file.exists():
            try:
                self.state_file.unlink()
                self._logger.info(
                    "state_cleared",
                    path=str(self.state_file),
                )
            except OSError as e:
                self._logger.warning(
                    "state_clear_failed",
                    path=str(self.state_file),
                    error=str(e),
                )

    def exists(self) -> bool:
        """Check if state file exists.

        Returns:
            True if state file exists
        """
        return self.state_file.exists()

    def get_state(self) -> Optional[dict]:
        """Get raw state data.

        Returns:
            State dictionary or None if not found/invalid
        """
        return self._load_state()

    def _load_state(self) -> Optional[dict]:
        """Load state from file.

        Returns:
            State dict or None if file doesn't exist or is corrupted
        """
        if not self.state_file.exists():
            return None

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                self._logger.warning(
                    "invalid_state_format",
                    path=str(self.state_file),
                )
                return None

            return data

        except yaml.YAMLError as e:
            self._logger.warning(
                "state_yaml_error",
                path=str(self.state_file),
                error=str(e),
            )
            return None
        except OSError as e:
            self._logger.warning(
                "state_load_error",
                path=str(self.state_file),
                error=str(e),
            )
            return None

    def _save_state(self, state: dict) -> None:
        """Save state to file atomically with secure permissions.

        Uses write-to-temp-then-rename pattern to prevent partial writes.

        Args:
            state: State dictionary to save
        """
        # Ensure parent directory exists
        self._config_path.mkdir(parents=True, exist_ok=True)

        # Write to temp file first (atomic write pattern)
        # Use tempfile in same directory to ensure same filesystem for rename
        temp_fd, temp_path = tempfile.mkstemp(
            suffix=".tmp",
            prefix="onboarding_state_",
            dir=self._config_path,
        )

        try:
            # Write content
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                yaml.safe_dump(state, f, default_flow_style=False)

            # Rename atomically
            temp_path_obj = Path(temp_path)
            temp_path_obj.replace(self.state_file)

            # Set secure permissions (owner read/write only)
            self._set_secure_permissions()

            self._logger.debug(
                "state_saved",
                path=str(self.state_file),
            )

        except Exception as e:
            # Clean up temp file on error
            try:
                Path(temp_path).unlink()
            except OSError:
                pass

            self._logger.error(
                "state_save_failed",
                path=str(self.state_file),
                error=str(e),
            )
            raise OnboardingStateError(f"Failed to save state: {e}")

    def _set_secure_permissions(self) -> None:
        """Set secure file permissions (600) on state file.

        Only applies on non-Windows systems.
        """
        if platform.system() != "Windows":
            try:
                os.chmod(self.state_file, stat.S_IRUSR | stat.S_IWUSR)
            except OSError as e:
                self._logger.warning(
                    "permission_set_failed",
                    path=str(self.state_file),
                    error=str(e),
                )


def check_for_resume(
    project_path: Path,
    config_path: Optional[Path] = None,
) -> Optional[ResumeInfo]:
    """Convenience function to check if onboarding can be resumed.

    Args:
        project_path: Current project path
        config_path: Optional config path (defaults to ~/.gao-dev/)

    Returns:
        ResumeInfo if resume is available, None otherwise
    """
    manager = OnboardingStateManager(config_path)

    if manager.can_resume(project_path):
        return manager.get_resume_info()

    return None

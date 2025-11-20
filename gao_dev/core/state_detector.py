"""Detect global and project state for GAO-Dev onboarding.

This module detects:
- Global state: Whether user is first-time or returning (based on ~/.gao-dev/)
- Project state: Whether directory is empty, brownfield, or existing GAO-Dev project
"""

import os
import time
from enum import Enum
from pathlib import Path
from typing import Tuple, Optional

import structlog
import yaml

logger = structlog.get_logger()


class GlobalState(str, Enum):
    """Global user state types."""

    FIRST_TIME = "first_time"
    RETURNING = "returning"


class ProjectState(str, Enum):
    """Project directory state types."""

    EMPTY = "empty"
    BROWNFIELD = "brownfield"
    GAO_DEV_PROJECT = "gao_dev_project"


# Brownfield indicator files that suggest an existing codebase
BROWNFIELD_INDICATORS = frozenset(
    [
        "package.json",
        "requirements.txt",
        "Cargo.toml",
        "go.mod",
        "pom.xml",
        "build.gradle",
        "Makefile",
        "pyproject.toml",
        "setup.py",
        "Gemfile",
        "CMakeLists.txt",
        "README.md",
    ]
)

# Brownfield patterns for glob matching (e.g., *.csproj)
BROWNFIELD_PATTERNS = frozenset([".csproj"])


def _get_global_config_dir() -> Path:
    """Get the global GAO-Dev configuration directory.

    Returns:
        Path to ~/.gao-dev/
    """
    return Path.home() / ".gao-dev"


def _get_global_config_file() -> Path:
    """Get the global GAO-Dev configuration file.

    Returns:
        Path to ~/.gao-dev/config.yaml
    """
    return _get_global_config_dir() / "config.yaml"


def _is_valid_yaml_config(config_path: Path) -> bool:
    """Check if a YAML configuration file is valid.

    Args:
        config_path: Path to the configuration file.

    Returns:
        True if the file exists and contains valid YAML, False otherwise.
    """
    if not config_path.exists():
        return False

    try:
        content = config_path.read_text(encoding="utf-8")
        # Empty file is still valid YAML (returns None)
        yaml.safe_load(content)
        return True
    except (yaml.YAMLError, OSError, PermissionError) as e:
        logger.warning("invalid_config_file", path=str(config_path), error=str(e))
        return False


def detect_global_state() -> GlobalState:
    """Detect global user state (first-time vs returning).

    Detection logic:
    - FIRST_TIME: ~/.gao-dev/ directory does not exist
    - RETURNING: ~/.gao-dev/config.yaml exists and is valid YAML

    Returns:
        GlobalState indicating the detected state.
    """
    start_time = time.perf_counter()
    logger.debug("detecting_global_state")

    config_dir = _get_global_config_dir()
    config_file = _get_global_config_file()

    # Check if global config directory exists
    if not config_dir.exists():
        elapsed = (time.perf_counter() - start_time) * 1000
        logger.info(
            "global_state_detected",
            state=GlobalState.FIRST_TIME.value,
            elapsed_ms=round(elapsed, 2),
        )
        return GlobalState.FIRST_TIME

    # Check if config file exists and is valid
    if _is_valid_yaml_config(config_file):
        elapsed = (time.perf_counter() - start_time) * 1000
        logger.info(
            "global_state_detected",
            state=GlobalState.RETURNING.value,
            elapsed_ms=round(elapsed, 2),
        )
        return GlobalState.RETURNING

    # Directory exists but no valid config - treat as first time
    elapsed = (time.perf_counter() - start_time) * 1000
    logger.info(
        "global_state_detected",
        state=GlobalState.FIRST_TIME.value,
        reason="no_valid_config",
        elapsed_ms=round(elapsed, 2),
    )
    return GlobalState.FIRST_TIME


def _find_gao_dev_root(start_path: Path) -> Optional[Path]:
    """Search up directory tree for .gao-dev/ directory.

    Args:
        start_path: Directory to start searching from.

    Returns:
        Path to directory containing .gao-dev/, or None if not found.
    """
    current = start_path.resolve()

    # Search up to root
    while True:
        gao_dev_dir = current / ".gao-dev"
        if gao_dev_dir.is_dir():
            # Check if this is a real GAO-Dev project or just web server artifacts
            # If .gao-dev only contains session.token and/or session.lock, it's not a real project
            try:
                contents = set(entry.name for entry in os.scandir(gao_dev_dir))
                # Ignore web server artifacts
                web_artifacts = {"session.token", "session.lock"}
                non_artifact_files = contents - web_artifacts

                if non_artifact_files:
                    # Found real GAO-Dev files beyond web server artifacts
                    logger.debug("found_gao_dev_root", path=str(current), non_artifact_count=len(non_artifact_files))
                    return current
                else:
                    # Only web server artifacts, not a real GAO-Dev project
                    # Continue searching up the tree
                    logger.debug(
                        "skipping_web_artifact_only_gao_dev",
                        path=str(current),
                        artifacts=list(contents),
                    )
            except (OSError, PermissionError) as e:
                logger.warning("failed_to_check_gao_dev_contents", path=str(gao_dev_dir), error=str(e))
                # On error, assume it's a real project (safer default)
                return current

        parent = current.parent
        if parent == current:
            # Reached root
            break
        current = parent

    return None


def _has_brownfield_indicator(directory: Path) -> bool:
    """Check if directory contains brownfield indicator files.

    Uses os.scandir() for fast directory scanning.

    Args:
        directory: Directory to check.

    Returns:
        True if any brownfield indicator is found.
    """
    try:
        with os.scandir(directory) as entries:
            for entry in entries:
                # Skip hidden files
                if entry.name.startswith("."):
                    continue

                # Check exact matches
                if entry.name in BROWNFIELD_INDICATORS:
                    logger.debug("brownfield_indicator_found", file=entry.name)
                    return True

                # Check pattern matches (e.g., *.csproj)
                for pattern in BROWNFIELD_PATTERNS:
                    if entry.name.endswith(pattern):
                        logger.debug("brownfield_pattern_found", file=entry.name, pattern=pattern)
                        return True

    except (OSError, PermissionError) as e:
        logger.warning("directory_scan_error", path=str(directory), error=str(e))

    return False


def _is_directory_empty(directory: Path) -> bool:
    """Check if directory is empty (excluding hidden files).

    Uses os.scandir() for fast directory scanning.

    Args:
        directory: Directory to check.

    Returns:
        True if directory has no non-hidden files/directories.
    """
    try:
        with os.scandir(directory) as entries:
            for entry in entries:
                # Skip hidden files
                if entry.name.startswith("."):
                    continue
                # Found at least one non-hidden entry
                return False
    except (OSError, PermissionError) as e:
        logger.warning("directory_scan_error", path=str(directory), error=str(e))
        # On error, treat as not empty (safer default)
        return False

    return True


def detect_project_state(project_path: Optional[Path] = None) -> ProjectState:
    """Detect project directory state.

    Detection logic:
    - GAO_DEV_PROJECT: .gao-dev/ directory exists (searches up from project_path)
    - EMPTY: Directory has no files (excluding hidden)
    - BROWNFIELD: Directory has code files but no .gao-dev/

    Args:
        project_path: Directory to check. Defaults to current working directory.

    Returns:
        ProjectState indicating the detected state.
    """
    start_time = time.perf_counter()
    logger.debug("detecting_project_state", path=str(project_path) if project_path else "cwd")

    # Default to current working directory
    if project_path is None:
        project_path = Path.cwd()

    project_path = project_path.resolve()

    # Ensure path exists and is a directory
    if not project_path.exists():
        logger.warning("project_path_not_exists", path=str(project_path))
        elapsed = (time.perf_counter() - start_time) * 1000
        logger.info(
            "project_state_detected",
            state=ProjectState.EMPTY.value,
            reason="path_not_exists",
            elapsed_ms=round(elapsed, 2),
        )
        return ProjectState.EMPTY

    if not project_path.is_dir():
        logger.warning("project_path_not_directory", path=str(project_path))
        elapsed = (time.perf_counter() - start_time) * 1000
        logger.info(
            "project_state_detected",
            state=ProjectState.EMPTY.value,
            reason="not_directory",
            elapsed_ms=round(elapsed, 2),
        )
        return ProjectState.EMPTY

    # Check for .gao-dev/ directory (search up from current path)
    gao_dev_root = _find_gao_dev_root(project_path)
    if gao_dev_root is not None:
        elapsed = (time.perf_counter() - start_time) * 1000
        logger.info(
            "project_state_detected",
            state=ProjectState.GAO_DEV_PROJECT.value,
            gao_dev_root=str(gao_dev_root),
            elapsed_ms=round(elapsed, 2),
        )
        return ProjectState.GAO_DEV_PROJECT

    # Check if directory is empty (excluding hidden files)
    if _is_directory_empty(project_path):
        elapsed = (time.perf_counter() - start_time) * 1000
        logger.info(
            "project_state_detected",
            state=ProjectState.EMPTY.value,
            elapsed_ms=round(elapsed, 2),
        )
        return ProjectState.EMPTY

    # Check for brownfield indicators
    if _has_brownfield_indicator(project_path):
        elapsed = (time.perf_counter() - start_time) * 1000
        logger.info(
            "project_state_detected",
            state=ProjectState.BROWNFIELD.value,
            elapsed_ms=round(elapsed, 2),
        )
        return ProjectState.BROWNFIELD

    # Has files but no indicators - still brownfield (existing non-empty directory)
    elapsed = (time.perf_counter() - start_time) * 1000
    logger.info(
        "project_state_detected",
        state=ProjectState.BROWNFIELD.value,
        reason="non_empty_no_indicators",
        elapsed_ms=round(elapsed, 2),
    )
    return ProjectState.BROWNFIELD


def detect_states(project_path: Optional[Path] = None) -> Tuple[GlobalState, ProjectState]:
    """Detect both global and project states.

    Convenience function that returns both states in a single call.

    Args:
        project_path: Directory to check for project state.
                     Defaults to current working directory.

    Returns:
        Tuple of (GlobalState, ProjectState).
    """
    start_time = time.perf_counter()

    global_state = detect_global_state()
    project_state = detect_project_state(project_path)

    elapsed = (time.perf_counter() - start_time) * 1000
    logger.info(
        "states_detected",
        global_state=global_state.value,
        project_state=project_state.value,
        total_elapsed_ms=round(elapsed, 2),
    )

    return global_state, project_state


def get_gao_dev_root(project_path: Optional[Path] = None) -> Optional[Path]:
    """Get the root directory of a GAO-Dev project.

    Searches up the directory tree for .gao-dev/ directory.

    Args:
        project_path: Directory to start searching from.
                     Defaults to current working directory.

    Returns:
        Path to directory containing .gao-dev/, or None if not found.
    """
    if project_path is None:
        project_path = Path.cwd()

    return _find_gao_dev_root(project_path)

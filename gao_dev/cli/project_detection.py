"""
Project root detection utilities.

This module provides utilities for detecting the root directory of a
GAO-Dev managed project. It searches for marker files/directories that
indicate a project root.
"""

from pathlib import Path
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)


class GAODevSourceDirectoryError(Exception):
    """
    Raised when GAO-Dev is run from its source repository directory.

    This error prevents users from accidentally operating on GAO-Dev's
    repository instead of their project. Provides clear installation
    and usage instructions.
    """

    def __init__(self) -> None:
        """Initialize error with helpful message."""
        message = """[E001] Running from GAO-Dev Source Directory

GAO-Dev must be installed via pip and run from your project directory.

Installation:
  pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main

Usage:
  cd /path/to/your/project
  gao-dev start

Alternative:
  gao-dev start --project /path/to/your/project

Documentation: https://docs.gao-dev.com/errors/E001
Support: https://github.com/memyselfmike/gao-agile-dev/issues/new"""
        super().__init__(message)

# Marker files/directories that indicate a project root
PROJECT_MARKERS = [
    ".gao-dev",        # Primary marker: project-scoped GAO-Dev data
    ".sandbox.yaml",   # Secondary marker: sandbox project metadata
]

# Marker files that identify GAO-Dev source repository
SOURCE_REPO_MARKERS = [
    ".gaodev-source",                          # Explicit marker file
    "gao_dev/orchestrator/orchestrator.py",    # Core orchestrator file
    "docs/bmm-workflow-status.md",             # BMM workflow tracking document
]


def _is_gaodev_source_repo(path: Path) -> bool:
    """
    Check if a directory is the GAO-Dev source repository.

    This function checks for distinctive markers that identify GAO-Dev's
    source repository to prevent users from accidentally running commands
    in the wrong directory.

    Args:
        path: Directory to check

    Returns:
        True if directory appears to be GAO-Dev source repo, False otherwise

    Examples:
        >>> _is_gaodev_source_repo(Path("/path/to/gao-agile-dev"))
        True
        >>> _is_gaodev_source_repo(Path("/path/to/user/project"))
        False
    """
    try:
        # Check for any of the source repo markers
        for marker in SOURCE_REPO_MARKERS:
            marker_path = path / marker
            try:
                if marker_path.exists():
                    logger.debug(
                        "Detected GAO-Dev source repository",
                        path=str(path),
                        marker=marker
                    )
                    return True
            except (OSError, PermissionError) as e:
                logger.debug(
                    "Error checking source marker",
                    path=str(marker_path),
                    error=str(e)
                )
                continue

        return False
    except Exception as e:
        logger.debug(
            "Error in source repo detection",
            path=str(path),
            error=str(e)
        )
        return False


def detect_project_root(start_dir: Optional[Path] = None) -> Path:
    """
    Detect the root directory of a GAO-Dev project.

    Searches for project markers (`.gao-dev/` or `.sandbox.yaml`) by
    walking up the directory tree from the starting directory. If no
    markers are found, returns the starting directory as a fallback.

    The search prioritizes `.gao-dev/` over `.sandbox.yaml` if both
    exist at different levels.

    Args:
        start_dir: Directory to start search from (defaults to current directory)

    Returns:
        Path to project root directory

    Raises:
        GAODevSourceDirectoryError: If run from GAO-Dev source repository

    Examples:
        >>> # From within a project
        >>> root = detect_project_root()
        >>> assert (root / ".gao-dev").exists()

        >>> # From a subdirectory
        >>> root = detect_project_root(Path("sandbox/projects/myapp/src/components"))
        >>> assert root.name == "myapp"

        >>> # No markers found
        >>> root = detect_project_root(Path("/tmp"))
        >>> assert root == Path("/tmp")  # Fallback to start_dir

    Note:
        This function raises GAODevSourceDirectoryError if run from
        GAO-Dev's source repository. Otherwise, if detection fails or
        markers are not found, it returns the starting directory as
        a safe fallback.
    """
    start_dir = start_dir or Path.cwd()

    logger.debug(
        "Detecting project root",
        start_dir=str(start_dir),
        markers=PROJECT_MARKERS
    )

    # Normalize path
    try:
        current = start_dir.resolve()
    except (OSError, RuntimeError) as e:
        logger.warning(
            "Failed to resolve path, using as-is",
            path=str(start_dir),
            error=str(e)
        )
        current = start_dir

    # CRITICAL: Check if we're in GAO-Dev source repo (check current and all parents)
    # This prevents users from accidentally operating on GAO-Dev's repository
    searched_dirs = []
    for parent in [current, *current.parents]:
        if _is_gaodev_source_repo(parent):
            logger.error(
                "Detected GAO-Dev source directory - refusing to proceed",
                directory=str(parent),
                start_dir=str(start_dir)
            )
            raise GAODevSourceDirectoryError()

    # Search up directory tree for project markers
    for parent in [current, *current.parents]:
        searched_dirs.append(str(parent))

        # Check for markers (in priority order)
        for marker in PROJECT_MARKERS:
            marker_path = parent / marker
            try:
                if marker_path.exists():
                    logger.info(
                        "Project root detected",
                        project_root=str(parent),
                        marker=marker,
                        start_dir=str(start_dir)
                    )
                    return parent
            except (OSError, PermissionError) as e:
                logger.debug(
                    "Error checking marker",
                    path=str(marker_path),
                    error=str(e)
                )
                continue

    # No markers found, use start directory as fallback
    logger.debug(
        "No project markers found, using start directory",
        start_dir=str(start_dir),
        searched=searched_dirs
    )

    return start_dir


def is_project_root(directory: Path) -> bool:
    """
    Check if a directory is a project root.

    Args:
        directory: Directory to check

    Returns:
        True if directory contains project markers

    Examples:
        >>> is_project_root(Path("sandbox/projects/myapp"))
        True
        >>> is_project_root(Path("sandbox/projects/myapp/src"))
        False
    """
    for marker in PROJECT_MARKERS:
        marker_path = directory / marker
        try:
            if marker_path.exists():
                return True
        except (OSError, PermissionError):
            continue

    return False


def find_all_projects(search_dir: Path, max_depth: int = 3) -> list[Path]:
    """
    Find all GAO-Dev projects within a directory.

    Searches for directories containing project markers up to a
    specified depth. Useful for discovering all projects in a
    workspace or sandbox directory.

    Args:
        search_dir: Directory to search in
        max_depth: Maximum depth to search (default: 3)

    Returns:
        List of project root directories

    Examples:
        >>> projects = find_all_projects(Path("sandbox/projects"))
        >>> for project in projects:
        ...     print(f"Found project: {project.name}")

    Note:
        This function stops searching deeper once a project root is
        found (doesn't look for nested projects).
    """
    projects = []

    def _search(directory: Path, depth: int) -> None:
        """Recursive search helper."""
        if depth > max_depth:
            return

        # Check if this is a project root
        if is_project_root(directory):
            projects.append(directory)
            return  # Don't search nested projects

        # Search subdirectories
        try:
            for child in directory.iterdir():
                if child.is_dir() and not child.name.startswith("."):
                    _search(child, depth + 1)
        except (OSError, PermissionError) as e:
            logger.debug(
                "Error searching directory",
                directory=str(directory),
                error=str(e)
            )

    _search(search_dir, 0)

    logger.debug(
        "Project search complete",
        search_dir=str(search_dir),
        found_count=len(projects)
    )

    return projects


def get_project_name(project_root: Path) -> str:
    """
    Get the project name from the project root.

    Args:
        project_root: Project root directory

    Returns:
        Project name (directory name)

    Examples:
        >>> root = Path("sandbox/projects/my-todo-app")
        >>> get_project_name(root)
        'my-todo-app'
    """
    return project_root.name

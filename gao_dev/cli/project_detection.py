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

# Marker files/directories that indicate a project root
PROJECT_MARKERS = [
    ".gao-dev",        # Primary marker: project-scoped GAO-Dev data
    ".sandbox.yaml",   # Secondary marker: sandbox project metadata
]


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
        This function never raises exceptions. If detection fails or
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

    # Search up directory tree
    searched_dirs = []
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

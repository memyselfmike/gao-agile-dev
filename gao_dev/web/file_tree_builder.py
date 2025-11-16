"""File tree builder for GAO-Dev web interface.

Builds hierarchical file tree structure from project files,
respecting .gitignore and showing only tracked directories.

Epic: 39.4 - File Management
Story: 39.11 - File Tree Navigation Component
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import structlog
from datetime import datetime, timedelta

logger = structlog.get_logger(__name__)

# Tracked directories (only these are shown in file tree)
TRACKED_DIRECTORIES = {"docs", "src", "gao_dev", "tests"}

# File type icons mapping (for frontend)
FILE_ICONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "react",
    ".jsx": "react",
    ".md": "markdown",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".txt": "text",
    ".html": "html",
    ".css": "css",
    ".sh": "shell",
    ".xml": "xml",
}


def parse_gitignore(project_root: Path) -> List[str]:
    """Parse .gitignore file and return list of patterns.

    Args:
        project_root: Root directory of project

    Returns:
        List of gitignore patterns
    """
    gitignore_path = project_root / ".gitignore"
    patterns = []

    if gitignore_path.exists():
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        patterns.append(line)
        except Exception as e:
            logger.warning("failed_to_parse_gitignore", error=str(e))

    return patterns


def should_ignore(path: Path, project_root: Path, gitignore_patterns: List[str]) -> bool:
    """Check if path should be ignored based on .gitignore patterns.

    Args:
        path: Path to check
        project_root: Root directory of project
        gitignore_patterns: List of gitignore patterns

    Returns:
        True if path should be ignored, False otherwise
    """
    # Always ignore hidden files/directories (starting with .)
    if any(part.startswith('.') for part in path.parts):
        return True

    # Get relative path from project root
    try:
        rel_path = path.relative_to(project_root)
    except ValueError:
        return True

    # Check against gitignore patterns (basic matching)
    rel_path_str = str(rel_path).replace('\\', '/')

    for pattern in gitignore_patterns:
        # Simple pattern matching (not full gitignore spec)
        # Directories end with /
        if pattern.endswith('/'):
            if rel_path_str.startswith(pattern.rstrip('/')):
                return True
        # Wildcard patterns
        elif '*' in pattern:
            # Simple wildcard matching (not comprehensive)
            import fnmatch
            if fnmatch.fnmatch(rel_path_str, pattern):
                return True
        # Exact match or prefix match
        elif rel_path_str == pattern or rel_path_str.startswith(pattern + '/'):
            return True

    return False


def get_file_icon(file_path: Path) -> str:
    """Get icon type for file based on extension.

    Args:
        file_path: Path to file

    Returns:
        Icon type string
    """
    suffix = file_path.suffix.lower()
    return FILE_ICONS.get(suffix, "file")


def build_file_tree(
    project_root: Path,
    recently_changed_cutoff: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """Build hierarchical file tree structure.

    Only includes tracked directories (docs/, src/, gao_dev/, tests/).
    Respects .gitignore patterns.

    Args:
        project_root: Root directory of project
        recently_changed_cutoff: Datetime cutoff for recently changed files
                                (default: 5 minutes ago)

    Returns:
        List of file tree nodes in hierarchical structure
    """
    if recently_changed_cutoff is None:
        recently_changed_cutoff = datetime.now() - timedelta(minutes=5)

    # Parse gitignore
    gitignore_patterns = parse_gitignore(project_root)

    # Build tree structure
    tree: List[Dict[str, Any]] = []

    for tracked_dir in sorted(TRACKED_DIRECTORIES):
        dir_path = project_root / tracked_dir

        if not dir_path.exists():
            continue

        # Build directory node
        dir_node = _build_directory_node(
            dir_path,
            project_root,
            gitignore_patterns,
            recently_changed_cutoff
        )

        if dir_node:
            tree.append(dir_node)

    logger.info(
        "file_tree_built",
        total_nodes=len(tree),
        tracked_dirs=list(TRACKED_DIRECTORIES)
    )

    return tree


def _build_directory_node(
    dir_path: Path,
    project_root: Path,
    gitignore_patterns: List[str],
    recently_changed_cutoff: datetime
) -> Optional[Dict[str, Any]]:
    """Build a directory node with children.

    Args:
        dir_path: Path to directory
        project_root: Root directory of project
        gitignore_patterns: List of gitignore patterns
        recently_changed_cutoff: Datetime cutoff for recently changed files

    Returns:
        Directory node dictionary or None if empty/ignored
    """
    # Check if should be ignored
    if should_ignore(dir_path, project_root, gitignore_patterns):
        return None

    # Get relative path
    try:
        rel_path = dir_path.relative_to(project_root)
    except ValueError:
        return None

    # Build children
    children: List[Dict[str, Any]] = []

    try:
        # Sort: directories first, then files (alphabetically)
        entries = sorted(
            dir_path.iterdir(),
            key=lambda p: (not p.is_dir(), p.name.lower())
        )

        for entry in entries:
            if should_ignore(entry, project_root, gitignore_patterns):
                continue

            if entry.is_dir():
                child_node = _build_directory_node(
                    entry,
                    project_root,
                    gitignore_patterns,
                    recently_changed_cutoff
                )
                if child_node:
                    children.append(child_node)

            elif entry.is_file():
                child_node = _build_file_node(
                    entry,
                    project_root,
                    recently_changed_cutoff
                )
                if child_node:
                    children.append(child_node)

    except PermissionError:
        logger.warning("permission_denied_reading_directory", path=str(dir_path))
        return None

    # Only return node if it has children
    if not children:
        return None

    return {
        "path": str(rel_path).replace('\\', '/'),
        "name": dir_path.name,
        "type": "directory",
        "children": children
    }


def _build_file_node(
    file_path: Path,
    project_root: Path,
    recently_changed_cutoff: datetime
) -> Optional[Dict[str, Any]]:
    """Build a file node.

    Args:
        file_path: Path to file
        project_root: Root directory of project
        recently_changed_cutoff: Datetime cutoff for recently changed files

    Returns:
        File node dictionary or None if invalid
    """
    try:
        rel_path = file_path.relative_to(project_root)
    except ValueError:
        return None

    # Get file metadata
    try:
        stat = file_path.stat()
        modified_time = datetime.fromtimestamp(stat.st_mtime)
        size = stat.st_size
        recently_changed = modified_time >= recently_changed_cutoff
    except (OSError, ValueError):
        modified_time = datetime.now()
        size = 0
        recently_changed = False

    return {
        "path": str(rel_path).replace('\\', '/'),
        "name": file_path.name,
        "type": "file",
        "icon": get_file_icon(file_path),
        "size": size,
        "modified": modified_time.isoformat(),
        "recentlyChanged": recently_changed
    }

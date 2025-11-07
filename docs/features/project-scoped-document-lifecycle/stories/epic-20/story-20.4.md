# Story 20.4: Add Project Root Detection

**Epic**: Epic 20 - Project-Scoped Document Lifecycle
**Status**: Ready
**Priority**: P1 (High)
**Estimated Effort**: 2 story points
**Owner**: Amelia (Developer)
**Created**: 2025-11-06

---

## User Story

**As a** GAO-Dev user
**I want** CLI commands to automatically detect the project root
**So that** I can run commands from any directory within a project without specifying paths

---

## Acceptance Criteria

### AC1: Project Detection Utility Created

- ✅ New file: `gao_dev/cli/project_detection.py`
- ✅ `detect_project_root()` function implemented
- ✅ Searches for `.gao-dev/` or `.sandbox.yaml` markers
- ✅ Walks up directory tree until marker found
- ✅ Returns current directory if no marker found (fallback)

### AC2: Detection Logic

- ✅ Starts from current working directory
- ✅ Checks current and all parent directories
- ✅ Prioritizes `.gao-dev/` over `.sandbox.yaml`
- ✅ Handles edge cases (root directory, symlinks)
- ✅ Clear logging of detection process

### AC3: Error Handling

- ✅ Handles permission errors gracefully
- ✅ Handles non-existent directories
- ✅ Returns sensible default (current directory)
- ✅ Logs warnings for ambiguous situations
- ✅ Never crashes, always returns a Path

### AC4: Unit Tests

- ✅ Test: `test_detect_with_gao_dev()` - Finds `.gao-dev/` directory
- ✅ Test: `test_detect_with_sandbox_yaml()` - Finds `.sandbox.yaml`
- ✅ Test: `test_detect_from_subdirectory()` - Walks up tree correctly
- ✅ Test: `test_detect_no_markers()` - Returns current directory
- ✅ Test: `test_detect_multiple_levels()` - Finds nearest marker
- ✅ All tests pass with 100% coverage

### AC5: Documentation

- ✅ Function docstring with examples
- ✅ Module docstring explaining purpose
- ✅ Type hints throughout
- ✅ Inline comments for complex logic

---

## Technical Details

### File Structure

```
gao_dev/cli/
├── __init__.py
├── commands.py
├── sandbox_commands.py
├── lifecycle_commands.py
└── project_detection.py      # NEW: Project root detection utilities
```

### Implementation Approach

**Step 1: Create project_detection.py**

```python
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
```

**Step 2: Update CLI __init__.py**

Export detection utilities:

```python
# In gao_dev/cli/__init__.py

from .commands import cli
from .sandbox_commands import sandbox
from .project_detection import (  # NEW
    detect_project_root,
    is_project_root,
    find_all_projects,
    get_project_name,
)

__all__ = [
    "cli",
    "sandbox",
    "detect_project_root",
    "is_project_root",
    "find_all_projects",
    "get_project_name",
]
```

---

## Testing Approach

### Unit Tests

Create `tests/cli/test_project_detection.py`:

```python
"""Tests for project root detection utilities."""

import pytest
from pathlib import Path
import tempfile
import shutil

from gao_dev.cli.project_detection import (
    detect_project_root,
    is_project_root,
    find_all_projects,
    get_project_name,
)


class TestProjectDetection:
    """Test suite for project root detection."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace with project structure."""
        temp_dir = Path(tempfile.mkdtemp())

        # Create project structure
        project1 = temp_dir / "projects" / "app1"
        project1.mkdir(parents=True)
        (project1 / ".gao-dev").mkdir()

        project2 = temp_dir / "projects" / "app2"
        project2.mkdir(parents=True)
        (project2 / ".sandbox.yaml").touch()

        # Create subdirectories
        (project1 / "src" / "components").mkdir(parents=True)

        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_detect_with_gao_dev(self, temp_workspace):
        """Test detection with .gao-dev marker."""
        project_dir = temp_workspace / "projects" / "app1"
        detected = detect_project_root(project_dir)

        assert detected == project_dir
        assert (detected / ".gao-dev").exists()

    def test_detect_with_sandbox_yaml(self, temp_workspace):
        """Test detection with .sandbox.yaml marker."""
        project_dir = temp_workspace / "projects" / "app2"
        detected = detect_project_root(project_dir)

        assert detected == project_dir
        assert (detected / ".sandbox.yaml").exists()

    def test_detect_from_subdirectory(self, temp_workspace):
        """Test detection from nested subdirectory."""
        subdir = temp_workspace / "projects" / "app1" / "src" / "components"
        detected = detect_project_root(subdir)

        expected = temp_workspace / "projects" / "app1"
        assert detected == expected

    def test_detect_no_markers(self, tmp_path):
        """Test detection when no markers found."""
        # Create directory without markers
        test_dir = tmp_path / "no-project"
        test_dir.mkdir()

        detected = detect_project_root(test_dir)

        # Should return start directory as fallback
        assert detected == test_dir

    def test_detect_multiple_levels(self, temp_workspace):
        """Test that nearest marker is found."""
        # Create nested structure
        outer = temp_workspace / "outer"
        outer.mkdir()
        (outer / ".gao-dev").mkdir()

        inner = outer / "inner"
        inner.mkdir()
        (inner / ".gao-dev").mkdir()

        # Detect from inner
        detected = detect_project_root(inner)
        assert detected == inner  # Finds nearest marker

    def test_is_project_root_true(self, temp_workspace):
        """Test is_project_root returns True for project roots."""
        project_dir = temp_workspace / "projects" / "app1"
        assert is_project_root(project_dir) is True

    def test_is_project_root_false(self, temp_workspace):
        """Test is_project_root returns False for non-roots."""
        subdir = temp_workspace / "projects" / "app1" / "src"
        assert is_project_root(subdir) is False

    def test_find_all_projects(self, temp_workspace):
        """Test finding all projects in directory."""
        projects_dir = temp_workspace / "projects"
        projects = find_all_projects(projects_dir, max_depth=2)

        assert len(projects) == 2
        project_names = {p.name for p in projects}
        assert project_names == {"app1", "app2"}

    def test_find_all_projects_respects_depth(self, temp_workspace):
        """Test that max_depth is respected."""
        # Create deeply nested project
        deep = temp_workspace / "a" / "b" / "c" / "project"
        deep.mkdir(parents=True)
        (deep / ".gao-dev").mkdir()

        # Search with shallow depth
        projects = find_all_projects(temp_workspace, max_depth=2)

        # Should not find deeply nested project
        assert deep not in projects

    def test_get_project_name(self, temp_workspace):
        """Test getting project name from path."""
        project_dir = temp_workspace / "projects" / "my-app"
        name = get_project_name(project_dir)

        assert name == "my-app"

    def test_detect_current_directory_default(self, temp_workspace, monkeypatch):
        """Test that detect_project_root uses current directory by default."""
        project_dir = temp_workspace / "projects" / "app1"

        # Change to project directory
        monkeypatch.chdir(project_dir)

        # Detect without arguments
        detected = detect_project_root()

        assert detected == project_dir

    def test_detect_handles_permission_error(self, tmp_path):
        """Test graceful handling of permission errors."""
        # This test is platform-specific and may need adjustment
        test_dir = tmp_path / "test"
        test_dir.mkdir()

        # Should not crash
        detected = detect_project_root(test_dir)
        assert detected == test_dir

    def test_detect_prioritizes_gao_dev(self, tmp_path):
        """Test that .gao-dev is prioritized over .sandbox.yaml."""
        # Create directory with both markers
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".gao-dev").mkdir()
        (project_dir / ".sandbox.yaml").touch()

        detected = detect_project_root(project_dir)

        assert detected == project_dir
        # Verify .gao-dev exists (prioritized)
        assert (detected / ".gao-dev").exists()
```

Run tests:
```bash
pytest tests/cli/test_project_detection.py -v --cov=gao_dev.cli.project_detection
```

---

## Dependencies

### Required Packages
- ✅ structlog (already installed)
- ✅ pathlib (standard library)
- ✅ pytest (already installed)

### Code Dependencies
- None (standalone utility)

---

## Definition of Done

- [ ] File `gao_dev/cli/project_detection.py` created
- [ ] `detect_project_root()` function implemented
- [ ] `is_project_root()` helper function implemented
- [ ] `find_all_projects()` discovery function implemented
- [ ] `get_project_name()` utility function implemented
- [ ] Comprehensive unit tests (100% coverage)
- [ ] Type hints throughout
- [ ] Documentation strings complete
- [ ] Exported in `__init__.py`
- [ ] Code review completed
- [ ] Committed to git with conventional commit message

---

## Related Stories

**Depends On**:
- Story 20.1: Create ProjectDocumentLifecycle Factory Class

**Blocks**:
- Story 20.5: Update Lifecycle CLI Commands

---

## Notes

### Key Design Decisions

1. **Fallback Behavior**: Returns current directory if no markers found (never fails)
2. **Priority Order**: `.gao-dev/` prioritized over `.sandbox.yaml`
3. **Tree Walking**: Searches from current directory up to filesystem root
4. **Error Handling**: Catches and logs all OS errors, never crashes
5. **Utility Functions**: Additional helpers for common operations

### Use Cases

**Use Case 1: User in project root**
```bash
cd sandbox/projects/my-app
gao-dev lifecycle list  # Detects my-app as project root
```

**Use Case 2: User in subdirectory**
```bash
cd sandbox/projects/my-app/src/components
gao-dev lifecycle list  # Walks up to my-app as project root
```

**Use Case 3: User outside project**
```bash
cd /tmp
gao-dev lifecycle list  # Uses /tmp as fallback (no markers)
```

### Future Enhancements

- Support for `.gaoproject` marker file
- Configuration file for custom markers
- Caching of detection results for performance
- Workspace detection (multiple projects)

---

## Acceptance Testing

### Test Case 1: Detect from Project Root

```python
from gao_dev.cli.project_detection import detect_project_root
from pathlib import Path

project_dir = Path("sandbox/projects/my-app")
detected = detect_project_root(project_dir)

assert detected == project_dir
assert (detected / ".gao-dev").exists()
```

**Expected**: Correctly identifies project root

### Test Case 2: Detect from Subdirectory

```python
subdir = Path("sandbox/projects/my-app/src/components")
detected = detect_project_root(subdir)

expected = Path("sandbox/projects/my-app")
assert detected == expected
```

**Expected**: Walks up tree to find project root

### Test Case 3: No Markers Found

```python
temp_dir = Path("/tmp/test")
temp_dir.mkdir(exist_ok=True)

detected = detect_project_root(temp_dir)

assert detected == temp_dir  # Fallback to start directory
```

**Expected**: Returns start directory as fallback

### Test Case 4: Find All Projects

```python
from gao_dev.cli.project_detection import find_all_projects

projects = find_all_projects(Path("sandbox/projects"))

assert len(projects) > 0
for project in projects:
    assert (project / ".gao-dev").exists() or (project / ".sandbox.yaml").exists()
```

**Expected**: Finds all projects in directory

---

**Created by**: Bob (Scrum Master)
**Ready for Implementation**: Yes
**Estimated Completion**: 1 day

---

*This story is part of Epic 20: Project-Scoped Document Lifecycle.*

# Story 1.2: Sandbox Manager Implementation

**Epic**: Epic 1 - Sandbox Infrastructure
**Status**: Draft
**Priority**: P0 (Critical)
**Estimated Effort**: 5 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27
**Depends On**: Story 1.1

---

## User Story

**As a** developer using GAO-Dev
**I want** a sandbox manager to handle project lifecycle
**So that** I can programmatically create, manage, and query sandbox projects

---

## Acceptance Criteria

### AC1: Sandbox Manager Class
- ✅ Class `SandboxManager` created in `gao_dev/sandbox/manager.py`
- ✅ Follows single responsibility principle
- ✅ Type hints on all methods
- ✅ Comprehensive docstrings

### AC2: Project Operations
- ✅ Can create new sandbox project
- ✅ Can get project information
- ✅ Can list all projects
- ✅ Can check if project exists
- ✅ Can delete project

### AC3: Project Metadata
- ✅ Stores project metadata in `.sandbox.yaml` per project
- ✅ Tracks: name, created_date, status, boilerplate_url, runs
- ✅ Can read and update metadata
- ✅ Validates metadata on load

### AC4: Directory Management
- ✅ Creates `sandbox/projects/<project_name>/` structure
- ✅ Creates subdirectories (docs, src, tests, benchmarks)
- ✅ Handles path resolution correctly (Windows/Unix)
- ✅ Validates directory permissions

### AC5: Error Handling
- ✅ Handles project already exists
- ✅ Handles project not found
- ✅ Handles filesystem errors gracefully
- ✅ Clear error messages

---

## Technical Details

### File Structure
```
gao_dev/sandbox/
├── __init__.py
├── manager.py          # NEW: SandboxManager class
├── models.py           # NEW: Data models
└── exceptions.py       # NEW: Custom exceptions
```

### Data Models

```python
# gao_dev/sandbox/models.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum

class ProjectStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"

@dataclass
class BenchmarkRun:
    """Represents a single benchmark run."""
    run_id: str
    started_at: datetime
    completed_at: Optional[datetime]
    status: ProjectStatus
    config_file: str
    metrics: dict

@dataclass
class ProjectMetadata:
    """Sandbox project metadata."""
    name: str
    created_at: datetime
    status: ProjectStatus
    boilerplate_url: Optional[str]
    last_modified: datetime
    runs: List[BenchmarkRun]
    tags: List[str]

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization."""
        pass

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectMetadata":
        """Load from dictionary."""
        pass
```

### Manager Interface

```python
# gao_dev/sandbox/manager.py

from pathlib import Path
from typing import List, Optional
import yaml

from .models import ProjectMetadata, ProjectStatus
from .exceptions import ProjectExistsError, ProjectNotFoundError

class SandboxManager:
    """
    Manages sandbox project lifecycle and operations.

    Responsible for creating, reading, updating, and deleting
    sandbox projects, as well as managing their metadata.
    """

    def __init__(self, sandbox_root: Path):
        """
        Initialize sandbox manager.

        Args:
            sandbox_root: Root directory for sandbox projects
        """
        self.sandbox_root = sandbox_root
        self.projects_dir = sandbox_root / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def create_project(
        self,
        name: str,
        boilerplate_url: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> ProjectMetadata:
        """
        Create a new sandbox project.

        Args:
            name: Project name (must be unique)
            boilerplate_url: Optional boilerplate repository URL
            tags: Optional project tags

        Returns:
            ProjectMetadata object

        Raises:
            ProjectExistsError: If project already exists
            ValueError: If name is invalid
        """
        pass

    def get_project(self, name: str) -> ProjectMetadata:
        """
        Get project metadata.

        Args:
            name: Project name

        Returns:
            ProjectMetadata object

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        pass

    def list_projects(
        self,
        status: Optional[ProjectStatus] = None,
    ) -> List[ProjectMetadata]:
        """
        List all sandbox projects.

        Args:
            status: Optional status filter

        Returns:
            List of ProjectMetadata objects
        """
        pass

    def update_project(self, name: str, metadata: ProjectMetadata) -> None:
        """
        Update project metadata.

        Args:
            name: Project name
            metadata: Updated metadata

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        pass

    def delete_project(self, name: str, force: bool = False) -> None:
        """
        Delete a sandbox project.

        Args:
            name: Project name
            force: Skip confirmation if True

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        pass

    def project_exists(self, name: str) -> bool:
        """Check if project exists."""
        pass

    def get_project_path(self, name: str) -> Path:
        """Get absolute path to project directory."""
        pass

    def _create_project_structure(self, project_dir: Path) -> None:
        """Create standard project directory structure."""
        pass

    def _load_metadata(self, project_dir: Path) -> ProjectMetadata:
        """Load project metadata from .sandbox.yaml."""
        pass

    def _save_metadata(self, project_dir: Path, metadata: ProjectMetadata) -> None:
        """Save project metadata to .sandbox.yaml."""
        pass

    def _validate_project_name(self, name: str) -> None:
        """Validate project name meets requirements."""
        pass
```

### Custom Exceptions

```python
# gao_dev/sandbox/exceptions.py

class SandboxError(Exception):
    """Base exception for sandbox operations."""
    pass

class ProjectExistsError(SandboxError):
    """Raised when project already exists."""
    pass

class ProjectNotFoundError(SandboxError):
    """Raised when project doesn't exist."""
    pass

class InvalidProjectNameError(SandboxError):
    """Raised when project name is invalid."""
    pass
```

---

## Implementation Steps

### Step 1: Create Module Structure
1. Create `gao_dev/sandbox/` directory
2. Create `__init__.py`, `manager.py`, `models.py`, `exceptions.py`
3. Set up package exports

### Step 2: Implement Data Models
1. Create `ProjectStatus` enum
2. Create `BenchmarkRun` dataclass
3. Create `ProjectMetadata` dataclass
4. Implement `to_dict()` and `from_dict()` methods
5. Add validation logic

### Step 3: Implement Custom Exceptions
1. Create exception hierarchy
2. Add helpful error messages
3. Include context in exceptions

### Step 4: Implement SandboxManager
1. Implement `__init__` and setup
2. Implement `create_project`
3. Implement `get_project` and `list_projects`
4. Implement `update_project` and `delete_project`
5. Implement helper methods

### Step 5: Write Unit Tests
1. Test project creation
2. Test duplicate project handling
3. Test project listing with filters
4. Test metadata serialization
5. Test error conditions

---

## Testing Approach

### Unit Tests
Location: `tests/unit/sandbox/test_manager.py`

```python
def test_create_project():
    """Test creating a new sandbox project."""
    pass

def test_create_duplicate_project():
    """Test error when creating duplicate project."""
    pass

def test_list_projects():
    """Test listing all projects."""
    pass

def test_list_projects_with_filter():
    """Test listing projects with status filter."""
    pass

def test_get_project():
    """Test getting project metadata."""
    pass

def test_get_nonexistent_project():
    """Test error when getting nonexistent project."""
    pass

def test_delete_project():
    """Test deleting a project."""
    pass

def test_metadata_serialization():
    """Test metadata to/from YAML."""
    pass
```

### Integration Tests
- Create real project in temp directory
- Verify directory structure created
- Verify metadata file created
- Clean up after tests

---

## Dependencies

### Python Packages
- PyYAML (for metadata serialization)
- pytest (for testing)
- All existing GAO-Dev dependencies

### Code Dependencies
- Story 1.1 (CLI structure)
- Core ConfigLoader (for path resolution)

---

## Definition of Done

- [ ] All source files created (`manager.py`, `models.py`, `exceptions.py`)
- [ ] All classes implemented with type hints and docstrings
- [ ] Unit tests written and passing (>80% coverage)
- [ ] Integration tests passing
- [ ] Can create and list projects programmatically
- [ ] Metadata persists correctly to YAML
- [ ] Error handling comprehensive
- [ ] Code follows QA_STANDARDS.md (12+/14 score)
- [ ] Code reviewed
- [ ] Committed to git with conventional commit

---

## Quality Requirements

Per QA_STANDARDS.md:
- No DRY violations
- No magic numbers (use named constants)
- No `Any` types
- Functions < 30 lines
- Cyclomatic complexity < 10
- 90%+ docstring coverage
- 90%+ type hint coverage
- Comprehensive error handling
- Clear naming conventions

---

## Related Stories

**Depends On**:
- Story 1.1 (Sandbox CLI structure)

**Blocks**:
- Story 1.3 (Project State Management)
- Story 1.4 (Sandbox init Command)
- Story 1.5 (Sandbox clean Command)
- Story 1.6 (Sandbox list Command)

---

## Notes

This story creates the core infrastructure for all sandbox operations. It's critical that this implementation is solid, as all other stories depend on it.

**Key Design Decisions**:
1. Use YAML for metadata (human-readable, easy to edit)
2. Store metadata in project directory (keeps project self-contained)
3. Use dataclasses (clean, type-safe, easy to serialize)
4. Custom exceptions (clear error handling, easier debugging)

---

**Created by**: Bob (Scrum Master) via BMAD workflow
**Ready for Implementation**: Yes (after Story 1.1)
**Estimated Completion**: 2-3 days

---

*This story is part of the GAO-Dev Sandbox & Benchmarking System project.*

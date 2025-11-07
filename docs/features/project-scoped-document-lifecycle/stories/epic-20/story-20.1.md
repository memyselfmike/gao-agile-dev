# Story 20.1: Create ProjectDocumentLifecycle Factory Class

**Epic**: Epic 20 - Project-Scoped Document Lifecycle
**Status**: Ready
**Priority**: P0 (Critical)
**Estimated Effort**: 3 story points
**Owner**: Amelia (Developer)
**Created**: 2025-11-06

---

## User Story

**As a** GAO-Dev developer
**I want** a factory class for creating project-scoped document lifecycle components
**So that** each project has its own isolated documentation tracking system

---

## Acceptance Criteria

### AC1: ProjectDocumentLifecycle Factory Class Created

- ✅ New file: `gao_dev/lifecycle/project_lifecycle.py`
- ✅ `ProjectDocumentLifecycle` class with factory methods
- ✅ `initialize(project_root: Path)` method creates all components
- ✅ Returns fully initialized `DocumentLifecycleManager`
- ✅ Type hints included throughout

### AC2: Project-Scoped Directory Structure

- ✅ Creates `.gao-dev/` directory in project root
- ✅ Initializes `documents.db` at `project_root/.gao-dev/documents.db`
- ✅ Sets archive directory to `project_root/.archive`
- ✅ Creates directories if they don't exist
- ✅ Gracefully handles existing directories

### AC3: Component Integration

- ✅ `DocumentRegistry` initialized with project-specific DB path
- ✅ `DocumentLifecycleManager` initialized with project context
- ✅ Optional `project_root` parameter added to `DocumentLifecycleManager`
- ✅ Components properly connected and returned

### AC4: Isolation Verification

- ✅ Multiple projects can be initialized simultaneously
- ✅ Each project has its own isolated `documents.db`
- ✅ Operations on one project don't affect others
- ✅ No shared state between project instances

### AC5: Unit Tests

- ✅ Test: `test_initialize_creates_structure()` - Verifies directory creation
- ✅ Test: `test_initialize_returns_manager()` - Returns correct instance
- ✅ Test: `test_multiple_projects_isolated()` - Verifies isolation
- ✅ Test: `test_existing_directory_handling()` - Handles existing `.gao-dev/`
- ✅ All tests pass

---

## Technical Details

### File Structure

```
gao_dev/lifecycle/
├── __init__.py
├── registry.py              # Existing: DocumentRegistry
├── manager.py               # Existing: DocumentLifecycleManager
├── archival.py              # Existing: ArchivalManager
└── project_lifecycle.py     # NEW: ProjectDocumentLifecycle factory
```

### Implementation Approach

**Step 1: Create project_lifecycle.py**

```python
"""
Project-scoped document lifecycle initialization.

This module provides factory methods for creating document lifecycle
components that are scoped to a specific project, ensuring proper
isolation and context management.
"""

from pathlib import Path
from typing import Optional
import structlog

from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.lifecycle.manager import DocumentLifecycleManager

logger = structlog.get_logger(__name__)


class ProjectDocumentLifecycle:
    """
    Factory for creating project-scoped document lifecycle components.

    This class provides a centralized way to initialize the document
    lifecycle system for a specific project, ensuring all components
    are properly configured and isolated.
    """

    @classmethod
    def initialize(
        cls,
        project_root: Path,
        create_dirs: bool = True
    ) -> DocumentLifecycleManager:
        """
        Initialize document lifecycle for a project.

        Creates the necessary directory structure and initializes all
        document lifecycle components with project-specific paths.

        Args:
            project_root: Root directory of the project
            create_dirs: Whether to create directories if they don't exist

        Returns:
            Fully initialized DocumentLifecycleManager

        Raises:
            ValueError: If project_root doesn't exist and create_dirs is False
            OSError: If directory creation fails

        Example:
            >>> project_root = Path("sandbox/projects/my-app")
            >>> doc_lifecycle = ProjectDocumentLifecycle.initialize(project_root)
            >>> doc_lifecycle.register_document("PRD.md", "product-requirements")
        """
        logger.info(
            "Initializing project-scoped document lifecycle",
            project_root=str(project_root)
        )

        # Validate project root
        if not project_root.exists():
            if create_dirs:
                logger.debug("Creating project root directory")
                project_root.mkdir(parents=True, exist_ok=True)
            else:
                raise ValueError(f"Project root does not exist: {project_root}")

        # Create .gao-dev directory
        gao_dev_dir = project_root / ".gao-dev"
        if create_dirs:
            gao_dev_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(".gao-dev directory ready", path=str(gao_dev_dir))

        # Set up paths
        db_path = gao_dev_dir / "documents.db"
        archive_dir = project_root / ".archive"

        logger.debug(
            "Project paths configured",
            db_path=str(db_path),
            archive_dir=str(archive_dir)
        )

        # Initialize components
        registry = DocumentRegistry(db_path)
        manager = DocumentLifecycleManager(
            registry=registry,
            archive_dir=archive_dir,
            project_root=project_root  # NEW parameter
        )

        logger.info(
            "Document lifecycle initialized successfully",
            project_root=str(project_root)
        )

        return manager

    @classmethod
    def get_gao_dev_dir(cls, project_root: Path) -> Path:
        """
        Get the .gao-dev directory path for a project.

        Args:
            project_root: Root directory of the project

        Returns:
            Path to .gao-dev directory
        """
        return project_root / ".gao-dev"

    @classmethod
    def get_db_path(cls, project_root: Path) -> Path:
        """
        Get the documents.db path for a project.

        Args:
            project_root: Root directory of the project

        Returns:
            Path to documents.db file
        """
        return cls.get_gao_dev_dir(project_root) / "documents.db"

    @classmethod
    def get_archive_dir(cls, project_root: Path) -> Path:
        """
        Get the archive directory path for a project.

        Args:
            project_root: Root directory of the project

        Returns:
            Path to archive directory
        """
        return project_root / ".archive"

    @classmethod
    def is_initialized(cls, project_root: Path) -> bool:
        """
        Check if document lifecycle is initialized for a project.

        Args:
            project_root: Root directory of the project

        Returns:
            True if .gao-dev directory and documents.db exist
        """
        gao_dev_dir = cls.get_gao_dev_dir(project_root)
        db_path = cls.get_db_path(project_root)

        return gao_dev_dir.exists() and db_path.exists()
```

**Step 2: Update DocumentLifecycleManager**

Add optional `project_root` parameter to constructor:

```python
# In gao_dev/lifecycle/manager.py

class DocumentLifecycleManager:
    """Manages document lifecycle operations."""

    def __init__(
        self,
        registry: DocumentRegistry,
        archive_dir: Path,
        project_root: Optional[Path] = None  # NEW parameter
    ):
        """
        Initialize the document lifecycle manager.

        Args:
            registry: Document registry instance
            archive_dir: Directory for archived documents
            project_root: Optional project root for logging context
        """
        self.registry = registry
        self.archive_dir = archive_dir
        self.project_root = project_root  # Store for context
        self.archival_manager = ArchivalManager(archive_dir)

        # Log initialization with project context
        if project_root:
            logger.info(
                "Document lifecycle manager initialized",
                project_root=str(project_root)
            )
```

**Step 3: Update __init__.py**

Export new factory class:

```python
# In gao_dev/lifecycle/__init__.py

from .registry import DocumentRegistry
from .manager import DocumentLifecycleManager
from .archival import ArchivalManager
from .project_lifecycle import ProjectDocumentLifecycle  # NEW

__all__ = [
    "DocumentRegistry",
    "DocumentLifecycleManager",
    "ArchivalManager",
    "ProjectDocumentLifecycle",  # NEW
]
```

---

## Testing Approach

### Unit Tests

Create `tests/lifecycle/test_project_lifecycle.py`:

```python
"""Tests for ProjectDocumentLifecycle factory."""

import pytest
from pathlib import Path
import tempfile
import shutil

from gao_dev.lifecycle.project_lifecycle import ProjectDocumentLifecycle
from gao_dev.lifecycle.manager import DocumentLifecycleManager


class TestProjectDocumentLifecycle:
    """Test suite for ProjectDocumentLifecycle."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_initialize_creates_structure(self, temp_project_dir):
        """Test that initialize creates .gao-dev structure."""
        # Initialize
        manager = ProjectDocumentLifecycle.initialize(temp_project_dir)

        # Verify structure
        assert (temp_project_dir / ".gao-dev").exists()
        assert (temp_project_dir / ".gao-dev" / "documents.db").exists()
        assert isinstance(manager, DocumentLifecycleManager)

    def test_initialize_returns_manager(self, temp_project_dir):
        """Test that initialize returns DocumentLifecycleManager."""
        manager = ProjectDocumentLifecycle.initialize(temp_project_dir)

        assert isinstance(manager, DocumentLifecycleManager)
        assert manager.project_root == temp_project_dir

    def test_multiple_projects_isolated(self, tmp_path):
        """Test that multiple projects are isolated."""
        # Create two projects
        project1 = tmp_path / "project1"
        project2 = tmp_path / "project2"

        manager1 = ProjectDocumentLifecycle.initialize(project1)
        manager2 = ProjectDocumentLifecycle.initialize(project2)

        # Verify isolated databases
        db1 = project1 / ".gao-dev" / "documents.db"
        db2 = project2 / ".gao-dev" / "documents.db"

        assert db1.exists()
        assert db2.exists()
        assert db1 != db2

        # Register document in project1
        manager1.registry.register_document(
            path="test.md",
            doc_type="test",
            metadata={}
        )

        # Verify project2 is unaffected
        docs = manager2.registry.list_documents()
        assert len(docs) == 0

    def test_existing_directory_handling(self, temp_project_dir):
        """Test handling of existing .gao-dev directory."""
        # Create .gao-dev manually
        gao_dev_dir = temp_project_dir / ".gao-dev"
        gao_dev_dir.mkdir(parents=True, exist_ok=True)

        # Initialize should succeed
        manager = ProjectDocumentLifecycle.initialize(temp_project_dir)

        assert isinstance(manager, DocumentLifecycleManager)
        assert (temp_project_dir / ".gao-dev" / "documents.db").exists()

    def test_get_gao_dev_dir(self, temp_project_dir):
        """Test get_gao_dev_dir helper method."""
        gao_dev_dir = ProjectDocumentLifecycle.get_gao_dev_dir(temp_project_dir)

        assert gao_dev_dir == temp_project_dir / ".gao-dev"

    def test_get_db_path(self, temp_project_dir):
        """Test get_db_path helper method."""
        db_path = ProjectDocumentLifecycle.get_db_path(temp_project_dir)

        assert db_path == temp_project_dir / ".gao-dev" / "documents.db"

    def test_get_archive_dir(self, temp_project_dir):
        """Test get_archive_dir helper method."""
        archive_dir = ProjectDocumentLifecycle.get_archive_dir(temp_project_dir)

        assert archive_dir == temp_project_dir / ".archive"

    def test_is_initialized_false(self, temp_project_dir):
        """Test is_initialized returns False before initialization."""
        assert not ProjectDocumentLifecycle.is_initialized(temp_project_dir)

    def test_is_initialized_true(self, temp_project_dir):
        """Test is_initialized returns True after initialization."""
        ProjectDocumentLifecycle.initialize(temp_project_dir)

        assert ProjectDocumentLifecycle.is_initialized(temp_project_dir)

    def test_create_dirs_false_raises_error(self, tmp_path):
        """Test that create_dirs=False raises error for non-existent path."""
        non_existent = tmp_path / "does-not-exist"

        with pytest.raises(ValueError, match="Project root does not exist"):
            ProjectDocumentLifecycle.initialize(non_existent, create_dirs=False)
```

Run tests:
```bash
pytest tests/lifecycle/test_project_lifecycle.py -v
```

---

## Dependencies

### Required Packages
- ✅ structlog (already installed)
- ✅ pathlib (standard library)
- ✅ pytest (already installed)

### Code Dependencies
- `gao_dev.lifecycle.registry.DocumentRegistry`
- `gao_dev.lifecycle.manager.DocumentLifecycleManager`
- `gao_dev.lifecycle.archival.ArchivalManager`

---

## Definition of Done

- [ ] File `gao_dev/lifecycle/project_lifecycle.py` created
- [ ] `ProjectDocumentLifecycle` factory class implemented
- [ ] `DocumentLifecycleManager` updated with `project_root` parameter
- [ ] Helper methods implemented (get_gao_dev_dir, get_db_path, etc.)
- [ ] Unit tests created and passing (100% coverage)
- [ ] Type hints throughout (mypy passes)
- [ ] Documentation strings complete
- [ ] Exported in `__init__.py`
- [ ] Code review completed
- [ ] Committed to git with conventional commit message

---

## Related Stories

**Depends On**: None (foundational story)

**Blocks**:
- Story 20.2: Update SandboxManager Integration
- Story 20.3: Update Orchestrator Integration
- Story 20.4: Add Project Root Detection

---

## Notes

### Key Design Decisions

1. **Factory Pattern**: Centralized initialization ensures consistency
2. **Path Isolation**: Each project gets its own `.gao-dev/` directory
3. **Helper Methods**: Utilities for common path operations
4. **Logging**: Comprehensive logging for debugging
5. **Type Safety**: Full type hints for IDE support

### Future Enhancements

- Support for custom `.gao-dev/` directory names
- Configuration file in `.gao-dev/` for project settings
- Backup/restore functionality for `.gao-dev/`
- Metrics tracking for document operations

---

## Acceptance Testing

### Test Case 1: Initialize New Project

```bash
# Python
from pathlib import Path
from gao_dev.lifecycle.project_lifecycle import ProjectDocumentLifecycle

project_root = Path("sandbox/projects/test-app")
manager = ProjectDocumentLifecycle.initialize(project_root)

# Verify
assert (project_root / ".gao-dev").exists()
assert (project_root / ".gao-dev" / "documents.db").exists()
```

**Expected**: Directory structure created, manager returned

### Test Case 2: Multiple Projects Isolated

```python
# Create two projects
manager1 = ProjectDocumentLifecycle.initialize(Path("sandbox/projects/app1"))
manager2 = ProjectDocumentLifecycle.initialize(Path("sandbox/projects/app2"))

# Register document in app1
manager1.registry.register_document("test.md", "test", {})

# Verify app2 unaffected
docs = manager2.registry.list_documents()
assert len(docs) == 0
```

**Expected**: Projects have isolated registries

### Test Case 3: Check Initialization Status

```python
project_root = Path("sandbox/projects/my-app")

# Before initialization
assert not ProjectDocumentLifecycle.is_initialized(project_root)

# After initialization
ProjectDocumentLifecycle.initialize(project_root)
assert ProjectDocumentLifecycle.is_initialized(project_root)
```

**Expected**: Status correctly reflects initialization state

---

**Created by**: Bob (Scrum Master)
**Ready for Implementation**: Yes
**Estimated Completion**: 1-2 days

---

*This story is part of Epic 20: Project-Scoped Document Lifecycle.*

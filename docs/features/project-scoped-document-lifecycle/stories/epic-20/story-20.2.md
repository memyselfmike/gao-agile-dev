# Story 20.2: Update SandboxManager Integration

**Epic**: Epic 20 - Project-Scoped Document Lifecycle
**Status**: Ready
**Priority**: P0 (Critical)
**Estimated Effort**: 3 story points
**Owner**: Amelia (Developer)
**Created**: 2025-11-06

---

## User Story

**As a** GAO-Dev developer
**I want** SandboxManager to initialize project-scoped document lifecycle on project creation
**So that** each sandbox project has its own documentation tracking from the start

---

## Acceptance Criteria

### AC1: SandboxManager Creates .gao-dev Structure

- ✅ `SandboxManager.create_project()` calls `ProjectDocumentLifecycle.initialize()`
- ✅ `.gao-dev/` directory created in project root on initialization
- ✅ `documents.db` created and ready for use
- ✅ Archive directory path configured correctly

### AC2: ProjectLifecycleService Integration

- ✅ `ProjectLifecycleService.create_project()` initializes document lifecycle
- ✅ Document lifecycle initialization logged with project context
- ✅ Initialization happens after directory creation, before git init
- ✅ Error handling for initialization failures

### AC3: ProjectMetadata Tracking

- ✅ `ProjectMetadata` includes document lifecycle version
- ✅ Metadata stored in `.sandbox.yaml` includes lifecycle info
- ✅ Can query if project has document lifecycle initialized
- ✅ Version tracking for future migrations

### AC4: Existing Project Handling

- ✅ Calling `create_project()` on existing project doesn't break
- ✅ Gracefully handles existing `.gao-dev/` directory
- ✅ Can re-initialize if needed (idempotent operation)
- ✅ Clear logging for existing vs. new initialization

### AC5: Integration Tests

- ✅ Test: `test_create_project_initializes_lifecycle()` - Verifies lifecycle created
- ✅ Test: `test_multiple_projects_isolated_lifecycles()` - Isolation verified
- ✅ Test: `test_project_metadata_includes_lifecycle()` - Metadata tracking
- ✅ Test: `test_existing_project_handling()` - Handles existing projects
- ✅ All tests pass

---

## Technical Details

### File Structure

```
gao_dev/sandbox/
├── manager.py                    # UPDATE: SandboxManager
├── services/
│   └── project_lifecycle.py      # UPDATE: ProjectLifecycleService
└── models/
    └── project.py                # UPDATE: ProjectMetadata
```

### Implementation Approach

**Step 1: Update ProjectMetadata Model**

Add document lifecycle tracking to metadata:

```python
# In gao_dev/sandbox/models/project.py

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class ProjectMetadata:
    """Metadata for a sandbox project."""

    name: str
    project_dir: Path
    created_at: datetime
    last_modified: datetime
    boilerplate_url: Optional[str] = None
    status: str = "active"

    # NEW: Document lifecycle tracking
    document_lifecycle_version: str = "1.0.0"
    document_lifecycle_initialized: bool = False

    # Existing fields...
    git_initialized: bool = False
    dependencies_installed: bool = False
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization."""
        return {
            "name": self.name,
            "project_dir": str(self.project_dir),
            "created_at": self.created_at.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "boilerplate_url": self.boilerplate_url,
            "status": self.status,
            "document_lifecycle_version": self.document_lifecycle_version,
            "document_lifecycle_initialized": self.document_lifecycle_initialized,
            "git_initialized": self.git_initialized,
            "dependencies_installed": self.dependencies_installed,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectMetadata":
        """Create from dictionary (YAML deserialization)."""
        return cls(
            name=data["name"],
            project_dir=Path(data["project_dir"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_modified=datetime.fromisoformat(data["last_modified"]),
            boilerplate_url=data.get("boilerplate_url"),
            status=data.get("status", "active"),
            document_lifecycle_version=data.get("document_lifecycle_version", "1.0.0"),
            document_lifecycle_initialized=data.get("document_lifecycle_initialized", False),
            git_initialized=data.get("git_initialized", False),
            dependencies_installed=data.get("dependencies_installed", False),
            metadata=data.get("metadata", {}),
        )
```

**Step 2: Update ProjectLifecycleService**

Add document lifecycle initialization:

```python
# In gao_dev/sandbox/services/project_lifecycle.py

from pathlib import Path
from typing import Optional
import structlog

from gao_dev.lifecycle.project_lifecycle import ProjectDocumentLifecycle
from gao_dev.sandbox.models.project import ProjectMetadata

logger = structlog.get_logger(__name__)


class ProjectLifecycleService:
    """Service for managing project lifecycle operations."""

    def __init__(self, projects_dir: Path):
        """Initialize the service."""
        self.projects_dir = projects_dir

    def create_project(
        self,
        name: str,
        boilerplate_url: Optional[str] = None
    ) -> ProjectMetadata:
        """
        Create a new sandbox project with full lifecycle setup.

        Args:
            name: Project name
            boilerplate_url: Optional boilerplate repository URL

        Returns:
            ProjectMetadata for the created project

        Raises:
            ValueError: If project already exists
            OSError: If directory creation fails
        """
        logger.info("Creating sandbox project", name=name)

        # Create project directory
        project_dir = self.projects_dir / name
        if project_dir.exists():
            raise ValueError(f"Project already exists: {name}")

        project_dir.mkdir(parents=True, exist_ok=False)
        logger.debug("Project directory created", path=str(project_dir))

        # Initialize document lifecycle (NEW)
        try:
            doc_manager = ProjectDocumentLifecycle.initialize(project_dir)
            document_lifecycle_initialized = True
            logger.info(
                "Document lifecycle initialized",
                project=name,
                db_path=str(ProjectDocumentLifecycle.get_db_path(project_dir))
            )
        except Exception as e:
            logger.error(
                "Failed to initialize document lifecycle",
                project=name,
                error=str(e)
            )
            document_lifecycle_initialized = False
            # Don't fail project creation, but log the issue

        # Initialize git repository (if enabled)
        git_initialized = False
        # ... existing git initialization code ...

        # Create project metadata
        metadata = ProjectMetadata(
            name=name,
            project_dir=project_dir,
            created_at=datetime.now(),
            last_modified=datetime.now(),
            boilerplate_url=boilerplate_url,
            status="active",
            document_lifecycle_initialized=document_lifecycle_initialized,
            git_initialized=git_initialized,
        )

        # Save metadata to .sandbox.yaml
        self._save_metadata(metadata)

        logger.info("Project created successfully", name=name)
        return metadata

    def initialize_document_lifecycle(
        self,
        project_name: str,
        force: bool = False
    ) -> bool:
        """
        Initialize or re-initialize document lifecycle for a project.

        Args:
            project_name: Name of the project
            force: Force re-initialization even if already initialized

        Returns:
            True if successful, False otherwise
        """
        project_dir = self.projects_dir / project_name

        if not project_dir.exists():
            logger.error("Project does not exist", project=project_name)
            return False

        # Check if already initialized
        if not force and ProjectDocumentLifecycle.is_initialized(project_dir):
            logger.info(
                "Document lifecycle already initialized",
                project=project_name
            )
            return True

        # Initialize
        try:
            ProjectDocumentLifecycle.initialize(project_dir)

            # Update metadata
            metadata = self._load_metadata(project_name)
            metadata.document_lifecycle_initialized = True
            metadata.last_modified = datetime.now()
            self._save_metadata(metadata)

            logger.info(
                "Document lifecycle initialized",
                project=project_name,
                force=force
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to initialize document lifecycle",
                project=project_name,
                error=str(e)
            )
            return False

    def _save_metadata(self, metadata: ProjectMetadata) -> None:
        """Save project metadata to .sandbox.yaml."""
        metadata_file = metadata.project_dir / ".sandbox.yaml"
        with open(metadata_file, "w") as f:
            yaml.dump(metadata.to_dict(), f)

    def _load_metadata(self, project_name: str) -> ProjectMetadata:
        """Load project metadata from .sandbox.yaml."""
        metadata_file = self.projects_dir / project_name / ".sandbox.yaml"
        with open(metadata_file, "r") as f:
            data = yaml.safe_load(f)
        return ProjectMetadata.from_dict(data)
```

**Step 3: Update SandboxManager**

Use ProjectLifecycleService in SandboxManager:

```python
# In gao_dev/sandbox/manager.py

class SandboxManager:
    """Manager for sandbox operations."""

    def __init__(self, projects_dir: Path):
        """Initialize the manager."""
        self.projects_dir = projects_dir
        self.lifecycle_service = ProjectLifecycleService(projects_dir)

    def create_project(
        self,
        name: str,
        boilerplate_url: Optional[str] = None,
        **kwargs
    ) -> ProjectMetadata:
        """
        Create a new sandbox project.

        This is a convenience wrapper around ProjectLifecycleService.create_project().

        Args:
            name: Project name
            boilerplate_url: Optional boilerplate repository URL
            **kwargs: Additional project options

        Returns:
            ProjectMetadata for the created project
        """
        return self.lifecycle_service.create_project(name, boilerplate_url)

    def initialize_document_lifecycle(
        self,
        project_name: str,
        force: bool = False
    ) -> bool:
        """
        Initialize document lifecycle for existing project.

        Args:
            project_name: Name of the project
            force: Force re-initialization

        Returns:
            True if successful
        """
        return self.lifecycle_service.initialize_document_lifecycle(
            project_name,
            force
        )
```

---

## Testing Approach

### Integration Tests

Create/update `tests/sandbox/test_sandbox_manager_lifecycle.py`:

```python
"""Integration tests for SandboxManager document lifecycle."""

import pytest
from pathlib import Path
import tempfile
import shutil

from gao_dev.sandbox.manager import SandboxManager
from gao_dev.lifecycle.project_lifecycle import ProjectDocumentLifecycle


class TestSandboxManagerLifecycle:
    """Test suite for SandboxManager document lifecycle integration."""

    @pytest.fixture
    def sandbox_dir(self):
        """Create temporary sandbox directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sandbox_manager(self, sandbox_dir):
        """Create SandboxManager instance."""
        return SandboxManager(sandbox_dir)

    def test_create_project_initializes_lifecycle(self, sandbox_manager, sandbox_dir):
        """Test that create_project initializes document lifecycle."""
        # Create project
        metadata = sandbox_manager.create_project("test-app")

        # Verify document lifecycle initialized
        project_dir = sandbox_dir / "test-app"
        assert (project_dir / ".gao-dev").exists()
        assert (project_dir / ".gao-dev" / "documents.db").exists()
        assert metadata.document_lifecycle_initialized is True

    def test_multiple_projects_isolated_lifecycles(self, sandbox_manager):
        """Test that multiple projects have isolated document lifecycles."""
        # Create two projects
        metadata1 = sandbox_manager.create_project("app1")
        metadata2 = sandbox_manager.create_project("app2")

        # Verify isolated
        assert metadata1.document_lifecycle_initialized is True
        assert metadata2.document_lifecycle_initialized is True

        # Get document managers
        manager1 = ProjectDocumentLifecycle.initialize(metadata1.project_dir)
        manager2 = ProjectDocumentLifecycle.initialize(metadata2.project_dir)

        # Register document in app1
        manager1.registry.register_document("test.md", "test", {})

        # Verify app2 unaffected
        docs = manager2.registry.list_documents()
        assert len(docs) == 0

    def test_project_metadata_includes_lifecycle(self, sandbox_manager):
        """Test that project metadata includes lifecycle information."""
        metadata = sandbox_manager.create_project("test-app")

        # Verify metadata
        assert hasattr(metadata, "document_lifecycle_initialized")
        assert hasattr(metadata, "document_lifecycle_version")
        assert metadata.document_lifecycle_initialized is True
        assert metadata.document_lifecycle_version == "1.0.0"

    def test_existing_project_handling(self, sandbox_manager, sandbox_dir):
        """Test handling of existing projects."""
        # Create project
        metadata1 = sandbox_manager.create_project("test-app")

        # Try to create again (should fail)
        with pytest.raises(ValueError, match="already exists"):
            sandbox_manager.create_project("test-app")

        # But can re-initialize lifecycle
        success = sandbox_manager.initialize_document_lifecycle("test-app", force=True)
        assert success is True

    def test_initialize_on_existing_without_force(self, sandbox_manager):
        """Test initialize on existing project without force flag."""
        # Create project (has lifecycle)
        metadata = sandbox_manager.create_project("test-app")
        assert metadata.document_lifecycle_initialized is True

        # Initialize without force (should be no-op but succeed)
        success = sandbox_manager.initialize_document_lifecycle("test-app", force=False)
        assert success is True

    def test_initialize_nonexistent_project(self, sandbox_manager):
        """Test initialize on non-existent project."""
        success = sandbox_manager.initialize_document_lifecycle("does-not-exist")
        assert success is False

    def test_metadata_persisted_to_yaml(self, sandbox_manager, sandbox_dir):
        """Test that metadata with lifecycle info is persisted to .sandbox.yaml."""
        metadata = sandbox_manager.create_project("test-app")

        # Load from file
        import yaml
        metadata_file = sandbox_dir / "test-app" / ".sandbox.yaml"
        with open(metadata_file, "r") as f:
            data = yaml.safe_load(f)

        # Verify lifecycle fields present
        assert "document_lifecycle_initialized" in data
        assert "document_lifecycle_version" in data
        assert data["document_lifecycle_initialized"] is True
```

Run tests:
```bash
pytest tests/sandbox/test_sandbox_manager_lifecycle.py -v
```

---

## Dependencies

### Required Packages
- ✅ structlog (already installed)
- ✅ PyYAML (already installed)
- ✅ pytest (already installed)

### Code Dependencies
- Story 20.1: ProjectDocumentLifecycle factory class
- `gao_dev.sandbox.manager.SandboxManager`
- `gao_dev.sandbox.services.project_lifecycle.ProjectLifecycleService`
- `gao_dev.sandbox.models.project.ProjectMetadata`

---

## Definition of Done

- [ ] `ProjectMetadata` updated with lifecycle tracking fields
- [ ] `ProjectLifecycleService.create_project()` initializes document lifecycle
- [ ] `ProjectLifecycleService.initialize_document_lifecycle()` method added
- [ ] `SandboxManager` uses updated lifecycle service
- [ ] Metadata persisted to `.sandbox.yaml` with lifecycle info
- [ ] Integration tests created and passing
- [ ] Error handling for initialization failures
- [ ] Logging comprehensive and clear
- [ ] Code review completed
- [ ] Committed to git with conventional commit message

---

## Related Stories

**Depends On**:
- Story 20.1: Create ProjectDocumentLifecycle Factory Class

**Blocks**:
- Story 20.3: Update Orchestrator Integration

---

## Notes

### Key Design Decisions

1. **Non-Fatal Failure**: Document lifecycle initialization failure doesn't prevent project creation
2. **Metadata Tracking**: Lifecycle status tracked in `.sandbox.yaml` for visibility
3. **Idempotent**: Can safely call initialize multiple times
4. **Version Tracking**: Version field for future migrations

### Migration Considerations

- Existing projects without `.gao-dev/` can be initialized using `initialize_document_lifecycle()`
- Version field allows detecting old projects needing migration
- Graceful degradation if lifecycle not initialized

---

## Acceptance Testing

### Test Case 1: Create Project Initializes Lifecycle

```bash
# Python
from gao_dev.sandbox.manager import SandboxManager
from pathlib import Path

manager = SandboxManager(Path("sandbox/projects"))
metadata = manager.create_project("test-app")

# Verify
assert (Path("sandbox/projects/test-app/.gao-dev/documents.db")).exists()
assert metadata.document_lifecycle_initialized is True
```

**Expected**: `.gao-dev/` structure created, metadata reflects initialization

### Test Case 2: Multiple Projects Isolated

```bash
# Create two projects
manager.create_project("app1")
manager.create_project("app2")

# Verify isolated databases
assert Path("sandbox/projects/app1/.gao-dev/documents.db").exists()
assert Path("sandbox/projects/app2/.gao-dev/documents.db").exists()
```

**Expected**: Each project has its own database

### Test Case 3: Metadata Persisted

```bash
# Create project
metadata = manager.create_project("test-app")

# Check .sandbox.yaml
import yaml
with open("sandbox/projects/test-app/.sandbox.yaml") as f:
    data = yaml.safe_load(f)

assert data["document_lifecycle_initialized"] is True
```

**Expected**: Lifecycle status saved to metadata file

---

**Created by**: Bob (Scrum Master)
**Ready for Implementation**: Yes
**Estimated Completion**: 1-2 days

---

*This story is part of Epic 20: Project-Scoped Document Lifecycle.*

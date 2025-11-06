"""Integration tests for SandboxManager document lifecycle."""

import pytest
from pathlib import Path
import tempfile
import shutil
import yaml

from gao_dev.sandbox.manager import SandboxManager
from gao_dev.lifecycle.project_lifecycle import ProjectDocumentLifecycle


class TestSandboxLifecycleIntegration:
    """Test suite for SandboxManager document lifecycle integration."""

    @pytest.fixture
    def sandbox_dir(self):
        """Create temporary sandbox directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # Cleanup
        if temp_dir.exists():
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
        project_dir = sandbox_dir / "projects" / "test-app"
        assert (project_dir / ".gao-dev").exists()
        assert (project_dir / ".gao-dev" / "documents.db").exists()
        assert metadata.document_lifecycle_initialized is True
        assert metadata.document_lifecycle_version == "1.0.0"

    def test_multiple_projects_isolated_lifecycles(self, sandbox_manager, sandbox_dir):
        """Test that multiple projects have isolated document lifecycles."""
        # Create two projects
        metadata1 = sandbox_manager.create_project("app1")
        metadata2 = sandbox_manager.create_project("app2")

        # Verify both initialized
        assert metadata1.document_lifecycle_initialized is True
        assert metadata2.document_lifecycle_initialized is True

        # Get document managers
        project_dir1 = sandbox_dir / "projects" / "app1"
        project_dir2 = sandbox_dir / "projects" / "app2"
        manager1 = ProjectDocumentLifecycle.initialize(project_dir1)
        manager2 = ProjectDocumentLifecycle.initialize(project_dir2)

        # Register document in app1
        manager1.register_document(
            path=project_dir1 / "test.md",
            doc_type="prd",
            author="test-user",
            metadata={}
        )

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
        with pytest.raises(Exception):  # ProjectExistsError
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
        metadata_file = sandbox_dir / "projects" / "test-app" / ".sandbox.yaml"
        with open(metadata_file, "r") as f:
            data = yaml.safe_load(f)

        # Verify lifecycle fields present
        assert "document_lifecycle_initialized" in data
        assert "document_lifecycle_version" in data
        assert data["document_lifecycle_initialized"] is True
        assert data["document_lifecycle_version"] == "1.0.0"

    def test_get_project_loads_lifecycle_metadata(self, sandbox_manager):
        """Test that getting project loads lifecycle metadata correctly."""
        # Create project
        metadata1 = sandbox_manager.create_project("test-app")
        assert metadata1.document_lifecycle_initialized is True

        # Get project (reload from disk)
        metadata2 = sandbox_manager.get_project("test-app")
        assert metadata2.document_lifecycle_initialized is True
        assert metadata2.document_lifecycle_version == "1.0.0"

    def test_list_projects_includes_lifecycle_metadata(self, sandbox_manager):
        """Test that listing projects includes lifecycle metadata."""
        # Create two projects
        sandbox_manager.create_project("app1")
        sandbox_manager.create_project("app2")

        # List projects
        projects = sandbox_manager.list_projects()

        # Verify both have lifecycle metadata
        assert len(projects) == 2
        for project in projects:
            assert hasattr(project, "document_lifecycle_initialized")
            assert hasattr(project, "document_lifecycle_version")
            assert project.document_lifecycle_initialized is True
            assert project.document_lifecycle_version == "1.0.0"

    def test_initialize_lifecycle_updates_metadata(self, sandbox_manager, sandbox_dir):
        """Test that initializing lifecycle updates metadata timestamps."""
        # Create project
        metadata1 = sandbox_manager.create_project("test-app")
        original_modified = metadata1.last_modified

        # Wait a moment and re-initialize
        import time
        time.sleep(0.1)
        success = sandbox_manager.initialize_document_lifecycle("test-app", force=True)
        assert success is True

        # Reload metadata
        metadata2 = sandbox_manager.get_project("test-app")
        assert metadata2.last_modified > original_modified

    def test_lifecycle_initialization_idempotent(self, sandbox_manager, sandbox_dir):
        """Test that lifecycle initialization is idempotent."""
        # Create project
        metadata = sandbox_manager.create_project("test-app")
        project_dir = sandbox_dir / "projects" / "test-app"

        # Get initial database
        db_path = project_dir / ".gao-dev" / "documents.db"
        assert db_path.exists()
        initial_mtime = db_path.stat().st_mtime

        # Initialize again (without force, should be no-op)
        import time
        time.sleep(0.1)
        success = sandbox_manager.initialize_document_lifecycle("test-app", force=False)
        assert success is True

        # Database should not be recreated
        assert db_path.stat().st_mtime == initial_mtime

    def test_backward_compatibility_missing_lifecycle_fields(self, sandbox_manager, sandbox_dir):
        """Test backward compatibility when lifecycle fields are missing from metadata."""
        # Create project
        metadata = sandbox_manager.create_project("test-app")
        project_dir = sandbox_dir / "projects" / "test-app"

        # Manually edit .sandbox.yaml to remove lifecycle fields
        metadata_file = project_dir / ".sandbox.yaml"
        with open(metadata_file, "r") as f:
            data = yaml.safe_load(f)

        # Remove lifecycle fields
        data.pop("document_lifecycle_initialized", None)
        data.pop("document_lifecycle_version", None)

        with open(metadata_file, "w") as f:
            yaml.dump(data, f)

        # Reload project - should have defaults
        reloaded = sandbox_manager.get_project("test-app")
        assert reloaded.document_lifecycle_initialized is False
        assert reloaded.document_lifecycle_version == "1.0.0"

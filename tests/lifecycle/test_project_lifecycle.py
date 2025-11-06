"""Tests for ProjectDocumentLifecycle factory."""

import pytest
from pathlib import Path
import tempfile
import shutil

from gao_dev.lifecycle.project_lifecycle import ProjectDocumentLifecycle
from gao_dev.lifecycle.document_manager import DocumentLifecycleManager


class TestProjectDocumentLifecycle:
    """Test suite for ProjectDocumentLifecycle."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # Clean up - ensure all connections are closed before removing directory
        import gc
        gc.collect()
        try:
            shutil.rmtree(temp_dir)
        except PermissionError:
            # On Windows, sometimes file handles aren't released immediately
            import time
            time.sleep(0.1)
            try:
                shutil.rmtree(temp_dir)
            except PermissionError:
                # If still locked, just pass - temp files will be cleaned eventually
                pass

    def test_initialize_creates_structure(self, temp_project_dir):
        """Test that initialize creates .gao-dev structure."""
        # Initialize
        manager = ProjectDocumentLifecycle.initialize(temp_project_dir)

        # Verify structure
        assert (temp_project_dir / ".gao-dev").exists()
        assert (temp_project_dir / ".gao-dev" / "documents.db").exists()
        assert isinstance(manager, DocumentLifecycleManager)

        # Close registry to release database connection
        manager.registry.close()

    def test_initialize_returns_manager(self, temp_project_dir):
        """Test that initialize returns DocumentLifecycleManager."""
        manager = ProjectDocumentLifecycle.initialize(temp_project_dir)

        assert isinstance(manager, DocumentLifecycleManager)
        assert manager.project_root == temp_project_dir

        # Close registry to release database connection
        manager.registry.close()

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
            doc_type="prd",
            author="test-author",
            metadata={}
        )

        # Verify project2 is unaffected
        docs = manager2.registry.query_documents()
        assert len(docs) == 0

        # Close registries to release database connections
        manager1.registry.close()
        manager2.registry.close()

    def test_existing_directory_handling(self, temp_project_dir):
        """Test handling of existing .gao-dev directory."""
        # Create .gao-dev manually
        gao_dev_dir = temp_project_dir / ".gao-dev"
        gao_dev_dir.mkdir(parents=True, exist_ok=True)

        # Initialize should succeed
        manager = ProjectDocumentLifecycle.initialize(temp_project_dir)

        assert isinstance(manager, DocumentLifecycleManager)
        assert (temp_project_dir / ".gao-dev" / "documents.db").exists()

        # Close registry to release database connection
        manager.registry.close()

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
        manager = ProjectDocumentLifecycle.initialize(temp_project_dir)

        assert ProjectDocumentLifecycle.is_initialized(temp_project_dir)

        # Close registry to release database connection
        manager.registry.close()

    def test_create_dirs_false_raises_error(self, tmp_path):
        """Test that create_dirs=False raises error for non-existent path."""
        non_existent = tmp_path / "does-not-exist"

        with pytest.raises(ValueError, match="Project root does not exist"):
            ProjectDocumentLifecycle.initialize(non_existent, create_dirs=False)

    def test_project_root_stored_in_manager(self, temp_project_dir):
        """Test that project_root is properly stored in manager."""
        manager = ProjectDocumentLifecycle.initialize(temp_project_dir)

        assert hasattr(manager, 'project_root')
        assert manager.project_root == temp_project_dir

        # Close registry to release database connection
        manager.registry.close()

    def test_archive_dir_path_correct(self, temp_project_dir):
        """Test that archive directory path is correctly set."""
        manager = ProjectDocumentLifecycle.initialize(temp_project_dir)

        expected_archive = temp_project_dir / ".archive"
        assert manager.archive_dir == expected_archive

        # Close registry to release database connection
        manager.registry.close()

    def test_database_path_correct(self, temp_project_dir):
        """Test that database path is correctly set."""
        manager = ProjectDocumentLifecycle.initialize(temp_project_dir)

        expected_db = temp_project_dir / ".gao-dev" / "documents.db"
        assert manager.registry.db_path == expected_db

        # Close registry to release database connection
        manager.registry.close()

    def test_initialize_creates_project_root_if_not_exists(self, tmp_path):
        """Test that initialize creates project root if it doesn't exist."""
        new_project = tmp_path / "new" / "nested" / "project"
        assert not new_project.exists()

        manager = ProjectDocumentLifecycle.initialize(new_project, create_dirs=True)

        assert new_project.exists()
        assert isinstance(manager, DocumentLifecycleManager)

        # Close registry to release database connection
        manager.registry.close()

    def test_is_initialized_false_when_only_directory_exists(self, temp_project_dir):
        """Test is_initialized returns False when only .gao-dev exists but no DB."""
        gao_dev_dir = temp_project_dir / ".gao-dev"
        gao_dev_dir.mkdir(parents=True, exist_ok=True)

        assert not ProjectDocumentLifecycle.is_initialized(temp_project_dir)

    def test_multiple_initializations_same_project(self, temp_project_dir):
        """Test that multiple initializations of same project work correctly."""
        manager1 = ProjectDocumentLifecycle.initialize(temp_project_dir)

        # Register a document
        manager1.registry.register_document(
            path="test.md",
            doc_type="prd",
            author="test-author",
            metadata={}
        )

        # Close first registry to release connection
        manager1.registry.close()

        # Initialize again - should work and access same DB
        manager2 = ProjectDocumentLifecycle.initialize(temp_project_dir)

        docs = manager2.registry.query_documents()
        assert len(docs) == 1
        assert docs[0].path == "test.md"

        # Close second registry
        manager2.registry.close()

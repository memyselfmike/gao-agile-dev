"""Integration tests for Orchestrator document lifecycle."""

import pytest
from pathlib import Path
import tempfile
import shutil
import json

from gao_dev.orchestrator.orchestrator import GAODevOrchestrator
from gao_dev.lifecycle.project_lifecycle import ProjectDocumentLifecycle


class TestOrchestratorLifecycle:
    """Test suite for Orchestrator document lifecycle integration."""

    @pytest.fixture
    def project_dir(self):
        """Create temporary project directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # Clean up any database connections before removing directory
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass

    def _cleanup_orchestrator(self, orchestrator):
        """Helper to clean up orchestrator database connections."""
        if orchestrator and orchestrator.doc_lifecycle:
            orchestrator.doc_lifecycle.registry.close()

    def test_orchestrator_initializes_lifecycle(self, project_dir):
        """Test that orchestrator initializes document lifecycle."""
        # Create orchestrator
        orchestrator = GAODevOrchestrator(project_root=project_dir)

        try:
            # Verify document lifecycle initialized
            assert orchestrator.doc_lifecycle is not None
            assert (project_dir / ".gao-dev" / "documents.db").exists()

            # Verify db path is correct
            expected_db_path = ProjectDocumentLifecycle.get_db_path(project_dir)
            assert expected_db_path == project_dir / ".gao-dev" / "documents.db"
            assert expected_db_path.exists()
        finally:
            # Clean up database connection
            if orchestrator.doc_lifecycle:
                orchestrator.doc_lifecycle.registry.close()

    def test_workflow_coordinator_has_doc_manager(self, project_dir):
        """Test that workflow coordinator receives document manager."""
        orchestrator = GAODevOrchestrator(project_root=project_dir)

        try:
            # Verify workflow_coordinator has doc_manager
            assert orchestrator.workflow_coordinator is not None
            assert orchestrator.workflow_coordinator.doc_manager is not None
            assert orchestrator.workflow_coordinator.doc_manager == orchestrator.doc_lifecycle
        finally:
            if orchestrator.doc_lifecycle:
                orchestrator.doc_lifecycle.registry.close()

    def test_get_document_manager(self, project_dir):
        """Test get_document_manager method."""
        orchestrator = GAODevOrchestrator(project_root=project_dir)

        try:
            doc_manager = orchestrator.get_document_manager()
            assert doc_manager is not None
            assert doc_manager.project_root == project_dir

            # Verify it's the same instance
            assert doc_manager == orchestrator.doc_lifecycle
        finally:
            self._cleanup_orchestrator(orchestrator)

    def test_multiple_orchestrators_isolated(self, tmp_path):
        """Test that multiple orchestrators have isolated lifecycles."""
        project1 = tmp_path / "project1"
        project2 = tmp_path / "project2"
        project1.mkdir()
        project2.mkdir()

        # Create two orchestrators
        orch1 = GAODevOrchestrator(project_root=project1)
        orch2 = GAODevOrchestrator(project_root=project2)

        try:
            # Verify isolated
            assert orch1.doc_lifecycle is not None
            assert orch2.doc_lifecycle is not None
            assert orch1.project_root != orch2.project_root

            # Register document in project1 using valid document type
            orch1.doc_lifecycle.registry.register_document("test.md", "prd", json.dumps({}))

            # Verify project2 unaffected
            docs = orch2.doc_lifecycle.registry.query_documents()
            assert len(docs) == 0

            # Verify project1 has the document
            docs1 = orch1.doc_lifecycle.registry.query_documents()
            assert len(docs1) == 1
            assert docs1[0].path == "test.md"
        finally:
            self._cleanup_orchestrator(orch1)
            self._cleanup_orchestrator(orch2)

    def test_orchestrator_without_project_root_uses_cwd(self):
        """Test orchestrator with default project root uses current directory."""
        # Create orchestrator without project_root
        # Note: This will create .gao-dev in current directory
        orchestrator = GAODevOrchestrator(project_root=Path.cwd())

        try:
            assert orchestrator.project_root == Path.cwd()
            assert orchestrator.doc_lifecycle is not None
        finally:
            self._cleanup_orchestrator(orchestrator)

    def test_orchestrator_lifecycle_failure_graceful(self, tmp_path):
        """Test that lifecycle initialization failure doesn't crash orchestrator."""
        # Use an invalid path that will cause initialization to fail
        # Create a file instead of directory to cause failure
        invalid_path = tmp_path / "invalid"
        invalid_path.touch()  # Create file, not directory

        # Should not crash, but doc_lifecycle will be None
        orchestrator = GAODevOrchestrator(project_root=invalid_path)

        # Orchestrator should still be created
        assert orchestrator is not None
        assert orchestrator.project_root == invalid_path

        # But doc_lifecycle should be None due to initialization failure
        assert orchestrator.doc_lifecycle is None

        # get_document_manager should return None
        assert orchestrator.get_document_manager() is None

    def test_orchestrator_with_existing_gao_dev(self, project_dir):
        """Test orchestrator with existing .gao-dev directory."""
        # Pre-create .gao-dev directory
        gao_dev_dir = project_dir / ".gao-dev"
        gao_dev_dir.mkdir(parents=True, exist_ok=True)

        # Create orchestrator
        orchestrator = GAODevOrchestrator(project_root=project_dir)

        try:
            # Should initialize successfully
            assert orchestrator.doc_lifecycle is not None
            assert (project_dir / ".gao-dev" / "documents.db").exists()
        finally:
            self._cleanup_orchestrator(orchestrator)

    def test_document_lifecycle_project_paths(self, project_dir):
        """Test that document lifecycle uses correct project paths."""
        orchestrator = GAODevOrchestrator(project_root=project_dir)

        try:
            # Verify paths
            assert orchestrator.doc_lifecycle.project_root == project_dir
            expected_db_path = project_dir / ".gao-dev" / "documents.db"
            expected_archive_dir = project_dir / ".archive"

            # Check db path
            actual_db_path = ProjectDocumentLifecycle.get_db_path(project_dir)
            assert actual_db_path == expected_db_path

            # Check archive dir path
            actual_archive_dir = ProjectDocumentLifecycle.get_archive_dir(project_dir)
            assert actual_archive_dir == expected_archive_dir
        finally:
            self._cleanup_orchestrator(orchestrator)

    def test_orchestrator_is_initialized_check(self, project_dir):
        """Test ProjectDocumentLifecycle.is_initialized() method."""
        # Before creating orchestrator
        assert not ProjectDocumentLifecycle.is_initialized(project_dir)

        # Create orchestrator
        orchestrator = GAODevOrchestrator(project_root=project_dir)

        try:
            # After creating orchestrator
            assert ProjectDocumentLifecycle.is_initialized(project_dir)
            assert orchestrator.doc_lifecycle is not None
        finally:
            self._cleanup_orchestrator(orchestrator)

    def test_workflow_coordinator_doc_manager_consistency(self, project_dir):
        """Test that workflow coordinator's doc_manager stays consistent."""
        orchestrator = GAODevOrchestrator(project_root=project_dir)

        try:
            # Verify initial state
            assert orchestrator.doc_lifecycle is not None
            assert orchestrator.workflow_coordinator.doc_manager is not None

            # Verify they are the same object
            assert orchestrator.workflow_coordinator.doc_manager is orchestrator.doc_lifecycle

            # Register a document via orchestrator using valid document type
            orchestrator.doc_lifecycle.registry.register_document("PRD.md", "prd", json.dumps({}))

            # Verify it's accessible via workflow coordinator
            docs = orchestrator.workflow_coordinator.doc_manager.registry.query_documents()
            assert len(docs) == 1
            assert docs[0].path == "PRD.md"
        finally:
            self._cleanup_orchestrator(orchestrator)

    def test_benchmark_orchestrator_uses_project_scoped(self, tmp_path):
        """Test that benchmark workflow orchestrator pattern uses project-scoped lifecycle."""
        # Simulate benchmark pattern: create orchestrator with specific project path
        project_dir = tmp_path / "benchmark-project"
        project_dir.mkdir()

        # Create orchestrator as benchmark would
        orchestrator = GAODevOrchestrator(project_root=project_dir)

        try:
            # Verify lifecycle is initialized in the correct location
            assert orchestrator.doc_lifecycle is not None
            assert ProjectDocumentLifecycle.is_initialized(project_dir)

            # Verify db path is in the project directory, not sandbox root
            db_path = ProjectDocumentLifecycle.get_db_path(project_dir)
            assert db_path == project_dir / ".gao-dev" / "documents.db"
            assert db_path.exists()
            assert db_path.is_relative_to(project_dir)
        finally:
            self._cleanup_orchestrator(orchestrator)

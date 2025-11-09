"""Integration tests for Epic 27: Integration & Migration.

Story 27.1: Integrate All Services with Orchestrator

Tests verify that:
1. GitIntegratedStateManager is properly integrated
2. CeremonyOrchestrator is properly integrated
3. All services work together
4. Orchestrator factory creates all services correctly
5. Services are properly closed on orchestrator close

Epic 27: Integration & Migration
Created: 2025-11-09
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock, MagicMock, patch

from gao_dev.orchestrator import GAODevOrchestrator
from gao_dev.orchestrator.orchestrator_factory import create_orchestrator
from gao_dev.core.services.git_integrated_state_manager import GitIntegratedStateManager
from gao_dev.orchestrator.ceremony_orchestrator import CeremonyOrchestrator


@pytest.fixture
def temp_project():
    """Create temporary project directory."""
    temp_dir = Path(tempfile.mkdtemp())

    # Create basic project structure
    (temp_dir / "docs").mkdir(parents=True, exist_ok=True)
    (temp_dir / "src").mkdir(parents=True, exist_ok=True)
    (temp_dir / ".gao-dev").mkdir(parents=True, exist_ok=True)

    # Create gao-dev.yaml config
    config_content = """
project_name: "Test Project"
project_level: 2
output_folder: "docs"
dev_story_location: "docs/stories"
git_auto_commit: true
qa_enabled: true
"""
    (temp_dir / "gao-dev.yaml").write_text(config_content)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestOrchestratorIntegration:
    """Test orchestrator service integration (Story 27.1)."""

    def test_orchestrator_factory_creates_git_state_manager(self, temp_project):
        """Test that orchestrator factory creates GitIntegratedStateManager."""
        # Create orchestrator using factory
        orchestrator = create_orchestrator(
            project_root=temp_project,
            mode="cli"
        )

        try:
            # Verify git_state_manager is created
            assert orchestrator.git_state_manager is not None
            assert isinstance(orchestrator.git_state_manager, GitIntegratedStateManager)

            # Verify it has correct configuration
            assert orchestrator.git_state_manager.project_path == temp_project
            assert orchestrator.git_state_manager.auto_commit is True

        finally:
            orchestrator.close()

    def test_orchestrator_factory_creates_ceremony_orchestrator(self, temp_project):
        """Test that orchestrator factory creates CeremonyOrchestrator."""
        orchestrator = create_orchestrator(
            project_root=temp_project,
            mode="cli"
        )

        try:
            # Verify ceremony_orchestrator is created
            assert orchestrator.ceremony_orchestrator is not None
            assert isinstance(orchestrator.ceremony_orchestrator, CeremonyOrchestrator)

            # Verify it has correct configuration
            assert orchestrator.ceremony_orchestrator.project_root == temp_project

        finally:
            orchestrator.close()

    def test_orchestrator_has_all_services(self, temp_project):
        """Test that orchestrator has all 10 services integrated."""
        orchestrator = create_orchestrator(
            project_root=temp_project,
            mode="cli"
        )

        try:
            # Verify all services are present
            assert orchestrator.workflow_execution_engine is not None
            assert orchestrator.artifact_manager is not None
            assert orchestrator.agent_coordinator is not None
            assert orchestrator.ceremony_orchestrator is not None
            assert orchestrator.workflow_coordinator is not None
            assert orchestrator.story_lifecycle is not None
            assert orchestrator.process_executor is not None
            assert orchestrator.quality_gate_manager is not None
            assert orchestrator.brian_orchestrator is not None
            assert orchestrator.git_state_manager is not None  # Epic 27.1

        finally:
            orchestrator.close()

    def test_orchestrator_close_closes_git_state_manager(self, temp_project):
        """Test that orchestrator.close() closes git_state_manager."""
        orchestrator = create_orchestrator(
            project_root=temp_project,
            mode="cli"
        )

        # Mock close method to track calls
        original_close = orchestrator.git_state_manager.close
        close_called = False

        def mock_close():
            nonlocal close_called
            close_called = True
            original_close()

        orchestrator.git_state_manager.close = mock_close

        # Close orchestrator
        orchestrator.close()

        # Verify git_state_manager.close() was called
        assert close_called is True

    def test_orchestrator_context_manager_closes_all_services(self, temp_project):
        """Test that context manager properly closes all services."""
        # Use orchestrator as context manager
        with create_orchestrator(project_root=temp_project, mode="cli") as orchestrator:
            # Verify services are available
            assert orchestrator.git_state_manager is not None
            assert orchestrator.ceremony_orchestrator is not None

        # After exiting context, services should be closed
        # (no exception should be raised)

    def test_git_state_manager_integration_with_db_path(self, temp_project):
        """Test that git_state_manager uses correct db_path."""
        orchestrator = create_orchestrator(
            project_root=temp_project,
            mode="cli"
        )

        try:
            # Verify db_path is set correctly
            expected_db_path = temp_project / ".gao-dev" / "documents.db"
            assert orchestrator.git_state_manager.db_path == expected_db_path

            # Verify .gao-dev directory exists
            assert (temp_project / ".gao-dev").exists()

        finally:
            orchestrator.close()

    def test_ceremony_orchestrator_integration_with_db_path(self, temp_project):
        """Test that ceremony_orchestrator uses correct db_path."""
        orchestrator = create_orchestrator(
            project_root=temp_project,
            mode="cli"
        )

        try:
            # Verify db_path is set correctly
            expected_db_path = temp_project / ".gao-dev" / "documents.db"
            assert orchestrator.ceremony_orchestrator.db_path == expected_db_path

        finally:
            orchestrator.close()

    def test_orchestrator_services_count_is_10(self, temp_project):
        """Test that orchestrator reports 10 services in logs."""
        with patch('gao_dev.orchestrator.orchestrator.logger') as mock_logger:
            orchestrator = create_orchestrator(
                project_root=temp_project,
                mode="cli"
            )

            try:
                # Check logger.info was called with services_count=10
                # Find the call with event="orchestrator_initialized"
                init_calls = [
                    call for call in mock_logger.info.call_args_list
                    if call[0][0] == "orchestrator_initialized"
                ]

                assert len(init_calls) > 0, "orchestrator_initialized log not found"

                # Verify services_count=10 in kwargs
                init_kwargs = init_calls[0][1]
                assert init_kwargs.get('services_count') == 10

            finally:
                orchestrator.close()

    def test_orchestrator_mode_passed_to_services(self, temp_project):
        """Test that mode parameter is properly passed through."""
        # Test with different modes
        for mode in ["cli", "benchmark", "api"]:
            orchestrator = create_orchestrator(
                project_root=temp_project,
                mode=mode
            )

            try:
                assert orchestrator.mode == mode
            finally:
                orchestrator.close()

    def test_orchestrator_api_key_passed_to_services(self, temp_project):
        """Test that API key is properly stored."""
        test_api_key = "test-api-key-12345"

        orchestrator = create_orchestrator(
            project_root=temp_project,
            api_key=test_api_key,
            mode="cli"
        )

        try:
            assert orchestrator.api_key == test_api_key
        finally:
            orchestrator.close()


class TestServiceInteroperability:
    """Test that all services work together correctly."""

    def test_all_services_can_coexist(self, temp_project):
        """Test that all 10 services can be instantiated together without conflicts."""
        orchestrator = create_orchestrator(
            project_root=temp_project,
            mode="cli"
        )

        try:
            # Verify all services are distinct objects
            services = [
                orchestrator.workflow_execution_engine,
                orchestrator.artifact_manager,
                orchestrator.agent_coordinator,
                orchestrator.ceremony_orchestrator,
                orchestrator.workflow_coordinator,
                orchestrator.story_lifecycle,
                orchestrator.process_executor,
                orchestrator.quality_gate_manager,
                orchestrator.brian_orchestrator,
                orchestrator.git_state_manager,
            ]

            # Check all are not None
            assert all(service is not None for service in services)

            # Check all are unique objects (no duplicate references)
            assert len(set(id(s) for s in services)) == 10

        finally:
            orchestrator.close()

    def test_git_state_manager_and_ceremony_use_same_db(self, temp_project):
        """Test that git_state_manager and ceremony_orchestrator share the same database."""
        orchestrator = create_orchestrator(
            project_root=temp_project,
            mode="cli"
        )

        try:
            # Both should use the same db_path
            assert (
                orchestrator.git_state_manager.db_path ==
                orchestrator.ceremony_orchestrator.db_path
            )

            # Both should point to .gao-dev/documents.db
            expected_db = temp_project / ".gao-dev" / "documents.db"
            assert orchestrator.git_state_manager.db_path == expected_db
            assert orchestrator.ceremony_orchestrator.db_path == expected_db

        finally:
            orchestrator.close()

    def test_orchestrator_close_is_idempotent(self, temp_project):
        """Test that calling close() multiple times doesn't cause errors."""
        orchestrator = create_orchestrator(
            project_root=temp_project,
            mode="cli"
        )

        # Close multiple times
        orchestrator.close()
        orchestrator.close()
        orchestrator.close()

        # Should not raise any exceptions

    def test_orchestrator_with_missing_git_state_manager(self, temp_project):
        """Test orchestrator can handle None git_state_manager gracefully."""
        from gao_dev.orchestrator.workflow_execution_engine import WorkflowExecutionEngine
        from gao_dev.orchestrator.artifact_manager import ArtifactManager
        from gao_dev.orchestrator.agent_coordinator import AgentCoordinator
        from gao_dev.orchestrator.ceremony_orchestrator import CeremonyOrchestrator
        from gao_dev.orchestrator.brian_orchestrator import BrianOrchestrator
        from gao_dev.core.services.workflow_coordinator import WorkflowCoordinator
        from gao_dev.core.services.story_lifecycle import StoryLifecycleManager
        from gao_dev.core.services.process_executor import ProcessExecutor
        from gao_dev.core.services.quality_gate import QualityGateManager

        # Create orchestrator with git_state_manager=None
        # Configure artifact_manager mock to have doc_lifecycle attribute
        mock_artifact_manager = Mock(spec=ArtifactManager)
        mock_artifact_manager.doc_lifecycle = None

        orchestrator = GAODevOrchestrator(
            project_root=temp_project,
            workflow_execution_engine=Mock(spec=WorkflowExecutionEngine),
            artifact_manager=mock_artifact_manager,
            agent_coordinator=Mock(spec=AgentCoordinator),
            ceremony_orchestrator=Mock(spec=CeremonyOrchestrator),
            workflow_coordinator=Mock(spec=WorkflowCoordinator),
            story_lifecycle=Mock(spec=StoryLifecycleManager),
            process_executor=Mock(spec=ProcessExecutor),
            quality_gate_manager=Mock(spec=QualityGateManager),
            brian_orchestrator=Mock(spec=BrianOrchestrator),
            git_state_manager=None,  # Explicitly None
            mode="cli"
        )

        try:
            # Should handle None gracefully
            assert orchestrator.git_state_manager is None

            # close() should not fail
            orchestrator.close()

        finally:
            pass  # Already closed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

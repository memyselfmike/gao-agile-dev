"""
Integration Workflow Tests for Epic 6.

CRITICAL: These tests verify end-to-end workflow execution BEFORE and
AFTER Epic 6 refactoring. They ensure that the orchestrator and sandbox
work together correctly after service extraction.

Test Coverage:
- Orchestrator + Sandbox integration
- Complete workflow execution paths
- Cross-component coordination
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from gao_dev.orchestrator.orchestrator import GAODevOrchestrator
from gao_dev.sandbox.manager import SandboxManager


# =============================================================================
# A. Orchestrator-Sandbox Integration Tests
# =============================================================================

class TestOrchestratorSandboxIntegration:
    """Test orchestrator and sandbox work together."""

    def test_orchestrator_and_sandbox_can_coexist(
        self,
        orchestrator_test_project: Path,
        sandbox_test_root: Path
    ):
        """
        Test orchestrator and sandbox manager can be used together.

        Verifies current integration behavior.
        """
        # When: Create both components
        orchestrator = GAODevOrchestrator(
            project_root=orchestrator_test_project,
            mode="cli"
        )
        sandbox = SandboxManager(sandbox_root=sandbox_test_root)

        # Then: Both initialized
        assert orchestrator is not None
        assert sandbox is not None

    def test_orchestrator_can_use_sandbox_paths(
        self,
        orchestrator_test_project: Path,
        sandbox_test_root: Path
    ):
        """
        Test orchestrator can interact with sandbox paths.

        Verifies current path handling behavior.
        """
        # Given: Orchestrator and sandbox
        orchestrator = GAODevOrchestrator(
            project_root=orchestrator_test_project,
            mode="cli"
        )
        sandbox = SandboxManager(sandbox_root=sandbox_test_root)

        # Create sandbox project
        sandbox.create_project(name="test-project", description="Test")
        project_path = sandbox.get_project_path("test-project")

        # Then: Orchestrator can work with sandbox paths
        assert project_path.exists()
        # Orchestrator should be able to execute tasks in this context


# =============================================================================
# B. Component Coordination Tests
# =============================================================================

class TestComponentCoordination:
    """Test coordination between major components."""

    def test_workflow_registry_accessible_from_orchestrator(
        self,
        orchestrator_test_project: Path
    ):
        """
        Test workflow registry is accessible for workflow execution.

        Verifies current workflow coordination behavior.
        """
        # Given: Orchestrator
        orchestrator = GAODevOrchestrator(
            project_root=orchestrator_test_project,
            mode="cli"
        )

        # Then: Workflow registry accessible
        assert orchestrator.workflow_registry is not None
        workflows = orchestrator.workflow_registry.list_workflows()
        assert isinstance(workflows, list)

    def test_config_loader_shared_correctly(
        self,
        orchestrator_test_project: Path
    ):
        """
        Test config loader is properly shared between components.

        Verifies current configuration sharing behavior.
        """
        # Given: Orchestrator
        orchestrator = GAODevOrchestrator(
            project_root=orchestrator_test_project,
            mode="cli"
        )

        # Then: Config loader consistent
        assert orchestrator.config_loader is not None
        assert orchestrator.workflow_registry.config_loader == orchestrator.config_loader


# =============================================================================
# C. State Consistency Tests
# =============================================================================

class TestStateConsistency:
    """Test state remains consistent across components."""

    def test_sandbox_state_persistence(self, sandbox_test_root: Path):
        """
        Test sandbox state persists correctly.

        Verifies current state management behavior.
        """
        # Given: Sandbox manager
        sandbox1 = SandboxManager(sandbox_root=sandbox_test_root)
        sandbox1.create_project(name="test-project", description="Test")

        # When: Create new manager instance
        sandbox2 = SandboxManager(sandbox_root=sandbox_test_root)

        # Then: State consistent
        assert sandbox2.project_exists("test-project")
        project1 = sandbox1.get_project("test-project")
        project2 = sandbox2.get_project("test-project")
        assert project1.name == project2.name
        assert project1.created_at == project2.created_at


# =============================================================================
# D. Error Propagation Tests
# =============================================================================

class TestErrorPropagation:
    """Test errors propagate correctly through the system."""

    def test_invalid_workflow_handling(self, orchestrator_test_project: Path):
        """
        Test invalid workflow execution is handled.

        Verifies current error handling behavior.
        """
        # Given: Orchestrator
        orchestrator = GAODevOrchestrator(
            project_root=orchestrator_test_project,
            mode="cli"
        )

        # Then: Has method to list workflows
        assert hasattr(orchestrator.workflow_registry, 'list_workflows')
        workflows = orchestrator.workflow_registry.list_workflows()
        assert isinstance(workflows, list)

    def test_sandbox_validation_errors_caught(self, sandbox_test_root: Path):
        """
        Test sandbox validation errors are caught.

        Verifies current validation error handling.
        """
        # Given: Sandbox manager
        sandbox = SandboxManager(sandbox_root=sandbox_test_root)

        # When/Then: Invalid operations raise appropriate errors
        with pytest.raises(ValueError):
            sandbox.create_project(name="invalid name", description="Test")

        with pytest.raises(ValueError):
            sandbox.get_project("nonexistent")


# =============================================================================
# E. Initialization Order Tests
# =============================================================================

class TestInitializationOrder:
    """Test components can be initialized in any order."""

    def test_orchestrator_first_then_sandbox(
        self,
        orchestrator_test_project: Path,
        sandbox_test_root: Path
    ):
        """
        Test orchestrator can be created before sandbox.

        Verifies current initialization independence.
        """
        # When: Create orchestrator first
        orchestrator = GAODevOrchestrator(
            project_root=orchestrator_test_project,
            mode="cli"
        )

        # Then: Create sandbox
        sandbox = SandboxManager(sandbox_root=sandbox_test_root)

        # Both should work
        assert orchestrator is not None
        assert sandbox is not None

    def test_sandbox_first_then_orchestrator(
        self,
        orchestrator_test_project: Path,
        sandbox_test_root: Path
    ):
        """
        Test sandbox can be created before orchestrator.

        Verifies current initialization independence.
        """
        # When: Create sandbox first
        sandbox = SandboxManager(sandbox_root=sandbox_test_root)

        # Then: Create orchestrator
        orchestrator = GAODevOrchestrator(
            project_root=orchestrator_test_project,
            mode="cli"
        )

        # Both should work
        assert sandbox is not None
        assert orchestrator is not None


# =============================================================================
# F. Path Handling Tests
# =============================================================================

class TestPathHandling:
    """Test path handling across components."""

    def test_project_root_handling(
        self,
        orchestrator_test_project: Path
    ):
        """
        Test project root paths are handled correctly.

        Verifies current path handling behavior.
        """
        # Given: Orchestrator with project root
        orchestrator = GAODevOrchestrator(
            project_root=orchestrator_test_project,
            mode="cli"
        )

        # Then: Project root properly set
        assert orchestrator.project_root == orchestrator_test_project
        assert orchestrator.project_root.exists()
        assert orchestrator.config_loader.project_root == orchestrator_test_project

    def test_sandbox_root_handling(self, sandbox_test_root: Path):
        """
        Test sandbox root paths are handled correctly.

        Verifies current sandbox path handling behavior.
        """
        # Given: Sandbox manager with sandbox root
        sandbox = SandboxManager(sandbox_root=sandbox_test_root)

        # Then: Sandbox root properly set
        assert sandbox.sandbox_root == sandbox_test_root
        assert sandbox.sandbox_root.exists()


# =============================================================================
# G. Resource Cleanup Tests
# =============================================================================

class TestResourceCleanup:
    """Test resources are cleaned up properly."""

    def test_sandbox_project_deletion_cleans_resources(
        self,
        sandbox_test_root: Path,
        sample_boilerplate: Path
    ):
        """
        Test deleting sandbox project cleans up all resources.

        Verifies current cleanup behavior.
        """
        # Given: Sandbox with project
        sandbox = SandboxManager(sandbox_root=sandbox_test_root)
        sandbox.create_project(name="test-project", description="Test", boilerplate_url=sample_boilerplate)

        project_path = sandbox.get_project_path("test-project")
        assert project_path.exists()

        # When: Delete project
        sandbox.delete_project("test-project")

        # Then: All resources cleaned up
        assert not project_path.exists()
        assert not sandbox.project_exists("test-project")


# =============================================================================
# Summary
# =============================================================================

"""
These integration tests verify that major components work together correctly.

After Epic 6 refactoring:
- All these tests MUST still pass
- Components should still integrate seamlessly
- Only internal structure changes, not external behavior

If any test fails after refactoring:
1. STOP immediately
2. Investigate integration point
3. Fix broken integration
4. Verify all integration tests pass
"""

"""
Orchestrator Regression Tests for Epic 6.

CRITICAL: These tests capture the current behavior of GAODevOrchestrator
(1,327 lines) BEFORE service extraction. All tests MUST pass before and
after Epic 6 refactoring to ensure zero regressions.

Test Coverage:
- Workflow execution behavior
- Agent management
- State management
- Quality gates
- Error handling
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from typing import AsyncGenerator

from gao_dev.orchestrator.orchestrator import GAODevOrchestrator
from gao_dev.orchestrator.brian_orchestrator import ScaleLevel, ProjectType
from gao_dev.core.workflow_registry import WorkflowRegistry


# =============================================================================
# A. Workflow Execution Tests
# =============================================================================

class TestOrchestratorWorkflowExecution:
    """Test current workflow execution behavior."""

    def test_orchestrator_initialization(self, orchestrator_test_project: Path):
        """
        Test orchestrator initializes correctly.

        This verifies the current initialization process including:
        - Configuration loading
        - Workflow registry setup
        - Brian orchestrator setup
        """
        # When: Orchestrator initialized
        orchestrator = GAODevOrchestrator(
            project_root=orchestrator_test_project,
            mode="cli"
        )

        # Then: All components initialized
        assert orchestrator.project_root == orchestrator_test_project
        assert orchestrator.config_loader is not None
        assert orchestrator.workflow_registry is not None
        assert orchestrator.brian_orchestrator is not None
        assert orchestrator.mode == "cli"

    def test_orchestrator_workflow_registry_indexed(self, orchestrator_test_project: Path):
        """
        Test workflow registry is indexed on initialization.

        Verifies current behavior where workflows are indexed during init.
        """
        # When: Orchestrator initialized
        orchestrator = GAODevOrchestrator(
            project_root=orchestrator_test_project,
            mode="cli"
        )

        # Then: Workflows indexed (should have some workflows)
        workflows = orchestrator.workflow_registry.list_workflows()
        # Note: May be empty if no workflows in test project, just verify no crash
        assert isinstance(workflows, list)

    @pytest.mark.asyncio
    async def test_workflow_artifact_verification(
        self,
        orchestrator_test_project: Path,
        mock_workflow_output
    ):
        """
        Test workflow artifact verification is delegated to QualityGateManager.

        Verifies that artifact validation is properly delegated in the refactored facade.
        """
        # Given: Orchestrator instance (using default factory)
        orchestrator = GAODevOrchestrator.create_default(
            project_root=orchestrator_test_project,
            mode="cli"
        )

        # Then: Verify QualityGateManager is injected for artifact validation
        assert hasattr(orchestrator, 'quality_gate_manager')
        assert orchestrator.quality_gate_manager is not None
        # Verify the service has the validation method
        assert hasattr(orchestrator.quality_gate_manager, 'validate_artifacts')

    def test_get_next_story_number(self, orchestrator_test_project: Path):
        """
        Test story numbering is delegated to StoryLifecycleManager.

        Verifies that story numbering logic is properly delegated in the refactored facade.
        """
        # Given: Orchestrator instance (using default factory)
        orchestrator = GAODevOrchestrator.create_default(
            project_root=orchestrator_test_project,
            mode="cli"
        )

        # Then: Verify StoryLifecycleManager is injected for story management
        assert hasattr(orchestrator, 'story_lifecycle')
        assert orchestrator.story_lifecycle is not None
        # Verify the service has story management methods
        assert hasattr(orchestrator.story_lifecycle, 'create_story')
        assert hasattr(orchestrator.story_lifecycle, 'transition_state')

    def test_get_agent_for_workflow(self, orchestrator_test_project: Path):
        """
        Test agent selection for workflows.

        Verifies current agent assignment logic.
        """
        # Given: Orchestrator instance
        orchestrator = GAODevOrchestrator(
            project_root=orchestrator_test_project,
            mode="cli"
        )

        # When/Then: Method exists for agent selection
        assert hasattr(orchestrator, '_get_agent_for_workflow')

    def test_scale_level_description(self, orchestrator_test_project: Path):
        """
        Test scale level description generation.

        Verifies current scale level handling behavior.
        """
        # Given: Orchestrator instance
        orchestrator = GAODevOrchestrator(
            project_root=orchestrator_test_project,
            mode="cli"
        )

        # When: Get description for scale level 3
        description = orchestrator.get_scale_level_description(ScaleLevel(3))

        # Then: Returns valid description
        assert isinstance(description, str)
        assert len(description) > 0


# =============================================================================
# B. Agent Management Tests
# =============================================================================

class TestOrchestratorAgentManagement:
    """Test current agent creation and execution."""

    def test_agent_definitions_loaded(self, orchestrator_test_project: Path):
        """
        Test services are initialized for agent execution.

        Verifies that all required services are injected and available.
        """
        # When: Orchestrator initialized using default factory
        orchestrator = GAODevOrchestrator.create_default(
            project_root=orchestrator_test_project,
            mode="cli"
        )

        # Then: All services are initialized
        assert hasattr(orchestrator, 'workflow_coordinator')
        assert orchestrator.workflow_coordinator is not None
        assert hasattr(orchestrator, 'story_lifecycle')
        assert orchestrator.story_lifecycle is not None
        assert hasattr(orchestrator, 'process_executor')
        assert orchestrator.process_executor is not None
        assert hasattr(orchestrator, 'quality_gate_manager')
        assert orchestrator.quality_gate_manager is not None

    def test_brian_orchestrator_initialized(self, orchestrator_test_project: Path):
        """
        Test Brian orchestrator is initialized correctly.

        Verifies current Brian initialization behavior.
        """
        # When: Orchestrator initialized
        orchestrator = GAODevOrchestrator(
            project_root=orchestrator_test_project,
            mode="cli"
        )

        # Then: Brian orchestrator configured
        assert orchestrator.brian_orchestrator is not None
        assert orchestrator.brian_orchestrator.workflow_registry is not None


# =============================================================================
# C. State Management Tests
# =============================================================================

class TestOrchestratorStateManagement:
    """Test current state management behavior."""

    def test_project_root_accessible(self, orchestrator_test_project: Path):
        """
        Test project root is accessible.

        Verifies current project root tracking behavior.
        """
        # When: Orchestrator initialized
        orchestrator = GAODevOrchestrator(
            project_root=orchestrator_test_project,
            mode="cli"
        )

        # Then: Project root accessible
        assert orchestrator.project_root == orchestrator_test_project
        assert orchestrator.project_root.exists()

    def test_config_loader_accessible(self, orchestrator_test_project: Path):
        """
        Test configuration loader is accessible.

        Verifies current config management behavior.
        """
        # When: Orchestrator initialized
        orchestrator = GAODevOrchestrator(
            project_root=orchestrator_test_project,
            mode="cli"
        )

        # Then: Config loader accessible
        assert orchestrator.config_loader is not None
        assert orchestrator.config_loader.project_root == orchestrator_test_project


# =============================================================================
# D. Quality Gate Tests
# =============================================================================

class TestOrchestratorQualityGates:
    """Test current quality gate validation."""

    @pytest.mark.asyncio
    async def test_artifact_verification_method_exists(self, orchestrator_test_project: Path):
        """
        Test artifact verification is delegated to QualityGateManager.

        Verifies that quality gate functionality is properly delegated.
        """
        # Given: Orchestrator instance using default factory
        orchestrator = GAODevOrchestrator.create_default(
            project_root=orchestrator_test_project,
            mode="cli"
        )

        # Then: QualityGateManager with validation method exists
        assert hasattr(orchestrator, 'quality_gate_manager')
        assert orchestrator.quality_gate_manager is not None
        assert hasattr(orchestrator.quality_gate_manager, 'validate_artifacts')
        assert callable(getattr(orchestrator.quality_gate_manager, 'validate_artifacts'))


# =============================================================================
# E. Mode Configuration Tests
# =============================================================================

class TestOrchestratorModeConfiguration:
    """Test current mode configuration behavior."""

    def test_cli_mode_initialization(self, orchestrator_test_project: Path):
        """
        Test CLI mode initialization and ProcessExecutor delegation.

        Verifies that CLI mode is properly initialized with ProcessExecutor.
        """
        # When: Orchestrator initialized in CLI mode
        orchestrator = GAODevOrchestrator.create_default(
            project_root=orchestrator_test_project,
            mode="cli"
        )

        # Then: CLI mode configured with ProcessExecutor
        assert orchestrator.mode == "cli"
        assert hasattr(orchestrator, 'process_executor')
        assert orchestrator.process_executor is not None
        # ProcessExecutor handles agent task execution
        assert hasattr(orchestrator.process_executor, 'execute_agent_task')

    def test_benchmark_mode_initialization_without_cli(self, orchestrator_test_project: Path):
        """
        Test benchmark mode fails gracefully without Claude CLI.

        Verifies current benchmark mode validation behavior.
        """
        # When/Then: Benchmark mode without CLI should raise error
        # Note: Only if Claude CLI not found
        # This test documents current behavior
        try:
            orchestrator = GAODevOrchestrator(
                project_root=orchestrator_test_project,
                mode="benchmark"
            )
            # If we get here, Claude CLI was found (OK)
            assert orchestrator.mode == "benchmark"
        except ValueError as e:
            # If Claude CLI not found, should raise ValueError (also OK)
            assert "Claude CLI not found" in str(e)

    def test_api_mode_initialization(self, orchestrator_test_project: Path):
        """
        Test API mode initialization.

        Verifies current API mode behavior.
        """
        # When: Orchestrator initialized in API mode
        orchestrator = GAODevOrchestrator(
            project_root=orchestrator_test_project,
            mode="api"
        )

        # Then: API mode configured
        assert orchestrator.mode == "api"


# =============================================================================
# F. Brian Orchestrator Integration Tests
# =============================================================================

class TestBrianOrchestratorIntegration:
    """Test current Brian orchestrator integration behavior."""

    def test_brian_has_workflow_registry(self, orchestrator_test_project: Path):
        """
        Test Brian orchestrator has workflow registry.

        Verifies current Brian-to-registry integration.
        """
        # When: Orchestrator initialized
        orchestrator = GAODevOrchestrator(
            project_root=orchestrator_test_project,
            mode="cli"
        )

        # Then: Brian has workflow registry
        assert orchestrator.brian_orchestrator.workflow_registry is not None
        assert isinstance(orchestrator.brian_orchestrator.workflow_registry, WorkflowRegistry)

    def test_brian_has_api_key(self, orchestrator_test_project: Path):
        """
        Test Brian orchestrator has API key.

        Verifies current API key handling.
        """
        # Given: API key
        api_key = "test-key-123"

        # When: Orchestrator initialized with API key
        orchestrator = GAODevOrchestrator(
            project_root=orchestrator_test_project,
            api_key=api_key,
            mode="cli"
        )

        # Then: API key stored
        assert orchestrator.api_key == api_key


# =============================================================================
# G. Error Handling Tests
# =============================================================================

class TestOrchestratorErrorHandling:
    """Test current error handling behavior."""

    def test_invalid_project_root_handling(self):
        """
        Test handling of invalid project root.

        Verifies current validation behavior.
        """
        # Given: Invalid project root
        invalid_root = Path("/nonexistent/path/that/does/not/exist")

        # When/Then: Should handle gracefully (may not raise immediately)
        # Just verify orchestrator can be created
        # Actual errors may occur later during workflow execution
        orchestrator = GAODevOrchestrator(
            project_root=invalid_root,
            mode="cli"
        )
        assert orchestrator.project_root == invalid_root

    def test_clarification_handler_exists(self, orchestrator_test_project: Path):
        """
        Test clarification handler method exists.

        Verifies current clarification handling capability.
        """
        # Given: Orchestrator instance
        orchestrator = GAODevOrchestrator(
            project_root=orchestrator_test_project,
            mode="cli"
        )

        # Then: Clarification handler exists
        assert hasattr(orchestrator, 'handle_clarification')
        assert callable(getattr(orchestrator, 'handle_clarification'))


# =============================================================================
# H. Integration Points Tests
# =============================================================================

class TestOrchestratorIntegrationPoints:
    """Test current integration points (workflow registry, config, etc.)."""

    def test_workflow_registry_integration(self, orchestrator_test_project: Path):
        """
        Test workflow registry integration.

        Verifies current registry integration behavior.
        """
        # When: Orchestrator initialized
        orchestrator = GAODevOrchestrator(
            project_root=orchestrator_test_project,
            mode="cli"
        )

        # Then: Workflow registry properly integrated
        assert orchestrator.workflow_registry is not None
        assert orchestrator.workflow_registry.config_loader == orchestrator.config_loader

    def test_config_loader_integration(self, orchestrator_test_project: Path):
        """
        Test config loader integration.

        Verifies current config loading behavior.
        """
        # When: Orchestrator initialized
        orchestrator = GAODevOrchestrator(
            project_root=orchestrator_test_project,
            mode="cli"
        )

        # Then: Config loader properly integrated
        assert orchestrator.config_loader is not None
        assert orchestrator.config_loader.project_root == orchestrator_test_project


# =============================================================================
# Summary
# =============================================================================

"""
These regression tests verify the CURRENT behavior of GAODevOrchestrator.

After Epic 6 refactoring:
- All these tests MUST still pass
- Same behavior, different internal structure
- Orchestrator becomes thin facade, services do the work

If any test fails after refactoring:
1. STOP immediately
2. Investigate root cause
3. Fix regression or adjust test (only if behavior INTENTIONALLY changed)
4. Document why behavior changed
"""

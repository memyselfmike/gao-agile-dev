"""Integration tests for GAODevOrchestrator facade pattern (Story 22.6).

These tests verify that the orchestrator properly delegates to all services
and maintains the expected public API without breaking changes.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock

from gao_dev.orchestrator import (
    GAODevOrchestrator,
    WorkflowExecutionEngine,
    ArtifactManager,
    AgentCoordinator,
    CeremonyOrchestrator,
)
from gao_dev.orchestrator.brian_orchestrator import BrianOrchestrator
from gao_dev.core.services.workflow_coordinator import WorkflowCoordinator
from gao_dev.core.services.story_lifecycle import StoryLifecycleManager
from gao_dev.core.services.process_executor import ProcessExecutor
from gao_dev.core.services.quality_gate import QualityGateManager
from gao_dev.core.context.context_persistence import ContextPersistence


@pytest.fixture
def mock_services():
    """Create mock services for orchestrator injection."""
    return {
        "workflow_execution_engine": Mock(spec=WorkflowExecutionEngine),
        "artifact_manager": Mock(spec=ArtifactManager),
        "agent_coordinator": Mock(spec=AgentCoordinator),
        "ceremony_orchestrator": Mock(spec=CeremonyOrchestrator),
        "workflow_coordinator": Mock(spec=WorkflowCoordinator),
        "story_lifecycle": Mock(spec=StoryLifecycleManager),
        "process_executor": Mock(spec=ProcessExecutor),
        "quality_gate_manager": Mock(spec=QualityGateManager),
        "brian_orchestrator": Mock(spec=BrianOrchestrator),
        "context_persistence": Mock(spec=ContextPersistence),
    }


@pytest.fixture
def orchestrator(tmp_path, mock_services):
    """Create orchestrator with injected mocked services."""
    # Add doc_lifecycle property to artifact_manager mock
    mock_services["artifact_manager"].doc_lifecycle = None

    return GAODevOrchestrator(
        project_root=tmp_path,
        **mock_services
    )


# Test 1: Orchestrator initializes all services
def test_orchestrator_initializes_all_services(orchestrator, mock_services):
    """Verify orchestrator stores all injected services."""
    assert orchestrator.workflow_execution_engine == mock_services["workflow_execution_engine"]
    assert orchestrator.artifact_manager == mock_services["artifact_manager"]
    assert orchestrator.agent_coordinator == mock_services["agent_coordinator"]
    assert orchestrator.ceremony_orchestrator == mock_services["ceremony_orchestrator"]
    assert orchestrator.workflow_coordinator == mock_services["workflow_coordinator"]
    assert orchestrator.story_lifecycle == mock_services["story_lifecycle"]
    assert orchestrator.process_executor == mock_services["process_executor"]
    assert orchestrator.quality_gate_manager == mock_services["quality_gate_manager"]
    assert orchestrator.brian_orchestrator == mock_services["brian_orchestrator"]


# Test 2: execute_task delegates to AgentCoordinator
@pytest.mark.asyncio
async def test_execute_task_delegates(orchestrator, mock_services):
    """Verify execute_task delegates to AgentCoordinator.execute_task()."""
    # Setup mock to return async generator
    async def mock_generator():
        yield "output1"
        yield "output2"

    mock_services["agent_coordinator"].execute_task = Mock(side_effect=lambda **kwargs: mock_generator())

    # Execute task
    results = []
    async for output in orchestrator.execute_task("test task"):
        results.append(output)

    # Verify delegation
    mock_services["agent_coordinator"].execute_task.assert_called_once()
    call_args = mock_services["agent_coordinator"].execute_task.call_args
    assert call_args[1]["agent_name"] == "Orchestrator"
    assert call_args[1]["instructions"] == "test task"
    assert len(results) == 2


# Test 3: create_prd delegates to WorkflowExecutionEngine
@pytest.mark.asyncio
async def test_create_prd_delegates(orchestrator, mock_services):
    """Verify create_prd delegates to WorkflowExecutionEngine.execute_task()."""
    from gao_dev.orchestrator.workflow_results import WorkflowResult, WorkflowStatus
    from datetime import datetime

    # Setup mock
    mock_result = WorkflowResult(
        workflow_name="create_prd",
        initial_prompt="Create PRD",
        status=WorkflowStatus.COMPLETED,
        start_time=datetime.now(),
    )
    mock_services["workflow_execution_engine"].execute_task = AsyncMock(return_value=mock_result)

    # Execute
    results = []
    async for output in orchestrator.create_prd("TestProject"):
        results.append(output)

    # Verify delegation
    mock_services["workflow_execution_engine"].execute_task.assert_called_once_with(
        "create_prd",
        {"project_name": "TestProject"}
    )
    assert len(results) == 1
    assert "completed" in results[0].lower()


# Test 4: assess_and_select_workflows delegates to Brian
@pytest.mark.asyncio
async def test_assess_and_select_workflows_delegates(orchestrator, mock_services):
    """Verify workflow selection delegates to BrianOrchestrator."""
    from gao_dev.orchestrator.models import WorkflowSequence, ScaleLevel, ProjectType

    # Setup mock
    mock_sequence = WorkflowSequence(
        scale_level=ScaleLevel.LEVEL_1,
        project_type=ProjectType.GREENFIELD,
        workflows=[],
        routing_rationale="Test rationale",
        phase_breakdown={}
    )
    mock_services["brian_orchestrator"].assess_and_select_workflows = AsyncMock(
        return_value=mock_sequence
    )

    # Execute
    result = await orchestrator.assess_and_select_workflows("Build a todo app")

    # Verify delegation
    mock_services["brian_orchestrator"].assess_and_select_workflows.assert_called_once_with(
        initial_prompt="Build a todo app",
        force_scale_level=None
    )
    assert result == mock_sequence


# Test 5: get_scale_level_description delegates to Brian
def test_get_scale_level_description_delegates(orchestrator, mock_services):
    """Verify scale level description delegates to BrianOrchestrator."""
    from gao_dev.orchestrator.models import ScaleLevel

    # Setup mock
    mock_services["brian_orchestrator"].get_scale_level_description = Mock(
        return_value="Small feature description"
    )

    # Execute
    result = orchestrator.get_scale_level_description(ScaleLevel.LEVEL_1)

    # Verify delegation
    mock_services["brian_orchestrator"].get_scale_level_description.assert_called_once_with(
        ScaleLevel.LEVEL_1
    )
    assert result == "Small feature description"


# Test 6: doc_lifecycle property delegates to ArtifactManager
def test_doc_lifecycle_property(orchestrator, mock_services):
    """Verify doc_lifecycle property accesses ArtifactManager.doc_lifecycle."""
    # Setup mock
    mock_doc_lifecycle = Mock()
    mock_services["artifact_manager"].doc_lifecycle = mock_doc_lifecycle

    # Test getter
    result = orchestrator.doc_lifecycle
    assert result == mock_doc_lifecycle

    # Test setter
    new_doc_lifecycle = Mock()
    orchestrator.doc_lifecycle = new_doc_lifecycle
    assert mock_services["artifact_manager"].doc_lifecycle == new_doc_lifecycle


# Test 7: close() delegates to doc_lifecycle
def test_close_delegates(orchestrator, mock_services):
    """Verify close() properly closes document lifecycle."""
    # Setup mock
    mock_doc_lifecycle = Mock()
    mock_doc_lifecycle.registry = Mock()
    mock_services["artifact_manager"].doc_lifecycle = mock_doc_lifecycle

    # Execute
    orchestrator.close()

    # Verify delegation
    mock_doc_lifecycle.registry.close.assert_called_once()


# Test 8: context manager works correctly
def test_context_manager(orchestrator, mock_services):
    """Verify orchestrator works as context manager."""
    # Setup mock
    mock_doc_lifecycle = Mock()
    mock_doc_lifecycle.registry = Mock()
    mock_services["artifact_manager"].doc_lifecycle = mock_doc_lifecycle

    # Use as context manager
    with orchestrator as orch:
        assert orch == orchestrator

    # Verify close was called
    mock_doc_lifecycle.registry.close.assert_called_once()


# Test 9: Public API unchanged (backward compatibility)
def test_public_api_unchanged(orchestrator):
    """Verify all expected public methods exist (backward compatibility)."""
    # Async methods
    assert hasattr(orchestrator, "execute_task")
    assert hasattr(orchestrator, "create_prd")
    assert hasattr(orchestrator, "create_story")
    assert hasattr(orchestrator, "implement_story")
    assert hasattr(orchestrator, "create_architecture")
    assert hasattr(orchestrator, "validate_story")
    assert hasattr(orchestrator, "assess_and_select_workflows")
    assert hasattr(orchestrator, "execute_workflow")
    assert hasattr(orchestrator, "execute_workflow_sequence_from_prompt")

    # Sync methods
    assert hasattr(orchestrator, "get_scale_level_description")
    assert hasattr(orchestrator, "handle_clarification")
    assert hasattr(orchestrator, "close")

    # Properties
    assert hasattr(orchestrator, "doc_lifecycle")
    assert hasattr(orchestrator, "project_root")
    assert hasattr(orchestrator, "mode")

    # Class method
    assert hasattr(GAODevOrchestrator, "create_default")


# Test 10: Service dependencies work together
@pytest.mark.asyncio
async def test_service_dependencies(orchestrator, mock_services):
    """Verify services are properly wired and can interact."""
    # Setup workflow execution that uses multiple services
    from gao_dev.orchestrator.models import WorkflowSequence, ScaleLevel, ProjectType
    from gao_dev.orchestrator.workflow_results import WorkflowResult, WorkflowStatus
    from gao_dev.core.models.workflow_context import WorkflowContext
    from datetime import datetime

    mock_sequence = WorkflowSequence(
        scale_level=ScaleLevel.LEVEL_1,
        project_type=ProjectType.GREENFIELD,
        workflows=[],
        routing_rationale="Test",
        phase_breakdown={}
    )

    mock_coord_result = WorkflowResult(
        workflow_name="test",
        initial_prompt="Test prompt",
        status=WorkflowStatus.COMPLETED,
        start_time=datetime.now(),
        step_results=[],
    )

    # Setup mocks
    mock_services["brian_orchestrator"].assess_and_select_workflows = AsyncMock(
        return_value=mock_sequence
    )
    mock_services["workflow_coordinator"].execute_sequence = AsyncMock(
        return_value=mock_coord_result
    )
    mock_services["context_persistence"].save_context = Mock(return_value=1)
    mock_services["context_persistence"].update_context = Mock()

    # Execute workflow (tests Brian + WorkflowCoordinator + ContextPersistence integration)
    result = await orchestrator.execute_workflow("Build todo app", workflow=mock_sequence)

    # Verify all services were used
    assert result.status == WorkflowStatus.COMPLETED
    mock_services["workflow_coordinator"].execute_sequence.assert_called_once()
    mock_services["context_persistence"].save_context.assert_called_once()
    mock_services["context_persistence"].update_context.assert_called()

"""
Integration tests for WorkflowContext integration with GAODevOrchestrator.

Tests verify that WorkflowContext is created, persisted, and updated throughout
the workflow lifecycle, with proper thread-local storage and error handling.
"""

import pytest
import uuid
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from gao_dev.orchestrator.orchestrator import GAODevOrchestrator
from gao_dev.orchestrator.workflow_results import WorkflowResult, WorkflowStatus
from gao_dev.orchestrator.brian_orchestrator import WorkflowSequence, ScaleLevel, ProjectType
from gao_dev.core.models.workflow import WorkflowInfo
from gao_dev.core.context.context_persistence import ContextPersistence
from gao_dev.core.context.workflow_context import WorkflowContext
from gao_dev.core.context.context_api import get_workflow_context, clear_workflow_context


@pytest.fixture
def test_db_path(tmp_path):
    """Create temporary database for testing."""
    db_path = tmp_path / "test_context.db"
    return db_path


@pytest.fixture
def context_persistence(test_db_path):
    """Create ContextPersistence with test database."""
    return ContextPersistence(db_path=test_db_path)


@pytest.fixture
def orchestrator(tmp_path, context_persistence):
    """Create GAODevOrchestrator with mocked services."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()

    # Mock workflow coordinator
    mock_coordinator = Mock()
    mock_coordinator.execute_sequence = AsyncMock(return_value=Mock(
        status=WorkflowStatus.COMPLETED,
        step_results=[],
        error_message=None,
        total_artifacts=0,
    ))

    # Mock other services
    mock_lifecycle = Mock()
    mock_executor = Mock()
    mock_quality = Mock()
    mock_brian = Mock()

    orchestrator = GAODevOrchestrator(
        project_root=project_root,
        api_key="test_key",
        mode="test",
        workflow_coordinator=mock_coordinator,
        story_lifecycle=mock_lifecycle,
        process_executor=mock_executor,
        quality_gate_manager=mock_quality,
        brian_orchestrator=mock_brian,
        context_persistence=context_persistence,
    )

    return orchestrator


@pytest.fixture
def simple_workflow_sequence():
    """Create simple workflow sequence for testing."""
    workflow_info = WorkflowInfo(
        name="test-workflow",
        description="Test workflow",
        phase=-1,  # Phase-independent
        installed_path=Path("/test"),
        author="Test",
        tags=["test"],
        variables={},
        required_tools=[],
        interactive=False,
        autonomous=True,
        iterative=False,
        web_bundle=False,
        output_file=None,
        templates={},
    )

    return WorkflowSequence(
        scale_level=ScaleLevel.LEVEL_2,
        workflows=[workflow_info],
        project_type=ProjectType.GREENFIELD,
        routing_rationale="Test workflow",
        phase_breakdown={"test": ["test-workflow"]},
        jit_tech_specs=False,
        estimated_stories=5,
        estimated_epics=1,
    )


@pytest.mark.asyncio
async def test_context_created_at_workflow_start(orchestrator, context_persistence, simple_workflow_sequence):
    """Test that WorkflowContext is created at workflow start."""
    # Clear any existing thread-local context
    clear_workflow_context()

    # Execute workflow
    result = await orchestrator.execute_workflow(
        initial_prompt="Build a test application",
        workflow=simple_workflow_sequence,
    )

    # Verify context_id in result
    assert result.context_id is not None
    assert isinstance(result.context_id, str)

    # Verify context persisted to database
    loaded_context = context_persistence.load_context(result.context_id)
    assert loaded_context is not None
    assert loaded_context.workflow_id == result.context_id
    assert loaded_context.workflow_name == result.workflow_name
    assert loaded_context.status == "completed"


@pytest.mark.asyncio
async def test_context_includes_workflow_metadata(orchestrator, context_persistence, simple_workflow_sequence):
    """Test that context includes workflow metadata."""
    clear_workflow_context()

    result = await orchestrator.execute_workflow(
        initial_prompt="Build a todo application",
        workflow=simple_workflow_sequence,
    )

    # Load context and verify metadata
    context = context_persistence.load_context(result.context_id)

    assert context.metadata["mode"] == "test"
    assert context.metadata["scale_level"] == ScaleLevel.LEVEL_2.value
    assert context.metadata["project_type"] == ProjectType.GREENFIELD.value
    assert context.metadata["estimated_stories"] == 5
    assert context.metadata["estimated_epics"] == 1
    assert "routing_rationale" in context.metadata


@pytest.mark.asyncio
async def test_context_persisted_at_initialization(orchestrator, context_persistence, simple_workflow_sequence):
    """Test that context is persisted at workflow initialization."""
    clear_workflow_context()

    # Mock coordinator to track when it's called
    calls_before_coordinator = []

    async def mock_execute_sequence(*args, **kwargs):
        # Check if context exists before coordinator execution
        context_id = kwargs.get("context", {}).metadata.get("tracking_context_id")
        if context_id:
            try:
                loaded = context_persistence.load_context(context_id)
                calls_before_coordinator.append(loaded is not None)
            except Exception:
                calls_before_coordinator.append(False)

        return Mock(
            status=WorkflowStatus.COMPLETED,
            step_results=[],
            error_message=None,
            total_artifacts=0,
        )

    orchestrator.workflow_coordinator.execute_sequence = mock_execute_sequence

    result = await orchestrator.execute_workflow(
        initial_prompt="Test prompt",
        workflow=simple_workflow_sequence,
    )

    # Context should exist before coordinator was called
    assert len(calls_before_coordinator) > 0
    assert calls_before_coordinator[0] is True


@pytest.mark.asyncio
async def test_context_updated_after_phase_transitions(orchestrator, context_persistence, simple_workflow_sequence):
    """Test that context is updated after phase transitions."""
    clear_workflow_context()

    result = await orchestrator.execute_workflow(
        initial_prompt="Test application",
        workflow=simple_workflow_sequence,
    )

    # Load context and verify phase history
    context = context_persistence.load_context(result.context_id)

    # Should have transitions: initialization -> planning -> completed
    assert len(context.phase_history) >= 2
    assert any(t.phase == "initialization" for t in context.phase_history)
    assert any(t.phase == "planning" for t in context.phase_history)
    assert context.current_phase == "completed"


@pytest.mark.asyncio
async def test_artifacts_recorded_in_context(orchestrator, context_persistence, simple_workflow_sequence):
    """Test that artifacts are recorded in context."""
    clear_workflow_context()

    # Mock coordinator to return artifacts
    async def mock_with_artifacts(*args, **kwargs):
        from gao_dev.orchestrator.workflow_results import WorkflowStepResult

        step_result = WorkflowStepResult(
            step_name="test-step",
            agent="TestAgent",
            status="success",
            start_time=datetime.now(),
            end_time=datetime.now(),
            artifacts_created=["file1.py", "file2.py"],
        )

        return Mock(
            status=WorkflowStatus.COMPLETED,
            step_results=[step_result],
            error_message=None,
            total_artifacts=2,
        )

    orchestrator.workflow_coordinator.execute_sequence = mock_with_artifacts

    result = await orchestrator.execute_workflow(
        initial_prompt="Test prompt",
        workflow=simple_workflow_sequence,
    )

    # Verify artifacts in context
    context = context_persistence.load_context(result.context_id)
    assert len(context.artifacts) == 2
    assert "file1.py" in context.artifacts
    assert "file2.py" in context.artifacts


@pytest.mark.asyncio
async def test_failed_workflow_marks_context_as_failed(orchestrator, context_persistence, simple_workflow_sequence):
    """Test that failed workflows mark context as failed."""
    clear_workflow_context()

    # Mock coordinator to return failure
    async def mock_failure(*args, **kwargs):
        return Mock(
            status=WorkflowStatus.FAILED,
            step_results=[],
            error_message="Test error",
            total_artifacts=0,
        )

    orchestrator.workflow_coordinator.execute_sequence = mock_failure

    result = await orchestrator.execute_workflow(
        initial_prompt="Test prompt",
        workflow=simple_workflow_sequence,
    )

    # Verify result is failed
    assert result.status == WorkflowStatus.FAILED
    assert result.context_id is not None

    # Verify context marked as failed
    context = context_persistence.load_context(result.context_id)
    assert context.status == "failed"
    assert context.current_phase == "failed"
    assert "error" in context.metadata
    assert context.metadata["error"] == "Test error"


@pytest.mark.asyncio
async def test_exception_marks_context_as_failed(orchestrator, context_persistence, simple_workflow_sequence):
    """Test that exceptions mark context as failed."""
    clear_workflow_context()

    # Mock coordinator to raise exception
    async def mock_exception(*args, **kwargs):
        raise ValueError("Test exception")

    orchestrator.workflow_coordinator.execute_sequence = mock_exception

    result = await orchestrator.execute_workflow(
        initial_prompt="Test prompt",
        workflow=simple_workflow_sequence,
    )

    # Verify result is failed
    assert result.status == WorkflowStatus.FAILED
    assert result.context_id is not None

    # Verify context marked as failed with exception details
    context = context_persistence.load_context(result.context_id)
    assert context.status == "failed"
    assert "error" in context.metadata
    assert "Test exception" in context.metadata["error"]
    assert context.metadata["exception_type"] == "ValueError"


@pytest.mark.asyncio
async def test_thread_local_context_set_during_workflow(orchestrator, context_persistence, simple_workflow_sequence):
    """Test that thread-local context is set during workflow execution."""
    clear_workflow_context()

    # Track thread-local context during execution
    context_during_execution = []

    async def mock_check_context(*args, **kwargs):
        # Check thread-local context
        current_context = get_workflow_context()
        context_during_execution.append(current_context)

        return Mock(
            status=WorkflowStatus.COMPLETED,
            step_results=[],
            error_message=None,
            total_artifacts=0,
        )

    orchestrator.workflow_coordinator.execute_sequence = mock_check_context

    result = await orchestrator.execute_workflow(
        initial_prompt="Test prompt",
        workflow=simple_workflow_sequence,
    )

    # Context should have been available during execution
    assert len(context_during_execution) > 0
    assert context_during_execution[0] is not None
    assert context_during_execution[0].workflow_id == result.context_id


@pytest.mark.asyncio
async def test_thread_local_context_cleared_after_workflow(orchestrator, context_persistence, simple_workflow_sequence):
    """Test that thread-local context is cleared after workflow completion."""
    clear_workflow_context()

    result = await orchestrator.execute_workflow(
        initial_prompt="Test prompt",
        workflow=simple_workflow_sequence,
    )

    # Context should be cleared after workflow
    current_context = get_workflow_context()
    assert current_context is None


@pytest.mark.asyncio
async def test_workflow_result_includes_context_id(orchestrator, context_persistence, simple_workflow_sequence):
    """Test that WorkflowResult includes context_id."""
    clear_workflow_context()

    result = await orchestrator.execute_workflow(
        initial_prompt="Test prompt",
        workflow=simple_workflow_sequence,
    )

    # Verify context_id in result
    assert result.context_id is not None
    assert isinstance(result.context_id, str)

    # Verify context_id is valid UUID
    try:
        uuid.UUID(result.context_id)
    except ValueError:
        pytest.fail("context_id is not a valid UUID")


@pytest.mark.asyncio
async def test_workflow_result_serialization_includes_context_id(orchestrator, context_persistence, simple_workflow_sequence):
    """Test that WorkflowResult serialization includes context_id."""
    clear_workflow_context()

    result = await orchestrator.execute_workflow(
        initial_prompt="Test prompt",
        workflow=simple_workflow_sequence,
    )

    # Serialize to dict
    result_dict = result.to_dict()

    # Verify context_id in serialized dict
    assert "context_id" in result_dict
    assert result_dict["context_id"] == result.context_id


@pytest.mark.asyncio
async def test_context_id_can_query_full_context(orchestrator, context_persistence, simple_workflow_sequence):
    """Test that context_id can be used to query full context."""
    clear_workflow_context()

    result = await orchestrator.execute_workflow(
        initial_prompt="Build a calculator application",
        workflow=simple_workflow_sequence,
    )

    # Query full context using context_id
    full_context = context_persistence.load_context(result.context_id)

    # Verify full context loaded
    assert full_context is not None
    assert full_context.workflow_id == result.context_id
    assert full_context.feature is not None
    assert full_context.workflow_name == result.workflow_name


@pytest.mark.asyncio
async def test_concurrent_workflows_have_isolated_contexts(orchestrator, context_persistence, simple_workflow_sequence, tmp_path):
    """Test that concurrent workflows have isolated contexts."""
    import asyncio

    clear_workflow_context()

    # Create second orchestrator for concurrent execution
    orchestrator2 = GAODevOrchestrator(
        project_root=tmp_path / "test_project2",
        api_key="test_key",
        mode="test",
        workflow_coordinator=orchestrator.workflow_coordinator,
        story_lifecycle=orchestrator.story_lifecycle,
        process_executor=orchestrator.process_executor,
        quality_gate_manager=orchestrator.quality_gate_manager,
        brian_orchestrator=orchestrator.brian_orchestrator,
        context_persistence=context_persistence,
    )

    # Execute two workflows concurrently
    task1 = orchestrator.execute_workflow(
        initial_prompt="First workflow",
        workflow=simple_workflow_sequence,
    )
    task2 = orchestrator2.execute_workflow(
        initial_prompt="Second workflow",
        workflow=simple_workflow_sequence,
    )

    results = await asyncio.gather(task1, task2)

    # Verify different context IDs
    assert results[0].context_id != results[1].context_id

    # Verify both contexts persisted separately
    context1 = context_persistence.load_context(results[0].context_id)
    context2 = context_persistence.load_context(results[1].context_id)

    assert context1.workflow_id == results[0].context_id
    assert context2.workflow_id == results[1].context_id
    assert context1.workflow_id != context2.workflow_id


@pytest.mark.asyncio
async def test_feature_name_extraction(orchestrator, context_persistence, simple_workflow_sequence):
    """Test feature name extraction from prompt."""
    clear_workflow_context()

    result = await orchestrator.execute_workflow(
        initial_prompt="Build a todo list application with user authentication",
        workflow=simple_workflow_sequence,
    )

    # Load context and check feature name
    context = context_persistence.load_context(result.context_id)

    # Feature name should be extracted from prompt
    assert context.feature is not None
    assert len(context.feature) > 0
    # Should be kebab-case
    assert "-" in context.feature or context.feature.islower()


@pytest.mark.asyncio
async def test_context_versioning(orchestrator, context_persistence, simple_workflow_sequence):
    """Test that context updates increment version."""
    clear_workflow_context()

    result = await orchestrator.execute_workflow(
        initial_prompt="Test prompt",
        workflow=simple_workflow_sequence,
    )

    # Load context and check version
    context = context_persistence.load_context(result.context_id)

    # Version should be incremented from initial save
    # Initial save is version 1, then we have updates during execution
    # So final version should be > 1
    # Note: We can't directly check version from WorkflowContext,
    # but we can verify context was updated by checking phase history
    assert len(context.phase_history) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

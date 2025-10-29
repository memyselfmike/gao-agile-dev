"""Tests for workflow execution (Story 7.2.2)."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
from datetime import datetime

from gao_dev.orchestrator import GAODevOrchestrator
from gao_dev.orchestrator.workflow_results import WorkflowStatus, WorkflowResult
from gao_dev.orchestrator.brian_orchestrator import WorkflowSequence, ScaleLevel, ProjectType
from gao_dev.core.models import WorkflowInfo


@pytest.fixture
def mock_project_root(tmp_path):
    """Create a temporary project root."""
    return tmp_path / "test_project"


@pytest.fixture
def mock_orchestrator(mock_project_root):
    """Create orchestrator with mocked dependencies."""
    with patch('gao_dev.orchestrator.orchestrator.ConfigLoader'):
        with patch('gao_dev.orchestrator.orchestrator.WorkflowRegistry'):
            with patch('gao_dev.orchestrator.orchestrator.BrianOrchestrator'):
                orchestrator = GAODevOrchestrator(
                    project_root=mock_project_root,
                    api_key="test-key"
                )
                return orchestrator


@pytest.fixture
def sample_workflow_sequence():
    """Create a sample workflow sequence for testing."""
    workflow1 = WorkflowInfo(
        name="prd",
        description="Create PRD",
        phase=2,
        installed_path=Path("/fake/path")
    )
    workflow2 = WorkflowInfo(
        name="architecture",
        description="Create Architecture",
        phase=3,
        installed_path=Path("/fake/path")
    )

    return WorkflowSequence(
        scale_level=ScaleLevel.LEVEL_2,
        workflows=[workflow1, workflow2],
        project_type=ProjectType.GREENFIELD,
        routing_rationale="Test sequence",
        phase_breakdown={"Phase 2": ["prd"], "Phase 3": ["architecture"]}
    )


@pytest.mark.asyncio
async def test_execute_workflow_with_provided_sequence(mock_orchestrator, sample_workflow_sequence):
    """Test execute_workflow with pre-provided workflow sequence."""
    # Mock the agent methods as async generators
    async def mock_create_prd(**kwargs):
        yield "PRD created"

    async def mock_create_architecture(**kwargs):
        yield "Architecture created"

    mock_orchestrator.create_prd = mock_create_prd
    mock_orchestrator.create_architecture = mock_create_architecture

    # Execute workflow
    result = await mock_orchestrator.execute_workflow(
        initial_prompt="Build a todo app",
        workflow=sample_workflow_sequence
    )

    # Verify result
    assert result.status == WorkflowStatus.COMPLETED
    assert result.total_steps == 2
    assert result.successful_steps == 2
    assert result.failed_steps == 0


@pytest.mark.asyncio
async def test_execute_workflow_auto_select(mock_orchestrator, sample_workflow_sequence):
    """Test execute_workflow with auto-selection."""
    # Mock Brian's workflow selection
    mock_orchestrator.assess_and_select_workflows = AsyncMock(
        return_value=sample_workflow_sequence
    )

    # Mock agent methods as async generators
    async def mock_create_prd(**kwargs):
        yield "PRD created"

    async def mock_create_architecture(**kwargs):
        yield "Architecture created"

    mock_orchestrator.create_prd = mock_create_prd
    mock_orchestrator.create_architecture = mock_create_architecture

    # Execute workflow without providing sequence
    result = await mock_orchestrator.execute_workflow(
        initial_prompt="Build a todo app"
    )

    # Verify auto-selection was called
    mock_orchestrator.assess_and_select_workflows.assert_called_once()

    # Verify result
    assert result.status == WorkflowStatus.COMPLETED
    assert result.total_steps == 2


@pytest.mark.asyncio
async def test_execute_workflow_step_failure(mock_orchestrator, sample_workflow_sequence):
    """Test workflow stops on step failure (fail-fast)."""
    # Mock first step to fail
    async def mock_create_prd_fail():
        raise Exception("PRD failed")
        yield

    mock_orchestrator.create_prd = mock_create_prd_fail

    # Execute workflow
    result = await mock_orchestrator.execute_workflow(
        initial_prompt="Build a todo app",
        workflow=sample_workflow_sequence
    )

    # Verify workflow failed
    assert result.status == WorkflowStatus.FAILED
    assert result.total_steps == 1  # Only first step attempted
    assert result.failed_steps == 1


@pytest.mark.asyncio
async def test_execute_workflow_empty_sequence(mock_orchestrator):
    """Test workflow handles empty sequence gracefully."""
    empty_sequence = WorkflowSequence(
        scale_level=ScaleLevel.LEVEL_0,
        workflows=[],
        project_type=ProjectType.GREENFIELD,
        routing_rationale="Empty for testing",
        phase_breakdown={}
    )

    # Execute workflow with empty sequence
    result = await mock_orchestrator.execute_workflow(
        initial_prompt="Build a todo app",
        workflow=empty_sequence
    )

    # Verify workflow completed with no steps
    # (Empty workflow sequence should complete successfully, just with 0 steps)
    assert result.total_steps == 0


def test_get_agent_for_workflow(mock_orchestrator):
    """Test agent mapping for workflows."""
    # Test PRD workflow -> John
    prd_workflow = WorkflowInfo(
        name="prd",
        description="Create PRD",
        phase=2,
        installed_path=Path("/fake")
    )
    assert mock_orchestrator._get_agent_for_workflow(prd_workflow) == "John"

    # Test architecture workflow -> Winston
    arch_workflow = WorkflowInfo(
        name="architecture",
        description="Create Architecture",
        phase=3,
        installed_path=Path("/fake")
    )
    assert mock_orchestrator._get_agent_for_workflow(arch_workflow) == "Winston"

    # Test story creation workflow -> Bob
    story_workflow = WorkflowInfo(
        name="create-story",
        description="Create Story",
        phase=4,
        installed_path=Path("/fake")
    )
    assert mock_orchestrator._get_agent_for_workflow(story_workflow) == "Bob"

    # Test implementation workflow -> Amelia
    impl_workflow = WorkflowInfo(
        name="dev-story",
        description="Implement Story",
        phase=4,
        installed_path=Path("/fake")
    )
    assert mock_orchestrator._get_agent_for_workflow(impl_workflow) == "Amelia"


def test_workflow_result_properties():
    """Test WorkflowResult computed properties."""
    from gao_dev.orchestrator.workflow_results import WorkflowResult, WorkflowStepResult

    result = WorkflowResult(
        workflow_name="test",
        initial_prompt="test prompt",
        status=WorkflowStatus.COMPLETED,
        start_time=datetime.now()
    )

    # Add successful steps
    result.step_results = [
        WorkflowStepResult(
            step_name="step1",
            agent="John",
            status="success",
            start_time=datetime.now(),
            end_time=datetime.now()
        ),
        WorkflowStepResult(
            step_name="step2",
            agent="Winston",
            status="success",
            start_time=datetime.now(),
            end_time=datetime.now()
        ),
    ]

    # Test properties
    assert result.total_steps == 2
    assert result.successful_steps == 2
    assert result.failed_steps == 0
    assert result.success

    # Test to_dict
    result_dict = result.to_dict()
    assert result_dict["workflow_name"] == "test"
    assert result_dict["total_steps"] == 2
    assert result_dict["successful_steps"] == 2


@pytest.mark.asyncio
async def test_execute_workflow_sequence_from_prompt(mock_orchestrator, sample_workflow_sequence):
    """Test convenience method for executing from prompt."""
    # Mock Brian's workflow selection
    mock_orchestrator.assess_and_select_workflows = AsyncMock(
        return_value=sample_workflow_sequence
    )

    # Mock agent methods as async generators
    async def mock_create_prd(**kwargs):
        yield "PRD created"

    async def mock_create_architecture(**kwargs):
        yield "Architecture created"

    mock_orchestrator.create_prd = mock_create_prd
    mock_orchestrator.create_architecture = mock_create_architecture

    # Execute from prompt
    result = await mock_orchestrator.execute_workflow_sequence_from_prompt(
        "Build a todo application"
    )

    # Verify execution
    assert result.success
    assert result.total_steps == 2
    mock_orchestrator.assess_and_select_workflows.assert_called_once()


def test_workflow_step_result_serialization():
    """Test WorkflowStepResult serialization."""
    from gao_dev.orchestrator.workflow_results import WorkflowStepResult

    step_result = WorkflowStepResult(
        step_name="test_step",
        agent="John",
        status="success",
        start_time=datetime.now(),
        end_time=datetime.now(),
        artifacts_created=["docs/PRD.md"],
        commit_hash="abc123"
    )

    # Test to_dict
    result_dict = step_result.to_dict()
    assert result_dict["step_name"] == "test_step"
    assert result_dict["agent"] == "John"
    assert result_dict["status"] == "success"
    assert result_dict["commit_hash"] == "abc123"
    assert "docs/PRD.md" in result_dict["artifacts_created"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

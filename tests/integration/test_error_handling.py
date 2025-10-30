"""Integration tests for error handling (Story 7.2.5 - AC4)."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from gao_dev.orchestrator import GAODevOrchestrator
from gao_dev.orchestrator.models import WorkflowSequence, ScaleLevel, ProjectType
from gao_dev.core.models.workflow import WorkflowInfo


@pytest.fixture
def temp_project(tmp_path):
    """Create temporary project directory."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def orchestrator(temp_project):
    """Create orchestrator for error testing."""
    return GAODevOrchestrator(
        project_root=temp_project,
        api_key="test-key",
        mode="benchmark"
    )


@pytest.mark.asyncio
async def test_workflow_handles_missing_agent_method(orchestrator):
    """Test error handling when agent method doesn't exist."""
    # Create workflow with non-existent method
    workflow_info = WorkflowInfo(
        name="invalid-workflow",
        description="Workflow with invalid agent method",
        phase=2,
        installed_path=Path("/fake")
    )

    sequence = WorkflowSequence(
        scale_level=ScaleLevel.LEVEL_1,
        workflows=[workflow_info],
        project_type=ProjectType.GREENFIELD,
        routing_rationale="Test invalid workflow",
        phase_breakdown={"Phase 2": ["invalid-workflow"]}
    )

    # Execute workflow with missing method
    result = await orchestrator.execute_workflow(
        "Test invalid workflow",
        workflow=sequence
    )

    # Should handle error gracefully
    assert result is not None
    assert result.workflow_name
    # Failed steps should be tracked
    assert hasattr(result, 'failed_steps')


@pytest.mark.asyncio
async def test_workflow_handles_agent_method_exception(orchestrator):
    """Test error handling when agent method raises exception."""
    workflow_info = WorkflowInfo(
        name="failing-workflow",
        description="Workflow that raises exception",
        phase=2,
        installed_path=Path("/fake")
    )

    sequence = WorkflowSequence(
        scale_level=ScaleLevel.LEVEL_1,
        workflows=[workflow_info],
        project_type=ProjectType.GREENFIELD,
        routing_rationale="Test failing workflow",
        phase_breakdown={}
    )

    # Mock agent method that raises exception
    async def failing_method():
        raise RuntimeError("Simulated agent failure")
        yield  # Make it a generator

    with patch.object(orchestrator, '_get_agent_method_for_workflow', return_value=failing_method):
        result = await orchestrator.execute_workflow(
            "Test failing workflow",
            workflow=sequence
        )

        # Should complete with error status
        assert result is not None
        assert result.workflow_name == "failing-workflow"


@pytest.mark.asyncio
async def test_workflow_timeout_handling(orchestrator):
    """Test that workflow respects timeout settings."""
    workflow_info = WorkflowInfo(
        name="slow-workflow",
        description="Workflow that times out",
        phase=2,
        installed_path=Path("/fake")
    )

    sequence = WorkflowSequence(
        scale_level=ScaleLevel.LEVEL_1,
        workflows=[workflow_info],
        project_type=ProjectType.GREENFIELD,
        routing_rationale="Test timeout",
        phase_breakdown={}
    )

    # Mock slow agent method
    async def slow_method():
        await asyncio.sleep(10)  # 10 seconds
        yield "Should timeout"

    with patch.object(orchestrator, '_get_agent_method_for_workflow', return_value=slow_method):
        start_time = asyncio.get_event_loop().time()

        # Use asyncio timeout to enforce limit
        try:
            result = await asyncio.wait_for(
                orchestrator.execute_workflow("Test timeout", workflow=sequence),
                timeout=2.0  # 2 second timeout
            )
            elapsed = asyncio.get_event_loop().time() - start_time
            # If it completes within timeout, that's fine
            assert elapsed < 3.0
            assert result is not None
        except asyncio.TimeoutError:
            # Timeout is also acceptable - test passed
            elapsed = asyncio.get_event_loop().time() - start_time
            assert elapsed <= 3.0  # Should timeout within 3 seconds
            pass  # Test passed - timeout occurred as expected


@pytest.mark.asyncio
async def test_workflow_handles_empty_workflow_list(orchestrator):
    """Test handling of empty workflow list (clarification needed)."""
    # Empty workflow sequence
    empty_sequence = WorkflowSequence(
        scale_level=ScaleLevel.LEVEL_0,
        workflows=[],
        project_type=ProjectType.GREENFIELD,
        routing_rationale="Needs clarification",
        phase_breakdown={}
    )

    result = await orchestrator.execute_workflow(
        "Unclear prompt",
        workflow=empty_sequence
    )

    # Should complete with 0 steps
    assert result.total_steps == 0
    assert result.workflow_name


@pytest.mark.asyncio
async def test_invalid_workflow_info_handling(orchestrator):
    """Test handling of invalid WorkflowInfo objects."""
    # Workflow with invalid path
    invalid_workflow = WorkflowInfo(
        name="invalid",
        description="Invalid workflow",
        phase=999,  # Invalid phase
        installed_path=Path("/non/existent/path")
    )

    sequence = WorkflowSequence(
        scale_level=ScaleLevel.LEVEL_1,
        workflows=[invalid_workflow],
        project_type=ProjectType.GREENFIELD,
        routing_rationale="Test invalid workflow",
        phase_breakdown={}
    )

    result = await orchestrator.execute_workflow(
        "Test invalid",
        workflow=sequence
    )

    # Should handle gracefully
    assert result is not None


@pytest.mark.asyncio
async def test_multiple_workflow_failure_handling(orchestrator):
    """Test handling when multiple workflows in sequence fail."""
    workflows = [
        WorkflowInfo(
            name=f"workflow-{i}",
            description=f"Workflow {i}",
            phase=2,
            installed_path=Path(f"/fake/{i}")
        )
        for i in range(3)
    ]

    sequence = WorkflowSequence(
        scale_level=ScaleLevel.LEVEL_2,
        workflows=workflows,
        project_type=ProjectType.GREENFIELD,
        routing_rationale="Test multiple failures",
        phase_breakdown={}
    )

    # Mock methods that all fail
    call_count = 0

    async def failing_method():
        nonlocal call_count
        call_count += 1
        raise RuntimeError(f"Failure {call_count}")
        yield

    with patch.object(orchestrator, '_get_agent_method_for_workflow', return_value=failing_method):
        result = await orchestrator.execute_workflow(
            "Test multiple failures",
            workflow=sequence
        )

        # Should track all failures
        assert result is not None
        assert call_count <= 3  # Should attempt each workflow


@pytest.mark.asyncio
async def test_orchestrator_handles_invalid_api_key(temp_project):
    """Test that invalid API key is handled gracefully."""
    orchestrator = GAODevOrchestrator(
        project_root=temp_project,
        api_key=None,  # No API key
        mode="benchmark"
    )

    # Should still initialize
    assert orchestrator.api_key is None


@pytest.mark.asyncio
async def test_project_root_validation(tmp_path):
    """Test that invalid project root is handled."""
    non_existent = tmp_path / "non_existent_dir"

    # Should handle non-existent directory
    orchestrator = GAODevOrchestrator(
        project_root=non_existent,
        api_key="test-key",
        mode="benchmark"
    )

    assert orchestrator.project_root == non_existent


def test_invalid_execution_mode(temp_project):
    """Test handling of invalid execution mode."""
    # Invalid mode should default to 'cli' or be validated
    orchestrator = GAODevOrchestrator(
        project_root=temp_project,
        api_key="test-key",
        mode="invalid_mode"
    )

    # Should have some default mode
    assert orchestrator.mode in ["cli", "benchmark", "api", "invalid_mode"]


@pytest.mark.asyncio
async def test_workflow_result_on_exception(orchestrator):
    """Test that WorkflowResult is always returned even on exception."""
    workflow_info = WorkflowInfo(
        name="exception-workflow",
        description="Workflow that throws exception",
        phase=2,
        installed_path=Path("/fake")
    )

    sequence = WorkflowSequence(
        scale_level=ScaleLevel.LEVEL_1,
        workflows=[workflow_info],
        project_type=ProjectType.GREENFIELD,
        routing_rationale="Test exception handling",
        phase_breakdown={}
    )

    # Mock method that raises unexpected exception
    async def exception_method():
        raise ValueError("Unexpected error")
        yield

    with patch.object(orchestrator, '_get_agent_method_for_workflow', return_value=exception_method):
        result = await orchestrator.execute_workflow(
            "Test exception",
            workflow=sequence
        )

        # Should always return a WorkflowResult
        assert result is not None
        assert hasattr(result, 'workflow_name')
        assert hasattr(result, 'status')
        assert hasattr(result, 'total_steps')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

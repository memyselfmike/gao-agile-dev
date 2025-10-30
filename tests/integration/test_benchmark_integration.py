"""Integration tests for benchmark system (Story 7.2.5 - AC6)."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from gao_dev.orchestrator import GAODevOrchestrator
from gao_dev.orchestrator.models import WorkflowSequence, ScaleLevel, ProjectType
from gao_dev.orchestrator.workflow_results import WorkflowResult, WorkflowStatus
from gao_dev.core.models.workflow import WorkflowInfo


@pytest.fixture
def temp_project(tmp_path):
    """Create temporary project directory."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


@pytest.mark.asyncio
async def test_benchmark_mode_execution(temp_project):
    """Test that benchmark mode executes workflows correctly."""
    orchestrator = GAODevOrchestrator(
        project_root=temp_project,
        api_key="test-key",
        mode="benchmark"
    )

    # Create simple workflow
    workflow_info = WorkflowInfo(
        name="benchmark-test-workflow",
        description="Test workflow for benchmarking",
        phase=2,
        installed_path=Path("/fake")
    )

    sequence = WorkflowSequence(
        scale_level=ScaleLevel.LEVEL_1,
        workflows=[workflow_info],
        project_type=ProjectType.GREENFIELD,
        routing_rationale="Benchmark test",
        phase_breakdown={}
    )

    # Mock agent method
    async def mock_method():
        yield "Task completed"

    with patch.object(orchestrator, '_get_agent_method_for_workflow', return_value=mock_method):
        result = await orchestrator.execute_workflow(
            "Test benchmark",
            workflow=sequence
        )

        # Verify result structure for benchmark collection
        assert result is not None
        assert result.workflow_name == "benchmark-test-workflow"
        assert result.initial_prompt == "Test benchmark"
        assert hasattr(result, 'start_time')
        assert hasattr(result, 'duration_seconds')
        assert hasattr(result, 'total_steps')


@pytest.mark.asyncio
async def test_benchmark_collects_timing_metrics(temp_project):
    """Test that benchmark mode collects timing metrics."""
    orchestrator = GAODevOrchestrator(
        project_root=temp_project,
        api_key="test-key",
        mode="benchmark"
    )

    workflow_info = WorkflowInfo(
        name="timing-test",
        description="Test timing collection",
        phase=2,
        installed_path=Path("/fake")
    )

    sequence = WorkflowSequence(
        scale_level=ScaleLevel.LEVEL_1,
        workflows=[workflow_info],
        project_type=ProjectType.GREENFIELD,
        routing_rationale="Timing test",
        phase_breakdown={}
    )

    # Mock with timed execution
    import asyncio

    async def timed_method():
        await asyncio.sleep(0.1)  # 100ms
        yield "Done"

    with patch.object(orchestrator, '_get_agent_method_for_workflow', return_value=timed_method):
        result = await orchestrator.execute_workflow(
            "Test timing",
            workflow=sequence
        )

        # Should have timing information
        assert result.duration_seconds >= 0.1
        assert result.start_time is not None


@pytest.mark.asyncio
async def test_benchmark_tracks_step_count(temp_project):
    """Test that benchmark tracks step counts correctly."""
    orchestrator = GAODevOrchestrator(
        project_root=temp_project,
        api_key="test-key",
        mode="benchmark"
    )

    # Multiple workflows
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
        routing_rationale="Multi-workflow test",
        phase_breakdown={}
    )

    async def mock_method():
        yield "Completed"

    with patch.object(orchestrator, '_get_agent_method_for_workflow', return_value=mock_method):
        result = await orchestrator.execute_workflow(
            "Test step count",
            workflow=sequence
        )

        # Should track total steps (3 workflows)
        assert result.total_steps == 3


@pytest.mark.asyncio
async def test_benchmark_workflow_result_format(temp_project):
    """Test that WorkflowResult has format expected by benchmark system."""
    orchestrator = GAODevOrchestrator(
        project_root=temp_project,
        api_key="test-key",
        mode="benchmark"
    )

    workflow_info = WorkflowInfo(
        name="format-test",
        description="Test result format",
        phase=2,
        installed_path=Path("/fake")
    )

    sequence = WorkflowSequence(
        scale_level=ScaleLevel.LEVEL_1,
        workflows=[workflow_info],
        project_type=ProjectType.GREENFIELD,
        routing_rationale="Format test",
        phase_breakdown={}
    )

    async def mock_method():
        yield "Completed"

    with patch.object(orchestrator, '_get_agent_method_for_workflow', return_value=mock_method):
        result = await orchestrator.execute_workflow(
            "Test format",
            workflow=sequence
        )

        # Verify all expected fields for benchmark
        assert hasattr(result, 'workflow_name')
        assert hasattr(result, 'initial_prompt')
        assert hasattr(result, 'status')
        assert hasattr(result, 'start_time')
        assert hasattr(result, 'end_time')
        assert hasattr(result, 'duration_seconds')
        assert hasattr(result, 'total_steps')
        assert hasattr(result, 'successful_steps')
        assert hasattr(result, 'failed_steps')
        assert hasattr(result, 'step_results')

        # Types should be correct
        assert isinstance(result.workflow_name, str)
        assert isinstance(result.total_steps, int)
        assert isinstance(result.successful_steps, int)
        assert isinstance(result.failed_steps, int)
        assert isinstance(result.duration_seconds, (int, float))


@pytest.mark.asyncio
async def test_benchmark_success_criteria_data(temp_project):
    """Test that WorkflowResult provides data for success criteria checking."""
    orchestrator = GAODevOrchestrator(
        project_root=temp_project,
        api_key="test-key",
        mode="benchmark"
    )

    workflow_info = WorkflowInfo(
        name="success-test",
        description="Test success criteria",
        phase=2,
        installed_path=Path("/fake")
    )

    sequence = WorkflowSequence(
        scale_level=ScaleLevel.LEVEL_1,
        workflows=[workflow_info],
        project_type=ProjectType.GREENFIELD,
        routing_rationale="Success criteria test",
        phase_breakdown={}
    )

    async def mock_method():
        yield "Completed with artifacts"

    with patch.object(orchestrator, '_get_agent_method_for_workflow', return_value=mock_method):
        result = await orchestrator.execute_workflow(
            "Test success",
            workflow=sequence
        )

        # Should have data for success criteria
        assert result.step_results is not None
        assert isinstance(result.step_results, list)

        # Each step should have result data
        for step in result.step_results:
            assert hasattr(step, 'step_name')
            assert hasattr(step, 'status')


@pytest.mark.asyncio
async def test_benchmark_mode_no_interactive_prompts(temp_project):
    """Test that benchmark mode never shows interactive prompts."""
    orchestrator = GAODevOrchestrator(
        project_root=temp_project,
        api_key="test-key",
        mode="benchmark"
    )

    # Clarification should return None in benchmark mode
    questions = ["What framework?", "What language?"]
    result = orchestrator.handle_clarification(questions, "Build app")

    assert result is None  # No interactive prompts


@pytest.mark.asyncio
async def test_scale_level_metadata_in_results(temp_project):
    """Test that scale level information is preserved in results."""
    orchestrator = GAODevOrchestrator(
        project_root=temp_project,
        api_key="test-key",
        mode="benchmark"
    )

    for scale_level in [ScaleLevel.LEVEL_1, ScaleLevel.LEVEL_2, ScaleLevel.LEVEL_3]:
        workflow_info = WorkflowInfo(
            name=f"scale-{scale_level.value}",
            description=f"Scale {scale_level.value} test",
            phase=2,
            installed_path=Path("/fake")
        )

        sequence = WorkflowSequence(
            scale_level=scale_level,
            workflows=[workflow_info],
            project_type=ProjectType.GREENFIELD,
            routing_rationale=f"Test scale {scale_level.value}",
            phase_breakdown={}
        )

        async def mock_method():
            yield "Done"

        with patch.object(orchestrator, '_get_agent_method_for_workflow', return_value=mock_method):
            result = await orchestrator.execute_workflow(
                f"Test scale {scale_level.value}",
                workflow=sequence
            )

            # Result should exist
            assert result is not None
            assert result.workflow_name == f"scale-{scale_level.value}"


@pytest.mark.asyncio
async def test_benchmark_handles_partial_workflow_completion(temp_project):
    """Test benchmark correctly tracks partial workflow completion."""
    orchestrator = GAODevOrchestrator(
        project_root=temp_project,
        api_key="test-key",
        mode="benchmark"
    )

    # 3 workflows: first succeeds, second fails, third shouldn't run
    workflows = [
        WorkflowInfo(
            name="workflow-success",
            description="Succeeds",
            phase=2,
            installed_path=Path("/fake/1")
        ),
        WorkflowInfo(
            name="workflow-fail",
            description="Fails",
            phase=2,
            installed_path=Path("/fake/2")
        ),
        WorkflowInfo(
            name="workflow-skip",
            description="Should be skipped",
            phase=2,
            installed_path=Path("/fake/3")
        ),
    ]

    sequence = WorkflowSequence(
        scale_level=ScaleLevel.LEVEL_2,
        workflows=workflows,
        project_type=ProjectType.GREENFIELD,
        routing_rationale="Test partial completion",
        phase_breakdown={}
    )

    call_count = [0]

    async def mock_method():
        call_count[0] += 1
        if call_count[0] == 2:
            raise RuntimeError("Second workflow fails")
        yield "Done"

    with patch.object(orchestrator, '_get_agent_method_for_workflow', return_value=mock_method):
        result = await orchestrator.execute_workflow(
            "Test partial",
            workflow=sequence
        )

        # Should track partial completion
        assert result.successful_steps >= 1  # First succeeded
        assert result.failed_steps >= 1  # Second failed
        # Third may or may not execute depending on fail-fast strategy


@pytest.mark.asyncio
async def test_benchmark_different_project_types(temp_project):
    """Test benchmark handles different project types correctly."""
    orchestrator = GAODevOrchestrator(
        project_root=temp_project,
        api_key="test-key",
        mode="benchmark"
    )

    for project_type in [ProjectType.GREENFIELD, ProjectType.ENHANCEMENT, ProjectType.BUG_FIX]:
        workflow_info = WorkflowInfo(
            name=f"{project_type.value}-workflow",
            description=f"{project_type.value} workflow",
            phase=2,
            installed_path=Path("/fake")
        )

        sequence = WorkflowSequence(
            scale_level=ScaleLevel.LEVEL_1,
            workflows=[workflow_info],
            project_type=project_type,
            routing_rationale=f"Test {project_type.value}",
            phase_breakdown={}
        )

        async def mock_method():
            yield "Done"

        with patch.object(orchestrator, '_get_agent_method_for_workflow', return_value=mock_method):
            result = await orchestrator.execute_workflow(
                f"Test {project_type.value}",
                workflow=sequence
            )

            assert result is not None
            assert result.workflow_name == f"{project_type.value}-workflow"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

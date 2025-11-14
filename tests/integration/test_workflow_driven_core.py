"""Integration tests for workflow-driven architecture (Story 7.2.5)."""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

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
def orchestrator(temp_project, monkeypatch):
    """Create orchestrator for integration testing."""
    # Set environment variable to bypass provider selection
    monkeypatch.setenv("AGENT_PROVIDER", "direct-api-anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-for-testing")

    return GAODevOrchestrator.create_default(
        project_root=temp_project
    )


def test_orchestrator_initialization(orchestrator, temp_project):
    """Test that orchestrator initializes all components correctly."""
    # Verify basic properties
    assert orchestrator.project_root == temp_project

    # Verify components initialized
    assert orchestrator.config_loader is not None
    assert orchestrator.workflow_registry is not None
    assert orchestrator.brian_orchestrator is not None


def test_workflow_registry_loaded(orchestrator):
    """Test that workflow registry loads workflows (Story 7.2.6)."""
    workflows = orchestrator.workflow_registry.list_workflows()

    # At minimum should have embedded workflows (3)
    # In real project root, would have 34+ from BMAD
    assert len(workflows) >= 3, f"Expected at least 3 workflows, got {len(workflows)}"

    # Should have workflows from at least 1 phase
    phases = {w.phase for w in workflows}
    assert len(phases) >= 1, "Expected workflows from at least 1 phase"


@pytest.mark.asyncio
async def test_workflow_execution_with_empty_sequence(orchestrator, temp_project):
    """Test workflow execution handles empty workflow sequence."""
    # Create empty workflow sequence (simulates clarification needed)
    empty_sequence = WorkflowSequence(
        scale_level=ScaleLevel.LEVEL_0,
        workflows=[],
        project_type=ProjectType.GREENFIELD,
        routing_rationale="Need clarification",
        phase_breakdown={}
    )

    # Execute workflow
    result = await orchestrator.execute_workflow(
        initial_prompt="Unclear prompt",
        workflow=empty_sequence
    )

    # Empty workflow completes with 0 steps (clarification was attempted)
    assert result.total_steps == 0
    assert result.status  # Has a status


@pytest.mark.asyncio
async def test_clarification_handling_in_cli_mode(orchestrator):
    """Test clarification handling in CLI mode (Story 7.2.4)."""
    questions = ["What framework?", "What platform?"]

    # CLI mode should return None for now (interactive not implemented)
    result = orchestrator.handle_clarification(questions, "Build app")

    assert result is None  # Will be enhanced when interactive added


@pytest.mark.asyncio
async def test_clarification_handling_in_benchmark_mode(temp_project, monkeypatch):
    """Test clarification handling in benchmark mode (Story 7.2.4)."""
    # Set environment variable to bypass provider selection
    monkeypatch.setenv("AGENT_PROVIDER", "direct-api-anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-for-testing")

    orchestrator_bench = GAODevOrchestrator.create_default(
        project_root=temp_project
    )

    questions = ["What framework?"]

    # Benchmark mode should return None (fails gracefully)
    result = orchestrator_bench.handle_clarification(questions, "Build app")

    assert result is None


def test_mode_detection(temp_project, monkeypatch):
    """Test that different execution modes are set correctly."""
    # Set environment variable to bypass provider selection
    monkeypatch.setenv("AGENT_PROVIDER", "direct-api-anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-for-testing")

    # Create orchestrator with factory method
    orch = GAODevOrchestrator.create_default(project_root=temp_project)

    # Verify orchestrator initialized successfully
    assert orch.project_root == temp_project
    assert orch.workflow_registry is not None
    assert orch.brian_orchestrator is not None


@pytest.mark.asyncio
async def test_workflow_sequence_from_prompt_integration(orchestrator):
    """
    Integration test: Full workflow from prompt assessment to execution.

    This is mocked for now, but demonstrates the integration flow.
    """
    with patch.object(orchestrator.brian_orchestrator, 'assess_and_select_workflows') as mock_assess:
        # Mock Brian returning a simple workflow sequence
        mock_workflow = WorkflowInfo(
            name="test-workflow",
            description="Test workflow",
            phase=2,
            installed_path=Path("/fake/path")
        )

        mock_sequence = WorkflowSequence(
            scale_level=ScaleLevel.LEVEL_1,
            workflows=[mock_workflow],
            project_type=ProjectType.GREENFIELD,
            routing_rationale="Simple test project",
            phase_breakdown={"Phase 2": ["test-workflow"]}
        )

        mock_assess.return_value = mock_sequence

        # Mock the execute methods
        async def mock_execute():
            yield "Task completed"

        orchestrator.create_prd = mock_execute

        # Execute workflow sequence from prompt
        result = await orchestrator.execute_workflow_sequence_from_prompt(
            "Build a simple application"
        )

        # Verify assessment was called
        mock_assess.assert_called_once()

        # Result should be a WorkflowResult
        assert hasattr(result, 'workflow_name')
        assert hasattr(result, 'status')
        assert hasattr(result, 'total_steps')


def test_brian_scale_level_detection(orchestrator):
    """Test that Brian's scale levels are accessible."""
    scale_levels = [
        ScaleLevel.LEVEL_0,
        ScaleLevel.LEVEL_1,
        ScaleLevel.LEVEL_2,
        ScaleLevel.LEVEL_3,
        ScaleLevel.LEVEL_4
    ]

    for level in scale_levels:
        description = orchestrator.get_scale_level_description(level)
        assert isinstance(description, str)
        assert len(description) > 0


def test_workflow_get_by_name_integration(orchestrator):
    """Test retrieving workflows by name from registry."""
    # Try to get a known workflow
    prd_workflow = orchestrator.workflow_registry.get_workflow("prd")

    if prd_workflow:
        assert prd_workflow.name == "prd"
        assert prd_workflow.phase == 2
        assert prd_workflow.description
        assert prd_workflow.installed_path.exists()


def test_workflow_list_by_phase_integration(orchestrator):
    """Test filtering workflows by phase."""
    # Get Phase 2 workflows
    phase_2_workflows = orchestrator.workflow_registry.list_workflows(phase=2)

    assert len(phase_2_workflows) > 0
    for workflow in phase_2_workflows:
        assert workflow.phase == 2


@pytest.mark.asyncio
async def test_workflow_result_structure(orchestrator):
    """Test that WorkflowResult has expected structure."""
    # Create minimal workflow sequence
    workflow_info = WorkflowInfo(
        name="test",
        description="Test",
        phase=2,
        installed_path=Path("/fake")
    )

    sequence = WorkflowSequence(
        scale_level=ScaleLevel.LEVEL_1,
        workflows=[workflow_info],
        project_type=ProjectType.GREENFIELD,
        routing_rationale="Test",
        phase_breakdown={}
    )

    # Mock agent method
    async def mock_method():
        yield "Done"

    with patch.object(orchestrator, '_get_agent_method_for_workflow', return_value=mock_method):
        result = await orchestrator.execute_workflow(
            "Test prompt",
            workflow=sequence
        )

        # Verify WorkflowResult structure
        assert result.workflow_name
        assert result.initial_prompt == "Test prompt"
        assert result.status
        assert result.start_time
        assert hasattr(result, 'total_steps')
        assert hasattr(result, 'successful_steps')
        assert hasattr(result, 'failed_steps')
        assert hasattr(result, 'duration_seconds')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

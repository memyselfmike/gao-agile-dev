"""
Unit tests for WorkflowExecutionEngine.

Tests the workflow execution engine extracted from orchestrator in Story 22.1.

Test Coverage:
- Engine initialization
- Workflow execution with variable resolution
- Task execution via prompts
- Error handling and retries
- Integration with WorkflowRegistry, WorkflowExecutor, and PromptLoader
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime

from gao_dev.orchestrator.workflow_execution_engine import WorkflowExecutionEngine
from gao_dev.orchestrator.workflow_results import WorkflowResult, WorkflowStatus
from gao_dev.core.models.workflow import WorkflowInfo
from gao_dev.core.workflow_registry import WorkflowRegistry
from gao_dev.core.workflow_executor import WorkflowExecutor
from gao_dev.core.prompt_loader import PromptLoader


@pytest.fixture
def mock_workflow_registry():
    """Create mock WorkflowRegistry."""
    registry = Mock(spec=WorkflowRegistry)
    return registry


@pytest.fixture
def mock_workflow_executor():
    """Create mock WorkflowExecutor."""
    executor = Mock(spec=WorkflowExecutor)
    return executor


@pytest.fixture
def mock_prompt_loader():
    """Create mock PromptLoader."""
    loader = Mock(spec=PromptLoader)
    return loader


@pytest.fixture
def mock_agent_executor():
    """Create mock agent executor (async generator)."""
    async def executor(workflow_info, **params):
        yield "Agent starting execution..."
        yield "Agent working..."
        yield "Agent completed successfully."

    return executor


@pytest.fixture
def sample_workflow_info():
    """Create sample WorkflowInfo for testing."""
    workflow_dir = Path(__file__).parent / "test_data" / "workflows" / "sample"
    workflow_dir.mkdir(parents=True, exist_ok=True)

    # Create instructions.md
    instructions_file = workflow_dir / "instructions.md"
    instructions_file.write_text(
        "Execute workflow for {{project_name}} with {{feature}} feature."
    )

    return WorkflowInfo(
        name="sample-workflow",
        description="Sample workflow for testing",
        phase=1,
        installed_path=workflow_dir,
        variables={
            "project_name": {"default": "TestProject", "required": False},
            "feature": {"default": "test-feature", "required": False},
        },
    )


@pytest.fixture
def workflow_engine(
    mock_workflow_registry,
    mock_workflow_executor,
    mock_prompt_loader,
    mock_agent_executor,
):
    """Create WorkflowExecutionEngine instance for testing."""
    return WorkflowExecutionEngine(
        workflow_registry=mock_workflow_registry,
        workflow_executor=mock_workflow_executor,
        prompt_loader=mock_prompt_loader,
        agent_executor=mock_agent_executor,
    )


class TestWorkflowExecutionEngineInitialization:
    """Test suite for engine initialization."""

    def test_engine_initialization(
        self,
        mock_workflow_registry,
        mock_workflow_executor,
        mock_prompt_loader,
        mock_agent_executor,
    ):
        """Test engine initializes with required dependencies."""
        engine = WorkflowExecutionEngine(
            workflow_registry=mock_workflow_registry,
            workflow_executor=mock_workflow_executor,
            prompt_loader=mock_prompt_loader,
            agent_executor=mock_agent_executor,
        )

        assert engine.workflow_registry == mock_workflow_registry
        assert engine.workflow_executor == mock_workflow_executor
        assert engine.prompt_loader == mock_prompt_loader
        assert engine.agent_executor == mock_agent_executor

    def test_engine_initialization_without_agent_executor(
        self,
        mock_workflow_registry,
        mock_workflow_executor,
        mock_prompt_loader,
    ):
        """Test engine can be initialized without agent executor."""
        engine = WorkflowExecutionEngine(
            workflow_registry=mock_workflow_registry,
            workflow_executor=mock_workflow_executor,
            prompt_loader=mock_prompt_loader,
            agent_executor=None,
        )

        assert engine.agent_executor is None


class TestWorkflowExecution:
    """Test suite for workflow execution."""

    @pytest.mark.asyncio
    async def test_execute_workflow_success(
        self,
        workflow_engine,
        mock_workflow_registry,
        mock_workflow_executor,
        sample_workflow_info,
    ):
        """Test successful workflow execution."""
        # Setup mocks
        mock_workflow_registry.get_workflow.return_value = sample_workflow_info
        mock_workflow_executor.resolve_variables.return_value = {
            "project_name": "MyApp",
            "feature": "auth",
            "date": "2025-11-09",
            "timestamp": "2025-11-09T10:00:00",
        }
        mock_workflow_executor.render_template.return_value = (
            "Execute workflow for MyApp with auth feature."
        )

        # Execute workflow
        result = await workflow_engine.execute(
            workflow_name="sample-workflow",
            params={"project_name": "MyApp", "feature": "auth"},
        )

        # Verify result
        assert result.status == WorkflowStatus.COMPLETED
        assert result.workflow_name == "sample-workflow"
        assert result.error_message is None
        assert result.start_time is not None
        assert result.end_time is not None

        # Verify mock calls
        mock_workflow_registry.get_workflow.assert_called_once_with("sample-workflow")
        mock_workflow_executor.resolve_variables.assert_called_once()
        mock_workflow_executor.render_template.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_workflow_with_variables(
        self,
        workflow_engine,
        mock_workflow_registry,
        mock_workflow_executor,
        sample_workflow_info,
    ):
        """Test workflow execution with variable resolution."""
        # Setup mocks
        mock_workflow_registry.get_workflow.return_value = sample_workflow_info

        # Simulate variable resolution
        expected_variables = {
            "project_name": "CustomApp",
            "feature": "payments",
            "date": "2025-11-09",
            "timestamp": "2025-11-09T10:00:00",
        }
        mock_workflow_executor.resolve_variables.return_value = expected_variables
        mock_workflow_executor.render_template.return_value = (
            "Execute workflow for CustomApp with payments feature."
        )

        # Execute workflow
        result = await workflow_engine.execute(
            workflow_name="sample-workflow",
            params={"project_name": "CustomApp", "feature": "payments"},
        )

        # Verify variable resolution was called with correct params
        call_args = mock_workflow_executor.resolve_variables.call_args
        assert call_args[0][0] == sample_workflow_info
        assert call_args[0][1]["project_name"] == "CustomApp"
        assert call_args[0][1]["feature"] == "payments"

        assert result.status == WorkflowStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_workflow_error_handling(
        self,
        workflow_engine,
        mock_workflow_registry,
    ):
        """Test workflow execution error handling."""
        # Simulate workflow not found
        mock_workflow_registry.get_workflow.return_value = None

        # Execute workflow
        result = await workflow_engine.execute(
            workflow_name="non-existent-workflow",
            params={},
        )

        # Verify error handling
        assert result.status == WorkflowStatus.FAILED
        assert "not found" in result.error_message.lower()
        assert result.end_time is not None

    @pytest.mark.asyncio
    async def test_workflow_not_found(
        self,
        workflow_engine,
        mock_workflow_registry,
    ):
        """Test handling of missing workflow."""
        # Setup mock to return None (workflow not found)
        mock_workflow_registry.get_workflow.return_value = None

        # Execute workflow
        result = await workflow_engine.execute(
            workflow_name="missing-workflow",
            params={},
        )

        # Verify error
        assert result.status == WorkflowStatus.FAILED
        assert "not found" in result.error_message.lower()
        assert result.workflow_name == "missing-workflow"

    @pytest.mark.asyncio
    async def test_execute_workflow_without_agent_executor(
        self,
        mock_workflow_registry,
        mock_workflow_executor,
        mock_prompt_loader,
        sample_workflow_info,
    ):
        """Test workflow execution fails without agent executor."""
        # Create engine without agent executor
        engine = WorkflowExecutionEngine(
            workflow_registry=mock_workflow_registry,
            workflow_executor=mock_workflow_executor,
            prompt_loader=mock_prompt_loader,
            agent_executor=None,
        )

        # Setup mocks
        mock_workflow_registry.get_workflow.return_value = sample_workflow_info
        mock_workflow_executor.resolve_variables.return_value = {}
        mock_workflow_executor.render_template.return_value = "Test instructions"

        # Execute workflow
        result = await engine.execute(
            workflow_name="sample-workflow",
            params={},
        )

        # Verify error
        assert result.status == WorkflowStatus.FAILED
        assert "no agent executor" in result.error_message.lower()


class TestTaskExecution:
    """Test suite for task execution."""

    @pytest.mark.asyncio
    async def test_execute_task_success(
        self,
        workflow_engine,
        mock_prompt_loader,
    ):
        """Test successful task execution."""
        # Setup mock prompt
        mock_template = Mock()
        mock_template.name = "create_prd"
        mock_prompt_loader.load_prompt.return_value = mock_template
        mock_prompt_loader.render_prompt.return_value = (
            "Use John agent to create PRD for MyApp."
        )

        # Execute task
        result = await workflow_engine.execute_task(
            task_name="create_prd",
            params={"project_name": "MyApp"},
        )

        # Verify result
        assert result.status == WorkflowStatus.COMPLETED
        assert result.workflow_name == "task:create_prd"
        assert result.error_message is None

        # Verify mock calls
        mock_prompt_loader.load_prompt.assert_called_once_with("tasks/create_prd")
        mock_prompt_loader.render_prompt.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_task_with_agent_mapping(
        self,
        workflow_engine,
        mock_prompt_loader,
    ):
        """Test task execution with agent parameter."""
        # Setup mock
        mock_template = Mock()
        mock_prompt_loader.load_prompt.return_value = mock_template
        mock_prompt_loader.render_prompt.return_value = "Execute story implementation"

        # Execute task
        result = await workflow_engine.execute_task(
            task_name="implement_story",
            params={"epic": "1", "story": "1", "agent": "Amelia"},
        )

        # Verify task execution
        assert result.status == WorkflowStatus.COMPLETED
        call_args = mock_prompt_loader.render_prompt.call_args
        assert "epic" in call_args[0][1]
        assert "story" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_execute_task_not_found(
        self,
        workflow_engine,
        mock_prompt_loader,
    ):
        """Test task execution with missing task prompt."""
        # Setup mock to return None (task not found)
        mock_prompt_loader.load_prompt.return_value = None

        # Execute task
        result = await workflow_engine.execute_task(
            task_name="non_existent_task",
            params={},
        )

        # Verify error
        assert result.status == WorkflowStatus.FAILED
        assert "not found" in result.error_message.lower()
        assert result.workflow_name == "task:non_existent_task"


class TestWorkflowResult:
    """Test suite for workflow result structure."""

    @pytest.mark.asyncio
    async def test_workflow_result_structure(
        self,
        workflow_engine,
        mock_workflow_registry,
        mock_workflow_executor,
        sample_workflow_info,
    ):
        """Test WorkflowResult has correct structure."""
        # Setup mocks
        mock_workflow_registry.get_workflow.return_value = sample_workflow_info
        mock_workflow_executor.resolve_variables.return_value = {}
        mock_workflow_executor.render_template.return_value = "Test"

        # Execute workflow
        result = await workflow_engine.execute(
            workflow_name="sample-workflow",
            params={},
        )

        # Verify result structure
        assert isinstance(result, WorkflowResult)
        assert hasattr(result, "workflow_name")
        assert hasattr(result, "status")
        assert hasattr(result, "start_time")
        assert hasattr(result, "end_time")
        assert hasattr(result, "error_message")
        assert hasattr(result, "initial_prompt")

    @pytest.mark.asyncio
    async def test_workflow_result_timing(
        self,
        workflow_engine,
        mock_workflow_registry,
        mock_workflow_executor,
        sample_workflow_info,
    ):
        """Test WorkflowResult timing information."""
        # Setup mocks
        mock_workflow_registry.get_workflow.return_value = sample_workflow_info
        mock_workflow_executor.resolve_variables.return_value = {}
        mock_workflow_executor.render_template.return_value = "Test"

        # Execute workflow
        result = await workflow_engine.execute(
            workflow_name="sample-workflow",
            params={},
        )

        # Verify timing
        assert result.start_time is not None
        assert result.end_time is not None
        assert result.end_time >= result.start_time
        assert result.duration_seconds is not None
        assert result.duration_seconds >= 0


class TestMultipleWorkflowExecution:
    """Test suite for sequential workflow execution."""

    @pytest.mark.asyncio
    async def test_multiple_workflow_execution(
        self,
        workflow_engine,
        mock_workflow_registry,
        mock_workflow_executor,
        sample_workflow_info,
    ):
        """Test executing multiple workflows sequentially."""
        # Setup mocks
        mock_workflow_registry.get_workflow.return_value = sample_workflow_info
        mock_workflow_executor.resolve_variables.return_value = {}
        mock_workflow_executor.render_template.return_value = "Test"

        # Execute first workflow
        result1 = await workflow_engine.execute(
            workflow_name="workflow-1",
            params={"param1": "value1"},
        )

        # Execute second workflow
        result2 = await workflow_engine.execute(
            workflow_name="workflow-2",
            params={"param2": "value2"},
        )

        # Verify both succeeded
        assert result1.status == WorkflowStatus.COMPLETED
        assert result2.status == WorkflowStatus.COMPLETED
        assert result1.start_time < result2.start_time


class TestVariableResolution:
    """Test suite for variable resolution logic."""

    @pytest.mark.asyncio
    async def test_variable_resolution(
        self,
        workflow_engine,
        mock_workflow_registry,
        mock_workflow_executor,
        sample_workflow_info,
    ):
        """Test variable resolution from multiple sources."""
        # Setup expected variables
        expected_vars = {
            "project_name": "MyApp",
            "feature": "auth",
            "date": "2025-11-09",
            "timestamp": "2025-11-09T10:00:00",
        }

        mock_workflow_registry.get_workflow.return_value = sample_workflow_info
        mock_workflow_executor.resolve_variables.return_value = expected_vars
        mock_workflow_executor.render_template.return_value = "Rendered instructions"

        # Execute workflow
        await workflow_engine.execute(
            workflow_name="sample-workflow",
            params={"project_name": "MyApp", "feature": "auth"},
        )

        # Verify variable resolution was called
        assert mock_workflow_executor.resolve_variables.called
        call_args = mock_workflow_executor.resolve_variables.call_args

        # Verify workflow info passed
        assert call_args[0][0] == sample_workflow_info

        # Verify params passed
        assert "project_name" in call_args[0][1]
        assert "feature" in call_args[0][1]

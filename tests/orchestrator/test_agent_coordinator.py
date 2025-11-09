"""Unit tests for AgentCoordinator service.

Tests the agent coordination service extracted in Story 22.3
from GAODevOrchestrator.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock
from gao_dev.orchestrator.agent_coordinator import AgentCoordinator
from gao_dev.core.services.process_executor import ProcessExecutor


@pytest.fixture
def mock_process_executor():
    """Create mock ProcessExecutor."""
    executor = Mock(spec=ProcessExecutor)
    # Note: execute_agent_task will be set per test
    return executor


@pytest.fixture
def project_root(tmp_path):
    """Create temporary project root."""
    return tmp_path / "test-project"


@pytest.fixture
def coordinator(mock_process_executor, project_root):
    """Create AgentCoordinator instance."""
    return AgentCoordinator(
        process_executor=mock_process_executor,
        project_root=project_root,
    )


class TestAgentCoordinatorInitialization:
    """Test AgentCoordinator initialization."""

    def test_coordinator_initialization(self, coordinator, project_root, mock_process_executor):
        """Test coordinator initializes with correct attributes."""
        assert coordinator.process_executor == mock_process_executor
        assert coordinator.project_root == project_root
        assert isinstance(coordinator._agent_cache, dict)
        assert len(coordinator._agent_cache) == 0


class TestExecuteTask:
    """Test execute_task method."""

    @pytest.mark.asyncio
    async def test_execute_task_success(self, project_root):
        """Test successful task execution."""
        # Setup
        instructions = "Implement Story 1.1"
        agent_name = "Amelia"
        context = {"epic": 1, "story": 1}

        # Create mock executor with async generator
        mock_executor = Mock(spec=ProcessExecutor)

        async def mock_output(**kwargs):
            yield "Starting task..."
            yield "Task complete"

        mock_executor.execute_agent_task = mock_output

        # Create coordinator with mock
        coordinator = AgentCoordinator(
            process_executor=mock_executor,
            project_root=project_root,
        )

        # Execute
        outputs = []
        async for output in coordinator.execute_task(
            agent_name=agent_name,
            instructions=instructions,
            context=context,
        ):
            outputs.append(output)

        # Verify
        assert len(outputs) == 2
        assert outputs[0] == "Starting task..."
        assert outputs[1] == "Task complete"

    @pytest.mark.asyncio
    async def test_execute_task_with_context(self, project_root):
        """Test task execution with custom context."""
        # Setup
        instructions = "Create PRD"
        agent_name = "John"
        context = {
            "epic": 1,
            "story": None,
            "workflow_name": "prd",
            "project_name": "TestApp",
        }

        # Create mock executor with async generator
        mock_executor = Mock(spec=ProcessExecutor)

        async def mock_output(**kwargs):
            yield "Creating PRD..."

        mock_executor.execute_agent_task = mock_output

        # Create coordinator with mock
        coordinator = AgentCoordinator(
            process_executor=mock_executor,
            project_root=project_root,
        )

        # Execute
        outputs = []
        async for output in coordinator.execute_task(
            agent_name=agent_name,
            instructions=instructions,
            context=context,
        ):
            outputs.append(output)

        # Verify
        assert len(outputs) == 1
        assert outputs[0] == "Creating PRD..."

    @pytest.mark.asyncio
    async def test_execute_task_error_handling(self, project_root):
        """Test task execution error handling."""
        # Setup
        instructions = "Do something that fails"
        agent_name = "Amelia"

        # Create mock executor that raises error
        mock_executor = Mock(spec=ProcessExecutor)

        async def mock_error(**kwargs):
            raise RuntimeError("Execution failed")
            yield  # Never reached but needed for generator

        mock_executor.execute_agent_task = mock_error

        # Create coordinator with mock
        coordinator = AgentCoordinator(
            process_executor=mock_executor,
            project_root=project_root,
        )

        # Execute and verify exception is raised
        with pytest.raises(RuntimeError) as exc_info:
            async for _ in coordinator.execute_task(
                agent_name=agent_name,
                instructions=instructions,
            ):
                pass

        assert str(exc_info.value) == "Execution failed"

    @pytest.mark.asyncio
    async def test_execute_task_with_custom_tools(self, project_root):
        """Test task execution with custom tools."""
        # Setup
        instructions = "Run tests"
        agent_name = "Murat"
        custom_tools = ["Read", "Bash", "TodoWrite"]

        # Track what was passed to executor
        captured_kwargs = {}

        # Create mock executor with async generator
        mock_executor = Mock(spec=ProcessExecutor)

        async def mock_output(**kwargs):
            captured_kwargs.update(kwargs)
            yield "Running tests..."

        mock_executor.execute_agent_task = mock_output

        # Create coordinator with mock
        coordinator = AgentCoordinator(
            process_executor=mock_executor,
            project_root=project_root,
        )

        # Execute
        outputs = []
        async for output in coordinator.execute_task(
            agent_name=agent_name,
            instructions=instructions,
            tools=custom_tools,
        ):
            outputs.append(output)

        # Verify custom tools were passed
        assert captured_kwargs["tools"] == custom_tools


class TestGetAgent:
    """Test get_agent method."""

    def test_get_agent_for_workflow_prd(self, coordinator):
        """Test PRD workflow maps to John."""
        agent = coordinator.get_agent("prd")
        assert agent == "John"

        agent = coordinator.get_agent("create-prd")
        assert agent == "John"

    def test_get_agent_for_workflow_story(self, coordinator):
        """Test story workflow maps to Bob."""
        agent = coordinator.get_agent("story-create")
        assert agent == "Bob"

        agent = coordinator.get_agent("create-story")
        assert agent == "Bob"

    def test_get_agent_for_workflow_implementation(self, coordinator):
        """Test implementation workflow maps to Amelia."""
        agent = coordinator.get_agent("story-implement")
        assert agent == "Amelia"

        agent = coordinator.get_agent("dev-implement")
        assert agent == "Amelia"

    def test_get_agent_for_workflow_architecture(self, coordinator):
        """Test architecture workflow maps to Winston."""
        agent = coordinator.get_agent("architecture")
        assert agent == "Winston"

        agent = coordinator.get_agent("tech-spec")
        assert agent == "Winston"

    def test_get_agent_for_workflow_test(self, coordinator):
        """Test test workflow maps to Murat."""
        agent = coordinator.get_agent("test-strategy")
        assert agent == "Murat"

        agent = coordinator.get_agent("qa-review")
        assert agent == "Murat"

    def test_get_agent_for_workflow_ux(self, coordinator):
        """Test UX workflow maps to Sally."""
        agent = coordinator.get_agent("ux-design")
        assert agent == "Sally"

        agent = coordinator.get_agent("design-wireframe")
        assert agent == "Sally"

    def test_get_agent_for_workflow_research(self, coordinator):
        """Test research workflow maps to Mary."""
        agent = coordinator.get_agent("research")
        assert agent == "Mary"

        agent = coordinator.get_agent("brief")
        assert agent == "Mary"

    def test_get_agent_for_workflow_default(self, coordinator):
        """Test unknown workflow maps to Orchestrator."""
        agent = coordinator.get_agent("unknown-workflow")
        assert agent == "Orchestrator"


class TestMultipleAgentExecution:
    """Test multiple agent execution scenarios."""

    @pytest.mark.asyncio
    async def test_multiple_agent_execution(self, project_root):
        """Test sequential execution of multiple agents."""
        # Create mock executor
        mock_executor = Mock(spec=ProcessExecutor)
        call_count = 0

        async def mock_output(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                yield "John creating PRD..."
            else:
                yield "Winston designing architecture..."

        mock_executor.execute_agent_task = mock_output

        # Create coordinator with mock
        coordinator = AgentCoordinator(
            process_executor=mock_executor,
            project_root=project_root,
        )

        # Execute John task
        john_outputs = []
        async for output in coordinator.execute_task(
            agent_name="John",
            instructions="Create PRD",
        ):
            john_outputs.append(output)

        # Execute Winston task
        winston_outputs = []
        async for output in coordinator.execute_task(
            agent_name="Winston",
            instructions="Create architecture",
        ):
            winston_outputs.append(output)

        # Verify
        assert len(john_outputs) == 1
        assert len(winston_outputs) == 1
        assert "John" in john_outputs[0]
        assert "Winston" in winston_outputs[0]

        # Verify executor was called twice
        assert call_count == 2


class TestAgentCaching:
    """Test agent caching functionality."""

    def test_agent_caching(self, coordinator):
        """Test agent cache is available for future extensions."""
        # Agent cache exists but is not currently used
        # This test ensures the infrastructure is in place
        assert hasattr(coordinator, "_agent_cache")
        assert isinstance(coordinator._agent_cache, dict)

        # Cache can be used for future agent instance caching
        coordinator._agent_cache["test_agent"] = Mock()
        assert "test_agent" in coordinator._agent_cache
        assert coordinator._agent_cache["test_agent"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

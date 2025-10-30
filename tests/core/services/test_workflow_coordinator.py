"""Tests for WorkflowCoordinator service."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from pathlib import Path
from datetime import datetime

from gao_dev.core.services.workflow_coordinator import WorkflowCoordinator
from gao_dev.core.events.event_bus import EventBus, Event
from gao_dev.core.models.workflow import WorkflowInfo
from gao_dev.orchestrator.models import WorkflowSequence, ScaleLevel, ProjectType
from gao_dev.core.models.workflow_context import WorkflowContext


@pytest.fixture
def mock_workflow_registry():
    """Mock IWorkflowRegistry."""
    registry = Mock()
    return registry


@pytest.fixture
def mock_agent_factory():
    """Mock IAgentFactory."""
    factory = Mock()
    return factory


@pytest.fixture
def event_bus():
    """Real EventBus for testing event publishing."""
    return EventBus()


@pytest.fixture
def mock_agent_executor():
    """Mock agent executor callback."""
    async def executor(workflow_info, epic=1, story=1):
        yield "Agent executed successfully"
    return executor


@pytest.fixture
def coordinator(
    mock_workflow_registry,
    mock_agent_factory,
    event_bus,
    mock_agent_executor
):
    """Create WorkflowCoordinator with mocked dependencies."""
    return WorkflowCoordinator(
        workflow_registry=mock_workflow_registry,
        agent_factory=mock_agent_factory,
        event_bus=event_bus,
        agent_executor=mock_agent_executor,
        project_root=Path("/fake/project"),
        max_retries=3
    )


@pytest.mark.asyncio
class TestWorkflowCoordinator:
    """Test suite for WorkflowCoordinator."""

    async def test_execute_sequence_success(self, coordinator, event_bus):
        """Test successful workflow sequence execution."""
        # Setup
        workflow_sequence = WorkflowSequence(
            scale_level=ScaleLevel.LEVEL_1,
            project_type=ProjectType.SOFTWARE,
            workflows=[
                WorkflowInfo(
                    name="prd",
                    description="Create PRD",
                    phase=2,
                    installed_path=Path("/fake/workflows/prd")
                ),
                WorkflowInfo(
                    name="create-story",
                    description="Create story",
                    phase=4,
                    installed_path=Path("/fake/workflows/create-story")
                )
            ],
            routing_rationale="Test sequence",
            phase_breakdown={"planning": ["prd"], "implementation": ["create-story"]}
        )

        context = WorkflowContext(
            initial_prompt="Test prompt",
            project_root=Path("/fake/project")
        )

        # Track events
        events_received = []
        event_bus.subscribe("WorkflowSequenceStarted", lambda e: events_received.append(e))
        event_bus.subscribe("WorkflowStepStarted", lambda e: events_received.append(e))
        event_bus.subscribe("WorkflowStepCompleted", lambda e: events_received.append(e))
        event_bus.subscribe("WorkflowSequenceCompleted", lambda e: events_received.append(e))

        # Execute
        result = await coordinator.execute_sequence(workflow_sequence, context)

        # Assert
        assert result.status.value == "completed"
        assert len(result.step_results) == 2
        assert result.step_results[0].status == "success"
        assert result.step_results[1].status == "success"

        # Assert events published
        assert len([e for e in events_received if e.type == "WorkflowSequenceStarted"]) == 1
        assert len([e for e in events_received if e.type == "WorkflowStepStarted"]) == 2
        assert len([e for e in events_received if e.type == "WorkflowStepCompleted"]) == 2
        assert len([e for e in events_received if e.type == "WorkflowSequenceCompleted"]) == 1


    async def test_execute_sequence_empty(self, coordinator):
        """Test execution of empty workflow sequence."""
        workflow_sequence = WorkflowSequence(
            scale_level=ScaleLevel.LEVEL_0,
            project_type=ProjectType.SOFTWARE,
            workflows=[],
            routing_rationale="Empty",
            phase_breakdown={}
        )

        context = WorkflowContext(
            initial_prompt="Test prompt",
            project_root=Path("/fake/project")
        )

        result = await coordinator.execute_sequence(workflow_sequence, context)

        assert result.status.value == "failed"
        assert "Empty workflow sequence" in result.error_message


    async def test_execute_workflow_with_retry(self, event_bus):
        """Test workflow retries on failure."""
        # Setup: Agent executor that fails twice then succeeds
        call_count = 0

        async def failing_executor(workflow_info, epic=1, story=1):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise RuntimeError("Temporary failure")
            yield "Success on third try"

        coordinator = WorkflowCoordinator(
            workflow_registry=Mock(),
            agent_factory=Mock(),
            event_bus=event_bus,
            agent_executor=failing_executor,
            project_root=Path("/fake"),
            max_retries=3
        )

        # Track retry events
        retry_events = []
        event_bus.subscribe("WorkflowStepFailed", lambda e: retry_events.append(e))

        # Execute
        workflow_info = WorkflowInfo(
            name="test",
            description="Test",
            phase=4,
            installed_path=Path("/fake/test")
        )
        context = WorkflowContext(
            initial_prompt="Test",
            project_root=Path("/fake")
        )

        result = await coordinator.execute_workflow(
            workflow_id="test",
            workflow_info=workflow_info,
            step_number=1,
            total_steps=1,
            context=context
        )

        # Assert
        assert result.status == "success"
        assert call_count == 3
        assert len(retry_events) == 2  # Failed twice before success


    async def test_execute_workflow_max_retries_exceeded(self, event_bus):
        """Test workflow fails after max retries."""
        # Setup: Agent executor that always fails
        async def always_failing_executor(workflow_info, epic=1, story=1):
            raise RuntimeError("Permanent failure")

        coordinator = WorkflowCoordinator(
            workflow_registry=Mock(),
            agent_factory=Mock(),
            event_bus=event_bus,
            agent_executor=always_failing_executor,
            project_root=Path("/fake"),
            max_retries=2
        )

        # Execute
        workflow_info = WorkflowInfo(
            name="test",
            description="Test",
            phase=4,
            installed_path=Path("/fake/test")
        )
        context = WorkflowContext(
            initial_prompt="Test",
            project_root=Path("/fake")
        )

        result = await coordinator.execute_workflow(
            workflow_id="test",
            workflow_info=workflow_info,
            step_number=1,
            total_steps=1,
            context=context
        )

        # Assert
        assert result.status == "failed"
        assert "Failed after 2 retries" in result.error_message


    async def test_get_agent_for_workflow(self, coordinator):
        """Test agent selection based on workflow name."""
        test_cases = [
            (WorkflowInfo(name="prd", description="", phase=2, installed_path=Path("/fake")), "John"),
            (WorkflowInfo(name="create-story", description="", phase=4, installed_path=Path("/fake")), "Bob"),
            (WorkflowInfo(name="dev-story", description="", phase=4, installed_path=Path("/fake")), "Amelia"),
            (WorkflowInfo(name="architecture", description="", phase=3, installed_path=Path("/fake")), "Winston"),
            (WorkflowInfo(name="test-plan", description="", phase=4, installed_path=Path("/fake")), "Murat"),
            (WorkflowInfo(name="ux-design", description="", phase=2, installed_path=Path("/fake")), "Sally"),
            (WorkflowInfo(name="research-brief", description="", phase=1, installed_path=Path("/fake")), "Mary"),
            (WorkflowInfo(name="unknown", description="", phase=1, installed_path=Path("/fake")), "Orchestrator"),
        ]

        for workflow_info, expected_agent in test_cases:
            agent = coordinator._get_agent_for_workflow(workflow_info)
            assert agent == expected_agent, f"Workflow {workflow_info.name} should map to {expected_agent}"


    async def test_execute_sequence_with_failure(self, event_bus):
        """Test sequence execution stops on step failure."""
        # Setup: Executor that fails on second workflow
        call_count = 0

        async def selective_failing_executor(workflow_info, epic=1, story=1):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise RuntimeError("Step 2 failure")
            yield f"Step {call_count} success"

        coordinator = WorkflowCoordinator(
            workflow_registry=Mock(),
            agent_factory=Mock(),
            event_bus=event_bus,
            agent_executor=selective_failing_executor,
            project_root=Path("/fake"),
            max_retries=0  # Fail immediately
        )

        # Track events
        events_received = []
        event_bus.subscribe("WorkflowSequenceFailed", lambda e: events_received.append(e))

        # Execute
        workflow_sequence = WorkflowSequence(
            scale_level=ScaleLevel.LEVEL_1,
            project_type=ProjectType.SOFTWARE,
            workflows=[
                WorkflowInfo(name="step1", description="Step 1", phase=4, installed_path=Path("/fake")),
                WorkflowInfo(name="step2", description="Step 2", phase=4, installed_path=Path("/fake")),
                WorkflowInfo(name="step3", description="Step 3", phase=4, installed_path=Path("/fake"))
            ],
            routing_rationale="Test sequence",
            phase_breakdown={"implementation": ["step1", "step2", "step3"]}
        )

        context = WorkflowContext(
            initial_prompt="Test prompt",
            project_root=Path("/fake")
        )

        result = await coordinator.execute_sequence(workflow_sequence, context)

        # Assert
        assert result.status.value == "failed"
        assert len(result.step_results) == 2  # Only 2 steps executed
        assert result.step_results[0].status == "success"
        assert result.step_results[1].status == "failed"
        assert len(events_received) == 1  # WorkflowSequenceFailed event
        assert events_received[0].data["failed_at_step"] == 2


    async def test_coordinator_initialization(
        self,
        mock_workflow_registry,
        mock_agent_factory,
        event_bus,
        mock_agent_executor
    ):
        """Test WorkflowCoordinator initializes correctly."""
        coordinator = WorkflowCoordinator(
            workflow_registry=mock_workflow_registry,
            agent_factory=mock_agent_factory,
            event_bus=event_bus,
            agent_executor=mock_agent_executor,
            project_root=Path("/test/path"),
            max_retries=5
        )

        assert coordinator.workflow_registry is mock_workflow_registry
        assert coordinator.agent_factory is mock_agent_factory
        assert coordinator.event_bus is event_bus
        assert coordinator.agent_executor is mock_agent_executor
        assert coordinator.project_root == Path("/test/path")
        assert coordinator.max_retries == 5


    async def test_execute_sequence_exception_handling(self, coordinator, event_bus):
        """Test sequence handles unexpected exceptions gracefully."""
        # Create a coordinator with an executor that raises unexpected error
        async def exception_executor(workflow_info, epic=1, story=1):
            raise ValueError("Unexpected error")

        bad_coordinator = WorkflowCoordinator(
            workflow_registry=Mock(),
            agent_factory=Mock(),
            event_bus=event_bus,
            agent_executor=exception_executor,
            project_root=Path("/fake"),
            max_retries=0
        )

        workflow_sequence = WorkflowSequence(
            scale_level=ScaleLevel.LEVEL_1,
            project_type=ProjectType.SOFTWARE,
            workflows=[WorkflowInfo(name="test", description="Test", phase=4, installed_path=Path("/fake"))],
            routing_rationale="Test",
            phase_breakdown={"implementation": ["test"]}
        )

        context = WorkflowContext(
            initial_prompt="Test",
            project_root=Path("/fake")
        )

        result = await bad_coordinator.execute_sequence(workflow_sequence, context)

        # Should handle exception gracefully
        assert result.status.value == "failed"
        assert result.error_message is not None
        assert result.end_time is not None

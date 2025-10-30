# Story 6.1 Implementation Plan - Extract WorkflowCoordinator Service

**Epic**: 6 - Legacy Cleanup & God Class Refactoring
**Story Points**: 5
**Priority**: P0 (Critical)
**Assigned To**: Amelia (Developer)
**Status**: In Progress
**Branch**: feature/epic-6-legacy-cleanup

---

## Context & Overview

### What We're Building

A focused `WorkflowCoordinator` service responsible for executing workflow sequences. This is the FIRST service extraction from the 1,327-line God Class orchestrator.

### Why This Matters

- **God Class Problem**: orchestrator.py has 1,327 lines doing everything
- **Single Responsibility**: Each service should do ONE thing well
- **SOLID Principles**: This is step 1 of achieving complete SOLID compliance
- **Epic 2 Reference**: We have a working implementation on Epic 2 branch to learn from

### Current State

- **Branch**: feature/epic-6-legacy-cleanup (already created)
- **Test Suite**: 550 tests passing (regression baseline)
- **Dependencies**: All required (Epic 1, 3, 4, 5 complete)
- **Epic 2 Branch**: Working implementation exists as reference

---

## Dependencies & Prerequisites

### Available Dependencies (Completed Epics)

✅ **Epic 1 - Interfaces** (AVAILABLE)
- `IWorkflowRegistry` - D:\GAO Agile Dev\gao_dev\core\interfaces\workflow.py
- `IAgentFactory` - D:\GAO Agile Dev\gao_dev\core\interfaces\agent.py
- `IEventBus` - D:\GAO Agile Dev\gao_dev\core\interfaces\event_bus.py

✅ **Epic 3 - Design Patterns** (AVAILABLE)
- `EventBus` implementation - D:\GAO Agile Dev\gao_dev\core\events\event_bus.py
- `AgentFactory` - D:\GAO Agile Dev\gao_dev\core\agent_factory.py

✅ **Epic 4 - Plugin Architecture** (AVAILABLE)
- Plugin system (not needed for this story)

✅ **Epic 5 - Methodology Abstraction** (AVAILABLE)
- Generic methodology models

### Models Available

- `WorkflowContext` - D:\GAO Agile Dev\gao_dev\core\models\workflow_context.py
- `WorkflowResult` - D:\GAO Agile Dev\gao_dev\core\models\workflow.py
- `WorkflowSequence` - D:\GAO Agile Dev\gao_dev\orchestrator\brian_orchestrator.py
- `Event` - D:\GAO Agile Dev\gao_dev\core\events\event_bus.py

### Reference Implementation

Epic 2 branch has working `WorkflowCoordinator`:
```bash
git show feature/epic-2-god-class-refactoring:gao_dev/core/services/workflow_coordinator.py
```

---

## Implementation Steps

### Phase 1: Setup Service Structure

#### Task 1.1: Create Service Directory
```bash
# Create services directory if it doesn't exist
mkdir -p gao_dev/core/services
```

**Files to create**:
- `gao_dev/core/services/__init__.py`
- `gao_dev/core/services/workflow_coordinator.py`

**Action**: Create directory and empty files

---

#### Task 1.2: Define Event Models

Before implementing the service, define the events it will publish.

**File**: `gao_dev/core/services/workflow_coordinator.py`

**Events to define** (as dataclasses):
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class WorkflowSequenceStarted:
    """Published when workflow sequence begins."""
    sequence_id: str
    workflow_count: int
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class WorkflowStepStarted:
    """Published when individual workflow step starts."""
    workflow_id: str
    step_number: int
    total_steps: int
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class WorkflowStepCompleted:
    """Published when workflow step completes successfully."""
    workflow_id: str
    step_number: int
    duration_seconds: float
    artifacts: list[str]
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class WorkflowStepFailed:
    """Published when workflow step fails."""
    workflow_id: str
    step_number: int
    error: str
    retry_count: int
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class WorkflowSequenceCompleted:
    """Published when entire sequence completes."""
    sequence_id: str
    duration_seconds: float
    total_steps: int
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class WorkflowSequenceFailed:
    """Published when sequence fails."""
    sequence_id: str
    failed_at_step: int
    error: str
    timestamp: datetime = field(default_factory=datetime.now)
```

**Why**: Events provide observability and enable loose coupling

---

### Phase 2: Implement WorkflowCoordinator Core

#### Task 2.1: Implement Constructor

**File**: `gao_dev/core/services/workflow_coordinator.py`

**Implementation**:
```python
import structlog
from typing import Callable
from pathlib import Path

from ..interfaces.workflow import IWorkflowRegistry
from ..interfaces.agent import IAgentFactory
from ..interfaces.event_bus import IEventBus
from ..events.event_bus import Event

logger = structlog.get_logger()


class WorkflowCoordinator:
    """
    Coordinates execution of workflow sequences.

    Single Responsibility: Execute workflows in sequence order, manage workflow
    context, publish lifecycle events, handle errors and retries.

    This service was extracted from GAODevOrchestrator (Epic 6, Story 6.1) to
    follow the Single Responsibility Principle.

    Responsibilities:
    - Execute workflows in sequence order
    - Manage workflow context across steps
    - Publish workflow lifecycle events
    - Handle workflow step failures with retry logic

    NOT responsible for:
    - Story lifecycle management (StoryLifecycleManager)
    - Quality gate validation (QualityGateManager)
    - Subprocess execution (ProcessExecutor)
    - Orchestrator-level logic (stays in orchestrator)

    Example:
        ```python
        coordinator = WorkflowCoordinator(
            workflow_registry=registry,
            agent_factory=factory,
            event_bus=bus,
            max_retries=3
        )

        result = await coordinator.execute_sequence(
            workflow_sequence=sequence,
            context=context
        )
        ```
    """

    def __init__(
        self,
        workflow_registry: IWorkflowRegistry,
        agent_factory: IAgentFactory,
        event_bus: IEventBus,
        agent_executor: Callable,  # Callback to execute agent task
        project_root: Path,
        max_retries: int = 3
    ):
        """
        Initialize coordinator with injected dependencies.

        Args:
            workflow_registry: Registry to lookup workflows
            agent_factory: Factory to create agents (future use)
            event_bus: Event bus for publishing lifecycle events
            agent_executor: Callback function to execute agent tasks
            project_root: Root directory of the project
            max_retries: Maximum retry attempts for failed workflows (default: 3)
        """
        self.workflow_registry = workflow_registry
        self.agent_factory = agent_factory
        self.event_bus = event_bus
        self.agent_executor = agent_executor
        self.project_root = project_root
        self.max_retries = max_retries

        logger.info(
            "workflow_coordinator_initialized",
            max_retries=max_retries,
            project_root=str(project_root)
        )
```

**Key Points**:
- All dependencies injected via constructor (Dependency Injection pattern)
- Single responsibility clearly documented
- Logging for observability
- Type hints throughout

---

#### Task 2.2: Implement execute_sequence() Method

This is the PRIMARY method that executes workflow sequences.

**Implementation**:
```python
async def execute_sequence(
    self,
    workflow_sequence: 'WorkflowSequence',
    context: 'WorkflowContext'
) -> 'WorkflowResult':
    """
    Execute a sequence of workflows step-by-step.

    Coordinates execution of multiple workflows in order, managing context
    passing, error handling, and event publishing.

    Args:
        workflow_sequence: Sequence of workflows to execute
        context: Execution context with project info and parameters

    Returns:
        WorkflowResult with execution status and artifacts

    Raises:
        WorkflowExecutionError: If sequence fails after max retries
    """
    from datetime import datetime
    from ...orchestrator.workflow_results import (
        WorkflowResult,
        WorkflowStatus
    )

    # Initialize result
    result = WorkflowResult(
        workflow_name=(
            workflow_sequence.workflows[0].name
            if workflow_sequence.workflows
            else "empty-sequence"
        ),
        initial_prompt=context.initial_prompt,
        status=WorkflowStatus.IN_PROGRESS,
        start_time=datetime.now(),
        project_path=str(context.project_root) if context.project_root else str(self.project_root)
    )

    try:
        # Validate sequence
        if not workflow_sequence.workflows:
            result.status = WorkflowStatus.FAILED
            result.error_message = "Empty workflow sequence"
            logger.warning("empty_workflow_sequence")
            return result

        # Generate sequence ID for tracking
        sequence_id = f"seq_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Publish sequence started event
        self.event_bus.publish(Event(
            type="WorkflowSequenceStarted",
            data={
                "sequence_id": sequence_id,
                "workflow_count": len(workflow_sequence.workflows)
            }
        ))

        logger.info(
            "workflow_sequence_started",
            sequence_id=sequence_id,
            workflow_count=len(workflow_sequence.workflows)
        )

        # Execute workflows step by step
        for i, workflow_info in enumerate(workflow_sequence.workflows, 1):
            logger.info(
                "workflow_step_starting",
                step=i,
                total=len(workflow_sequence.workflows),
                workflow=workflow_info.name
            )

            # Execute single workflow step
            step_result = await self.execute_workflow(
                workflow_id=workflow_info.name,
                workflow_info=workflow_info,
                step_number=i,
                total_steps=len(workflow_sequence.workflows),
                context=context
            )

            result.step_results.append(step_result)

            # Check for failure
            if step_result.status == "failed":
                logger.error(
                    "workflow_step_failed",
                    step=workflow_info.name,
                    error=step_result.error_message
                )
                result.status = WorkflowStatus.FAILED
                result.error_message = f"Step {i} failed: {step_result.error_message}"

                # Publish sequence failed event
                self.event_bus.publish(Event(
                    type="WorkflowSequenceFailed",
                    data={
                        "sequence_id": sequence_id,
                        "failed_at_step": i,
                        "error": step_result.error_message
                    }
                ))
                break

        # Mark as completed if all steps succeeded
        if result.status != WorkflowStatus.FAILED:
            result.status = WorkflowStatus.COMPLETED
            result.end_time = datetime.now()

            # Publish sequence completed event
            self.event_bus.publish(Event(
                type="WorkflowSequenceCompleted",
                data={
                    "sequence_id": sequence_id,
                    "duration_seconds": (result.end_time - result.start_time).total_seconds(),
                    "total_steps": len(result.step_results)
                }
            ))

            logger.info(
                "workflow_sequence_completed",
                sequence_id=sequence_id,
                steps=len(result.step_results),
                duration=(result.end_time - result.start_time).total_seconds()
            )

    except Exception as e:
        result.status = WorkflowStatus.FAILED
        result.error_message = str(e)
        logger.error(
            "workflow_sequence_error",
            error=str(e),
            exc_info=True
        )

    finally:
        result.end_time = datetime.now()
        result.total_artifacts = sum(
            len(step.artifacts_created) for step in result.step_results
        )

    return result
```

**Key Points**:
- Event publishing at key lifecycle points
- Error handling with fail-fast
- Context passing between steps
- Comprehensive logging

---

#### Task 2.3: Implement execute_workflow() Method

This executes a single workflow step with retry logic.

**Implementation**:
```python
async def execute_workflow(
    self,
    workflow_id: str,
    workflow_info: 'WorkflowInfo',
    step_number: int,
    total_steps: int,
    context: 'WorkflowContext',
    epic: int = 1,
    story: int = 1
) -> 'WorkflowStepResult':
    """
    Execute a single workflow step with retry logic.

    Publishes events for workflow step lifecycle. Retries on failure up to
    max_retries times with exponential backoff.

    Args:
        workflow_id: Workflow identifier
        workflow_info: Workflow metadata
        step_number: Current step number in sequence
        total_steps: Total steps in sequence
        context: Execution context
        epic: Epic number for story workflows (default: 1)
        story: Story number for story workflows (default: 1)

    Returns:
        WorkflowStepResult with execution status
    """
    from datetime import datetime
    from ...orchestrator.workflow_results import WorkflowStepResult
    import asyncio

    step_result = WorkflowStepResult(
        step_name=workflow_info.name,
        agent=self._get_agent_for_workflow(workflow_info),
        status="in_progress",
        start_time=datetime.now()
    )

    # Publish step started event
    self.event_bus.publish(Event(
        type="WorkflowStepStarted",
        data={
            "workflow_id": workflow_id,
            "step_number": step_number,
            "total_steps": total_steps
        }
    ))

    logger.info(
        "workflow_step_started",
        workflow=workflow_id,
        step=step_number,
        agent=step_result.agent
    )

    # Retry loop
    retry_count = 0
    last_error = None

    while retry_count <= self.max_retries:
        try:
            # Execute agent task via callback
            output_parts = []
            async for message in self.agent_executor(workflow_info, epic, story):
                output_parts.append(message)

            step_result.output = "\n".join(output_parts)
            step_result.status = "success"

            # Publish step completed event
            step_result.end_time = datetime.now()
            self.event_bus.publish(Event(
                type="WorkflowStepCompleted",
                data={
                    "workflow_id": workflow_id,
                    "step_number": step_number,
                    "duration_seconds": (
                        step_result.end_time - step_result.start_time
                    ).total_seconds(),
                    "artifacts": step_result.artifacts_created
                }
            ))

            logger.info(
                "workflow_step_completed",
                workflow=workflow_id,
                agent=step_result.agent,
                retry_count=retry_count
            )
            break  # Success, exit retry loop

        except Exception as e:
            last_error = e
            retry_count += 1

            logger.warning(
                "workflow_step_failed_retrying",
                workflow=workflow_id,
                retry_count=retry_count,
                max_retries=self.max_retries,
                error=str(e)
            )

            # Publish step failed event
            self.event_bus.publish(Event(
                type="WorkflowStepFailed",
                data={
                    "workflow_id": workflow_id,
                    "step_number": step_number,
                    "error": str(e),
                    "retry_count": retry_count
                }
            ))

            if retry_count <= self.max_retries:
                # Exponential backoff: 2^retry_count seconds
                backoff_seconds = 2 ** retry_count
                logger.info(
                    "workflow_retry_backoff",
                    workflow=workflow_id,
                    backoff_seconds=backoff_seconds
                )
                await asyncio.sleep(backoff_seconds)
            else:
                # Max retries exceeded
                step_result.status = "failed"
                step_result.error_message = f"Failed after {self.max_retries} retries: {str(last_error)}"
                logger.error(
                    "workflow_step_max_retries_exceeded",
                    workflow=workflow_id,
                    max_retries=self.max_retries,
                    error=str(last_error)
                )

    # Finalize result
    step_result.end_time = datetime.now()
    if step_result.start_time:
        step_result.duration_seconds = (
            step_result.end_time - step_result.start_time
        ).total_seconds()

    return step_result
```

**Key Points**:
- Retry logic with exponential backoff
- Event publishing for all lifecycle events
- Comprehensive error handling
- Detailed logging for debugging

---

#### Task 2.4: Implement Helper Methods

**Implementation**:
```python
def _get_agent_for_workflow(self, workflow_info: 'WorkflowInfo') -> str:
    """
    Determine which agent should execute a workflow.

    Maps workflow names to agent names based on workflow type.
    This is a temporary mapping until AgentFactory is fully integrated.

    Args:
        workflow_info: Workflow metadata

    Returns:
        Agent name (e.g., "John", "Amelia", "Bob")
    """
    workflow_name_lower = workflow_info.name.lower()

    # Map workflow patterns to agents
    if "prd" in workflow_name_lower:
        return "John"
    elif "architecture" in workflow_name_lower or "tech-spec" in workflow_name_lower:
        return "Winston"
    elif "story" in workflow_name_lower and "create" in workflow_name_lower:
        return "Bob"
    elif "implement" in workflow_name_lower or "dev" in workflow_name_lower:
        return "Amelia"
    elif "test" in workflow_name_lower or "qa" in workflow_name_lower:
        return "Murat"
    elif "ux" in workflow_name_lower or "design" in workflow_name_lower:
        return "Sally"
    elif "brief" in workflow_name_lower or "research" in workflow_name_lower:
        return "Mary"
    else:
        return "Orchestrator"
```

**Why**: Encapsulates agent selection logic, easy to replace with AgentFactory later

---

### Phase 3: Write Comprehensive Tests

#### Task 3.1: Create Test File

**File**: `tests/core/services/test_workflow_coordinator.py`

**Test Structure**:
```python
"""Tests for WorkflowCoordinator service."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from pathlib import Path
from datetime import datetime

from gao_dev.core.services.workflow_coordinator import WorkflowCoordinator
from gao_dev.core.events.event_bus import EventBus, Event


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
        from gao_dev.orchestrator.brian_orchestrator import WorkflowSequence, WorkflowInfo, ScaleLevel
        from gao_dev.core.models.workflow_context import WorkflowContext

        workflow_sequence = WorkflowSequence(
            scale_level=ScaleLevel.SMALL,
            project_type=None,
            workflows=[
                WorkflowInfo(name="prd", description="Create PRD"),
                WorkflowInfo(name="create-story", description="Create story")
            ],
            routing_rationale="Test sequence"
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
        from gao_dev.orchestrator.brian_orchestrator import WorkflowSequence, ScaleLevel
        from gao_dev.core.models.workflow_context import WorkflowContext

        workflow_sequence = WorkflowSequence(
            scale_level=ScaleLevel.ATOMIC,
            project_type=None,
            workflows=[],
            routing_rationale="Empty"
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
        from gao_dev.orchestrator.brian_orchestrator import WorkflowInfo
        from gao_dev.core.models.workflow_context import WorkflowContext

        workflow_info = WorkflowInfo(name="test", description="Test")
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
        from gao_dev.orchestrator.brian_orchestrator import WorkflowInfo
        from gao_dev.core.models.workflow_context import WorkflowContext

        workflow_info = WorkflowInfo(name="test", description="Test")
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
        from gao_dev.orchestrator.brian_orchestrator import WorkflowInfo

        test_cases = [
            (WorkflowInfo(name="prd", description=""), "John"),
            (WorkflowInfo(name="create-story", description=""), "Bob"),
            (WorkflowInfo(name="dev-story", description=""), "Amelia"),
            (WorkflowInfo(name="architecture", description=""), "Winston"),
            (WorkflowInfo(name="test-plan", description=""), "Murat"),
            (WorkflowInfo(name="ux-design", description=""), "Sally"),
            (WorkflowInfo(name="research-brief", description=""), "Mary"),
            (WorkflowInfo(name="unknown", description=""), "Orchestrator"),
        ]

        for workflow_info, expected_agent in test_cases:
            agent = coordinator._get_agent_for_workflow(workflow_info)
            assert agent == expected_agent, f"Workflow {workflow_info.name} should map to {expected_agent}"


    async def test_context_passing(self, coordinator):
        """Test context is passed between workflow steps."""
        # This test verifies context flows through the system
        # Implementation will depend on how context is used in actual workflows
        pass  # TODO: Implement when context passing is finalized
```

**Coverage Target**: 80%+ (Story requirement)

---

#### Task 3.2: Run Tests

```bash
# Run tests for WorkflowCoordinator only
cd "D:\GAO Agile Dev"
python -m pytest tests/core/services/test_workflow_coordinator.py -v

# Run with coverage
python -m pytest tests/core/services/test_workflow_coordinator.py --cov=gao_dev.core.services.workflow_coordinator --cov-report=term-missing
```

**Expected Output**:
- All tests passing
- Coverage >= 80%

---

### Phase 4: Update Orchestrator to Use WorkflowCoordinator

#### Task 4.1: Import WorkflowCoordinator in Orchestrator

**File**: `gao_dev/orchestrator/orchestrator.py`

**Add import**:
```python
from ..core.services.workflow_coordinator import WorkflowCoordinator
```

---

#### Task 4.2: Initialize WorkflowCoordinator in __init__

**File**: `gao_dev/orchestrator/orchestrator.py`

**Find the `__init__` method and add**:
```python
# Initialize EventBus (if not already done)
from ..core.events.event_bus import EventBus
self.event_bus = EventBus()

# Initialize WorkflowCoordinator
self.workflow_coordinator = WorkflowCoordinator(
    workflow_registry=self.workflow_registry,
    agent_factory=None,  # Will be added in future story
    event_bus=self.event_bus,
    agent_executor=self._get_agent_method_for_workflow,
    project_root=self.project_root,
    max_retries=3
)
```

**Where**: After `self.workflow_registry` initialization

---

#### Task 4.3: Replace execute_workflow with WorkflowCoordinator

**File**: `gao_dev/orchestrator/orchestrator.py`

**Find the `execute_workflow` method (around line 893)**:
```python
async def execute_workflow(
    self,
    initial_prompt: str,
    workflow: Optional[WorkflowSequence] = None,
    commit_after_steps: bool = True
) -> "WorkflowResult":
```

**Replace the workflow execution logic** (lines ~929-1000):

**OLD CODE** (to be replaced):
```python
# Step 2: Execute workflows sequentially
for i, workflow_info in enumerate(workflow.workflows, 1):
    logger.info(
        "workflow_step_started",
        step=i,
        total=len(workflow.workflows),
        workflow_name=workflow_info.name
    )

    step_result = await self._execute_workflow_step(
        workflow_info=workflow_info,
        step_number=i,
        total_steps=len(workflow.workflows)
    )

    result.step_results.append(step_result)

    # ... rest of old logic
```

**NEW CODE** (delegate to WorkflowCoordinator):
```python
# Step 2: Execute workflows using WorkflowCoordinator
from ..core.models.workflow_context import WorkflowContext

workflow_context = WorkflowContext(
    initial_prompt=initial_prompt,
    project_root=self.project_root,
    metadata={
        "mode": self.mode,
        "commit_after_steps": commit_after_steps
    }
)

# Delegate to WorkflowCoordinator
coordinator_result = await self.workflow_coordinator.execute_sequence(
    workflow_sequence=workflow,
    context=workflow_context
)

# Copy results from coordinator to orchestrator result
result.status = coordinator_result.status
result.step_results = coordinator_result.step_results
result.error_message = coordinator_result.error_message
result.total_artifacts = coordinator_result.total_artifacts
```

**Why**: This delegates workflow coordination to the new service, removing that responsibility from orchestrator

---

#### Task 4.4: Mark Old Methods as Deprecated

**File**: `gao_dev/orchestrator/orchestrator.py`

**Find `_execute_workflow_step` method (around line 1150)** and add deprecation comment:
```python
async def _execute_workflow_step(
    self,
    workflow_info: "WorkflowInfo",
    step_number: int,
    total_steps: int,
    epic: int = 1,
    story: int = 1
) -> "WorkflowStepResult":
    """
    Execute a single workflow step.

    DEPRECATED: This method will be removed after Epic 6.5.
    Use WorkflowCoordinator.execute_workflow() instead.

    ...
    """
```

**Why**: Signals to other developers that this is legacy code to be removed

---

### Phase 5: Regression Testing

#### Task 5.1: Run Full Test Suite

```bash
cd "D:\GAO Agile Dev"

# Run ALL tests to ensure nothing broke
python -m pytest tests/ -v

# Expected: 550+ tests passing (same as before)
```

**Success Criteria**:
- All existing tests still pass
- No new failures introduced
- Test count >= 550

---

#### Task 5.2: Manual Smoke Test

```bash
# Test basic orchestrator functionality
gao-dev health
gao-dev list-workflows
```

**Expected**: Commands work normally

---

### Phase 6: Documentation & Cleanup

#### Task 6.1: Update __init__.py

**File**: `gao_dev/core/services/__init__.py`

```python
"""Core services for GAO-Dev.

Services extracted from God Classes to follow Single Responsibility Principle.
"""

from .workflow_coordinator import WorkflowCoordinator

__all__ = ["WorkflowCoordinator"]
```

---

#### Task 6.2: Add Service Documentation

Create docstring at module level in `workflow_coordinator.py`:
```python
"""
WorkflowCoordinator Service - Coordinates multi-step workflow execution.

Extracted from GAODevOrchestrator (Epic 6, Story 6.1) to achieve SOLID principles.

Responsibilities:
- Execute workflow sequences step-by-step
- Manage workflow context passing
- Publish workflow lifecycle events
- Handle errors with retry logic

NOT responsible for:
- Story lifecycle (StoryLifecycleManager)
- Quality gates (QualityGateManager)
- Subprocess execution (ProcessExecutor)
- High-level orchestration (stays in orchestrator)
"""
```

---

#### Task 6.3: Update Story Status

**File**: `docs/features/core-gao-dev-system-refactor/stories/epic-6/story-6.1.md`

Add completion section at bottom:
```markdown
---

## Implementation Complete

**Date**: 2025-10-30
**Implemented By**: Amelia
**Test Coverage**: XX%
**Tests Passing**: X/X

### Files Created
- gao_dev/core/services/__init__.py
- gao_dev/core/services/workflow_coordinator.py
- tests/core/services/test_workflow_coordinator.py

### Files Modified
- gao_dev/orchestrator/orchestrator.py (integrated WorkflowCoordinator)

### Key Metrics
- WorkflowCoordinator: XXX lines (< 200 ✓)
- Test coverage: XX% (>= 80% ✓)
- Regression tests: 550+ passing ✓

### Verification
- [x] Service created and under 200 lines
- [x] All acceptance criteria met
- [x] Unit tests written (80%+ coverage)
- [x] Regression tests passing
- [x] Orchestrator integrated
- [x] Documentation complete
```

---

### Phase 7: Git Commit

#### Task 7.1: Create Atomic Commit

```bash
cd "D:\GAO Agile Dev"

# Stage all changes
git add gao_dev/core/services/
git add tests/core/services/
git add gao_dev/orchestrator/orchestrator.py
git add docs/features/core-gao-dev-system-refactor/stories/epic-6/story-6.1.md
git add docs/features/core-gao-dev-system-refactor/sprint-status.yaml

# Create commit
git commit -m "feat(epic-6): implement Story 6.1 - Extract WorkflowCoordinator Service

Extract workflow coordination logic from 1,327-line GAODevOrchestrator into
focused WorkflowCoordinator service following Single Responsibility Principle.

Changes:
- Create WorkflowCoordinator service (XXX lines, < 200)
- Implement workflow sequence execution with retry logic
- Add event publishing for workflow lifecycle
- Integrate WorkflowCoordinator into orchestrator
- Write comprehensive tests (XX% coverage, X/X passing)
- All 550+ regression tests passing

This is the FIRST service extraction in Epic 6 God Class refactoring.

Test Results: X/X tests passed, XX% coverage

🤖 Generated with GAO-Dev
Co-Authored-By: Amelia <noreply@anthropic.com>
Co-Authored-By: Bob <noreply@anthropic.com>"

# Push to feature branch
git push origin feature/epic-6-legacy-cleanup
```

---

## Definition of Done Checklist

Before marking story as complete, verify ALL items:

### Acceptance Criteria
- [ ] `WorkflowCoordinator` class created at `gao_dev/core/services/workflow_coordinator.py`
- [ ] Class is < 200 lines (target: 150-180 lines)
- [ ] Single responsibility: Execute workflow sequences
- [ ] Executes workflow sequences step-by-step
- [ ] Handles workflow errors and retry logic (max 3 retries, exponential backoff)
- [ ] Publishes events for workflow lifecycle (6 event types defined)
- [ ] Supports workflow context passing between steps
- [ ] Uses `WorkflowRegistry` to get workflows
- [ ] Uses `AgentFactory` interface (injected but not yet used)
- [ ] Uses `EventBus` to publish events
- [ ] All dependencies injected via constructor

### Testing
- [ ] Unit tests created at `tests/core/services/test_workflow_coordinator.py`
- [ ] Test coverage >= 80%
- [ ] Tests for successful sequence execution
- [ ] Tests for error handling and retries
- [ ] Tests for event publishing
- [ ] Tests for agent mapping
- [ ] Mock implementations for all dependencies
- [ ] All new tests passing (X/X)
- [ ] All regression tests passing (550+)

### Documentation
- [ ] Class docstring explains responsibility
- [ ] Method docstrings for all public methods
- [ ] Type hints throughout (no `Any` types)
- [ ] Usage examples in class docstring
- [ ] Module-level docstring explaining service purpose
- [ ] Story completion section added to story file

### Integration
- [ ] `WorkflowCoordinator` imported in orchestrator
- [ ] Orchestrator creates `WorkflowCoordinator` instance
- [ ] Orchestrator delegates to `WorkflowCoordinator` for sequence execution
- [ ] Old `_execute_workflow_step` marked as deprecated
- [ ] Behavior unchanged (regression tests validate)

### Code Quality
- [ ] No code duplication (DRY principle)
- [ ] Single Responsibility Principle followed
- [ ] Dependency Injection used throughout
- [ ] Comprehensive logging for observability
- [ ] Error handling with meaningful messages
- [ ] No emojis (Windows compatibility)
- [ ] Line length <= 100 characters

### Git & Process
- [ ] Branch: feature/epic-6-legacy-cleanup
- [ ] Atomic commit with clear message
- [ ] Commit follows conventional commit format
- [ ] Sprint status updated (story marked as done)
- [ ] Story file updated with completion details
- [ ] Changes pushed to feature branch

---

## Troubleshooting Guide

### Issue: Tests Failing

**Symptom**: Unit tests fail with import errors or mock issues

**Solution**:
1. Check import paths are correct
2. Ensure all test fixtures properly set up
3. Verify mock objects match interface signatures
4. Run single test to isolate: `pytest tests/core/services/test_workflow_coordinator.py::TestWorkflowCoordinator::test_execute_sequence_success -v`

---

### Issue: Orchestrator Integration Breaks

**Symptom**: Orchestrator tests fail after integration

**Solution**:
1. Check `WorkflowCoordinator` initialization in orchestrator `__init__`
2. Verify `agent_executor` callback signature matches
3. Check `WorkflowContext` is constructed correctly
4. Review delegation logic in `execute_workflow`

---

### Issue: Coverage Below 80%

**Symptom**: Test coverage report shows < 80%

**Solution**:
1. Run coverage report: `pytest --cov=gao_dev.core.services.workflow_coordinator --cov-report=html`
2. Open `htmlcov/index.html` to see uncovered lines
3. Add tests for uncovered branches/error paths
4. Focus on error handling and edge cases

---

### Issue: Circular Import

**Symptom**: `ImportError: cannot import name 'X' from partially initialized module`

**Solution**:
1. Use forward references in type hints: `'WorkflowSequence'`
2. Move imports inside methods if needed
3. Check import order in `__init__.py` files
4. Review dependency graph for cycles

---

## Reference Materials

### Key Files to Review

1. **Story Definition**: `docs/features/core-gao-dev-system-refactor/stories/epic-6/story-6.1.md`
2. **Epic 2 Reference**: `git show feature/epic-2-god-class-refactoring:gao_dev/core/services/workflow_coordinator.py`
3. **Orchestrator**: `gao_dev/orchestrator/orchestrator.py` (lines 1-1328)
4. **Interfaces**: `gao_dev/core/interfaces/workflow.py`, `agent.py`, `event_bus.py`
5. **Models**: `gao_dev/core/models/workflow.py`, `workflow_context.py`

### Design Patterns Used

- **Dependency Injection**: All dependencies injected via constructor
- **Observer Pattern**: EventBus for publish-subscribe
- **Single Responsibility**: Service does ONE thing (workflow coordination)
- **Retry Pattern**: Exponential backoff for transient failures

### Helpful Commands

```bash
# View Epic 2 implementation
git show feature/epic-2-god-class-refactoring:gao_dev/core/services/workflow_coordinator.py

# Run tests with coverage
pytest tests/core/services/test_workflow_coordinator.py --cov=gao_dev.core.services.workflow_coordinator --cov-report=term-missing

# Check test count
pytest tests/ --collect-only | grep "test session"

# View current branch
git branch --show-current

# Check story status
cat docs/features/core-gao-dev-system-refactor/sprint-status.yaml | grep -A 10 "number: 1"
```

---

## Time Estimates

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 1: Setup | 1.1-1.2 | 15 min |
| Phase 2: Core Implementation | 2.1-2.4 | 2 hours |
| Phase 3: Testing | 3.1-3.2 | 1.5 hours |
| Phase 4: Integration | 4.1-4.4 | 1 hour |
| Phase 5: Regression Testing | 5.1-5.2 | 30 min |
| Phase 6: Documentation | 6.1-6.3 | 30 min |
| Phase 7: Git Commit | 7.1 | 15 min |
| **TOTAL** | | **6 hours** |

**Story Points**: 5 (aligns with 1 day estimate)

---

## Success Metrics

After completing this story:

✅ **Code Quality**
- WorkflowCoordinator: < 200 lines
- No duplication
- Single responsibility clear

✅ **Testing**
- 80%+ coverage
- All unit tests passing
- 550+ regression tests passing

✅ **Integration**
- Orchestrator uses WorkflowCoordinator
- Behavior unchanged
- Events published correctly

✅ **Progress**
- Story 6.1 complete
- Epic 6: 5/47 story points done (10.6%)
- Ready for Story 6.2 (StoryLifecycleManager)

---

## Next Steps (After Story 6.1 Complete)

1. **Story 6.2**: Extract StoryLifecycleManager
2. **Story 6.3**: Extract ProcessExecutor
3. **Story 6.4**: Extract QualityGateManager
4. **Story 6.5**: Refactor orchestrator as thin facade (CRITICAL)

---

**Remember**: This is the FIRST extraction from the God Class. Take time to get it right. The pattern we establish here will be repeated for Stories 6.2-6.4.

**Questions?** Review the story file, check Epic 2 branch, or refer to completed Epic 3/4/5 implementations.

Good luck, Amelia! Let's refactor this God Class! 💪

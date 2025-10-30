# Story 6.1: Extract WorkflowCoordinator Service

**Epic**: 6 - Legacy Cleanup & God Class Refactoring
**Story Points**: 5
**Priority**: P0 (Critical)
**Type**: Refactoring
**Status**: Ready

---

## Overview

Extract the workflow coordination logic from the 1,327-line `GAODevOrchestrator` into a focused `WorkflowCoordinator` service responsible solely for executing workflow sequences.

---

## User Story

**As a** GAO-Dev architect
**I want** workflow sequence execution logic extracted into a dedicated service
**So that** the orchestrator is not a God Class and follows single responsibility principle

---

## Acceptance Criteria

1. **Service Created**
   - [ ] `gao_dev/core/services/workflow_coordinator.py` created
   - [ ] Class `WorkflowCoordinator` < 200 lines
   - [ ] Single responsibility: Execute workflow sequences

2. **Functionality**
   - [ ] Executes workflow sequences step-by-step
   - [ ] Handles workflow errors and retry logic
   - [ ] Publishes events for workflow lifecycle (started, step completed, completed, failed)
   - [ ] Supports workflow context passing between steps

3. **Dependencies**
   - [ ] Uses `WorkflowRegistry` to get workflows
   - [ ] Uses `AgentFactory` to create agents
   - [ ] Uses `EventBus` to publish events
   - [ ] All dependencies injected via constructor

4. **Testing**
   - [ ] Unit tests created (80%+ coverage)
   - [ ] Tests for successful sequence execution
   - [ ] Tests for error handling and retries
   - [ ] Tests for event publishing
   - [ ] Mock implementations for dependencies

5. **Documentation**
   - [ ] Class docstring explains responsibility
   - [ ] Method docstrings for all public methods
   - [ ] Type hints throughout
   - [ ] Usage examples in docstring

---

## Technical Details

### Service Responsibility

**WorkflowCoordinator** is responsible for:
- Executing a sequence of workflows in order
- Managing workflow context across steps
- Publishing workflow lifecycle events
- Handling workflow step failures

**NOT responsible for**:
- Story lifecycle management
- Quality gate validation
- Subprocess execution
- Orchestrator-level logic

### Interface

```python
class WorkflowCoordinator:
    """
    Coordinates execution of workflow sequences.

    Responsible for:
    - Executing workflows in sequence order
    - Managing workflow context
    - Publishing workflow lifecycle events
    - Error handling and retry logic
    """

    def __init__(
        self,
        workflow_registry: IWorkflowRegistry,
        agent_factory: IAgentFactory,
        event_bus: IEventBus,
        max_retries: int = 3
    ):
        """Initialize coordinator with dependencies."""
        self.workflow_registry = workflow_registry
        self.agent_factory = agent_factory
        self.event_bus = event_bus
        self.max_retries = max_retries

    async def execute_sequence(
        self,
        sequence: WorkflowSequence,
        context: WorkflowContext
    ) -> WorkflowResult:
        """
        Execute a sequence of workflows.

        Args:
            sequence: Sequence of workflow identifiers
            context: Initial workflow context

        Returns:
            WorkflowResult with status and outputs

        Raises:
            WorkflowExecutionError: If workflow sequence fails
        """
        pass

    async def execute_workflow(
        self,
        workflow_id: str,
        context: WorkflowContext
    ) -> WorkflowStepResult:
        """Execute a single workflow step."""
        pass
```

### Events Published

- `WorkflowSequenceStarted(sequence_id, workflow_count)`
- `WorkflowStepStarted(workflow_id, step_number)`
- `WorkflowStepCompleted(workflow_id, step_number, duration)`
- `WorkflowStepFailed(workflow_id, step_number, error, retry_count)`
- `WorkflowSequenceCompleted(sequence_id, duration, results)`
- `WorkflowSequenceFailed(sequence_id, failed_at_step, error)`

### Error Handling

- Retry failed workflows up to `max_retries` times
- Exponential backoff between retries
- Log all errors with context
- Publish failure events for observability

---

## Implementation Steps

1. **Create Service File**
   - Create `gao_dev/core/services/__init__.py` if not exists
   - Create `gao_dev/core/services/workflow_coordinator.py`
   - Import necessary interfaces and models

2. **Implement Core Logic**
   - Constructor with dependency injection
   - `execute_sequence()` method
   - `execute_workflow()` method
   - Error handling and retry logic

3. **Event Publishing**
   - Publish events at key lifecycle points
   - Include relevant context in events

4. **Extract from Orchestrator**
   - Identify workflow coordination code in `orchestrator.py`
   - Copy to `WorkflowCoordinator`
   - Refactor to use injected dependencies
   - Remove BMAD-specific assumptions

5. **Write Tests**
   - Unit test with mocked dependencies
   - Test successful execution
   - Test error handling
   - Test event publishing
   - Test retry logic

6. **Update Orchestrator**
   - Create `WorkflowCoordinator` instance in orchestrator
   - Replace inline coordination code with service calls
   - Verify behavior unchanged

---

## Testing Strategy

### Unit Tests

```python
# tests/core/services/test_workflow_coordinator.py

class TestWorkflowCoordinator:
    def test_execute_sequence_success(self):
        """Test successful workflow sequence execution."""
        # Mock dependencies
        # Execute sequence
        # Assert all workflows executed in order
        # Assert events published
        pass

    def test_execute_sequence_with_retry(self):
        """Test workflow retries on failure."""
        # Mock workflow that fails twice then succeeds
        # Execute sequence
        # Assert 3 attempts made
        # Assert final success
        pass

    def test_execute_sequence_failure(self):
        """Test sequence fails after max retries."""
        # Mock workflow that always fails
        # Execute sequence
        # Assert max retries attempted
        # Assert failure event published
        pass

    def test_context_passing(self):
        """Test context passed between workflow steps."""
        # Execute multi-step sequence
        # Verify context updated by each step
        # Verify final context contains all updates
        pass
```

### Integration Tests

- Test with real `WorkflowRegistry` (file-based)
- Test with real event bus
- Verify events published to bus
- Verify workflow execution end-to-end

---

## Dependencies

### Prerequisites
- Epic 1 complete (interfaces defined)
- Epic 3 complete (EventBus available)
- Epic 4 complete (AgentFactory available)

### Imports Required
```python
from ..interfaces.workflow import IWorkflowRegistry
from ..interfaces.agent import IAgentFactory
from ..interfaces.event_bus import IEventBus
from ..models.workflow import WorkflowSequence, WorkflowContext, WorkflowResult
from ..events.events import (
    WorkflowSequenceStarted,
    WorkflowStepStarted,
    WorkflowStepCompleted,
    WorkflowSequenceFailed
)
```

---

## Definition of Done

- [ ] `WorkflowCoordinator` class created (< 200 lines)
- [ ] All acceptance criteria met
- [ ] Unit tests written (80%+ coverage)
- [ ] Integration tests pass
- [ ] Type hints throughout (mypy passes)
- [ ] Docstrings complete
- [ ] Code reviewed
- [ ] Orchestrator updated to use service
- [ ] Behavior unchanged (regression tests pass)

---

## Related Stories

- **Story 6.2**: Extract StoryLifecycleManager (depends on this)
- **Story 6.5**: Refactor Orchestrator as Facade (uses this service)
- **Original Epic 2, Story 2.1**: This completes that work

---

## Notes

- This is the FIRST service extraction from the God Class
- Keep business logic pure (no I/O in service)
- Use dependency injection for all dependencies
- Publish events for observability
- Write tests FIRST to understand current behavior
- Extract incrementally, verify at each step

---

**Status**: Ready to start
**Estimated Time**: 1 day
**Assigned To**: TBD

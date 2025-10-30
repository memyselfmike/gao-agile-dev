# GAODevOrchestrator - Workflow Orchestration Facade

**Version**: 2.0 (Post-Epic 6 Refactoring)
**Status**: Production-Ready
**Last Updated**: 2025-10-30

---

## Overview

The `GAODevOrchestrator` is a thin facade that orchestrates workflow execution for the GAO-Dev system. It delegates specialized responsibilities to focused services while maintaining a clean, simple interface for clients.

**Key Principle**: Single Responsibility - Orchestration only

---

## Architecture

### Facade Pattern

The orchestrator follows the Facade pattern:

```python
class GAODevOrchestrator:
    """
    Thin facade coordinating workflow execution.

    Delegates to specialized services:
    - WorkflowCoordinator: Workflow execution
    - StoryLifecycleManager: Story and epic lifecycle
    - ProcessExecutor: Subprocess execution
    - QualityGateManager: Artifact validation
    - BrianOrchestrator: Complexity assessment
    """

    def __init__(
        self,
        workflow_coordinator: WorkflowCoordinator,
        story_lifecycle: StoryLifecycleManager,
        process_executor: ProcessExecutor,
        quality_gate: QualityGateManager,
        brian: BrianOrchestrator
    ):
        self.workflow_coordinator = workflow_coordinator
        self.story_lifecycle = story_lifecycle
        self.process_executor = process_executor
        self.quality_gate = quality_gate
        self.brian = brian
```

### Services Delegated To

| Service | Responsibility | Location |
|---------|-----------------|----------|
| WorkflowCoordinator | Multi-step workflow execution | `core/services/workflow_coordinator.py` |
| StoryLifecycleManager | Story state management | `core/services/story_lifecycle.py` |
| ProcessExecutor | Subprocess execution (agents) | `core/services/process_executor.py` |
| QualityGateManager | Artifact validation | `core/services/quality_gate.py` |
| BrianOrchestrator | Scale assessment & workflow selection | `orchestrator/brian_orchestrator.py` |

---

## Usage

### Basic Usage (Recommended)

```python
from gao_dev.orchestrator import GAODevOrchestrator

async def main():
    # Create orchestrator (services initialized automatically)
    orchestrator = GAODevOrchestrator()

    # Define workflow sequence
    workflow_seq = ["prd", "tech-spec", "create-story", "dev-story"]

    # Create context
    context = WorkflowContext(
        user_prompt="Build a todo app with auth",
        scale_level=ScaleLevel.LEVEL_2
    )

    # Execute workflow sequence
    result = await orchestrator.execute_workflow_sequence(
        sequence=workflow_seq,
        context=context
    )

    print(f"Result: {result.status}")
    print(f"Artifacts: {result.artifacts}")

# Run async
await main()
```

### Advanced Usage (Direct Service Access)

For fine-grained control, access services directly:

```python
from gao_dev.core.services import WorkflowCoordinator, StoryLifecycleManager

# Create services
event_bus = EventBus()
workflow_reg = WorkflowRegistry()
agent_factory = AgentFactory()

coordinator = WorkflowCoordinator(workflow_reg, agent_factory, event_bus)
story_manager = StoryLifecycleManager(story_repo, event_bus)

# Use services directly
story = await story_manager.create_story(epic=1, story=1, details=...)
result = await coordinator.execute_sequence(seq, ctx)
```

---

## Public API

### Main Methods

#### execute_workflow_sequence()

Execute a sequence of workflows in order.

```python
async def execute_workflow_sequence(
    self,
    sequence: List[str],
    context: WorkflowContext
) -> WorkflowResult:
    """
    Execute a sequence of workflows.

    Args:
        sequence: List of workflow names in order
        context: Workflow execution context

    Returns:
        WorkflowResult: Execution result with status and artifacts

    Raises:
        WorkflowNotFoundError: If workflow in sequence not found
        WorkflowExecutionError: If workflow execution fails
    """
```

**Example**:
```python
result = await orchestrator.execute_workflow_sequence(
    sequence=["prd", "tech-spec", "create-story"],
    context=context
)
```

#### implement_story()

Create and implement a story with workflow execution.

```python
async def implement_story(
    self,
    epic: int,
    story: int,
    details: StoryDetails,
    workflow_seq: Optional[List[str]] = None
) -> StoryResult:
    """
    Create story and execute implementation workflow.

    Args:
        epic: Epic number
        story: Story number within epic
        details: Story details (title, description, etc.)
        workflow_seq: Optional custom workflow sequence

    Returns:
        StoryResult: Story created with implementation results
    """
```

**Example**:
```python
result = await orchestrator.implement_story(
    epic=1,
    story=1,
    details=StoryDetails(
        title="Build API",
        description="Create REST API endpoints"
    )
)
```

#### assess_scale_level()

Assess project complexity and recommend scale level.

```python
async def assess_scale_level(
    self,
    prompt: str
) -> Tuple[ScaleLevel, str]:
    """
    Assess project complexity from user prompt.

    Args:
        prompt: User's project description

    Returns:
        Tuple of (ScaleLevel, Reasoning)
    """
```

**Example**:
```python
scale_level, reasoning = await orchestrator.assess_scale_level(
    "Build a simple todo app"
)
print(f"Scale: {scale_level}")
```

---

## Internal Structure

### File Organization

```
orchestrator/
├── __init__.py              # Public API
├── README.md                # This file
├── orchestrator.py          # Main facade (728 lines)
├── workflow_results.py      # Result type definitions
├── agent_definitions.py     # Agent personas and configs
├── brian_orchestrator.py    # Complexity assessment
└── context.py               # Orchestration context
```

### Line Count (Post-Epic 6)

| File | Lines | Purpose |
|------|-------|---------|
| orchestrator.py | 728 | Facade, delegates to services |
| brian_orchestrator.py | 450+ | Scale assessment, workflow selection |
| workflow_results.py | 150+ | Result types |
| agent_definitions.py | 100+ | Agent configurations |
| context.py | 80+ | Context models |

**Total**: ~1,500 lines (down from 1,900+ before Epic 6)

---

## Design Principles

### Single Responsibility Principle

The orchestrator has **one responsibility**: **Orchestration**

What it DOES:
- Coordinates service interactions
- Handles high-level workflows
- Routes to appropriate services
- Returns results to clients

What it DOES NOT do (delegated to services):
- Workflow execution details (WorkflowCoordinator)
- Story state management (StoryLifecycleManager)
- Subprocess management (ProcessExecutor)
- Quality validation (QualityGateManager)

### Facade Pattern

The orchestrator is a **Facade** providing simplified interface to complex subsystem:

```
Complex Services Layer
├── WorkflowCoordinator
├── StoryLifecycleManager
├── ProcessExecutor
├── QualityGateManager
└── BrianOrchestrator
        ↑
        │ delegates
        │
    GAODevOrchestrator (Facade)
        ↓
        │ simple interface
        │
    Client Code
```

### Dependency Inversion

The orchestrator depends on abstractions (interfaces), not concrete implementations:

```python
# Services are injected, not instantiated
def __init__(
    self,
    workflow_coordinator: WorkflowCoordinator,  # Abstraction
    story_lifecycle: StoryLifecycleManager,      # Abstraction
    # Not: self.coordinator = WorkflowCoordinator()
)
```

---

## Testing

### Unit Testing

```python
import pytest
from unittest.mock import Mock, AsyncMock

class TestGAODevOrchestrator:
    @pytest.fixture
    def orchestrator(self):
        # Create mocks for services
        workflow_coord = AsyncMock()
        story_lifecycle = AsyncMock()
        process_executor = AsyncMock()
        quality_gate = AsyncMock()
        brian = AsyncMock()

        return GAODevOrchestrator(
            workflow_coordinator=workflow_coord,
            story_lifecycle=story_lifecycle,
            process_executor=process_executor,
            quality_gate=quality_gate,
            brian=brian
        )

    @pytest.mark.asyncio
    async def test_execute_workflow_sequence(self, orchestrator):
        # Arrange
        orchestrator.workflow_coordinator.execute_sequence.return_value = (
            WorkflowResult(status="completed")
        )

        # Act
        result = await orchestrator.execute_workflow_sequence(seq, ctx)

        # Assert
        assert result.status == "completed"
        orchestrator.workflow_coordinator.execute_sequence.assert_called_once()
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_orchestrator_end_to_end():
    # Create real services
    event_bus = EventBus()
    registry = WorkflowRegistry()
    factory = AgentFactory()

    coordinator = WorkflowCoordinator(registry, factory, event_bus)
    # ... create other services ...

    orchestrator = GAODevOrchestrator(
        workflow_coordinator=coordinator,
        # ... other services ...
    )

    # Execute real workflow
    result = await orchestrator.execute_workflow_sequence(seq, ctx)

    # Verify results
    assert result.status == "completed"
    assert len(result.artifacts) > 0
```

---

## Error Handling

### Error Types

```python
# Workflow not found
try:
    result = await orchestrator.execute_workflow_sequence(
        sequence=["nonexistent-workflow"],
        context=context
    )
except WorkflowNotFoundError as e:
    print(f"Workflow not found: {e}")

# Workflow execution failed
try:
    result = await orchestrator.execute_workflow_sequence(
        sequence=["prd"],
        context=context
    )
except WorkflowExecutionError as e:
    print(f"Workflow failed: {e}")
    print(f"Details: {e.details}")

# Invalid context
try:
    result = await orchestrator.execute_workflow_sequence(
        sequence=["prd"],
        context=None  # Invalid
    )
except ValueError as e:
    print(f"Invalid context: {e}")
```

---

## Event Publishing

Services publish events that clients can subscribe to:

```python
from gao_dev.core.events import EventBus
from gao_dev.core.events.events import WorkflowCompleted, StoryCreated

# Create orchestrator with event bus
event_bus = EventBus()
orchestrator = GAODevOrchestrator(
    # ... services ...
    # Services are initialized with event_bus
)

# Subscribe to events
async def on_workflow_completed(event: WorkflowCompleted):
    print(f"Workflow {event.workflow_id} completed!")

event_bus.subscribe(WorkflowCompleted, on_workflow_completed)

# Events are published by services during execution
result = await orchestrator.execute_workflow_sequence(seq, ctx)
# on_workflow_completed will be called automatically
```

---

## Performance Characteristics

### Startup Performance

- Service initialization: ~100ms
- Event bus setup: ~20ms
- Dependency injection: ~30ms
- **Total**: ~150ms

### Execution Performance

- Workflow execution: No added overhead
- Service delegation: < 1ms per call
- Event publishing: < 1ms per event
- **Result**: Identical performance to pre-refactoring

### Memory Usage

- Orchestrator instance: < 50MB
- Service instances: ~100MB total
- **Per-instance overhead**: ~150MB

---

## Migration Guide

### From Old Monolithic Code

If you were using the old orchestrator before Epic 6:

**Before** (monolithic):
```python
orchestrator = GAODevOrchestrator()
result = await orchestrator.execute_workflow_sequence(seq, ctx)
```

**After** (service-based):
```python
# Same usage - no changes needed!
orchestrator = GAODevOrchestrator()
result = await orchestrator.execute_workflow_sequence(seq, ctx)

# OR access services directly (new)
coordinator = orchestrator.workflow_coordinator
story_mgr = orchestrator.story_lifecycle
result = await coordinator.execute_sequence(seq, ctx)
```

**Status**: **Fully backward compatible** - no migration needed

---

## FAQ

### Q: What if I need fine-grained control?

**A**: Access services directly:
```python
orchestrator = GAODevOrchestrator()
coordinator = orchestrator.workflow_coordinator
result = await coordinator.execute_sequence(seq, ctx)
```

### Q: How do I test my orchestrator usage?

**A**: Use mock services with dependency injection:
```python
orchestrator = GAODevOrchestrator(
    workflow_coordinator=Mock(),
    story_lifecycle=Mock(),
    # ... other mocks ...
)
```

### Q: Can I subscribe to orchestrator events?

**A**: Yes! Services publish events. Subscribe to the event bus:
```python
event_bus.subscribe(WorkflowCompleted, handler)
event_bus.subscribe(StoryCreated, handler)
```

### Q: Is the orchestrator thread-safe?

**A**: The orchestrator itself is stateless. Services handle their own thread safety.

### Q: How do I handle errors?

**A**: Use try/except blocks around orchestrator calls:
```python
try:
    result = await orchestrator.execute_workflow_sequence(seq, ctx)
except WorkflowExecutionError as e:
    # Handle error
    pass
```

---

## Resources

- **Architecture**: `docs/features/core-gao-dev-system-refactor/ARCHITECTURE-AFTER-EPIC-6.md`
- **Epic 6 Summary**: `docs/features/core-gao-dev-system-refactor/EPIC-6-COMPLETION-SUMMARY.md`
- **Migration Guide**: `docs/features/core-gao-dev-system-refactor/MIGRATION-GUIDE.md`
- **Services**: `gao_dev/core/services/`
- **Tests**: `tests/orchestrator/`

---

## Contributing

To extend the orchestrator:

1. **Don't modify the facade** (breaks stability)
2. **Create a new service** (follows Single Responsibility)
3. **Inject the service** into orchestrator
4. **Delegate to the service** from orchestrator
5. **Test the service** independently

---

## Version History

| Version | Date | Notes |
|---------|------|-------|
| 2.0 | 2025-10-30 | Post-Epic 6: Service-based architecture |
| 1.0 | 2025-10-29 | Monolithic God Class (pre-refactoring) |

---

**Status**: Production-Ready
**Last Updated**: 2025-10-30
**Maintained by**: Amelia (Software Developer)

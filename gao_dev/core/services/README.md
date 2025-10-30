# Core Services - Specialized Business Logic

**Version**: 1.0 (Epic 6 - New)
**Status**: Production-Ready
**Last Updated**: 2025-10-30

---

## Overview

The `core/services` module contains four specialized services extracted from the monolithic `GAODevOrchestrator` (Epic 6 refactoring). Each service has a single responsibility and can be used independently or through the orchestrator facade.

**Architecture**: Service-Oriented with Dependency Injection

---

## Services Overview

| Service | Responsibility | File | Lines |
|---------|-----------------|------|-------|
| WorkflowCoordinator | Multi-step workflow execution | `workflow_coordinator.py` | 342 |
| StoryLifecycleManager | Story state management | `story_lifecycle.py` | 172 |
| ProcessExecutor | Subprocess execution | `process_executor.py` | 180 |
| QualityGateManager | Quality validation | `quality_gate.py` | 266 |

---

## Service Details

### 1. WorkflowCoordinator

**Responsibility**: Execute sequences of workflows in order, managing context and events.

**Location**: `gao_dev/core/services/workflow_coordinator.py`

**Dependencies**:
- `IWorkflowRegistry` - Workflow discovery
- `IAgentFactory` - Agent creation
- `IEventBus` - Event publishing

**Key Methods**:

```python
class WorkflowCoordinator:
    async def execute_sequence(
        self,
        sequence: WorkflowSequence,
        context: WorkflowContext
    ) -> WorkflowResult:
        """Execute workflow sequence step-by-step."""

    async def execute_single_step(
        self,
        workflow: IWorkflow,
        context: WorkflowContext
    ) -> StepResult:
        """Execute one workflow step."""

    async def handle_workflow_error(
        self,
        workflow_id: str,
        error: Exception
    ) -> ErrorRecoveryResult:
        """Handle workflow error with recovery logic."""
```

**Usage**:

```python
from gao_dev.core.services import WorkflowCoordinator

coordinator = WorkflowCoordinator(
    workflow_registry=registry,
    agent_factory=factory,
    event_bus=bus
)

result = await coordinator.execute_sequence(
    sequence=["prd", "tech-spec", "create-story"],
    context=context
)
```

**Events Published**:
- `WorkflowStarted(workflow_id, timestamp)`
- `StepCompleted(workflow_id, step_num, result)`
- `WorkflowCompleted(workflow_id, result)`
- `WorkflowFailed(workflow_id, error)`

---

### 2. StoryLifecycleManager

**Responsibility**: Manage story creation, state transitions, and lifecycle events.

**Location**: `gao_dev/core/services/story_lifecycle.py`

**Dependencies**:
- `IStoryRepository` - Story persistence
- `IEventBus` - Event publishing

**Key Methods**:

```python
class StoryLifecycleManager:
    async def create_story(
        self,
        epic: int,
        story: int,
        details: StoryDetails
    ) -> Story:
        """Create new story with validation."""

    async def transition_state(
        self,
        story_id: StoryIdentifier,
        new_state: StoryState
    ) -> Story:
        """Transition story to new state."""

    async def get_story(self, story_id: StoryIdentifier) -> Story:
        """Retrieve story by ID."""

    async def get_epic_progress(self, epic: int) -> EpicProgress:
        """Calculate epic completion status."""
```

**Usage**:

```python
from gao_dev.core.services import StoryLifecycleManager

manager = StoryLifecycleManager(
    story_repository=repo,
    event_bus=bus
)

story = await manager.create_story(
    epic=1,
    story=1,
    details=StoryDetails(
        title="Build API",
        description="REST endpoints"
    )
)

await manager.transition_state(
    story_id=story.id,
    new_state=StoryState.IN_PROGRESS
)
```

**Valid State Transitions**:
```
Ready → In Progress → Code Review → Testing → Done
```

**Events Published**:
- `StoryCreated(story_id, epic, story)`
- `StateTransitioned(story_id, old_state, new_state)`
- `StoryCompleted(story_id, result)`

---

### 3. ProcessExecutor

**Responsibility**: Execute subprocesses (Claude agent tasks) and collect output.

**Location**: `gao_dev/core/services/process_executor.py`

**Dependencies**:
- `IEventBus` - Event publishing

**Key Methods**:

```python
class ProcessExecutor:
    async def execute_agent_task(
        self,
        agent_name: str,
        task: str,
        context: AgentContext
    ) -> ProcessResult:
        """Execute agent task in subprocess."""

    async def execute_workflow_task(
        self,
        workflow_name: str,
        context: WorkflowContext
    ) -> ProcessResult:
        """Execute workflow command."""

    async def stream_output(
        self,
        process: asyncio.subprocess.Process
    ) -> AsyncIterator[str]:
        """Stream subprocess output."""
```

**Usage**:

```python
from gao_dev.core.services import ProcessExecutor

executor = ProcessExecutor(event_bus=bus)

result = await executor.execute_agent_task(
    agent_name="amelia",
    task="Implement Story 1.1",
    context=context
)

print(f"Exit code: {result.exit_code}")
print(f"Output: {result.output}")
```

**Error Handling**:
- Timeout handling (configurable)
- Exit code checking
- Signal handling (SIGTERM, SIGKILL)
- Output streaming with error detection

**Events Published**:
- `ProcessStarted(process_id, timestamp)`
- `ProcessCompleted(process_id, exit_code)`
- `ProcessFailed(process_id, error)`

---

### 4. QualityGateManager

**Responsibility**: Validate workflow artifacts against quality standards.

**Location**: `gao_dev/core/services/quality_gate.py`

**Dependencies**:
- List of `IArtifactValidator` implementations

**Key Methods**:

```python
class QualityGateManager:
    async def validate_artifacts(
        self,
        workflow: IWorkflow,
        artifacts: List[Artifact]
    ) -> ValidationResult:
        """Validate all artifacts from workflow."""

    async def validate_single_artifact(
        self,
        artifact: Artifact,
        rules: List[ValidationRule]
    ) -> ArtifactValidationResult:
        """Validate single artifact."""

    def get_quality_score(
        self,
        validation_result: ValidationResult
    ) -> float:
        """Calculate overall quality score (0.0-1.0)."""
```

**Usage**:

```python
from gao_dev.core.services import QualityGateManager

manager = QualityGateManager(
    validators=[
        FileExistenceValidator(),
        ContentValidator(),
        StructureValidator(),
        ComplianceValidator()
    ]
)

result = await manager.validate_artifacts(
    workflow=workflow,
    artifacts=artifacts
)

print(f"Quality score: {result.quality_score}")
print(f"Validation errors: {result.errors}")
```

**Built-in Validators**:
- **FileExistenceValidator**: Ensure expected files exist
- **ContentValidator**: Validate file content quality
- **StructureValidator**: Check project structure
- **PerformanceValidator**: Performance benchmarks
- **ComplianceValidator**: SOLID principle compliance

**Events Published**:
- `ValidationStarted(workflow_id)`
- `ValidationCompleted(workflow_id, result)`
- `ValidationFailed(workflow_id, errors)`

---

## Design Patterns

### Single Responsibility Principle

Each service has **exactly one reason to change**:

```python
# Good: Each service has one responsibility
class WorkflowCoordinator:
    """Responsibility: Execute workflows"""

class StoryLifecycleManager:
    """Responsibility: Manage story state"""

class ProcessExecutor:
    """Responsibility: Execute subprocesses"""

class QualityGateManager:
    """Responsibility: Validate quality"""

# Bad: One service with multiple responsibilities (what we fixed)
class OldOrchestrator:
    """
    Responsibilities:
    - Workflow execution
    - Story management
    - Process execution
    - Quality validation
    (This was the problem - Epic 6 fixed it)
    """
```

### Dependency Injection

All services use constructor-based dependency injection:

```python
# Good: Dependencies injected
coordinator = WorkflowCoordinator(
    workflow_registry=registry,      # Injected
    agent_factory=factory,           # Injected
    event_bus=bus                    # Injected
)

# Bad: Hard-coded instantiation (what we fixed)
class OldCoordinator:
    def __init__(self):
        self.registry = WorkflowRegistry()  # Hard-coded
        self.factory = AgentFactory()       # Hard-coded
```

### Repository Pattern

Services use repositories for data access:

```python
# Service doesn't know about database
manager = StoryLifecycleManager(
    story_repository=repo,  # Abstraction, not DB
    event_bus=bus
)

# Repository handles data access details
class StoryRepository:
    async def save(self, story: Story):
        # Save to file, database, or wherever
        pass
```

### Event-Driven Architecture

Services publish events for loose coupling:

```python
# Service publishes event
await event_bus.publish(StoryCreated(story.id))

# Subscribers can react without coupling
event_bus.subscribe(StoryCreated, metrics_collector.on_story_created)
event_bus.subscribe(StoryCreated, notification_service.on_story_created)
```

---

## Testing

### Unit Testing Services

```python
import pytest
from unittest.mock import Mock, AsyncMock

class TestWorkflowCoordinator:
    @pytest.fixture
    def coordinator(self):
        return WorkflowCoordinator(
            workflow_registry=Mock(),
            agent_factory=Mock(),
            event_bus=AsyncMock()
        )

    @pytest.mark.asyncio
    async def test_execute_sequence(self, coordinator):
        # Arrange
        coordinator.workflow_registry.get_workflow.return_value = Mock()
        coordinator.agent_factory.create_agent.return_value = Mock()

        # Act
        result = await coordinator.execute_sequence(seq, ctx)

        # Assert
        assert result.status == "completed"
        coordinator.event_bus.publish.assert_called()
```

### Testing with Real Services

```python
@pytest.mark.asyncio
async def test_services_integration():
    # Create real services
    event_bus = EventBus()
    registry = WorkflowRegistry()
    factory = AgentFactory()
    repo = StoryRepository()

    coordinator = WorkflowCoordinator(registry, factory, event_bus)
    manager = StoryLifecycleManager(repo, event_bus)
    executor = ProcessExecutor(event_bus)

    # Test interaction
    story = await manager.create_story(1, 1, details)
    result = await coordinator.execute_sequence(seq, ctx)

    assert story.state == "Ready"
    assert result.status == "completed"
```

---

## Error Handling

### Service-Level Errors

```python
from gao_dev.core.exceptions import (
    ServiceError,
    ValidationError,
    ProcessError,
    StateTransitionError
)

# Handle validation errors
try:
    story = await manager.create_story(1, 1, bad_details)
except ValidationError as e:
    print(f"Validation failed: {e}")

# Handle state transition errors
try:
    await manager.transition_state(story.id, StoryState.COMPLETED)
except StateTransitionError as e:
    print(f"Invalid transition: {e}")

# Handle process errors
try:
    result = await executor.execute_agent_task("agent", "task", ctx)
except ProcessError as e:
    print(f"Process failed: {e}")
```

---

## Performance

### Execution Performance

| Operation | Time | Notes |
|-----------|------|-------|
| create_story() | ~5ms | Database write |
| transition_state() | ~3ms | Validation + update |
| execute_sequence() | Varies | Depends on workflows |
| validate_artifacts() | ~50-500ms | Depends on validators |

### Memory Usage

| Service | Memory | Notes |
|---------|--------|-------|
| WorkflowCoordinator | ~10MB | Minimal state |
| StoryLifecycleManager | ~5MB | Repository handling |
| ProcessExecutor | ~50-500MB | Subprocess overhead |
| QualityGateManager | ~20MB | Validator instances |

---

## Configuration

### Environment Variables

```python
# Subprocess timeout
PROCESS_TIMEOUT = int(os.getenv("PROCESS_TIMEOUT", "3600"))  # 1 hour

# Quality gate threshold
QUALITY_THRESHOLD = float(os.getenv("QUALITY_THRESHOLD", "0.85"))

# Event bus implementation
EVENT_BUS_TYPE = os.getenv("EVENT_BUS_TYPE", "in-memory")
```

---

## Usage Patterns

### Pattern 1: Using Through Orchestrator (Recommended)

```python
# Simplest - use facade
from gao_dev.orchestrator import GAODevOrchestrator

orchestrator = GAODevOrchestrator()
result = await orchestrator.execute_workflow_sequence(seq, ctx)
```

### Pattern 2: Direct Service Usage (Advanced)

```python
# More control - use services directly
from gao_dev.core.services import WorkflowCoordinator

coordinator = WorkflowCoordinator(registry, factory, bus)
result = await coordinator.execute_sequence(seq, ctx)
```

### Pattern 3: Subscribing to Events (Integration)

```python
# Listen to events for integration
from gao_dev.core.events.events import StoryCreated

bus.subscribe(StoryCreated, my_event_handler)
```

---

## FAQ

### Q: Should I use services directly or through the facade?

**A**: Use the facade (GAODevOrchestrator) unless you need fine-grained control. Services are for advanced use cases.

### Q: How do I test services?

**A**: Use dependency injection with mocks:
```python
coordinator = WorkflowCoordinator(
    Mock(),  # workflow_registry
    Mock(),  # agent_factory
    Mock()   # event_bus
)
```

### Q: How do I subscribe to service events?

**A**: Use the EventBus:
```python
event_bus.subscribe(StoryCreated, my_handler)
```

### Q: Can I create custom validators?

**A**: Yes, implement `IArtifactValidator`:
```python
class MyValidator(IArtifactValidator):
    async def validate(self, artifact: Artifact) -> ValidationResult:
        # Custom validation
        pass
```

### Q: What if I need to modify service behavior?

**A**: Services are designed for extension, not modification. Create decorators or compose services instead.

---

## Resources

- **Architecture**: `docs/features/core-gao-dev-system-refactor/ARCHITECTURE-AFTER-EPIC-6.md`
- **Orchestrator**: `gao_dev/orchestrator/README.md`
- **Sandbox**: `gao_dev/sandbox/README.md`
- **Tests**: `tests/core/services/`

---

## Contributing

To add new services:

1. Create service class with single responsibility
2. Use dependency injection for all dependencies
3. Implement interface (if shared behavior)
4. Publish domain events
5. Write comprehensive tests
6. Document public API

---

**Status**: Production-Ready
**Last Updated**: 2025-10-30
**Maintained by**: Amelia (Software Developer)

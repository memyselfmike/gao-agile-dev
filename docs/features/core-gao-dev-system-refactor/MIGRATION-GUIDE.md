# Migration Guide: Epic 6 Refactoring

**Date**: 2025-10-30
**Version**: 1.0
**Status**: FINAL
**Audience**: Developers integrating with GAO-Dev

---

## Overview

Epic 6 refactored the GAO-Dev core system from monolithic God Classes to a clean, service-based architecture. This guide helps you understand what changed and how to migrate your code if needed.

**Good news**: Most users won't need to change anything. The public API is stable and backward compatible.

---

## Breaking Changes Assessment

### Executive Summary

**Breaking Changes**: NONE for users of the public facade

**What This Means**:
- Existing code using `GAODevOrchestrator` continues to work
- Existing code using `SandboxManager` continues to work
- No migration required for existing integrations
- New code can leverage new service-based architecture

---

## What Changed

### 1. Internal Architecture

**Before (Monolithic)**:
```python
# All logic in one class
class GAODevOrchestrator:
    # 1,327 lines with 8+ responsibilities:
    - Workflow coordination
    - Story lifecycle
    - Process execution
    - Quality validation
    - Artifact creation
    - Health checks
    - Brian integration
    - Result tracking
```

**After (Service-Based)**:
```python
# Thin facade with specialized services
class GAODevOrchestrator:  # 728 lines
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
        # ... delegates to services
```

### 2. Service Availability

**New**: Services are now available for direct use

**Before**:
```python
# Could only use facade
orchestrator = GAODevOrchestrator()
result = await orchestrator.execute_workflow_sequence(seq, ctx)
```

**After (Still works)**:
```python
# Can use facade (still works)
orchestrator = GAODevOrchestrator()
result = await orchestrator.execute_workflow_sequence(seq, ctx)

# OR use services directly (new)
coordinator = WorkflowCoordinator(registry, factory, bus)
result = await coordinator.execute_sequence(seq, ctx)
```

### 3. Event Publishing

**New**: Services now publish domain events

**Before**: Limited event publishing

**After**: Services publish at key lifecycle points

```python
# Events published by services:
- WorkflowStarted(workflow_id)
- StepCompleted(workflow_id, step)
- WorkflowCompleted(workflow_id, result)
- StoryCreated(story_id)
- StateTransitioned(story_id, old_state, new_state)
- ProjectCreated(project_id)
```

---

## Migration Scenarios

### Scenario 1: Using the Public Facade (No Migration Needed)

**If you use GAODevOrchestrator**, nothing changes:

```python
# Your existing code continues to work
from gao_dev.orchestrator import GAODevOrchestrator

orchestrator = GAODevOrchestrator()
result = await orchestrator.execute_workflow_sequence(
    sequence=workflow_seq,
    context=workflow_ctx
)
```

**Status**: ✓ No changes needed
**Migration Difficulty**: NONE
**Compatibility**: 100%

---

### Scenario 2: Using SandboxManager (No Migration Needed)

**If you use SandboxManager**, nothing changes:

```python
# Your existing code continues to work
from gao_dev.sandbox import SandboxManager

manager = SandboxManager()
project = await manager.create_project(
    name="my-project",
    boilerplate_url="https://..."
)
```

**Status**: ✓ No changes needed
**Migration Difficulty**: NONE
**Compatibility**: 100%

---

### Scenario 3: Accessing New Services (Enhancement, Not Required)

**New**: You can now use services directly for fine-grained control

**Old pattern** (still works):
```python
from gao_dev.orchestrator import GAODevOrchestrator

orchestrator = GAODevOrchestrator()
result = await orchestrator.execute_workflow_sequence(seq, ctx)
```

**New pattern** (optional):
```python
from gao_dev.core.services import (
    WorkflowCoordinator,
    StoryLifecycleManager,
    ProcessExecutor,
    QualityGateManager
)
from gao_dev.core.events import EventBus
from gao_dev.core.workflow_registry import WorkflowRegistry
from gao_dev.agents.factory import AgentFactory

# Initialize services
event_bus = EventBus()
registry = WorkflowRegistry()
factory = AgentFactory()

# Create coordinator
coordinator = WorkflowCoordinator(registry, factory, event_bus)

# Use directly
result = await coordinator.execute_sequence(seq, ctx)
```

**Status**: Optional enhancement
**Migration Difficulty**: NONE (existing code works)
**Benefits**: Fine-grained control, testability, service reuse

---

### Scenario 4: Subscribing to Events (New Capability)

**New**: Services publish events that you can subscribe to

```python
from gao_dev.core.events import EventBus
from gao_dev.core.events.events import StoryCreated, WorkflowCompleted

# Create event bus
event_bus = EventBus()

# Subscribe to events
async def on_story_created(event: StoryCreated):
    print(f"Story created: {event.story_id}")

event_bus.subscribe(StoryCreated, on_story_created)

# Events published automatically by services
# Your handler will be called
```

**Status**: Optional new feature
**Migration Difficulty**: NONE (existing code works without subscribing)
**Benefits**: Extensibility, loose coupling, new integration points

---

## Code Examples

### Example 1: Basic Usage (No Changes)

```python
# Before and After - Identical code
from gao_dev.orchestrator import GAODevOrchestrator

async def main():
    orchestrator = GAODevOrchestrator()

    workflow_seq = ["prd", "tech-spec", "create-story", "dev-story"]
    context = WorkflowContext(
        user_prompt="Build a todo app",
        scale_level=ScaleLevel.LEVEL_2
    )

    result = await orchestrator.execute_workflow_sequence(
        sequence=workflow_seq,
        context=context
    )

    print(f"Result: {result.status}")

await main()
```

**Status**: ✓ No migration needed
**Compatibility**: 100%

---

### Example 2: Orchestrator with Events (New Optional Feature)

```python
from gao_dev.orchestrator import GAODevOrchestrator
from gao_dev.core.events import EventBus
from gao_dev.core.events.events import WorkflowCompleted, StoryCreated

class WorkflowMonitor:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.completed_workflows = 0
        self.created_stories = 0

        # Subscribe to events
        event_bus.subscribe(WorkflowCompleted, self.on_workflow_completed)
        event_bus.subscribe(StoryCreated, self.on_story_created)

    async def on_workflow_completed(self, event: WorkflowCompleted):
        self.completed_workflows += 1
        print(f"Workflow {event.workflow_id} completed!")

    async def on_story_created(self, event: StoryCreated):
        self.created_stories += 1
        print(f"Story {event.story_id} created!")

async def main():
    event_bus = EventBus()
    monitor = WorkflowMonitor(event_bus)

    orchestrator = GAODevOrchestrator(
        event_bus=event_bus  # Pass event bus
    )

    result = await orchestrator.execute_workflow_sequence(seq, ctx)
    print(f"Total workflows: {monitor.completed_workflows}")

await main()
```

**Status**: New optional feature
**Migration Difficulty**: NONE
**Benefit**: Real-time monitoring

---

### Example 3: Using Services Directly (New Optional)

```python
from gao_dev.core.services import WorkflowCoordinator, StoryLifecycleManager
from gao_dev.core.events import EventBus
from gao_dev.core.workflow_registry import WorkflowRegistry
from gao_dev.agents.factory import AgentFactory

async def main():
    # Initialize services
    event_bus = EventBus()
    registry = WorkflowRegistry()
    factory = AgentFactory()
    repo = StoryRepository()

    # Create specialized services
    coordinator = WorkflowCoordinator(registry, factory, event_bus)
    story_manager = StoryLifecycleManager(repo, event_bus)

    # Use services directly
    # This gives you fine-grained control vs using orchestrator facade
    story = await story_manager.create_story(
        epic=1,
        story=1,
        details=StoryDetails(
            title="Build API",
            description="Create REST API"
        )
    )

    result = await coordinator.execute_sequence(
        sequence=["tech-spec", "dev-story"],
        context=ctx
    )

    print(f"Story {story.id} created and workflow executed")

await main()
```

**Status**: New optional capability
**Migration Difficulty**: NONE
**Benefit**: Fine-grained control, direct service usage

---

### Example 4: Testing with Services (Improved Testability)

```python
# Before: Difficult to test due to tight coupling
# After: Easy to test with mock services

import pytest
from unittest.mock import Mock, AsyncMock
from gao_dev.core.services import WorkflowCoordinator

class TestWorkflowCoordinator:
    @pytest.fixture
    def coordinator(self):
        # Create mocks
        workflow_registry = Mock()
        agent_factory = Mock()
        event_bus = AsyncMock()

        return WorkflowCoordinator(
            workflow_registry=workflow_registry,
            agent_factory=agent_factory,
            event_bus=event_bus
        )

    @pytest.mark.asyncio
    async def test_execute_sequence(self, coordinator):
        # Mock dependencies
        coordinator.workflow_registry.get_workflow.return_value = Mock()
        coordinator.agent_factory.create_agent.return_value = Mock()

        # Execute
        result = await coordinator.execute_sequence(seq, ctx)

        # Assert
        assert result.status == "completed"
        coordinator.event_bus.publish.assert_called()

```

**Status**: Much improved
**Migration Difficulty**: NONE
**Benefit**: Easy unit testing

---

## Import Changes

### Old Imports (Still Work)

```python
# These still work - no changes needed
from gao_dev.orchestrator import GAODevOrchestrator
from gao_dev.sandbox import SandboxManager
```

### New Imports (Optional)

```python
# These are now available
from gao_dev.core.services import (
    WorkflowCoordinator,
    StoryLifecycleManager,
    ProcessExecutor,
    QualityGateManager
)

from gao_dev.sandbox.repositories import ProjectRepository
from gao_dev.sandbox.project_lifecycle import ProjectLifecycleService
from gao_dev.sandbox.benchmark_tracker import BenchmarkTrackingService
from gao_dev.sandbox.boilerplate_service import BoilerplateService

from gao_dev.core.events import EventBus
from gao_dev.core.events.events import (
    StoryCreated,
    WorkflowCompleted,
    StateTransitioned
)
```

---

## Dependency Injection Pattern

### Before

```python
# Tightly coupled, hard to test
class OldOrchestrator:
    def __init__(self):
        self.workflow_registry = WorkflowRegistry()  # Direct instantiation
        self.agent_factory = AgentFactory()           # Direct instantiation

# Hard to test because can't substitute dependencies
```

### After

```python
# Loosely coupled, easy to test
class WorkflowCoordinator:
    def __init__(
        self,
        workflow_registry: IWorkflowRegistry,  # Injected
        agent_factory: IAgentFactory,          # Injected
        event_bus: IEventBus                   # Injected
    ):
        self.workflow_registry = workflow_registry
        self.agent_factory = agent_factory
        self.event_bus = event_bus

# Easy to test with mocks
coordinator = WorkflowCoordinator(
    workflow_registry=Mock(),
    agent_factory=Mock(),
    event_bus=Mock()
)
```

---

## FAQ

### Q: Will my code break after Epic 6?

**A**: No. The public API is stable and backward compatible. Existing code using `GAODevOrchestrator` and `SandboxManager` continues to work unchanged.

### Q: Do I need to update my imports?

**A**: No, existing imports continue to work. New imports are available optionally.

### Q: Can I still use the orchestrator facade?

**A**: Yes, the facade is the recommended way to use GAO-Dev. Services are available for advanced users who need fine-grained control.

### Q: How do I subscribe to events?

**A**: Create an EventBus, pass it to services, and subscribe to event types:

```python
event_bus = EventBus()
event_bus.subscribe(WorkflowCompleted, handler_function)
```

### Q: What if I want to use services directly?

**A**: Create instances with dependency injection:

```python
coordinator = WorkflowCoordinator(registry, factory, event_bus)
result = await coordinator.execute_sequence(seq, ctx)
```

### Q: Are there performance implications?

**A**: No. The refactoring focused on structure, not algorithms. Performance is identical (< 200ms startup overhead).

### Q: Do I need to understand services to use GAO-Dev?

**A**: No. Use the facade as before. Understanding services is optional for advanced use cases.

### Q: How do I test my integration?

**A**: Use dependency injection with mocks:

```python
coordinator = WorkflowCoordinator(
    Mock(),  # workflow_registry
    Mock(),  # agent_factory
    Mock()   # event_bus
)
```

### Q: What about legacy_models.py?

**A**: Removed in Story 6.8. All references migrated to new locations.

### Q: Can I extend with plugins?

**A**: Yes! Plugin system is ready (Epic 4). Create plugins that subscribe to events.

---

## Troubleshooting

### Issue: AttributeError about missing method

**Cause**: Code might be calling internal method that was refactored

**Solution**: Use public methods on facade instead, or directly instantiate service

```python
# Wrong
orchestrator._internal_method()

# Right
await orchestrator.execute_workflow_sequence(seq, ctx)
```

### Issue: Events not firing

**Cause**: Event bus not passed to services

**Solution**: Pass event bus during initialization

```python
# Wrong
coordinator = WorkflowCoordinator(registry, factory)

# Right
event_bus = EventBus()
coordinator = WorkflowCoordinator(registry, factory, event_bus)
```

### Issue: Imports not found

**Cause**: New service modules not recognized

**Solution**: Check import paths

```python
# Correct paths
from gao_dev.core.services import WorkflowCoordinator
from gao_dev.core.events import EventBus
from gao_dev.sandbox.repositories import ProjectRepository
```

---

## Testing Your Migration

### Step 1: Verify Public API

```python
from gao_dev.orchestrator import GAODevOrchestrator
from gao_dev.sandbox import SandboxManager

# These should work unchanged
orch = GAODevOrchestrator()
mgr = SandboxManager()
```

### Step 2: Test Existing Workflows

```python
# Run existing code
result = await orch.execute_workflow_sequence(seq, ctx)
assert result.status == "completed"
```

### Step 3: (Optional) Try New Services

```python
from gao_dev.core.services import WorkflowCoordinator

coordinator = WorkflowCoordinator(registry, factory, event_bus)
result = await coordinator.execute_sequence(seq, ctx)
assert result.status == "completed"
```

### Step 4: (Optional) Subscribe to Events

```python
from gao_dev.core.events.events import StoryCreated

def on_story(event):
    print(f"Story: {event.story_id}")

event_bus.subscribe(StoryCreated, on_story)
# Should see output when stories created
```

---

## Summary Table

| Scenario | Breaking Changes | Migration Difficulty | Compatibility |
|----------|-----------------|----------------------|----------------|
| Using facade (GAODevOrchestrator) | NONE | NONE | 100% |
| Using SandboxManager | NONE | NONE | 100% |
| Accessing services directly | NONE (new feature) | NONE | 100% |
| Subscribing to events | NONE (new feature) | NONE | 100% |
| Testing with mocks | NONE (improvement) | NONE | 100% |

---

## Resources

- **Architecture**: See `ARCHITECTURE-AFTER-EPIC-6.md`
- **Completion Summary**: See `EPIC-6-COMPLETION-SUMMARY.md`
- **Code**: `gao_dev/core/services/` and `gao_dev/sandbox/`
- **Tests**: See test files for usage examples

---

## Conclusion

Epic 6 refactoring maintains complete backward compatibility while offering new optional features:

- **No breaking changes** for users of public facade
- **Optional service usage** for fine-grained control
- **Event system** for loose coupling
- **Better testability** via dependency injection
- **Clean architecture** for long-term maintenance

**Your existing code continues to work. Enjoy the improved architecture!**

---

**Version**: 1.0
**Date**: 2025-10-30
**Status**: FINAL

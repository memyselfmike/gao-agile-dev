# Story 2.1: Extract WorkflowCoordinator from Orchestrator

**Epic**: Epic 2 - God Class Refactoring
**Story Points**: 5
**Priority**: P0 (Critical)
**Status**: Draft

---

## User Story

**As a** core developer
**I want** workflow coordination logic extracted from GAODevOrchestrator
**So that** workflow execution is a focused, testable component

---

## Description

Extract workflow coordination logic from the 1,328-line `GAODevOrchestrator` class into a new `WorkflowCoordinator` service. This class will handle multi-step workflow execution, agent coordination, and result aggregation.

**Current State**: Lines 893-1104 in orchestrator.py contain workflow coordination logic mixed with other concerns.

**Target State**: New `WorkflowCoordinator` class (< 200 lines) in `gao_dev/core/services/workflow_coordinator.py`.

---

## Acceptance Criteria

### WorkflowCoordinator Implementation

- [ ] **Class created**: `gao_dev/core/services/workflow_coordinator.py`
- [ ] **Constructor**: Accepts IWorkflowRegistry, IAgentFactory, IEventBus (dependency injection)
- [ ] **Size**: < 200 lines
- [ ] **Single responsibility**: Coordinate workflow sequence execution

### Methods

- [ ] **execute_sequence(sequence, context)** → WorkflowResult
  - Execute list of workflows in order
  - Handle workflow step execution
  - Aggregate step results
  - Publish events (WorkflowStarted, WorkflowCompleted, WorkflowFailed)

- [ ] **execute_step(workflow_info, step_number)** → WorkflowStepResult
  - Execute single workflow step
  - Get appropriate agent from factory
  - Delegate to agent
  - Handle errors gracefully

### Integration

- [ ] **GAODevOrchestrator refactored**:
  - Instantiates WorkflowCoordinator in constructor
  - Delegates to coordinator.execute_sequence()
  - No direct workflow execution logic remaining

### Testing

- [ ] Unit tests for WorkflowCoordinator (80%+ coverage)
- [ ] Integration tests for complete workflows
- [ ] Regression tests ensure existing behavior preserved
- [ ] All existing orchestrator tests still pass

---

## Technical Details

### Extraction Strategy

1. **Identify methods to extract**:
   - `execute_workflow()` → `execute_sequence()`
   - `_execute_workflow_step()` → `execute_step()`
   - `_get_agent_for_workflow()` → moved to AgentFactory
   - `_get_agent_method_for_workflow()` → moved to workflow mapping

2. **Add dependency injection**:
   ```python
   class WorkflowCoordinator:
       def __init__(
           self,
           workflow_registry: IWorkflowRegistry,
           agent_factory: IAgentFactory,
           event_bus: IEventBus
       ):
           self.workflow_registry = workflow_registry
           self.agent_factory = agent_factory
           self.event_bus = event_bus
   ```

3. **Maintain backward compatibility**:
   - GAODevOrchestrator keeps same public API
   - Internal delegation to WorkflowCoordinator
   - No breaking changes

---

## Dependencies

- **Depends On**:
  - Epic 1 complete (interfaces, base classes)
  - Regression test suite created

- **Blocks**:
  - Story 2.5 (Refactor orchestrator as facade)
  - All future orchestrator work

---

## Definition of Done

- [ ] WorkflowCoordinator class < 200 lines
- [ ] Single responsibility (one sentence description possible)
- [ ] 80%+ test coverage
- [ ] All existing tests pass (100%)
- [ ] Integration test demonstrates end-to-end workflow
- [ ] GAODevOrchestrator delegates to coordinator
- [ ] Code review approved
- [ ] Merged to feature branch

---

## Related

- **Epic**: Epic 2 - God Class Refactoring
- **Next Story**: Story 2.2 - Extract StoryLifecycleManager

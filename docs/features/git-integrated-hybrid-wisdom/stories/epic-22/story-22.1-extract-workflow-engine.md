# Story 22.1: Extract WorkflowExecutionEngine

**Epic**: Epic 22 - Orchestrator Decomposition & Architectural Refactoring
**Story ID**: 22.1
**Priority**: P0
**Estimate**: 6 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Extract workflow execution logic from the GAODevOrchestrator into a dedicated WorkflowExecutionEngine service. This is the first step in decomposing the orchestrator god class (1,477 LOC) into focused, maintainable services.

The workflow execution engine will handle all workflow-related logic including workflow execution, task execution, variable resolution, and error handling. This extraction reduces the orchestrator's complexity and follows the Single Responsibility Principle.

This story must be completed first as workflow execution is the core functionality that other services build upon.

---

## Acceptance Criteria

- [ ] Create `WorkflowExecutionEngine` service (~200 LOC)
- [ ] Move `execute_workflow()` logic to engine (~210 LOC)
- [ ] Move `execute_task()` logic to engine (~40 LOC)
- [ ] Orchestrator delegates workflow execution to engine
- [ ] All existing workflow execution tests pass
- [ ] 10 new unit tests for engine
- [ ] Zero breaking changes to public API
- [ ] Service follows SOLID principles (<200 LOC)

---

## Technical Approach

### Implementation Details

The WorkflowExecutionEngine will encapsulate all workflow execution logic currently embedded in the orchestrator. It will own workflow variable resolution, template rendering, and execution coordination.

**Key Responsibilities**:
1. Execute workflows with variable resolution
2. Execute generic tasks via workflows
3. Handle workflow errors and retries
4. Coordinate with WorkflowRegistry and PromptLoader
5. Return structured workflow results

**Design Pattern**: Service pattern with dependency injection

### Files to Modify

- `gao_dev/orchestrator/workflow_execution_engine.py` (+200 LOC / NEW)
  - Add: WorkflowExecutionEngine class
  - Add: execute() method (from orchestrator's execute_workflow)
  - Add: execute_task() method (from orchestrator's execute_task)
  - Add: Error handling and logging
  - Add: Variable resolution coordination

- `gao_dev/orchestrator/orchestrator.py` (-250 LOC / +20 delegation)
  - Remove: execute_workflow() implementation (~210 LOC)
  - Remove: execute_task() implementation (~40 LOC)
  - Add: Delegate to workflow_engine.execute()
  - Add: workflow_engine initialization in __init__

### New Files to Create

- `gao_dev/orchestrator/workflow_execution_engine.py` (~200 LOC)
  - Purpose: Dedicated service for workflow execution
  - Key components:
    - WorkflowExecutionEngine class
    - execute(workflow_name, params) -> WorkflowResult
    - execute_task(task_name, agent, params) -> WorkflowResult
    - _resolve_variables() helper
    - _handle_workflow_error() helper

- `tests/orchestrator/test_workflow_execution_engine.py` (~150 LOC)
  - Purpose: Unit tests for workflow execution engine
  - Key components:
    - 10 unit tests covering all methods
    - Mock WorkflowRegistry and PromptLoader
    - Test variable resolution
    - Test error handling

---

## Testing Strategy

### Unit Tests (10 tests)

- test_execute_workflow_success() - Verifies successful workflow execution
- test_execute_workflow_with_variables() - Tests variable resolution
- test_execute_workflow_error_handling() - Tests error scenarios
- test_execute_task_success() - Verifies task execution
- test_execute_task_with_agent_mapping() - Tests agent selection
- test_workflow_result_structure() - Validates return type
- test_engine_initialization() - Tests constructor
- test_variable_resolution() - Tests variable resolution logic
- test_workflow_not_found() - Tests missing workflow handling
- test_multiple_workflow_execution() - Tests sequential executions

**Total Tests**: 10 tests
**Test File**: `tests/orchestrator/test_workflow_execution_engine.py`

### Integration Tests (Covered in Story 22.6)

Integration with orchestrator facade will be tested separately.

---

## Dependencies

**Upstream**: None (first story in Epic 22)

**Downstream**:
- Story 22.6 depends on this (orchestrator facade needs engine)
- All workflow execution functionality depends on this service

---

## Implementation Notes

### Current Orchestrator Methods to Extract

```python
# From gao_dev/orchestrator/orchestrator.py

def execute_workflow(self, workflow_name: str, params: Dict[str, Any]) -> WorkflowResult:
    # ~210 LOC implementation
    # Variable resolution
    # Workflow execution
    # Error handling
    # Return WorkflowResult

def execute_task(self, task_name: str, agent_name: str, params: Dict[str, Any]) -> WorkflowResult:
    # ~40 LOC implementation
    # Task execution via workflows
    # Agent coordination
    # Return WorkflowResult
```

### New Engine Structure

```python
# gao_dev/orchestrator/workflow_execution_engine.py

class WorkflowExecutionEngine:
    """Service for executing workflows with variable resolution."""

    def __init__(
        self,
        workflow_registry: WorkflowRegistry,
        workflow_executor: WorkflowExecutor,
        prompt_loader: PromptLoader
    ):
        self.registry = workflow_registry
        self.executor = workflow_executor
        self.prompt_loader = prompt_loader

    def execute(
        self,
        workflow_name: str,
        params: Dict[str, Any],
        agent: Optional[BaseAgent] = None
    ) -> WorkflowResult:
        """Execute workflow with variable resolution."""
        # Load workflow
        # Resolve variables
        # Execute via WorkflowExecutor
        # Return result

    def execute_task(
        self,
        task_name: str,
        params: Dict[str, Any]
    ) -> WorkflowResult:
        """Execute generic task via task prompt."""
        # Load task prompt
        # Execute as workflow
        # Return result
```

### Migration Strategy

1. Create WorkflowExecutionEngine with copied logic
2. Add engine to orchestrator's __init__
3. Update execute_workflow to delegate to engine
4. Run tests to ensure no regressions
5. Remove old implementation from orchestrator
6. Clean up imports and dependencies

### Important Notes

- **Zero Breaking Changes**: Public API must remain identical
- **Variable Resolution**: Ensure WorkflowExecutor integration works
- **Error Handling**: Preserve all existing error handling behavior
- **Logging**: Use structlog for all operations
- **Type Safety**: Full type hints, no `Any` where avoidable

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (10/10 unit tests)
- [ ] Code coverage >80% for new service
- [ ] Code review completed
- [ ] Documentation updated (docstrings, comments)
- [ ] No breaking changes (regression tests pass)
- [ ] Git commit created with proper message
- [ ] MyPy strict mode passes

---

**Created**: 2025-11-09
**Last Updated**: 2025-11-09

# Story 22.6: Convert Orchestrator to Facade

**Epic**: Epic 22 - Orchestrator Decomposition & Architectural Refactoring
**Story ID**: 22.6
**Priority**: P0
**Estimate**: 6 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Convert the GAODevOrchestrator to a thin facade that delegates to the specialized services created in Stories 22.1-22.5. This is the culmination of the decomposition effort, transforming a 1,477 LOC god class into a clean <300 LOC facade.

The facade maintains the exact same public API (zero breaking changes) while delegating all responsibilities to focused services.

---

## Acceptance Criteria

- [ ] Orchestrator reduced to <300 LOC (target: ~250 LOC)
- [ ] All public methods delegate to services
- [ ] High-level API preserved (no breaking changes)
- [ ] Initialization logic simplified
- [ ] Service composition clear and maintainable
- [ ] 10 integration tests pass
- [ ] All existing orchestrator tests still pass

---

## Technical Approach

### Implementation Details

The orchestrator becomes a facade that:
1. Initializes all services in __init__
2. Delegates all workflow execution to WorkflowExecutionEngine
3. Delegates all artifact operations to ArtifactManager
4. Delegates all agent operations to AgentCoordinator
5. Delegates all ceremony operations to CeremonyOrchestrator
6. Maintains high-level convenience methods

**Design Pattern**: Facade pattern with service composition

### Files to Modify

- `gao_dev/orchestrator/orchestrator.py` (refactor to <300 LOC)
  - Refactor: __init__ to create all services
  - Refactor: All public methods to delegate
  - Remove: All implementation logic (moved to services)
  - Simplify: Service wiring and composition
  - Keep: High-level API methods (create_prd, create_story, etc.)

### New Files to Create

- `tests/integration/test_orchestrator_facade.py` (~150 LOC)
  - Purpose: Integration tests for orchestrator facade
  - Key components:
    - 10 integration tests
    - Test service composition
    - Test delegation works correctly
    - Test public API unchanged
    - Test error propagation

---

## Testing Strategy

### Integration Tests (10 tests)

- test_orchestrator_initializes_all_services() - Test service creation
- test_execute_workflow_delegates() - Test workflow delegation
- test_artifact_detection_delegates() - Test artifact delegation
- test_agent_execution_delegates() - Test agent delegation
- test_ceremony_orchestration_delegates() - Test ceremony delegation
- test_create_prd_end_to_end() - Test high-level API
- test_create_story_end_to_end() - Test story creation
- test_error_propagation() - Test errors bubble up correctly
- test_public_api_unchanged() - Test API compatibility
- test_service_dependencies() - Test services work together

**Total Tests**: 10 integration tests
**Test File**: `tests/integration/test_orchestrator_facade.py`

### Regression Tests

All existing orchestrator tests must still pass:
- `tests/orchestrator/test_orchestrator.py`
- `tests/integration/test_orchestrator_integration.py`
- Any workflow-related integration tests

---

## Dependencies

**Upstream**: Stories 22.1, 22.2, 22.3, 22.4, 22.5

**Downstream**: Story 22.7 (validation), Story 22.8 (documentation)

---

## Implementation Notes

### Before Refactoring (Current State)

```python
# gao_dev/orchestrator/orchestrator.py
# Current: 1,477 LOC god class

class GAODevOrchestrator:
    def __init__(self, ...):
        # ~350 LOC initialization
        # Many dependencies
        # Complex setup

    def execute_workflow(self, ...):
        # ~210 LOC implementation
        # Variable resolution
        # Workflow execution
        # Artifact detection

    def create_prd(self, ...):
        # ~80 LOC implementation
        # Workflow execution
        # Agent coordination

    # ... 20+ more methods
```

### After Refactoring (Facade)

```python
# gao_dev/orchestrator/orchestrator.py
# Target: ~250 LOC facade

class GAODevOrchestrator:
    """
    Orchestrator facade for GAO-Dev operations.

    Delegates to specialized services:
    - WorkflowExecutionEngine: Workflow execution
    - ArtifactManager: Artifact detection/registration
    - AgentCoordinator: Agent lifecycle management
    - CeremonyOrchestrator: Ceremony coordination
    """

    def __init__(
        self,
        project_root: Path,
        config_loader: ConfigLoader,
        git_manager: GitManager,
        document_lifecycle: DocumentLifecycleManager
    ):
        """Initialize orchestrator with all services."""
        self.project_root = project_root
        self.config = config_loader
        self.git = git_manager
        self.lifecycle = document_lifecycle

        # Initialize services (delegation)
        self.workflow_engine = WorkflowExecutionEngine(
            workflow_registry=WorkflowRegistry(),
            workflow_executor=WorkflowExecutor(),
            prompt_loader=PromptLoader()
        )

        self.artifact_manager = ArtifactManager(
            document_lifecycle=document_lifecycle,
            tracked_dirs=["docs", "src", "gao_dev"]
        )

        self.agent_coordinator = AgentCoordinator(
            agent_factory=AgentFactory(),
            config=config_loader
        )

        self.ceremony_orchestrator = CeremonyOrchestrator(
            config=config_loader
        )

    # High-level API methods (delegates)

    def create_prd(
        self,
        project_name: str,
        description: str = ""
    ) -> WorkflowResult:
        """Create PRD via John agent and prd workflow."""
        return self.workflow_engine.execute(
            workflow_name="prd",
            params={"project_name": project_name, "description": description}
        )

    def execute_workflow(
        self,
        workflow_name: str,
        params: Dict[str, Any]
    ) -> WorkflowResult:
        """Execute workflow with artifact tracking."""
        # Snapshot before
        before = self.artifact_manager.snapshot(self.project_root)

        # Execute workflow
        result = self.workflow_engine.execute(workflow_name, params)

        # Detect and register artifacts
        after = self.artifact_manager.snapshot(self.project_root)
        artifacts = self.artifact_manager.detect(before, after)
        self.artifact_manager.register(artifacts, params)

        return result

    def create_story(
        self,
        epic_num: int,
        story_num: int,
        title: str
    ) -> WorkflowResult:
        """Create story via Bob agent."""
        return self.workflow_engine.execute(
            workflow_name="create_story",
            params={
                "epic_num": epic_num,
                "story_num": story_num,
                "title": title
            }
        )

    # ... remaining high-level methods (all delegate)
```

### Refactoring Checklist

**Initialization**:
- [ ] Create all 4 services in __init__
- [ ] Pass correct dependencies to each service
- [ ] Remove complex initialization logic (delegated)

**Delegation**:
- [ ] execute_workflow() → workflow_engine.execute()
- [ ] execute_task() → workflow_engine.execute_task()
- [ ] Artifact detection → artifact_manager.snapshot/detect/register
- [ ] Agent execution → agent_coordinator.execute_task()
- [ ] Ceremony calls → ceremony_orchestrator.hold_*()

**High-Level API**:
- [ ] create_prd() → delegates to workflow_engine
- [ ] create_architecture() → delegates to workflow_engine
- [ ] create_story() → delegates to workflow_engine
- [ ] implement_story() → delegates to workflow_engine + agent_coordinator
- [ ] All convenience methods preserved

**Cleanup**:
- [ ] Remove all implementation logic
- [ ] Remove helper methods (moved to services)
- [ ] Simplify imports
- [ ] Update docstrings

### Service Composition Diagram

```
GAODevOrchestrator (Facade ~250 LOC)
         │
         ├─→ WorkflowExecutionEngine
         │   └─> execute(), execute_task()
         │
         ├─→ ArtifactManager
         │   └─> snapshot(), detect(), register()
         │
         ├─→ AgentCoordinator
         │   └─> execute_task(), get_agent()
         │
         └─→ CeremonyOrchestrator
             └─> hold_standup(), hold_retro(), hold_planning()
```

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Orchestrator <300 LOC (target: ~250 LOC)
- [ ] All public methods delegate to services
- [ ] All tests passing (10 integration + all existing)
- [ ] Code review completed
- [ ] No breaking changes confirmed
- [ ] Git commit created
- [ ] Performance not degraded (benchmark if needed)
- [ ] MyPy strict mode passes

---

**Created**: 2025-11-09
**Last Updated**: 2025-11-09

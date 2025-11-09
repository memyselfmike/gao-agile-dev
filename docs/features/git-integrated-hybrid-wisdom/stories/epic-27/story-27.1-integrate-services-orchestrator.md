# Story 27.1: Integrate All Services with Orchestrator

**Epic**: Epic 27 - Integration & Migration
**Story ID**: 27.1
**Priority**: P0
**Estimate**: 8 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Integrate all services from Epics 22-26 with the main GAODevOrchestrator: WorkflowExecutionEngine, ArtifactManager, AgentCoordinator, GitIntegratedStateManager, CeremonyOrchestrator.

---

## Acceptance Criteria

- [ ] WorkflowExecutionEngine integrated (from Epic 22.1)
- [ ] ArtifactManager integrated (from Epic 22.2)
- [ ] AgentCoordinator integrated (from Epic 22.3)
- [ ] GitIntegratedStateManager integrated (from Epic 25.1)
- [ ] CeremonyOrchestrator integrated (from Epic 26.1)
- [ ] All integrations tested (no circular dependencies)
- [ ] Orchestrator facade delegates correctly
- [ ] 10 integration tests

---

## Files to Modify

- `gao_dev/orchestrator/orchestrator.py` (+~100 LOC initialization and delegation)
- `tests/integration/test_orchestrator_integration.py` (+~200 LOC)

---

## Key Changes

```python
class GAODevOrchestrator:
    def __init__(self, ...):
        # Initialize all services
        self.workflow_engine = WorkflowExecutionEngine(...)
        self.artifact_manager = ArtifactManager(...)
        self.agent_coordinator = AgentCoordinator(...)
        self.state_manager = GitIntegratedStateManager(...)
        self.ceremony_orchestrator = CeremonyOrchestrator(...)

    def execute_workflow(self, workflow: str, params: Dict) -> WorkflowResult:
        """Delegate to workflow_engine."""
        return self.workflow_engine.execute(workflow, params)

    def create_story(self, epic: int, story: int, content: str, metadata: Dict) -> Story:
        """Delegate to state_manager (atomic commit)."""
        return self.state_manager.create_story(epic, story, content, metadata)
```

---

## Testing Strategy

- test_workflow_engine_integration()
- test_artifact_manager_integration()
- test_agent_coordinator_integration()
- test_state_manager_integration()
- test_ceremony_orchestrator_integration()
- test_no_circular_dependencies()
- test_service_initialization_order()
- test_facade_delegation()
- + 2 more (10 total)

---

## Definition of Done

- [ ] All 10 tests passing
- [ ] All services integrated
- [ ] No circular dependencies
- [ ] Git commit: "feat(epic-27): integrate all services with orchestrator"

---

**Created**: 2025-11-09

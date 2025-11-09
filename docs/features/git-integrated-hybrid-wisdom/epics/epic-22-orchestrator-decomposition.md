# Epic 22: Orchestrator Decomposition & Architectural Refactoring

**Epic ID**: Epic-GHW-22
**Feature**: Git-Integrated Hybrid Wisdom Architecture
**Duration**: Week 1 (5 days)
**Owner**: Amelia (Developer)
**Status**: Planning
**Priority**: P0 (CRITICAL - Must be first)

---

## Epic Goal

Decompose the orchestrator god class (1,477 LOC) into focused, maintainable services following SOLID principles, while maintaining zero breaking changes to the public API.

**Success Criteria**:
- Orchestrator reduced to <300 LOC (facade only)
- 4-5 new focused services created (<200 LOC each)
- All existing tests still pass (zero breaking changes)
- Public API remains unchanged
- 40+ refactoring tests added

---

## Background & Problem Statement

### Current State

**GAODevOrchestrator is a god class**:
- **1,477 LOC** (should be <300)
- **24 methods** mixing 8 different responsibilities
- **Violates Single Responsibility Principle**
- **Difficult to test, extend, and maintain**

### Responsibilities Mixed in Orchestrator

The orchestrator currently handles:

1. **Initialization & Setup** (~350 LOC) ✅ OK
2. **High-level API** (~150 LOC) ✅ OK
3. **Brian Integration** (~100 LOC) ⚠️ Could be cleaner
4. **Workflow Execution** (~250 LOC) ❌ Should be separate service
5. **Artifact Detection** (~140 LOC) ❌ Should be separate service
6. **Artifact Registration** (~150 LOC) ❌ Should be separate service
7. **Agent Coordination** (~200 LOC) ❌ Should be separate service
8. **Metadata Extraction** (~80 LOC) ❌ Should be separate service

**Total to extract**: ~970 LOC (~66% of the class)

### Why This Must Be First

Adding Epics 23-27 on top of this broken architecture would:
- ❌ Add more complexity to god class
- ❌ Accumulate technical debt
- ❌ Make refactoring harder later
- ❌ Violate clean architecture principles

**The right order**: Fix architecture FIRST, then add enhancements.

---

## User Stories (8 stories)

### Story 22.1: Extract WorkflowExecutionEngine
**Priority**: P0 (Critical)
**Estimate**: 6 hours

**Description**:
Extract workflow execution logic from orchestrator into dedicated WorkflowExecutionEngine service.

**Acceptance Criteria**:
- [ ] Create `WorkflowExecutionEngine` service (~200 LOC)
- [ ] Move `execute_workflow()` logic to engine
- [ ] Move `execute_task()` logic to engine
- [ ] Orchestrator delegates to engine
- [ ] All workflow execution tests pass
- [ ] 10 unit tests for engine

**Methods to Extract**:
- `execute_workflow()` (~210 LOC) → `WorkflowExecutionEngine.execute()`
- `execute_task()` (~40 LOC) → `WorkflowExecutionEngine.execute_task()`

**Files Modified**:
- `gao_dev/orchestrator/orchestrator.py` (-250 LOC, +20 delegation)
- `gao_dev/orchestrator/workflow_execution_engine.py` (new, ~200 LOC)
- `tests/orchestrator/test_workflow_execution_engine.py` (new, ~150 LOC)

---

### Story 22.2: Extract ArtifactManager
**Priority**: P0 (Critical)
**Estimate**: 8 hours

**Description**:
Extract artifact detection, registration, and type inference into dedicated ArtifactManager service.

**Acceptance Criteria**:
- [ ] Create `ArtifactManager` service (~250 LOC)
- [ ] Move snapshot, detection, registration logic
- [ ] Move type inference logic
- [ ] Orchestrator delegates to ArtifactManager
- [ ] All artifact tests pass
- [ ] 15 unit tests for manager

**Methods to Extract**:
- `_snapshot_project_files()` (~70 LOC) → `ArtifactManager.snapshot()`
- `_detect_artifacts()` (~40 LOC) → `ArtifactManager.detect()`
- `_register_artifacts()` (~98 LOC) → `ArtifactManager.register()`
- `_infer_document_type()` (~78 LOC) → `ArtifactManager.infer_type()`

**Files Modified**:
- `gao_dev/orchestrator/orchestrator.py` (-286 LOC, +30 delegation)
- `gao_dev/orchestrator/artifact_manager.py` (new, ~250 LOC)
- `tests/orchestrator/test_artifact_manager.py` (new, ~200 LOC)

---

### Story 22.3: Extract AgentCoordinator
**Priority**: P0 (Critical)
**Estimate**: 6 hours

**Description**:
Extract agent lifecycle management and coordination into dedicated AgentCoordinator service.

**Acceptance Criteria**:
- [ ] Create `AgentCoordinator` service (~180 LOC)
- [ ] Move agent task execution
- [ ] Move agent-workflow mapping
- [ ] Orchestrator delegates to coordinator
- [ ] All agent coordination tests pass
- [ ] 10 unit tests for coordinator

**Methods to Extract**:
- `_execute_agent_task_static()` (~135 LOC) → `AgentCoordinator.execute_task()`
- `_get_agent_for_workflow()` (~35 LOC) → `AgentCoordinator.get_agent()`

**Files Modified**:
- `gao_dev/orchestrator/orchestrator.py` (-170 LOC, +20 delegation)
- `gao_dev/orchestrator/agent_coordinator.py` (new, ~180 LOC)
- `tests/orchestrator/test_agent_coordinator.py` (new, ~150 LOC)

---

### Story 22.4: Extract CeremonyOrchestrator (Foundation)
**Priority**: P1 (High)
**Estimate**: 5 hours

**Description**:
Create foundation for CeremonyOrchestrator service (to be fully implemented in Epic 26).

**Acceptance Criteria**:
- [ ] Create `CeremonyOrchestrator` service (~100 LOC stub)
- [ ] Define ceremony interface (hold_standup, hold_retro, etc.)
- [ ] Orchestrator delegates ceremony calls
- [ ] Basic ceremony test framework
- [ ] 5 unit tests

**New Methods**:
- `hold_standup()` (stub)
- `hold_retrospective()` (stub)
- `hold_planning()` (stub)

**Files Modified**:
- `gao_dev/orchestrator/ceremony_orchestrator.py` (new, ~100 LOC)
- `gao_dev/orchestrator/orchestrator.py` (+20 delegation)
- `tests/orchestrator/test_ceremony_orchestrator.py` (new, ~80 LOC)

---

### Story 22.5: Extract MetadataExtractor Utility
**Priority**: P2 (Medium)
**Estimate**: 3 hours

**Description**:
Extract metadata extraction logic into utility service.

**Acceptance Criteria**:
- [ ] Create `MetadataExtractor` utility (~80 LOC)
- [ ] Move feature name extraction
- [ ] Move epic/story number extraction
- [ ] ArtifactManager uses MetadataExtractor
- [ ] 8 unit tests

**Methods to Extract**:
- `_extract_feature_name()` (~27 LOC) → `MetadataExtractor.extract_feature_name()`
- Additional extraction methods (~50 LOC)

**Files Modified**:
- `gao_dev/orchestrator/metadata_extractor.py` (new, ~80 LOC)
- `gao_dev/orchestrator/artifact_manager.py` (uses MetadataExtractor)
- `tests/orchestrator/test_metadata_extractor.py` (new, ~100 LOC)

---

### Story 22.6: Convert Orchestrator to Facade
**Priority**: P0 (Critical)
**Estimate**: 6 hours

**Description**:
Convert orchestrator to thin facade that delegates to specialized services.

**Acceptance Criteria**:
- [ ] Orchestrator reduced to <300 LOC
- [ ] All public methods delegate to services
- [ ] High-level API preserved (no breaking changes)
- [ ] Initialization logic simplified
- [ ] 10 integration tests

**Orchestrator Structure After**:
```python
class GAODevOrchestrator:
    def __init__(self, ...):
        self.workflow_engine = WorkflowExecutionEngine(...)
        self.artifact_manager = ArtifactManager(...)
        self.agent_coordinator = AgentCoordinator(...)
        self.ceremony_orchestrator = CeremonyOrchestrator(...)

    # High-level API (delegates)
    def create_prd(self, ...):
        return self.workflow_engine.execute(...)

    def execute_workflow(self, ...):
        return self.workflow_engine.execute(...)
```

**Files Modified**:
- `gao_dev/orchestrator/orchestrator.py` (refactor to <300 LOC)
- `tests/integration/test_orchestrator_facade.py` (new, ~150 LOC)

---

### Story 22.7: Refactoring Tests & Validation
**Priority**: P0 (Critical)
**Estimate**: 5 hours

**Description**:
Create comprehensive refactoring tests to ensure zero breaking changes.

**Acceptance Criteria**:
- [ ] All existing tests pass (100%)
- [ ] Public API unchanged (contract tests)
- [ ] Performance not degraded
- [ ] No new external dependencies
- [ ] 15 refactoring validation tests

**Test Categories**:
- Contract tests (API unchanged)
- Regression tests (behavior unchanged)
- Performance tests (no degradation)
- Integration tests (services work together)

**Files Modified**:
- `tests/orchestrator/test_refactoring_validation.py` (new, ~200 LOC)
- All existing orchestrator tests (verify still pass)

---

### Story 22.8: Documentation & Migration Guide
**Priority**: P1 (High)
**Estimate**: 3 hours

**Description**:
Document new architecture and provide migration guide for developers.

**Acceptance Criteria**:
- [ ] Architecture diagram updated
- [ ] Service responsibilities documented
- [ ] Migration guide for custom orchestrations
- [ ] Update CLAUDE.md with new structure
- [ ] Code examples updated

**Files Modified**:
- `docs/features/git-integrated-hybrid-wisdom/ARCHITECTURE.md` (update)
- `docs/features/git-integrated-hybrid-wisdom/EPIC-22-MIGRATION.md` (new)
- `CLAUDE.md` (update orchestrator section)
- `gao_dev/orchestrator/README.md` (new)

---

## Dependencies

**Upstream**: None (foundation epic - MUST be first)

**Downstream**:
- Epic 23: GitManager Enhancement (benefits from clean architecture)
- Epic 24: State Tables & Tracker (integrates with cleaner orchestrator)
- Epic 25: Git-Integrated State Manager (relies on service separation)
- Epic 26: Multi-Agent Ceremonies (builds on CeremonyOrchestrator foundation)

---

## Technical Notes

### Service Extraction Strategy

**Phase 1**: Extract services (Stories 22.1-22.5)
- Create new service classes
- Move methods from orchestrator
- Add delegation in orchestrator

**Phase 2**: Convert to facade (Story 22.6)
- Simplify orchestrator initialization
- Ensure all methods delegate
- Remove duplication

**Phase 3**: Validate (Story 22.7-22.8)
- Run full test suite
- Verify zero breaking changes
- Document new architecture

### LOC Breakdown

| Component | Before | After | Change |
|-----------|--------|-------|--------|
| GAODevOrchestrator | 1,477 | <300 | -1,177 |
| WorkflowExecutionEngine | 0 | ~200 | +200 |
| ArtifactManager | 0 | ~250 | +250 |
| AgentCoordinator | 0 | ~180 | +180 |
| CeremonyOrchestrator | 0 | ~100 | +100 |
| MetadataExtractor | 0 | ~80 | +80 |
| **Total** | **1,477** | **~1,110** | **-367** |

**Net reduction**: 367 LOC (better separation reduces duplication)

### Service Responsibilities

**WorkflowExecutionEngine**:
- Execute workflows with variable resolution
- Execute generic tasks
- Handle workflow errors and retries

**ArtifactManager**:
- Snapshot project files
- Detect created/modified artifacts
- Infer document types
- Register artifacts in document lifecycle

**AgentCoordinator**:
- Map workflows to agents
- Execute agent tasks
- Manage agent lifecycle

**CeremonyOrchestrator** (foundation in Epic 22, full in Epic 26):
- Coordinate multi-agent ceremonies
- Manage ceremony lifecycle
- Track ceremony artifacts

**MetadataExtractor**:
- Extract feature names
- Extract epic/story numbers
- Parse metadata from paths/content

**GAODevOrchestrator** (facade):
- High-level API (create_prd, create_story, etc.)
- Service initialization
- Context management
- Delegates everything else

---

## Testing Strategy

### Unit Tests (~65 tests)

**WorkflowExecutionEngine** (10 tests):
- test_execute_workflow()
- test_execute_task()
- test_error_handling()
- ...

**ArtifactManager** (15 tests):
- test_snapshot_files()
- test_detect_artifacts()
- test_register_artifacts()
- test_infer_document_type()
- ...

**AgentCoordinator** (10 tests):
- test_execute_agent_task()
- test_get_agent_for_workflow()
- test_agent_error_handling()
- ...

**CeremonyOrchestrator** (5 tests):
- test_ceremony_interface()
- test_stub_methods()
- ...

**MetadataExtractor** (8 tests):
- test_extract_feature_name()
- test_extract_epic_number()
- ...

**Orchestrator Facade** (10 tests):
- test_delegates_workflow_execution()
- test_delegates_artifact_management()
- test_public_api_unchanged()
- ...

**Refactoring Validation** (15 tests):
- test_all_public_methods_exist()
- test_api_signatures_unchanged()
- test_behavior_unchanged()
- test_performance_not_degraded()
- ...

### Integration Tests (~10 tests)

- test_orchestrator_facade_integration()
- test_workflow_execution_end_to_end()
- test_artifact_detection_integration()
- test_agent_coordination_integration()
- ...

**Total Tests**: ~75 tests
**Target Coverage**: >80% for all new services

---

## Risks & Mitigation

### Risk 1: Breaking Changes
**Likelihood**: Medium
**Impact**: High
**Mitigation**:
- Use facade pattern (public API unchanged)
- Comprehensive contract tests
- Validation tests before and after

### Risk 2: Performance Degradation
**Likelihood**: Low
**Impact**: Medium
**Mitigation**:
- Services are lightweight (minimal overhead)
- Performance benchmarks
- Profile before/after

### Risk 3: Incomplete Extraction
**Likelihood**: Medium
**Impact**: Medium
**Mitigation**:
- Clear LOC targets per service
- Code review of orchestrator (should be <300 LOC)
- Architecture review after refactor

### Risk 4: Test Maintenance
**Likelihood**: Low
**Impact**: Low
**Mitigation**:
- Existing tests should still pass
- Only add tests for new services
- Integration tests cover edge cases

---

## Success Metrics

### Epic-Level Metrics

- [ ] Orchestrator reduced to <300 LOC (target: ~250)
- [ ] 4-5 services created (<200 LOC each)
- [ ] 75+ tests passing (65 unit, 10 integration)
- [ ] Zero breaking changes (100% API compatibility)
- [ ] All existing tests still pass
- [ ] Documentation complete

### Code Quality Metrics

- [ ] All services <200 LOC (SOLID compliance)
- [ ] Cyclomatic complexity <10 per method
- [ ] Test coverage >80% for new services
- [ ] Zero new linting errors
- [ ] MyPy strict mode passes

---

## Architecture Comparison

### Before (Epic 22)

```
┌─────────────────────────────────────┐
│    GAODevOrchestrator (GOD CLASS)   │
│            1,477 LOC                │
│                                     │
│  - Workflow execution               │
│  - Artifact management              │
│  - Agent coordination               │
│  - Metadata extraction              │
│  - High-level API                   │
│  - Initialization                   │
│  - Brian integration                │
│  - Ceremony coordination (future)   │
└─────────────────────────────────────┘
```

### After (Epic 22)

```
┌────────────────────────────────────────────────────────────┐
│         GAODevOrchestrator (FACADE)                        │
│                   ~250 LOC                                 │
│                                                            │
│  - High-level API (delegates)                              │
│  - Service initialization                                  │
│  - Context management                                      │
└────────────────────────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┬──────────────┐
         ↓               ↓               ↓              ↓
┌────────────────┐ ┌────────────┐ ┌────────────┐ ┌─────────────┐
│WorkflowExec    │ │Artifact    │ │Agent       │ │Ceremony     │
│Engine          │ │Manager     │ │Coordinator │ │Orchestrator │
│~200 LOC        │ │~250 LOC    │ │~180 LOC    │ │~100 LOC     │
└────────────────┘ └────────────┘ └────────────┘ └─────────────┘
         │               │               │
         └───────────────┴───────────────┘
                         │
                  ┌──────────────┐
                  │Metadata      │
                  │Extractor     │
                  │~80 LOC       │
                  └──────────────┘
```

**Benefits**:
- ✅ Single Responsibility Principle (each service <200 LOC)
- ✅ Easy to test (focused services)
- ✅ Easy to extend (add new services)
- ✅ Zero breaking changes (facade pattern)

---

**Epic Status**: Ready for Story Implementation
**Next Step**: Amelia implements Story 22.1
**Created**: 2025-11-09

---

## References

- [Orchestration Architecture Review](../../../analysis/ORCHESTRATION_ARCHITECTURE_REVIEW.md)
- [Gap Analysis Summary](../../../analysis/GAP_ANALYSIS_SUMMARY.md)
- [Current Orchestrator](../../../../gao_dev/orchestrator/orchestrator.py)

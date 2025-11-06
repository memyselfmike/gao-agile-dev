# Epic 6: Story Assignments

**Epic**: Legacy Cleanup & God Class Refactoring
**Created**: 2025-10-30
**Sprint**: Week 11-13
**Total Story Points**: 47

---

## Developer Assignments

### Amelia (Software Developer)
**Primary Responsibility**: Service extraction and refactoring
**Story Points**: 37 (79% of epic)

#### Orchestrator Services (Stories 6.1-6.5)

**Story 6.1: Extract WorkflowCoordinator Service**
- **Points**: 5
- **Duration**: 1 day
- **Status**: Ready
- **Focus**: Extract workflow sequence execution logic
- **Deliverables**:
  - `gao_dev/core/services/workflow_coordinator.py` (< 200 lines)
  - Unit tests (80%+ coverage)
  - Event publishing integration

**Story 6.2: Extract StoryLifecycleManager Service**
- **Points**: 5
- **Duration**: 1 day
- **Status**: Ready
- **Focus**: Extract story/epic lifecycle management
- **Deliverables**:
  - `gao_dev/core/services/story_lifecycle.py` (< 200 lines)
  - Unit tests (80%+ coverage)
  - State transition logic

**Story 6.3: Extract ProcessExecutor Service**
- **Points**: 3
- **Duration**: 0.5 day
- **Status**: Ready
- **Focus**: Extract subprocess execution (Claude CLI)
- **Deliverables**:
  - `gao_dev/core/services/process_executor.py` (< 150 lines)
  - Unit tests (80%+ coverage)
  - Error handling and logging

**Story 6.4: Extract QualityGateManager Service**
- **Points**: 3
- **Duration**: 0.5 day
- **Status**: Ready
- **Focus**: Extract artifact validation logic
- **Deliverables**:
  - `gao_dev/core/services/quality_gate.py` (< 150 lines)
  - Unit tests (80%+ coverage)
  - Validation rules

**Story 6.5: Refactor GAODevOrchestrator as Thin Facade**
- **Points**: 5
- **Duration**: 1 day
- **Status**: Blocked (6.1-6.4 required)
- **Focus**: CRITICAL - Reduce orchestrator to < 200 lines
- **Deliverables**:
  - Refactored `gao_dev/orchestrator/orchestrator.py` (< 200 lines)
  - Facade delegates to all 4 services
  - Integration tests pass
  - Zero regressions

#### Sandbox Services (Stories 6.6-6.7)

**Story 6.6: Extract Services from SandboxManager**
- **Points**: 8
- **Duration**: 2 days
- **Status**: Ready
- **Focus**: Extract 3 services from sandbox manager
- **Deliverables**:
  - `gao_dev/sandbox/repositories/project_repository.py` (< 200 lines)
  - `gao_dev/sandbox/project_lifecycle.py` (< 150 lines)
  - `gao_dev/sandbox/benchmark_tracker.py` (enhanced, < 100 lines)
  - Unit tests for each (80%+ coverage)

**Story 6.7: Refactor SandboxManager as Thin Facade**
- **Points**: 3
- **Duration**: 0.5 day
- **Status**: Blocked (6.6 required)
- **Focus**: Reduce sandbox manager to < 150 lines
- **Deliverables**:
  - Refactored `gao_dev/sandbox/manager.py` (< 150 lines)
  - Facade delegates to 3 services
  - Integration tests pass
  - Zero regressions

#### Legacy Code Cleanup (Story 6.8)

**Story 6.8: Migrate from Legacy Models**
- **Points**: 5
- **Duration**: 1 day
- **Status**: Ready (can run parallel with 6.1-6.7)
- **Focus**: Remove `legacy_models.py`, migrate all imports
- **Deliverables**:
  - Health models moved to `health_check.py`
  - All 8 files migrated from legacy imports
  - `legacy_models.py` deleted
  - All tests passing

---

### Murat (Test Architect)
**Primary Responsibility**: Integration testing and validation
**Story Points**: 8 (17% of epic)

**Story 6.9: Integration Testing & Validation**
- **Points**: 8
- **Duration**: 2 days
- **Status**: Blocked (6.1-6.8 required)
- **Focus**: CRITICAL - Final validation before production
- **Deliverables**:
  - Comprehensive integration test suite
  - E2E workflow tests (create-prd, create-story, dev-story)
  - Sandbox workflow tests (init, run, clean)
  - Performance benchmarks (< 5% variance)
  - Test report with metrics

**Responsibilities**:
- Design integration test strategy
- Create test fixtures and data
- Write integration tests for all workflows
- Execute performance benchmarks
- Validate zero regressions
- Document test coverage and results

---

### Bob (Scrum Master)
**Primary Responsibility**: Documentation and sprint tracking
**Story Points**: 2 (4% of epic)

**Story 6.10: Update Documentation & Architecture**
- **Points**: 2
- **Duration**: 0.5 day
- **Status**: Blocked (6.9 required)
- **Focus**: Update all documentation to match implementation
- **Deliverables**:
  - Updated `ARCHITECTURE.md`
  - Updated `epics.md` (mark Epic 6 complete)
  - Updated `.claude/CLAUDE.md`
  - Updated `README.md`
  - Component diagrams
  - Migration guide (if needed)

**Additional Responsibilities**:
- Track daily progress in `sprint-status.yaml`
- Update story status after completion
- Monitor blockers and dependencies
- Facilitate daily standups
- Update metrics in sprint tracking

---

## Execution Strategy

### Parallel Track 1: Orchestrator (Week 1)
```
Amelia:
  Day 1-2: Stories 6.1 + 6.2 (10 pts)
  Day 3:   Stories 6.3 + 6.4 (6 pts)
  Day 4:   Story 6.5 (5 pts)
```

### Parallel Track 2: Sandbox (Week 2)
```
Amelia:
  Day 1-2: Story 6.6 (8 pts)
  Day 3:   Story 6.7 (3 pts)
```

### Parallel Track 3: Legacy Cleanup (Week 1-2)
```
Amelia:
  Day 4-5 (Week 1) or Day 4 (Week 2): Story 6.8 (5 pts)
  (Can be done in parallel with orchestrator or sandbox work)
```

### Sequential: Validation (Week 3)
```
Murat:
  Day 1-2: Story 6.9 (8 pts) - Integration Testing

Bob:
  Day 3:   Story 6.10 (2 pts) - Documentation
```

---

## Story Dependencies

### Week 1: Orchestrator Refactoring
- **6.1-6.4** can be done sequentially (no internal dependencies)
- **6.5** BLOCKED until 6.1-6.4 complete
- **6.8** can start in parallel

### Week 2: Sandbox Refactoring
- **6.6** can start immediately (no dependencies on orchestrator)
- **6.7** BLOCKED until 6.6 complete
- **6.8** must complete by end of Week 2

### Week 3: Validation
- **6.9** BLOCKED until ALL 6.1-6.8 complete
- **6.10** BLOCKED until 6.9 complete

---

## Daily Standup Format

**Each Developer Reports**:
1. **Yesterday**: Which story worked on, progress percentage
2. **Today**: Which story working on, expected completion
3. **Blockers**: Any impediments or questions

**Bob Tracks**:
- Update `sprint-status.yaml` with progress
- Identify blockers early
- Adjust timeline if needed

---

## Success Criteria by Developer

### Amelia's Success Metrics
- [ ] All 7 services extracted (< 300 lines each)
- [ ] Orchestrator reduced to < 200 lines
- [ ] SandboxManager reduced to < 150 lines
- [ ] `legacy_models.py` removed
- [ ] All unit tests pass (80%+ coverage per service)
- [ ] Zero regressions in existing functionality

### Murat's Success Metrics
- [ ] All integration tests pass (100%)
- [ ] E2E workflows work end-to-end
- [ ] Performance variance < 5%
- [ ] Test coverage report generated
- [ ] All acceptance criteria validated

### Bob's Success Metrics
- [ ] All documentation updated
- [ ] Architecture diagrams reflect new structure
- [ ] Sprint tracking accurate and complete
- [ ] Epic 6 marked complete
- [ ] Migration guide created (if needed)

---

## Communication Protocols

### Daily Updates
- Post progress to sprint channel
- Update story status in `sprint-status.yaml`
- Flag blockers immediately

### Code Reviews
- Each story requires code review before completion
- Reviewer: Bob or another available agent
- Focus: SOLID principles, line count, test coverage

### Integration Checkpoints
- After Story 6.5: Validate orchestrator works
- After Story 6.7: Validate sandbox works
- After Story 6.8: Validate legacy cleanup complete
- After Story 6.9: Final validation checkpoint

---

## Risk Management

### High-Impact Risks

1. **Breaking Existing Functionality** (Amelia)
   - **Mitigation**: Run regression tests after each story
   - **Response**: Revert and iterate if tests fail

2. **Service Boundaries Wrong** (Amelia)
   - **Mitigation**: Follow Epic 2 original design, code review
   - **Response**: Adjust and re-extract if needed

3. **Integration Tests Fail** (Murat)
   - **Mitigation**: Early integration testing during Stories 6.1-6.8
   - **Response**: Identify root cause, work with Amelia to fix

4. **Performance Degradation** (Murat)
   - **Mitigation**: Continuous benchmarking
   - **Response**: Profile and optimize hotspots

---

## Definition of Done (Per Story)

### Amelia (Stories 6.1-6.8)
- [ ] Code written and follows SOLID principles
- [ ] Service/class within line count limits
- [ ] Unit tests written (80%+ coverage)
- [ ] Type hints throughout (mypy passes)
- [ ] Docstrings complete
- [ ] Code reviewed and approved
- [ ] All existing tests still pass
- [ ] Story status updated to "done"
- [ ] Atomic commit pushed

### Murat (Story 6.9)
- [ ] Integration test suite complete
- [ ] All integration tests pass
- [ ] Performance benchmarks executed
- [ ] Test report generated
- [ ] Coverage metrics documented
- [ ] Story status updated to "done"

### Bob (Story 6.10)
- [ ] All documentation files updated
- [ ] Architecture diagrams created/updated
- [ ] Migration guide written (if needed)
- [ ] Epic 6 marked complete in all tracking files
- [ ] Story status updated to "done"

---

## Epic 6 Completion Checklist

**After All Stories Complete**:
- [ ] All 10 stories marked "done"
- [ ] All 47 story points complete
- [ ] All acceptance criteria met
- [ ] All tests passing (unit + integration)
- [ ] Code metrics: orchestrator < 200, sandbox < 150
- [ ] Documentation updated
- [ ] Stakeholder demo complete
- [ ] Ready to merge to main

---

**Status**: Assignments Complete
**Next Action**: Create regression test suite, then start Story 6.1
**Estimated Completion**: 3 weeks from start date

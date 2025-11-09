# Epic Overview: Git-Integrated Hybrid Wisdom Architecture

**Feature**: Git-Integrated Hybrid Wisdom Architecture
**Total Epics**: 6 (Epics 22-27)
**Total Duration**: 6 weeks (1 epic per week)
**Status**: Planning

---

## Epic Summary

### Epic 22: Orchestrator Decomposition & Architectural Refactoring
**Duration**: Week 1 (5 days)
**Owner**: Amelia (Developer)
**Stories**: ~8 stories

**Goal**: Decompose orchestrator god class (1000+ LOC) into focused, maintainable services following SOLID principles.

**Key Deliverables**:
- WorkflowCoordinator service (~200 LOC)
- CeremonyOrchestrator service (~200 LOC)
- AgentCoordinator service (~200 LOC)
- Orchestrator facade (delegates to services)
- 40+ refactoring tests
- Zero breaking changes

**Dependencies**: None (foundation epic - MUST be first)

**Success Criteria**:
- Orchestrator reduced to <300 LOC (facade only)
- All services <200 LOC
- All existing tests still pass
- No breaking changes to public API

**Why First**: Fixes root architectural problem before adding complexity

---

### Epic 23: GitManager Enhancement
**Duration**: Week 2 (5 days)
**Owner**: Amelia (Developer)
**Stories**: ~8 stories

**Goal**: Enhance GitManager with transaction support, branch management, and file history methods.

**Key Deliverables**:
- 14 new methods added to GitManager
- GitCommitManager deprecated and functionality migrated
- 30+ unit tests
- API documentation

**Dependencies**: Epic 22 (cleaner architecture for integration)

**Success Criteria**:
- All new methods tested (>80% coverage)
- No breaking changes
- GitCommitManager removed from codebase

---

### Epic 24: State Tables & Tracker
**Duration**: Week 3 (5 days)
**Owner**: Amelia (Developer)
**Stories**: ~7 stories

**Goal**: Create database state tables and StateCoordinator service with specialized sub-services.

**Key Deliverables**:
- Migration 005 (5 new tables with indexes)
- StateCoordinator facade (~300 LOC)
- 5 specialized state services (~100 LOC each)
- 50+ unit tests
- Database schema documentation

**Dependencies**: Epic 22 + Epic 23 (needs clean architecture + GitManager)

**Success Criteria**:
- Migration runs successfully
- Query performance <5ms
- All services follow SRP (<200 LOC)

---

### Epic 25: Git-Integrated State Manager
**Duration**: Week 4 (5 days)
**Owner**: Amelia (Developer)
**Stories**: ~9 stories

**Goal**: Implement git-integrated state management with atomic commits, fast context loading, and safe migration.

**Key Deliverables**:
- GitIntegratedStateManager (~600 LOC)
- FastContextLoader (~400 LOC)
- GitMigrationManager (~500 LOC)
- GitAwareConsistencyChecker (~300 LOC)
- 70+ tests (unit + integration)

**Dependencies**: Epic 22 + Epic 23 + Epic 24

**Success Criteria**:
- Atomic operations with rollback working
- Context loading <5ms
- Migration safe with full rollback
- Consistency checking functional

---

### Epic 26: Multi-Agent Ceremonies Architecture
**Duration**: Week 5 (5 days)
**Owner**: Amelia (Developer)
**Stories**: ~8 stories

**Goal**: Implement multi-agent ceremony system for stand-ups, retrospectives, and planning sessions.

**Key Deliverables**:
- CeremonyOrchestrator (~400 LOC)
- ConversationManager (~300 LOC)
- Ceremony artifacts tracked as documents
- Real-time context loading integration
- 35+ ceremony tests

**Dependencies**: Epic 22 + Epic 25 (needs clean architecture + fast context)

**Success Criteria**:
- Stand-up ceremonies functional
- Retrospective ceremonies functional
- Ceremony artifacts properly tracked
- Context loading <5ms during ceremonies

**Why Included**: Essential for complete wisdom management (not "future work")

---

### Epic 27: Integration & Migration
**Duration**: Week 6 (5 days)
**Owner**: Amelia (Developer) + Bob (Scrum Master)
**Stories**: ~6 stories

**Goal**: Integrate all services, update CLI, create migration tools, and complete documentation.

**Key Deliverables**:
- Full orchestrator integration
- CLI command updates
- Migration tools and documentation
- Updated CLAUDE.md
- 15+ E2E tests
- Migration guide

**Dependencies**: All previous epics (22-26)

**Success Criteria**:
- All tests passing (>80% coverage)
- Performance targets met (<5ms context loads)
- Documentation complete
- Migration tested on real projects

---

## Timeline

```
Week 1: Epic 22 - Orchestrator Decomposition (FOUNDATION)
├── Day 1-2: Extract WorkflowCoordinator
├── Day 3: Extract CeremonyOrchestrator
├── Day 4: Extract AgentCoordinator
└── Day 5: Convert Orchestrator to facade + testing

Week 2: Epic 23 - GitManager Enhancement
├── Day 1-2: Transaction support methods
├── Day 3: Branch management methods
├── Day 4: File history methods
└── Day 5: Deprecation & testing

Week 3: Epic 24 - State Tables & Tracker
├── Day 1: Migration 005 (tables + indexes)
├── Day 2-3: StateCoordinator + services
├── Day 4: Testing & optimization
└── Day 5: Documentation

Week 4: Epic 25 - Git-Integrated State Manager
├── Day 1-2: GitIntegratedStateManager
├── Day 3: FastContextLoader
├── Day 4: Migration & consistency checking
└── Day 5: Integration tests

Week 5: Epic 26 - Multi-Agent Ceremonies
├── Day 1-2: CeremonyOrchestrator
├── Day 3: ConversationManager
├── Day 4: Ceremony artifact tracking
└── Day 5: Integration tests

Week 6: Epic 27 - Integration & Migration
├── Day 1-2: Full orchestrator integration
├── Day 3: CLI updates
├── Day 4: Migration tools & E2E tests
└── Day 5: Documentation & validation
```

---

## Story Count Estimate

| Epic | Stories | Avg Story Size | Total Effort |
|------|---------|----------------|--------------|
| Epic 22 | 8 | 4-6 hours | 32-48 hours |
| Epic 23 | 8 | 4-6 hours | 32-48 hours |
| Epic 24 | 7 | 4-6 hours | 28-42 hours |
| Epic 25 | 9 | 4-8 hours | 36-72 hours |
| Epic 26 | 8 | 4-6 hours | 32-48 hours |
| Epic 27 | 6 | 4-8 hours | 24-48 hours |
| **Total** | **46** | **4-7 hours** | **184-306 hours** |

**Total Duration**: 23-38 developer-days (5-8 weeks at 1 developer)

---

## Dependencies Graph

```
Epic 22: Orchestrator Decomposition (FOUNDATION - MUST BE FIRST)
    ↓
    ├─→ Epic 23: GitManager Enhancement
    │       ↓
    │       └─→ Epic 24: State Tables & Tracker
    │               ↓
    │               └─→ Epic 25: Git-Integrated State Manager
    │                       ↓
    │                       ├─→ Epic 26: Multi-Agent Ceremonies
    │                       │       ↓
    └───────────────────────┴──────→ Epic 27: Integration & Migration
```

**Critical Path**: Epic 22 MUST be completed first (fixes architecture)
**Sequential Dependencies**: Epics must be completed in order (22 → 23 → 24 → 25 → 26 → 27)

---

## Why Epic 22 Must Be First

**The Problem**: The orchestrator is a god class (1000+ LOC) that violates SOLID principles and mixes multiple concerns:
- Agent coordination
- Workflow execution
- Ceremony orchestration
- State management
- Context loading

**The Risk**: Adding Epics 23-27 on top of a broken architecture:
- ❌ More complexity added to god class
- ❌ Technical debt accumulates
- ❌ Harder to refactor later
- ❌ Testing becomes more difficult

**The Solution**: Fix architecture FIRST (Epic 22):
- ✅ Clean foundation for enhancements
- ✅ Each service <200 LOC (maintainable)
- ✅ SOLID principles followed
- ✅ Easier to add features (23-27)
- ✅ Zero breaking changes (facade pattern)

**Analogy**: "Fix the engine before adding turbochargers"

---

## Risk Summary

### Critical Risks (Mitigated)

1. **Orchestrator God Class** → ✅ Solved by Epic 22 (decomposition)
2. **Data Consistency** → ✅ Solved by git transaction model (Epic 25)
3. **Migration Safety** → ✅ Solved by git branch + checkpoints (Epic 25)
4. **Performance** → ✅ Validated via benchmarks (Epic 25)

### Remaining Risks (Manageable)

1. **SQLite Concurrency** → Mitigated by git serialization (acceptable)
2. **Database Size Growth** → Monitor, defer archival to v2
3. **Developer Onboarding** → Mitigated by comprehensive docs
4. **Epic 22 Refactoring Complexity** → Mitigated by zero-breaking-changes approach

---

## Success Metrics

### Per-Epic Metrics

**Epic 22**:
- [ ] Orchestrator reduced to <300 LOC (facade)
- [ ] 3 new services created (<200 LOC each)
- [ ] 40+ tests passing
- [ ] Zero breaking changes

**Epic 23**:
- [ ] 14 new GitManager methods implemented
- [ ] 30+ tests passing
- [ ] GitCommitManager removed
- [ ] No breaking changes

**Epic 24**:
- [ ] 5 tables created with indexes
- [ ] 6 services implemented (<200 LOC each)
- [ ] Query performance <5ms
- [ ] 50+ tests passing

**Epic 25**:
- [ ] 4 new services implemented
- [ ] Context loading <5ms (benchmarked)
- [ ] Migration rollback works 100%
- [ ] 70+ tests passing

**Epic 26**:
- [ ] CeremonyOrchestrator implemented
- [ ] ConversationManager implemented
- [ ] Ceremony artifacts tracked
- [ ] 35+ tests passing

**Epic 27**:
- [ ] Full orchestrator integration complete
- [ ] CLI commands updated
- [ ] Documentation complete
- [ ] 15+ E2E tests passing
- [ ] >80% overall test coverage

### Overall Feature Metrics

- [ ] All 46 stories completed
- [ ] >80% test coverage
- [ ] Performance targets met (<5ms)
- [ ] Migration guide complete
- [ ] Zero breaking changes
- [ ] Orchestrator god class eliminated

---

## Epic Files

Each epic has detailed breakdown in:

- [Epic 22: Orchestrator Decomposition](./epic-22-orchestrator-decomposition.md) (NEW - CRITICAL)
- [Epic 23: GitManager Enhancement](./epic-23-gitmanager-enhancement.md) (formerly Epic 1)
- [Epic 24: State Tables & Tracker](./epic-24-state-tables-tracker.md) (formerly Epic 2)
- [Epic 25: Git-Integrated State Manager](./epic-25-git-integrated-state-manager.md) (formerly Epic 3)
- [Epic 26: Multi-Agent Ceremonies](./epic-26-multi-agent-ceremonies.md) (NEW - ESSENTIAL)
- [Epic 27: Integration & Migration](./epic-27-integration-migration.md) (formerly Epic 4)

---

## Gap Analysis Reference

This updated plan addresses all gaps identified in the comprehensive gap analysis (docs/analysis/GAP_ANALYSIS_SUMMARY.md):

**Gaps Fixed**:
1. ✅ Orchestrator god class addressed (Epic 22)
2. ✅ Workflow orchestration architecture addressed (Epic 22)
3. ✅ Multi-agent ceremonies included (Epic 26, not deferred)
4. ✅ Brian provider abstraction (already in Epic 21)
5. ✅ Unified wisdom management (complete document-centric architecture)

**Analysis Documents**:
- ORCHESTRATION_ARCHITECTURE_REVIEW.md → Drives Epic 22
- MULTI_AGENT_CEREMONIES_ARCHITECTURE.md → Drives Epic 26
- WISDOM_MANAGEMENT_INTEGRATION.md → Drives Epics 24-25
- WORKFLOW_ORCHESTRATION_AUDIT.md → Drives Epic 22

---

## Next Steps

1. **Review & Approve**: Product Owner reviews updated epic breakdown
2. **Create Epic 22**: Define detailed stories for orchestrator decomposition
3. **Update Epic Files**: Rename epic-1 to epic-23, create 22, 24-27
4. **Sprint Planning**: Plan Sprint 1 (Epic 22 stories)
5. **Implementation**: Amelia implements Epic 22 stories
6. **Iteration**: Repeat for Epics 23-27

---

**Document Status**: Updated - Aligned with Gap Analysis
**Created**: 2025-11-09
**Last Updated**: 2025-11-09
**Supersedes**: OVERVIEW.md (4 epics, missing orchestrator decomposition)

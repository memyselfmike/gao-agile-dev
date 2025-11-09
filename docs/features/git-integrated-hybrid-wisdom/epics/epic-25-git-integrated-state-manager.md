# Epic 25: Git-Integrated State Manager

**Epic ID**: Epic-GHW-25
**Feature**: Git-Integrated Hybrid Wisdom Architecture
**Duration**: Week 4 (5 days)
**Owner**: Amelia (Developer)
**Status**: Planning
**Previous Epic**: Epic 22, Epic 23, Epic 24

---

## Epic Goal

Implement git-integrated state management with atomic commits, fast context loading, safe migration, and consistency checking.

**Success Criteria**:
- GitIntegratedStateManager implemented (~600 LOC)
- FastContextLoader implemented (~400 LOC)
- GitMigrationManager implemented (~500 LOC)
- GitAwareConsistencyChecker implemented (~300 LOC)
- Context loading <5ms (benchmarked)
- Migration safe with 100% rollback
- 70+ tests passing

---

## Overview

This epic implements the git transaction layer that ensures file-database consistency through atomic git commits.

### Key Deliverables

1. **GitIntegratedStateManager**: Atomic operations via git commits
2. **FastContextLoader**: <5ms context queries
3. **GitMigrationManager**: Safe migration with rollback
4. **GitAwareConsistencyChecker**: Detect and repair inconsistencies
5. **Testing**: 70+ unit and integration tests

---

## User Stories (9 stories)

### Story 25.1: Implement GitIntegratedStateManager (Core)
**Priority**: P0 (Critical)
**Estimate**: 8 hours

**Description**:
Implement core git-integrated state manager with atomic commit support.

**Acceptance Criteria**:
- [ ] Service ~600 LOC
- [ ] create_epic(), create_story(), transition_story() methods
- [ ] All operations atomic (file + DB + git commit)
- [ ] Rollback on error (DB rollback + git reset)
- [ ] 20 unit tests

---

### Story 25.2: Add Transaction Support to State Manager
**Priority**: P0 (Critical)
**Estimate**: 6 hours

**Description**:
Add full transaction support with pre-checks and error handling.

**Acceptance Criteria**:
- [ ] Pre-check: working tree clean
- [ ] DB transaction wrapping
- [ ] Git commit at end
- [ ] Rollback on any error
- [ ] 15 transaction tests

---

### Story 25.3: Implement FastContextLoader
**Priority**: P0 (Critical)
**Estimate**: 8 hours

**Description**:
Implement fast context loader for <5ms epic context queries.

**Acceptance Criteria**:
- [ ] Service ~400 LOC
- [ ] get_epic_context() <5ms
- [ ] get_agent_context() <5ms (role-specific)
- [ ] analyze_existing_project() <10ms
- [ ] 15 unit tests, 5 performance benchmarks

---

### Story 25.4: Implement GitMigrationManager (Phase 1-2)
**Priority**: P1 (High)
**Estimate**: 6 hours

**Description**:
Implement migration manager phases 1-2 (table creation, epic backfill).

**Acceptance Criteria**:
- [ ] Service ~500 LOC
- [ ] Phase 1: Create tables (with git commit)
- [ ] Phase 2: Backfill epics (with git commit)
- [ ] Checkpoint tracking
- [ ] 8 migration tests

---

### Story 25.5: Implement GitMigrationManager (Phase 3-4)
**Priority**: P1 (High)
**Estimate**: 6 hours

**Description**:
Complete migration manager with story backfill and validation.

**Acceptance Criteria**:
- [ ] Phase 3: Backfill stories (infer state from git)
- [ ] Phase 4: Validate migration
- [ ] Rollback support (delete branch)
- [ ] Migration report generation
- [ ] 10 migration tests

---

### Story 25.6: Implement GitAwareConsistencyChecker
**Priority**: P1 (High)
**Estimate**: 6 hours

**Description**:
Implement consistency checker to detect file-DB mismatches.

**Acceptance Criteria**:
- [ ] Service ~300 LOC
- [ ] check_consistency() detects all issues
- [ ] repair() syncs DB to files
- [ ] Git-aware (uses git status)
- [ ] 15 consistency tests

---

### Story 25.7: Integration Tests
**Priority**: P0 (Critical)
**Estimate**: 6 hours

**Description**:
Create comprehensive integration tests for all services.

**Acceptance Criteria**:
- [ ] Test atomic commits end-to-end
- [ ] Test rollback scenarios
- [ ] Test migration full workflow
- [ ] Test consistency check and repair
- [ ] 20 integration tests

---

### Story 25.8: Performance Benchmarks
**Priority**: P1 (High)
**Estimate**: 4 hours

**Description**:
Create performance benchmarks and validate targets.

**Acceptance Criteria**:
- [ ] Epic context <5ms (p95)
- [ ] Agent context <5ms (p95)
- [ ] Story creation <100ms
- [ ] Story transition <50ms
- [ ] 10 benchmark tests

---

### Story 25.9: Documentation
**Priority**: P1 (High)
**Estimate**: 3 hours

**Description**:
Document git transaction model and services.

**Acceptance Criteria**:
- [ ] Git transaction flow documented
- [ ] Service APIs documented
- [ ] Migration guide started
- [ ] Examples added

---

## Dependencies

**Upstream**: Epic 22, Epic 23, Epic 24

**Downstream**: Epic 26 (ceremonies use fast context), Epic 27 (integration)

---

## Technical Notes

### Git Transaction Flow

```
1. Pre-check: git working tree clean
2. Begin DB transaction
3. Write files
4. Update database
5. Commit DB transaction
6. Git add + commit (ATOMIC)
7. On error: rollback DB + git reset --hard
```

### Performance Targets

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Epic context | <5ms | p95 |
| Agent context | <5ms | p95 |
| Story creation | <100ms | Including git |
| Story transition | <50ms | Including git |
| Project analysis | <10ms | Database only |

---

## Testing Strategy

**Unit Tests**: 50+
- GitIntegratedStateManager: 20
- FastContextLoader: 15
- GitMigrationManager: 18
- GitAwareConsistencyChecker: 15

**Integration Tests**: 20

**Performance Benchmarks**: 10

**Total**: 80+ tests

---

## Success Metrics

- [ ] All 4 services implemented
- [ ] Context loading <5ms (benchmarked)
- [ ] Migration rollback works 100%
- [ ] Consistency checking functional
- [ ] 80+ tests passing
- [ ] Test coverage >80%

---

**Epic Status**: Planning (Awaiting Epic 22-24 completion)
**Next Step**: Complete Epics 22-24 first
**Created**: 2025-11-09

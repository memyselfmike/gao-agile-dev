# Story 25.7: Integration Tests

**Epic**: Epic 25 - Git-Integrated State Manager
**Story ID**: 25.7
**Priority**: P0
**Estimate**: 6 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Create comprehensive integration tests validating all Epic 25 services work together end-to-end with real git operations.

---

## Acceptance Criteria

- [ ] Test atomic commits end-to-end (file + DB + git)
- [ ] Test rollback scenarios (all error paths)
- [ ] Test migration full workflow (phases 1-4)
- [ ] Test consistency check and repair
- [ ] All tests use real git (no mocks)
- [ ] 20 integration tests

---

## Files to Create

- `tests/integration/test_git_integrated_state_integration.py` (~400 LOC)

---

## Test Categories

- Atomic operations (5 tests)
- Rollback scenarios (5 tests)
- Migration workflow (5 tests)
- Consistency checking (5 tests)

---

## Definition of Done

- [ ] 20 integration tests passing
- [ ] Git commit: "test(epic-25): add integration tests"

---

**Created**: 2025-11-09

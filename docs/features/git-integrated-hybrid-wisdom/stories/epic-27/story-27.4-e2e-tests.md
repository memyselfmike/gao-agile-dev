# Story 27.4: End-to-End Tests

**Epic**: Epic 27 - Integration & Migration
**Story ID**: 27.4
**Priority**: P0
**Estimate**: 8 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Create comprehensive E2E tests validating complete workflows from CLI commands through orchestrator to git commits.

---

## Acceptance Criteria

- [ ] E2E test: Create epic to completion (PRD → Architecture → Stories → Implementation → Done)
- [ ] E2E test: Ceremony with context loading (stand-up with fast context)
- [ ] E2E test: Existing project migration (full migration workflow)
- [ ] E2E test: Error recovery and rollback (simulate errors, verify rollback)
- [ ] E2E test: Multi-story workflow (create multiple stories, track progress)
- [ ] All tests use real git (no mocks)
- [ ] All tests create temporary projects (cleanup after)
- [ ] 15 E2E tests

---

## Files to Create

- `tests/e2e/test_epic_lifecycle.py` (~200 LOC)
- `tests/e2e/test_ceremony_workflows.py` (~150 LOC)
- `tests/e2e/test_migration_workflows.py` (~150 LOC)
- `tests/e2e/test_error_recovery.py` (~150 LOC)
- `tests/e2e/test_multi_story_workflows.py` (~150 LOC)

---

## Test Categories

**Epic Lifecycle** (3 tests):
- test_create_epic_to_completion()
- test_epic_progress_tracking()
- test_epic_archival()

**Ceremonies** (3 tests):
- test_standup_with_context_loading()
- test_retrospective_with_learnings()
- test_planning_with_estimation()

**Migration** (3 tests):
- test_migration_existing_project()
- test_migration_rollback()
- test_consistency_check_and_repair()

**Error Recovery** (3 tests):
- test_rollback_on_file_error()
- test_rollback_on_db_error()
- test_rollback_on_git_error()

**Multi-Story** (3 tests):
- test_create_multiple_stories()
- test_story_state_transitions()
- test_epic_progress_calculation()

---

## Definition of Done

- [ ] 15 E2E tests passing
- [ ] All tests run in <60 seconds total
- [ ] Git commit: "test(epic-27): add comprehensive E2E tests"

---

**Created**: 2025-11-09

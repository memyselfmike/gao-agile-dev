# Story 25.2: Add Transaction Support to State Manager

**Epic**: Epic 25 - Git-Integrated State Manager
**Story ID**: 25.2
**Priority**: P0
**Estimate**: 6 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Add comprehensive transaction support with pre-checks, DB transaction wrapping, git commit coordination, and full rollback on errors.

---

## Acceptance Criteria

- [ ] Pre-check: is_working_tree_clean() before ALL operations
- [ ] DB transaction wrapping (begin → commit/rollback)
- [ ] Git commit after successful DB commit
- [ ] Full rollback on ANY error (DB + git reset --hard)
- [ ] Structured logging with transaction IDs
- [ ] 15 transaction tests (success + error scenarios)

---

## Files to Modify

- `gao_dev/core/services/git_integrated_state_manager.py` (+~100 LOC)
- `tests/core/services/test_git_integrated_state_manager.py` (+~200 LOC)

---

## Testing Strategy

- test_pre_check_clean_tree()
- test_pre_check_fails_dirty_tree()
- test_db_transaction_wrapping()
- test_rollback_on_file_write_error()
- test_rollback_on_db_error()
- test_rollback_on_git_error()
- test_transaction_logging()
- + 8 more (15 total)

---

## Definition of Done

- [ ] 15 tests passing
- [ ] Full transaction support
- [ ] Git commit: "feat(epic-25): add transaction support to state manager"

---

**Created**: 2025-11-09

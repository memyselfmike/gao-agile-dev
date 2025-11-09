# Story 25.4: Implement GitMigrationManager (Phase 1-2)

**Epic**: Epic 25 - Git-Integrated State Manager
**Story ID**: 25.4
**Priority**: P1
**Estimate**: 6 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Implement GitMigrationManager phases 1-2: table creation and epic backfill. Each phase creates a git commit checkpoint.

---

## Acceptance Criteria

- [ ] Service ~500 LOC (partial, completed in 25.5)
- [ ] Phase 1: Create state tables (with git commit)
- [ ] Phase 2: Backfill epics from files (with git commit)
- [ ] Create migration branch for safety
- [ ] Checkpoint tracking (save SHAs)
- [ ] 8 migration tests

---

## Files to Create

- `gao_dev/core/services/git_migration_manager.py` (~300 LOC partial)
- `tests/core/services/test_git_migration_manager.py` (~150 LOC partial)

---

## Key Methods

```python
class GitMigrationManager:
    def migrate_to_hybrid_architecture(self) -> MigrationResult:
        # 1. Pre-flight checks
        # 2. Create migration branch
        # 3. Phase 1: Create tables (commit)
        # 4. Phase 2: Backfill epics (commit)

    def _phase_1_create_tables(self) -> None
    def _phase_2_backfill_epics(self) -> None
```

---

## Definition of Done

- [ ] 8 tests passing
- [ ] Phases 1-2 complete
- [ ] Git commit: "feat(epic-25): implement GitMigrationManager phases 1-2"

---

**Created**: 2025-11-09

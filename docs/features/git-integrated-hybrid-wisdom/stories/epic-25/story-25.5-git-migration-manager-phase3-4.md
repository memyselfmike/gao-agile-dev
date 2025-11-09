# Story 25.5: Implement GitMigrationManager (Phase 3-4)

**Epic**: Epic 25 - Git-Integrated State Manager
**Story ID**: 25.5
**Priority**: P1
**Estimate**: 6 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Complete GitMigrationManager with story backfill (infer state from git) and validation. Includes rollback support.

---

## Acceptance Criteria

- [ ] Phase 3: Backfill stories (infer state from git history)
- [ ] Phase 4: Validate migration completeness
- [ ] Rollback support (delete migration branch)
- [ ] State inference from git log (commit messages + file age)
- [ ] Migration report generation
- [ ] 10 migration tests

---

## Files to Modify

- `gao_dev/core/services/git_migration_manager.py` (+~200 LOC)
- `tests/core/services/test_git_migration_manager.py` (+~150 LOC)

---

## Key Methods

```python
def _phase_3_backfill_stories(self) -> None:
    """Parse story files, infer state from git, create story_state."""

def _phase_4_validate(self) -> None:
    """Validate all state matches files."""

def _infer_story_state_from_git(self, file: Path) -> str:
    """Infer state from git history."""

def rollback_migration(self, checkpoint_sha: str) -> None:
    """Delete migration branch, rollback to checkpoint."""
```

---

## Definition of Done

- [ ] 10 tests passing
- [ ] Full migration complete
- [ ] Rollback works
- [ ] Git commit: "feat(epic-25): complete GitMigrationManager phases 3-4"

---

**Created**: 2025-11-09

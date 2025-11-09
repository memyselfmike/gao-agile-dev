# Story 25.6: Implement GitAwareConsistencyChecker

**Epic**: Epic 25 - Git-Integrated State Manager
**Story ID**: 25.6
**Priority**: P1
**Estimate**: 6 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Implement GitAwareConsistencyChecker to detect and repair file-database inconsistencies using git status and git history.

---

## Acceptance Criteria

- [ ] Service ~300 LOC
- [ ] check_consistency() detects 4 issue types
- [ ] repair() syncs DB to files (file is source of truth)
- [ ] Git-aware (uses git status, is_file_tracked)
- [ ] Generates ConsistencyReport
- [ ] 15 consistency tests

---

## Files to Create

- `gao_dev/core/services/git_consistency_checker.py` (~300 LOC)
- `tests/core/services/test_git_consistency_checker.py` (~200 LOC)

---

## Key Methods

```python
class GitAwareConsistencyChecker:
    def check_consistency(self) -> ConsistencyReport:
        """Check file-DB consistency."""
        # Check 1: Uncommitted changes
        # Check 2: Orphaned DB records (file deleted)
        # Check 3: Unregistered files
        # Check 4: State mismatches

    def repair(self, report: ConsistencyReport) -> None:
        """Repair issues (atomic commit)."""
```

---

## Definition of Done

- [ ] 15 tests passing
- [ ] Service ~300 LOC
- [ ] Git commit: "feat(epic-25): implement GitAwareConsistencyChecker"

---

**Created**: 2025-11-09

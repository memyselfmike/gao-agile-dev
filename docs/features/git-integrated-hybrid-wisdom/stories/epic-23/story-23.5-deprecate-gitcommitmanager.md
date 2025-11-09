# Story 23.5: Deprecate GitCommitManager

**Epic**: Epic 23 - GitManager Enhancement
**Story ID**: 23.5
**Priority**: P1
**Estimate**: 4 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Remove GitCommitManager service and migrate its functionality to the enhanced GitManager. GitCommitManager was created for sandbox commit operations but is now redundant with the enhanced GitManager's transaction support methods.

This consolidation eliminates code duplication, reduces maintenance burden, and provides a single source of truth for git operations. All GitCommitManager functionality (atomic commits, commit message formatting) is now available in GitManager with the new transaction support methods from Story 23.1.

This story deletes the GitCommitManager file, updates all references to use GitManager instead, migrates tests, and adds a deprecation notice to the CHANGELOG.

---

## Acceptance Criteria

- [ ] `gao_dev/sandbox/git_commit_manager.py` file deleted (-259 LOC)
- [ ] `gao_dev/sandbox/benchmark/runner.py` updated to use GitManager
- [ ] All GitCommitManager usage replaced with GitManager.commit()
- [ ] All GitCommitManager tests migrated to test_git_manager_enhanced.py
- [ ] No references to GitCommitManager in codebase (search confirms)
- [ ] Deprecation notice added to CHANGELOG.md
- [ ] All existing tests still pass
- [ ] Sandbox benchmark runner still creates proper commits

---

## Technical Approach

### Implementation Details

Replace GitCommitManager with GitManager across the codebase. The primary usage is in the sandbox benchmark runner which creates atomic commits for story completion.

**Migration Strategy**:
1. Identify all GitCommitManager usages (primarily in sandbox/benchmark)
2. Replace with GitManager equivalents
3. Migrate tests to existing test_git_manager_enhanced.py
4. Delete GitCommitManager file
5. Update imports and remove from __all__ exports

**Functionality Mapping**:
- `GitCommitManager.commit_changes()` → `GitManager.add_all()` + `GitManager.commit()`
- `GitCommitManager.create_atomic_commit()` → Same as above
- Commit message formatting → Move to benchmark runner

### Files to Modify

- `gao_dev/sandbox/git_commit_manager.py` (DELETE -259 LOC)
  - Remove entire file

- `gao_dev/sandbox/benchmark/runner.py` (~20 LOC changes)
  - Remove: GitCommitManager import
  - Add: Use GitManager from orchestrator
  - Modify: Replace commit_changes() calls with git.add_all() + git.commit()

- `gao_dev/sandbox/__init__.py` (-1 LOC)
  - Remove: GitCommitManager from __all__

- `tests/sandbox/test_git_commit_manager.py` (DELETE or migrate)
  - Option 1: Delete file (tests covered by test_git_manager_enhanced.py)
  - Option 2: Migrate useful tests to test_git_manager_enhanced.py

- `CHANGELOG.md` (+5 LOC)
  - Add: Deprecation notice under "Deprecated" section

---

## Testing Strategy

### Migration Validation (5 tests)

- test_benchmark_runner_uses_gitmanager() - Verify runner uses GitManager
- test_atomic_commit_still_works() - Verify sandbox commits still atomic
- test_no_gitcommitmanager_references() - Grep codebase for "GitCommitManager"
- test_all_imports_removed() - Verify no import statements reference it
- test_sandbox_benchmark_integration() - E2E test of benchmark with commits

**Total Tests**: 5 validation tests
**Test File**: `tests/sandbox/test_git_manager_integration.py`

---

## Dependencies

**Upstream**: Story 23.1 (GitManager must have transaction support first)

**Downstream**: None (cleanup story)

---

## Implementation Notes

### GitCommitManager Usage Analysis

Current usages (grep results):
```
gao_dev/sandbox/git_commit_manager.py:259 LOC
gao_dev/sandbox/benchmark/runner.py:3 imports, 5 calls
tests/sandbox/test_git_commit_manager.py:12 tests
```

**Benchmark Runner Usage**:
```python
# OLD (GitCommitManager)
from gao_dev.sandbox.git_commit_manager import GitCommitManager
git_commit_mgr = GitCommitManager(sandbox_path)
git_commit_mgr.commit_changes("feat: complete story 5.3")

# NEW (GitManager)
git_manager = orchestrator.git  # or inject GitManager
git_manager.add_all()
git_manager.commit("feat: complete story 5.3")
```

### Migration Steps

1. **Update benchmark runner** (Story 23.5):
   ```python
   # runner.py changes
   - from gao_dev.sandbox.git_commit_manager import GitCommitManager
   + # Use GitManager from orchestrator

   - self.git_commit_mgr = GitCommitManager(self.sandbox_path)
   + # GitManager already available via orchestrator

   - self.git_commit_mgr.commit_changes(message)
   + self.git_manager.add_all()
   + self.git_manager.commit(message)
   ```

2. **Delete files**:
   - Delete `gao_dev/sandbox/git_commit_manager.py`
   - Delete or migrate `tests/sandbox/test_git_commit_manager.py`

3. **Update CHANGELOG.md**:
   ```markdown
   ## [Unreleased]

   ### Deprecated
   - GitCommitManager removed - use GitManager transaction methods instead
   ```

### Validation Checklist

After migration:
- [ ] `git grep "GitCommitManager"` returns 0 results (except CHANGELOG)
- [ ] All tests pass (no test failures)
- [ ] Sandbox benchmarks create commits successfully
- [ ] No import errors when running `pytest`

### Rollback Plan

If issues found:
1. Revert git commit
2. GitCommitManager restored automatically
3. Re-evaluate migration strategy

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] GitCommitManager file deleted
- [ ] All tests passing
- [ ] No references to GitCommitManager in code
- [ ] Code review completed
- [ ] CHANGELOG updated
- [ ] Git commit: "refactor(epic-23): deprecate GitCommitManager, use GitManager instead"
- [ ] MyPy strict mode passes

---

**Created**: 2025-11-09
**Last Updated**: 2025-11-09

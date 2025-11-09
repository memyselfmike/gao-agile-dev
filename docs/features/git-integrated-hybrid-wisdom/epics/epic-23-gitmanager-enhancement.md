# Epic 23: GitManager Enhancement

**Epic ID**: Epic-GHW-23
**Feature**: Git-Integrated Hybrid Wisdom Architecture
**Duration**: Week 2 (5 days)
**Owner**: Amelia (Developer)
**Status**: Planning
**Previous Epic**: Epic 22 (Orchestrator Decomposition)

---

## Epic Goal

Enhance GitManager with transaction support, branch management, and file history methods required for git-integrated hybrid architecture.

**Success Criteria**:
- 10 new methods added to GitManager
- GitCommitManager deprecated and removed
- 30+ unit tests passing
- No breaking changes to existing code
- API documentation complete

---

## User Stories (8 stories)

### Story 1.1: Add Transaction Support Methods
**Priority**: P0 (Critical)
**Estimate**: 6 hours

**Description**:
Add methods for git transaction support: `is_working_tree_clean()`, `add_all()`, `commit()`, `reset_hard()`, `get_head_sha()`.

**Acceptance Criteria**:
- [ ] `is_working_tree_clean()` returns True/False for clean state
- [ ] `add_all()` stages all changes
- [ ] `commit()` creates commit and returns SHA
- [ ] `reset_hard()` rolls back uncommitted changes
- [ ] `get_head_sha()` returns current commit hash
- [ ] All methods have comprehensive docstrings
- [ ] 15 unit tests covering all methods

**Files Modified**:
- `gao_dev/core/git_manager.py` (+~100 LOC)
- `tests/core/test_git_manager_enhanced.py` (new file, ~200 LOC)

---

### Story 1.2: Add Branch Management Methods
**Priority**: P0 (Critical)
**Estimate**: 4 hours

**Description**:
Add enhanced branch management: `create_branch()`, `checkout()`, `delete_branch()`, enhance `merge()`.

**Acceptance Criteria**:
- [ ] `create_branch()` creates and optionally checks out branch
- [ ] `checkout()` switches to existing branch
- [ ] `delete_branch()` deletes with optional force flag
- [ ] `merge()` supports --no-ff and custom messages
- [ ] 10 unit tests covering all scenarios

**Files Modified**:
- `gao_dev/core/git_manager.py` (+~50 LOC)
- `tests/core/test_git_manager_enhanced.py` (+~100 LOC)

---

### Story 1.3: Add File History Query Methods
**Priority**: P0 (Critical)
**Estimate**: 6 hours

**Description**:
Add methods for querying file history: `get_last_commit_for_file()`, `file_deleted_in_history()`, `is_file_tracked()`, `get_file_status()`.

**Acceptance Criteria**:
- [ ] `get_last_commit_for_file()` returns commit info dict
- [ ] `file_deleted_in_history()` detects deleted files
- [ ] `is_file_tracked()` checks if file in git index
- [ ] `get_file_status()` returns status (clean, modified, staged, etc.)
- [ ] 12 unit tests covering all methods

**Files Modified**:
- `gao_dev/core/git_manager.py` (+~80 LOC)
- `tests/core/test_git_manager_enhanced.py` (+~150 LOC)

---

### Story 1.4: Add Query Enhancement Methods
**Priority**: P1 (High)
**Estimate**: 4 hours

**Description**:
Add `get_commit_info()` and `get_commits_since()` for detailed commit queries.

**Acceptance Criteria**:
- [ ] `get_commit_info()` returns comprehensive commit metadata
- [ ] `get_commits_since()` returns list of commits in range
- [ ] Support optional file path filtering
- [ ] 8 unit tests

**Files Modified**:
- `gao_dev/core/git_manager.py` (+~60 LOC)
- `tests/core/test_git_manager_enhanced.py` (+~100 LOC)

---

### Story 1.5: Deprecate GitCommitManager
**Priority**: P1 (High)
**Estimate**: 4 hours

**Description**:
Remove GitCommitManager and migrate functionality to GitManager.

**Acceptance Criteria**:
- [ ] GitCommitManager file deleted
- [ ] Sandbox runner updated to use GitManager
- [ ] All GitCommitManager tests migrated
- [ ] Deprecation notice added to CHANGELOG

**Files Modified**:
- `gao_dev/sandbox/git_commit_manager.py` (DELETE)
- `gao_dev/sandbox/benchmark/runner.py` (refactor)
- `tests/sandbox/test_git_manager.py` (update)

---

### Story 1.6: Integration Tests for Git Operations
**Priority**: P1 (High)
**Estimate**: 5 hours

**Description**:
Create integration tests verifying GitManager works end-to-end.

**Acceptance Criteria**:
- [ ] Test complete workflow: init → commit → branch → merge
- [ ] Test rollback scenarios (reset_hard)
- [ ] Test file history queries on real repo
- [ ] 10 integration tests

**Files Modified**:
- `tests/integration/test_git_manager_integration.py` (new, ~300 LOC)

---

### Story 1.7: API Documentation
**Priority**: P1 (High)
**Estimate**: 3 hours

**Description**:
Create comprehensive API documentation for enhanced GitManager.

**Acceptance Criteria**:
- [ ] All new methods documented with examples
- [ ] Migration guide from GitCommitManager
- [ ] Update CLAUDE.md with GitManager reference
- [ ] Add docstring examples for all new methods

**Files Modified**:
- `gao_dev/core/git_manager.py` (enhanced docstrings)
- `docs/features/git-integrated-hybrid-wisdom/GITMANAGER_API.md` (new)
- `CLAUDE.md` (update git workflow section)

---

### Story 1.8: Performance & Smoke Tests
**Priority**: P2 (Medium)
**Estimate**: 3 hours

**Description**:
Validate GitManager performance and add smoke tests.

**Acceptance Criteria**:
- [ ] Git operations complete in <100ms
- [ ] Smoke tests verify no regressions
- [ ] Test coverage >80% for GitManager
- [ ] pytest-benchmark tests added

**Files Modified**:
- `tests/performance/test_git_performance.py` (new, ~100 LOC)
- `tests/smoke/test_git_smoke.py` (new, ~50 LOC)

---

## Dependencies

**Upstream**: Epic 22 (Orchestrator Decomposition - cleaner architecture)

**Downstream**:
- Epic 24 requires enhanced GitManager for state tracking
- Epic 25 requires all GitManager methods for state manager

---

## Technical Notes

### GitManager Methods Summary

**Transaction Support** (5 methods):
```python
is_working_tree_clean() -> bool
add_all() -> bool
commit(message: str, ...) -> str
reset_hard(target: str = "HEAD") -> bool
get_head_sha(short: bool = True) -> str
```

**Branch Management** (3 methods):
```python
create_branch(name: str, checkout: bool = True) -> bool
checkout(branch: str) -> bool
delete_branch(name: str, force: bool = False) -> bool
```

**File History** (4 methods):
```python
get_last_commit_for_file(path: Path) -> Optional[Dict]
file_deleted_in_history(path: Path) -> bool
is_file_tracked(path: Path) -> bool
get_file_status(path: Path) -> str
```

**Query Enhancements** (2 methods):
```python
get_commit_info(sha: str = "HEAD") -> Dict
get_commits_since(since: str, until: str = "HEAD", ...) -> List[Dict]
```

**Total**: 14 new methods (10 critical, 4 enhancement)

---

## Testing Strategy

**Unit Tests** (~30 tests):
- Transaction methods: 15 tests
- Branch methods: 10 tests
- File history: 12 tests
- Query methods: 8 tests

**Integration Tests** (~10 tests):
- End-to-end workflows
- Rollback scenarios
- Real repository operations

**Total Tests**: ~40 tests
**Target Coverage**: >80%

---

## Risks & Mitigation

**Risk 1: Breaking Changes**
- **Mitigation**: All additions, no signature changes
- **Validation**: Run full test suite after each story

**Risk 2: Windows Compatibility**
- **Mitigation**: Test on Windows, avoid Unix-specific git flags
- **Validation**: Windows CI pipeline

**Risk 3: Git Not Installed**
- **Mitigation**: Already have git availability check
- **Validation**: Error handling tests

---

## Success Metrics

- [ ] 14 new methods implemented
- [ ] 40+ tests passing
- [ ] >80% code coverage for GitManager
- [ ] GitCommitManager fully removed
- [ ] No breaking changes detected
- [ ] Documentation complete

---

**Epic Status**: Ready for Story Implementation
**Next Step**: Amelia implements Story 1.1
**Created**: 2025-11-09

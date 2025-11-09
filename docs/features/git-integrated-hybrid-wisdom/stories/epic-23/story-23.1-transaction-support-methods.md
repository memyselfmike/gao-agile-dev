# Story 23.1: Add Transaction Support Methods

**Epic**: Epic 23 - GitManager Enhancement
**Story ID**: 23.1
**Priority**: P0
**Estimate**: 6 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Add core transaction support methods to GitManager to enable atomic git operations for the hybrid architecture. These methods are CRITICAL for the git transaction model where every state change creates one atomic git commit bundling file and database changes together.

The transaction support methods form the foundation for Epic 25 (Git-Integrated State Manager) which will use these methods to ensure 100% data consistency through atomic commits. Without these methods, the entire git transaction layer cannot function.

This story implements 5 essential methods: `is_working_tree_clean()` for pre-checks, `add_all()` and `commit()` for committing changes, `reset_hard()` for rollback, and `get_head_sha()` for checkpoint tracking.

---

## Acceptance Criteria

- [ ] `is_working_tree_clean()` returns True/False for clean working directory state
- [ ] `add_all()` stages all changes (both tracked and untracked files)
- [ ] `commit()` creates commit with message and returns SHA (7-char short form)
- [ ] `reset_hard()` performs hard reset to rollback uncommitted changes (DESTRUCTIVE)
- [ ] `get_head_sha()` returns current commit hash (short or long form)
- [ ] All methods have comprehensive docstrings with examples
- [ ] Error handling for all git failures
- [ ] Structured logging for all operations
- [ ] 15 unit tests covering all methods and error cases
- [ ] Type hints for all parameters and return values

---

## Technical Approach

### Implementation Details

Add five transaction support methods to the existing GitManager class. These methods wrap git commands and provide clean Python APIs with proper error handling and logging.

**Key Methods**:
1. **is_working_tree_clean()**: Runs `git status --porcelain`, returns True if output is empty
2. **add_all()**: Runs `git add -A` to stage all changes
3. **commit()**: Runs `git commit -m` with message, extracts SHA from output
4. **reset_hard()**: Runs `git reset --hard` to discard uncommitted changes (DANGEROUS)
5. **get_head_sha()**: Runs `git rev-parse HEAD` (or `--short`) to get commit hash

**Design Pattern**: Extension of existing GitManager service

### Files to Modify

- `gao_dev/core/git_manager.py` (+~100 LOC / -0 LOC)
  - Add: `is_working_tree_clean() -> bool` method (~15 LOC)
  - Add: `add_all() -> bool` method (~15 LOC)
  - Add: `commit(message: str, allow_empty: bool = False) -> str` method (~20 LOC)
  - Add: `reset_hard(target: str = "HEAD") -> bool` method (~15 LOC)
  - Add: `get_head_sha(short: bool = True) -> str` method (~15 LOC)
  - Add: Comprehensive docstrings and error handling (~20 LOC)

### New Files to Create

- `tests/core/test_git_manager_enhanced.py` (~200 LOC)
  - Purpose: Unit tests for enhanced GitManager transaction methods
  - Key components:
    - 15 unit tests covering all new methods
    - Mock git subprocess calls
    - Test success and error scenarios
    - Validate return types and values

---

## Testing Strategy

### Unit Tests (15 tests)

- test_is_working_tree_clean_true() - Tests clean working tree detection
- test_is_working_tree_clean_false() - Tests dirty working tree detection (modified files)
- test_is_working_tree_clean_untracked() - Tests dirty working tree with untracked files
- test_add_all_success() - Tests staging all changes
- test_add_all_empty_repo() - Tests add_all on empty repository
- test_commit_success() - Tests successful commit creation
- test_commit_returns_sha() - Validates commit SHA return value
- test_commit_with_allow_empty() - Tests empty commit creation
- test_commit_fails_on_dirty_tree() - Tests commit requires add_all first
- test_reset_hard_success() - Tests hard reset to HEAD
- test_reset_hard_to_specific_sha() - Tests reset to specific commit
- test_reset_hard_warning_logged() - Validates DESTRUCTIVE warning logged
- test_get_head_sha_short() - Tests short SHA retrieval (7 chars)
- test_get_head_sha_long() - Tests long SHA retrieval (40 chars)
- test_transaction_flow_integration() - Tests full flow: add_all → commit → get_sha

**Total Tests**: 15 tests
**Test File**: `tests/core/test_git_manager_enhanced.py`

---

## Dependencies

**Upstream**: Epic 22 (clean architecture establishes clean codebase)

**Downstream**:
- Story 23.2 (branch management builds on transaction support)
- Story 25.1 (GitIntegratedStateManager uses these methods)
- Story 25.2 (transaction support requires these methods)

---

## Implementation Notes

### Critical Safety Considerations

**reset_hard() is DESTRUCTIVE**:
- Discards all uncommitted changes permanently
- Must log LOUD warnings before execution
- Use only in error recovery scenarios
- Consider alternatives (stash) for user-facing operations

**commit() assumes staged changes**:
- Caller must run add_all() first
- Or pass allow_empty=True for empty commits (rare)
- Returns SHA for checkpoint tracking

**is_working_tree_clean() pre-check**:
- ALWAYS call before atomic operations
- Prevents conflicts from uncommitted changes
- GitIntegratedStateManager will use this extensively

### Git Command Details

```python
# is_working_tree_clean() implementation
result = subprocess.run(
    ["git", "status", "--porcelain"],
    cwd=self.repo_path,
    capture_output=True,
    text=True
)
return result.stdout.strip() == ""  # Empty means clean

# commit() implementation
result = subprocess.run(
    ["git", "commit", "-m", message],
    cwd=self.repo_path,
    capture_output=True,
    text=True
)
# Extract SHA from output like "[main abc1234] message"
match = re.search(r'\[.* ([a-f0-9]+)\]', result.stdout)
return match.group(1) if match else ""

# reset_hard() implementation
logger.warning("DESTRUCTIVE: git reset --hard", target=target)
subprocess.run(
    ["git", "reset", "--hard", target],
    cwd=self.repo_path,
    check=True
)
```

### Performance Considerations

All methods complete in <50ms for typical repositories:
- `is_working_tree_clean()`: <10ms
- `add_all()`: <20ms (depends on file count)
- `commit()`: <50ms
- `reset_hard()`: <30ms
- `get_head_sha()`: <10ms

### Error Handling

All methods must handle:
- Git not installed: Raise GitError with helpful message
- Not a git repository: Raise GitError
- Git command failures: Log error, raise GitError
- Subprocess timeouts: Configurable timeout (default 30s)

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (15/15)
- [ ] Code coverage >80% for new methods
- [ ] Code review completed
- [ ] Documentation updated (comprehensive docstrings with examples)
- [ ] No breaking changes (existing tests still pass)
- [ ] Git commit created with message: "feat(epic-23): add transaction support methods to GitManager"
- [ ] MyPy strict mode passes
- [ ] No linting errors (Ruff)

---

**Created**: 2025-11-09
**Last Updated**: 2025-11-09

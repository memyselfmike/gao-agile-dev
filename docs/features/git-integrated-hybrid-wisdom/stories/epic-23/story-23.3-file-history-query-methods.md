# Story 23.3: Add File History Query Methods

**Epic**: Epic 23 - GitManager Enhancement
**Story ID**: 23.3
**Priority**: P0
**Estimate**: 6 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Add file history query methods to GitManager to support migration state inference and consistency checking. These methods enable GitMigrationManager to infer story states from git history and GitAwareConsistencyChecker to detect file-database inconsistencies.

The migration backfill process (Story 25.5) needs to infer story states for existing projects. By querying the last commit for each story file, we can determine if a story is "done" (commit message contains "complete"), "in_progress", or "todo" based on git history and file age.

This story implements 4 file history methods: `get_last_commit_for_file()` returns detailed commit info, `file_deleted_in_history()` detects deleted files, `is_file_tracked()` checks git index, and `get_file_status()` returns file state (clean, modified, staged, untracked).

---

## Acceptance Criteria

- [ ] `get_last_commit_for_file(path)` returns Dict with SHA, message, author, date
- [ ] `file_deleted_in_history(path)` returns True if file was deleted in git history
- [ ] `is_file_tracked(path)` returns True if file is tracked by git (in index)
- [ ] `get_file_status(path)` returns status string (clean, modified, staged, untracked, deleted)
- [ ] All methods handle file not found gracefully (return None or False)
- [ ] Methods work for files in subdirectories (relative to repo root)
- [ ] Comprehensive docstrings with examples
- [ ] Structured logging for queries
- [ ] 12 unit tests covering all methods and edge cases
- [ ] Type hints with proper Optional handling

---

## Technical Approach

### Implementation Details

Add four file history query methods using git log and git status commands. These methods extract historical information about files from git's internal database.

**Key Methods**:
1. **get_last_commit_for_file()**: Runs `git log -1` on file, parses output
2. **file_deleted_in_history()**: Checks `git log --diff-filter=D` for deletions
3. **is_file_tracked()**: Runs `git ls-files` to check if file in index
4. **get_file_status()**: Runs `git status --porcelain` on specific file

**Design Pattern**: Extension of existing GitManager service

### Files to Modify

- `gao_dev/core/git_manager.py` (+~80 LOC / -0 LOC)
  - Add: `get_last_commit_for_file(path: Path) -> Optional[Dict[str, Any]]` (~25 LOC)
  - Add: `file_deleted_in_history(path: Path) -> bool` (~15 LOC)
  - Add: `is_file_tracked(path: Path) -> bool` (~10 LOC)
  - Add: `get_file_status(path: Path) -> str` (~20 LOC)
  - Add: Helper `_parse_commit_info()` (~10 LOC)

### New Files to Create

- `tests/core/test_git_manager_enhanced.py` (+~150 LOC appended)
  - Purpose: Unit tests for file history methods
  - Key components:
    - 12 unit tests for file queries
    - Create test files in temp git repo
    - Test various file states and histories

---

## Testing Strategy

### Unit Tests (12 tests)

- test_get_last_commit_for_file_success() - Tests commit info retrieval for tracked file
- test_get_last_commit_for_file_not_found() - Tests None return for non-existent file
- test_get_last_commit_for_file_untracked() - Tests None return for untracked file
- test_get_last_commit_info_structure() - Validates returned dict structure (sha, message, author, date)
- test_file_deleted_in_history_true() - Tests detection of deleted file
- test_file_deleted_in_history_false() - Tests False for existing file
- test_is_file_tracked_true() - Tests True for tracked file
- test_is_file_tracked_false() - Tests False for untracked file
- test_get_file_status_clean() - Tests "clean" for committed, unchanged file
- test_get_file_status_modified() - Tests "modified" for changed tracked file
- test_get_file_status_staged() - Tests "staged" for added file
- test_get_file_status_untracked() - Tests "untracked" for new file

**Total Tests**: 12 tests
**Test File**: `tests/core/test_git_manager_enhanced.py` (appended)

---

## Dependencies

**Upstream**: Story 23.1 (transaction support), Story 23.2 (branch management)

**Downstream**:
- Story 25.5 (GitMigrationManager uses get_last_commit_for_file to infer state)
- Story 25.6 (GitAwareConsistencyChecker uses get_file_status and is_file_tracked)

---

## Implementation Notes

### Git Command Details

```python
# get_last_commit_for_file() implementation
result = subprocess.run(
    ["git", "log", "-1", "--format=%H|%s|%an|%ai", "--", str(path)],
    cwd=self.repo_path,
    capture_output=True,
    text=True
)
if not result.stdout.strip():
    return None  # File not tracked or no commits
sha, message, author, date = result.stdout.strip().split("|")
return {
    "sha": sha[:7],  # Short SHA
    "message": message,
    "author": author,
    "date": date
}

# file_deleted_in_history() implementation
result = subprocess.run(
    ["git", "log", "--diff-filter=D", "--", str(path)],
    cwd=self.repo_path,
    capture_output=True
)
return bool(result.stdout.strip())  # Non-empty output = deleted

# is_file_tracked() implementation
result = subprocess.run(
    ["git", "ls-files", str(path)],
    cwd=self.repo_path,
    capture_output=True,
    text=True
)
return bool(result.stdout.strip())  # Non-empty = tracked

# get_file_status() implementation
result = subprocess.run(
    ["git", "status", "--porcelain", str(path)],
    cwd=self.repo_path,
    capture_output=True,
    text=True
)
status_code = result.stdout[:2] if result.stdout else "  "
return {
    "  ": "clean",
    " M": "modified",
    "M ": "staged",
    "A ": "staged",
    "??": "untracked",
    " D": "deleted"
}.get(status_code, "unknown")
```

### Use Cases

**Migration State Inference** (Story 25.5):
```python
commit_info = git.get_last_commit_for_file(Path("docs/stories/epic-5/story-5.3.md"))
if commit_info and "complete" in commit_info["message"].lower():
    state = "done"
elif commit_info and "progress" in commit_info["message"].lower():
    state = "in_progress"
else:
    state = "todo"
```

**Consistency Checking** (Story 25.6):
```python
# Detect unregistered files
for file in docs_files:
    if git.is_file_tracked(file):
        if not registry.get_by_path(file):
            report.add_issue(f"Unregistered tracked file: {file}")

# Detect orphaned DB records
for doc in registry.get_all_documents():
    status = git.get_file_status(doc.path)
    if status == "deleted":
        report.add_issue(f"Orphaned DB record for deleted file: {doc.path}")
```

### Performance Considerations

File history queries are I/O bound:
- `get_last_commit_for_file()`: 10-50ms per file
- `is_file_tracked()`: 5-10ms per file
- Batch operations should be avoided (run in parallel if needed)
- Cache results if querying same file multiple times

### Error Handling

All methods must handle:
- File not found: Return None or False (not an error)
- Path outside repo: Raise GitError
- Git command failures: Log warning, return safe default
- Invalid path format: Raise ValueError

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (12/12)
- [ ] Code coverage >80% for new methods
- [ ] Code review completed
- [ ] Documentation updated (comprehensive docstrings with examples)
- [ ] No breaking changes (all existing tests pass)
- [ ] Git commit created with message: "feat(epic-23): add file history query methods to GitManager"
- [ ] MyPy strict mode passes
- [ ] No linting errors (Ruff)

---

**Created**: 2025-11-09
**Last Updated**: 2025-11-09

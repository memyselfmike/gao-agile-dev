# Story 23.4: Add Query Enhancement Methods

**Epic**: Epic 23 - GitManager Enhancement
**Story ID**: 23.4
**Priority**: P1
**Estimate**: 4 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Add enhanced commit query methods to GitManager for detailed commit information retrieval and commit range queries. These methods support ceremony summaries and learning extraction by providing access to commit history and metadata.

The CeremonyOrchestrator (Epic 26) needs to link ceremony outcomes to commits, and the migration system needs to query commit ranges during validation. These methods provide rich commit metadata beyond basic git operations.

This story implements 2 query enhancement methods: `get_commit_info()` for detailed single-commit metadata, and `get_commits_since()` for retrieving commit ranges with optional file filtering.

---

## Acceptance Criteria

- [ ] `get_commit_info(sha="HEAD")` returns comprehensive Dict with SHA, message, author, email, date, files_changed
- [ ] `get_commits_since(since, until="HEAD")` returns List of commit Dicts in range
- [ ] Optional file path filtering for `get_commits_since()` (commits affecting specific file)
- [ ] Both methods parse git output into structured Python dicts
- [ ] Methods handle invalid SHAs gracefully (raise GitError with clear message)
- [ ] Comprehensive docstrings with usage examples
- [ ] Structured logging for queries
- [ ] 8 unit tests covering all parameters and edge cases
- [ ] Type hints with proper List and Dict typing

---

## Technical Approach

### Implementation Details

Add two query enhancement methods using git log and git show commands. Parse raw git output into structured Python dicts for easy consumption.

**Key Methods**:
1. **get_commit_info()**: Runs `git show` with format options, parses into Dict
2. **get_commits_since()**: Runs `git log` with range, optionally filters by file

**Return Structure**:
```python
{
    "sha": "abc1234",  # Short SHA
    "full_sha": "abc123456789...",  # Full SHA
    "message": "feat: commit message",
    "author": "John Doe",
    "email": "john@example.com",
    "date": "2025-11-09T10:30:00-08:00",
    "files_changed": ["file1.py", "file2.md"]  # Only in get_commit_info
}
```

### Files to Modify

- `gao_dev/core/git_manager.py` (+~60 LOC / -0 LOC)
  - Add: `get_commit_info(sha: str = "HEAD") -> Dict[str, Any]` (~25 LOC)
  - Add: `get_commits_since(since: str, until: str = "HEAD", file_path: Optional[Path] = None) -> List[Dict[str, Any]]` (~25 LOC)
  - Add: Helper `_parse_commit_log()` (~10 LOC)

### New Files to Create

- `tests/core/test_git_manager_enhanced.py` (+~100 LOC appended)
  - Purpose: Unit tests for query enhancement methods
  - Key components:
    - 8 unit tests for commit queries
    - Test with real git commits in temp repo
    - Validate data structure and filtering

---

## Testing Strategy

### Unit Tests (8 tests)

- test_get_commit_info_head() - Tests retrieving HEAD commit info
- test_get_commit_info_specific_sha() - Tests retrieving specific commit by SHA
- test_get_commit_info_invalid_sha() - Tests error handling for invalid SHA
- test_get_commit_info_structure() - Validates returned dict has all required keys
- test_get_commits_since_date() - Tests commit range query by date
- test_get_commits_since_sha() - Tests commit range query by SHA
- test_get_commits_since_with_file_filter() - Tests filtering commits by file path
- test_get_commits_since_empty_range() - Tests empty result for no commits in range

**Total Tests**: 8 tests
**Test File**: `tests/core/test_git_manager_enhanced.py` (appended)

---

## Dependencies

**Upstream**: Story 23.3 (file history methods establish pattern)

**Downstream**:
- Story 26.6 (ceremony artifact integration links commits to ceremonies)
- Story 25.5 (migration validation queries commit ranges)

---

## Implementation Notes

### Git Command Details

```python
# get_commit_info() implementation
result = subprocess.run(
    ["git", "show", "--format=%H|%h|%s|%an|%ae|%ai", "--name-only", sha],
    cwd=self.repo_path,
    capture_output=True,
    text=True
)
lines = result.stdout.strip().split("\n")
full_sha, short_sha, message, author, email, date = lines[0].split("|")
files = [line for line in lines[2:] if line.strip()]  # Skip blank line
return {
    "sha": short_sha,
    "full_sha": full_sha,
    "message": message,
    "author": author,
    "email": email,
    "date": date,
    "files_changed": files
}

# get_commits_since() implementation
cmd = ["git", "log", f"{since}..{until}", "--format=%H|%h|%s|%an|%ae|%ai"]
if file_path:
    cmd.extend(["--", str(file_path)])
result = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True)
commits = []
for line in result.stdout.strip().split("\n"):
    if line:
        full_sha, short_sha, message, author, email, date = line.split("|")
        commits.append({
            "sha": short_sha,
            "full_sha": full_sha,
            "message": message,
            "author": author,
            "email": email,
            "date": date
        })
return commits
```

### Use Cases

**Ceremony Linking** (Epic 26):
```python
commit_info = git.get_commit_info("HEAD")
ceremony_summary = {
    "ceremony_type": "standup",
    "date": datetime.now(),
    "commit_sha": commit_info["sha"],
    "commit_message": commit_info["message"]
}
```

**Migration Validation** (Story 25.5):
```python
# Validate all migration commits present
migration_commits = git.get_commits_since("migration-start-sha", "HEAD")
assert len(migration_commits) == 4  # 4 migration phases
assert "phase 1" in migration_commits[0]["message"]
```

### Performance Considerations

- `get_commit_info()`: 20-50ms per commit
- `get_commits_since()`: 50-200ms depending on range size
- Limit commit range queries to <100 commits for performance
- Consider pagination for large ranges (future enhancement)

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (8/8)
- [ ] Code coverage >80%
- [ ] Code review completed
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] Git commit: "feat(epic-23): add query enhancement methods to GitManager"
- [ ] MyPy strict mode passes

---

**Created**: 2025-11-09
**Last Updated**: 2025-11-09

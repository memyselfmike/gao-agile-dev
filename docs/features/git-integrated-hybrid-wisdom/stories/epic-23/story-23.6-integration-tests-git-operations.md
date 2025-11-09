# Story 23.6: Integration Tests for Git Operations

**Epic**: Epic 23 - GitManager Enhancement
**Story ID**: 23.6
**Priority**: P1
**Estimate**: 5 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Create comprehensive integration tests verifying GitManager enhanced methods work correctly in realistic end-to-end scenarios with actual git repositories.

While Stories 23.1-23.4 provide unit tests with mocked git commands, integration tests validate the methods work with real git operations. These tests create temporary git repositories, perform real commits/branches/resets, and verify correct behavior.

Integration tests catch issues that unit tests miss: subprocess failures, git version incompatibilities, edge cases in git output parsing, and cross-platform git command differences (Windows vs Unix).

---

## Acceptance Criteria

- [ ] Test complete workflow: init → add → commit → branch → merge
- [ ] Test transaction rollback scenarios (reset_hard after failed operations)
- [ ] Test file history queries on real repository with actual commits
- [ ] Test branch operations (create, checkout, delete, merge)
- [ ] All tests use real git commands (no mocks)
- [ ] Tests create temporary git repos (cleanup after each test)
- [ ] 10 integration tests covering critical workflows
- [ ] Tests pass on Windows and Unix
- [ ] Tests complete in <5 seconds total

---

## Technical Approach

### Implementation Details

Create integration test suite using pytest fixtures for temporary git repositories. Each test creates a fresh git repo, performs operations, and validates results.

**Test Categories**:
1. **Transaction workflows**: add_all → commit → get_sha → reset_hard
2. **Branch workflows**: create_branch → checkout → commit → merge
3. **File history workflows**: commit file → query history → verify data
4. **Rollback scenarios**: start transaction → error → rollback → verify clean

**Fixtures**:
- `temp_git_repo`: Creates temporary git repo, cleans up after test
- `git_manager`: Returns GitManager instance for temp repo
- `commit_test_file`: Helper to create and commit test files

### New Files to Create

- `tests/integration/test_git_manager_integration.py` (~300 LOC)
  - Purpose: Integration tests for GitManager enhanced methods
  - Key components:
    - 10 integration tests
    - Pytest fixtures for temporary git repos
    - Real git operations (no mocks)
    - Validation of complete workflows

---

## Testing Strategy

### Integration Tests (10 tests)

- test_transaction_workflow_complete() - Tests add_all → commit → get_sha flow
- test_atomic_commit_rollback() - Tests rollback on commit failure
- test_branch_create_checkout_merge() - Tests complete branch workflow
- test_branch_delete_after_merge() - Tests branch cleanup
- test_file_history_after_commits() - Tests get_last_commit_for_file with real commits
- test_file_status_changes() - Tests get_file_status through modify/stage/commit cycle
- test_multiple_commits_query() - Tests get_commits_since with commit range
- test_reset_hard_undoes_changes() - Tests reset_hard rollback
- test_dirty_tree_detection() - Tests is_working_tree_clean with various states
- test_cross_method_integration() - Tests using multiple methods together

**Total Tests**: 10 integration tests
**Test File**: `tests/integration/test_git_manager_integration.py`

---

## Dependencies

**Upstream**: Stories 23.1-23.4 (all methods must be implemented first)

**Downstream**: Story 23.8 (performance tests build on integration tests)

---

## Implementation Notes

### Pytest Fixture Setup

```python
import pytest
import tempfile
from pathlib import Path
from gao_dev.core.git_manager import GitManager

@pytest.fixture
def temp_git_repo():
    """Create temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        subprocess.run(["git", "init"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)
        yield repo_path
        # Cleanup automatic

@pytest.fixture
def git_manager(temp_git_repo):
    """GitManager instance for temporary repo."""
    return GitManager(temp_git_repo)

@pytest.fixture
def commit_test_file(temp_git_repo, git_manager):
    """Helper to create and commit a test file."""
    def _commit(filename, content, message):
        file_path = temp_git_repo / filename
        file_path.write_text(content)
        git_manager.add_all()
        return git_manager.commit(message)
    return _commit
```

### Example Integration Test

```python
def test_transaction_workflow_complete(git_manager, temp_git_repo):
    """Test complete transaction workflow: add → commit → get SHA."""
    # Create test file
    test_file = temp_git_repo / "test.txt"
    test_file.write_text("Hello World")

    # Verify dirty tree
    assert not git_manager.is_working_tree_clean()

    # Stage changes
    assert git_manager.add_all()

    # Commit changes
    sha = git_manager.commit("test: add test file")
    assert sha
    assert len(sha) == 7  # Short SHA

    # Verify clean tree
    assert git_manager.is_working_tree_clean()

    # Verify SHA matches HEAD
    head_sha = git_manager.get_head_sha()
    assert sha == head_sha

    # Verify commit info
    commit_info = git_manager.get_commit_info()
    assert commit_info["sha"] == sha
    assert commit_info["message"] == "test: add test file"
```

### Cross-Platform Considerations

Tests must work on both Windows and Unix:
- Use `Path` for file paths (handles / vs \)
- Avoid Unix-specific git flags
- Test on both platforms in CI
- Handle line ending differences (CRLF vs LF)

### Performance Requirements

Integration tests should be fast:
- Each test <500ms
- Total suite <5 seconds
- Use small files (< 1KB)
- Minimize git operations per test

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All 10 integration tests passing
- [ ] Tests pass on Windows and Unix
- [ ] Tests complete in <5 seconds
- [ ] Code review completed
- [ ] Git commit: "test(epic-23): add integration tests for GitManager operations"
- [ ] MyPy strict mode passes

---

**Created**: 2025-11-09
**Last Updated**: 2025-11-09

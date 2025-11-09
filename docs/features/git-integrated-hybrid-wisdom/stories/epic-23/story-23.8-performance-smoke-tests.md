# Story 23.8: Performance and Smoke Tests

**Epic**: Epic 23 - GitManager Enhancement
**Story ID**: 23.8
**Priority**: P2
**Estimate**: 3 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Add performance benchmarks and smoke tests to validate GitManager enhanced methods meet performance targets and don't introduce regressions.

Performance is critical for Epic 25 where git operations occur frequently (every state change creates a commit). Git operations must complete in <100ms to maintain responsive user experience. Smoke tests ensure no regressions in existing functionality.

This story creates pytest-benchmark tests for all new methods, validates <100ms performance targets, and adds smoke tests verifying core git functionality works across the codebase.

---

## Acceptance Criteria

- [ ] Git operations complete in <100ms (individual methods)
- [ ] Transaction workflow (add_all → commit) completes in <100ms total
- [ ] pytest-benchmark tests created for performance validation
- [ ] Smoke tests verify no regressions in existing git operations
- [ ] Test coverage for GitManager >80%
- [ ] Performance benchmarks run in CI (optional: fail if targets missed)
- [ ] Smoke tests cover all existing GitManager methods (clone, init, etc.)

---

## Technical Approach

### Implementation Details

Create two test suites:
1. **Performance Benchmarks**: pytest-benchmark tests measuring method execution time
2. **Smoke Tests**: Quick validation tests ensuring existing functionality works

**Performance Targets**:
- `is_working_tree_clean()`: <10ms
- `add_all()`: <20ms (small repos)
- `commit()`: <50ms
- `reset_hard()`: <30ms
- `get_head_sha()`: <10ms
- `create_branch()`: <15ms
- `checkout()`: <20ms
- `get_last_commit_for_file()`: <30ms
- Full transaction (add → commit): <100ms

**Benchmark Tool**: pytest-benchmark plugin

### New Files to Create

- `tests/performance/test_git_performance.py` (~100 LOC)
  - Purpose: Performance benchmarks for GitManager methods
  - Key components:
    - pytest-benchmark tests for all new methods
    - Validate <100ms targets
    - Run on small test repositories

- `tests/smoke/test_git_smoke.py` (~50 LOC)
  - Purpose: Smoke tests for GitManager
  - Key components:
    - Quick validation of core git operations
    - Verify existing methods still work
    - Detect regressions

---

## Testing Strategy

### Performance Benchmarks (8 benchmarks)

- benchmark_is_working_tree_clean() - Target: <10ms
- benchmark_add_all() - Target: <20ms
- benchmark_commit() - Target: <50ms
- benchmark_reset_hard() - Target: <30ms
- benchmark_get_head_sha() - Target: <10ms
- benchmark_create_branch() - Target: <15ms
- benchmark_get_last_commit_for_file() - Target: <30ms
- benchmark_full_transaction() - Target: <100ms (add_all + commit)

### Smoke Tests (5 tests)

- test_git_clone_still_works() - Verify existing clone() method works
- test_git_init_still_works() - Verify existing init() method works
- test_git_status_still_works() - Verify existing status() method works
- test_enhanced_methods_available() - Verify all 14 new methods exist
- test_no_breaking_changes() - Verify existing method signatures unchanged

**Total**: 8 benchmarks + 5 smoke tests

---

## Dependencies

**Upstream**: Stories 23.1-23.6 (all methods must be implemented and tested)

**Downstream**: Epic 25 (performance validation ensures fast enough for production)

---

## Implementation Notes

### pytest-benchmark Setup

```python
import pytest
from pathlib import Path
from gao_dev.core.git_manager import GitManager

@pytest.fixture
def git_manager_with_repo(tmp_path):
    """GitManager with initialized temp repository."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    git = GitManager(repo_path)
    git.init()
    # Create initial commit for history
    (repo_path / "README.md").write_text("# Test")
    git.add_all()
    git.commit("Initial commit")
    return git

def test_benchmark_is_working_tree_clean(benchmark, git_manager_with_repo):
    """Benchmark is_working_tree_clean() - target <10ms."""
    result = benchmark(git_manager_with_repo.is_working_tree_clean)
    assert result is True
    assert benchmark.stats['mean'] < 0.010  # 10ms

def test_benchmark_full_transaction(benchmark, git_manager_with_repo, tmp_path):
    """Benchmark full transaction workflow - target <100ms."""
    def transaction():
        # Create file
        (tmp_path / "test_repo" / "test.txt").write_text("test")
        # Add and commit
        git_manager_with_repo.add_all()
        return git_manager_with_repo.commit("test: benchmark")

    sha = benchmark(transaction)
    assert sha
    assert benchmark.stats['mean'] < 0.100  # 100ms
```

### Smoke Test Examples

```python
def test_enhanced_methods_available():
    """Verify all 14 new methods exist on GitManager."""
    git = GitManager(Path("."))

    # Transaction support
    assert hasattr(git, 'is_working_tree_clean')
    assert hasattr(git, 'add_all')
    assert hasattr(git, 'commit')
    assert hasattr(git, 'reset_hard')
    assert hasattr(git, 'get_head_sha')

    # Branch management
    assert hasattr(git, 'create_branch')
    assert hasattr(git, 'checkout')
    assert hasattr(git, 'delete_branch')

    # File history
    assert hasattr(git, 'get_last_commit_for_file')
    assert hasattr(git, 'file_deleted_in_history')
    assert hasattr(git, 'is_file_tracked')
    assert hasattr(git, 'get_file_status')

    # Query enhancements
    assert hasattr(git, 'get_commit_info')
    assert hasattr(git, 'get_commits_since')

def test_no_breaking_changes():
    """Verify existing method signatures unchanged."""
    git = GitManager(Path("."))

    # Existing methods still work with same signatures
    assert callable(git.init)
    assert callable(git.clone)
    assert callable(git.get_current_branch)
    # Verify merge() signature (enhanced but backward compatible)
    import inspect
    sig = inspect.signature(git.merge)
    assert 'branch' in sig.parameters
    # New parameters have defaults (backward compatible)
    assert sig.parameters.get('no_ff', None)
    assert sig.parameters.get('message', None)
```

### Coverage Validation

Use pytest-cov to ensure >80% coverage:

```bash
pytest tests/core/test_git_manager_enhanced.py \
       tests/integration/test_git_manager_integration.py \
       tests/performance/test_git_performance.py \
       --cov=gao_dev.core.git_manager \
       --cov-report=term-missing

# Expected output:
# gao_dev/core/git_manager.py    85%    (target: >80%)
```

### CI Integration

Add performance benchmarks to CI pipeline:

```yaml
# .github/workflows/tests.yml
- name: Run performance benchmarks
  run: |
    pytest tests/performance/ --benchmark-only
    # Optional: Fail if targets missed
    pytest tests/performance/ --benchmark-only --benchmark-max-time=0.1
```

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All benchmarks passing (targets met)
- [ ] All smoke tests passing
- [ ] Test coverage >80% for GitManager
- [ ] CI includes performance tests
- [ ] Code review completed
- [ ] Git commit: "test(epic-23): add performance benchmarks and smoke tests for GitManager"

---

**Created**: 2025-11-09
**Last Updated**: 2025-11-09

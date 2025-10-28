# Story 7.1.4: Create Integration Test Suite

**Epic**: 7.1 - Integration & Architecture Fix
**Story Points**: 2
**Priority**: P1
**Status**: Ready
**Owner**: Amelia (Developer)

## User Story

As a developer
I want integration tests for benchmark workflows
So that future changes don't break end-to-end functionality

## Goal

Create test suite to catch integration bugs before production.

## Acceptance Criteria

- [ ] Create `tests/integration/test_benchmark_workflows.py`
- [ ] Test phase-based workflow (mocked)
- [ ] Test story-based workflow (mocked)
- [ ] Test artifact creation
- [ ] Test git commit creation
- [ ] Tests run in under 5 minutes
- [ ] Tests pass on CI (if exists)

## Test Cases

```python
def test_phase_based_workflow():
    """Test phase execution creates artifacts and commits."""

def test_story_based_workflow():
    """Test story execution with QA validation."""

def test_artifact_parser():
    """Test artifact extraction from agent output."""

def test_git_commit_manager():
    """Test atomic commits per story/phase."""
```

## Definition of Done

- [ ] Tests written and passing
- [ ] Coverage > 80% for critical paths
- [ ] Documented in README
- [ ] Story updated to Done

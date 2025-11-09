# Story 29.7: Testing & Validation

**Epic**: Epic 29 - Self-Learning Feedback Loop
**Status**: Not Started
**Priority**: P0 (Critical)
**Estimated Effort**: 8 story points (revised from 3 - C12 fix complexity)
**Owner**: Murat (Test Architect)
**Created**: 2025-11-09
**Dependencies**: Stories 29.1-29.6 (all previous stories)

---

## User Story

**As a** test architect
**I want** comprehensive tests for the self-learning loop with multi-project infrastructure
**So that** I can trust the system makes correct decisions

---

## Acceptance Criteria

### AC1: Multi-Project Test Infrastructure (C12 Fix - CRITICAL)

- [ ] Create reusable test fixtures for multi-project scenarios
- [ ] Shared fixtures in `tests/fixtures/multi_project.py` (~200 lines):
  ```python
  @pytest.fixture
  def multi_project_setup(tmp_path):
      """
      Setup multiple isolated test projects.

      Returns:
          Dict with project paths, databases, orchestrators
      """
      projects = {}
      for i in range(1, 4):  # 3 test projects
          project_root = tmp_path / f"project_{i}"
          project_root.mkdir()

          # Initialize .gao-dev
          gao_dev_dir = project_root / ".gao-dev"
          gao_dev_dir.mkdir()

          # Create isolated database
          db_path = gao_dev_dir / "documents.db"
          init_database(db_path)

          # Create orchestrator
          orchestrator = GAODevOrchestrator.create_default(project_root)

          projects[f"project_{i}"] = {
              "root": project_root,
              "db": db_path,
              "orchestrator": orchestrator
          }

      yield projects

      # Cleanup
      for project in projects.values():
          cleanup_project(project["root"])
  ```
- [ ] Deterministic test data (no random values)
- [ ] Cleanup between tests (pytest fixtures)
- [ ] Project isolation (separate .gao-dev directories)

### AC2: Unit Tests (70+ tests total)

- [ ] **LearningApplicationService** (~25 tests):
  - Scoring algorithm (additive formula, C2 fix)
  - Context similarity (asymmetric tags, C11 fix)
  - Decay calculation (smooth curve)
  - Confidence updates (monotonic growth)
  - Application recording
  - Performance targets (<50ms scoring, <100ms recording)
- [ ] **Brian Context Augmentation** (~15 tests):
  - Context building with 0-5 learnings
  - Template rendering
  - Performance (<500ms, C5 fix)
  - Cache hit/miss
  - Fallback on errors
- [ ] **Workflow Adjuster** (~20 tests):
  - Quality/Process/Architectural adjustments
  - Cycle detection (C7 fix - various scenarios)
  - Adjustment limits (C1 fix - max 3 workflows, max 3 adjustments)
  - Validation failures
  - Rollback on error
- [ ] **Action Item Integration** (~10 tests):
  - CRITICAL priority auto-convert (C8 fix)
  - Max 1 conversion per epic (C8 fix)
  - HIGH/MEDIUM/LOW don't convert
  - Stale item cleanup

### AC3: Integration Tests (30+ tests)

- [ ] **Self-Learning Across Projects** (~15 tests):
  - Project 1: Quality issue → Retrospective → Learning indexed
  - Project 2: Brian retrieves learning → Adjusts workflows
  - Project 3: Learning applied → Success recorded → Confidence updated
  - Verify: Learning confidence increases with successes
  - Verify: Failed applications decrease confidence
- [ ] **Workflow Adjustment Pipeline** (~10 tests):
  - Base workflows selected
  - Learnings retrieved
  - Workflows adjusted
  - Dependency validation (C7 fix)
  - Adjusted workflows execute correctly
- [ ] **Action Item Flow** (~5 tests):
  - Ceremony creates action items
  - CRITICAL item converts to story
  - Story appears in next sprint
  - Story completion recorded

### AC4: End-to-End Tests (5+ tests) (C12 Fix)

- [ ] **E2E Test 1: Small Feature with Learning**:
  ```python
  def test_e2e_level2_feature_with_learning(multi_project_setup):
      """
      Test Level 2 feature with self-learning across 2 projects.

      Flow:
      1. Project 1: Build feature, quality gate fails
      2. Retrospective extracts learning: "Add code review"
      3. Project 2: Build similar feature
      4. Brian retrieves learning, adds code-review workflow
      5. Project 2 succeeds with better quality
      6. Learning confidence increases
      """
      project1 = multi_project_setup["project_1"]
      project2 = multi_project_setup["project_2"]

      # Project 1: Quality issue
      result1 = project1["orchestrator"].execute_workflow(
          user_prompt="Build authentication feature",
          scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE
      )
      assert result1.quality_gate_passed == False

      # Retrospective
      retro = project1["orchestrator"].hold_retrospective(epic_num=1)
      learnings = extract_learnings(retro.transcript)
      assert len(learnings) > 0

      # Project 2: Similar feature
      result2 = project2["orchestrator"].execute_workflow(
          user_prompt="Build authorization feature",
          scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE
      )

      # Verify learning applied
      workflows = result2.workflows
      assert any(wf.workflow_name == "code-review" for wf in workflows)

      # Verify success
      assert result2.quality_gate_passed == True

      # Verify confidence increased
      learning = get_learning_by_content(learnings[0].content)
      assert learning.confidence_score > 0.5
  ```

- [ ] **E2E Test 2: Workflow Cycle Prevention**:
  - Attempt to create circular dependency
  - Verify cycle detection (C7 fix)
  - Verify fallback to original workflows

- [ ] **E2E Test 3: Ceremony Limits**:
  - Execute workflows for large project
  - Verify max 10 ceremonies per epic (C1 fix)
  - Verify cooldown periods enforced

- [ ] **E2E Test 4: Action Item Limits**:
  - Generate multiple CRITICAL action items
  - Verify only 1 converts per epic (C8 fix)
  - Verify others marked for manual review

- [ ] **E2E Test 5: Learning Decay Over Time**:
  - Create learning, age it (mock time)
  - Run maintenance job
  - Verify decay factor updated
  - Verify stale learnings deactivated

### AC5: Mock Time-Based Triggers (C12 Fix)

- [ ] Mock datetime for deterministic testing:
  ```python
  from unittest.mock import patch
  from datetime import datetime, timedelta

  @pytest.fixture
  def mock_time():
      """Mock time for deterministic tests."""
      base_time = datetime(2025, 11, 9, 12, 0, 0)

      with patch('datetime.datetime') as mock_dt:
          mock_dt.now.return_value = base_time
          mock_dt.fromisoformat = datetime.fromisoformat
          yield mock_dt

  def test_decay_with_mock_time(mock_time):
      """Test decay calculation with mocked time."""
      # Index learning at base_time
      learning = index_learning(content="Test", indexed_at=mock_time.now())

      # Fast-forward 30 days
      mock_time.now.return_value = mock_time.now() + timedelta(days=30)

      # Calculate decay
      decay = calculate_decay(learning.indexed_at)
      assert 0.91 <= decay <= 0.93  # Expected ~0.92
  ```
- [ ] Prevents flaky tests due to real time
- [ ] Enables testing future scenarios

### AC6: Performance Benchmarks

- [ ] Benchmark tests for critical paths:
  ```python
  def test_benchmark_learning_scoring(benchmark):
      """Benchmark learning relevance scoring."""
      learnings = [create_learning() for _ in range(50)]

      def score_all():
          return learning_service.get_relevant_learnings(
              scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
              project_type="greenfield",
              context={"tags": ["api", "auth"]},
              limit=5
          )

      result = benchmark(score_all)

      # Should complete in <50ms
      assert result.stats.mean < 0.05
  ```
- [ ] Targets:
  - Learning scoring: <50ms
  - Context building: <500ms (C5 fix)
  - Cycle detection: <10ms
  - Action item conversion: <200ms

### AC7: Test Documentation

- [ ] Create `tests/README.md` documenting:
  - Test structure and organization
  - How to run different test suites
  - Multi-project fixture usage
  - Mock time patterns
  - Performance benchmarking
  - C12 fix: Multi-project test patterns
- [ ] Document common patterns and pitfalls

### AC8: CI/CD Integration

- [ ] Update GitHub Actions workflow:
  ```yaml
  # .github/workflows/test.yml
  test-self-learning:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-benchmark pytest-cov
      - name: Run Epic 29 tests
        run: |
          pytest tests/core/services/test_learning_*.py -v --cov
          pytest tests/orchestrator/test_brian_*.py -v --cov
          pytest tests/methodologies/test_workflow_adjuster.py -v --cov
          pytest tests/e2e/test_self_learning_*.py -v
      - name: Coverage report
        run: pytest --cov=gao_dev --cov-report=html --cov-report=term
      - name: Upload coverage
        uses: codecov/codecov-action@v3
  ```
- [ ] Enforce coverage thresholds (>95% for Epic 29 code)

---

## Technical Details

### Test Organization

```
tests/
├── fixtures/
│   ├── multi_project.py           # C12 Fix: Multi-project fixtures (NEW)
│   ├── mock_time.py               # C12 Fix: Time mocking (NEW)
│   └── learning_factories.py      # Learning test data factories
│
├── core/services/
│   ├── test_learning_application_service.py  (~300 lines)
│   ├── test_action_item_integration_service.py  (~250 lines)
│   └── test_learning_maintenance_job.py  (~200 lines)
│
├── orchestrator/
│   └── test_brian_context_augmentation.py  (~250 lines)
│
├── methodologies/adaptive_agile/
│   └── test_workflow_adjuster.py  (~400 lines)
│
└── e2e/
    ├── test_self_learning_across_projects.py  (~400 lines, C12 Fix)
    ├── test_workflow_cycle_prevention.py  (~200 lines, C7 Fix)
    ├── test_ceremony_limits.py  (~200 lines, C1 Fix)
    ├── test_action_item_limits.py  (~150 lines, C8 Fix)
    └── test_learning_decay_over_time.py  (~150 lines, C10 Fix)
```

### Multi-Project Test Pattern (C12 Fix)

```python
# tests/fixtures/multi_project.py

@pytest.fixture
def isolated_projects(tmp_path):
    """
    Create multiple isolated test projects.

    Each project has:
    - Separate .gao-dev directory
    - Separate database
    - Separate git repo
    - Separate orchestrator instance

    This prevents cross-contamination in tests.
    """
    projects = []

    for i in range(3):
        # Create project root
        project_root = tmp_path / f"project_{i}"
        project_root.mkdir()

        # Initialize .gao-dev
        gao_dev_dir = project_root / ".gao-dev"
        gao_dev_dir.mkdir()

        # Create database with migrations
        db_path = gao_dev_dir / "documents.db"
        run_migrations(db_path)

        # Initialize git repo
        init_git_repo(project_root)

        # Create orchestrator
        orchestrator = GAODevOrchestrator.create_default(project_root)

        projects.append({
            "id": i,
            "root": project_root,
            "db": db_path,
            "orchestrator": orchestrator
        })

    yield projects

    # Cleanup
    for project in projects:
        cleanup_project(project["root"])


# Usage in tests
def test_learning_across_projects(isolated_projects):
    """Test learning flows from project 1 to project 2."""
    p1 = isolated_projects[0]
    p2 = isolated_projects[1]

    # Project 1: Create learning
    learning = index_learning_in_project(p1, content="Use code review")

    # Project 2: Retrieve learning
    learnings = get_learnings_in_project(p2, category="quality")

    # Should retrieve learning from P1 (shared learning database)
    # OR isolated (depending on design decision)
    assert learning in learnings
```

### Deterministic Learning Ordering (C12 Fix)

```python
# Prevent flaky tests from non-deterministic ordering

def test_learning_retrieval_deterministic():
    """Test learnings retrieved in deterministic order."""
    # Create learnings with explicit scores
    learnings = [
        create_learning(id=1, relevance_score=0.9),
        create_learning(id=2, relevance_score=0.8),
        create_learning(id=3, relevance_score=0.7),
    ]

    # Retrieve top 2
    top = get_relevant_learnings(limit=2)

    # Should always return same order (by score DESC)
    assert [l.id for l in top] == [1, 2]
```

---

## Testing Strategy

### Test Coverage Goals

- **Unit Tests**: >95% coverage for Epic 29 code
- **Integration Tests**: >90% coverage for integration paths
- **E2E Tests**: 100% coverage for user-facing scenarios
- **Overall**: >95% coverage for Epic 29 feature

### Test Execution

```bash
# Run all Epic 29 tests
pytest tests/core/services/test_learning_*.py \
       tests/orchestrator/test_brian_*.py \
       tests/methodologies/test_workflow_adjuster.py \
       tests/e2e/test_self_learning_*.py \
       -v --cov=gao_dev --cov-report=html

# Run only E2E tests
pytest tests/e2e/test_self_learning_*.py -v

# Run performance benchmarks
pytest tests/ --benchmark-only

# Run with coverage
pytest --cov=gao_dev --cov-report=term --cov-fail-under=95
```

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] C12 fix applied: Multi-project test infrastructure created
- [ ] 70+ unit tests passing
- [ ] 30+ integration tests passing
- [ ] 5+ E2E tests passing
- [ ] Mock time patterns implemented
- [ ] Performance benchmarks passing
- [ ] Test coverage >95% for Epic 29 code
- [ ] Test documentation complete
- [ ] CI/CD integration working
- [ ] All critical fixes validated (C1, C2, C5, C7, C8, C10, C11, C12)
- [ ] No flaky tests
- [ ] Code reviewed and approved
- [ ] Changes committed with clear message
- [ ] Story marked complete in sprint-status.yaml

---

## Dependencies

**Upstream**: Stories 29.1-29.6 (all must be complete before testing)

**External**:
- pytest
- pytest-benchmark
- pytest-cov
- pytest-mock

---

## Notes

- **CRITICAL**: Story complexity increased from 3 to 8 points due to C12 fix
- C12 fix: Multi-project test infrastructure is complex but essential
- Mock time prevents flaky tests
- Deterministic test data critical for reproducibility
- This story validates ALL Epic 29 functionality
- High coverage essential for production confidence

---

## Related Documents

- PRD: `docs/features/ceremony-integration-and-self-learning/PRD.md`
- Architecture: `ARCHITECTURE.md` (Testing Strategy section)
- Critical Fixes: `CRITICAL_FIXES.md` (ALL fixes validated here)
- Epic 29: `epics/epic-29-self-learning-feedback-loop.md`

# Epic 6 Regression Test Suite

**Status**: Ready for Baseline Capture
**Created**: 2025-10-30
**Purpose**: Ensure zero regressions during Epic 6 refactoring

---

## Overview

This regression test suite captures the CURRENT behavior of:
- **GAODevOrchestrator** (1,327 lines) - Before service extraction
- **SandboxManager** (781 lines) - Before service extraction

After Epic 6 refactoring, ALL these tests MUST still pass to ensure zero regressions.

---

## Test Files

| File | Purpose | Test Count | Priority |
|------|---------|------------|----------|
| `test_orchestrator_regression.py` | Orchestrator behavior tests | ~25 | P0 |
| `test_sandbox_regression.py` | Sandbox manager behavior tests | ~30 | P0 |
| `test_workflow_integration.py` | Integration tests | ~15 | P0 |
| `test_performance_baseline.py` | Performance baselines | ~12 | P0 |

**Total**: ~82 regression tests

---

## Usage

### Step 1: Capture Baseline (BEFORE Epic 6)

**CRITICAL**: Run this BEFORE starting any Epic 6 refactoring work!

```bash
# Capture performance baselines
pytest tests/regression/epic_6/test_performance_baseline.py --baseline-mode=capture -v

# Run all regression tests to verify they pass
pytest tests/regression/epic_6/ -v
```

Expected output:
- All tests pass (100%)
- Performance baselines saved to `baselines/performance_baseline.json`

### Step 2: Validate After Each Story

After completing each Epic 6 story (6.1, 6.2, etc.):

```bash
# Run all regression tests
pytest tests/regression/epic_6/ -v

# Compare performance to baseline
pytest tests/regression/epic_6/test_performance_baseline.py --baseline-mode=compare -v
```

**Success Criteria**:
- All tests pass (100%)
- Performance within 5% of baseline (10% for memory)

**If ANY test fails**:
1. STOP immediately
2. Investigate root cause
3. Fix regression
4. Re-run tests
5. Only proceed when all tests pass

### Step 3: Final Validation (AFTER Epic 6)

After completing all Epic 6 stories:

```bash
# Full regression suite
pytest tests/regression/epic_6/ -v --cov=gao_dev --cov-report=html

# Generate test report
pytest tests/regression/epic_6/ --html=report.html --self-contained-html
```

---

## Test Categories

### A. Orchestrator Regression Tests

**File**: `test_orchestrator_regression.py`

**Coverage**:
- Workflow execution behavior
- Agent management
- State management
- Quality gates
- Error handling
- Brian orchestrator integration
- Mode configuration (CLI, API, benchmark)

**Key Tests**:
- `test_orchestrator_initialization` - Basic initialization
- `test_workflow_artifact_verification` - Quality gates
- `test_agent_definitions_loaded` - Agent management
- `test_project_root_accessible` - State management

### B. Sandbox Regression Tests

**File**: `test_sandbox_regression.py`

**Coverage**:
- Project lifecycle (create, list, delete)
- Project state management
- Benchmark tracking
- Clean state management
- Validation
- Boilerplate integration

**Key Tests**:
- `test_create_project_basic` - Project creation
- `test_create_project_with_boilerplate` - Boilerplate copying
- `test_add_benchmark_run` - Benchmark tracking
- `test_is_clean_after_creation` - Clean state
- `test_boilerplate_files_copied` - Boilerplate integration

### C. Integration Tests

**File**: `test_workflow_integration.py`

**Coverage**:
- Orchestrator + Sandbox integration
- Component coordination
- State consistency
- Error propagation
- Initialization order
- Path handling
- Resource cleanup

**Key Tests**:
- `test_orchestrator_and_sandbox_can_coexist` - Basic integration
- `test_workflow_registry_accessible_from_orchestrator` - Coordination
- `test_sandbox_state_persistence` - State consistency

### D. Performance Baseline Tests

**File**: `test_performance_baseline.py`

**Coverage**:
- Initialization performance
- Operation performance
- Memory usage
- Workflow registry performance

**Key Tests**:
- `test_orchestrator_initialization_time` - Orchestrator init
- `test_sandbox_project_creation_time` - Project creation
- `test_orchestrator_memory_usage` - Memory baseline

---

## Baseline Data

Performance baselines are stored in: `baselines/performance_baseline.json`

**Format**:
```json
{
  "test_name": {
    "baseline_value": 0.145,
    "unit": "seconds",
    "tolerance": 0.05,
    "min_acceptable": 0.1378,
    "max_acceptable": 0.1523,
    "measured_date": "2025-10-30T10:30:00"
  }
}
```

**Tolerance Levels**:
- Time measurements: 5% tolerance
- Memory measurements: 10% tolerance

---

## Success Criteria

### Per-Story Validation

After each Epic 6 story:
- [ ] All regression tests pass (100%)
- [ ] Performance within tolerance
- [ ] No new test failures
- [ ] Coverage maintained (80%+)

### Final Epic 6 Validation

After all stories complete:
- [ ] All 82+ regression tests pass (100%)
- [ ] Performance within tolerance (< 5%)
- [ ] Memory within tolerance (< 10%)
- [ ] Integration tests pass (100%)
- [ ] Zero regressions confirmed

---

## Red Alert Thresholds

**STOP work immediately if**:
- Any regression test fails
- Performance degrades > 10%
- Memory usage increases > 20%
- Test coverage drops below 75%

**Investigate immediately if**:
- Performance degrades 5-10%
- Memory usage increases 10-20%
- Test execution time increases > 20%

---

## Troubleshooting

### Tests Failing After Refactoring

1. **Check if behavior intentionally changed**
   - Review story acceptance criteria
   - Check if behavior was supposed to change
   - If yes: Update test expectations and document

2. **Check if regression introduced**
   - Compare behavior before and after
   - Identify what broke
   - Fix the regression
   - Verify tests pass

3. **Check if test needs updating**
   - Some tests may test implementation details
   - If refactoring changes implementation but not behavior
   - Update test to match new implementation

### Performance Regression

1. **Profile the code**
   ```bash
   python -m cProfile -o profile.stats your_test.py
   ```

2. **Identify bottleneck**
   - Check for unnecessary loops
   - Check for inefficient algorithms
   - Check for excess I/O operations

3. **Optimize**
   - Fix bottleneck
   - Re-run performance tests
   - Verify within tolerance

### Baseline Capture Issues

If baseline capture fails:
- Check that all dependencies installed
- Check that project structure correct
- Check that test fixtures working
- Run individual tests to isolate issue

---

## Commands Reference

```bash
# Quick test run (no baseline)
pytest tests/regression/epic_6/ -v

# Capture baseline
pytest tests/regression/epic_6/test_performance_baseline.py --baseline-mode=capture -v

# Compare to baseline
pytest tests/regression/epic_6/test_performance_baseline.py --baseline-mode=compare -v

# Run with coverage
pytest tests/regression/epic_6/ --cov=gao_dev --cov-report=html -v

# Run specific test file
pytest tests/regression/epic_6/test_orchestrator_regression.py -v

# Run specific test
pytest tests/regression/epic_6/test_orchestrator_regression.py::TestOrchestratorWorkflowExecution::test_orchestrator_initialization -v

# Generate HTML report
pytest tests/regression/epic_6/ --html=report.html --self-contained-html

# Run only fast tests (skip slow/stress tests)
pytest tests/regression/epic_6/ -v -m "not slow"
```

---

## Maintenance

### Adding New Tests

When adding new regression tests:
1. Follow existing test patterns
2. Use descriptive test names
3. Add clear docstrings
4. Test current behavior, not ideal behavior
5. Add to appropriate test file

### Updating Baseline

To update baseline after intentional performance improvement:
```bash
# Re-capture baseline
pytest tests/regression/epic_6/test_performance_baseline.py --baseline-mode=capture -v

# Commit updated baseline
git add tests/regression/epic_6/baselines/
git commit -m "chore: update performance baselines after optimization"
```

**Document why baseline changed** in commit message.

---

## Epic 6 Integration

This regression test suite integrates with Epic 6 as follows:

### Before Epic 6 Starts
- [ ] All tests implemented
- [ ] All tests passing
- [ ] Baselines captured
- [ ] Suite committed to git

### During Epic 6 (After Each Story)
- [ ] Run regression suite
- [ ] Verify 100% pass rate
- [ ] Compare performance
- [ ] Update story status only if tests pass

### After Epic 6 Complete
- [ ] Full regression suite passes
- [ ] Final performance validation
- [ ] Generate test report
- [ ] Mark Epic 6 complete

---

## Contact

For questions about regression tests:
- See: `docs/features/core-gao-dev-system-refactor/EPIC-6-REGRESSION-TEST-SUITE.md`
- See: `docs/features/core-gao-dev-system-refactor/EPIC-6-IMPLEMENTATION-GUIDE.md`

---

**REMEMBER**: No Epic 6 refactoring work begins until this regression test suite is implemented and ALL tests pass.

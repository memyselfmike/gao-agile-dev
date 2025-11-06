# Epic 6: Regression Test Suite

**Epic**: Legacy Cleanup & God Class Refactoring
**Created**: 2025-10-30
**Priority**: P0 - CRITICAL
**Purpose**: Ensure zero regressions during refactoring

---

## Overview

**CRITICAL**: This regression test suite MUST be created and ALL tests MUST pass BEFORE starting any Epic 6 refactoring work.

The test suite captures the current behavior of:
1. `GAODevOrchestrator` (1,327 lines) - Before extracting services
2. `SandboxManager` (781 lines) - Before extracting services
3. Integration workflows - End-to-end functionality
4. Performance baselines - To detect degradation

**Success Criterion**: After each Epic 6 story, ALL these tests must still pass.

---

## Test Suite Structure

```
tests/regression/epic_6/
├── __init__.py
├── test_orchestrator_regression.py      # Orchestrator behavior tests
├── test_sandbox_regression.py           # Sandbox manager behavior tests
├── test_workflow_integration.py         # E2E workflow tests
├── test_performance_baseline.py         # Performance benchmarks
├── fixtures/
│   ├── test_projects.py
│   ├── test_workflows.py
│   └── test_data.py
└── baselines/
    ├── orchestrator_baseline.json       # Expected behaviors
    ├── sandbox_baseline.json
    └── performance_baseline.json
```

---

## 1. Orchestrator Regression Tests

**File**: `tests/regression/epic_6/test_orchestrator_regression.py`

### Test Categories

#### A. Workflow Execution Tests

```python
class TestOrchestratorWorkflowExecution:
    """Test current workflow execution behavior."""

    def test_create_prd_workflow_execution(self):
        """Test create-prd workflow executes correctly."""
        # Given: A project name and basic config
        # When: create-prd workflow executed
        # Then: PRD.md created, all artifacts present
        pass

    def test_create_story_workflow_execution(self):
        """Test create-story workflow executes correctly."""
        # Given: Epic and story numbers
        # When: create-story workflow executed
        # Then: Story file created, sprint status updated
        pass

    def test_dev_story_workflow_execution(self):
        """Test dev-story workflow executes correctly."""
        # Given: Existing story file
        # When: dev-story workflow executed
        # Then: Implementation created, tests pass
        pass

    def test_workflow_sequence_execution(self):
        """Test multiple workflows execute in sequence."""
        # Given: Sequence of workflows
        # When: Sequence executed
        # Then: All workflows run, context passed between steps
        pass

    def test_workflow_error_handling(self):
        """Test workflow failure handling."""
        # Given: Workflow that will fail
        # When: Workflow executed
        # Then: Error caught, logged, user notified
        pass
```

#### B. Agent Management Tests

```python
class TestOrchestratorAgentManagement:
    """Test current agent creation and execution."""

    def test_agent_creation_from_config(self):
        """Test agents created correctly from config."""
        # Given: Agent configurations
        # When: Orchestrator initializes
        # Then: All agents available
        pass

    def test_agent_assignment_to_workflow(self):
        """Test correct agent assigned to workflow."""
        # Given: Workflow requiring specific agent
        # When: Workflow executed
        # Then: Correct agent used
        pass

    def test_multi_agent_workflow(self):
        """Test workflow requiring multiple agents."""
        # Given: Complex workflow
        # When: Workflow executed
        # Then: Multiple agents coordinate correctly
        pass
```

#### C. State Management Tests

```python
class TestOrchestratorStateManagement:
    """Test current state management behavior."""

    def test_workflow_state_persistence(self):
        """Test workflow state saved correctly."""
        # Given: Running workflow
        # When: State checkpoint
        # Then: State persisted to disk
        pass

    def test_workflow_state_recovery(self):
        """Test workflow recovery from saved state."""
        # Given: Interrupted workflow
        # When: Orchestrator restarts
        # Then: Workflow resumes from last checkpoint
        pass

    def test_concurrent_workflow_state(self):
        """Test state isolation between concurrent workflows."""
        # Given: Multiple workflows running
        # When: State updates
        # Then: Each workflow has isolated state
        pass
```

#### D. Quality Gate Tests

```python
class TestOrchestratorQualityGates:
    """Test current quality gate validation."""

    def test_artifact_validation(self):
        """Test workflow artifacts validated."""
        # Given: Workflow completion
        # When: Quality gates run
        # Then: Required artifacts validated
        pass

    def test_quality_gate_failure(self):
        """Test workflow fails on missing artifacts."""
        # Given: Incomplete workflow output
        # When: Quality gates run
        # Then: Workflow marked failed
        pass

    def test_quality_gate_bypass(self):
        """Test quality gate bypass flag works."""
        # Given: Quality gate failure
        # When: Bypass flag set
        # Then: Workflow continues
        pass
```

---

## 2. Sandbox Manager Regression Tests

**File**: `tests/regression/epic_6/test_sandbox_regression.py`

### Test Categories

#### A. Project Lifecycle Tests

```python
class TestSandboxProjectLifecycle:
    """Test current project lifecycle behavior."""

    def test_sandbox_init(self):
        """Test sandbox project initialization."""
        # Given: Project name and boilerplate
        # When: sandbox init executed
        # Then: Project created, structure correct
        pass

    def test_sandbox_clean(self):
        """Test sandbox project cleanup."""
        # Given: Existing sandbox project
        # When: sandbox clean executed
        # Then: Project reset to initial state
        pass

    def test_sandbox_delete(self):
        """Test sandbox project deletion."""
        # Given: Existing sandbox project
        # When: sandbox delete executed
        # Then: Project removed, state cleaned up
        pass

    def test_sandbox_list(self):
        """Test listing sandbox projects."""
        # Given: Multiple sandbox projects
        # When: sandbox list executed
        # Then: All projects listed with status
        pass
```

#### B. Project State Management Tests

```python
class TestSandboxStateManagement:
    """Test current sandbox state management."""

    def test_project_state_creation(self):
        """Test project state file created."""
        # Given: New sandbox project
        # When: Project initialized
        # Then: State file created with metadata
        pass

    def test_project_state_updates(self):
        """Test project state updated correctly."""
        # Given: Existing project
        # When: Project operations performed
        # Then: State file reflects changes
        pass

    def test_project_state_persistence(self):
        """Test project state persists across sessions."""
        # Given: Project with state
        # When: Manager restarts
        # Then: State loaded correctly
        pass
```

#### C. Benchmark Tracking Tests

```python
class TestSandboxBenchmarkTracking:
    """Test current benchmark tracking behavior."""

    def test_benchmark_run_tracking(self):
        """Test benchmark runs tracked correctly."""
        # Given: Benchmark configuration
        # When: Benchmark executed
        # Then: Run metrics recorded
        pass

    def test_benchmark_metrics_calculation(self):
        """Test benchmark metrics calculated correctly."""
        # Given: Multiple benchmark runs
        # When: Metrics requested
        # Then: Averages, trends calculated
        pass

    def test_benchmark_comparison(self):
        """Test benchmark comparison functionality."""
        # Given: Multiple benchmark runs
        # When: Comparison requested
        # Then: Differences highlighted
        pass
```

#### D. Boilerplate Integration Tests

```python
class TestSandboxBoilerplateIntegration:
    """Test current boilerplate integration behavior."""

    def test_boilerplate_cloning(self):
        """Test boilerplate repository cloned correctly."""
        # Given: Boilerplate URL
        # When: sandbox init with boilerplate
        # Then: Repository cloned, files present
        pass

    def test_template_variable_substitution(self):
        """Test template variables substituted."""
        # Given: Boilerplate with variables
        # When: Project initialized
        # Then: Variables replaced with values
        pass

    def test_dependency_installation(self):
        """Test dependencies installed after cloning."""
        # Given: Boilerplate with dependencies
        # When: Project initialized
        # Then: Dependencies installed
        pass
```

---

## 3. Integration Workflow Tests

**File**: `tests/regression/epic_6/test_workflow_integration.py`

### Test Categories

#### A. End-to-End Workflow Tests

```python
class TestE2EWorkflows:
    """Test complete workflows end-to-end."""

    def test_full_prd_creation_flow(self):
        """Test complete PRD creation flow."""
        # Given: Project name
        # When: create-prd workflow executed
        # Then: PRD created, formatted, validated
        pass

    def test_full_story_creation_flow(self):
        """Test complete story creation flow."""
        # Given: PRD exists, epic number
        # When: create-story workflow executed
        # Then: Story created, sprint status updated
        pass

    def test_full_story_implementation_flow(self):
        """Test complete story implementation flow."""
        # Given: Story file exists
        # When: dev-story workflow executed
        # Then: Code implemented, tested, documented
        pass

    def test_full_project_workflow(self):
        """Test complete project workflow (PRD → Stories → Implementation)."""
        # Given: Project concept
        # When: Full workflow executed
        # Then: Project created, stories implemented, tests pass
        pass
```

#### B. Sandbox Integration Tests

```python
class TestSandboxIntegration:
    """Test sandbox integration with orchestrator."""

    def test_orchestrator_creates_sandbox_project(self):
        """Test orchestrator can create sandbox project."""
        # Given: Orchestrator workflow
        # When: Workflow requests sandbox
        # Then: Sandbox project created
        pass

    def test_orchestrator_runs_in_sandbox(self):
        """Test orchestrator runs workflow in sandbox."""
        # Given: Sandbox project
        # When: Workflow executed in sandbox
        # Then: Workflow runs, outputs in sandbox
        pass

    def test_sandbox_benchmark_integration(self):
        """Test sandbox benchmarks integrate with orchestrator."""
        # Given: Benchmark configuration
        # When: Orchestrator runs benchmark
        # Then: Metrics collected, reported
        pass
```

---

## 4. Performance Baseline Tests

**File**: `tests/regression/epic_6/test_performance_baseline.py`

### Performance Metrics

```python
class TestPerformanceBaseline:
    """Establish performance baselines before refactoring."""

    def test_orchestrator_initialization_time(self):
        """Baseline: Orchestrator initialization time."""
        # Measure: Time to initialize GAODevOrchestrator
        # Baseline: Record current time
        # Tolerance: +/- 5% after refactoring
        pass

    def test_workflow_execution_time(self):
        """Baseline: Workflow execution time."""
        # Measure: Time to execute create-prd workflow
        # Baseline: Record current time
        # Tolerance: +/- 5% after refactoring
        pass

    def test_sandbox_initialization_time(self):
        """Baseline: Sandbox initialization time."""
        # Measure: Time to initialize sandbox project
        # Baseline: Record current time
        # Tolerance: +/- 5% after refactoring
        pass

    def test_memory_usage_baseline(self):
        """Baseline: Memory usage during operation."""
        # Measure: Memory usage during workflow execution
        # Baseline: Record current usage
        # Tolerance: +/- 10% after refactoring
        pass

    def test_concurrent_workflow_performance(self):
        """Baseline: Concurrent workflow performance."""
        # Measure: Time for 3 concurrent workflows
        # Baseline: Record current time
        # Tolerance: +/- 5% after refactoring
        pass
```

### Baseline Data Format

```json
{
  "test_name": "test_orchestrator_initialization_time",
  "baseline_value": 0.145,
  "unit": "seconds",
  "tolerance": 0.05,
  "min_acceptable": 0.1378,
  "max_acceptable": 0.1523,
  "measured_date": "2025-10-30",
  "measured_by": "Murat"
}
```

---

## 5. Test Execution Strategy

### Phase 1: Baseline Capture (Before Epic 6)

**MUST DO FIRST**:
1. Run ALL regression tests
2. Verify ALL tests pass (100%)
3. Record performance baselines
4. Save baseline data to `baselines/`
5. Commit baseline data to git

**Commands**:
```bash
# Run all regression tests
pytest tests/regression/epic_6/ -v --tb=short

# Run with coverage
pytest tests/regression/epic_6/ --cov=gao_dev --cov-report=html

# Run performance baselines
pytest tests/regression/epic_6/test_performance_baseline.py --baseline-mode=capture
```

### Phase 2: Continuous Validation (During Epic 6)

**After Each Story**:
1. Run ALL regression tests
2. Compare performance to baseline
3. Verify 100% pass rate
4. If any test fails:
   - STOP
   - Investigate root cause
   - Fix or revert changes
   - Retry

**Commands**:
```bash
# Run regression tests after story completion
pytest tests/regression/epic_6/ -v

# Compare performance to baseline
pytest tests/regression/epic_6/test_performance_baseline.py --baseline-mode=compare
```

### Phase 3: Final Validation (After Epic 6)

**After All Stories Complete**:
1. Run FULL regression suite
2. Run FULL integration tests
3. Run performance benchmarks
4. Generate test report
5. Validate zero regressions

**Commands**:
```bash
# Full regression suite
pytest tests/regression/epic_6/ -v --cov=gao_dev --cov-report=html

# Full integration tests
pytest tests/integration/ -v

# Generate test report
pytest tests/regression/epic_6/ --html=report.html --self-contained-html
```

---

## 6. Test Coverage Requirements

### Minimum Coverage Targets

**Per Component**:
- Orchestrator: 80%+ coverage maintained
- Sandbox Manager: 80%+ coverage maintained
- New Services: 80%+ coverage (unit tests)
- Integration: All critical paths tested

**Overall**:
- Test suite pass rate: 100%
- Regression tests: 0 failures
- Performance variance: < 5%
- Line coverage: 80%+ maintained

---

## 7. Test Data and Fixtures

### Fixture Requirements

**Orchestrator Fixtures**:
- Mock agent configurations
- Sample workflow definitions
- Test project structures
- Mock Claude CLI responses

**Sandbox Fixtures**:
- Sample boilerplate repositories
- Test project structures
- Benchmark configurations
- Mock git operations

**Integration Fixtures**:
- Complete test projects
- Multi-step workflow definitions
- Expected artifact outputs

### Fixture Location

```
tests/regression/epic_6/fixtures/
├── agents/
│   ├── test_agents.yaml
│   └── mock_agent_responses.json
├── workflows/
│   ├── test_workflows.yaml
│   └── workflow_sequences.json
├── projects/
│   ├── test_project_1/
│   └── test_project_2/
└── benchmarks/
    ├── test_benchmark_1.yaml
    └── test_benchmark_2.yaml
```

---

## 8. Continuous Monitoring

### Test Metrics Dashboard

Track these metrics during Epic 6:

| Metric | Baseline | Current | Status |
|--------|----------|---------|--------|
| Regression Tests Pass Rate | 100% | - | - |
| Orchestrator Coverage | 80% | - | - |
| Sandbox Coverage | 80% | - | - |
| Workflow Execution Time | 2.5s | - | - |
| Memory Usage | 120MB | - | - |
| Integration Tests Pass Rate | 100% | - | - |

### Alert Thresholds

**RED ALERT** (Stop work immediately):
- Any regression test fails
- Performance degrades > 10%
- Coverage drops below 75%
- Memory usage increases > 20%

**YELLOW ALERT** (Investigate):
- Performance degrades 5-10%
- Coverage drops 75-80%
- Memory usage increases 10-20%
- Test execution time increases > 20%

---

## 9. Test Execution Checklist

### Before Starting Epic 6

- [ ] All regression tests written
- [ ] All regression tests pass (100%)
- [ ] Performance baselines captured
- [ ] Baseline data committed to git
- [ ] Test fixtures created
- [ ] Test execution commands documented
- [ ] Continuous monitoring set up

### After Each Story (6.1-6.8)

- [ ] Run ALL regression tests
- [ ] Verify 100% pass rate
- [ ] Compare performance to baseline
- [ ] Update test coverage metrics
- [ ] Document any issues
- [ ] Story NOT complete until tests pass

### After Epic 6 Complete

- [ ] Full regression suite passes (100%)
- [ ] Full integration suite passes (100%)
- [ ] Performance within tolerance (< 5%)
- [ ] Coverage maintained (80%+)
- [ ] Test report generated
- [ ] Zero regressions confirmed

---

## 10. Test Maintenance

### Test Updates

**When to Update Tests**:
- When behavior INTENTIONALLY changes
- When new features added
- When bugs fixed

**How to Update**:
1. Document reason for change
2. Update test expectations
3. Update baseline data
4. Get review approval
5. Commit with clear message

### Test Documentation

**Each Test Must Have**:
- Clear docstring explaining what it tests
- Given/When/Then structure
- Expected behavior documented
- Baseline values recorded
- Tolerance levels defined

---

## Summary

This regression test suite is **CRITICAL** for Epic 6 success. It ensures:

1. **Zero Regressions**: All existing behavior preserved
2. **Performance Maintained**: No degradation during refactoring
3. **Confidence**: Safe to refactor knowing tests will catch issues
4. **Continuous Validation**: Test after every story

**REMEMBER**: Epic 6 is refactoring, not new features. The system MUST behave exactly the same after refactoring. These tests prove it.

---

**Status**: Draft - Needs Implementation
**Next Action**: Implement regression test suite before starting Story 6.1
**Priority**: P0 - MUST BE DONE FIRST

---

**CRITICAL RULE**:
> "No Epic 6 refactoring work begins until this regression test suite is implemented and ALL tests pass."

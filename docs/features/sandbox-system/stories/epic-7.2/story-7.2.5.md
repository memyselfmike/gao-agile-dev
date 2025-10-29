# Story 7.2.5: Integration Testing

**Epic**: 7.2 - Workflow-Driven Core Architecture
**Story Points**: 2
**Status**: Ready
**Priority**: High

---

## User Story

As a **developer**, I want **comprehensive integration tests for the workflow-driven architecture**, so that **I can verify GAO-Dev autonomously selects and executes workflows correctly end-to-end**.

---

## Context

Epic 7.2 introduces a fundamental architectural change: GAO-Dev becomes workflow-driven with intelligent workflow selection. This story ensures the entire system works together correctly through comprehensive integration testing.

**What Needs Testing**:
1. Workflow selection from various prompts
2. Complete workflow execution end-to-end
3. Clarification dialog in different modes
4. Benchmark integration with new architecture
5. Artifact creation and git commits
6. Metrics collection and reporting

---

## Acceptance Criteria

### AC1: Integration Test Suite Created
- [ ] Create `tests/integration/test_workflow_driven_core.py`
- [ ] Test structure follows existing patterns
- [ ] Tests can run in sandbox environment
- [ ] Cleanup after tests (temp directories)

### AC2: Test Workflow Selection
- [ ] Test: Greenfield prompt selects greenfield workflow
- [ ] Test: Enhancement prompt selects story workflow
- [ ] Test: Ambiguous prompt triggers clarification
- [ ] Test: Explicit workflow override works

### AC3: Test Complete Workflow Execution
- [ ] Test: Simple workflow executes all steps
- [ ] Test: Artifacts created in correct locations
- [ ] Test: Git commits made after each step
- [ ] Test: WorkflowResult contains expected metrics

### AC4: Test Error Handling
- [ ] Test: Workflow stops on step failure (fail-fast)
- [ ] Test: Timeout handling works
- [ ] Test: Invalid workflow name fails gracefully
- [ ] Test: Missing agent method fails with clear error

### AC5: Test Clarification Dialog
- [ ] Test: Benchmark mode uses defaults
- [ ] Test: Enhanced prompt includes clarification answers
- [ ] Test: Clarification loop prevents infinite loops (max 3)

### AC6: Test Benchmark Integration
- [ ] Test: BenchmarkRunner calls GAO-Dev core
- [ ] Test: Metrics extracted from WorkflowResult
- [ ] Test: Success criteria evaluated correctly
- [ ] Test: Benchmark report generated

### AC7: Test with Real BMAD Workflows
- [ ] Test: Load workflow from `bmad/bmm/workflows/`
- [ ] Test: Execute PRD creation workflow
- [ ] Test: Execute story implementation workflow
- [ ] Test: Verify outputs match workflow expectations

### AC8: Performance Tests
- [ ] Test: Workflow selection completes in < 5s
- [ ] Test: Simple workflow completes in reasonable time
- [ ] Test: Memory usage stays within bounds

### AC9: Documentation
- [ ] Document how to run integration tests
- [ ] Document test data setup
- [ ] Document expected test outputs
- [ ] Add troubleshooting guide for test failures

---

## Technical Details

### Test Structure

```
tests/
├── integration/
│   ├── __init__.py
│   ├── test_workflow_driven_core.py      # Main integration tests
│   ├── test_workflow_selection.py        # Workflow selector tests
│   ├── test_benchmark_integration.py     # Benchmark integration tests
│   └── fixtures/
│       ├── test_workflows/               # Simple test workflows
│       ├── test_prompts.yaml             # Test prompt examples
│       └── test_benchmarks/              # Test benchmark configs
└── conftest.py                           # Pytest fixtures
```

### Integration Test Examples

```python
# tests/integration/test_workflow_driven_core.py

import pytest
import tempfile
from pathlib import Path
from gao_dev.orchestrator import GAODevOrchestrator, ExecutionMode
from gao_dev.orchestrator.workflow_results import WorkflowStatus

@pytest.fixture
def test_project():
    """Create temporary test project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "test_project"
        project_path.mkdir()

        # Initialize git
        import subprocess
        subprocess.run(["git", "init"], cwd=project_path, check=True)
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=project_path,
            check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=project_path,
            check=True
        )

        yield project_path


@pytest.mark.integration
@pytest.mark.asyncio
async def test_greenfield_workflow_selection(test_project):
    """Test that greenfield prompt selects appropriate workflow."""
    orchestrator = GAODevOrchestrator(
        project_root=test_project,
        mode=ExecutionMode.BENCHMARK  # Use benchmark mode to avoid prompts
    )

    prompt = "Build a new todo application with Python and FastAPI"

    # Should auto-select greenfield workflow
    result = await orchestrator.execute_workflow(prompt)

    assert result.status == WorkflowStatus.COMPLETED
    assert "greenfield" in result.workflow_name.lower()
    assert result.total_steps > 0
    assert len(result.step_results) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_workflow_execution_creates_artifacts(test_project):
    """Test that workflow execution creates expected artifacts."""
    orchestrator = GAODevOrchestrator(
        project_root=test_project,
        mode=ExecutionMode.BENCHMARK
    )

    # Simple test workflow
    from gao_dev.core.workflow_registry import Workflow, WorkflowStep

    test_workflow = Workflow(
        name="test-workflow",
        description="Simple test workflow",
        steps=[
            WorkflowStep(
                name="Create PRD",
                agent="John",
                task_type="create_prd",
                parameters={"project_name": "Test Project"}
            )
        ]
    )

    result = await orchestrator.execute_workflow(
        initial_prompt="Build test project",
        workflow=test_workflow
    )

    # Verify workflow completed
    assert result.status == WorkflowStatus.COMPLETED

    # Verify artifacts created
    assert result.total_artifacts > 0

    # Verify PRD exists
    prd_path = test_project / "docs" / "PRD.md"
    assert prd_path.exists()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_workflow_stops_on_failure(test_project):
    """Test that workflow stops on first step failure."""
    orchestrator = GAODevOrchestrator(
        project_root=test_project,
        mode=ExecutionMode.BENCHMARK
    )

    # Workflow with invalid step
    from gao_dev.core.workflow_registry import Workflow, WorkflowStep

    failing_workflow = Workflow(
        name="failing-workflow",
        description="Workflow that fails",
        steps=[
            WorkflowStep(
                name="Valid Step",
                agent="John",
                task_type="create_prd",
                parameters={"project_name": "Test"}
            ),
            WorkflowStep(
                name="Invalid Step",
                agent="NonExistent",
                task_type="invalid_task",
                parameters={}
            ),
            WorkflowStep(
                name="Should Not Execute",
                agent="Amelia",
                task_type="implement_story",
                parameters={}
            )
        ]
    )

    result = await orchestrator.execute_workflow(
        initial_prompt="Test failure",
        workflow=failing_workflow
    )

    # Workflow should fail
    assert result.status == WorkflowStatus.FAILED

    # Only first 2 steps should be attempted
    assert len(result.step_results) == 2

    # First step should succeed
    assert result.step_results[0].status == "success"

    # Second step should fail
    assert result.step_results[1].status == "failed"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_clarification_in_benchmark_mode(test_project):
    """Test that clarification uses defaults in benchmark mode."""
    orchestrator = GAODevOrchestrator(
        project_root=test_project,
        mode=ExecutionMode.BENCHMARK
    )

    # Ambiguous prompt that triggers clarification
    prompt = "Build an app"

    # Should complete with defaults
    result = await orchestrator.execute_workflow(prompt)

    # Should have selected a workflow using defaults
    assert result.workflow_name != "auto-select"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_benchmark_runner_integration(test_project):
    """Test complete benchmark run with new architecture."""
    from gao_dev.sandbox.benchmark.runner import BenchmarkRunner
    from gao_dev.sandbox.benchmark.config import BenchmarkConfig

    # Create simple benchmark config
    config = BenchmarkConfig(
        name="test-benchmark",
        initial_prompt="Build a simple calculator application",
        timeout_seconds=300,
        success_criteria={
            "artifacts_exist": ["docs/PRD.md"]
        }
    )

    runner = BenchmarkRunner(
        config=config,
        project_path=test_project
    )

    # Run benchmark (should call GAO-Dev core)
    result = await runner.run_benchmark()

    # Verify benchmark completed
    assert result.benchmark_name == "test-benchmark"
    assert result.workflow_name is not None

    # Verify metrics collected
    assert result.duration_seconds > 0
    assert "total_steps" in result.metrics


@pytest.mark.integration
@pytest.mark.slow
async def test_load_real_bmad_workflow():
    """Test loading and executing real BMAD workflow."""
    from gao_dev.core.workflow_registry import WorkflowRegistry

    registry = WorkflowRegistry()

    # Load PRD workflow from BMAD
    workflows = registry.list_workflows()
    prd_workflows = [w for w in workflows if "prd" in w.name.lower()]

    assert len(prd_workflows) > 0, "Should have PRD workflow in BMAD"

    # Verify workflow structure
    prd_workflow = prd_workflows[0]
    assert prd_workflow.steps is not None
    assert len(prd_workflow.steps) > 0


@pytest.mark.integration
@pytest.mark.performance
async def test_workflow_selection_performance(test_project):
    """Test that workflow selection completes quickly."""
    import time

    orchestrator = GAODevOrchestrator(
        project_root=test_project,
        mode=ExecutionMode.BENCHMARK
    )

    prompt = "Build a todo application"

    start = time.time()
    selection = await orchestrator.select_workflow_for_prompt(prompt)
    duration = time.time() - start

    # Selection should be fast (< 5 seconds)
    assert duration < 5.0

    # Should have selected a workflow
    assert selection.workflow is not None
```

### Fixtures and Test Data

```python
# tests/conftest.py

import pytest
from pathlib import Path

@pytest.fixture
def mock_api_key(monkeypatch):
    """Mock Anthropic API key for tests."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-12345")


@pytest.fixture
def test_workflow():
    """Simple test workflow for integration tests."""
    from gao_dev.core.workflow_registry import Workflow, WorkflowStep

    return Workflow(
        name="test-workflow",
        description="Simple test workflow",
        steps=[
            WorkflowStep(
                name="Create PRD",
                agent="John",
                task_type="create_prd",
                parameters={"project_name": "Test"}
            ),
            WorkflowStep(
                name="Create Architecture",
                agent="Winston",
                task_type="create_architecture",
                parameters={}
            )
        ]
    )
```

### Test Prompts Data

```yaml
# tests/integration/fixtures/test_prompts.yaml

test_prompts:
  greenfield:
    - "Build a new todo application with Python"
    - "Create a RESTful API for managing tasks"
    - "Develop a simple blog platform"

  enhancement:
    - "Add user authentication to existing app"
    - "Implement search functionality"
    - "Add email notifications"

  bug_fix:
    - "Fix the login bug"
    - "Resolve database connection issue"

  ambiguous:
    - "Build an app"
    - "Fix it"
    - "Make it better"
```

---

## Testing Strategy

### Test Categories

1. **Unit Tests** (Stories 7.2.1-7.2.4)
   - Individual component tests
   - Mocked dependencies
   - Fast execution

2. **Integration Tests** (This story)
   - End-to-end workflow execution
   - Real BMAD workflows
   - Sandbox environment
   - Slower execution

3. **Performance Tests**
   - Workflow selection speed
   - Memory usage
   - Execution time benchmarks

### Running Tests

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific test file
pytest tests/integration/test_workflow_driven_core.py -v

# Run with coverage
pytest tests/integration/ --cov=gao_dev.orchestrator --cov-report=html

# Run only fast tests
pytest -m "integration and not slow"

# Run performance tests
pytest -m "performance"
```

---

## Dependencies

- **All Stories 7.2.1-7.2.4**: Must be complete for integration testing
- **BMAD Workflows**: Must exist in `bmad/bmm/workflows/`
- **Pytest**: Testing framework (INSTALLED)
- **pytest-asyncio**: Async test support (INSTALLED)

---

## Definition of Done

- [ ] Integration test suite created in `tests/integration/`
- [ ] Tests cover workflow selection, execution, clarification, benchmark
- [ ] Tests use real BMAD workflows
- [ ] Error handling and edge cases tested
- [ ] Performance tests for critical paths
- [ ] All tests passing
- [ ] Test coverage >80% for orchestrator module
- [ ] Documentation for running tests
- [ ] CI/CD integration (if applicable)
- [ ] Code review completed
- [ ] Story committed atomically to git

---

## Out of Scope

- UI/visual regression tests (no UI yet)
- Load testing / stress testing (future)
- Security testing (separate epic)
- Cross-platform testing (focus on development platform)

---

## Success Metrics

- **Coverage**: >80% code coverage for orchestrator module
- **Pass Rate**: 100% of integration tests pass
- **Performance**: Workflow selection < 5s, simple workflow < 2 minutes
- **Reliability**: Tests are deterministic and reproducible

---

## Notes

- Integration tests may take longer to run - mark slow tests with @pytest.mark.slow
- Use temporary directories and cleanup after tests
- Mock external API calls if necessary to avoid rate limits
- Document any special test setup (API keys, etc.)
- These tests verify the entire Epic 7.2 architecture works correctly

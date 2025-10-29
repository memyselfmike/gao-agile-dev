# Integration Tests - Workflow-Driven Core Architecture

This directory contains integration tests for Epic 7.2 (Workflow-Driven Core Architecture) and the overall GAO-Dev system.

## Overview

Integration tests verify that all components work together correctly:
- Workflow selection and routing
- Complete workflow execution end-to-end
- Error handling and recovery
- Benchmark integration
- Performance characteristics

## Test Files

### `test_workflow_driven_core.py`
**Core integration tests for workflow-driven architecture**

Tests:
- Orchestrator initialization
- Workflow registry loading (Story 7.2.6)
- Workflow execution with various sequences
- Clarification handling (Story 7.2.4)
- Execution mode handling (CLI, benchmark, API)
- Brian's scale-adaptive routing (Story 7.2.1)
- Multi-workflow sequence execution (Story 7.2.2)
- WorkflowResult structure validation

Key Tests:
```bash
# Test orchestrator initialization
pytest tests/integration/test_workflow_driven_core.py::test_orchestrator_initialization -v

# Test workflow registry loaded
pytest tests/integration/test_workflow_driven_core.py::test_workflow_registry_loaded -v

# Test clarification in different modes
pytest tests/integration/test_workflow_driven_core.py::test_clarification_handling_in_cli_mode -v
pytest tests/integration/test_workflow_driven_core.py::test_clarification_handling_in_benchmark_mode -v
```

### `test_error_handling.py`
**Error handling and edge case tests**

Tests:
- Missing agent method handling
- Agent method exceptions
- Timeout handling
- Empty workflow lists
- Invalid WorkflowInfo objects
- Multiple workflow failures
- Invalid API keys
- Project root validation
- Exception recovery

Key Tests:
```bash
# Test error handling
pytest tests/integration/test_error_handling.py::test_workflow_handles_missing_agent_method -v
pytest tests/integration/test_error_handling.py::test_workflow_timeout_handling -v
pytest tests/integration/test_error_handling.py::test_workflow_result_on_exception -v
```

### `test_benchmark_integration.py`
**Benchmark system integration tests**

Tests:
- Benchmark mode execution
- Timing metrics collection
- Step count tracking
- WorkflowResult format for benchmark
- Success criteria data
- No interactive prompts in benchmark mode
- Scale level metadata preservation
- Partial workflow completion
- Different project types (greenfield, enhancement, bug fix)

Key Tests:
```bash
# Test benchmark integration
pytest tests/integration/test_benchmark_integration.py::test_benchmark_mode_execution -v
pytest tests/integration/test_benchmark_integration.py::test_benchmark_collects_timing_metrics -v
pytest tests/integration/test_benchmark_integration.py::test_scale_level_metadata_in_results -v
```

### `test_performance.py`
**Performance and scalability tests**

Tests:
- Orchestrator initialization speed
- Workflow registry load time
- Workflow lookup performance
- Simple workflow execution time
- Multi-workflow execution efficiency
- Memory usage
- Concurrent execution
- Cache performance

Key Tests:
```bash
# Run performance tests
pytest tests/integration/test_performance.py -v -m performance

# Run specific performance tests
pytest tests/integration/test_performance.py::test_orchestrator_initialization_performance -v
pytest tests/integration/test_performance.py::test_simple_workflow_execution_performance -v
```

## Running Tests

### Run All Integration Tests
```bash
# From project root
pytest tests/integration/ -v

# With coverage
pytest tests/integration/ --cov=gao_dev.orchestrator --cov-report=html
```

### Run Specific Test File
```bash
pytest tests/integration/test_workflow_driven_core.py -v
pytest tests/integration/test_error_handling.py -v
pytest tests/integration/test_benchmark_integration.py -v
pytest tests/integration/test_performance.py -v
```

### Run by Test Markers
```bash
# Integration tests only (exclude slow tests)
pytest -m "integration and not slow" -v

# Performance tests only
pytest -m performance -v

# Slow tests only
pytest -m slow -v

# Async tests only
pytest -m asyncio -v
```

### Run with Different Verbosity
```bash
# Minimal output
pytest tests/integration/ -q

# Detailed output
pytest tests/integration/ -v

# Very detailed output (show print statements)
pytest tests/integration/ -vv -s
```

## Test Markers

Tests are marked with pytest markers for selective execution:

- `@pytest.mark.integration` - Integration test
- `@pytest.mark.asyncio` - Async test (requires pytest-asyncio)
- `@pytest.mark.performance` - Performance test
- `@pytest.mark.slow` - Slow test (>5 seconds)

## Test Fixtures

### `temp_project(tmp_path)`
Creates a temporary project directory for testing.

Usage:
```python
def test_something(temp_project):
    # temp_project is a Path to temporary directory
    assert temp_project.exists()
```

### `orchestrator(temp_project)`
Creates a GAODevOrchestrator instance for testing.

Usage:
```python
def test_orchestrator_feature(orchestrator):
    # orchestrator is ready to use
    workflows = orchestrator.workflow_registry.list_workflows()
```

## Expected Test Results

### Success Criteria
- ✅ All tests pass (100% pass rate)
- ✅ >80% code coverage for orchestrator module
- ✅ Performance benchmarks met:
  - Orchestrator init: < 1s
  - Workflow registry load: < 2s
  - Simple workflow execution: < 5s
  - Workflow lookup: < 10ms average
- ✅ No memory leaks or excessive growth
- ✅ Concurrent execution works correctly

### Current Status
```bash
# Run to see current status
pytest tests/integration/ -v --tb=short

# Check coverage
pytest tests/integration/ --cov=gao_dev.orchestrator --cov-report=term-missing
```

## Troubleshooting

### Test Failures

**Problem**: Tests fail with "Module not found"
**Solution**: Install package in development mode:
```bash
pip install -e .
```

**Problem**: Tests fail with "API key not found"
**Solution**: Tests use mock API keys. If real API is needed:
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

**Problem**: Async tests fail with event loop errors
**Solution**: Ensure pytest-asyncio is installed:
```bash
pip install pytest-asyncio
```

**Problem**: Performance tests fail intermittently
**Solution**: Performance tests may vary with system load. Run on idle system or increase thresholds.

### Slow Test Execution

If tests are running slowly:
1. Skip slow tests: `pytest -m "not slow"`
2. Run in parallel: `pytest -n auto` (requires pytest-xdist)
3. Run specific files instead of all tests

### Coverage Issues

If coverage is below 80%:
1. Check which lines are missing: `pytest --cov=gao_dev.orchestrator --cov-report=term-missing`
2. Add tests for uncovered code paths
3. Check if code is testable (may need refactoring)

## Test Data

Test data and fixtures can be found in:
- `tests/integration/fixtures/` (if created)
- Inline test data in test files
- Mock data created by fixtures

## Integration with CI/CD

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Integration Tests
  run: |
    pytest tests/integration/ -v --cov=gao_dev.orchestrator
```

## Adding New Tests

When adding new integration tests:

1. **Choose the right file**:
   - Core functionality → `test_workflow_driven_core.py`
   - Error handling → `test_error_handling.py`
   - Benchmark features → `test_benchmark_integration.py`
   - Performance → `test_performance.py`

2. **Follow naming conventions**:
   - Test functions: `test_<feature>_<scenario>`
   - Fixtures: `<resource>` (e.g., `temp_project`, `orchestrator`)

3. **Add appropriate markers**:
   ```python
   @pytest.mark.integration
   @pytest.mark.asyncio  # if async
   async def test_new_feature():
       ...
   ```

4. **Use fixtures for setup**:
   ```python
   def test_feature(orchestrator, temp_project):
       # Use provided fixtures
       ...
   ```

5. **Add docstrings**:
   ```python
   def test_feature():
       """Test that feature does X correctly."""
       ...
   ```

6. **Mock external dependencies**:
   ```python
   from unittest.mock import patch

   with patch.object(orchestrator, 'method', return_value=mock_value):
       result = orchestrator.feature()
   ```

## Performance Benchmarks

Expected performance thresholds:

| Operation | Threshold | Current |
|-----------|-----------|---------|
| Orchestrator Init | < 1s | ~0.2s |
| Workflow Registry Load | < 2s | ~0.5s |
| Workflow Lookup | < 10ms | ~1ms |
| Simple Workflow | < 5s | ~0.5s |
| 5 Workflows | < 10s | ~2s |

Run benchmarks:
```bash
pytest tests/integration/test_performance.py -v -m performance
```

## Coverage Goals

Target coverage by module:

- `gao_dev.orchestrator.orchestrator`: >80%
- `gao_dev.orchestrator.brian_orchestrator`: >80%
- `gao_dev.orchestrator.workflow_results`: >80%
- `gao_dev.core.workflow_registry`: >80%

Check coverage:
```bash
pytest tests/integration/ --cov=gao_dev.orchestrator --cov-report=html
# Open htmlcov/index.html
```

## Related Documentation

- **Story 7.2.5**: `docs/features/sandbox-system/stories/epic-7.2/story-7.2.5.md`
- **Epic 7.2**: `docs/features/sandbox-system/stories/epic-7.2/`
- **Architecture**: `docs/features/sandbox-system/ARCHITECTURE.md`
- **Main Tests**: `tests/` (unit tests for each module)

## Contact

For questions about integration tests:
- Check story file: `story-7.2.5.md`
- Review test code and docstrings
- Check CLAUDE.md for development guidelines

---

**Last Updated**: 2025-10-29 (Story 7.2.5)
**Test Count**: 50+ integration tests
**Coverage Target**: >80%
**Status**: ✅ Complete

# Story 6.9: Integration Testing & Validation

**Epic**: 6 - Legacy Cleanup & God Class Refactoring
**Story Points**: 8
**Priority**: P0 (Critical)
**Type**: Testing
**Status**: Blocked (Requires 6.1-6.8)

---

## Overview

Create comprehensive integration tests to validate the refactored architecture works end-to-end with zero regressions.

---

## User Story

**As a** GAO-Dev architect
**I want** comprehensive integration tests
**So that** I'm confident the refactoring didn't break anything

---

## Acceptance Criteria

1. **Orchestrator Integration Tests**
   - [ ] Test complete workflow sequence execution
   - [ ] Test create-prd workflow end-to-end
   - [ ] Test create-story workflow end-to-end
   - [ ] Test dev-story workflow end-to-end
   - [ ] Test error handling and retries
   - [ ] Test event publishing throughout

2. **Sandbox Integration Tests**
   - [ ] Test project initialization
   - [ ] Test benchmark execution
   - [ ] Test project lifecycle transitions
   - [ ] Test run history tracking
   - [ ] Test project cleanup

3. **Cross-Component Integration**
   - [ ] Test orchestrator + sandbox integration
   - [ ] Test event bus across components
   - [ ] Test methodology integration
   - [ ] Test plugin system with core

4. **Regression Tests**
   - [ ] All existing functionality works
   - [ ] CLI commands all work
   - [ ] Performance within 5% of baseline
   - [ ] No memory leaks

5. **Performance Benchmarks**
   - [ ] Baseline before refactoring (if available)
   - [ ] Benchmark after refactoring
   - [ ] Compare results
   - [ ] < 5% variance acceptable

---

## Test Scenarios

### Scenario 1: Complete Project Build

```python
async def test_complete_project_build_integration():
    """Test full project build from prompt to completion."""
    orchestrator = GAODevOrchestrator.create_default(
        project_root=tmp_path,
        api_key=TEST_API_KEY,
        mode="test"
    )

    # Execute full workflow
    result = await orchestrator.build_project(
        prompt="Build a todo app with React and FastAPI"
    )

    # Verify:
    assert result.status == "completed"
    assert result.artifacts_created > 0
    assert (tmp_path / "docs" / "PRD.md").exists()
    assert (tmp_path / "docs" / "ARCHITECTURE.md").exists()
    # ... more assertions
```

### Scenario 2: Story Creation and Implementation

```python
async def test_story_creation_and_implementation():
    """Test story workflow end-to-end."""
    orchestrator = GAODevOrchestrator.create_default(...)

    # Create story
    story = await orchestrator.create_and_implement_story(
        epic=1,
        story=1
    )

    # Verify:
    assert story.status == StoryStatus.DONE
    assert story.implementation_complete
    assert story.tests_passing
    # ... more assertions
```

### Scenario 3: Sandbox Workflow

```python
async def test_sandbox_benchmark_workflow():
    """Test sandbox benchmark execution."""
    manager = SandboxManager.create_default(...)

    # Initialize project
    project = await manager.init_project("test-project")
    assert project.status == ProjectStatus.INITIALIZED

    # Run benchmark
    result = await manager.run_benchmark("benchmarks/test.yaml")
    assert result.success

    # Verify run tracked
    runs = await manager.get_run_history("test-project")
    assert len(runs) == 1
```

### Scenario 4: Event Bus Integration

```python
async def test_event_bus_integration():
    """Test events published across components."""
    event_collector = EventCollector()
    orchestrator = GAODevOrchestrator.create_default(...)

    # Subscribe to all events
    orchestrator.event_bus.subscribe(Event, event_collector)

    # Execute workflow
    await orchestrator.build_project("Simple prompt")

    # Verify events published
    events = event_collector.get_events()
    assert any(isinstance(e, WorkflowSequenceStarted) for e in events)
    assert any(isinstance(e, WorkflowStepCompleted) for e in events)
    assert any(isinstance(e, StoryCreated) for e in events)
```

---

## Performance Benchmarks

### Benchmark Suite

1. **Workflow Execution Time**
   - Measure: Time to execute each workflow type
   - Target: < 5% increase from baseline

2. **Memory Usage**
   - Measure: Peak memory during execution
   - Target: < 10% increase from baseline

3. **Startup Time**
   - Measure: Time to initialize orchestrator
   - Target: < 1 second

4. **Concurrent Execution**
   - Measure: Multiple orchestrators running simultaneously
   - Target: No resource contention

### Benchmark Script

```python
async def benchmark_workflow_execution():
    """Benchmark workflow execution performance."""
    iterations = 10
    times = []

    for _ in range(iterations):
        start = time.time()
        orchestrator = GAODevOrchestrator.create_default(...)
        result = await orchestrator.build_project("Test prompt")
        end = time.time()
        times.append(end - start)

    avg_time = sum(times) / len(times)
    print(f"Average execution time: {avg_time:.2f}s")

    # Compare to baseline (if available)
    if baseline_time:
        variance = ((avg_time - baseline_time) / baseline_time) * 100
        print(f"Variance from baseline: {variance:.2f}%")
        assert variance < 5.0, "Performance regression detected"
```

---

## Implementation Steps

1. **Create Test Infrastructure**
   - Set up integration test fixtures
   - Create test project directories
   - Mock external dependencies (API calls)

2. **Write Orchestrator Integration Tests**
   - Test each workflow type
   - Test error scenarios
   - Test event publishing

3. **Write Sandbox Integration Tests**
   - Test project lifecycle
   - Test benchmark execution
   - Test run tracking

4. **Write Cross-Component Tests**
   - Test interactions between components
   - Test event bus integration
   - Test plugin integration

5. **Run Regression Tests**
   - Ensure all existing tests pass
   - Fix any broken tests
   - Update tests if API changed

6. **Performance Benchmarks**
   - Establish baseline (if not exists)
   - Run benchmarks after refactoring
   - Compare and document results

7. **Document Results**
   - Create test report
   - Document any issues found
   - Update Epic 6 status

---

## Definition of Done

- [ ] All integration tests written and passing
- [ ] All regression tests passing
- [ ] Performance benchmarks run
- [ ] < 5% performance variance
- [ ] No memory leaks detected
- [ ] Test coverage maintained at 80%+
- [ ] Test report documented
- [ ] Epic 6 validation complete
- [ ] Ready for production

---

## Test Report Template

```markdown
# Epic 6 Integration Test Report

**Date**: [date]
**Test Duration**: [duration]
**Tests Run**: [count]
**Tests Passed**: [count]
**Tests Failed**: [count]

## Test Results

### Orchestrator Integration Tests
- [✅/❌] create-prd workflow
- [✅/❌] create-story workflow
- [✅/❌] dev-story workflow
- [✅/❌] error handling
- [✅/❌] event publishing

### Sandbox Integration Tests
- [✅/❌] project initialization
- [✅/❌] benchmark execution
- [✅/❌] lifecycle transitions
- [✅/❌] run tracking

### Performance Benchmarks
- Workflow execution: [time] (baseline: [time], variance: [%])
- Memory usage: [MB] (baseline: [MB], variance: [%])
- Startup time: [ms]
- Concurrent execution: [pass/fail]

## Issues Found
[List any issues discovered during testing]

## Recommendations
[Any recommendations for improvements]

## Conclusion
[Overall assessment of refactoring quality]
```

---

**Related Stories**: All Epic 6 stories (6.1-6.8)
**Estimated Time**: 2 days
**Critical**: Final validation before production release!

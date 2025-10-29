# Story 7.2.3: Refactor Benchmark for Scale-Adaptive Testing

**Epic**: 7.2 - Workflow-Driven Core Architecture
**Story Points**: 4
**Status**: Ready
**Priority**: High

---

## User Story

As a **benchmark system**, I want to **be a passive test harness that calls GAO-Dev core**, so that **I measure GAO-Dev's autonomous performance without defining how it should work**.

---

## Context

Currently, the benchmark system orchestrates workflow execution, defining phases and calling agents. This story refactors it to be a passive observer that lets GAO-Dev decide and execute workflows autonomously.

**Problem**:
- BenchmarkRunner and WorkflowOrchestrator define workflow execution
- Benchmark config specifies phases and agent sequence
- GAO-Dev is told HOW to work instead of deciding autonomously
- Violates separation of concerns

**Solution**:
Simplify benchmark to:
1. Provide initial prompt to GAO-Dev
2. Call `gao_dev.execute_workflow(prompt)`
3. Collect metrics and performance data
4. Evaluate success criteria
5. Generate reports

---

## Acceptance Criteria

### AC1: Simplify Benchmark Config Format
- [ ] New config format with only `initial_prompt` and `success_criteria`
- [ ] Remove `phases` section from config (workflows define phases now)
- [ ] Optional `workflow_name` to force specific workflow
- [ ] Optional `timeout` and `expected_duration`
- [ ] Backward compatibility: Support old format with deprecation warning

### AC2: Refactor BenchmarkRunner
- [ ] Simplify `run_benchmark()` to call GAO-Dev core
- [ ] Call `gao_orchestrator.execute_workflow(initial_prompt)`
- [ ] Remove WorkflowOrchestrator initialization
- [ ] Collect WorkflowResult from GAO-Dev

### AC3: Metrics Collection (Keep)
- [ ] Keep all existing metrics collection
- [ ] Extract metrics from WorkflowResult
- [ ] Track: duration, artifacts created, commits, success
- [ ] Store metrics in database as before

### AC4: Success Criteria Evaluation
- [ ] Evaluate success_criteria against WorkflowResult
- [ ] Check: artifacts_exist, tests_pass, builds_successfully
- [ ] Generate pass/fail status
- [ ] Include criteria results in benchmark report

### AC5: Remove Workflow Orchestration Code
- [ ] Remove or deprecate WorkflowOrchestrator class
- [ ] Remove phase-based execution logic from benchmark
- [ ] Clean up imports and dependencies
- [ ] Mark as deprecated if backward compatibility needed

### AC6: Update Example Benchmarks
- [ ] Convert existing benchmarks to new format
- [ ] `greenfield-simple.yaml` - Just initial_prompt
- [ ] `todo-app-incremental.yaml` - Use story-based workflow
- [ ] Add comments explaining new format

### AC7: Tests
- [ ] Unit tests for simplified BenchmarkRunner
- [ ] Test with various workflow types
- [ ] Test metrics collection from WorkflowResult
- [ ] Test success criteria evaluation
- [ ] >80% code coverage

---

## Technical Details

### New Benchmark Config Format

```yaml
# sandbox/benchmarks/greenfield-simple-v2.yaml

benchmark:
  name: "greenfield-simple"
  description: "Build a simple todo application from scratch"

  # The ONLY thing benchmark provides: initial prompt
  initial_prompt: |
    Build a simple todo application with the following features:
    - Add, edit, delete tasks
    - Mark tasks as complete
    - Filter by status (all, active, completed)
    - Persist to database
    - RESTful API
    - Python/FastAPI

  # Optional: Force specific workflow (otherwise GAO-Dev auto-selects)
  # workflow_name: "greenfield-full-development"

  # Expected duration (for reporting, not timeout)
  expected_duration_minutes: 120

  # Timeout (actual hard limit)
  timeout_seconds: 7200

  # Success criteria (evaluated after completion)
  success_criteria:
    artifacts_exist:
      - "docs/PRD.md"
      - "docs/ARCHITECTURE.md"
      - "src/**/*.py"
      - "tests/**/*.py"

    tests_pass: true
    builds_successfully: true

    min_test_coverage: 80

    quality_checks:
      - type: "linting"
        tool: "ruff"
        must_pass: true

      - type: "type_checking"
        tool: "mypy"
        must_pass: true

  # Optional: Metadata for reporting
  metadata:
    project_type: "greenfield"
    complexity: "simple"
    language: "python"
    framework: "fastapi"
```

### Old Format (Deprecated but Supported)

```yaml
# sandbox/benchmarks/greenfield-simple-old.yaml

benchmark:
  name: "greenfield-simple-old"
  initial_prompt: "Build todo app..."

  # DEPRECATED: phases are now defined by workflow, not benchmark
  phases:
    - phase_name: "Product Requirements"
      agent: "John"
      expected_duration_minutes: 20
    # ... (old format)

  success_criteria:
    artifacts_exist: [...]
```

### Refactored BenchmarkRunner

```python
# gao_dev/sandbox/benchmark/runner.py

from datetime import datetime
import asyncio
from typing import Optional

from ...orchestrator import GAODevOrchestrator
from ...orchestrator.workflow_results import WorkflowResult
from .config import BenchmarkConfig
from .validator import BenchmarkValidator

class BenchmarkRunner:
    """
    Passive test harness for GAO-Dev benchmarking.

    Provides initial prompt to GAO-Dev and measures performance.
    Does NOT orchestrate workflow execution.
    """

    def __init__(
        self,
        config: BenchmarkConfig,
        project_path: Path,
        api_key: Optional[str] = None
    ):
        self.config = config
        self.project_path = project_path
        self.api_key = api_key
        self.logger = structlog.get_logger().bind(
            component="benchmark_runner",
            benchmark=config.name
        )

    async def run_benchmark(self) -> BenchmarkResult:
        """
        Run benchmark by calling GAO-Dev core.

        Flow:
        1. Initialize GAO-Dev orchestrator
        2. Provide initial prompt
        3. Let GAO-Dev select and execute workflow autonomously
        4. Collect metrics from WorkflowResult
        5. Evaluate success criteria
        6. Return benchmark results
        """
        self.logger.info(
            "benchmark_started",
            prompt=self.config.initial_prompt[:100]
        )

        # Start timer
        start_time = datetime.now()

        try:
            # Initialize GAO-Dev (autonomous system)
            gao_dev = GAODevOrchestrator(
                project_root=self.project_path,
                api_key=self.api_key
            )

            # Execute workflow autonomously
            # GAO-Dev decides HOW to work, we just provide WHAT to build
            workflow_result: WorkflowResult = await gao_dev.execute_workflow(
                initial_prompt=self.config.initial_prompt,
                workflow=self._get_forced_workflow() if self.config.workflow_name else None
            )

            # Collect metrics from workflow execution
            duration = (datetime.now() - start_time).total_seconds()
            metrics = self._extract_metrics(workflow_result, duration)

            # Evaluate success criteria
            validator = BenchmarkValidator(
                project_path=self.project_path,
                config=self.config
            )
            validation_result = await validator.validate(workflow_result)

            # Create benchmark result
            result = BenchmarkResult(
                benchmark_name=self.config.name,
                success=workflow_result.success and validation_result.passed,
                workflow_name=workflow_result.workflow_name,
                duration_seconds=duration,
                metrics=metrics,
                validation_result=validation_result,
                workflow_result=workflow_result
            )

            self.logger.info(
                "benchmark_completed",
                success=result.success,
                duration=duration,
                workflow=workflow_result.workflow_name
            )

            return result

        except asyncio.TimeoutError:
            self.logger.error("benchmark_timeout")
            return self._create_timeout_result(start_time)

        except Exception as e:
            self.logger.error("benchmark_failed", error=str(e), exc_info=True)
            return self._create_error_result(start_time, e)

    def _get_forced_workflow(self) -> Optional[Workflow]:
        """Get forced workflow if specified in config."""
        if not self.config.workflow_name:
            return None

        # Load workflow from registry
        # (This allows explicit workflow testing)
        pass

    def _extract_metrics(
        self,
        workflow_result: WorkflowResult,
        duration: float
    ) -> Dict[str, Any]:
        """
        Extract metrics from workflow execution.

        Converts WorkflowResult to benchmark metrics.
        """
        return {
            "duration_seconds": duration,
            "total_steps": workflow_result.total_steps,
            "successful_steps": workflow_result.successful_steps,
            "total_artifacts": workflow_result.total_artifacts,
            "commits": [
                step.commit_hash for step in workflow_result.step_results
                if step.commit_hash
            ],
            # Can extract tokens/cost if available from workflow_result
        }

    def _create_timeout_result(self, start_time: datetime) -> BenchmarkResult:
        """Create result for timeout."""
        return BenchmarkResult(
            benchmark_name=self.config.name,
            success=False,
            duration_seconds=(datetime.now() - start_time).total_seconds(),
            error="Benchmark exceeded timeout"
        )

    def _create_error_result(
        self,
        start_time: datetime,
        error: Exception
    ) -> BenchmarkResult:
        """Create result for error."""
        return BenchmarkResult(
            benchmark_name=self.config.name,
            success=False,
            duration_seconds=(datetime.now() - start_time).total_seconds(),
            error=str(error)
        )
```

### Simplified Flow Diagram

```
BEFORE (Wrong):
User → Benchmark Config (defines phases) → BenchmarkRunner
         → WorkflowOrchestrator → Calls agents in order
         → GAO-Dev (passive) → Results

AFTER (Correct):
User → Benchmark Config (initial_prompt only) → BenchmarkRunner
         → GAO-Dev.execute_workflow(prompt)
            → GAO-Dev selects workflow
            → GAO-Dev executes autonomously
            → GAO-Dev calls agents
         → WorkflowResult → BenchmarkRunner
         → Metrics & Validation → Results
```

---

## Testing Strategy

### Unit Tests (`tests/test_benchmark_runner.py`)

```python
import pytest
from unittest.mock import Mock, AsyncMock
from gao_dev.sandbox.benchmark.runner import BenchmarkRunner
from gao_dev.orchestrator.workflow_results import WorkflowResult, WorkflowStatus

@pytest.mark.asyncio
async def test_benchmark_runner_simplified():
    """Test simplified benchmark runner calls GAO-Dev core."""
    config = Mock()
    config.name = "test-benchmark"
    config.initial_prompt = "Build todo app"
    config.workflow_name = None

    runner = BenchmarkRunner(
        config=config,
        project_path=Path("/tmp/test")
    )

    # Mock GAO-Dev execute_workflow
    mock_workflow_result = WorkflowResult(
        workflow_name="greenfield",
        initial_prompt="Build todo app",
        status=WorkflowStatus.COMPLETED,
        start_time=datetime.now()
    )

    # Runner should call execute_workflow and collect metrics
    result = await runner.run_benchmark()

    assert result.success
    assert result.workflow_name == "greenfield"

@pytest.mark.asyncio
async def test_benchmark_extracts_metrics():
    """Test metrics extraction from WorkflowResult."""
    # Test that runner properly extracts metrics from WorkflowResult
    pass

@pytest.mark.asyncio
async def test_benchmark_evaluates_success_criteria():
    """Test success criteria evaluation."""
    # Test that runner checks artifacts_exist, tests_pass, etc.
    pass
```

---

## Migration Strategy

### Phase 1: Add Support for New Format
1. Update BenchmarkConfig to support both old and new formats
2. Add deprecation warning for old format
3. Keep existing WorkflowOrchestrator for backward compatibility

### Phase 2: Refactor Runner
1. Add simplified run path for new format
2. Keep old path for deprecated format
3. Extract common metrics collection

### Phase 3: Update Benchmarks
1. Convert all example benchmarks to new format
2. Add `-v2` suffix during transition
3. Document migration guide

### Phase 4: Remove Old Code (Future)
1. After transition period, remove WorkflowOrchestrator
2. Remove old config format support
3. Clean up codebase

---

## Dependencies

- **Story 7.2.2**: Workflow Executor (REQUIRED - execute_workflow method)
- **WorkflowResult**: Must return comprehensive metrics
- **BenchmarkValidator**: Must evaluate success criteria (EXISTS)

---

## Definition of Done

- [ ] New benchmark config format documented and supported
- [ ] BenchmarkRunner refactored to call GAO-Dev core
- [ ] WorkflowOrchestrator deprecated or removed
- [ ] Metrics collection updated to use WorkflowResult
- [ ] Success criteria evaluation implemented
- [ ] Example benchmarks converted to new format
- [ ] Backward compatibility with deprecation warnings
- [ ] Unit tests for simplified runner (>80% coverage)
- [ ] Integration test with real workflow
- [ ] Type hints complete (mypy passes)
- [ ] Documentation updated
- [ ] Code review completed
- [ ] Story committed atomically to git

---

## Story Enhancement Notes

**Original Story Points**: 3 points
**Updated Story Points**: 4 points (+1 point)

**Reason for Increase**:
- Added scale level support in benchmark config
- Added testing for workflow sequences (not just single workflows)
- Added metrics for multi-workflow execution
- Increased complexity to support scale-adaptive benchmarking

---

## Out of Scope

- Real-time progress streaming (future enhancement)
- Benchmark comparison UI (Epic 5 already handles this)
- Distributed benchmark execution (future)

---

## Notes

- This completes the architectural refactor - GAO-Dev is now truly autonomous
- Benchmark becomes simple: provide prompt (with optional scale level), collect results
- Focus on clean separation: benchmark TESTS, GAO-Dev WORKS
- Keep metrics collection comprehensive for analysis
- Backward compatibility important during transition
- Scale-adaptive testing validates Brian's workflow selection

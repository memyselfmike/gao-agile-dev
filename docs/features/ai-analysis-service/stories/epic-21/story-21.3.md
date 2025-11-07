# Story 21.3: Update Brian Initialization Points

**Epic**: 21 - AI Analysis Service & Brian Provider Abstraction
**Story Points**: 3
**Status**: Blocked (depends on Stories 21.1, 21.2)
**Priority**: High
**Assignee**: TBD

---

## User Story

As a **developer**, I want **all locations that create Brian to inject AIAnalysisService**, so that **Brian works correctly with the new provider abstraction across the entire codebase**.

---

## Context

After refactoring Brian to use AIAnalysisService (Story 21.2), all places that instantiate Brian need to be updated to:
1. Create an AIAnalysisService instance
2. Pass it to Brian's constructor
3. Share ProcessExecutor between agents and analysis service

**Affected Components**:
- GAODevOrchestrator (main orchestrator)
- BenchmarkRunner (benchmark system)
- Tests (unit and integration tests)
- CLI commands (if Brian used directly)

---

## Acceptance Criteria

### AC1: Update GAODevOrchestrator
- [ ] Create AIAnalysisService in GAODevOrchestrator.__init__
- [ ] Use existing ProcessExecutor instance
- [ ] Pass analysis_service to Brian constructor
- [ ] Remove any old API key passing logic
- [ ] Test that orchestrator initializes correctly

### AC2: Update BenchmarkRunner
- [ ] Create AIAnalysisService in BenchmarkRunner
- [ ] Share ProcessExecutor with agent execution
- [ ] Pass analysis_service to Brian
- [ ] Verify benchmarks can run

### AC3: Update All Tests
- [ ] Update unit tests that create Brian directly
- [ ] Update integration tests
- [ ] Mock AIAnalysisService where appropriate
- [ ] All tests pass

### AC4: Configuration Flow
- [ ] Model configuration still works:
  - GAO_DEV_MODEL environment variable
  - Brian's YAML config
  - Default fallback
- [ ] ProcessExecutor uses correct provider
- [ ] Logging shows correct provider being used

### AC5: No Regression
- [ ] All existing functionality works
- [ ] Workflow selection works
- [ ] Scale-adaptive routing works
- [ ] Benchmarks run successfully

---

## Technical Details

### Files to Update

```
gao_dev/
├── orchestrator/
│   └── orchestrator.py           # MODIFIED - Create and pass service
│
├── sandbox/
│   └── benchmark/
│       └── orchestrator.py       # MODIFIED - Create and pass service
│
└── cli/
    └── commands.py               # CHECK - Brian used directly?

tests/
├── unit/
│   └── orchestrator/
│       └── test_*.py             # MODIFIED - Mock service
└── integration/
    └── test_*.py                 # MODIFIED - Real or mocked service
```

### GAODevOrchestrator Changes

#### Before
```python
# gao_dev/orchestrator/orchestrator.py

class GAODevOrchestrator:
    def __init__(
        self,
        workflow_registry: WorkflowRegistry,
        executor: ProcessExecutor,
        ...
    ):
        # Create Brian with API key
        self.brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model=brian_model
        )
```

#### After
```python
# gao_dev/orchestrator/orchestrator.py

from ..core.services import AIAnalysisService

class GAODevOrchestrator:
    def __init__(
        self,
        workflow_registry: WorkflowRegistry,
        executor: ProcessExecutor,
        ...
    ):
        # Create analysis service with shared executor
        self.analysis_service = AIAnalysisService(
            executor=executor,
            default_model=brian_model
        )

        # Create Brian with analysis service
        self.brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=self.analysis_service,
            model=brian_model
        )
```

### BenchmarkRunner Changes

#### Before
```python
# gao_dev/sandbox/benchmark/orchestrator.py

class BenchmarkRunner:
    def __init__(self, config: BenchmarkConfig):
        # Create orchestrator
        self.orchestrator = GAODevOrchestrator(...)
```

#### After
```python
# gao_dev/sandbox/benchmark/orchestrator.py

class BenchmarkRunner:
    def __init__(self, config: BenchmarkConfig):
        # ProcessExecutor created somewhere
        executor = self._create_executor()

        # Analysis service shares executor
        analysis_service = AIAnalysisService(executor=executor)

        # Create orchestrator with service
        self.orchestrator = GAODevOrchestrator(
            executor=executor,
            analysis_service=analysis_service,  # If needed
            ...
        )
```

**Note**: Exact changes depend on how GAODevOrchestrator is currently instantiated in the benchmark system.

### Test Updates

```python
# tests/unit/orchestrator/test_orchestrator.py

@pytest.fixture
def mock_analysis_service():
    """Mock AIAnalysisService for tests."""
    service = Mock(spec=AIAnalysisService)
    service.analyze = AsyncMock(return_value=AnalysisResult(
        response='{"scale_level": 2}',
        model_used="test-model",
        tokens_used=100,
        duration_ms=500
    ))
    return service


@pytest.fixture
def orchestrator(mock_workflow_registry, mock_executor, mock_analysis_service):
    """Create orchestrator with mocked dependencies."""
    # Create orchestrator (which creates Brian internally)
    orch = GAODevOrchestrator(
        workflow_registry=mock_workflow_registry,
        executor=mock_executor,
        # ... other params
    )

    # Override Brian's analysis_service with mock
    orch.brian.analysis_service = mock_analysis_service

    return orch
```

---

## Implementation Checklist

### Phase 1: Find All Brian Instantiations
- [ ] Search codebase for `BrianOrchestrator(`
- [ ] Document all instantiation locations
- [ ] Identify which need updates

### Phase 2: Update Orchestrator
- [ ] Create AIAnalysisService in GAODevOrchestrator
- [ ] Pass to Brian constructor
- [ ] Test orchestrator initialization
- [ ] Verify workflow selection works

### Phase 3: Update Benchmark System
- [ ] Find Brian usage in benchmark code
- [ ] Update to use AIAnalysisService
- [ ] Test benchmark execution
- [ ] Verify metrics collection works

### Phase 4: Update Tests
- [ ] Update unit tests
- [ ] Update integration tests
- [ ] Add tests for service injection
- [ ] Verify all tests pass

### Phase 5: Configuration Validation
- [ ] Test with GAO_DEV_MODEL environment variable
- [ ] Test with default model
- [ ] Test with YAML config
- [ ] Verify logging shows correct model

---

## Testing Strategy

### Unit Tests
```python
def test_orchestrator_creates_analysis_service(mock_executor, mock_workflow_registry):
    """Test that orchestrator creates analysis service."""
    orch = GAODevOrchestrator(
        workflow_registry=mock_workflow_registry,
        executor=mock_executor
    )

    assert orch.analysis_service is not None
    assert isinstance(orch.analysis_service, AIAnalysisService)
    assert orch.brian.analysis_service is orch.analysis_service


def test_orchestrator_shares_executor():
    """Test that analysis service shares executor with agents."""
    executor = Mock(spec=ProcessExecutor)
    orch = GAODevOrchestrator(executor=executor, ...)

    # Analysis service should use same executor
    assert orch.analysis_service.executor is executor
```

### Integration Tests
```python
async def test_end_to_end_with_real_providers():
    """Test Brian with real providers."""
    # Setup with real ProcessExecutor
    executor = ProcessExecutor(provider="opencode-sdk")
    analysis_service = AIAnalysisService(executor=executor)

    brian = BrianOrchestrator(
        workflow_registry=registry,
        analysis_service=analysis_service,
        model="deepseek-r1"
    )

    # Test analysis
    result = await brian.analyze_prompt("Build todo app")

    assert result.scale_level > 0
```

---

## Definition of Done

- [ ] All Brian instantiations updated
- [ ] AIAnalysisService created and passed correctly
- [ ] ProcessExecutor shared appropriately
- [ ] All tests pass
- [ ] Configuration flow works
- [ ] No functional regression
- [ ] Code reviewed and approved

---

## Dependencies

- **Story 21.1** (required): AIAnalysisService must exist
- **Story 21.2** (required): Brian must be refactored first
- **GAODevOrchestrator** (exists): Main orchestrator
- **BenchmarkRunner** (exists): Benchmark system
- **ProcessExecutor** (exists): Provider abstraction

---

## Migration Risk Assessment

**Low Risk**:
- Changes are localized to initialization code
- No business logic changes
- Easy to revert if issues arise

**Mitigation**:
- Update one component at a time
- Test after each update
- Keep existing tests as regression suite

---

## Notes

- This is primarily a "wiring" story - connecting components
- No new functionality, just dependency injection
- Should be straightforward once Stories 21.1 and 21.2 are complete
- Focus on maintaining existing behavior

---

## Search Patterns

Use these to find all Brian instantiations:

```bash
# Find all Brian instantiations
grep -r "BrianOrchestrator(" gao_dev/

# Find all imports
grep -r "from.*brian_orchestrator import" gao_dev/

# Find test usage
grep -r "BrianOrchestrator" tests/
```

---

## Related Documents

- **Story 21.1**: Create AI Analysis Service (prerequisite)
- **Story 21.2**: Refactor Brian (prerequisite)
- **Story 21.4**: Integration Testing (follow-up)
- **Epic 21 Plan**: `docs/features/ai-analysis-service/EPIC-21-PLAN.md`
- **GAODevOrchestrator**: `gao_dev/orchestrator/orchestrator.py`
- **BenchmarkRunner**: `gao_dev/sandbox/benchmark/orchestrator.py`

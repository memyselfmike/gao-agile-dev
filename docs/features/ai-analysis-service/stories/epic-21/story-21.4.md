# Story 21.4: Integration Testing with Multiple Providers

**Epic**: 21 - AI Analysis Service & Brian Provider Abstraction
**Story Points**: 5
**Status**: Blocked (depends on Stories 21.1, 21.2, 21.3)
**Priority**: High
**Assignee**: TBD

---

## User Story

As a **developer**, I want **comprehensive integration tests with all providers**, so that **I can be confident the AI Analysis Service abstraction works correctly with Claude Code, OpenCode, and local models**.

---

## Context

After implementing AIAnalysisService and refactoring Brian, we need to validate that:
1. Service works with all providers (Claude Code, OpenCode, Anthropic)
2. Brian works correctly with each provider
3. Model selection works (env var, config, explicit)
4. Error scenarios are handled gracefully
5. Performance is acceptable (<5% overhead)

**Testing Strategy**:
- Unit tests: Mock service/executor (already in Stories 21.1-21.3)
- Integration tests: Real providers, real models
- Performance tests: Measure overhead vs. direct API calls

---

## Acceptance Criteria

### AC1: Integration Test Infrastructure
- [ ] Create `tests/integration/test_brian_provider_abstraction.py`
- [ ] Setup fixtures for each provider
- [ ] Environment configuration helpers
- [ ] Cleanup after tests

### AC2: Test with Claude Code Provider
- [ ] Test Brian + AIAnalysisService + Claude Code
- [ ] Verify workflow selection works
- [ ] Check response parsing
- [ ] Validate metrics captured

### AC3: Test with OpenCode Provider
- [ ] Test Brian + AIAnalysisService + OpenCode
- [ ] Works with Ollama backend
- [ ] Handles deepseek-r1 model
- [ ] Same functionality as Claude

### AC4: Test with Mocked Provider
- [ ] Test with fully mocked provider
- [ ] Fast test execution
- [ ] Validates abstraction layer
- [ ] No external dependencies

### AC5: Model Selection Tests
- [ ] Test GAO_DEV_MODEL environment variable
- [ ] Test model from YAML config
- [ ] Test explicit model parameter
- [ ] Test default model fallback
- [ ] Verify priority order

### AC6: Error Handling Tests
- [ ] Test API failures (timeout, 5xx errors)
- [ ] Test invalid model name
- [ ] Test malformed JSON response
- [ ] Test rate limiting
- [ ] Verify error messages and logging

### AC7: Performance Benchmarks
- [ ] Measure service overhead
- [ ] Compare direct API vs. service
- [ ] Target: <5% overhead
- [ ] Document performance metrics

### AC8: Cross-Provider Consistency
- [ ] Same prompts work with all providers
- [ ] Responses parsed consistently
- [ ] Error handling consistent
- [ ] Logging consistent

---

## Technical Details

### Test File Structure

```
tests/
├── integration/
│   ├── test_brian_provider_abstraction.py  # NEW - Main integration tests
│   ├── conftest.py                         # MODIFIED - Add fixtures
│   └── providers/                          # NEW - Provider-specific tests
│       ├── test_claude_code.py
│       ├── test_opencode.py
│       └── test_mock_provider.py
│
└── performance/                            # NEW - Performance tests
    └── test_analysis_service_overhead.py
```

### Integration Test Implementation

```python
# tests/integration/test_brian_provider_abstraction.py

import pytest
import os
from gao_dev.core.services import AIAnalysisService
from gao_dev.core.process_executor import ProcessExecutor
from gao_dev.orchestrator.brian_orchestrator import BrianOrchestrator
from gao_dev.core.workflow_registry import WorkflowRegistry


@pytest.fixture
def workflow_registry():
    """Real workflow registry."""
    from pathlib import Path
    workflows_dir = Path(__file__).parent.parent.parent / "gao_dev" / "workflows"
    return WorkflowRegistry(workflows_dir)


@pytest.fixture
def claude_code_provider():
    """Setup Claude Code provider."""
    provider = ProcessExecutor(provider="claude-code")
    return provider


@pytest.fixture
def opencode_provider():
    """Setup OpenCode provider (Ollama + deepseek-r1)."""
    # Check if Ollama is running
    pytest.importorskip("ollama")  # Skip if ollama not available

    provider = ProcessExecutor(provider="opencode-sdk")
    return provider


@pytest.fixture
def mock_provider():
    """Setup mocked provider."""
    from unittest.mock import Mock, AsyncMock

    provider = Mock(spec=ProcessExecutor)
    provider.execute = AsyncMock()
    return provider


class TestBrianWithClaudeCode:
    """Test Brian with Claude Code provider."""

    async def test_basic_workflow_selection(self, workflow_registry, claude_code_provider):
        """Test basic workflow selection with Claude."""
        # Create service
        analysis_service = AIAnalysisService(
            executor=claude_code_provider,
            default_model="claude-sonnet-4-5-20250929"
        )

        # Create Brian
        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=analysis_service
        )

        # Test analysis
        result = await brian.analyze_prompt("Build a simple todo application")

        # Verify
        assert result.scale_level in [0, 1, 2, 3, 4]
        assert result.workflows is not None
        assert len(result.workflows) > 0

    async def test_scale_level_2_project(self, workflow_registry, claude_code_provider):
        """Test Level 2 project classification."""
        analysis_service = AIAnalysisService(executor=claude_code_provider)
        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=analysis_service
        )

        result = await brian.analyze_prompt(
            "Create a todo application with user authentication, "
            "CRUD operations, and task filtering"
        )

        # Should be Level 2 (small feature, 3-8 stories)
        assert result.scale_level == 2


class TestBrianWithOpenCode:
    """Test Brian with OpenCode + Ollama + deepseek-r1."""

    @pytest.mark.integration
    @pytest.mark.requires_ollama
    async def test_deepseek_r1_analysis(self, workflow_registry, opencode_provider):
        """Test Brian with local deepseek-r1 model."""
        # Create service with deepseek-r1
        analysis_service = AIAnalysisService(
            executor=opencode_provider,
            default_model="deepseek-r1"
        )

        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=analysis_service,
            model="deepseek-r1"
        )

        # Test analysis
        result = await brian.analyze_prompt("Build a todo app")

        # Should work with local model
        assert result.scale_level is not None
        assert result.workflows is not None

    @pytest.mark.integration
    async def test_opencode_performance(self, workflow_registry, opencode_provider):
        """Test performance with local model."""
        import time

        analysis_service = AIAnalysisService(
            executor=opencode_provider,
            default_model="deepseek-r1"
        )

        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=analysis_service
        )

        start = time.time()
        result = await brian.analyze_prompt("Build a CRM system")
        duration = time.time() - start

        # Should complete in reasonable time
        assert duration < 30.0  # 30 seconds max
        assert result.scale_level == 3  # Medium-large project


class TestModelSelection:
    """Test model selection priority."""

    async def test_env_variable_override(self, workflow_registry, mock_provider):
        """Test GAO_DEV_MODEL environment variable."""
        os.environ["GAO_DEV_MODEL"] = "deepseek-r1"

        analysis_service = AIAnalysisService(executor=mock_provider)
        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=analysis_service
        )

        # Should use env var model
        assert brian.model == "deepseek-r1"

        del os.environ["GAO_DEV_MODEL"]

    async def test_explicit_model_parameter(self, workflow_registry, mock_provider):
        """Test explicit model parameter."""
        analysis_service = AIAnalysisService(executor=mock_provider)
        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=analysis_service,
            model="explicit-model"
        )

        assert brian.model == "explicit-model"


class TestErrorHandling:
    """Test error scenarios."""

    async def test_api_timeout(self, workflow_registry):
        """Test API timeout handling."""
        from gao_dev.exceptions.analysis_exceptions import AnalysisError
        from unittest.mock import Mock, AsyncMock

        # Mock provider that times out
        provider = Mock(spec=ProcessExecutor)
        provider.execute = AsyncMock(side_effect=TimeoutError("API timeout"))

        analysis_service = AIAnalysisService(executor=provider)
        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=analysis_service
        )

        with pytest.raises(AnalysisError) as exc_info:
            await brian.analyze_prompt("Test")

        assert "timeout" in str(exc_info.value).lower()

    async def test_invalid_model(self, workflow_registry, mock_provider):
        """Test invalid model name."""
        from gao_dev.exceptions.analysis_exceptions import InvalidModelError

        mock_provider.execute.side_effect = InvalidModelError("Model not found")

        analysis_service = AIAnalysisService(executor=mock_provider)
        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=analysis_service,
            model="invalid-model-xyz"
        )

        with pytest.raises(InvalidModelError):
            await brian.analyze_prompt("Test")


class TestPerformance:
    """Performance benchmarks."""

    async def test_service_overhead(self, workflow_registry, claude_code_provider):
        """Measure overhead from service abstraction."""
        import time

        # Test with service
        analysis_service = AIAnalysisService(executor=claude_code_provider)
        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=analysis_service
        )

        start = time.time()
        await brian.analyze_prompt("Build todo app")
        service_duration = time.time() - start

        # Should be fast (< 5 seconds for analysis)
        assert service_duration < 5.0

        # Log for comparison
        print(f"Service overhead: {service_duration:.2f}s")
```

---

## Test Execution Strategy

### Phase 1: Mock Provider Tests (Fast)
```bash
pytest tests/integration/test_brian_provider_abstraction.py::TestMocked -v
```
- Runs in seconds
- No external dependencies
- Validates abstraction layer

### Phase 2: Claude Code Tests (Requires API)
```bash
export ANTHROPIC_API_KEY="your-key"
pytest tests/integration/test_brian_provider_abstraction.py::TestBrianWithClaudeCode -v
```
- Requires Anthropic API key
- Tests real provider
- ~10-30 seconds

### Phase 3: OpenCode Tests (Requires Ollama)
```bash
export AGENT_PROVIDER="opencode-sdk"
export GAO_DEV_MODEL="deepseek-r1"
pytest tests/integration/test_brian_provider_abstraction.py::TestBrianWithOpenCode -v -m requires_ollama
```
- Requires Ollama running
- Requires deepseek-r1 model
- Tests local model usage
- Slower (local inference)

### Phase 4: Performance Tests
```bash
pytest tests/performance/ -v --benchmark-only
```
- Measures overhead
- Compares providers
- Documents metrics

---

## Environment Setup

### For OpenCode Tests

```bash
# Install and start Ollama
ollama pull deepseek-r1:8b

# Start OpenCode server
opencode start

# Verify setup
ollama list  # Should show deepseek-r1
curl http://localhost:11434/api/tags  # Should return models

# Run tests
export AGENT_PROVIDER=opencode-sdk
export GAO_DEV_MODEL=deepseek-r1
pytest tests/integration/ -v -m requires_ollama
```

---

## Definition of Done

- [ ] Integration tests implemented for all providers
- [ ] Tests pass with Claude Code provider
- [ ] Tests pass with OpenCode + deepseek-r1 (if Ollama available)
- [ ] Tests pass with mocked provider
- [ ] Model selection tests pass
- [ ] Error handling tests pass
- [ ] Performance benchmarks documented
- [ ] CI/CD integration (skip Ollama tests if not available)
- [ ] Documentation updated

---

## Dependencies

- **Story 21.1** (required): AIAnalysisService
- **Story 21.2** (required): Brian refactored
- **Story 21.3** (required): Initialization updated
- **pytest** (installed): Test framework
- **pytest-asyncio** (installed): Async test support
- **Ollama** (optional): For local model tests

---

## CI/CD Considerations

```yaml
# .github/workflows/test.yml
- name: Integration Tests (Claude Code)
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: pytest tests/integration/ -v -m "not requires_ollama"

- name: Integration Tests (OpenCode)
  # Only run if Ollama is setup
  if: env.OLLAMA_AVAILABLE == 'true'
  run: pytest tests/integration/ -v -m requires_ollama
```

---

## Related Documents

- **Story 21.1**: Create AI Analysis Service (prerequisite)
- **Story 21.2**: Refactor Brian (prerequisite)
- **Story 21.3**: Update Initialization (prerequisite)
- **Story 21.5**: Benchmark Validation (uses these tests)
- **Epic 21 Plan**: `docs/features/ai-analysis-service/EPIC-21-PLAN.md`

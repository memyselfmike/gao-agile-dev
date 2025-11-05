# Story 11.14: Comprehensive Testing & QA

**Epic**: Epic 11 - Agent Provider Abstraction
**Status**: Not Started
**Priority**: P0 (Critical)
**Estimated Effort**: 13 story points
**Owner**: Murat (Test Architect) + Amelia (Developer)
**Created**: 2025-11-04
**Dependencies**: All Phase 1-3 stories

---

## User Story

**As a** GAO-Dev quality assurance lead
**I want** comprehensive test coverage across all provider implementations
**So that** we can confidently release the provider abstraction to production

---

## Acceptance Criteria

### AC1: Unit Test Coverage
- ✅ All provider implementations tested (100% coverage)
- ✅ All strategies tested (selection, performance, cost)
- ✅ Factory and selector tested
- ✅ Configuration loading tested
- ✅ Error handling tested
- ✅ Edge cases covered

### AC2: Integration Test Suite
- ✅ End-to-end provider usage tests
- ✅ ProcessExecutor integration tests
- ✅ Multi-provider workflow tests
- ✅ Configuration override tests
- ✅ Plugin system integration tests
- ✅ All tests pass

### AC3: Provider Compatibility Matrix Tests
- ✅ Cross-provider functionality tests
- ✅ Same task executed on all providers
- ✅ Output comparison tests
- ✅ Tool compatibility tests
- ✅ Model support tests
- ✅ Matrix report generated

### AC4: Performance Test Suite
- ✅ Initialization benchmarks
- ✅ Streaming latency tests
- ✅ Memory usage tests
- ✅ Caching effectiveness tests
- ✅ Regression detection tests
- ✅ CI performance gates

### AC5: Security & Sandboxing Tests
- ✅ Plugin sandboxing tests
- ✅ Permission enforcement tests
- ✅ Malicious plugin detection
- ✅ Resource limit tests
- ✅ API key validation tests
- ✅ All security tests pass

### AC6: Backward Compatibility Tests
- ✅ Legacy ProcessExecutor API tests
- ✅ Existing workflow tests still pass
- ✅ Configuration backward compatibility
- ✅ No breaking changes detected
- ✅ 400+ existing tests pass unchanged

### AC7: Error Scenario Tests
- ✅ Missing API keys
- ✅ Invalid providers
- ✅ Network failures
- ✅ Timeout scenarios
- ✅ Rate limiting
- ✅ Malformed configurations
- ✅ CLI not found

### AC8: Multi-Platform Tests
- ✅ Windows tests pass
- ✅ macOS tests pass
- ✅ Linux tests pass
- ✅ Platform-specific issues identified
- ✅ Workarounds documented

### AC9: Stress & Load Tests
- ✅ Concurrent provider usage
- ✅ High-volume streaming
- ✅ Cache saturation tests
- ✅ Memory leak detection
- ✅ Connection pool exhaustion
- ✅ System remains stable

### AC10: User Acceptance Testing
- ✅ Test scenarios defined
- ✅ Manual testing completed
- ✅ User feedback incorporated
- ✅ Known issues documented
- ✅ Workarounds provided

### AC11: CI/CD Integration
- ✅ All tests run in CI
- ✅ Performance tests nightly
- ✅ Security scans pass
- ✅ Type checking passes (MyPy strict)
- ✅ Linting passes (Ruff)
- ✅ Code coverage >90%

### AC12: Test Documentation
- ✅ Test strategy documented
- ✅ Test execution guide
- ✅ Troubleshooting failed tests
- ✅ Adding new tests guide
- ✅ CI configuration documented

---

## Technical Details

### File Structure
```
tests/
├── unit/
│   └── providers/
│       ├── test_base_provider.py
│       ├── test_claude_code_provider.py
│       ├── test_opencode_provider.py
│       ├── test_direct_api_provider.py
│       ├── test_provider_factory.py
│       ├── test_provider_selector.py
│       ├── test_selection_strategies.py
│       ├── test_provider_cache.py
│       └── test_provider_plugins.py
│
├── integration/
│   └── providers/
│       ├── test_provider_integration.py
│       ├── test_process_executor.py
│       ├── test_multi_provider_workflow.py
│       ├── test_configuration_loading.py
│       └── test_plugin_integration.py
│
├── performance/
│   └── providers/
│       ├── test_provider_performance.py
│       ├── benchmark_initialization.py
│       ├── benchmark_streaming.py
│       └── benchmark_caching.py
│
├── security/
│   └── providers/
│       ├── test_plugin_sandboxing.py
│       ├── test_permissions.py
│       └── test_api_key_validation.py
│
├── compatibility/
│   └── providers/
│       ├── test_provider_parity.py
│       ├── test_backward_compatibility.py
│       └── test_cross_provider.py
│
├── stress/
│   └── providers/
│       ├── test_concurrent_usage.py
│       ├── test_memory_leaks.py
│       └── test_connection_pool.py
│
└── platform/
    └── providers/
        ├── test_windows.py
        ├── test_macos.py
        └── test_linux.py

docs/testing/
├── provider-test-strategy.md          # NEW: Test strategy
├── provider-test-execution.md         # NEW: Execution guide
└── provider-test-troubleshooting.md   # NEW: Troubleshooting
```

### Implementation Approach

#### Step 1: Comprehensive Unit Tests

**File**: `tests/unit/providers/test_provider_factory.py`

```python
"""Comprehensive tests for ProviderFactory."""

import pytest
from unittest.mock import Mock, patch

from gao_dev.core.providers.factory import ProviderFactory
from gao_dev.core.providers.base import ProviderError
from gao_dev.core.providers.claude_code import ClaudeCodeProvider


class TestProviderFactory:
    """Test ProviderFactory functionality."""

    def test_register_provider(self):
        """Test provider registration."""
        factory = ProviderFactory()

        # Register custom provider
        class CustomProvider:
            pass

        factory.register_provider("custom", CustomProvider)

        assert "custom" in factory.list_providers()

    def test_create_provider_success(self):
        """Test successful provider creation."""
        factory = ProviderFactory()

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = factory.create_provider("claude-code")

            assert provider is not None
            assert provider.name == "claude-code"

    def test_create_provider_not_registered(self):
        """Test creating unregistered provider fails."""
        factory = ProviderFactory()

        with pytest.raises(ProviderError, match="not registered"):
            factory.create_provider("nonexistent")

    def test_create_provider_caching(self):
        """Test provider caching."""
        factory = ProviderFactory()

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider1 = factory.create_provider("claude-code")
            provider2 = factory.create_provider("claude-code")

            # Should return same instance from cache
            assert provider1 is provider2

    def test_list_providers(self):
        """Test listing registered providers."""
        factory = ProviderFactory()

        providers = factory.list_providers()

        assert "claude-code" in providers
        # OpenCode may not be available
        # Direct API should be available

    def test_get_provider_info(self):
        """Test getting provider information."""
        factory = ProviderFactory()

        info = factory.get_provider_info("claude-code")

        assert info["name"] == "claude-code"
        assert "models" in info
        assert "requires_cli" in info

    def test_create_with_config(self):
        """Test creating provider with configuration."""
        factory = ProviderFactory()

        config = {
            "api_key": "test-key",
            "timeout": 1800,
        }

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = factory.create_provider("claude-code", config)

            assert provider is not None

    def test_model_translation_cache(self):
        """Test model name translation caching."""
        factory = ProviderFactory()

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            # First call
            model1 = factory.translate_model_name("claude-code", "sonnet-4.5")

            # Second call (should be cached)
            model2 = factory.translate_model_name("claude-code", "sonnet-4.5")

            assert model1 == model2
            assert model1 == "claude-sonnet-4-5-20250929"
```

#### Step 2: Integration Tests

**File**: `tests/integration/providers/test_provider_integration.py`

```python
"""Integration tests for provider system."""

import pytest
import asyncio
from pathlib import Path

from gao_dev.core.providers.factory import ProviderFactory
from gao_dev.core.providers.models import AgentContext
from gao_dev.core.process_executor import ProcessExecutor


@pytest.mark.integration
class TestProviderIntegration:
    """Test end-to-end provider integration."""

    @pytest.mark.asyncio
    async def test_end_to_end_claude_code(self, tmp_path):
        """Test end-to-end with ClaudeCodeProvider."""
        # Skip if no API key
        if not os.environ.get("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set")

        factory = ProviderFactory()
        provider = factory.create_provider("claude-code")

        context = AgentContext(project_root=tmp_path)

        # Execute simple task
        results = []
        async for result in provider.execute_task(
            task="Echo 'Hello World'",
            context=context,
            model="sonnet-4.5",
            tools=["Bash"],
            timeout=60,
        ):
            results.append(result)

        assert len(results) > 0
        assert any("Hello World" in r for r in results)

    @pytest.mark.asyncio
    async def test_process_executor_auto_select(self, tmp_path):
        """Test ProcessExecutor auto-selects provider."""
        if not os.environ.get("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set")

        # Don't specify provider - should auto-select
        executor = ProcessExecutor(project_root=tmp_path)

        # Provider should be selected
        assert executor.provider is not None
        assert executor.provider.name in [
            "claude-code", "opencode", "direct-api-anthropic"
        ]

    @pytest.mark.asyncio
    async def test_multi_provider_workflow(self, tmp_path):
        """Test using multiple providers in sequence."""
        if not os.environ.get("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set")

        factory = ProviderFactory()

        # Try all available providers
        providers_to_test = []
        for name in ["claude-code", "direct-api"]:
            try:
                provider = factory.create_provider(
                    name,
                    {"provider": "anthropic"} if "direct-api" in name else {}
                )
                providers_to_test.append(provider)
            except Exception:
                pass

        assert len(providers_to_test) > 0

        # Execute same task on each
        for provider in providers_to_test:
            context = AgentContext(project_root=tmp_path)

            results = []
            async for result in provider.execute_task(
                task="What is 2+2?",
                context=context,
                model="sonnet-4.5",
                timeout=60,
            ):
                results.append(result)

            assert len(results) > 0
```

#### Step 3: Backward Compatibility Tests

**File**: `tests/compatibility/providers/test_backward_compatibility.py`

```python
"""Backward compatibility tests."""

import pytest
from pathlib import Path

from gao_dev.core.process_executor import ProcessExecutor


class TestBackwardCompatibility:
    """Ensure no breaking changes."""

    def test_legacy_process_executor_constructor(self):
        """Test legacy ProcessExecutor constructor still works."""
        # Old way with explicit CLI path
        executor = ProcessExecutor(
            project_root=Path("/tmp"),
            cli_path=Path("/usr/bin/claude"),
        )

        assert executor.provider is not None
        assert executor.provider.name == "claude-code"

    def test_legacy_api_key_parameter(self):
        """Test legacy api_key parameter works."""
        executor = ProcessExecutor(
            project_root=Path("/tmp"),
            api_key="test-key",
        )

        # Should create provider with API key
        assert executor.provider is not None

    def test_existing_workflows_unchanged(self):
        """Test existing workflows work unchanged."""
        # This would run full workflow tests
        # to ensure nothing broke
        pass

    def test_existing_tests_still_pass(self):
        """Verify all 400+ existing tests still pass."""
        # This is validated by running full test suite
        # This test is a placeholder/marker
        assert True
```

#### Step 4: Security Tests

**File**: `tests/security/providers/test_plugin_sandboxing.py`

```python
"""Security and sandboxing tests for provider plugins."""

import pytest

from gao_dev.plugins.provider_plugin import BaseProviderPlugin
from gao_dev.plugins.provider_plugin_manager import ProviderPluginManager


@pytest.mark.security
class TestPluginSecurity:
    """Test plugin security and sandboxing."""

    def test_malicious_plugin_detected(self):
        """Test malicious plugin is detected."""
        # Create plugin that tries to access restricted resources
        # Verify it's blocked/warned
        pass

    def test_plugin_resource_limits(self):
        """Test plugin resource limits enforced."""
        # Create plugin that tries to use excessive resources
        # Verify limits enforced
        pass

    def test_plugin_permission_enforcement(self):
        """Test plugin permissions enforced."""
        # Create plugin without file system permission
        # Verify file operations blocked
        pass

    def test_invalid_provider_rejected(self):
        """Test invalid provider class rejected."""
        class InvalidPlugin(BaseProviderPlugin):
            def get_provider_class(self):
                # Return class that doesn't implement IAgentProvider
                class NotAProvider:
                    pass
                return NotAProvider

            def get_provider_metadata(self):
                # Minimal metadata
                pass

        plugin = InvalidPlugin()
        assert not plugin.validate_provider_class()
```

#### Step 5: Performance Regression Tests

**File**: `tests/performance/providers/test_provider_performance.py`

```python
"""Performance regression tests."""

import pytest
import time

from gao_dev.core.providers.factory import ProviderFactory


@pytest.mark.performance
class TestPerformanceRegression:
    """Detect performance regressions."""

    def test_initialization_time_threshold(self):
        """Test initialization within threshold."""
        factory = ProviderFactory()

        # Cold start
        start = time.time()
        provider1 = factory.create_provider("claude-code")
        cold_time = time.time() - start

        # Warm start (cached)
        start = time.time()
        provider2 = factory.create_provider("claude-code")
        warm_time = time.time() - start

        # Thresholds
        assert cold_time < 0.050  # <50ms cold start
        assert warm_time < 0.005  # <5ms warm start

    def test_model_translation_time_threshold(self):
        """Test model translation within threshold."""
        factory = ProviderFactory()

        start = time.time()
        model = factory.translate_model_name("claude-code", "sonnet-4.5")
        elapsed = time.time() - start

        assert elapsed < 0.001  # <1ms

    def test_memory_usage_threshold(self):
        """Test memory usage within threshold."""
        import tracemalloc

        factory = ProviderFactory()

        tracemalloc.start()

        # Create multiple providers
        providers = []
        for _ in range(10):
            provider = factory.create_provider("claude-code")
            providers.append(provider)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Should not use excessive memory
        assert peak < 10 * 1024 * 1024  # <10MB for 10 providers
```

#### Step 6: Test Documentation

**File**: `docs/testing/provider-test-strategy.md`

```markdown
# Provider Abstraction Test Strategy

## Test Pyramid

```
       /\
      /  \     E2E Tests (10%)
     /____\
    /      \   Integration Tests (30%)
   /________\
  /          \ Unit Tests (60%)
 /__________\
```

## Test Categories

### 1. Unit Tests (60% of tests)
- **Purpose**: Test individual components in isolation
- **Coverage Target**: 100%
- **Location**: `tests/unit/providers/`
- **Run Time**: <30 seconds

**Components Tested**:
- Provider implementations
- Factory
- Selector
- Selection strategies
- Cache
- Configuration loaders

### 2. Integration Tests (30% of tests)
- **Purpose**: Test component interactions
- **Coverage Target**: All critical paths
- **Location**: `tests/integration/providers/`
- **Run Time**: <5 minutes

**Scenarios Tested**:
- End-to-end provider usage
- ProcessExecutor integration
- Multi-provider workflows
- Configuration loading
- Plugin system

### 3. E2E Tests (10% of tests)
- **Purpose**: Test complete user workflows
- **Coverage Target**: Happy path + critical errors
- **Location**: `tests/e2e/providers/`
- **Run Time**: <10 minutes

**Scenarios Tested**:
- Create PRD with provider
- Implement story with provider
- Benchmark run with provider

## Special Test Suites

### Performance Tests
- **When**: Nightly in CI, before release
- **Purpose**: Detect regressions
- **Thresholds**:
  - Initialization: <50ms cold, <5ms warm
  - Translation: <1ms
  - Memory: <10MB per provider

### Security Tests
- **When**: Every commit, before release
- **Purpose**: Prevent vulnerabilities
- **Checks**:
  - Plugin sandboxing
  - Permission enforcement
  - API key validation

### Compatibility Tests
- **When**: Before release
- **Purpose**: Ensure backward compatibility
- **Checks**:
  - All existing tests pass
  - Legacy API works
  - Configurations compatible

### Platform Tests
- **When**: Before release
- **Purpose**: Multi-platform support
- **Platforms**:
  - Windows
  - macOS
  - Linux

## Test Execution

### Local Development
```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run with coverage
pytest --cov=gao_dev/core/providers

# Run performance tests
pytest -m performance
```

### CI Pipeline
```yaml
# .github/workflows/test.yml
- Run unit tests (every commit)
- Run integration tests (every commit)
- Run security tests (every commit)
- Run performance tests (nightly)
- Run platform tests (before release)
```

## Definition of Done

Test checklist before merging:
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Coverage >90%
- [ ] Type checking passes (MyPy)
- [ ] Linting passes (Ruff)
- [ ] No security issues
- [ ] Performance thresholds met
- [ ] Backward compatibility verified
```

---

## Testing Strategy

### Test Execution Plan
1. **Phase 1**: Unit tests (2 days)
2. **Phase 2**: Integration tests (2 days)
3. **Phase 3**: Security & performance tests (2 days)
4. **Phase 4**: Platform & compatibility tests (1 day)
5. **Phase 5**: User acceptance testing (1 day)

### Success Criteria
- All tests pass
- Coverage >90%
- No critical bugs
- Performance thresholds met
- Security scan clean

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit test coverage >90%
- [ ] Integration tests complete
- [ ] Provider compatibility matrix generated
- [ ] Performance tests passing
- [ ] Security tests passing
- [ ] Backward compatibility verified
- [ ] Error scenario tests complete
- [ ] Multi-platform tests passing
- [ ] Stress tests passing
- [ ] UAT complete
- [ ] CI/CD integrated
- [ ] Test documentation complete
- [ ] All tests pass
- [ ] Code reviewed
- [ ] Changes committed

---

## Dependencies

**Upstream**:
- All Phase 1-3 stories - MUST be complete

**Downstream**:
- Story 11.15 (Migration Tooling) - uses test results
- Story 11.16 (Production Documentation) - documents test coverage

---

## Notes

- **Critical Story**: Must be thorough before release
- **No Shortcuts**: Every provider must be tested
- **Security**: Plugin sandboxing is critical
- **Performance**: Must not degrade
- **Backward Compat**: Must not break existing code
- **Documentation**: Test strategy and execution guide
- **CI**: All tests must run automatically

---

## Related Documents

- PRD: `docs/features/agent-provider-abstraction/PRD.md`
- Architecture: `docs/features/agent-provider-abstraction/ARCHITECTURE.md`
- Test Strategy: `docs/testing/provider-test-strategy.md`

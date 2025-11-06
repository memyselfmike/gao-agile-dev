# Story 19.4: Integration Testing and Validation

**Epic**: Epic 19 - OpenCode SDK Integration
**Status**: Draft
**Priority**: P1 (High)
**Estimated Effort**: 3 story points
**Owner**: Murat (Test Architect) + Amelia (Developer)
**Created**: 2025-11-06

---

## User Story

**As a** QA engineer
**I want** comprehensive integration tests for the OpenCode SDK provider
**So that** I can verify it works correctly with real OpenCode servers and maintains system quality

---

## Acceptance Criteria

### AC1: Unit Test Coverage
- Unit tests cover all public methods of `OpenCodeSDKProvider`
- Mock-based tests don't require running server
- Test coverage >85% for `opencode_sdk.py`
- All edge cases and error paths tested

### AC2: Integration Tests
- Integration test runs end-to-end with real OpenCode server
- Tests task execution with multiple models
- Tests server lifecycle (start, execute, stop)
- Tests error recovery and retry logic

### AC3: Provider Validation Tests
- Provider registered in factory
- Provider selection via configuration
- Provider switching works correctly
- All tools supported correctly

### AC4: Existing Tests Pass
- All 400+ existing tests pass without modification
- No regressions introduced
- Type checking passes (mypy strict mode)
- Linting passes (ruff)

### AC5: Test Documentation
- Test files have clear docstrings
- Complex test scenarios documented
- Setup/teardown procedures documented
- Known limitations documented

### AC6: CI/CD Integration
- Tests run in CI/CD pipeline
- Integration tests skip if OpenCode not available
- Test results reported correctly
- Coverage reports generated

---

## Technical Details

### File Structure
```
tests/
├── core/
│   └── providers/
│       ├── test_opencode_sdk.py              # NEW: Unit tests
│       └── test_opencode_sdk_lifecycle.py    # NEW: Lifecycle tests
├── integration/
│   └── test_opencode_sdk_integration.py      # NEW: Integration tests
└── conftest.py                               # MODIFIED: Add fixtures
```

### Implementation Approach

**Step 1: Unit Tests (test_opencode_sdk.py)**
```python
"""Unit tests for OpenCodeSDKProvider."""

import pytest
from unittest.mock import Mock, MagicMock, patch

from gao_dev.core.providers.opencode_sdk import OpenCodeSDKProvider
from gao_dev.core.providers.exceptions import (
    ProviderInitializationError,
    TaskExecutionError,
)


class TestOpenCodeSDKProvider:
    """Test OpenCodeSDKProvider implementation."""

    def test_initialization(self):
        """Test provider initialization."""
        provider = OpenCodeSDKProvider(
            server_url="http://localhost:4096",
            port=4096,
        )

        assert provider.server_url == "http://localhost:4096"
        assert provider.port == 4096
        assert provider.sdk_client is None

    @patch('gao_dev.core.providers.opencode_sdk.Opencode')
    @patch('gao_dev.core.providers.opencode_sdk.subprocess.Popen')
    @patch('gao_dev.core.providers.opencode_sdk.requests.get')
    def test_initialize_with_auto_start(self, mock_requests, mock_popen, mock_opencode):
        """Test initialization with auto-start enabled."""
        # Setup mocks
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.return_value = mock_response

        # Initialize
        provider = OpenCodeSDKProvider(auto_start_server=True)
        provider.initialize()

        # Verify
        assert provider.sdk_client is not None
        mock_popen.assert_called_once()

    def test_model_translation(self):
        """Test model name translation."""
        provider = OpenCodeSDKProvider()

        # Test all supported models
        test_cases = [
            ("claude-sonnet-4-5-20250929", ("anthropic", "claude-sonnet-4.5")),
            ("claude-opus-4-20250514", ("anthropic", "claude-opus-4")),
            ("claude-3-5-sonnet-20241022", ("anthropic", "claude-3.5-sonnet")),
            ("claude-3-haiku-20240307", ("anthropic", "claude-3-haiku")),
        ]

        for canonical, expected in test_cases:
            result = provider._translate_model(canonical)
            assert result == expected, f"Failed for {canonical}"

    def test_model_translation_unsupported(self):
        """Test model translation with unsupported model."""
        provider = OpenCodeSDKProvider()

        with pytest.raises(TaskExecutionError) as exc_info:
            provider._translate_model("unsupported-model-123")

        assert "not supported" in str(exc_info.value).lower()

    @patch('gao_dev.core.providers.opencode_sdk.Opencode')
    def test_execute_task_mocked(self, mock_opencode):
        """Test task execution with mocked SDK."""
        # Setup mocks
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Task result"
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_session.chat.return_value = mock_response

        mock_client = MagicMock()
        mock_client.create_session.return_value = mock_session
        mock_opencode.return_value = mock_client

        # Execute
        provider = OpenCodeSDKProvider(auto_start_server=False)
        provider.sdk_client = mock_client

        response = provider.execute_task(
            prompt="Test prompt",
            model="claude-sonnet-4-5-20250929",
        )

        # Verify
        assert response.content == "Task result"
        assert response.model == "claude-sonnet-4-5-20250929"
        assert response.provider == "opencode-sdk"

    def test_supports_tool(self):
        """Test tool support checking."""
        provider = OpenCodeSDKProvider()

        # Test supported tools
        supported = ["Read", "Write", "Edit", "Grep", "Glob", "Bash"]
        for tool in supported:
            assert provider.supports_tool(tool), f"{tool} should be supported"

        # Test unsupported tool
        assert not provider.supports_tool("InvalidTool")

    def test_get_supported_models(self):
        """Test getting supported models."""
        provider = OpenCodeSDKProvider()
        models = provider.get_supported_models()

        assert len(models) > 0
        assert "claude-sonnet-4-5-20250929" in models

    def test_cleanup(self):
        """Test provider cleanup."""
        provider = OpenCodeSDKProvider()
        provider.sdk_client = MagicMock()
        provider.session = MagicMock()
        provider.server_process = MagicMock()

        provider.cleanup()

        assert provider.sdk_client is None
        assert provider.session is None
```

**Step 2: Integration Tests (test_opencode_sdk_integration.py)**
```python
"""Integration tests for OpenCodeSDKProvider with real OpenCode server."""

import pytest
import subprocess
import time

from gao_dev.core.providers.opencode_sdk import OpenCodeSDKProvider
from gao_dev.core.providers.exceptions import TaskExecutionError


# Skip integration tests if OpenCode not available
def is_opencode_available():
    """Check if OpenCode CLI is available."""
    try:
        subprocess.run(
            ["opencode", "--version"],
            capture_output=True,
            timeout=5,
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


pytestmark = pytest.mark.skipif(
    not is_opencode_available(),
    reason="OpenCode CLI not available"
)


class TestOpenCodeSDKIntegration:
    """Integration tests with real OpenCode server."""

    @pytest.fixture
    def provider(self):
        """Create provider instance for testing."""
        provider = OpenCodeSDKProvider(auto_start_server=True)
        provider.initialize()
        yield provider
        provider.cleanup()

    def test_end_to_end_task_execution(self, provider):
        """Test complete task execution flow."""
        response = provider.execute_task(
            prompt="Say 'Hello, World!' and nothing else.",
            model="claude-sonnet-4-5-20250929",
        )

        assert response.content is not None
        assert len(response.content) > 0
        assert response.provider == "opencode-sdk"
        assert "hello" in response.content.lower()

    def test_multiple_tasks_same_session(self, provider):
        """Test executing multiple tasks in same session."""
        # First task
        response1 = provider.execute_task(
            prompt="Count to 3",
            model="claude-sonnet-4-5-20250929",
        )
        assert response1.content is not None

        # Second task
        response2 = provider.execute_task(
            prompt="What is 2 + 2?",
            model="claude-sonnet-4-5-20250929",
        )
        assert response2.content is not None

    def test_different_models(self, provider):
        """Test task execution with different models."""
        models_to_test = [
            "claude-sonnet-4-5-20250929",
            "claude-3-5-sonnet-20241022",
        ]

        for model in models_to_test:
            response = provider.execute_task(
                prompt="Say hi",
                model=model,
            )
            assert response.content is not None
            assert response.model == model

    def test_server_recovery_after_error(self, provider):
        """Test provider recovery after task error."""
        # First, cause an error
        try:
            provider.execute_task(
                prompt="Test",
                model="invalid-model",
            )
        except TaskExecutionError:
            pass  # Expected

        # Verify provider still works
        response = provider.execute_task(
            prompt="Recovery test",
            model="claude-sonnet-4-5-20250929",
        )
        assert response.content is not None

    def test_server_lifecycle(self):
        """Test complete server lifecycle."""
        # Create provider
        provider = OpenCodeSDKProvider(auto_start_server=True)

        # Initialize (starts server)
        provider.initialize()
        assert provider.server_process is not None
        assert provider._is_server_healthy()

        # Execute task
        response = provider.execute_task(
            prompt="Test",
            model="claude-sonnet-4-5-20250929",
        )
        assert response.content is not None

        # Cleanup (stops server)
        provider.cleanup()
        time.sleep(1)  # Allow time for shutdown

        # Server should be stopped
        assert not provider._is_server_healthy()


class TestProviderFactory:
    """Test provider factory integration."""

    def test_factory_creates_sdk_provider(self):
        """Test factory can create SDK provider."""
        from gao_dev.core.providers.factory import ProviderFactory

        provider = ProviderFactory.create_provider(
            provider_name="opencode-sdk",
            config={},
        )

        assert isinstance(provider, OpenCodeSDKProvider)

    def test_provider_switching(self):
        """Test switching between providers."""
        from gao_dev.core.providers.factory import ProviderFactory

        # Create SDK provider
        sdk_provider = ProviderFactory.create_provider("opencode-sdk", {})
        assert isinstance(sdk_provider, OpenCodeSDKProvider)

        # Create CLI provider
        cli_provider = ProviderFactory.create_provider("opencode-cli", {})
        assert cli_provider.__class__.__name__ == "OpenCodeProvider"
```

**Step 3: Update conftest.py**
```python
# tests/conftest.py

import pytest


@pytest.fixture
def mock_opencode_sdk():
    """Fixture for mocking OpenCode SDK."""
    from unittest.mock import MagicMock, patch

    with patch('gao_dev.core.providers.opencode_sdk.Opencode') as mock:
        mock_client = MagicMock()
        mock_session = MagicMock()
        mock_client.create_session.return_value = mock_session
        mock.return_value = mock_client
        yield mock


@pytest.fixture
def opencode_sdk_provider():
    """Fixture for creating OpenCodeSDKProvider instance."""
    from gao_dev.core.providers.opencode_sdk import OpenCodeSDKProvider

    provider = OpenCodeSDKProvider(auto_start_server=False)
    yield provider
    provider.cleanup()
```

---

## Testing Approach

### Manual Testing
```bash
# Run unit tests
pytest tests/core/providers/test_opencode_sdk.py -v

# Run integration tests (requires OpenCode)
pytest tests/integration/test_opencode_sdk_integration.py -v

# Run with coverage
pytest tests/core/providers/test_opencode_sdk.py --cov=gao_dev.core.providers.opencode_sdk

# Run all tests
pytest tests/ -v

# Type checking
mypy gao_dev/core/providers/opencode_sdk.py

# Linting
ruff check gao_dev/core/providers/opencode_sdk.py
```

### Expected Output
```
===== Test Results =====
test_opencode_sdk.py::TestOpenCodeSDKProvider::test_initialization PASSED
test_opencode_sdk.py::TestOpenCodeSDKProvider::test_execute_task_mocked PASSED
...
test_opencode_sdk_integration.py::TestOpenCodeSDKIntegration::test_end_to_end_task_execution PASSED
...

Coverage: 87% for opencode_sdk.py

===== 420+ tests passed in X.XXs =====
```

---

## Dependencies

### Required Packages
- pytest (existing)
- pytest-cov (existing)
- pytest-mock (existing)
- requests-mock (for HTTP mocking)

### Code Dependencies
- Story 19.1 (SDK dependency)
- Story 19.2 (Core provider)
- Story 19.3 (Server lifecycle)

### External Dependencies
- OpenCode CLI (for integration tests)
- Running OpenCode server (for integration tests)

---

## Definition of Done

- [x] Unit tests created with >85% coverage
- [x] Integration tests created for end-to-end scenarios
- [x] Provider validation tests created
- [x] All 400+ existing tests pass
- [x] Type checking passes (mypy strict mode)
- [x] Linting passes (ruff)
- [x] Test documentation complete
- [x] CI/CD integration configured
- [x] Code follows existing style (ASCII-only, type hints)
- [x] Committed to git with conventional commit message

---

## Related Stories

**Depends On**:
- Story 19.1 (Add OpenCode SDK Dependency)
- Story 19.2 (Implement OpenCodeSDKProvider Core)
- Story 19.3 (Server Lifecycle Management)

**Blocks**:
- Story 19.5 (Provider Registration and Documentation)

---

## Notes

### Test Strategy

**Unit Tests** (Fast, No External Dependencies)
- Mock all external dependencies (SDK, subprocess, HTTP)
- Test individual methods in isolation
- Cover all code paths and edge cases
- Run on every commit

**Integration Tests** (Slower, Requires OpenCode)
- Test with real OpenCode server
- Verify end-to-end functionality
- Test multiple scenarios and models
- Skip if OpenCode not available

### Coverage Goals
- **Unit tests**: >90% line coverage
- **Integration tests**: Cover main user flows
- **Total**: >85% combined coverage

### CI/CD Considerations
- Unit tests run always
- Integration tests skip if OpenCode not installed
- Use pytest markers: `@pytest.mark.integration`
- Generate coverage reports for code review

---

## Acceptance Testing

### Test Case 1: Unit Test Coverage
```bash
$ pytest tests/core/providers/test_opencode_sdk.py --cov
...
Coverage: 87% for opencode_sdk.py
```
**Expected**: Coverage >85%

### Test Case 2: Integration Test
```bash
$ pytest tests/integration/test_opencode_sdk_integration.py::test_end_to_end_task_execution -v
...
PASSED
```
**Expected**: Integration test passes with real server

### Test Case 3: All Tests Pass
```bash
$ pytest tests/
...
===== 420+ passed in X.XXs =====
```
**Expected**: All tests pass, including new ones

### Test Case 4: Type Checking
```bash
$ mypy gao_dev/core/providers/opencode_sdk.py --strict
Success: no issues found
```
**Expected**: Type checking passes

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Integration tests flaky | Medium | Medium | Add retries, better error handling |
| Coverage below target | Low | Low | Add more edge case tests |
| CI/CD issues | Medium | Low | Test locally first, skip integration in CI |
| Existing tests break | High | Low | Run full suite before committing |

---

## Implementation Checklist

- [ ] Create `tests/core/providers/test_opencode_sdk.py`
- [ ] Create `tests/core/providers/test_opencode_sdk_lifecycle.py`
- [ ] Create `tests/integration/test_opencode_sdk_integration.py`
- [ ] Update `tests/conftest.py` with fixtures
- [ ] Write unit tests for all public methods
- [ ] Write unit tests for error paths
- [ ] Write integration tests for end-to-end scenarios
- [ ] Write provider factory tests
- [ ] Add pytest markers for test categorization
- [ ] Run all tests locally
- [ ] Check coverage meets target (>85%)
- [ ] Run type checking (mypy)
- [ ] Run linting (ruff)
- [ ] Document complex test scenarios
- [ ] Create git commit with conventional message

---

**Created by**: Bob (Scrum Master) via BMAD workflow
**Ready for Implementation**: Yes (after Stories 19.1, 19.2, 19.3)
**Estimated Completion**: 0.5 days

---

*This story is part of the GAO-Dev OpenCode SDK Integration project.*

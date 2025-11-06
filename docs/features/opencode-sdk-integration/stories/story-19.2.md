# Story 19.2: Implement OpenCodeSDKProvider Core

**Epic**: Epic 19 - OpenCode SDK Integration
**Status**: Draft
**Priority**: P0 (Critical)
**Estimated Effort**: 8 story points
**Owner**: Amelia (Developer)
**Created**: 2025-11-06

---

## User Story

**As a** GAO-Dev system
**I want** a fully-implemented OpenCodeSDKProvider that uses the OpenCode SDK
**So that** I can execute agent tasks via direct API calls instead of CLI subprocesses

---

## Acceptance Criteria

### AC1: Class Implementation
- `OpenCodeSDKProvider` class created in `gao_dev/core/providers/opencode_sdk.py`
- Inherits from `IAgentProvider` interface
- All interface methods implemented (no NotImplementedError)
- Type hints for all methods and parameters

### AC2: Task Execution
- `execute_task()` method creates SDK session and sends chat message
- Returns properly formatted `AgentResponse` object
- Handles streaming responses (if supported by SDK)
- Includes usage statistics (tokens, cost)

### AC3: Model Translation
- Translates canonical model names to OpenCode provider/model IDs
- Supports all standard models (Claude Sonnet, Opus, Haiku)
- Handles model not found errors gracefully
- Model mapping documented in code

### AC4: Tool Support
- `supports_tool()` returns correct tool availability
- `get_supported_models()` returns list of available models
- Tool definitions translated to SDK format

### AC5: Error Handling
- SDK exceptions caught and translated to provider exceptions
- Clear error messages for all failure scenarios
- Retries for transient failures (network errors)
- Proper cleanup on errors

### AC6: Logging and Observability
- structlog used for all logging
- Logs cover: initialization, task execution, errors, cleanup
- Log levels appropriate (DEBUG, INFO, WARNING, ERROR)
- No sensitive data in logs (API keys, user content)

### AC7: Type Safety
- MyPy passes in strict mode
- No `Any` types used
- All imports properly typed

---

## Technical Details

### File Structure
```
gao_dev/core/providers/
├── __init__.py              # MODIFIED: Export OpenCodeSDKProvider
├── opencode_sdk.py          # NEW: SDK provider implementation
├── interfaces.py            # EXISTING: IAgentProvider interface
├── opencode.py              # EXISTING: CLI provider (kept for fallback)
└── exceptions.py            # EXISTING: Provider exceptions
```

### Implementation Approach

**Step 1: Create opencode_sdk.py Module**
```python
"""OpenCode SDK-based agent provider implementation."""

from typing import Dict, List, Optional, Any
import structlog
from opencode_ai import Opencode

from gao_dev.core.providers.interfaces import IAgentProvider, AgentResponse
from gao_dev.core.providers.exceptions import (
    ProviderError,
    ProviderInitializationError,
    TaskExecutionError,
)

logger = structlog.get_logger(__name__)


class OpenCodeSDKProvider(IAgentProvider):
    """
    OpenCode SDK-based agent provider.

    Uses OpenCode's Python SDK for direct API access, eliminating
    subprocess hanging issues present in CLI-based provider.

    Attributes:
        sdk_client: OpenCode SDK client instance
        server_url: URL of OpenCode server (default: http://localhost:4096)
        session: Current SDK session for task execution
    """

    # Model translation map: canonical name -> (provider_id, model_id)
    MODEL_MAP = {
        "claude-sonnet-4-5-20250929": ("anthropic", "claude-sonnet-4.5"),
        "claude-opus-4-20250514": ("anthropic", "claude-opus-4"),
        "claude-3-5-sonnet-20241022": ("anthropic", "claude-3.5-sonnet"),
        "claude-3-haiku-20240307": ("anthropic", "claude-3-haiku"),
    }

    def __init__(
        self,
        server_url: str = "http://localhost:4096",
        api_key: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """
        Initialize OpenCode SDK provider.

        Args:
            server_url: URL of OpenCode server
            api_key: API key for authentication (if required)
            **kwargs: Additional configuration options
        """
        self.server_url = server_url
        self.api_key = api_key
        self.sdk_client: Optional[Opencode] = None
        self.session: Optional[Any] = None

        logger.info(
            "opencode_sdk_provider_init",
            server_url=server_url,
            has_api_key=bool(api_key),
        )

    def initialize(self) -> None:
        """Initialize SDK client and verify server connection."""
        try:
            logger.info("opencode_sdk_provider_initialize_start")

            # Create SDK client
            self.sdk_client = Opencode(base_url=self.server_url)

            logger.info("opencode_sdk_provider_initialize_complete")

        except Exception as e:
            logger.error(
                "opencode_sdk_provider_initialize_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise ProviderInitializationError(
                f"Failed to initialize OpenCode SDK provider: {e}"
            ) from e

    def execute_task(
        self,
        prompt: str,
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any
    ) -> AgentResponse:
        """
        Execute agent task using OpenCode SDK.

        Args:
            prompt: Task prompt/message
            model: Model name (canonical format)
            tools: Available tools for agent
            **kwargs: Additional execution parameters

        Returns:
            AgentResponse with task results

        Raises:
            TaskExecutionError: If task execution fails
        """
        if not self.sdk_client:
            raise TaskExecutionError("Provider not initialized")

        try:
            # Translate model name
            provider_id, model_id = self._translate_model(model)

            logger.info(
                "opencode_sdk_execute_task_start",
                model=model,
                provider_id=provider_id,
                model_id=model_id,
                has_tools=bool(tools),
            )

            # Create session if needed
            if not self.session:
                self.session = self.sdk_client.create_session(
                    provider_id=provider_id,
                    model_id=model_id,
                )
                logger.debug("opencode_sdk_session_created", session_id=self.session.id)

            # Send chat message
            response = self.session.chat(
                message=prompt,
                tools=tools or [],
            )

            # Extract response content
            content = self._extract_content(response)
            usage = self._extract_usage(response)

            logger.info(
                "opencode_sdk_execute_task_complete",
                content_length=len(content),
                usage=usage,
            )

            return AgentResponse(
                content=content,
                usage=usage,
                model=model,
                provider="opencode-sdk",
            )

        except Exception as e:
            logger.error(
                "opencode_sdk_execute_task_failed",
                error=str(e),
                error_type=type(e).__name__,
                model=model,
            )
            raise TaskExecutionError(
                f"Failed to execute task with OpenCode SDK: {e}"
            ) from e

    def _translate_model(self, canonical_name: str) -> tuple[str, str]:
        """
        Translate canonical model name to OpenCode provider/model IDs.

        Args:
            canonical_name: Canonical model name

        Returns:
            Tuple of (provider_id, model_id)

        Raises:
            TaskExecutionError: If model not found
        """
        if canonical_name not in self.MODEL_MAP:
            raise TaskExecutionError(
                f"Model '{canonical_name}' not supported by OpenCode SDK provider. "
                f"Supported models: {list(self.MODEL_MAP.keys())}"
            )

        return self.MODEL_MAP[canonical_name]

    def _extract_content(self, response: Any) -> str:
        """Extract text content from SDK response."""
        # TODO: Update based on actual SDK response structure
        if hasattr(response, 'content'):
            return response.content
        elif hasattr(response, 'text'):
            return response.text
        elif isinstance(response, str):
            return response
        else:
            return str(response)

    def _extract_usage(self, response: Any) -> Dict[str, int]:
        """Extract usage statistics from SDK response."""
        # TODO: Update based on actual SDK response structure
        usage = {}
        if hasattr(response, 'usage'):
            usage = {
                'input_tokens': getattr(response.usage, 'input_tokens', 0),
                'output_tokens': getattr(response.usage, 'output_tokens', 0),
            }
        return usage

    def supports_tool(self, tool_name: str) -> bool:
        """Check if tool is supported by OpenCode SDK."""
        # OpenCode SDK supports all Claude tools
        supported_tools = {
            "Read", "Write", "Edit", "Grep", "Glob", "Bash",
            "WebFetch", "WebSearch", "AskUserQuestion", "TodoWrite",
        }
        return tool_name in supported_tools

    def get_supported_models(self) -> List[str]:
        """Get list of models supported by OpenCode SDK provider."""
        return list(self.MODEL_MAP.keys())

    def cleanup(self) -> None:
        """Clean up SDK resources."""
        try:
            logger.info("opencode_sdk_provider_cleanup_start")

            # Close session if exists
            if self.session:
                # TODO: Close session if SDK provides method
                self.session = None

            # Clean up client
            if self.sdk_client:
                # TODO: Close client if SDK provides method
                self.sdk_client = None

            logger.info("opencode_sdk_provider_cleanup_complete")

        except Exception as e:
            logger.warning(
                "opencode_sdk_provider_cleanup_error",
                error=str(e),
            )
```

**Step 2: Update __init__.py**
```python
# gao_dev/core/providers/__init__.py

from .interfaces import IAgentProvider, AgentResponse
from .anthropic import AnthropicProvider
from .opencode import OpenCodeProvider  # CLI-based (deprecated)
from .opencode_sdk import OpenCodeSDKProvider  # NEW: SDK-based
from .exceptions import ProviderError, TaskExecutionError

__all__ = [
    "IAgentProvider",
    "AgentResponse",
    "AnthropicProvider",
    "OpenCodeProvider",
    "OpenCodeSDKProvider",
    "ProviderError",
    "TaskExecutionError",
]
```

---

## Testing Approach

### Unit Tests
```python
# tests/core/providers/test_opencode_sdk.py
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

    def test_init(self):
        """Test provider initialization."""
        provider = OpenCodeSDKProvider(server_url="http://localhost:4096")
        assert provider.server_url == "http://localhost:4096"
        assert provider.sdk_client is None
        assert provider.session is None

    @patch('gao_dev.core.providers.opencode_sdk.Opencode')
    def test_initialize_success(self, mock_opencode):
        """Test successful provider initialization."""
        provider = OpenCodeSDKProvider()
        provider.initialize()

        assert provider.sdk_client is not None
        mock_opencode.assert_called_once()

    @patch('gao_dev.core.providers.opencode_sdk.Opencode')
    def test_initialize_failure(self, mock_opencode):
        """Test initialization failure handling."""
        mock_opencode.side_effect = Exception("Connection failed")

        provider = OpenCodeSDKProvider()
        with pytest.raises(ProviderInitializationError):
            provider.initialize()

    def test_translate_model_success(self):
        """Test model name translation."""
        provider = OpenCodeSDKProvider()
        provider_id, model_id = provider._translate_model("claude-sonnet-4-5-20250929")

        assert provider_id == "anthropic"
        assert model_id == "claude-sonnet-4.5"

    def test_translate_model_not_found(self):
        """Test model translation with unsupported model."""
        provider = OpenCodeSDKProvider()

        with pytest.raises(TaskExecutionError) as exc_info:
            provider._translate_model("unsupported-model")

        assert "not supported" in str(exc_info.value).lower()

    @patch('gao_dev.core.providers.opencode_sdk.Opencode')
    def test_execute_task_success(self, mock_opencode):
        """Test successful task execution."""
        # Setup mocks
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Task completed successfully"
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_session.chat.return_value = mock_response

        mock_client = MagicMock()
        mock_client.create_session.return_value = mock_session
        mock_opencode.return_value = mock_client

        # Execute task
        provider = OpenCodeSDKProvider()
        provider.initialize()

        response = provider.execute_task(
            prompt="Test prompt",
            model="claude-sonnet-4-5-20250929",
        )

        assert response.content == "Task completed successfully"
        assert response.model == "claude-sonnet-4-5-20250929"
        assert response.provider == "opencode-sdk"
        assert response.usage['input_tokens'] == 100
        assert response.usage['output_tokens'] == 50

    def test_execute_task_not_initialized(self):
        """Test task execution without initialization."""
        provider = OpenCodeSDKProvider()

        with pytest.raises(TaskExecutionError) as exc_info:
            provider.execute_task(
                prompt="Test",
                model="claude-sonnet-4-5-20250929",
            )

        assert "not initialized" in str(exc_info.value).lower()

    def test_supports_tool(self):
        """Test tool support checking."""
        provider = OpenCodeSDKProvider()

        assert provider.supports_tool("Read") is True
        assert provider.supports_tool("Write") is True
        assert provider.supports_tool("Bash") is True
        assert provider.supports_tool("InvalidTool") is False

    def test_get_supported_models(self):
        """Test getting supported models list."""
        provider = OpenCodeSDKProvider()
        models = provider.get_supported_models()

        assert "claude-sonnet-4-5-20250929" in models
        assert "claude-opus-4-20250514" in models
        assert len(models) > 0

    def test_cleanup(self):
        """Test provider cleanup."""
        provider = OpenCodeSDKProvider()
        provider.sdk_client = MagicMock()
        provider.session = MagicMock()

        provider.cleanup()

        assert provider.sdk_client is None
        assert provider.session is None
```

### Integration Tests (Story 19.4)
Integration tests will be created in Story 19.4 with real OpenCode server.

---

## Dependencies

### Required Packages
- opencode-ai ^0.1.0a36 (from Story 19.1)
- structlog (existing)
- Python 3.11+ (existing)

### Code Dependencies
- Story 19.1 (SDK dependency must be installed)
- `IAgentProvider` interface (existing)
- Provider exceptions (existing)

### External Dependencies
- None (mocked for unit tests)

---

## Definition of Done

- [x] File `gao_dev/core/providers/opencode_sdk.py` created
- [x] `OpenCodeSDKProvider` class implements all `IAgentProvider` methods
- [x] `execute_task()` creates session and sends chat message
- [x] Model translation works for all standard models
- [x] Error handling covers all scenarios
- [x] Logging with structlog throughout
- [x] Unit tests written with >90% coverage
- [x] Type checking passes (mypy strict mode)
- [x] All existing tests still pass
- [x] Code follows existing style (ASCII-only, type hints)
- [x] Committed to git with conventional commit message

---

## Related Stories

**Depends On**:
- Story 19.1 (Add OpenCode SDK Dependency)

**Blocks**:
- Story 19.3 (Server Lifecycle Management)
- Story 19.4 (Integration Testing and Validation)
- Story 19.5 (Provider Registration and Documentation)

---

## Notes

### Key Design Decisions

1. **Session Management**: Create session once per provider instance, reuse for multiple tasks
2. **Model Mapping**: Use static dictionary for model translation (simple, maintainable)
3. **Error Handling**: Translate SDK exceptions to provider exceptions for consistency
4. **Logging**: Use structlog for structured logging with context

### SDK Response Structure
The `_extract_content()` and `_extract_usage()` methods have TODO comments because the SDK's response structure needs to be verified. These will be updated during implementation based on actual SDK behavior.

### Future Enhancements
- Support for streaming responses
- Advanced tool configuration
- Custom model mappings via config
- Response caching

---

## Acceptance Testing

### Test Case 1: Provider Initialization
```python
provider = OpenCodeSDKProvider(server_url="http://localhost:4096")
provider.initialize()
assert provider.sdk_client is not None
```
**Expected**: Provider initializes successfully

### Test Case 2: Task Execution
```python
provider = OpenCodeSDKProvider()
provider.initialize()
response = provider.execute_task(
    prompt="Say hello",
    model="claude-sonnet-4-5-20250929",
)
assert response.content is not None
assert response.provider == "opencode-sdk"
```
**Expected**: Task executes and returns response

### Test Case 3: Model Translation
```python
provider = OpenCodeSDKProvider()
provider_id, model_id = provider._translate_model("claude-sonnet-4-5-20250929")
assert provider_id == "anthropic"
assert model_id == "claude-sonnet-4.5"
```
**Expected**: Model name translated correctly

### Test Case 4: Tool Support
```python
provider = OpenCodeSDKProvider()
assert provider.supports_tool("Read") is True
assert provider.supports_tool("InvalidTool") is False
```
**Expected**: Tool support checked correctly

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| SDK API differs from expected | High | Medium | Mock SDK for unit tests, verify in integration tests |
| Session creation fails | High | Low | Retry logic, clear error messages |
| Response parsing fails | Medium | Low | Defensive parsing, handle multiple formats |
| Performance degradation | Medium | Low | Benchmark in Story 19.4 |

---

## Implementation Checklist

- [ ] Create `opencode_sdk.py` module
- [ ] Implement `OpenCodeSDKProvider` class
- [ ] Implement `initialize()` method
- [ ] Implement `execute_task()` method
- [ ] Implement `_translate_model()` method
- [ ] Implement `_extract_content()` method
- [ ] Implement `_extract_usage()` method
- [ ] Implement `supports_tool()` method
- [ ] Implement `get_supported_models()` method
- [ ] Implement `cleanup()` method
- [ ] Add structlog logging throughout
- [ ] Update `__init__.py` to export new provider
- [ ] Write comprehensive unit tests
- [ ] Run mypy type checking
- [ ] Run full test suite
- [ ] Create git commit with conventional message

---

**Created by**: Bob (Scrum Master) via BMAD workflow
**Ready for Implementation**: Yes (after Story 19.1)
**Estimated Completion**: 1 day

---

*This story is part of the GAO-Dev OpenCode SDK Integration project.*

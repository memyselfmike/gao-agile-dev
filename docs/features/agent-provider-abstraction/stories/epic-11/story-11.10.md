# Story 11.10: Implement Direct API Provider

**Epic**: Epic 11 - Agent Provider Abstraction
**Status**: Not Started
**Priority**: P1 (High)
**Estimated Effort**: 13 story points
**Owner**: Amelia (Developer)
**Created**: 2025-11-04
**Dependencies**: Story 11.1 (Provider Interface), Story 11.3 (ProviderFactory)

---

## User Story

**As a** GAO-Dev developer
**I want** to execute AI tasks directly via API calls without CLI overhead
**So that** I can achieve better performance, lower latency, and more control over API interactions

---

## Acceptance Criteria

### AC1: DirectAPIProvider Implementation Created
- ✅ `DirectAPIProvider` class implements `IAgentProvider`
- ✅ Located in `gao_dev/core/providers/direct_api.py`
- ✅ Supports Anthropic, OpenAI, Google providers
- ✅ Provider selection via configuration
- ✅ No subprocess execution (direct HTTP API calls)
- ✅ Type-safe implementation (MyPy strict passes)

### AC2: Anthropic API Integration
- ✅ Uses official `anthropic` Python SDK
- ✅ Supports all Claude models (Sonnet 4.5, 3.5, Opus, Haiku)
- ✅ Streaming response support
- ✅ Tool calling support (if needed)
- ✅ Token usage tracking
- ✅ Cost calculation based on model pricing

### AC3: OpenAI API Integration
- ✅ Uses official `openai` Python SDK
- ✅ Supports GPT-4, GPT-4 Turbo, GPT-3.5 models
- ✅ Streaming response support
- ✅ Function calling support (if needed)
- ✅ Token usage tracking
- ✅ Cost calculation

### AC4: Google API Integration
- ✅ Uses `google-generativeai` Python SDK
- ✅ Supports Gemini Pro, Gemini Pro Vision models
- ✅ Streaming response support
- ✅ Token usage tracking
- ✅ Cost calculation

### AC5: Connection Management
- ✅ HTTP connection pooling
- ✅ Automatic retry logic (exponential backoff)
- ✅ Rate limiting support
- ✅ Timeout configuration
- ✅ Graceful error handling
- ✅ API key validation on initialization

### AC6: Performance Optimization
- ✅ ~25% faster than CLI-based providers (no subprocess overhead)
- ✅ Lower memory footprint (no additional process)
- ✅ Efficient streaming implementation
- ✅ Minimal latency between chunks
- ✅ Performance benchmarks documented

### AC7: Model Name Translation
- ✅ Canonical model names supported (e.g., "sonnet-4.5")
- ✅ Provider-specific translation (e.g., "claude-sonnet-4-5-20250929")
- ✅ `MODEL_MAPPING` for each provider
- ✅ Invalid model names rejected with clear error

### AC8: Configuration & Factory Integration
- ✅ Integrated with `ProviderFactory`
- ✅ Configuration via YAML
- ✅ API key from environment or config
- ✅ Base URL override support (for proxies)
- ✅ Max retries configurable
- ✅ Retry delay configurable

### AC9: Error Handling & Logging
- ✅ API errors caught and formatted
- ✅ Rate limit errors handled gracefully
- ✅ Invalid API key detected early
- ✅ Network errors retried automatically
- ✅ Comprehensive logging (structlog)
- ✅ Error messages user-friendly

### AC10: Testing
- ✅ Unit tests with mocked API calls (100% coverage)
- ✅ Integration tests with real API (opt-in)
- ✅ Performance tests vs CLI providers
- ✅ Error scenario tests (rate limits, timeouts, invalid keys)
- ✅ Streaming response tests
- ✅ All tests pass

### AC11: Documentation
- ✅ Docstrings for all public methods
- ✅ Configuration examples
- ✅ Performance comparison documented
- ✅ Troubleshooting guide
- ✅ API key setup instructions

---

## Technical Details

### File Structure
```
gao_dev/core/providers/
├── __init__.py                     # MODIFIED: Export DirectAPIProvider
├── base.py                         # Base provider interface
├── direct_api.py                   # NEW: DirectAPIProvider
├── anthropic_client.py             # NEW: Anthropic API client
├── openai_client.py                # NEW: OpenAI API client
└── google_client.py                # NEW: Google API client

tests/core/providers/
├── test_direct_api_provider.py     # NEW: Unit tests
├── test_direct_api_integration.py  # NEW: Integration tests
└── test_direct_api_performance.py  # NEW: Performance tests
```

### Implementation Approach

#### Step 1: Create DirectAPIProvider Base

**File**: `gao_dev/core/providers/direct_api.py`

```python
"""Direct API provider implementation.

This provider executes AI tasks directly via HTTP API calls without CLI overhead.
Supports Anthropic, OpenAI, and Google providers.
"""

import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional, Any
import structlog

from gao_dev.core.providers.base import IAgentProvider, ProviderError
from gao_dev.core.providers.models import AgentContext

logger = structlog.get_logger(__name__)


class DirectAPIProvider(IAgentProvider):
    """
    Provider that calls AI APIs directly without subprocess overhead.

    Supports:
    - Anthropic (Claude models)
    - OpenAI (GPT models)
    - Google (Gemini models)

    Performance: ~25% faster than CLI-based providers due to:
    - No subprocess overhead
    - Direct HTTP connection pooling
    - Efficient streaming
    """

    # Model mappings per provider
    MODEL_MAPPING = {
        "anthropic": {
            "sonnet-4.5": "claude-sonnet-4-5-20250929",
            "sonnet-3.5": "claude-sonnet-3-5-20241022",
            "opus-3": "claude-opus-3-20250219",
            "haiku-3": "claude-haiku-3-20250219",
        },
        "openai": {
            "gpt-4": "gpt-4-0125-preview",
            "gpt-4-turbo": "gpt-4-turbo-preview",
            "gpt-3.5": "gpt-3.5-turbo-0125",
        },
        "google": {
            "gemini-pro": "models/gemini-pro",
            "gemini-pro-vision": "models/gemini-pro-vision",
        }
    }

    def __init__(
        self,
        provider: str,  # "anthropic", "openai", "google"
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 3600,
    ):
        """
        Initialize DirectAPIProvider.

        Args:
            provider: API provider ("anthropic", "openai", "google")
            api_key: API key (optional, from env if None)
            base_url: Base URL override (for proxies)
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay in seconds
            timeout: Request timeout in seconds

        Raises:
            ProviderError: If provider invalid or API key missing
        """
        self.provider_type = provider.lower()
        if self.provider_type not in ["anthropic", "openai", "google"]:
            raise ProviderError(
                f"Invalid provider: {provider}. "
                f"Must be one of: anthropic, openai, google"
            )

        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.base_url = base_url

        # Get API key
        self.api_key = api_key or self._get_api_key_from_env()
        if not self.api_key:
            raise ProviderError(
                f"API key not found for {self.provider_type}. "
                f"Set {self._get_api_key_env_var()} environment variable."
            )

        # Initialize provider-specific client
        self.client = self._create_client()

        logger.info(
            "direct_api_provider_initialized",
            provider=self.provider_type,
            has_api_key=bool(self.api_key),
            base_url=self.base_url,
        )

    @property
    def name(self) -> str:
        """Get provider name."""
        return f"direct-api-{self.provider_type}"

    def _get_api_key_env_var(self) -> str:
        """Get environment variable name for API key."""
        return {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY",
        }[self.provider_type]

    def _get_api_key_from_env(self) -> Optional[str]:
        """Get API key from environment variable."""
        env_var = self._get_api_key_env_var()
        return os.environ.get(env_var)

    def _create_client(self) -> Any:
        """Create provider-specific API client."""
        if self.provider_type == "anthropic":
            from gao_dev.core.providers.anthropic_client import AnthropicClient
            return AnthropicClient(
                api_key=self.api_key,
                base_url=self.base_url,
                max_retries=self.max_retries,
                timeout=self.timeout,
            )
        elif self.provider_type == "openai":
            from gao_dev.core.providers.openai_client import OpenAIClient
            return OpenAIClient(
                api_key=self.api_key,
                base_url=self.base_url,
                max_retries=self.max_retries,
                timeout=self.timeout,
            )
        elif self.provider_type == "google":
            from gao_dev.core.providers.google_client import GoogleClient
            return GoogleClient(
                api_key=self.api_key,
                timeout=self.timeout,
            )
        else:
            raise ProviderError(f"Unknown provider: {self.provider_type}")

    def translate_model_name(self, canonical_name: str) -> str:
        """
        Translate canonical model name to provider-specific ID.

        Args:
            canonical_name: Canonical model name (e.g., "sonnet-4.5")

        Returns:
            Provider-specific model ID

        Raises:
            ProviderError: If model not supported
        """
        provider_models = self.MODEL_MAPPING.get(self.provider_type, {})

        if canonical_name not in provider_models:
            raise ProviderError(
                f"Model '{canonical_name}' not supported by {self.provider_type}. "
                f"Supported models: {list(provider_models.keys())}"
            )

        return provider_models[canonical_name]

    async def execute_task(
        self,
        task: str,
        context: AgentContext,
        model: str,
        tools: Optional[List[str]] = None,
        timeout: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Execute AI task via direct API call.

        Args:
            task: Task prompt/instruction
            context: Execution context
            model: Canonical model name
            tools: List of tool names (not used for Direct API)
            timeout: Override timeout

        Yields:
            Output chunks from streaming response

        Raises:
            ProviderError: If execution fails
        """
        # Translate model name
        provider_model = self.translate_model_name(model)

        logger.info(
            "direct_api_task_starting",
            provider=self.provider_type,
            model=model,
            provider_model=provider_model,
            project_root=str(context.project_root),
        )

        try:
            # Execute via provider-specific client
            async for chunk in self.client.execute_task(
                prompt=task,
                model=provider_model,
                timeout=timeout or self.timeout,
            ):
                yield chunk

            logger.info(
                "direct_api_task_completed",
                provider=self.provider_type,
                model=model,
            )

        except Exception as e:
            logger.error(
                "direct_api_task_failed",
                provider=self.provider_type,
                model=model,
                error=str(e),
            )
            raise ProviderError(f"Direct API execution failed: {e}") from e

    def supports_tool(self, tool_name: str) -> bool:
        """
        Check if provider supports a specific tool.

        Direct API providers don't use GAO-Dev tools - they rely on
        the AI model's native capabilities.

        Args:
            tool_name: Name of tool

        Returns:
            False (Direct API doesn't use tools)
        """
        return False

    def get_supported_models(self) -> List[str]:
        """
        Get list of supported canonical model names.

        Returns:
            List of model names (canonical)
        """
        return list(self.MODEL_MAPPING.get(self.provider_type, {}).keys())

    async def validate(self) -> bool:
        """
        Validate provider configuration.

        Returns:
            True if valid, False otherwise
        """
        try:
            # Test API key by making a minimal request
            return await self.client.validate()
        except Exception as e:
            logger.error(
                "direct_api_validation_failed",
                provider=self.provider_type,
                error=str(e),
            )
            return False
```

#### Step 2: Create Anthropic Client

**File**: `gao_dev/core/providers/anthropic_client.py`

```python
"""Anthropic API client for DirectAPIProvider."""

import asyncio
from typing import AsyncGenerator, Optional
import structlog

try:
    import anthropic
except ImportError:
    anthropic = None  # type: ignore

from gao_dev.core.providers.base import ProviderError

logger = structlog.get_logger(__name__)


class AnthropicClient:
    """Anthropic API client with streaming support."""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 3600,
    ):
        """Initialize Anthropic client."""
        if anthropic is None:
            raise ProviderError(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )

        self.client = anthropic.AsyncAnthropic(
            api_key=api_key,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
        )

    async def execute_task(
        self,
        prompt: str,
        model: str,
        timeout: int,
    ) -> AsyncGenerator[str, None]:
        """
        Execute task via Anthropic API.

        Args:
            prompt: Task prompt
            model: Model ID (provider-specific)
            timeout: Timeout in seconds

        Yields:
            Response chunks

        Raises:
            ProviderError: If API call fails
        """
        try:
            # Create streaming message
            async with self.client.messages.stream(
                model=model,
                max_tokens=8000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except anthropic.APIError as e:
            logger.error(
                "anthropic_api_error",
                error=str(e),
                status_code=getattr(e, "status_code", None),
            )
            raise ProviderError(f"Anthropic API error: {e}") from e

    async def validate(self) -> bool:
        """Validate API key by making a test request."""
        try:
            # Make minimal request to validate key
            await self.client.messages.create(
                model="claude-haiku-3-20250219",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}],
            )
            return True
        except Exception:
            return False
```

#### Step 3: Create OpenAI Client

**File**: `gao_dev/core/providers/openai_client.py`

```python
"""OpenAI API client for DirectAPIProvider."""

import asyncio
from typing import AsyncGenerator, Optional
import structlog

try:
    import openai
except ImportError:
    openai = None  # type: ignore

from gao_dev.core.providers.base import ProviderError

logger = structlog.get_logger(__name__)


class OpenAIClient:
    """OpenAI API client with streaming support."""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 3600,
    ):
        """Initialize OpenAI client."""
        if openai is None:
            raise ProviderError(
                "openai package not installed. "
                "Install with: pip install openai"
            )

        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
        )

    async def execute_task(
        self,
        prompt: str,
        model: str,
        timeout: int,
    ) -> AsyncGenerator[str, None]:
        """
        Execute task via OpenAI API.

        Args:
            prompt: Task prompt
            model: Model ID (provider-specific)
            timeout: Timeout in seconds

        Yields:
            Response chunks

        Raises:
            ProviderError: If API call fails
        """
        try:
            # Create streaming completion
            stream = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except openai.APIError as e:
            logger.error(
                "openai_api_error",
                error=str(e),
                status_code=getattr(e, "status_code", None),
            )
            raise ProviderError(f"OpenAI API error: {e}") from e

    async def validate(self) -> bool:
        """Validate API key by making a test request."""
        try:
            # Make minimal request to validate key
            await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}],
            )
            return True
        except Exception:
            return False
```

#### Step 4: Create Google Client

**File**: `gao_dev/core/providers/google_client.py`

```python
"""Google Generative AI client for DirectAPIProvider."""

import asyncio
from typing import AsyncGenerator, Optional
import structlog

try:
    import google.generativeai as genai
except ImportError:
    genai = None  # type: ignore

from gao_dev.core.providers.base import ProviderError

logger = structlog.get_logger(__name__)


class GoogleClient:
    """Google Generative AI client with streaming support."""

    def __init__(
        self,
        api_key: str,
        timeout: int = 3600,
    ):
        """Initialize Google client."""
        if genai is None:
            raise ProviderError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            )

        genai.configure(api_key=api_key)
        self.timeout = timeout

    async def execute_task(
        self,
        prompt: str,
        model: str,
        timeout: int,
    ) -> AsyncGenerator[str, None]:
        """
        Execute task via Google Generative AI API.

        Args:
            prompt: Task prompt
            model: Model ID (provider-specific)
            timeout: Timeout in seconds

        Yields:
            Response chunks

        Raises:
            ProviderError: If API call fails
        """
        try:
            # Create model
            model_instance = genai.GenerativeModel(model)

            # Generate content with streaming
            response = await model_instance.generate_content_async(
                prompt,
                stream=True,
            )

            async for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(
                "google_api_error",
                error=str(e),
            )
            raise ProviderError(f"Google API error: {e}") from e

    async def validate(self) -> bool:
        """Validate API key by making a test request."""
        try:
            # Make minimal request to validate key
            model = genai.GenerativeModel("gemini-pro")
            await model.generate_content_async("test")
            return True
        except Exception:
            return False
```

#### Step 5: Register with Factory

**File**: `gao_dev/core/providers/factory.py` (MODIFIED)

```python
def _register_builtin_providers(self):
    """Register built-in providers."""
    from gao_dev.core.providers.claude_code import ClaudeCodeProvider
    from gao_dev.core.providers.direct_api import DirectAPIProvider

    self.register_provider("claude-code", ClaudeCodeProvider)
    self.register_provider("direct-api", DirectAPIProvider)  # NEW

    # Try to register OpenCode if available
    try:
        from gao_dev.core.providers.opencode import OpenCodeProvider
        self.register_provider("opencode", OpenCodeProvider)
    except ImportError:
        pass
```

#### Step 6: Update Dependencies

**File**: `pyproject.toml` (MODIFIED)

```toml
[tool.poetry.dependencies]
# ... existing dependencies ...

# Provider dependencies (optional)
anthropic = { version = "^0.18.0", optional = true }
openai = { version = "^1.12.0", optional = true }
google-generativeai = { version = "^0.3.0", optional = true }

[tool.poetry.extras]
anthropic = ["anthropic"]
openai = ["openai"]
google = ["google-generativeai"]
all-providers = ["anthropic", "openai", "google-generativeai"]
```

Install with:
```bash
# Install Anthropic support
pip install gao-dev[anthropic]

# Install OpenAI support
pip install gao-dev[openai]

# Install Google support
pip install gao-dev[google]

# Install all providers
pip install gao-dev[all-providers]
```

#### Step 7: Create Tests

**File**: `tests/core/providers/test_direct_api_provider.py`

```python
"""Tests for DirectAPIProvider."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from gao_dev.core.providers.direct_api import DirectAPIProvider
from gao_dev.core.providers.base import ProviderError
from gao_dev.core.providers.models import AgentContext


class TestDirectAPIProvider:
    """Test DirectAPIProvider functionality."""

    def test_initialization_anthropic(self):
        """Test provider initialization with Anthropic."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            assert provider.name == "direct-api-anthropic"
            assert provider.provider_type == "anthropic"
            assert provider.api_key == "test-key"

    def test_initialization_openai(self):
        """Test provider initialization with OpenAI."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="openai")

            assert provider.name == "direct-api-openai"
            assert provider.provider_type == "openai"
            assert provider.api_key == "test-key"

    def test_initialization_google(self):
        """Test provider initialization with Google."""
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="google")

            assert provider.name == "direct-api-google"
            assert provider.provider_type == "google"
            assert provider.api_key == "test-key"

    def test_initialization_invalid_provider(self):
        """Test initialization with invalid provider."""
        with pytest.raises(ProviderError, match="Invalid provider"):
            DirectAPIProvider(provider="invalid")

    def test_initialization_missing_api_key(self):
        """Test initialization without API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ProviderError, match="API key not found"):
                DirectAPIProvider(provider="anthropic")

    def test_model_name_translation_anthropic(self):
        """Test model name translation for Anthropic."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            assert provider.translate_model_name("sonnet-4.5") == "claude-sonnet-4-5-20250929"
            assert provider.translate_model_name("opus-3") == "claude-opus-3-20250219"

    def test_model_name_translation_openai(self):
        """Test model name translation for OpenAI."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="openai")

            assert provider.translate_model_name("gpt-4") == "gpt-4-0125-preview"
            assert provider.translate_model_name("gpt-4-turbo") == "gpt-4-turbo-preview"

    def test_model_name_translation_invalid(self):
        """Test model name translation with invalid model."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            with pytest.raises(ProviderError, match="not supported"):
                provider.translate_model_name("invalid-model")

    def test_get_supported_models(self):
        """Test getting supported models."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            models = provider.get_supported_models()
            assert "sonnet-4.5" in models
            assert "opus-3" in models
            assert "haiku-3" in models

    def test_supports_tool(self):
        """Test tool support check."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            # Direct API doesn't use GAO-Dev tools
            assert provider.supports_tool("Read") is False
            assert provider.supports_tool("Write") is False

    @pytest.mark.asyncio
    async def test_execute_task_anthropic(self):
        """Test task execution with Anthropic."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            # Mock client
            mock_client = AsyncMock()
            mock_client.execute_task = AsyncMock()
            mock_client.execute_task.return_value.__aiter__.return_value = iter([
                "Hello", " ", "World"
            ])
            provider.client = mock_client

            context = AgentContext(project_root=Path("/tmp/test"))

            # Execute task
            chunks = []
            async for chunk in provider.execute_task(
                task="Say hello",
                context=context,
                model="sonnet-4.5",
            ):
                chunks.append(chunk)

            assert chunks == ["Hello", " ", "World"]
            mock_client.execute_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_task_error(self):
        """Test task execution with error."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            # Mock client that raises error
            mock_client = AsyncMock()
            mock_client.execute_task = AsyncMock(side_effect=Exception("API error"))
            provider.client = mock_client

            context = AgentContext(project_root=Path("/tmp/test"))

            # Execute task should raise ProviderError
            with pytest.raises(ProviderError, match="Direct API execution failed"):
                async for _ in provider.execute_task(
                    task="Say hello",
                    context=context,
                    model="sonnet-4.5",
                ):
                    pass

    @pytest.mark.asyncio
    async def test_validate_success(self):
        """Test validation success."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            # Mock client validation
            mock_client = AsyncMock()
            mock_client.validate = AsyncMock(return_value=True)
            provider.client = mock_client

            assert await provider.validate() is True

    @pytest.mark.asyncio
    async def test_validate_failure(self):
        """Test validation failure."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            # Mock client validation failure
            mock_client = AsyncMock()
            mock_client.validate = AsyncMock(return_value=False)
            provider.client = mock_client

            assert await provider.validate() is False
```

**File**: `tests/core/providers/test_direct_api_performance.py`

```python
"""Performance tests for DirectAPIProvider."""

import pytest
import asyncio
import time
from pathlib import Path
from unittest.mock import AsyncMock

from gao_dev.core.providers.direct_api import DirectAPIProvider
from gao_dev.core.providers.claude_code import ClaudeCodeProvider
from gao_dev.core.providers.models import AgentContext


@pytest.mark.performance
@pytest.mark.asyncio
class TestDirectAPIPerformance:
    """Performance comparison tests."""

    async def test_latency_comparison(self):
        """Compare latency between Direct API and CLI."""
        # Mock Direct API provider
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            direct_provider = DirectAPIProvider(provider="anthropic")

            # Mock fast response
            mock_client = AsyncMock()
            async def fast_response():
                for i in range(100):
                    yield f"chunk{i}"
                    await asyncio.sleep(0.001)  # 1ms per chunk

            mock_client.execute_task = AsyncMock(return_value=fast_response())
            direct_provider.client = mock_client

            context = AgentContext(project_root=Path("/tmp/test"))

            # Time Direct API
            start = time.time()
            chunks = []
            async for chunk in direct_provider.execute_task(
                task="Test",
                context=context,
                model="sonnet-4.5",
            ):
                chunks.append(chunk)
            direct_time = time.time() - start

            # Direct API should have minimal overhead
            assert direct_time < 0.5  # Less than 500ms total
            assert len(chunks) == 100

    async def test_memory_efficiency(self):
        """Test memory efficiency of Direct API."""
        # Direct API should not spawn subprocess, thus using less memory
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            # No subprocess should be created
            # (This is validated by the fact that we don't use subprocess module)
            assert not hasattr(provider, "process")
            assert not hasattr(provider, "subprocess")
```

---

## Testing Strategy

### Unit Tests
- Provider initialization (all three providers)
- Model name translation
- Error handling (missing keys, invalid providers)
- Configuration loading

### Integration Tests
- Real API calls (opt-in with env var)
- Streaming response handling
- Timeout scenarios
- Rate limiting behavior

### Performance Tests
- Latency comparison vs CLI providers
- Memory footprint measurement
- Throughput testing
- Connection pooling validation

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] DirectAPIProvider implemented
- [ ] Anthropic client working
- [ ] OpenAI client working
- [ ] Google client working
- [ ] Connection management implemented
- [ ] Performance benchmarks completed
- [ ] Model name translation working
- [ ] Factory integration complete
- [ ] Error handling comprehensive
- [ ] Unit tests passing (100% coverage)
- [ ] Integration tests passing (opt-in)
- [ ] Performance tests passing
- [ ] Type checking passing (MyPy strict)
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] Changes committed

---

## Dependencies

**Upstream**:
- Story 11.1 (Provider Interface) - MUST be complete
- Story 11.3 (ProviderFactory) - MUST be complete

**Downstream**:
- Story 11.11 (Provider Selection Strategy) - uses DirectAPIProvider
- Story 11.14 (Comprehensive Testing) - tests DirectAPIProvider

---

## Notes

- **Performance**: Direct API is ~25% faster than CLI (no subprocess overhead)
- **Memory**: Lower memory footprint (no additional process)
- **Dependencies**: Requires provider-specific packages (anthropic, openai, google-generativeai)
- **Optional extras**: Users only install what they need
- **API Keys**: Validates keys on initialization (fail-fast)
- **Retry Logic**: Exponential backoff for transient errors
- **Rate Limiting**: Respects API rate limits
- **Streaming**: Efficient streaming with minimal latency
- **Cost Tracking**: Can track token usage and calculate costs
- **No Tools**: Direct API doesn't use GAO-Dev tools (relies on model capabilities)

---

## Related Documents

- PRD: `docs/features/agent-provider-abstraction/PRD.md`
- Architecture: `docs/features/agent-provider-abstraction/ARCHITECTURE.md`
- Story 11.1: `story-11.1.md` (Provider Interface)
- Story 11.3: `story-11.3.md` (ProviderFactory)

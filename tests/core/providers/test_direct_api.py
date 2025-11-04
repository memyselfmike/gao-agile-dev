"""Tests for DirectAPIProvider.

Epic: 11 - Agent Provider Abstraction
Story: 11.10 - Implement Direct API Provider
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from gao_dev.core.providers.direct_api import DirectAPIProvider
from gao_dev.core.providers.base import IAgentProvider
from gao_dev.core.providers.exceptions import (
    ProviderConfigurationError,
    ProviderExecutionError,
    ModelNotFoundError
)
from gao_dev.core.providers.models import AgentContext


class TestDirectAPIProviderInitialization:
    """Test DirectAPIProvider initialization."""

    def test_initialization_anthropic(self):
        """Test provider initialization with Anthropic."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            assert provider.name == "direct-api-anthropic"
            assert provider.version == "1.0.0"
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
        with pytest.raises(ProviderConfigurationError, match="Invalid provider"):
            DirectAPIProvider(provider="invalid")

    def test_initialization_missing_api_key(self):
        """Test initialization without API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ProviderConfigurationError, match="API key not found"):
                DirectAPIProvider(provider="anthropic")

    def test_initialization_with_explicit_key(self):
        """Test initialization with explicit API key."""
        provider = DirectAPIProvider(provider="anthropic", api_key="explicit-key")

        assert provider.api_key == "explicit-key"

    def test_initialization_with_config(self):
        """Test initialization with configuration."""
        provider = DirectAPIProvider(
            provider="anthropic",
            api_key="test-key",
            base_url="https://custom.api.com",
            max_retries=5,
            retry_delay=2.0,
            timeout=7200
        )

        assert provider.base_url == "https://custom.api.com"
        assert provider.max_retries == 5
        assert provider.retry_delay == 2.0
        assert provider.timeout == 7200


class TestDirectAPIProviderInterface:
    """Test DirectAPIProvider implements IAgentProvider."""

    def test_implements_interface(self):
        """Test that DirectAPIProvider implements IAgentProvider."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            assert isinstance(provider, IAgentProvider)

    def test_has_required_properties(self):
        """Test required properties exist."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            assert hasattr(provider, "name")
            assert hasattr(provider, "version")
            assert isinstance(provider.name, str)
            assert isinstance(provider.version, str)

    def test_has_required_methods(self):
        """Test required methods exist."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            assert hasattr(provider, "execute_task")
            assert hasattr(provider, "supports_tool")
            assert hasattr(provider, "get_supported_models")
            assert hasattr(provider, "translate_model_name")
            assert hasattr(provider, "validate_configuration")
            assert hasattr(provider, "get_configuration_schema")
            assert hasattr(provider, "initialize")
            assert hasattr(provider, "cleanup")


class TestModelTranslation:
    """Test model name translation."""

    def test_anthropic_model_translation(self):
        """Test Anthropic model name translation."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            assert provider.translate_model_name("sonnet-4.5") == "claude-sonnet-4-5-20250929"
            assert provider.translate_model_name("opus-3") == "claude-opus-3-20250219"
            assert provider.translate_model_name("haiku-3") == "claude-haiku-3-20250219"

    def test_openai_model_translation(self):
        """Test OpenAI model name translation."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="openai")

            assert provider.translate_model_name("gpt-4") == "gpt-4-0125-preview"
            assert provider.translate_model_name("gpt-4-turbo") == "gpt-4-turbo-preview"

    def test_google_model_translation(self):
        """Test Google model name translation."""
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="google")

            assert provider.translate_model_name("gemini-pro") == "models/gemini-pro"

    def test_invalid_model_raises_error(self):
        """Test translation of invalid model raises error."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            with pytest.raises(ModelNotFoundError, match="not found"):
                provider.translate_model_name("invalid-model")


class TestGetSupportedModels:
    """Test getting supported models."""

    def test_anthropic_supported_models(self):
        """Test Anthropic supported models."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            models = provider.get_supported_models()

            assert "sonnet-4.5" in models
            assert "sonnet-3.5" in models
            assert "opus-3" in models
            assert "haiku-3" in models

    def test_openai_supported_models(self):
        """Test OpenAI supported models."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="openai")

            models = provider.get_supported_models()

            assert "gpt-4" in models
            assert "gpt-4-turbo" in models
            assert "gpt-3.5" in models


class TestToolSupport:
    """Test tool support."""

    def test_supports_tool_returns_false(self):
        """Test that Direct API doesn't support GAO-Dev tools."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            # Direct API doesn't use GAO-Dev tools
            assert provider.supports_tool("Read") is False
            assert provider.supports_tool("Write") is False
            assert provider.supports_tool("Bash") is False


class TestConfigurationValidation:
    """Test configuration validation."""

    @pytest.mark.asyncio
    async def test_validate_configuration_success(self):
        """Test successful configuration validation."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            # Mock client validation
            mock_client = AsyncMock()
            mock_client.validate = AsyncMock(return_value=True)
            provider.client = mock_client

            result = await provider.validate_configuration()

            assert result is True
            mock_client.validate.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_configuration_failure(self):
        """Test configuration validation failure."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            # Mock client validation failure
            mock_client = AsyncMock()
            mock_client.validate = AsyncMock(return_value=False)
            provider.client = mock_client

            result = await provider.validate_configuration()

            assert result is False


class TestConfigurationSchema:
    """Test configuration schema."""

    def test_get_configuration_schema(self):
        """Test getting configuration schema."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            schema = provider.get_configuration_schema()

            assert isinstance(schema, dict)
            assert schema["type"] == "object"
            assert "provider" in schema["properties"]
            assert "api_key" in schema["properties"]
            assert "provider" in schema["required"]


class TestExecuteTask:
    """Test task execution."""

    @pytest.mark.asyncio
    async def test_execute_task_success(self):
        """Test successful task execution."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            # Mock client
            mock_client = MagicMock()

            async def mock_execute(prompt, model, timeout):
                yield "Hello"
                yield " "
                yield "World"

            mock_client.execute_task = mock_execute
            provider.client = mock_client

            context = AgentContext(project_root=Path("/tmp/test"))

            # Execute task
            chunks = []
            async for chunk in provider.execute_task(
                task="Say hello",
                context=context,
                model="sonnet-4.5",
                tools=[],
            ):
                chunks.append(chunk)

            assert chunks == ["Hello", " ", "World"]

    @pytest.mark.asyncio
    async def test_execute_task_error(self):
        """Test task execution with error."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            # Mock client that raises error
            mock_client = MagicMock()

            async def mock_execute_error(prompt, model, timeout):
                raise Exception("API error")
                yield  # Never reached

            mock_client.execute_task = mock_execute_error
            provider.client = mock_client

            context = AgentContext(project_root=Path("/tmp/test"))

            # Execute task should raise ProviderExecutionError
            with pytest.raises(ProviderExecutionError, match="Direct API execution failed"):
                async for _ in provider.execute_task(
                    task="Say hello",
                    context=context,
                    model="sonnet-4.5",
                    tools=[],
                ):
                    pass


class TestLifecycle:
    """Test provider lifecycle."""

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test provider initialization."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            await provider.initialize()

            assert provider._initialized is True

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self):
        """Test initialization is idempotent."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            await provider.initialize()
            await provider.initialize()  # Should not fail

            assert provider._initialized is True

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test provider cleanup."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = DirectAPIProvider(provider="anthropic")

            await provider.initialize()
            await provider.cleanup()

            assert provider._initialized is False

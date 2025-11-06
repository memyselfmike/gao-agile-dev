"""Unit tests for OpenCodeSDKProvider.

Tests the core functionality of the OpenCode SDK-based provider,
including initialization, task execution, model translation, and
error handling.

Story: 19.2 - Implement OpenCodeSDKProvider Core
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from pathlib import Path

from gao_dev.core.providers.opencode_sdk import OpenCodeSDKProvider
from gao_dev.core.providers.models import AgentContext
from gao_dev.core.providers.exceptions import (
    ProviderInitializationError,
    ProviderExecutionError,
    ProviderConfigurationError,
    ModelNotSupportedError,
)


class TestOpenCodeSDKProviderInit:
    """Test OpenCodeSDKProvider initialization."""

    def test_init_default(self):
        """Test provider initialization with default parameters."""
        provider = OpenCodeSDKProvider()

        assert provider.server_url == "http://localhost:4096"
        assert provider.sdk_client is None
        assert provider.session is None
        assert provider._initialized is False

    def test_init_custom_server_url(self):
        """Test provider initialization with custom server URL."""
        provider = OpenCodeSDKProvider(server_url="http://localhost:8080")

        assert provider.server_url == "http://localhost:8080"

    def test_init_with_api_key(self):
        """Test provider initialization with API key."""
        provider = OpenCodeSDKProvider(api_key="sk-test-key")

        assert provider.api_key == "sk-test-key"

    def test_init_api_key_from_env(self):
        """Test provider initialization gets API key from environment."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-env-key'}):
            provider = OpenCodeSDKProvider()

            assert provider.api_key == "sk-env-key"

    def test_provider_name(self):
        """Test provider name property."""
        provider = OpenCodeSDKProvider()

        assert provider.name == "opencode-sdk"

    def test_provider_version(self):
        """Test provider version property."""
        provider = OpenCodeSDKProvider()

        assert provider.version == "1.0.0"


class TestOpenCodeSDKProviderInitialization:
    """Test provider initialize() and cleanup() methods."""

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful provider initialization."""
        with patch('opencode_ai.Opencode') as mock_opencode:
            mock_client = MagicMock()
            mock_opencode.return_value = mock_client

            provider = OpenCodeSDKProvider()
            await provider.initialize()

            assert provider._initialized is True
            assert provider.sdk_client is not None
            mock_opencode.assert_called_once_with(base_url="http://localhost:4096")

    @pytest.mark.asyncio
    async def test_initialize_already_initialized(self):
        """Test initialization when already initialized (idempotent)."""
        with patch('opencode_ai.Opencode') as mock_opencode:
            provider = OpenCodeSDKProvider()
            await provider.initialize()
            await provider.initialize()  # Second call

            # Should only create client once
            assert mock_opencode.call_count == 1

    @pytest.mark.asyncio
    async def test_initialize_sdk_not_installed(self):
        """Test initialization failure when SDK not installed."""
        # Mock the import to fail within initialize()
        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == 'opencode_ai':
                raise ImportError("No module named 'opencode_ai'")
            return real_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mock_import):
            provider = OpenCodeSDKProvider()

            with pytest.raises(ProviderInitializationError) as exc_info:
                await provider.initialize()

            assert "not installed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_initialize_connection_error(self):
        """Test initialization failure with connection error."""
        with patch('opencode_ai.Opencode', side_effect=Exception("Connection refused")):
            provider = OpenCodeSDKProvider()

            with pytest.raises(ProviderInitializationError) as exc_info:
                await provider.initialize()

            assert "failed to initialize" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test provider cleanup."""
        with patch('opencode_ai.Opencode'):
            provider = OpenCodeSDKProvider()
            await provider.initialize()

            provider.session = MagicMock()
            provider.sdk_client = MagicMock()

            await provider.cleanup()

            assert provider.session is None
            assert provider.sdk_client is None
            assert provider._initialized is False

    @pytest.mark.asyncio
    async def test_cleanup_error_handling(self):
        """Test cleanup handles errors gracefully."""
        provider = OpenCodeSDKProvider()
        provider.session = MagicMock()
        provider.session.close = Mock(side_effect=Exception("Close failed"))

        # Should not raise exception
        await provider.cleanup()

        assert provider._initialized is False


class TestOpenCodeSDKProviderModelTranslation:
    """Test model name translation."""

    def test_translate_model_claude_full_name(self):
        """Test translating full Claude model name."""
        provider = OpenCodeSDKProvider()
        provider_id, model_id = provider._translate_model("claude-sonnet-4-5-20250929")

        assert provider_id == "anthropic"
        assert model_id == "claude-sonnet-4.5"

    def test_translate_model_canonical_name(self):
        """Test translating canonical model name."""
        provider = OpenCodeSDKProvider()
        provider_id, model_id = provider._translate_model("sonnet-4.5")

        assert provider_id == "anthropic"
        assert model_id == "claude-sonnet-4.5"

    def test_translate_model_openai(self):
        """Test translating OpenAI model name."""
        provider = OpenCodeSDKProvider()
        provider_id, model_id = provider._translate_model("gpt-4")

        assert provider_id == "openai"
        assert model_id == "gpt-4"

    def test_translate_model_not_found(self):
        """Test model translation with unsupported model."""
        provider = OpenCodeSDKProvider()

        with pytest.raises(ModelNotSupportedError) as exc_info:
            provider._translate_model("unsupported-model-xyz")

        assert "not found" in str(exc_info.value).lower() or "not supported" in str(exc_info.value).lower()
        assert exc_info.value.model_name == "unsupported-model-xyz"

    def test_translate_model_name_public_method(self):
        """Test public translate_model_name method."""
        provider = OpenCodeSDKProvider()
        model_id = provider.translate_model_name("sonnet-4.5")

        assert model_id == "anthropic/claude-sonnet-4.5"


class TestOpenCodeSDKProviderTaskExecution:
    """Test task execution functionality."""

    @pytest.mark.asyncio
    async def test_execute_task_not_initialized(self):
        """Test task execution fails when not initialized."""
        provider = OpenCodeSDKProvider()
        context = AgentContext(project_root=Path("/test"))

        with pytest.raises(ProviderConfigurationError) as exc_info:
            async for _ in provider.execute_task(
                task="Test task",
                context=context,
                model="sonnet-4.5",
                tools=["Read"],
            ):
                pass

        assert "not initialized" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_execute_task_success(self):
        """Test successful task execution."""
        with patch('opencode_ai.Opencode') as mock_opencode:
            # Setup mocks
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.content = "Task completed successfully"
            mock_response.usage = MagicMock()
            mock_response.usage.input_tokens = 100
            mock_response.usage.output_tokens = 50
            mock_session.chat.return_value = mock_response

            mock_client = MagicMock()
            mock_client.create_session.return_value = mock_session
            mock_opencode.return_value = mock_client

            # Execute task
            provider = OpenCodeSDKProvider()
            await provider.initialize()

            context = AgentContext(project_root=Path("/test"))
            results = []
            async for result in provider.execute_task(
                task="Test prompt",
                context=context,
                model="sonnet-4.5",
                tools=["Read", "Write"],
            ):
                results.append(result)

            # Verify results
            assert len(results) == 1
            assert results[0] == "Task completed successfully"

            # Verify SDK calls
            mock_client.create_session.assert_called_once_with(
                provider_id="anthropic",
                model_id="claude-sonnet-4.5",
            )
            mock_session.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_task_session_reuse(self):
        """Test that session is reused for multiple tasks."""
        with patch('opencode_ai.Opencode') as mock_opencode:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.content = "Response"
            mock_response.usage = MagicMock()
            mock_response.usage.input_tokens = 10
            mock_response.usage.output_tokens = 5
            mock_session.chat.return_value = mock_response

            mock_client = MagicMock()
            mock_client.create_session.return_value = mock_session
            mock_opencode.return_value = mock_client

            provider = OpenCodeSDKProvider()
            await provider.initialize()

            context = AgentContext(project_root=Path("/test"))

            # Execute first task
            async for _ in provider.execute_task(
                task="Task 1",
                context=context,
                model="sonnet-4.5",
                tools=["Read"],
            ):
                pass

            # Execute second task
            async for _ in provider.execute_task(
                task="Task 2",
                context=context,
                model="sonnet-4.5",
                tools=["Read"],
            ):
                pass

            # Session should be created only once
            assert mock_client.create_session.call_count == 1
            # Chat should be called twice
            assert mock_session.chat.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_task_invalid_model(self):
        """Test task execution with invalid model."""
        with patch('opencode_ai.Opencode'):
            provider = OpenCodeSDKProvider()
            await provider.initialize()

            context = AgentContext(project_root=Path("/test"))

            with pytest.raises(ModelNotSupportedError):
                async for _ in provider.execute_task(
                    task="Test",
                    context=context,
                    model="invalid-model-123",
                    tools=["Read"],
                ):
                    pass

    @pytest.mark.asyncio
    async def test_execute_task_sdk_error(self):
        """Test task execution with SDK error."""
        with patch('opencode_ai.Opencode') as mock_opencode:
            mock_session = MagicMock()
            mock_session.chat.side_effect = Exception("SDK communication error")

            mock_client = MagicMock()
            mock_client.create_session.return_value = mock_session
            mock_opencode.return_value = mock_client

            provider = OpenCodeSDKProvider()
            await provider.initialize()

            context = AgentContext(project_root=Path("/test"))

            with pytest.raises(ProviderExecutionError) as exc_info:
                async for _ in provider.execute_task(
                    task="Test",
                    context=context,
                    model="sonnet-4.5",
                    tools=["Read"],
                ):
                    pass

            assert "failed to execute" in str(exc_info.value).lower()


class TestOpenCodeSDKProviderResponseExtraction:
    """Test response content and usage extraction."""

    def test_extract_content_from_content_attribute(self):
        """Test extracting content from response.content."""
        provider = OpenCodeSDKProvider()
        response = MagicMock()
        response.content = "Test content"

        content = provider._extract_content(response)

        assert content == "Test content"

    def test_extract_content_from_text_attribute(self):
        """Test extracting content from response.text."""
        provider = OpenCodeSDKProvider()
        response = MagicMock(spec=[])
        response.text = "Test text"

        content = provider._extract_content(response)

        assert content == "Test text"

    def test_extract_content_from_string(self):
        """Test extracting content from string response."""
        provider = OpenCodeSDKProvider()
        response = "Direct string response"

        content = provider._extract_content(response)

        assert content == "Direct string response"

    def test_extract_content_unknown_format(self):
        """Test extracting content from unknown format."""
        provider = OpenCodeSDKProvider()
        response = MagicMock(spec=[])  # No known attributes

        content = provider._extract_content(response)

        # Should convert to string
        assert isinstance(content, str)

    def test_extract_usage_full(self):
        """Test extracting full usage statistics."""
        provider = OpenCodeSDKProvider()
        response = MagicMock()
        response.usage.input_tokens = 100
        response.usage.output_tokens = 50
        response.usage.total_tokens = 150

        usage = provider._extract_usage(response)

        assert usage['input_tokens'] == 100
        assert usage['output_tokens'] == 50
        assert usage['total_tokens'] == 150

    def test_extract_usage_partial(self):
        """Test extracting partial usage statistics."""
        provider = OpenCodeSDKProvider()
        response = MagicMock()
        response.usage = MagicMock(spec=['input_tokens'])
        response.usage.input_tokens = 100
        # No output_tokens or total_tokens attributes

        usage = provider._extract_usage(response)

        assert usage['input_tokens'] == 100
        assert 'output_tokens' not in usage

    def test_extract_usage_no_usage(self):
        """Test extracting usage when not available."""
        provider = OpenCodeSDKProvider()
        response = MagicMock(spec=[])  # No usage attribute

        usage = provider._extract_usage(response)

        assert usage == {}

    def test_extract_usage_error(self):
        """Test usage extraction handles errors gracefully."""
        provider = OpenCodeSDKProvider()
        response = MagicMock()
        response.usage.input_tokens = "not-a-number"  # Invalid type

        # Should not raise, returns empty dict
        usage = provider._extract_usage(response)

        assert isinstance(usage, dict)


class TestOpenCodeSDKProviderToolSupport:
    """Test tool support checking."""

    def test_supports_read_tool(self):
        """Test that Read tool is supported."""
        provider = OpenCodeSDKProvider()

        assert provider.supports_tool("Read") is True

    def test_supports_write_tool(self):
        """Test that Write tool is supported."""
        provider = OpenCodeSDKProvider()

        assert provider.supports_tool("Write") is True

    def test_supports_bash_tool(self):
        """Test that Bash tool is supported."""
        provider = OpenCodeSDKProvider()

        assert provider.supports_tool("Bash") is True

    def test_supports_partial_tool(self):
        """Test that partially supported tools return True."""
        provider = OpenCodeSDKProvider()

        assert provider.supports_tool("Grep") is True
        assert provider.supports_tool("MultiEdit") is True

    def test_not_supports_webfetch_tool(self):
        """Test that WebFetch is not supported."""
        provider = OpenCodeSDKProvider()

        assert provider.supports_tool("WebFetch") is False

    def test_not_supports_todowrite_tool(self):
        """Test that TodoWrite is not supported."""
        provider = OpenCodeSDKProvider()

        assert provider.supports_tool("TodoWrite") is False

    def test_not_supports_unknown_tool(self):
        """Test that unknown tools are not supported."""
        provider = OpenCodeSDKProvider()

        assert provider.supports_tool("UnknownTool123") is False


class TestOpenCodeSDKProviderModelSupport:
    """Test model support and listing."""

    def test_get_supported_models(self):
        """Test getting list of supported models."""
        provider = OpenCodeSDKProvider()
        models = provider.get_supported_models()

        # Should return all canonical names
        assert "sonnet-4.5" in models
        assert "opus-4" in models
        assert "gpt-4" in models
        assert "claude-sonnet-4-5-20250929" in models

    def test_get_supported_models_not_empty(self):
        """Test that supported models list is not empty."""
        provider = OpenCodeSDKProvider()
        models = provider.get_supported_models()

        assert len(models) > 0


class TestOpenCodeSDKProviderConfiguration:
    """Test configuration validation and schema."""

    @pytest.mark.asyncio
    async def test_validate_configuration_valid(self):
        """Test configuration validation with valid setup."""
        # Mock the import check
        with patch('builtins.__import__') as mock_import:
            mock_import.return_value = MagicMock()  # Successfully import
            provider = OpenCodeSDKProvider(
                server_url="http://localhost:4096",
                api_key="sk-test"
            )

            is_valid = await provider.validate_configuration()

            assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_configuration_no_server_url(self):
        """Test configuration validation without server URL."""
        provider = OpenCodeSDKProvider(server_url="")

        is_valid = await provider.validate_configuration()

        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_configuration_sdk_not_installed(self):
        """Test configuration validation when SDK not installed."""
        # Mock the import to fail
        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == 'opencode_ai':
                raise ImportError("No module named 'opencode_ai'")
            return real_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mock_import):
            provider = OpenCodeSDKProvider()

            is_valid = await provider.validate_configuration()

            assert is_valid is False

    def test_get_configuration_schema(self):
        """Test getting configuration schema."""
        provider = OpenCodeSDKProvider()
        schema = provider.get_configuration_schema()

        assert schema['type'] == 'object'
        assert 'server_url' in schema['properties']
        assert 'api_key' in schema['properties']
        assert schema['properties']['server_url']['type'] == 'string'


class TestOpenCodeSDKProviderRepr:
    """Test string representation."""

    def test_repr(self):
        """Test __repr__ method."""
        provider = OpenCodeSDKProvider(
            server_url="http://localhost:4096",
            api_key="sk-test"
        )

        repr_str = repr(provider)

        assert "OpenCodeSDKProvider" in repr_str
        assert "http://localhost:4096" in repr_str
        assert "has_api_key=True" in repr_str
        assert "initialized=False" in repr_str

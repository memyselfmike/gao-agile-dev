"""Unit tests for OpenCodeProvider.

Tests cover:
- Provider properties and metadata
- Model translation for all AI providers
- Tool support checking
- Configuration validation
- CLI detection
- Task execution (mocked subprocess)
- Error handling
- Timeout scenarios

Story: 11.7 - Implement OpenCodeProvider
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess
import os

from gao_dev.core.providers.opencode import OpenCodeProvider
from gao_dev.core.providers.models import AgentContext
from gao_dev.core.providers.exceptions import (
    ProviderExecutionError,
    ProviderTimeoutError,
    ProviderConfigurationError,
    ModelNotSupportedError
)


class TestOpenCodeProviderBasic:
    """Test basic provider properties and initialization."""

    def test_provider_name(self):
        """Test provider name is 'opencode'."""
        provider = OpenCodeProvider()
        assert provider.name == "opencode"

    def test_provider_version(self):
        """Test provider version."""
        provider = OpenCodeProvider()
        assert provider.version == "1.0.0"

    def test_default_ai_provider(self):
        """Test default AI provider is anthropic."""
        provider = OpenCodeProvider()
        assert provider.ai_provider == "anthropic"

    def test_custom_ai_provider(self):
        """Test custom AI provider."""
        provider = OpenCodeProvider(ai_provider="openai")
        assert provider.ai_provider == "openai"

    def test_ai_provider_lowercase(self):
        """Test AI provider is lowercased."""
        provider = OpenCodeProvider(ai_provider="OpenAI")
        assert provider.ai_provider == "openai"

    def test_api_key_from_parameter(self):
        """Test API key from parameter."""
        provider = OpenCodeProvider(api_key="test-key")
        assert provider.api_key == "test-key"

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"})
    def test_api_key_from_environment(self):
        """Test API key from environment variable."""
        provider = OpenCodeProvider(ai_provider="anthropic")
        assert provider.api_key == "env-key"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "openai-key"})
    def test_api_key_openai_from_environment(self):
        """Test OpenAI API key from environment."""
        provider = OpenCodeProvider(ai_provider="openai")
        assert provider.api_key == "openai-key"

    def test_repr(self):
        """Test string representation."""
        provider = OpenCodeProvider(ai_provider="anthropic", api_key="test")
        repr_str = repr(provider)
        assert "OpenCodeProvider" in repr_str
        assert "anthropic" in repr_str
        assert "has_api_key=True" in repr_str


class TestModelTranslation:
    """Test model name translation for all AI providers."""

    def test_model_translation_anthropic(self):
        """Test model translation for Anthropic."""
        provider = OpenCodeProvider(ai_provider="anthropic")

        assert provider.translate_model_name("sonnet-4.5") == "anthropic/claude-sonnet-4.5"
        assert provider.translate_model_name("opus-3") == "anthropic/claude-opus-3"
        assert provider.translate_model_name("haiku-3") == "anthropic/claude-haiku-3"
        assert provider.translate_model_name("sonnet-3.5") == "anthropic/claude-sonnet-3.5"

    def test_model_translation_openai(self):
        """Test model translation for OpenAI."""
        provider = OpenCodeProvider(ai_provider="openai")

        assert provider.translate_model_name("gpt-4") == "openai/gpt-4"
        assert provider.translate_model_name("gpt-4-turbo") == "openai/gpt-4-turbo"
        assert provider.translate_model_name("gpt-5") == "openai/gpt-5"
        assert provider.translate_model_name("gpt-5-codex") == "openai/gpt-5-codex"

    def test_model_translation_google(self):
        """Test model translation for Google."""
        provider = OpenCodeProvider(ai_provider="google")

        assert provider.translate_model_name("gemini-2.5-pro") == "google/gemini-2.5-pro"
        assert provider.translate_model_name("gemini-pro") == "google/gemini-pro"

    def test_model_passthrough_anthropic(self):
        """Test passthrough for already-formatted Anthropic models."""
        provider = OpenCodeProvider(ai_provider="anthropic")

        # Already in provider/model format
        result = provider.translate_model_name("anthropic/claude-sonnet-4.5")
        assert result == "anthropic/claude-sonnet-4.5"

    def test_model_not_supported_raises_error(self):
        """Test unsupported model raises ModelNotSupportedError."""
        provider = OpenCodeProvider(ai_provider="anthropic")

        with pytest.raises(ModelNotSupportedError) as exc_info:
            provider.translate_model_name("gpt-4")  # OpenAI model on Anthropic provider

        assert "gpt-4" in str(exc_info.value)
        assert "opencode" in str(exc_info.value)  # Provider name, not AI provider

    def test_model_not_supported_includes_supported_models(self):
        """Test error includes list of supported models."""
        provider = OpenCodeProvider(ai_provider="openai")

        with pytest.raises(ModelNotSupportedError) as exc_info:
            provider.translate_model_name("sonnet-4.5")  # Anthropic model on OpenAI provider

        # Check context includes supported models
        assert exc_info.value.context
        assert "supported_models" in exc_info.value.context


class TestSupportedModels:
    """Test get_supported_models() method."""

    def test_get_supported_models_anthropic(self):
        """Test getting supported models for Anthropic."""
        provider = OpenCodeProvider(ai_provider="anthropic")
        models = provider.get_supported_models()

        assert "sonnet-4.5" in models
        assert "opus-3" in models
        assert "haiku-3" in models
        assert "gpt-4" not in models

        # Should not include passthrough format
        assert not any(m.startswith("anthropic/") for m in models)

    def test_get_supported_models_openai(self):
        """Test getting supported models for OpenAI."""
        provider = OpenCodeProvider(ai_provider="openai")
        models = provider.get_supported_models()

        assert "gpt-4" in models
        assert "gpt-4-turbo" in models
        assert "gpt-5" in models
        assert "sonnet-4.5" not in models

        # Should not include passthrough format
        assert not any(m.startswith("openai/") for m in models)

    def test_get_supported_models_google(self):
        """Test getting supported models for Google."""
        provider = OpenCodeProvider(ai_provider="google")
        models = provider.get_supported_models()

        assert "gemini-2.5-pro" in models
        assert "gemini-pro" in models

        # Should not include passthrough format
        assert not any(m.startswith("google/") for m in models)


class TestToolSupport:
    """Test tool support checking."""

    def test_supports_core_tools(self):
        """Test support for core file operations."""
        provider = OpenCodeProvider()

        # Excellent support (90-100%)
        assert provider.supports_tool("Read") is True
        assert provider.supports_tool("Write") is True
        assert provider.supports_tool("Edit") is True
        assert provider.supports_tool("Bash") is True
        assert provider.supports_tool("Glob") is True

    def test_supports_partial_tools(self):
        """Test support for partially supported tools."""
        provider = OpenCodeProvider()

        # Partial support (60-70%)
        assert provider.supports_tool("MultiEdit") is True
        assert provider.supports_tool("Grep") is True

    def test_unsupported_tools(self):
        """Test unsupported tools."""
        provider = OpenCodeProvider()

        # Not supported
        assert provider.supports_tool("Task") is False
        assert provider.supports_tool("WebFetch") is False
        assert provider.supports_tool("WebSearch") is False
        assert provider.supports_tool("TodoWrite") is False
        assert provider.supports_tool("AskUserQuestion") is False
        assert provider.supports_tool("NotebookEdit") is False
        assert provider.supports_tool("Skill") is False
        assert provider.supports_tool("SlashCommand") is False

    def test_supports_unknown_tool(self):
        """Test unknown tool returns False."""
        provider = OpenCodeProvider()
        assert provider.supports_tool("UnknownTool") is False


class TestConfigurationValidation:
    """Test configuration validation."""

    @pytest.mark.asyncio
    async def test_validate_configuration_valid(self):
        """Test configuration validation when valid."""
        with patch.object(Path, 'exists', return_value=True):
            provider = OpenCodeProvider(
                cli_path=Path("/usr/bin/opencode"),
                ai_provider="anthropic",
                api_key="test-key"
            )
            is_valid = await provider.validate_configuration()
            assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_configuration_no_cli(self):
        """Test configuration validation when CLI missing."""
        provider = OpenCodeProvider(cli_path=None, api_key="test-key")
        is_valid = await provider.validate_configuration()
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_configuration_no_api_key(self):
        """Test configuration validation when API key missing."""
        with patch.object(Path, 'exists', return_value=True):
            provider = OpenCodeProvider(
                cli_path=Path("/usr/bin/opencode"),
                api_key=None
            )
            is_valid = await provider.validate_configuration()
            assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_configuration_invalid_provider(self):
        """Test configuration validation with invalid AI provider."""
        with patch.object(Path, 'exists', return_value=True):
            provider = OpenCodeProvider(
                cli_path=Path("/usr/bin/opencode"),
                ai_provider="invalid",
                api_key="test-key"
            )
            is_valid = await provider.validate_configuration()
            assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_configuration_multiple_issues(self):
        """Test configuration validation with multiple issues."""
        provider = OpenCodeProvider(
            cli_path=None,
            ai_provider="invalid",
            api_key=None
        )
        is_valid = await provider.validate_configuration()
        assert is_valid is False


class TestConfigurationSchema:
    """Test configuration schema."""

    def test_get_configuration_schema(self):
        """Test configuration schema structure."""
        provider = OpenCodeProvider()
        schema = provider.get_configuration_schema()

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "cli_path" in schema["properties"]
        assert "ai_provider" in schema["properties"]
        assert "api_key" in schema["properties"]

    def test_schema_ai_provider_enum(self):
        """Test AI provider has enum constraint."""
        provider = OpenCodeProvider()
        schema = provider.get_configuration_schema()

        ai_provider_schema = schema["properties"]["ai_provider"]
        assert "enum" in ai_provider_schema
        assert "anthropic" in ai_provider_schema["enum"]
        assert "openai" in ai_provider_schema["enum"]
        assert "google" in ai_provider_schema["enum"]

    def test_schema_required_fields(self):
        """Test required fields."""
        provider = OpenCodeProvider()
        schema = provider.get_configuration_schema()

        assert "required" in schema
        assert "ai_provider" in schema["required"]


class TestCLIDetection:
    """Test CLI auto-detection."""

    def test_detect_cli_found(self):
        """Test CLI detection when found."""
        test_path = Path.home() / ".opencode" / "bin" / "opencode"

        with patch.object(Path, 'exists') as mock_exists:
            mock_exists.return_value = True

            with patch.object(Path, 'is_file') as mock_is_file:
                mock_is_file.return_value = True

                provider = OpenCodeProvider()
                assert provider.cli_path is not None

    def test_detect_cli_not_found(self):
        """Test CLI detection when not found."""
        with patch.object(Path, 'exists', return_value=False):
            with patch.object(Path, 'is_file', return_value=False):
                provider = OpenCodeProvider()
                assert provider.cli_path is None

    def test_custom_cli_path(self):
        """Test custom CLI path."""
        custom_path = Path("/custom/path/opencode")
        provider = OpenCodeProvider(cli_path=custom_path)
        assert provider.cli_path == custom_path


class TestInitializeCleanup:
    """Test initialize() and cleanup() methods."""

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test initialization."""
        provider = OpenCodeProvider()
        assert provider._initialized is False

        await provider.initialize()
        assert provider._initialized is True

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test cleanup."""
        provider = OpenCodeProvider()
        await provider.initialize()
        assert provider._initialized is True

        await provider.cleanup()
        assert provider._initialized is False

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self):
        """Test initialize can be called multiple times."""
        provider = OpenCodeProvider()

        await provider.initialize()
        await provider.initialize()  # Should not raise

        assert provider._initialized is True


@pytest.mark.asyncio
class TestTaskExecution:
    """Test task execution (with mocked subprocess)."""

    async def test_execute_task_success(self, tmp_path):
        """Test successful task execution."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Task completed successfully", "")

        with patch('subprocess.Popen', return_value=mock_process):
            provider = OpenCodeProvider(
                cli_path=Path("/usr/bin/opencode"),
                ai_provider="anthropic",
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            results = []
            async for result in provider.execute_task(
                task="Write hello.py",
                context=context,
                model="sonnet-4.5",
                tools=["Read", "Write"],
                timeout=60
            ):
                results.append(result)

            assert len(results) > 0
            assert "Task completed successfully" in results[0]

    async def test_execute_task_builds_correct_command(self, tmp_path):
        """Test correct command is built."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Done", "")

        with patch('subprocess.Popen', return_value=mock_process) as mock_popen:
            provider = OpenCodeProvider(
                cli_path=Path("/usr/bin/opencode"),
                ai_provider="anthropic",
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            async for _ in provider.execute_task(
                task="Test task",
                context=context,
                model="sonnet-4.5",
                tools=["Read"],
                timeout=60
            ):
                pass

            # Verify command
            call_args = mock_popen.call_args
            cmd = call_args[0][0]

            # Windows converts paths with backslashes, so just check basename
            assert Path(cmd[0]).name == "opencode" or Path(cmd[0]).name == "opencode.exe"
            assert "run" in cmd
            assert "--model" in cmd
            assert "anthropic/claude-sonnet-4.5" in cmd

    async def test_execute_task_sets_api_key_env(self, tmp_path):
        """Test API key is set in environment."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Done", "")

        with patch('subprocess.Popen', return_value=mock_process) as mock_popen:
            provider = OpenCodeProvider(
                cli_path=Path("/usr/bin/opencode"),
                ai_provider="anthropic",
                api_key="test-key-123"
            )

            context = AgentContext(project_root=tmp_path)

            async for _ in provider.execute_task(
                task="Test task",
                context=context,
                model="sonnet-4.5",
                tools=["Read"],
                timeout=60
            ):
                pass

            # Verify environment
            call_kwargs = mock_popen.call_args[1]
            env = call_kwargs['env']

            assert "ANTHROPIC_API_KEY" in env
            assert env["ANTHROPIC_API_KEY"] == "test-key-123"

    async def test_execute_task_sets_working_directory(self, tmp_path):
        """Test working directory is set correctly."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Done", "")

        with patch('subprocess.Popen', return_value=mock_process) as mock_popen:
            provider = OpenCodeProvider(
                cli_path=Path("/usr/bin/opencode"),
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            async for _ in provider.execute_task(
                task="Test task",
                context=context,
                model="sonnet-4.5",
                tools=["Read"],
                timeout=60
            ):
                pass

            # Verify cwd
            call_kwargs = mock_popen.call_args[1]
            assert call_kwargs['cwd'] == str(tmp_path)

    async def test_execute_task_openai_provider(self, tmp_path):
        """Test execution with OpenAI provider."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Done", "")

        with patch('subprocess.Popen', return_value=mock_process) as mock_popen:
            provider = OpenCodeProvider(
                cli_path=Path("/usr/bin/opencode"),
                ai_provider="openai",
                api_key="openai-key"
            )

            context = AgentContext(project_root=tmp_path)

            async for _ in provider.execute_task(
                task="Test task",
                context=context,
                model="gpt-4",
                tools=["Read"],
                timeout=60
            ):
                pass

            # Verify model and API key
            call_args = mock_popen.call_args
            cmd = call_args[0][0]
            env = call_args[1]['env']

            assert "openai/gpt-4" in cmd
            assert "OPENAI_API_KEY" in env
            assert env["OPENAI_API_KEY"] == "openai-key"


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling scenarios."""

    async def test_execute_task_no_cli(self, tmp_path):
        """Test execution without CLI raises error."""
        provider = OpenCodeProvider(cli_path=None)
        context = AgentContext(project_root=tmp_path)

        with pytest.raises(ProviderConfigurationError) as exc_info:
            async for _ in provider.execute_task(
                task="Test",
                context=context,
                model="sonnet-4.5",
                tools=["Read"],
                timeout=60
            ):
                pass

        assert "OpenCode CLI not found" in str(exc_info.value)

    async def test_execute_task_nonzero_exit_code(self, tmp_path):
        """Test execution with non-zero exit code."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = ("", "Error occurred")

        with patch('subprocess.Popen', return_value=mock_process):
            provider = OpenCodeProvider(
                cli_path=Path("/usr/bin/opencode"),
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            with pytest.raises(ProviderExecutionError) as exc_info:
                async for _ in provider.execute_task(
                    task="Test",
                    context=context,
                    model="sonnet-4.5",
                    tools=["Read"],
                    timeout=60
                ):
                    pass

            assert "exit code 1" in str(exc_info.value)

    async def test_execute_task_timeout(self, tmp_path):
        """Test execution timeout."""
        mock_process = Mock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired("cmd", 60)

        with patch('subprocess.Popen', return_value=mock_process):
            provider = OpenCodeProvider(
                cli_path=Path("/usr/bin/opencode"),
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            with pytest.raises(ProviderTimeoutError):
                async for _ in provider.execute_task(
                    task="Test",
                    context=context,
                    model="sonnet-4.5",
                    tools=["Read"],
                    timeout=1
                ):
                    pass

    async def test_execute_task_unsupported_model(self, tmp_path):
        """Test execution with unsupported model raises error."""
        provider = OpenCodeProvider(
            cli_path=Path("/usr/bin/opencode"),
            ai_provider="anthropic",
            api_key="test-key"
        )

        context = AgentContext(project_root=tmp_path)

        with pytest.raises(ModelNotSupportedError):
            async for _ in provider.execute_task(
                task="Test",
                context=context,
                model="gpt-4",  # OpenAI model on Anthropic provider
                tools=["Read"],
                timeout=60
            ):
                pass

    async def test_execute_task_subprocess_error(self, tmp_path):
        """Test execution with subprocess exception."""
        with patch('subprocess.Popen', side_effect=OSError("Permission denied")):
            provider = OpenCodeProvider(
                cli_path=Path("/usr/bin/opencode"),
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            with pytest.raises(ProviderExecutionError) as exc_info:
                async for _ in provider.execute_task(
                    task="Test",
                    context=context,
                    model="sonnet-4.5",
                    tools=["Read"],
                    timeout=60
                ):
                    pass

            assert "Permission denied" in str(exc_info.value)

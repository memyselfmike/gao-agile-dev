"""Unit tests for ClaudeCodeProvider.

Tests behavioral compatibility with ProcessExecutor and all IAgentProvider
interface requirements.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import subprocess
import os

from gao_dev.core.providers.claude_code import ClaudeCodeProvider
from gao_dev.core.providers.models import AgentContext
from gao_dev.core.providers.exceptions import (
    ProviderExecutionError,
    ProviderTimeoutError,
    ProviderConfigurationError
)


class TestClaudeCodeProviderBasics:
    """Test basic ClaudeCodeProvider functionality."""

    def test_provider_name(self):
        """Test provider name."""
        provider = ClaudeCodeProvider(
            cli_path=Path("/usr/bin/claude"),
            api_key="test-key"
        )
        assert provider.name == "claude-code"

    def test_provider_version(self):
        """Test provider version."""
        provider = ClaudeCodeProvider(
            cli_path=Path("/usr/bin/claude"),
            api_key="test-key"
        )
        assert provider.version == "1.0.0"

    def test_initialization_with_explicit_params(self):
        """Test initialization with explicit parameters."""
        cli_path = Path("/usr/bin/claude")
        api_key = "test-api-key"

        provider = ClaudeCodeProvider(
            cli_path=cli_path,
            api_key=api_key
        )

        assert provider.cli_path == cli_path
        assert provider.api_key == api_key
        assert provider._initialized is False

    def test_initialization_with_autodetect(self):
        """Test initialization with auto-detection."""
        with patch('gao_dev.core.providers.claude_code.find_claude_cli', return_value=Path("/detected/claude")):
            with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'env-key'}):
                provider = ClaudeCodeProvider()

                assert provider.cli_path == Path("/detected/claude")
                assert provider.api_key == "env-key"

    def test_initialization_no_cli_found(self):
        """Test initialization when CLI not found."""
        with patch('gao_dev.core.providers.claude_code.find_claude_cli', return_value=None):
            provider = ClaudeCodeProvider()

            assert provider.cli_path is None

    def test_repr(self):
        """Test string representation."""
        provider = ClaudeCodeProvider(
            cli_path=Path("/usr/bin/claude"),
            api_key="test-key"
        )

        repr_str = repr(provider)
        assert "ClaudeCodeProvider" in repr_str
        assert "cli_path" in repr_str
        assert "has_api_key" in repr_str


class TestModelTranslation:
    """Test model name translation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider = ClaudeCodeProvider(
            cli_path=Path("/usr/bin/claude"),
            api_key="test-key"
        )

    def test_canonical_name_translation(self):
        """Test translation of canonical model names."""
        assert self.provider.translate_model_name("sonnet-4.5") == "claude-sonnet-4-5-20250929"
        assert self.provider.translate_model_name("sonnet-3.5") == "claude-sonnet-3-5-20241022"
        assert self.provider.translate_model_name("opus-3") == "claude-opus-3-20250219"
        assert self.provider.translate_model_name("haiku-3") == "claude-haiku-3-20250219"

    def test_full_model_id_passthrough(self):
        """Test passthrough of full model IDs."""
        full_id = "claude-sonnet-4-5-20250929"
        assert self.provider.translate_model_name(full_id) == full_id

        full_id = "claude-opus-3-20250219"
        assert self.provider.translate_model_name(full_id) == full_id

    def test_unknown_model_passthrough(self):
        """Test passthrough of unknown model names."""
        # Should passthrough unknown models (not raise error)
        assert self.provider.translate_model_name("unknown-model") == "unknown-model"

    def test_get_supported_models(self):
        """Test getting list of supported models."""
        models = self.provider.get_supported_models()

        assert "sonnet-4.5" in models
        assert "sonnet-3.5" in models
        assert "opus-3" in models
        assert "haiku-3" in models

        # Should only contain canonical names, not full IDs
        assert "claude-sonnet-4-5-20250929" not in models


class TestToolSupport:
    """Test tool support checking."""

    def setup_method(self):
        """Set up test fixtures."""
        self.provider = ClaudeCodeProvider(
            cli_path=Path("/usr/bin/claude"),
            api_key="test-key"
        )

    def test_supported_tools(self):
        """Test that standard tools are supported."""
        assert self.provider.supports_tool("Read") is True
        assert self.provider.supports_tool("Write") is True
        assert self.provider.supports_tool("Edit") is True
        assert self.provider.supports_tool("Bash") is True
        assert self.provider.supports_tool("Grep") is True
        assert self.provider.supports_tool("Glob") is True
        assert self.provider.supports_tool("TodoWrite") is True

    def test_unsupported_tool(self):
        """Test that unsupported tools return False."""
        assert self.provider.supports_tool("NonExistentTool") is False
        assert self.provider.supports_tool("CustomTool") is False


class TestConfigurationValidation:
    """Test configuration validation."""

    @pytest.mark.asyncio
    async def test_validate_configuration_valid(self):
        """Test configuration validation when valid."""
        provider = ClaudeCodeProvider(
            cli_path=Path("/usr/bin/claude"),
            api_key="test-key"
        )

        with patch.object(Path, 'exists', return_value=True):
            is_valid = await provider.validate_configuration()
            assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_configuration_no_cli(self):
        """Test configuration validation when CLI missing."""
        with patch('gao_dev.core.providers.claude_code.find_claude_cli', return_value=None):
            provider = ClaudeCodeProvider(cli_path=None, api_key="test-key")

            is_valid = await provider.validate_configuration()
            assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_configuration_cli_not_exists(self):
        """Test configuration validation when CLI path doesn't exist."""
        provider = ClaudeCodeProvider(
            cli_path=Path("/nonexistent/claude"),
            api_key="test-key"
        )

        is_valid = await provider.validate_configuration()
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_configuration_no_api_key(self):
        """Test configuration validation when API key missing."""
        provider = ClaudeCodeProvider(
            cli_path=Path("/usr/bin/claude"),
            api_key=None
        )

        with patch.object(Path, 'exists', return_value=True):
            is_valid = await provider.validate_configuration()
            assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_configuration_nothing_set(self):
        """Test configuration validation when nothing is set."""
        provider = ClaudeCodeProvider(cli_path=None, api_key=None)

        is_valid = await provider.validate_configuration()
        assert is_valid is False

    def test_get_configuration_schema(self):
        """Test configuration schema."""
        provider = ClaudeCodeProvider(
            cli_path=Path("/usr/bin/claude"),
            api_key="test-key"
        )

        schema = provider.get_configuration_schema()

        assert schema["type"] == "object"
        assert "cli_path" in schema["properties"]
        assert "api_key" in schema["properties"]
        assert schema["properties"]["cli_path"]["type"] == "string"
        assert schema["properties"]["api_key"]["type"] == "string"
        assert schema["required"] == []  # Both optional


class TestLifecycle:
    """Test provider lifecycle (initialize/cleanup)."""

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test provider initialization."""
        provider = ClaudeCodeProvider(
            cli_path=Path("/usr/bin/claude"),
            api_key="test-key"
        )

        assert provider._initialized is False

        await provider.initialize()

        assert provider._initialized is True

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test provider cleanup."""
        provider = ClaudeCodeProvider(
            cli_path=Path("/usr/bin/claude"),
            api_key="test-key"
        )

        await provider.initialize()
        assert provider._initialized is True

        await provider.cleanup()
        assert provider._initialized is False

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self):
        """Test that initialize can be called multiple times."""
        provider = ClaudeCodeProvider(
            cli_path=Path("/usr/bin/claude"),
            api_key="test-key"
        )

        await provider.initialize()
        await provider.initialize()  # Should not raise

        assert provider._initialized is True


class TestExecuteTask:
    """Test task execution."""

    @pytest.mark.asyncio
    async def test_execute_task_no_cli(self, tmp_path):
        """Test execution fails when CLI not set."""
        with patch('gao_dev.core.providers.claude_code.find_claude_cli', return_value=None):
            provider = ClaudeCodeProvider(cli_path=None, api_key="test-key")
            context = AgentContext(project_root=tmp_path)

            with pytest.raises(ProviderConfigurationError) as exc_info:
                async for _ in provider.execute_task(
                    task="Test task",
                    context=context,
                    model="sonnet-4.5",
                    tools=["Read"]
                ):
                    pass

            assert "Claude CLI not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_task_success(self, tmp_path):
        """Test successful task execution."""
        # Mock subprocess
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Task completed successfully", "")

        with patch('subprocess.Popen', return_value=mock_process):
            provider = ClaudeCodeProvider(
                cli_path=Path("/usr/bin/claude"),
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            results = []
            async for result in provider.execute_task(
                task="Test task",
                context=context,
                model="sonnet-4.5",
                tools=["Read", "Write"],
                timeout=60
            ):
                results.append(result)

            assert len(results) == 1
            assert "Task completed successfully" in results[0]

    @pytest.mark.asyncio
    async def test_execute_task_timeout(self, tmp_path):
        """Test task execution timeout."""
        mock_process = Mock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired("cmd", 60)
        mock_process.kill = Mock()

        with patch('subprocess.Popen', return_value=mock_process):
            provider = ClaudeCodeProvider(
                cli_path=Path("/usr/bin/claude"),
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            with pytest.raises(ProviderTimeoutError) as exc_info:
                async for _ in provider.execute_task(
                    task="Test task",
                    context=context,
                    model="sonnet-4.5",
                    tools=["Read"],
                    timeout=1
                ):
                    pass

            assert "timed out" in str(exc_info.value).lower()
            mock_process.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_task_failure(self, tmp_path):
        """Test task execution failure."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = ("", "Error occurred")

        with patch('subprocess.Popen', return_value=mock_process):
            provider = ClaudeCodeProvider(
                cli_path=Path("/usr/bin/claude"),
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            with pytest.raises(ProviderExecutionError) as exc_info:
                async for _ in provider.execute_task(
                    task="Test task",
                    context=context,
                    model="sonnet-4.5",
                    tools=["Read"],
                    timeout=60
                ):
                    pass

            assert "exit code 1" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_task_no_output(self, tmp_path):
        """Test task execution with no output (error case)."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = ("", "")

        with patch('subprocess.Popen', return_value=mock_process):
            provider = ClaudeCodeProvider(
                cli_path=Path("/usr/bin/claude"),
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            with pytest.raises(ProviderExecutionError) as exc_info:
                async for _ in provider.execute_task(
                    task="Test task",
                    context=context,
                    model="sonnet-4.5",
                    tools=["Read"],
                    timeout=60
                ):
                    pass

            # Should have specific message about checking claude.bat
            assert "check if claude.bat is configured correctly" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_task_command_building(self, tmp_path):
        """Test that command is built correctly."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Success", "")

        with patch('subprocess.Popen', return_value=mock_process) as popen_mock:
            provider = ClaudeCodeProvider(
                cli_path=Path("/usr/bin/claude"),
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

            # Verify command structure
            call_args = popen_mock.call_args
            cmd = call_args[0][0]

            assert str(provider.cli_path) in cmd
            assert "--print" in cmd
            assert "--dangerously-skip-permissions" in cmd
            assert "--model" in cmd
            assert "claude-sonnet-4-5-20250929" in cmd
            assert "--add-dir" in cmd
            assert str(tmp_path) in cmd

    @pytest.mark.asyncio
    async def test_execute_task_environment_variables(self, tmp_path):
        """Test that environment variables are set correctly."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Success", "")

        with patch('subprocess.Popen', return_value=mock_process) as popen_mock:
            provider = ClaudeCodeProvider(
                cli_path=Path("/usr/bin/claude"),
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

            # Verify environment variables
            call_args = popen_mock.call_args
            env = call_args[1]['env']

            assert 'ANTHROPIC_API_KEY' in env
            assert env['ANTHROPIC_API_KEY'] == "test-key-123"

    @pytest.mark.asyncio
    async def test_execute_task_windows_encoding(self, tmp_path):
        """Test Windows encoding settings."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Success", "")

        with patch('subprocess.Popen', return_value=mock_process) as popen_mock:
            provider = ClaudeCodeProvider(
                cli_path=Path("/usr/bin/claude"),
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

            # Verify encoding settings for Windows compatibility
            call_args = popen_mock.call_args
            kwargs = call_args[1]

            assert kwargs['encoding'] == 'utf-8'
            assert kwargs['errors'] == 'replace'
            assert kwargs['text'] is True

    @pytest.mark.asyncio
    async def test_execute_task_with_stderr(self, tmp_path):
        """Test execution with stderr output."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Success", "Warning message")

        with patch('subprocess.Popen', return_value=mock_process):
            provider = ClaudeCodeProvider(
                cli_path=Path("/usr/bin/claude"),
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            results = []
            async for result in provider.execute_task(
                task="Test task",
                context=context,
                model="sonnet-4.5",
                tools=["Read"],
                timeout=60
            ):
                results.append(result)

            # Should still succeed and return stdout
            assert len(results) == 1
            assert "Success" in results[0]

    @pytest.mark.asyncio
    async def test_execute_task_default_timeout(self, tmp_path):
        """Test that default timeout is used when not specified."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Success", "")

        with patch('subprocess.Popen', return_value=mock_process):
            provider = ClaudeCodeProvider(
                cli_path=Path("/usr/bin/claude"),
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            async for _ in provider.execute_task(
                task="Test task",
                context=context,
                model="sonnet-4.5",
                tools=["Read"]
                # No timeout specified
            ):
                pass

            # Verify default timeout was used
            call_args = mock_process.communicate.call_args
            assert call_args[1]['timeout'] == ClaudeCodeProvider.DEFAULT_TIMEOUT

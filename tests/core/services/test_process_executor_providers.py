"""Tests for ProcessExecutor provider functionality."""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from gao_dev.core.services.process_executor import ProcessExecutor
from gao_dev.core.providers.claude_code import ClaudeCodeProvider
from gao_dev.core.providers.base import IAgentProvider


class MockProvider(IAgentProvider):
    """Mock provider for testing."""

    def __init__(self):
        self._configured = True
        self._initialized = False

    @property
    def name(self) -> str:
        return "mock"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def execute_task(self, task, context, model, tools, timeout=None, **kwargs):
        yield f"Mock result for: {task[:50]}"

    def supports_tool(self, tool_name: str) -> bool:
        return True

    def get_supported_models(self):
        return ["mock-model"]

    def translate_model_name(self, canonical_name: str) -> str:
        return canonical_name

    async def validate_configuration(self) -> bool:
        return self._configured

    def get_configuration_schema(self):
        return {}

    async def initialize(self) -> None:
        self._initialized = True

    async def cleanup(self) -> None:
        self._initialized = False


class TestProcessExecutorProviders:
    """Test ProcessExecutor provider functionality."""

    @pytest.mark.asyncio
    async def test_provider_injection(self, tmp_path):
        """Test injecting provider instance."""
        provider = MockProvider()
        executor = ProcessExecutor(tmp_path, provider=provider)

        assert executor.provider is provider
        assert executor.provider.name == "mock"

    @pytest.mark.asyncio
    async def test_provider_name_only(self, tmp_path):
        """Test creating provider by name."""
        with patch('gao_dev.core.providers.factory.ProviderFactory.create_provider') as mock_create:
            mock_create.return_value = MockProvider()

            executor = ProcessExecutor(tmp_path, provider_name="claude-code")

            mock_create.assert_called_once_with("claude-code", config=None)

    @pytest.mark.asyncio
    async def test_provider_with_config(self, tmp_path):
        """Test creating provider with config."""
        with patch('gao_dev.core.providers.factory.ProviderFactory.create_provider') as mock_create:
            mock_create.return_value = MockProvider()

            config = {"api_key": "test"}
            executor = ProcessExecutor(
                tmp_path,
                provider_name="claude-code",
                provider_config=config
            )

            mock_create.assert_called_once_with("claude-code", config=config)

    @pytest.mark.asyncio
    async def test_execute_with_provider(self, tmp_path):
        """Test executing task with provider."""
        provider = MockProvider()
        executor = ProcessExecutor(tmp_path, provider=provider)

        results = []
        async for result in executor.execute_agent_task("Test task"):
            results.append(result)

        assert len(results) > 0
        assert "Mock result" in results[0]

    @pytest.mark.asyncio
    async def test_provider_not_configured_raises_error(self, tmp_path):
        """Test error when provider not configured."""
        provider = MockProvider()
        provider._configured = False

        executor = ProcessExecutor(tmp_path, provider=provider)

        with pytest.raises(ValueError) as exc_info:
            async for _ in executor.execute_agent_task("Test task"):
                pass

        assert "not properly configured" in str(exc_info.value)
        assert provider.name in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_with_model_and_tools(self, tmp_path):
        """Test executing task with model and tools parameters."""
        provider = MockProvider()
        executor = ProcessExecutor(tmp_path, provider=provider)

        results = []
        async for result in executor.execute_agent_task(
            "Test task",
            model="sonnet-4.5",
            tools=["Read", "Write"],
            timeout=3600
        ):
            results.append(result)

        assert len(results) > 0


class TestProcessExecutorLegacyAPI:
    """Test ProcessExecutor backward compatibility."""

    @pytest.mark.asyncio
    async def test_legacy_constructor(self, tmp_path):
        """Test legacy constructor still works."""
        with patch('gao_dev.core.providers.factory.ProviderFactory.create_provider') as mock_create:
            mock_create.return_value = MockProvider()

            executor = ProcessExecutor(
                project_root=tmp_path,
                cli_path=Path("/usr/bin/claude"),
                api_key="sk-test"
            )

            # Should create claude-code provider with legacy config
            mock_create.assert_called_once()
            args, kwargs = mock_create.call_args
            assert args[0] == "claude-code"
            assert "cli_path" in kwargs["config"]
            assert "api_key" in kwargs["config"]

    @pytest.mark.asyncio
    async def test_legacy_cli_path_only(self, tmp_path):
        """Test legacy constructor with cli_path only."""
        with patch('gao_dev.core.providers.factory.ProviderFactory.create_provider') as mock_create:
            mock_create.return_value = MockProvider()

            executor = ProcessExecutor(
                project_root=tmp_path,
                cli_path=Path("/usr/bin/claude")
            )

            # Should create claude-code provider
            mock_create.assert_called_once()
            args, kwargs = mock_create.call_args
            assert args[0] == "claude-code"
            assert "cli_path" in kwargs["config"]

    @pytest.mark.asyncio
    async def test_legacy_api_key_only(self, tmp_path):
        """Test legacy constructor with api_key only."""
        with patch('gao_dev.core.providers.factory.ProviderFactory.create_provider') as mock_create:
            mock_create.return_value = MockProvider()

            executor = ProcessExecutor(
                project_root=tmp_path,
                api_key="sk-test"
            )

            # Should create claude-code provider
            mock_create.assert_called_once()
            args, kwargs = mock_create.call_args
            assert args[0] == "claude-code"
            assert "api_key" in kwargs["config"]

    @pytest.mark.asyncio
    async def test_default_constructor_no_legacy_params(self, tmp_path):
        """Test constructor without any legacy params uses default provider."""
        with patch('gao_dev.core.providers.factory.ProviderFactory.create_provider') as mock_create:
            mock_create.return_value = MockProvider()

            executor = ProcessExecutor(project_root=tmp_path)

            # Should create claude-code provider with no config
            mock_create.assert_called_once_with("claude-code", config=None)

    def test_executor_repr(self, tmp_path):
        """Test executor string representation."""
        provider = MockProvider()
        executor = ProcessExecutor(tmp_path, provider=provider)

        repr_str = repr(executor)
        assert "ProcessExecutor" in repr_str
        assert "mock" in repr_str

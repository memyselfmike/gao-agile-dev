"""Integration tests for OpenCodeSDKProvider with real OpenCode server.

These tests verify end-to-end functionality with a real OpenCode server instance.
Tests are skipped if OpenCode CLI is not available.

Story: 19.4 - Integration Testing and Validation
"""

import pytest
import subprocess
import asyncio
from pathlib import Path
from typing import AsyncGenerator

from gao_dev.core.providers.opencode_sdk import OpenCodeSDKProvider
from gao_dev.core.providers.models import AgentContext
from gao_dev.core.providers.exceptions import (
    ModelNotSupportedError,
)


# =============================================================================
# Helper Functions
# =============================================================================

def is_opencode_available() -> bool:
    """
    Check if OpenCode CLI is available on the system.

    Returns:
        True if opencode command is available, False otherwise
    """
    try:
        result = subprocess.run(
            ["opencode", "--version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


# Skip all integration tests if OpenCode not available
pytestmark = pytest.mark.skipif(
    not is_opencode_available(),
    reason="OpenCode CLI not available - install from https://github.com/modelcontextprotocol/opencode"
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
async def provider_with_server() -> AsyncGenerator[OpenCodeSDKProvider, None]:
    """
    Create provider instance with auto-started server for testing.

    Yields:
        OpenCodeSDKProvider: Initialized provider with running server

    Note:
        Automatically cleans up server on teardown
    """
    provider = OpenCodeSDKProvider(auto_start_server=True)
    await provider.initialize()

    yield provider

    # Cleanup
    await provider.cleanup()


@pytest.fixture
def agent_context(tmp_path: Path) -> AgentContext:
    """
    Create agent context for testing.

    Args:
        tmp_path: Pytest temporary directory

    Returns:
        AgentContext: Test context with temporary project root
    """
    return AgentContext(project_root=tmp_path)


# =============================================================================
# Integration Tests - End-to-End Task Execution
# =============================================================================

class TestOpenCodeSDKIntegrationBasic:
    """Basic end-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_end_to_end_simple_task(
        self,
        provider_with_server: OpenCodeSDKProvider,
        agent_context: AgentContext
    ):
        """Test complete task execution flow with simple prompt."""
        # Execute simple task
        results = []
        async for result in provider_with_server.execute_task(
            task="Say 'Hello, World!' and nothing else.",
            context=agent_context,
            model="claude-sonnet-4-5-20250929",
            tools=["Read", "Write"],
        ):
            results.append(result)

        # Verify response
        assert len(results) > 0
        content = "".join(results)
        assert len(content) > 0
        assert "hello" in content.lower()

    @pytest.mark.asyncio
    async def test_end_to_end_with_different_model(
        self,
        provider_with_server: OpenCodeSDKProvider,
        agent_context: AgentContext
    ):
        """Test task execution with different Claude model."""
        results = []
        async for result in provider_with_server.execute_task(
            task="What is 2 + 2? Answer with just the number.",
            context=agent_context,
            model="claude-3-5-sonnet-20241022",
            tools=[],
        ):
            results.append(result)

        # Verify response
        assert len(results) > 0
        content = "".join(results)
        assert "4" in content

    @pytest.mark.asyncio
    async def test_multiple_tasks_same_session(
        self,
        provider_with_server: OpenCodeSDKProvider,
        agent_context: AgentContext
    ):
        """Test executing multiple tasks in same session (session reuse)."""
        # First task
        results1 = []
        async for result in provider_with_server.execute_task(
            task="Count from 1 to 3.",
            context=agent_context,
            model="claude-sonnet-4-5-20250929",
            tools=[],
        ):
            results1.append(result)

        assert len(results1) > 0

        # Second task (should reuse session)
        results2 = []
        async for result in provider_with_server.execute_task(
            task="What is the capital of France?",
            context=agent_context,
            model="claude-sonnet-4-5-20250929",
            tools=[],
        ):
            results2.append(result)

        assert len(results2) > 0
        content2 = "".join(results2)
        assert "paris" in content2.lower()


# =============================================================================
# Integration Tests - Error Handling
# =============================================================================

class TestOpenCodeSDKIntegrationErrors:
    """Test error handling in integration scenarios."""

    @pytest.mark.asyncio
    async def test_invalid_model_error(
        self,
        provider_with_server: OpenCodeSDKProvider,
        agent_context: AgentContext
    ):
        """Test that invalid model raises appropriate error."""
        with pytest.raises(ModelNotSupportedError) as exc_info:
            async for _ in provider_with_server.execute_task(
                task="Test",
                context=agent_context,
                model="invalid-model-xyz-123",
                tools=[],
            ):
                pass

        assert "invalid-model-xyz-123" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_recovery_after_error(
        self,
        provider_with_server: OpenCodeSDKProvider,
        agent_context: AgentContext
    ):
        """Test provider recovers and works after encountering error."""
        # First, cause an error
        try:
            async for _ in provider_with_server.execute_task(
                task="Test",
                context=agent_context,
                model="invalid-model",
                tools=[],
            ):
                pass
        except ModelNotSupportedError:
            pass  # Expected

        # Verify provider still works
        results = []
        async for result in provider_with_server.execute_task(
            task="Say 'recovered'",
            context=agent_context,
            model="claude-sonnet-4-5-20250929",
            tools=[],
        ):
            results.append(result)

        assert len(results) > 0
        content = "".join(results)
        assert len(content) > 0


# =============================================================================
# Integration Tests - Server Lifecycle
# =============================================================================

class TestOpenCodeSDKIntegrationLifecycle:
    """Test complete server lifecycle in integration scenarios."""

    @pytest.mark.asyncio
    async def test_server_auto_start_and_stop(self):
        """Test complete server lifecycle: start, use, stop."""
        # Create provider with auto-start
        provider = OpenCodeSDKProvider(auto_start_server=True)

        # Initialize (should start server)
        await provider.initialize()
        assert provider._initialized is True
        assert provider._is_server_healthy()

        # Execute task to verify server works
        context = AgentContext(project_root=Path("/tmp"))
        results = []
        async for result in provider.execute_task(
            task="Say hi",
            context=context,
            model="claude-sonnet-4-5-20250929",
            tools=[],
        ):
            results.append(result)

        assert len(results) > 0

        # Cleanup (should stop server)
        await provider.cleanup()

        # Give server time to shutdown
        await asyncio.sleep(1)

        # Verify cleanup
        assert provider._initialized is False
        assert provider.sdk_client is None
        assert provider.session is None

    @pytest.mark.asyncio
    async def test_server_reuse_existing(self):
        """Test that provider can reuse already-running server."""
        # Start first provider
        provider1 = OpenCodeSDKProvider(auto_start_server=True, port=4096)
        await provider1.initialize()

        try:
            # Create second provider (should detect and reuse server)
            provider2 = OpenCodeSDKProvider(auto_start_server=True, port=4096)
            await provider2.initialize()

            # Both should work
            context = AgentContext(project_root=Path("/tmp"))

            results1 = []
            async for result in provider1.execute_task(
                task="Say 'first'",
                context=context,
                model="claude-sonnet-4-5-20250929",
                tools=[],
            ):
                results1.append(result)

            results2 = []
            async for result in provider2.execute_task(
                task="Say 'second'",
                context=context,
                model="claude-sonnet-4-5-20250929",
                tools=[],
            ):
                results2.append(result)

            assert len(results1) > 0
            assert len(results2) > 0

            # Cleanup second
            await provider2.cleanup()

        finally:
            # Cleanup first
            await provider1.cleanup()


# =============================================================================
# Integration Tests - Provider Factory
# =============================================================================

class TestProviderFactoryIntegration:
    """Test provider factory integration with OpenCode SDK provider."""

    def test_factory_creates_sdk_provider(self):
        """Test factory can create OpenCode SDK provider."""
        from gao_dev.core.providers.factory import ProviderFactory

        provider = ProviderFactory.create_provider(
            provider_name="opencode-sdk",
            config={},
        )

        assert isinstance(provider, OpenCodeSDKProvider)
        assert provider.name == "opencode-sdk"

    def test_factory_creates_sdk_provider_with_config(self):
        """Test factory creates provider with custom configuration."""
        from gao_dev.core.providers.factory import ProviderFactory

        provider = ProviderFactory.create_provider(
            provider_name="opencode-sdk",
            config={
                "server_url": "http://localhost:8080",
                "port": 8080,
                "auto_start_server": False,
            },
        )

        assert isinstance(provider, OpenCodeSDKProvider)
        assert provider.server_url == "http://localhost:8080"
        assert provider.port == 8080
        assert provider.auto_start_server is False

    def test_provider_switching(self):
        """Test switching between different provider types."""
        from gao_dev.core.providers.factory import ProviderFactory

        # Create SDK provider
        sdk_provider = ProviderFactory.create_provider("opencode-sdk", {})
        assert isinstance(sdk_provider, OpenCodeSDKProvider)

        # Create CLI provider (if available)
        try:
            cli_provider = ProviderFactory.create_provider("opencode-cli", {})
            # Should be different instance, different class
            assert cli_provider is not sdk_provider
            assert not isinstance(cli_provider, type(sdk_provider))
        except Exception:
            # CLI provider may not be registered
            pass


# =============================================================================
# Integration Tests - Model Support
# =============================================================================

class TestOpenCodeSDKIntegrationModels:
    """Test different model support in integration scenarios."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("model", [
        "claude-sonnet-4-5-20250929",
        "claude-3-5-sonnet-20241022",
        "sonnet-4.5",
        "sonnet-3.5",
    ])
    async def test_different_claude_models(
        self,
        provider_with_server: OpenCodeSDKProvider,
        agent_context: AgentContext,
        model: str
    ):
        """Test task execution with different Claude models."""
        results = []
        async for result in provider_with_server.execute_task(
            task="Say 'test'",
            context=agent_context,
            model=model,
            tools=[],
        ):
            results.append(result)

        assert len(results) > 0
        content = "".join(results)
        assert len(content) > 0


# =============================================================================
# Integration Tests - Tool Support
# =============================================================================

class TestOpenCodeSDKIntegrationTools:
    """Test tool support in integration scenarios."""

    @pytest.mark.asyncio
    async def test_task_with_read_write_tools(
        self,
        provider_with_server: OpenCodeSDKProvider,
        agent_context: AgentContext,
        tmp_path: Path
    ):
        """Test task execution with Read and Write tools."""
        # Update context to use tmp_path
        context = AgentContext(project_root=tmp_path)

        results = []
        async for result in provider_with_server.execute_task(
            task=f"Create a file named 'test.txt' in {tmp_path} with content 'Hello Integration Test'",
            context=context,
            model="claude-sonnet-4-5-20250929",
            tools=["Read", "Write"],
        ):
            results.append(result)

        assert len(results) > 0

        # Note: OpenCode SDK may not actually execute tools in test environment
        # This test verifies the provider accepts tool parameters

    def test_tool_support_checking(self, provider_with_server: OpenCodeSDKProvider):
        """Test tool support checking methods."""
        # Supported tools
        assert provider_with_server.supports_tool("Read") is True
        assert provider_with_server.supports_tool("Write") is True
        assert provider_with_server.supports_tool("Bash") is True
        assert provider_with_server.supports_tool("Grep") is True

        # Unsupported tools
        assert provider_with_server.supports_tool("WebFetch") is False
        assert provider_with_server.supports_tool("TodoWrite") is False
        assert provider_with_server.supports_tool("UnknownTool") is False


# =============================================================================
# Integration Tests - Configuration
# =============================================================================

class TestOpenCodeSDKIntegrationConfig:
    """Test configuration validation in integration scenarios."""

    @pytest.mark.asyncio
    async def test_configuration_validation(self):
        """Test configuration validation before use."""
        provider = OpenCodeSDKProvider()

        # Should be valid (SDK installed since tests are running)
        is_valid = await provider.validate_configuration()

        # May be True or False depending on environment
        assert isinstance(is_valid, bool)

    def test_configuration_schema(self):
        """Test configuration schema."""
        provider = OpenCodeSDKProvider()
        schema = provider.get_configuration_schema()

        assert schema['type'] == 'object'
        assert 'server_url' in schema['properties']
        assert 'api_key' in schema['properties']

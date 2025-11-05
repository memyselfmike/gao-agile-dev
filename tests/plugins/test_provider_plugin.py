"""Tests for provider plugin system."""

import pytest
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional, Type

from gao_dev.core.providers.base import IAgentProvider
from gao_dev.core.providers.models import AgentContext
from gao_dev.core.providers.factory import ProviderFactory
from gao_dev.core.providers.exceptions import DuplicateProviderError
from gao_dev.plugins.exceptions import PluginValidationError
from gao_dev.plugins.provider_plugin import BaseProviderPlugin
from gao_dev.plugins.provider_plugin_manager import ProviderPluginManager


# Test provider implementation
class MockProvider(IAgentProvider):
    """Mock provider for unit tests."""

    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.config = kwargs

    @property
    def name(self) -> str:
        return "test-provider"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def execute_task(
        self,
        task: str,
        context: AgentContext,
        model: str,
        tools: List[str],
        timeout: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        yield f"Executed: {task}"

    def supports_tool(self, tool_name: str) -> bool:
        return tool_name in ["Read", "Write", "Edit"]

    def get_supported_models(self) -> List[str]:
        return ["test-model"]

    def translate_model_name(self, gao_model_name: str) -> str:
        return gao_model_name

    def validate_configuration(self, config: Dict) -> bool:
        return "api_key" in config

    def get_configuration_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "api_key": {"type": "string"}
            },
            "required": ["api_key"]
        }

    def initialize(self) -> bool:
        return True

    def cleanup(self) -> None:
        pass


class MockProviderPlugin(BaseProviderPlugin):
    """Mock provider plugin."""

    def get_provider_name(self) -> str:
        return "test-provider"

    def get_provider_class(self) -> Type[IAgentProvider]:
        return MockProvider

    def validate_configuration(self, config: Dict) -> bool:
        return "api_key" in config

    def get_default_configuration(self) -> Dict:
        return {"timeout": 300}

    def get_supported_models(self) -> List[str]:
        return ["test-model"]

    def get_required_tools(self) -> List[str]:
        return []

    def get_setup_instructions(self) -> Optional[str]:
        return "Test setup instructions"


class TestBaseProviderPlugin:
    """Test BaseProviderPlugin interface."""

    def test_provider_name(self):
        """Test get_provider_name method."""
        plugin = MockProviderPlugin()
        assert plugin.get_provider_name() == "test-provider"

    def test_provider_class(self):
        """Test get_provider_class method."""
        plugin = MockProviderPlugin()
        provider_class = plugin.get_provider_class()
        assert provider_class == MockProvider
        assert issubclass(provider_class, IAgentProvider)

    def test_validate_configuration(self):
        """Test configuration validation."""
        plugin = MockProviderPlugin()

        # Valid config
        assert plugin.validate_configuration({"api_key": "test"})

        # Invalid config
        assert not plugin.validate_configuration({})

    def test_get_default_configuration(self):
        """Test default configuration."""
        plugin = MockProviderPlugin()
        defaults = plugin.get_default_configuration()
        assert "timeout" in defaults
        assert defaults["timeout"] == 300

    def test_get_supported_models(self):
        """Test supported models."""
        plugin = MockProviderPlugin()
        models = plugin.get_supported_models()
        assert "test-model" in models

    def test_get_required_tools(self):
        """Test required tools."""
        plugin = MockProviderPlugin()
        tools = plugin.get_required_tools()
        assert isinstance(tools, list)

    def test_get_setup_instructions(self):
        """Test setup instructions."""
        plugin = MockProviderPlugin()
        instructions = plugin.get_setup_instructions()
        assert instructions is not None
        assert "Test setup instructions" in instructions

    def test_on_provider_registered_callback(self):
        """Test on_provider_registered callback."""
        plugin = MockProviderPlugin()
        # Should not raise
        plugin.on_provider_registered()


class TestProviderPluginManager:
    """Test ProviderPluginManager."""

    def test_initialization(self):
        """Test manager initialization."""
        factory = ProviderFactory()
        manager = ProviderPluginManager(factory)
        assert manager.factory == factory
        assert len(manager.plugins) == 0

    def test_register_plugin(self):
        """Test plugin registration."""
        factory = ProviderFactory()
        manager = ProviderPluginManager(factory)
        plugin = MockProviderPlugin()

        # Register plugin
        manager.register_plugin(plugin)

        # Verify registration
        assert "test-provider" in manager.plugins
        assert "test-provider" in factory.list_providers()

    def test_register_plugin_with_custom_name(self):
        """Test plugin registration with custom name."""
        factory = ProviderFactory()
        manager = ProviderPluginManager(factory)
        plugin = MockProviderPlugin()

        # Register with custom name
        manager.register_plugin(plugin, "custom-name")

        # Verify registration
        assert "custom-name" in manager.plugins
        assert "custom-name" in factory.list_providers()

    def test_register_duplicate_provider(self):
        """Test registering duplicate provider raises error."""
        factory = ProviderFactory()
        manager = ProviderPluginManager(factory)
        plugin1 = MockProviderPlugin()
        plugin2 = MockProviderPlugin()

        # Register first plugin
        manager.register_plugin(plugin1)

        # Try to register duplicate - should raise ValueError or DuplicateProviderError
        with pytest.raises((ValueError, DuplicateProviderError)):
            manager.register_plugin(plugin2)

    def test_unregister_plugin(self):
        """Test plugin unregistration."""
        factory = ProviderFactory()
        manager = ProviderPluginManager(factory)
        plugin = MockProviderPlugin()

        # Register plugin
        manager.register_plugin(plugin)
        assert "test-provider" in manager.plugins

        # Unregister plugin
        manager.unregister_plugin("test-provider")
        assert "test-provider" not in manager.plugins

    def test_unregister_nonexistent_plugin(self):
        """Test unregistering non-existent plugin raises error."""
        factory = ProviderFactory()
        manager = ProviderPluginManager(factory)

        with pytest.raises(KeyError):
            manager.unregister_plugin("nonexistent")

    def test_list_provider_plugins(self):
        """Test listing provider plugins."""
        factory = ProviderFactory()
        manager = ProviderPluginManager(factory)
        plugin = MockProviderPlugin()

        # Initially empty
        assert len(manager.list_provider_plugins()) == 0

        # Register plugin
        manager.register_plugin(plugin)

        # List plugins
        plugins = manager.list_provider_plugins()
        assert len(plugins) == 1
        assert "test-provider" in plugins

    def test_get_plugin(self):
        """Test getting specific plugin."""
        factory = ProviderFactory()
        manager = ProviderPluginManager(factory)
        plugin = MockProviderPlugin()

        # Register plugin
        manager.register_plugin(plugin)

        # Get plugin
        retrieved = manager.get_plugin("test-provider")
        assert retrieved == plugin

        # Get non-existent plugin
        assert manager.get_plugin("nonexistent") is None

    def test_validate_provider_config(self):
        """Test provider configuration validation."""
        factory = ProviderFactory()
        manager = ProviderPluginManager(factory)
        plugin = MockProviderPlugin()
        manager.register_plugin(plugin)

        # Valid config
        assert manager.validate_provider_config(
            "test-provider", {"api_key": "test"}
        )

        # Invalid config
        assert not manager.validate_provider_config("test-provider", {})

    def test_validate_config_for_nonexistent_provider(self):
        """Test validation for non-existent provider raises error."""
        factory = ProviderFactory()
        manager = ProviderPluginManager(factory)

        with pytest.raises(KeyError):
            manager.validate_provider_config("nonexistent", {})

    def test_get_provider_info(self):
        """Test getting provider information."""
        factory = ProviderFactory()
        manager = ProviderPluginManager(factory)
        plugin = MockProviderPlugin()
        manager.register_plugin(plugin)

        # Get info
        info = manager.get_provider_info("test-provider")

        assert info["name"] == "test-provider"
        assert info["class"] == "MockProvider"
        assert "test-model" in info["supported_models"]
        assert info["required_tools"] == []
        assert "timeout" in info["default_config"]
        assert info["setup_instructions"] is not None

    def test_get_info_for_nonexistent_provider(self):
        """Test getting info for non-existent provider raises error."""
        factory = ProviderFactory()
        manager = ProviderPluginManager(factory)

        with pytest.raises(KeyError):
            manager.get_provider_info("nonexistent")


class TestProviderPluginValidation:
    """Test provider plugin validation."""

    def test_validate_plugin_missing_provider_name(self):
        """Test validation fails if provider_name method missing."""

        class BadPlugin(BaseProviderPlugin):
            def get_provider_class(self) -> Type[IAgentProvider]:
                return MockProvider

        # Cannot instantiate without implementing abstract method
        with pytest.raises(TypeError, match="abstract"):
            BadPlugin()

    def test_validate_plugin_missing_provider_class(self):
        """Test validation fails if provider_class method missing."""

        class BadPlugin(BaseProviderPlugin):
            def get_provider_name(self) -> str:
                return "bad-plugin"

        # Cannot instantiate without implementing abstract method
        with pytest.raises(TypeError, match="abstract"):
            BadPlugin()

    def test_validate_plugin_invalid_provider_class(self):
        """Test validation fails if provider class doesn't implement interface."""

        class NotAProvider:
            pass

        class BadPlugin(BaseProviderPlugin):
            def get_provider_name(self) -> str:
                return "bad-plugin"

            def get_provider_class(self) -> Type[IAgentProvider]:
                return NotAProvider  # type: ignore

        factory = ProviderFactory()
        manager = ProviderPluginManager(factory)
        plugin = BadPlugin()

        with pytest.raises(PluginValidationError, match="doesn't implement"):
            manager.register_plugin(plugin)

    def test_validate_plugin_empty_provider_name(self):
        """Test validation fails if provider name is empty."""

        class BadPlugin(BaseProviderPlugin):
            def get_provider_name(self) -> str:
                return ""

            def get_provider_class(self) -> Type[IAgentProvider]:
                return MockProvider

        factory = ProviderFactory()
        manager = ProviderPluginManager(factory)
        plugin = BadPlugin()

        with pytest.raises(PluginValidationError, match="empty provider name"):
            manager.register_plugin(plugin)


class TestProviderPluginIntegration:
    """Integration tests for provider plugin system."""

    @pytest.mark.asyncio
    async def test_end_to_end_plugin_registration(self):
        """Test complete plugin registration and usage flow."""
        # Create factory and manager
        factory = ProviderFactory()
        manager = ProviderPluginManager(factory)

        # Create and register plugin
        plugin = MockProviderPlugin()
        manager.register_plugin(plugin)

        # Create provider instance
        provider = factory.create_provider(
            "test-provider", {"api_key": "test123"}
        )

        # Execute task
        context = AgentContext(project_root=Path.cwd())

        # Collect results
        results = []
        async for message in provider.execute_task(
            "Test task", context, "test-model", ["Read", "Write"]
        ):
            results.append(message)

        # Verify results
        assert len(results) > 0
        assert "Test task" in results[0]

    def test_multiple_plugins_registration(self):
        """Test registering multiple plugins."""

        class Plugin1(BaseProviderPlugin):
            def get_provider_name(self) -> str:
                return "provider-1"

            def get_provider_class(self) -> Type[IAgentProvider]:
                return MockProvider

        class Plugin2(BaseProviderPlugin):
            def get_provider_name(self) -> str:
                return "provider-2"

            def get_provider_class(self) -> Type[IAgentProvider]:
                return MockProvider

        factory = ProviderFactory()
        manager = ProviderPluginManager(factory)

        # Register both plugins
        manager.register_plugin(Plugin1())
        manager.register_plugin(Plugin2())

        # Verify both registered
        assert "provider-1" in factory.list_providers()
        assert "provider-2" in factory.list_providers()
        assert len(manager.list_provider_plugins()) == 2

    def test_plugin_cleanup_called(self):
        """Test plugin cleanup is called on unregister."""
        cleanup_called = []

        class CleanupPlugin(MockProviderPlugin):
            def cleanup(self) -> None:
                cleanup_called.append(True)

        factory = ProviderFactory()
        manager = ProviderPluginManager(factory)
        plugin = CleanupPlugin()

        # Register and unregister
        manager.register_plugin(plugin)
        manager.unregister_plugin("test-provider")

        # Verify cleanup was called
        assert len(cleanup_called) == 1

    def test_plugin_on_registered_callback(self):
        """Test on_provider_registered callback is called."""
        callback_called = []

        class CallbackPlugin(MockProviderPlugin):
            def on_provider_registered(self) -> None:
                callback_called.append(True)

        factory = ProviderFactory()
        manager = ProviderPluginManager(factory)
        plugin = CallbackPlugin()

        # Register plugin
        manager.register_plugin(plugin)

        # Verify callback was called
        assert len(callback_called) == 1

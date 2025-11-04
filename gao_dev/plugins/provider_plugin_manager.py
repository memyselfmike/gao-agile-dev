"""Manager for provider plugins.

This module handles discovery, validation, and registration of provider plugins
with the ProviderFactory.
"""

import inspect
from pathlib import Path
from typing import Dict, List, Optional

import structlog

from gao_dev.core.providers.base import IAgentProvider
from gao_dev.core.providers.factory import ProviderFactory
from gao_dev.plugins.discovery import PluginDiscovery
from gao_dev.plugins.exceptions import PluginValidationError
from gao_dev.plugins.provider_plugin import BaseProviderPlugin

logger = structlog.get_logger(__name__)


class ProviderPluginManager:
    """Manages provider plugin lifecycle and registration.

    The ProviderPluginManager discovers provider plugins, validates them,
    and registers their providers with the ProviderFactory for use throughout
    GAO-Dev.

    Example:
        ```python
        from gao_dev.plugins.provider_plugin_manager import ProviderPluginManager
        from gao_dev.core.providers.factory import ProviderFactory

        # Initialize manager
        factory = ProviderFactory()
        manager = ProviderPluginManager(factory)

        # Discover and register plugins
        manager.discover_plugins()
        manager.register_all()

        # List registered providers
        providers = manager.list_provider_plugins()
        for name, plugin in providers.items():
            print(f"Provider: {name}")
        ```

    Attributes:
        factory: ProviderFactory instance for registering providers
        plugins: Dictionary of loaded provider plugins
    """

    def __init__(self, factory: ProviderFactory):
        """Initialize provider plugin manager.

        Args:
            factory: ProviderFactory to register providers with
        """
        self.factory = factory
        self.plugins: Dict[str, BaseProviderPlugin] = {}
        self._discovery: Optional[PluginDiscovery] = None

    def discover_plugins(
        self, plugin_dirs: Optional[List[Path]] = None
    ) -> List[str]:
        """Discover provider plugins in specified directories.

        Args:
            plugin_dirs: List of directories to search. If None, uses default
                        discovery paths.

        Returns:
            List of discovered provider plugin names

        Example:
            ```python
            manager = ProviderPluginManager(factory)
            plugins = manager.discover_plugins([Path("./my_plugins")])
            print(f"Found {len(plugins)} provider plugins")
            ```
        """
        if plugin_dirs is None:
            plugin_dirs = self._get_default_plugin_dirs()

        self._discovery = PluginDiscovery(plugin_dirs)
        discovered = self._discovery.discover_plugins()

        # Filter for provider plugins
        provider_plugins = []
        for plugin_name, plugin_info in discovered.items():
            try:
                # Load plugin class
                plugin_class = self._discovery.load_plugin_class(plugin_info)

                # Check if it's a provider plugin
                if self._is_provider_plugin(plugin_class):
                    provider_plugins.append(plugin_name)
                    logger.info(
                        "provider_plugin_discovered",
                        plugin_name=plugin_name,
                        plugin_class=plugin_class.__name__,
                    )
            except Exception as e:
                logger.warning(
                    "failed_to_check_plugin",
                    plugin_name=plugin_name,
                    error=str(e),
                )

        return provider_plugins

    def register_plugin(
        self, plugin: BaseProviderPlugin, plugin_name: Optional[str] = None
    ) -> None:
        """Register a provider plugin.

        Validates the plugin and registers its provider with the factory.

        Args:
            plugin: Provider plugin instance
            plugin_name: Optional name override (defaults to plugin.get_provider_name())

        Raises:
            PluginValidationError: If plugin validation fails
            ValueError: If provider name already registered

        Example:
            ```python
            plugin = MyProviderPlugin()
            manager.register_plugin(plugin)
            ```
        """
        # Get provider name
        provider_name = plugin_name or plugin.get_provider_name()

        # Validate plugin
        self._validate_plugin(plugin, provider_name)

        # Get provider class
        provider_class = plugin.get_provider_class()

        # Register with factory
        try:
            self.factory.register_provider(provider_name, provider_class)
            logger.info(
                "provider_plugin_registered",
                provider_name=provider_name,
                provider_class=provider_class.__name__,
            )
        except ValueError as e:
            raise ValueError(
                f"Failed to register provider '{provider_name}': {e}"
            ) from e

        # Store plugin
        self.plugins[provider_name] = plugin

        # Notify plugin
        plugin.on_provider_registered()

    def register_all(self) -> Dict[str, str]:
        """Register all discovered provider plugins.

        Returns:
            Dictionary mapping provider names to registration status
            ("success" or error message)

        Example:
            ```python
            manager.discover_plugins()
            results = manager.register_all()
            for name, status in results.items():
                print(f"{name}: {status}")
            ```
        """
        if self._discovery is None:
            self.discover_plugins()

        results = {}
        assert self._discovery is not None  # For type checker

        for plugin_name, plugin_info in self._discovery._plugins.items():
            try:
                # Load plugin class
                plugin_class = self._discovery.load_plugin_class(plugin_info)

                # Check if provider plugin
                if not self._is_provider_plugin(plugin_class):
                    continue

                # Instantiate plugin
                plugin = plugin_class()

                # Initialize plugin
                if hasattr(plugin, "initialize"):
                    if not plugin.initialize():
                        results[plugin_name] = "initialization_failed"
                        continue

                # Register plugin
                self.register_plugin(plugin, plugin_name)
                results[plugin_name] = "success"

            except Exception as e:
                logger.error(
                    "provider_plugin_registration_failed",
                    plugin_name=plugin_name,
                    error=str(e),
                )
                results[plugin_name] = str(e)

        return results

    def unregister_plugin(self, provider_name: str) -> None:
        """Unregister a provider plugin.

        Args:
            provider_name: Name of provider to unregister

        Raises:
            KeyError: If provider not found
        """
        if provider_name not in self.plugins:
            raise KeyError(f"Provider plugin '{provider_name}' not found")

        plugin = self.plugins[provider_name]

        # Cleanup plugin
        if hasattr(plugin, "cleanup"):
            try:
                plugin.cleanup()
            except Exception as e:
                logger.warning(
                    "plugin_cleanup_failed",
                    provider_name=provider_name,
                    error=str(e),
                )

        # Remove from registry
        del self.plugins[provider_name]

        logger.info("provider_plugin_unregistered", provider_name=provider_name)

    def list_provider_plugins(self) -> Dict[str, BaseProviderPlugin]:
        """List all registered provider plugins.

        Returns:
            Dictionary mapping provider names to plugin instances
        """
        return self.plugins.copy()

    def get_plugin(self, provider_name: str) -> Optional[BaseProviderPlugin]:
        """Get a specific provider plugin.

        Args:
            provider_name: Name of provider

        Returns:
            Plugin instance or None if not found
        """
        return self.plugins.get(provider_name)

    def validate_provider_config(
        self, provider_name: str, config: Dict
    ) -> bool:
        """Validate configuration for a provider.

        Args:
            provider_name: Name of provider
            config: Configuration dictionary

        Returns:
            True if valid, False otherwise

        Raises:
            KeyError: If provider not found
        """
        plugin = self.get_plugin(provider_name)
        if plugin is None:
            raise KeyError(f"Provider '{provider_name}' not found")

        return plugin.validate_configuration(config)

    def get_provider_info(self, provider_name: str) -> Dict:
        """Get information about a provider plugin.

        Args:
            provider_name: Name of provider

        Returns:
            Dictionary with provider metadata

        Raises:
            KeyError: If provider not found
        """
        plugin = self.get_plugin(provider_name)
        if plugin is None:
            raise KeyError(f"Provider '{provider_name}' not found")

        return {
            "name": provider_name,
            "class": plugin.get_provider_class().__name__,
            "supported_models": plugin.get_supported_models(),
            "required_tools": plugin.get_required_tools(),
            "default_config": plugin.get_default_configuration(),
            "setup_instructions": plugin.get_setup_instructions(),
        }

    # Private methods

    def _get_default_plugin_dirs(self) -> List[Path]:
        """Get default plugin discovery directories."""
        return [
            Path.cwd() / "plugins",
            Path.home() / ".gao-dev" / "plugins",
        ]

    def _is_provider_plugin(self, plugin_class: type) -> bool:
        """Check if a class is a provider plugin."""
        return (
            inspect.isclass(plugin_class)
            and issubclass(plugin_class, BaseProviderPlugin)
            and plugin_class is not BaseProviderPlugin
        )

    def _validate_plugin(
        self, plugin: BaseProviderPlugin, provider_name: str
    ) -> None:
        """Validate a provider plugin.

        Args:
            plugin: Plugin instance to validate
            provider_name: Provider name

        Raises:
            PluginValidationError: If validation fails
        """
        # Check required methods
        if not hasattr(plugin, "get_provider_name"):
            raise PluginValidationError(
                f"Plugin '{provider_name}' missing get_provider_name method"
            )

        if not hasattr(plugin, "get_provider_class"):
            raise PluginValidationError(
                f"Plugin '{provider_name}' missing get_provider_class method"
            )

        # Get provider class
        try:
            provider_class = plugin.get_provider_class()
        except Exception as e:
            raise PluginValidationError(
                f"Plugin '{provider_name}' get_provider_class failed: {e}"
            ) from e

        # Validate provider class implements IAgentProvider
        if not issubclass(provider_class, IAgentProvider):
            raise PluginValidationError(
                f"Provider class '{provider_class.__name__}' doesn't implement IAgentProvider"
            )

        # Validate provider name
        plugin_provider_name = plugin.get_provider_name()
        if not plugin_provider_name:
            raise PluginValidationError(
                f"Plugin '{provider_name}' returned empty provider name"
            )

        if not isinstance(plugin_provider_name, str):
            raise PluginValidationError(
                f"Plugin '{provider_name}' provider name must be string, got {type(plugin_provider_name)}"
            )

        logger.debug(
            "provider_plugin_validated",
            provider_name=provider_name,
            provider_class=provider_class.__name__,
        )

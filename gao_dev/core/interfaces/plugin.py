"""Plugin system interfaces."""

from abc import ABC, abstractmethod
from typing import List
from pathlib import Path
from ...plugins.models import PluginMetadata


class IPluginDiscovery(ABC):
    """Interface for plugin discovery.

    Implementations of this interface scan configured directories,
    identify valid plugins, load their metadata, and return discovered
    plugin information.
    """

    @abstractmethod
    def discover_plugins(self, plugin_dirs: List[Path]) -> List[PluginMetadata]:
        """Discover all valid plugins in given directories.

        Args:
            plugin_dirs: List of directories to scan for plugins

        Returns:
            List of discovered plugin metadata

        Raises:
            PluginValidationError: If plugin metadata validation fails
        """
        pass

    @abstractmethod
    def is_valid_plugin(self, plugin_path: Path) -> bool:
        """Check if path contains a valid plugin.

        Args:
            plugin_path: Path to potential plugin directory

        Returns:
            True if valid plugin structure, False otherwise
        """
        pass

    @abstractmethod
    def load_plugin_metadata(self, plugin_path: Path) -> PluginMetadata:
        """Load metadata from plugin directory.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Plugin metadata object

        Raises:
            PluginValidationError: If metadata is invalid
            PluginLoadError: If metadata file cannot be read
        """
        pass

    @abstractmethod
    def get_plugin_dirs(self) -> List[Path]:
        """Get plugin directories from configuration.

        Returns:
            List of absolute paths to plugin directories

        Note:
            Creates directories if they don't exist
        """
        pass


class IPluginLoader(ABC):
    """Interface for plugin loading and lifecycle management.

    Implementations handle loading plugins, managing their lifecycle,
    and providing access to loaded plugin instances.
    """

    @abstractmethod
    def load_plugin(self, metadata: PluginMetadata):
        """Load a plugin from its metadata.

        Args:
            metadata: Plugin metadata

        Raises:
            PluginLoadError: If plugin fails to load
            PluginSecurityError: If plugin violates security constraints
        """
        pass

    @abstractmethod
    def unload_plugin(self, plugin_name: str):
        """Unload a plugin by name.

        Args:
            plugin_name: Name of plugin to unload

        Raises:
            PluginNotFoundError: If plugin not loaded
        """
        pass

    @abstractmethod
    def reload_plugin(self, plugin_name: str):
        """Reload a plugin by name.

        Args:
            plugin_name: Name of plugin to reload

        Raises:
            PluginNotFoundError: If plugin not found
            PluginLoadError: If plugin fails to reload
        """
        pass

    @abstractmethod
    def get_loaded_plugin(self, plugin_name: str):
        """Get a loaded plugin instance.

        Args:
            plugin_name: Name of plugin

        Returns:
            Plugin instance

        Raises:
            PluginNotFoundError: If plugin not loaded
        """
        pass

    @abstractmethod
    def is_loaded(self, plugin_name: str) -> bool:
        """Check if plugin is loaded.

        Args:
            plugin_name: Name of plugin

        Returns:
            True if loaded, False otherwise
        """
        pass


class IPluginRegistry(ABC):
    """Interface for plugin registry.

    Implementations maintain a registry of available and loaded plugins,
    providing registration, lookup, and management capabilities.
    """

    @abstractmethod
    def register(self, metadata: PluginMetadata):
        """Register a plugin.

        Args:
            metadata: Plugin metadata

        Raises:
            DuplicatePluginError: If plugin already registered
        """
        pass

    @abstractmethod
    def unregister(self, plugin_name: str):
        """Unregister a plugin.

        Args:
            plugin_name: Name of plugin to unregister

        Raises:
            PluginNotFoundError: If plugin not registered
        """
        pass

    @abstractmethod
    def get_plugin(self, plugin_name: str) -> PluginMetadata:
        """Get plugin metadata by name.

        Args:
            plugin_name: Name of plugin

        Returns:
            Plugin metadata

        Raises:
            PluginNotFoundError: If plugin not registered
        """
        pass

    @abstractmethod
    def list_plugins(self, plugin_type: str = None) -> List[PluginMetadata]:
        """List registered plugins.

        Args:
            plugin_type: Optional plugin type filter

        Returns:
            List of plugin metadata
        """
        pass

    @abstractmethod
    def plugin_exists(self, plugin_name: str) -> bool:
        """Check if plugin is registered.

        Args:
            plugin_name: Name of plugin

        Returns:
            True if registered, False otherwise
        """
        pass

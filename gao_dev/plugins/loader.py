"""Plugin loading and lifecycle management."""

import importlib
import sys
from pathlib import Path
from typing import Dict, Any, List
import structlog

from ..core.interfaces.plugin import IPluginLoader
from .models import PluginMetadata
from .exceptions import (
    PluginLoadError,
    PluginNotFoundError,
    DuplicatePluginError,
)

logger = structlog.get_logger(__name__)


class PluginLoader(IPluginLoader):
    """Loads and manages plugin instances with lifecycle management.

    Handles dynamic module import, class instantiation, lifecycle hooks,
    and plugin registry management.

    Lifecycle:
        1. load_plugin() - Import module, instantiate class
        2. initialize() - Call plugin's initialize() hook (optional)
        3. [Plugin is active and can be used]
        4. cleanup() - Call plugin's cleanup() hook (optional)
        5. unload_plugin() - Remove from registry

    Example:
        ```python
        loader = PluginLoader()

        # Load a plugin
        metadata = PluginMetadata(...)
        loader.load_plugin(metadata)

        # Use plugin
        plugin = loader.get_loaded_plugin("my-plugin")
        plugin.do_something()

        # Unload when done
        loader.unload_plugin("my-plugin")
        ```
    """

    def __init__(self):
        """Initialize plugin loader with empty registries."""
        self._loaded_plugins: Dict[str, Any] = {}
        self._plugin_metadata: Dict[str, PluginMetadata] = {}

    def load_plugin(self, metadata: PluginMetadata) -> None:
        """Load a plugin from its metadata.

        Dynamically imports the plugin module, instantiates the plugin class,
        calls the initialize() hook if present, and stores the plugin instance.

        Args:
            metadata: Plugin metadata containing entry point and configuration

        Raises:
            DuplicatePluginError: If plugin already loaded
            PluginLoadError: If import, instantiation, or initialization fails
        """
        plugin_name = metadata.name.lower()

        # Check if already loaded
        if plugin_name in self._loaded_plugins:
            raise DuplicatePluginError(
                f"Plugin '{metadata.name}' is already loaded"
            )

        plugin_parent_dir = None
        try:
            # Add plugin parent directory to sys.path temporarily
            # This allows importing like: "plugin_name.module.Class"
            plugin_parent_dir = str(metadata.plugin_path.parent)
            if plugin_parent_dir not in sys.path:
                sys.path.insert(0, plugin_parent_dir)

            # Parse entry point: "module.path.ClassName"
            module_path, class_name = self._parse_entry_point(metadata.entry_point)

            # Import module
            try:
                module = importlib.import_module(module_path)
            except ImportError as e:
                raise PluginLoadError(
                    f"Failed to import plugin module '{module_path}': {e}"
                ) from e

            # Get class from module
            if not hasattr(module, class_name):
                raise PluginLoadError(
                    f"Module '{module_path}' has no class '{class_name}'"
                )

            plugin_class = getattr(module, class_name)

            # Instantiate plugin
            try:
                plugin_instance = plugin_class()
            except Exception as e:
                raise PluginLoadError(
                    f"Failed to instantiate plugin class '{class_name}': {e}"
                ) from e

            # Call initialize hook if exists
            if hasattr(plugin_instance, 'initialize'):
                try:
                    success = plugin_instance.initialize()
                    if success is False:
                        raise PluginLoadError(
                            f"Plugin '{metadata.name}' initialization returned False"
                        )
                except Exception as e:
                    raise PluginLoadError(
                        f"Plugin '{metadata.name}' initialization failed: {e}"
                    ) from e

            # Store plugin
            self._loaded_plugins[plugin_name] = plugin_instance
            self._plugin_metadata[plugin_name] = metadata

            logger.info(
                "plugin_loaded",
                plugin_name=metadata.name,
                plugin_type=metadata.type.value,
                plugin_version=metadata.version
            )

        except (DuplicatePluginError, PluginLoadError):
            # Re-raise plugin-specific errors
            raise
        except Exception as e:
            raise PluginLoadError(
                f"Unexpected error loading plugin '{metadata.name}': {e}"
            ) from e
        finally:
            # Remove plugin parent directory from sys.path
            if plugin_parent_dir and plugin_parent_dir in sys.path:
                sys.path.remove(plugin_parent_dir)

    def unload_plugin(self, plugin_name: str) -> None:
        """Unload a plugin by name.

        Calls the plugin's cleanup() hook if present, then removes the
        plugin from the registry.

        Args:
            plugin_name: Name of plugin to unload (case-insensitive)

        Raises:
            PluginNotFoundError: If plugin is not loaded
        """
        plugin_name_lower = plugin_name.lower()

        if plugin_name_lower not in self._loaded_plugins:
            raise PluginNotFoundError(
                f"Plugin '{plugin_name}' is not loaded. "
                f"Loaded plugins: {list(self._loaded_plugins.keys())}"
            )

        plugin_instance = self._loaded_plugins[plugin_name_lower]
        metadata = self._plugin_metadata[plugin_name_lower]

        # Call cleanup hook if exists
        if hasattr(plugin_instance, 'cleanup'):
            try:
                plugin_instance.cleanup()
            except Exception as e:
                logger.warning(
                    "plugin_cleanup_failed",
                    plugin_name=plugin_name,
                    error=str(e),
                    exc_info=True
                )

        # Remove from registry
        del self._loaded_plugins[plugin_name_lower]
        del self._plugin_metadata[plugin_name_lower]

        logger.info(
            "plugin_unloaded",
            plugin_name=metadata.name,
            plugin_type=metadata.type.value
        )

    def reload_plugin(self, plugin_name: str) -> None:
        """Reload a plugin by name.

        Unloads the existing plugin and loads it again with fresh metadata.
        This is useful for plugin development and hot-reloading.

        Args:
            plugin_name: Name of plugin to reload (case-insensitive)

        Raises:
            PluginNotFoundError: If plugin is not loaded
            PluginLoadError: If plugin fails to reload
        """
        plugin_name_lower = plugin_name.lower()

        if plugin_name_lower not in self._plugin_metadata:
            raise PluginNotFoundError(
                f"Plugin '{plugin_name}' is not loaded"
            )

        # Get current metadata
        metadata = self._plugin_metadata[plugin_name_lower]

        # Unload
        self.unload_plugin(plugin_name)

        # Reload module from disk (clear import cache)
        module_path, _ = self._parse_entry_point(metadata.entry_point)
        if module_path in sys.modules:
            importlib.reload(sys.modules[module_path])

        # Load again
        self.load_plugin(metadata)

        logger.info(
            "plugin_reloaded",
            plugin_name=metadata.name,
            plugin_type=metadata.type.value
        )

    def get_loaded_plugin(self, plugin_name: str) -> Any:
        """Get a loaded plugin instance.

        Args:
            plugin_name: Name of plugin (case-insensitive)

        Returns:
            Plugin instance

        Raises:
            PluginNotFoundError: If plugin is not loaded
        """
        plugin_name_lower = plugin_name.lower()

        if plugin_name_lower not in self._loaded_plugins:
            raise PluginNotFoundError(
                f"Plugin '{plugin_name}' is not loaded. "
                f"Loaded plugins: {list(self._loaded_plugins.keys())}"
            )

        return self._loaded_plugins[plugin_name_lower]

    def is_loaded(self, plugin_name: str) -> bool:
        """Check if plugin is loaded.

        Args:
            plugin_name: Name of plugin (case-insensitive)

        Returns:
            True if plugin is loaded, False otherwise
        """
        return plugin_name.lower() in self._loaded_plugins

    def list_loaded_plugins(self) -> List[str]:
        """List all loaded plugin names.

        Returns:
            List of plugin names (sorted alphabetically)
        """
        return sorted(self._loaded_plugins.keys())

    def load_all_enabled(
        self,
        discovered_plugins: List[PluginMetadata]
    ) -> Dict[str, str]:
        """Load all enabled plugins from discovered list.

        Filters out disabled plugins and loads each enabled plugin,
        tracking the result for each plugin.

        Args:
            discovered_plugins: List of discovered plugin metadata

        Returns:
            Dictionary mapping plugin_name to status:
            - "loaded": Successfully loaded
            - "skipped (disabled)": Plugin disabled in metadata
            - "failed: <error>": Load error with message
        """
        results = {}

        for metadata in discovered_plugins:
            if not metadata.enabled:
                results[metadata.name] = "skipped (disabled)"
                logger.debug(
                    "plugin_skipped",
                    plugin_name=metadata.name,
                    reason="disabled"
                )
                continue

            try:
                self.load_plugin(metadata)
                results[metadata.name] = "loaded"
            except Exception as e:
                error_msg = f"failed: {e}"
                results[metadata.name] = error_msg
                logger.error(
                    "plugin_load_failed",
                    plugin_name=metadata.name,
                    error=str(e),
                    exc_info=True
                )

        logger.info(
            "plugin_batch_load_complete",
            total_plugins=len(discovered_plugins),
            loaded=sum(1 for s in results.values() if s == "loaded"),
            skipped=sum(1 for s in results.values() if s.startswith("skipped")),
            failed=sum(1 for s in results.values() if s.startswith("failed"))
        )

        return results

    def unload_all(self) -> None:
        """Unload all loaded plugins.

        Calls cleanup() on each plugin and removes from registry.
        Errors during unload are logged but don't stop the process.
        """
        # Get list of plugin names (copy to avoid modification during iteration)
        plugin_names = list(self._loaded_plugins.keys())

        for plugin_name in plugin_names:
            try:
                self.unload_plugin(plugin_name)
            except Exception as e:
                logger.error(
                    "plugin_unload_failed",
                    plugin_name=plugin_name,
                    error=str(e),
                    exc_info=True
                )

        logger.info(
            "all_plugins_unloaded",
            count=len(plugin_names)
        )

    def get_plugin_metadata(self, plugin_name: str) -> PluginMetadata:
        """Get metadata for a loaded plugin.

        Args:
            plugin_name: Name of plugin (case-insensitive)

        Returns:
            Plugin metadata

        Raises:
            PluginNotFoundError: If plugin is not loaded
        """
        plugin_name_lower = plugin_name.lower()

        if plugin_name_lower not in self._plugin_metadata:
            raise PluginNotFoundError(
                f"Plugin '{plugin_name}' is not loaded"
            )

        return self._plugin_metadata[plugin_name_lower]

    # Private helper methods

    def _parse_entry_point(self, entry_point: str) -> tuple[str, str]:
        """Parse entry point into module path and class name.

        Args:
            entry_point: Entry point string (e.g., "my_plugin.agent.MyAgent")

        Returns:
            Tuple of (module_path, class_name)

        Raises:
            PluginLoadError: If entry point format is invalid
        """
        if not entry_point or '.' not in entry_point:
            raise PluginLoadError(
                f"Invalid entry point '{entry_point}'. "
                f"Must be in format 'module.path.ClassName'"
            )

        parts = entry_point.rsplit('.', 1)
        if len(parts) != 2:
            raise PluginLoadError(
                f"Invalid entry point '{entry_point}'. "
                f"Must contain module path and class name"
            )

        module_path, class_name = parts
        return module_path, class_name

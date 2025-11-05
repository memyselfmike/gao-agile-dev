"""
ChecklistPluginManager for GAO-Dev.

Manages the lifecycle of checklist plugins including discovery,
registration, and dependency resolution.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import structlog

from gao_dev.plugins.checklist_plugin import ChecklistPlugin

logger = structlog.get_logger(__name__)


class ChecklistPluginManager:
    """
    Manages checklist plugin lifecycle.

    Handles:
    - Auto-discovery of plugins in configured directories
    - Manual registration via API
    - Plugin priority management for override order
    - Dependency resolution between plugins
    - Plugin enable/disable capability
    """

    def __init__(self, plugins_dir: Optional[Path] = None):
        """
        Initialize plugin manager.

        Args:
            plugins_dir: Optional directory to search for plugins.
                        If None, discovery is not performed automatically.
        """
        self.plugins_dir = plugins_dir
        self.plugins: Dict[str, ChecklistPlugin] = {}
        self._plugin_priority: Dict[str, int] = {}
        self._plugin_metadata: Dict[str, Dict] = {}

    def discover_plugins(self) -> List[ChecklistPlugin]:
        """
        Discover all checklist plugins in plugins directory.

        Scans the plugins directory for Python modules that contain
        ChecklistPlugin implementations. Automatically imports and
        instantiates discovered plugins.

        Returns:
            List of discovered ChecklistPlugin instances

        Example:
            >>> manager = ChecklistPluginManager(Path("plugins"))
            >>> plugins = manager.discover_plugins()
            >>> print(f"Found {len(plugins)} plugins")
        """
        if not self.plugins_dir:
            logger.warning("no_plugins_dir_configured")
            return []

        if not self.plugins_dir.exists():
            logger.warning(
                "plugins_dir_not_found", plugins_dir=str(self.plugins_dir)
            )
            return []

        discovered = []

        # Scan for plugin directories
        for item in self.plugins_dir.iterdir():
            if not item.is_dir():
                continue

            # Skip hidden directories and __pycache__
            if item.name.startswith(".") or item.name == "__pycache__":
                continue

            # Look for __init__.py
            init_file = item / "__init__.py"
            if not init_file.exists():
                continue

            try:
                # Try to import the module
                module_name = f"checklist_plugin_{item.name}"
                spec = importlib.util.spec_from_file_location(
                    module_name, init_file
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)

                    # Find ChecklistPlugin subclasses
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, ChecklistPlugin)
                            and attr is not ChecklistPlugin
                        ):
                            # Instantiate the plugin
                            plugin = attr()
                            metadata = plugin.get_checklist_metadata()
                            name = metadata.get("name")
                            priority = metadata.get("priority", 0)

                            if not name:
                                logger.warning(
                                    "plugin_missing_name",
                                    plugin_path=str(item),
                                )
                                continue

                            # Initialize plugin
                            if plugin.initialize():
                                self.register_plugin(plugin, metadata)
                                discovered.append(plugin)
                                logger.info(
                                    "checklist_plugin_discovered",
                                    plugin_name=name,
                                    version=metadata.get("version"),
                                    priority=priority,
                                    plugin_path=str(item),
                                )
                            else:
                                logger.warning(
                                    "plugin_initialization_failed",
                                    plugin_name=name,
                                    plugin_path=str(item),
                                )

            except Exception as e:
                logger.error(
                    "plugin_discovery_error",
                    plugin_path=str(item),
                    error=str(e),
                    exc_info=True,
                )

        logger.info(
            "plugin_discovery_complete",
            plugins_found=len(discovered),
            plugin_names=list(self.plugins.keys()),
        )

        return discovered

    def register_plugin(
        self, plugin: ChecklistPlugin, metadata: Optional[Dict] = None
    ) -> None:
        """
        Manually register a plugin.

        Args:
            plugin: ChecklistPlugin instance to register
            metadata: Optional metadata (if not provided, will call get_checklist_metadata())

        Example:
            >>> from my_plugin import MyPlugin
            >>> manager = ChecklistPluginManager()
            >>> manager.register_plugin(MyPlugin())
        """
        if metadata is None:
            metadata = plugin.get_checklist_metadata()

        name = metadata.get("name")
        if not name:
            raise ValueError("Plugin metadata must include 'name' field")

        priority = metadata.get("priority", 0)

        self.plugins[name] = plugin
        self._plugin_priority[name] = priority
        self._plugin_metadata[name] = metadata

        logger.info(
            "plugin_registered",
            plugin_name=name,
            version=metadata.get("version"),
            priority=priority,
        )

    def get_plugin(self, name: str) -> Optional[ChecklistPlugin]:
        """
        Get plugin by name.

        Args:
            name: Plugin name

        Returns:
            ChecklistPlugin instance or None if not found
        """
        return self.plugins.get(name)

    def get_all_checklist_directories(self) -> List[Tuple[Path, str, int]]:
        """
        Get all checklist directories from all plugins.

        Returns:
            List of tuples: (directory_path, plugin_name, priority)
            Sorted by priority (highest first)

        Example:
            >>> manager = ChecklistPluginManager()
            >>> # ... register plugins ...
            >>> for path, plugin_name, priority in manager.get_all_checklist_directories():
            ...     print(f"{plugin_name} (priority {priority}): {path}")
        """
        directories = []
        for name, plugin in self.plugins.items():
            priority = self._plugin_priority[name]
            for directory in plugin.get_checklist_directories():
                directories.append((directory, name, priority))

        # Sort by priority descending (highest priority first)
        directories.sort(key=lambda x: x[2], reverse=True)
        return directories

    def validate_dependencies(self) -> bool:
        """
        Validate all plugin dependencies are met.

        Checks that each plugin's declared dependencies are satisfied
        by other registered plugins.

        Returns:
            True if all dependencies satisfied, False otherwise

        Example:
            >>> manager = ChecklistPluginManager()
            >>> # ... register plugins ...
            >>> if not manager.validate_dependencies():
            ...     print("Dependency validation failed!")
        """
        for name, plugin in self.plugins.items():
            metadata = self._plugin_metadata[name]
            dependencies = metadata.get("dependencies", [])

            for dep in dependencies:
                if dep not in self.plugins:
                    logger.error(
                        "plugin_dependency_missing",
                        plugin=name,
                        missing_dependency=dep,
                    )
                    return False

        logger.info("plugin_dependencies_validated")
        return True

    def list_plugins(self) -> List[Tuple[str, Dict]]:
        """
        List all registered plugins with metadata.

        Returns:
            List of tuples: (plugin_name, metadata)

        Example:
            >>> manager = ChecklistPluginManager()
            >>> for name, metadata in manager.list_plugins():
            ...     print(f"{name} v{metadata['version']}")
        """
        return [(name, self._plugin_metadata[name]) for name in self.plugins.keys()]

    def enable_plugin(self, name: str) -> bool:
        """
        Enable a disabled plugin.

        Args:
            name: Plugin name

        Returns:
            True if enabled successfully, False if plugin not found
        """
        if name in self._plugin_metadata:
            self._plugin_metadata[name]["enabled"] = True
            logger.info("plugin_enabled", plugin_name=name)
            return True
        return False

    def disable_plugin(self, name: str) -> bool:
        """
        Disable a plugin without removing it.

        Args:
            name: Plugin name

        Returns:
            True if disabled successfully, False if plugin not found
        """
        if name in self._plugin_metadata:
            self._plugin_metadata[name]["enabled"] = False
            logger.info("plugin_disabled", plugin_name=name)
            return True
        return False

    def is_plugin_enabled(self, name: str) -> bool:
        """
        Check if plugin is enabled.

        Args:
            name: Plugin name

        Returns:
            True if plugin exists and is enabled, False otherwise
        """
        if name not in self._plugin_metadata:
            return False
        return self._plugin_metadata[name].get("enabled", True)

    def cleanup(self) -> None:
        """
        Cleanup all registered plugins.

        Calls cleanup() on each plugin and clears the registry.
        """
        for name, plugin in self.plugins.items():
            try:
                plugin.cleanup()
                logger.info("plugin_cleaned_up", plugin_name=name)
            except Exception as e:
                logger.error(
                    "plugin_cleanup_error",
                    plugin_name=name,
                    error=str(e),
                    exc_info=True,
                )

        self.plugins.clear()
        self._plugin_priority.clear()
        self._plugin_metadata.clear()
        logger.info("all_plugins_cleaned_up")

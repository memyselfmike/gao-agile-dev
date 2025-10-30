"""GAO-Dev Plugin System.

This package provides the plugin architecture for GAO-Dev, enabling dynamic
loading of custom agents, workflows, methodologies, and tools.

Key Components:
- PluginDiscovery: Discovers plugins from configured directories
- PluginLoader: Loads and manages plugin lifecycle
- BasePlugin: Base class for plugins with lifecycle hooks
- PluginRegistry: Registers and manages loaded plugins
"""

from .models import PluginMetadata, PluginType
from .discovery import PluginDiscovery
from .loader import PluginLoader
from .base_plugin import BasePlugin
from .exceptions import (
    PluginError,
    PluginValidationError,
    PluginNotFoundError,
    PluginLoadError,
    DuplicatePluginError,
)

__all__ = [
    'PluginMetadata',
    'PluginType',
    'PluginDiscovery',
    'PluginLoader',
    'BasePlugin',
    'PluginError',
    'PluginValidationError',
    'PluginNotFoundError',
    'PluginLoadError',
    'DuplicatePluginError',
]

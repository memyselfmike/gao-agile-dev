"""GAO-Dev Plugin System.

This package provides the plugin architecture for GAO-Dev, enabling dynamic
loading of custom agents, workflows, methodologies, and tools.

Key Components:
- PluginDiscovery: Discovers plugins from configured directories
- PluginLoader: Loads and manages plugin lifecycle
- PluginRegistry: Registers and manages loaded plugins
"""

from .models import PluginMetadata, PluginType
from .exceptions import (
    PluginError,
    PluginValidationError,
    PluginNotFoundError,
    PluginLoadError
)

__all__ = [
    'PluginMetadata',
    'PluginType',
    'PluginError',
    'PluginValidationError',
    'PluginNotFoundError',
    'PluginLoadError',
]

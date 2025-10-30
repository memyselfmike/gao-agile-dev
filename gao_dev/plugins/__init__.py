"""GAO-Dev Plugin System.

This package provides the plugin architecture for GAO-Dev, enabling dynamic
loading of custom agents, workflows, methodologies, and tools.

Key Components:
- PluginDiscovery: Discovers plugins from configured directories
- PluginLoader: Loads and manages plugin lifecycle
- BasePlugin: Base class for plugins with lifecycle hooks
- BaseAgentPlugin: Base class for agent plugins
- AgentPluginManager: Manages agent plugins
- PluginRegistry: Registers and manages loaded plugins
"""

from .models import PluginMetadata, PluginType, AgentMetadata, WorkflowMetadata
from .discovery import PluginDiscovery
from .loader import PluginLoader
from .base_plugin import BasePlugin
from .agent_plugin import BaseAgentPlugin
from .agent_plugin_manager import AgentPluginManager
from .workflow_plugin import BaseWorkflowPlugin
from .workflow_plugin_manager import WorkflowPluginManager
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
    'AgentMetadata',
    'WorkflowMetadata',
    'PluginDiscovery',
    'PluginLoader',
    'BasePlugin',
    'BaseAgentPlugin',
    'AgentPluginManager',
    'BaseWorkflowPlugin',
    'WorkflowPluginManager',
    'PluginError',
    'PluginValidationError',
    'PluginNotFoundError',
    'PluginLoadError',
    'DuplicatePluginError',
]

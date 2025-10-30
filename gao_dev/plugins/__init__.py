"""GAO-Dev Plugin System.

This package provides the plugin architecture for GAO-Dev, enabling dynamic
loading of custom agents, workflows, methodologies, and tools.

Key Components:
- PluginDiscovery: Discovers plugins from configured directories
- PluginLoader: Loads and manages plugin lifecycle
- BasePlugin: Base class for plugins with lifecycle hooks
- BaseAgentPlugin: Base class for agent plugins
- AgentPluginManager: Manages agent plugins
- BaseWorkflowPlugin: Base class for workflow plugins
- WorkflowPluginManager: Manages workflow plugins
- PluginSandbox: Security and resource management
- PermissionManager: Permission management
- ResourceMonitor: Resource monitoring
"""

from .models import (
    PluginMetadata,
    PluginType,
    PluginPermission,
    ValidationResult,
    ResourceUsage,
    AgentMetadata,
    WorkflowMetadata,
)
from .discovery import PluginDiscovery
from .loader import PluginLoader
from .base_plugin import BasePlugin
from .agent_plugin import BaseAgentPlugin
from .agent_plugin_manager import AgentPluginManager
from .workflow_plugin import BaseWorkflowPlugin
from .workflow_plugin_manager import WorkflowPluginManager
from .sandbox import PluginSandbox
from .permission_manager import PermissionManager
from .resource_monitor import ResourceMonitor
from .exceptions import (
    PluginError,
    PluginValidationError,
    PluginNotFoundError,
    PluginLoadError,
    PluginSecurityError,
    PermissionDeniedError,
    PluginTimeoutError,
    ResourceLimitError,
    DuplicatePluginError,
)

__all__ = [
    # Models
    'PluginMetadata',
    'PluginType',
    'PluginPermission',
    'ValidationResult',
    'ResourceUsage',
    'AgentMetadata',
    'WorkflowMetadata',
    # Core Components
    'PluginDiscovery',
    'PluginLoader',
    'BasePlugin',
    'BaseAgentPlugin',
    'AgentPluginManager',
    'BaseWorkflowPlugin',
    'WorkflowPluginManager',
    # Security
    'PluginSandbox',
    'PermissionManager',
    'ResourceMonitor',
    # Exceptions
    'PluginError',
    'PluginValidationError',
    'PluginNotFoundError',
    'PluginLoadError',
    'PluginSecurityError',
    'PermissionDeniedError',
    'PluginTimeoutError',
    'ResourceLimitError',
    'DuplicatePluginError',
]

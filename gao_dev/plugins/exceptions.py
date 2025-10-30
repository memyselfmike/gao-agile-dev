"""Plugin system exceptions."""


class PluginError(Exception):
    """Base exception for plugin system errors."""

    pass


class PluginValidationError(PluginError):
    """Raised when plugin validation fails.

    This includes:
    - Invalid plugin.yaml structure
    - Missing required metadata fields
    - Invalid version format
    - Invalid entry point format
    - Invalid plugin name
    """

    pass


class PluginNotFoundError(PluginError):
    """Raised when a plugin cannot be found.

    This occurs when:
    - Plugin directory doesn't exist
    - Plugin not registered
    - Plugin name not in registry
    """

    pass


class PluginLoadError(PluginError):
    """Raised when plugin fails to load.

    This includes:
    - Module import errors
    - Class instantiation errors
    - Missing dependencies
    - Invalid plugin implementation
    """

    pass


class PluginSecurityError(PluginError):
    """Raised when plugin violates security constraints.

    This includes:
    - Attempting to access restricted modules
    - File system access violations
    - Network access violations
    - Resource limit violations
    """

    pass


class PluginDependencyError(PluginError):
    """Raised when plugin dependencies cannot be satisfied.

    This includes:
    - Missing Python packages
    - Version conflicts
    - Circular dependencies
    """

    pass


class DuplicatePluginError(PluginError):
    """Raised when attempting to register a duplicate plugin.

    This occurs when:
    - Plugin with same name already registered
    - Conflicting entry points
    """

    pass


class PermissionDeniedError(PluginSecurityError):
    """Raised when plugin attempts operation without permission.

    This occurs when:
    - Plugin accesses file system without file:read/write permission
    - Plugin makes network request without network:request permission
    - Plugin executes subprocess without subprocess:execute permission
    - Plugin registers hook without hook:register permission
    """

    pass


class PluginTimeoutError(PluginError):
    """Raised when plugin operation exceeds timeout.

    This occurs when:
    - Plugin initialization takes too long
    - Hook execution exceeds timeout
    - Workflow/agent execution exceeds timeout
    """

    pass


class ResourceLimitError(PluginSecurityError):
    """Raised when plugin exceeds resource limits.

    This occurs when:
    - Memory usage exceeds configured limit
    - CPU usage sustained above configured limit
    - File size exceeds configured limit
    """

    pass

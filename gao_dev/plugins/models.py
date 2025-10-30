"""Plugin models and data structures."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, List
import re


class PluginType(Enum):
    """Types of plugins supported by GAO-Dev."""

    AGENT = "agent"
    WORKFLOW = "workflow"
    METHODOLOGY = "methodology"
    TOOL = "tool"


class PluginPermission(Enum):
    """Permissions that plugins can request.

    Plugins must declare required permissions in plugin.yaml. The permission
    system enforces access control at runtime.

    Example plugin.yaml:
        permissions:
          - file:read
          - file:write
          - hook:register
    """

    FILE_READ = "file:read"
    FILE_WRITE = "file:write"
    FILE_DELETE = "file:delete"
    NETWORK_REQUEST = "network:request"
    SUBPROCESS_EXECUTE = "subprocess:execute"
    HOOK_REGISTER = "hook:register"
    CONFIG_READ = "config:read"
    CONFIG_WRITE = "config:write"
    DATABASE_READ = "database:read"
    DATABASE_WRITE = "database:write"


@dataclass
class ValidationResult:
    """Result of plugin validation.

    Attributes:
        valid: Whether plugin passed validation
        errors: List of error messages (validation failures)
        warnings: List of warning messages (suspicious but not fatal)
    """

    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ResourceUsage:
    """Resource usage metrics for a plugin.

    Attributes:
        cpu_percent: CPU usage as percentage (0-100)
        memory_mb: Memory usage in megabytes
        start_time: Timestamp when monitoring started
    """

    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    start_time: float = 0.0


@dataclass
class PluginMetadata:
    """Metadata describing a plugin.

    Attributes:
        name: Unique plugin identifier (e.g., 'my-custom-agent')
        version: Semantic version (e.g., '1.0.0')
        type: Type of plugin (agent, workflow, methodology, tool)
        entry_point: Module path to plugin class (e.g., 'my_plugin.agent.MyAgent')
        plugin_path: Absolute path to plugin directory
        description: Optional description of plugin functionality
        author: Optional plugin author name
        dependencies: Optional list of Python package dependencies
        enabled: Whether plugin is enabled (default: True)
        permissions: List of requested permissions (default: empty)
        timeout_seconds: Plugin initialization timeout in seconds (default: 30)
    """

    name: str
    version: str
    type: PluginType
    entry_point: str
    plugin_path: Path
    description: Optional[str] = None
    author: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    enabled: bool = True
    permissions: List[str] = field(default_factory=list)
    timeout_seconds: int = 30

    def __post_init__(self):
        """Validate metadata after initialization."""
        from .exceptions import PluginValidationError

        # Validate required fields
        if not self.name:
            raise PluginValidationError("Plugin name is required")

        if not self.name.replace('-', '').replace('_', '').isalnum():
            raise PluginValidationError(
                f"Invalid plugin name '{self.name}'. "
                "Name must contain only alphanumeric characters, hyphens, and underscores"
            )

        if not self.version:
            raise PluginValidationError("Plugin version is required")

        if not self.entry_point:
            raise PluginValidationError("Plugin entry_point is required")

        # Validate semantic version
        if not self._is_valid_semver(self.version):
            raise PluginValidationError(
                f"Invalid version '{self.version}'. "
                "Must follow semantic versioning (e.g., 1.0.0)"
            )

        # Validate entry point format
        if not self._is_valid_entry_point(self.entry_point):
            raise PluginValidationError(
                f"Invalid entry_point '{self.entry_point}'. "
                "Must be in format 'module.submodule.ClassName'"
            )

        # Ensure plugin_path is Path object
        if not isinstance(self.plugin_path, Path):
            self.plugin_path = Path(self.plugin_path)

        # Convert type string to enum if needed
        if isinstance(self.type, str):
            try:
                self.type = PluginType(self.type.lower())
            except ValueError:
                valid_types = [t.value for t in PluginType]
                raise PluginValidationError(
                    f"Invalid plugin type '{self.type}'. "
                    f"Must be one of: {valid_types}"
                )

    @staticmethod
    def _is_valid_semver(version: str) -> bool:
        """Check if version follows semantic versioning.

        Args:
            version: Version string to validate

        Returns:
            True if valid semantic version, False otherwise

        Examples:
            >>> PluginMetadata._is_valid_semver("1.0.0")
            True
            >>> PluginMetadata._is_valid_semver("1.0.0-alpha")
            True
            >>> PluginMetadata._is_valid_semver("1.0")
            False
        """
        pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$'
        return bool(re.match(pattern, version))

    @staticmethod
    def _is_valid_entry_point(entry_point: str) -> bool:
        """Check if entry point follows Python module format.

        Args:
            entry_point: Entry point string to validate

        Returns:
            True if valid entry point, False otherwise

        Examples:
            >>> PluginMetadata._is_valid_entry_point("my_plugin.agent.MyAgent")
            True
            >>> PluginMetadata._is_valid_entry_point("my_plugin")
            False
        """
        # Must have at least module.ClassName
        parts = entry_point.split('.')
        if len(parts) < 2:
            return False

        # Each part must be valid Python identifier
        for part in parts:
            if not part.isidentifier():
                return False

        return True

    def get_module_path(self) -> str:
        """Get module path without class name.

        Returns:
            Module path (e.g., 'my_plugin.agent' from 'my_plugin.agent.MyAgent')
        """
        parts = self.entry_point.rsplit('.', 1)
        return parts[0] if len(parts) > 1 else ''

    def get_class_name(self) -> str:
        """Get class name from entry point.

        Returns:
            Class name (e.g., 'MyAgent' from 'my_plugin.agent.MyAgent')
        """
        parts = self.entry_point.rsplit('.', 1)
        return parts[1] if len(parts) > 1 else self.entry_point

    def __repr__(self) -> str:
        """String representation of plugin metadata."""
        return (
            f"PluginMetadata(name='{self.name}', version='{self.version}', "
            f"type={self.type.value}, enabled={self.enabled})"
        )


@dataclass
class AgentMetadata:
    """Metadata for an agent plugin.

    Describes the capabilities and configuration of a custom agent
    provided by a plugin.

    Attributes:
        name: Unique agent name
        role: Agent role/specialty
        description: Agent description
        capabilities: List of agent capabilities
        tools: List of available tools
        model: Claude model to use (default: claude-sonnet-4-5-20250929)

    Example:
        ```python
        metadata = AgentMetadata(
            name="DomainExpert",
            role="Domain Expert",
            description="Expert in specific domain knowledge",
            capabilities=["analysis", "consultation"],
            tools=["Read", "Grep", "WebFetch"],
            model="claude-sonnet-4-5-20250929"
        )
        ```
    """
    name: str
    role: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    model: str = "claude-sonnet-4-5-20250929"

    def __post_init__(self):
        """Validate agent metadata after initialization."""
        if not self.name:
            raise ValueError("Agent name is required")
        if not self.role:
            raise ValueError("Agent role is required")
        if not self.description:
            raise ValueError("Agent description is required")


@dataclass
class WorkflowMetadata:
    """Metadata for a workflow plugin.

    Describes the capabilities and configuration of a custom workflow
    provided by a plugin.

    Attributes:
        name: Unique workflow name
        description: Workflow description
        phase: BMAD phase (1-4, or -1 for phase-independent)
        tags: List of workflow tags
        required_tools: List of required tools

    Example:
        ```python
        from gao_dev.core.models.workflow import WorkflowIdentifier

        metadata = WorkflowMetadata(
            name="domain-analysis",
            description="Analyze domain-specific requirements",
            phase=1,
            tags=["analysis", "domain"],
            required_tools=["Read", "Grep", "WebFetch"]
        )
        ```
    """
    name: str
    description: str
    phase: int = -1  # -1 means phase-independent
    tags: List[str] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate workflow metadata after initialization."""
        if not self.name:
            raise ValueError("Workflow name is required")
        if not self.description:
            raise ValueError("Workflow description is required")
        if self.phase < -1 or self.phase > 4:
            raise ValueError(f"Phase must be -1 to 4, got {self.phase}")

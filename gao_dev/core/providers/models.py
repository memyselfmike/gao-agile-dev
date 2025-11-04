"""Provider models and data structures.

This module defines data models used by the provider abstraction system,
primarily the AgentContext dataclass which encapsulates execution context
information passed to providers.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass
class AgentContext:
    """
    Context information for agent task execution.

    Provides environment and metadata needed by providers to execute
    tasks correctly. This context is passed to all provider execute_task()
    calls and encapsulates:

    - Project structure information (root, working directory)
    - Execution metadata (user ID, session ID, etc.)
    - Environment variables for subprocess execution
    - Execution hints (permissions, network access)

    The context is provider-agnostic - providers interpret fields as needed
    for their specific execution model.

    Example:
        ```python
        # Minimal context
        context = AgentContext(
            project_root=Path("/path/to/project")
        )

        # Full context with metadata
        context = AgentContext(
            project_root=Path("/path/to/project"),
            working_directory=Path("/path/to/project/src"),
            metadata={
                "user_id": "user123",
                "session_id": "sess456",
                "epic": "11",
                "story": "11.1"
            },
            environment_vars={
                "CUSTOM_VAR": "value"
            },
            allow_destructive_operations=False,
            enable_network=True
        )

        # Use with provider
        async for message in provider.execute_task(
            task="Implement feature",
            context=context,
            model="sonnet-4.5",
            tools=["Read", "Write"]
        ):
            print(message)
        ```
    """

    # Required fields
    project_root: Path
    """
    Project root directory (absolute path).

    This is the base directory for the project being worked on.
    Providers use this to:
    - Set current working directory
    - Resolve relative file paths
    - Scope file operations
    - Configure sandboxing

    Must be an absolute path. Automatically resolved in __post_init__.
    """

    # Optional fields
    metadata: Dict[str, str] = field(default_factory=dict)
    """
    Additional metadata (user ID, session ID, epic/story info, etc.).

    Use cases:
    - Tracking which user/session initiated the task
    - Associating task with epic/story for metrics
    - Passing custom provider-specific metadata
    - Audit logging and compliance

    Example:
        {
            "user_id": "user123",
            "session_id": "sess456",
            "epic": "11",
            "story": "11.1",
            "benchmark_id": "bench789"
        }
    """

    working_directory: Optional[Path] = None
    """
    Current working directory (defaults to project_root).

    If specified, providers should execute tasks from this directory.
    Useful for:
    - Working in subdirectories (e.g., monorepo packages)
    - Scoping operations to specific modules
    - Matching developer workflow

    Automatically set to project_root in __post_init__ if None.
    Must be absolute path (resolved in __post_init__).
    """

    environment_vars: Dict[str, str] = field(default_factory=dict)
    """
    Additional environment variables for subprocess execution.

    Merged with system environment variables when spawning subprocesses.
    Use for:
    - Setting provider-specific environment variables
    - Overriding system defaults
    - Passing secrets (use carefully - prefer secure methods)

    Example:
        {
            "NODE_ENV": "production",
            "CUSTOM_CONFIG": "/path/to/config"
        }

    Note: API key environment variables (ANTHROPIC_API_KEY, OPENAI_API_KEY)
    should be handled by providers, not set here (security best practice).
    """

    # Execution hints
    allow_destructive_operations: bool = True
    """
    Whether to allow file deletion, git reset, destructive operations.

    If False, providers should:
    - Prevent file deletion
    - Prevent git reset/rebase operations
    - Prevent database drops
    - Warn before destructive operations

    Use cases:
    - Sandbox environments (disallow destruction)
    - Production environments (extra safety)
    - Read-only analysis tasks

    Default: True (allow all operations)
    """

    enable_network: bool = True
    """
    Whether to allow network access.

    If False, providers should:
    - Block API calls (when possible)
    - Block package installation
    - Block git clone/fetch
    - Disable WebFetch/WebSearch tools

    Use cases:
    - Air-gapped environments
    - Security-sensitive operations
    - Offline development
    - Testing network resilience

    Default: True (allow network access)

    Note: Enforcement depends on provider capabilities. CLI providers
    may not be able to enforce network restrictions.
    """

    def __post_init__(self) -> None:
        """
        Validate and normalize context after initialization.

        Performs:
        - Sets working_directory to project_root if None
        - Resolves all paths to absolute paths
        - Validates that paths exist (logs warning if not)

        Raises:
            ValueError: If project_root is not a valid path
        """
        # Validate project_root
        if not isinstance(self.project_root, Path):
            raise ValueError(
                f"project_root must be a Path, got {type(self.project_root)}"
            )

        # Set default working_directory
        if self.working_directory is None:
            self.working_directory = self.project_root

        # Resolve to absolute paths
        self.project_root = self.project_root.resolve()
        self.working_directory = self.working_directory.resolve()

        # Validate paths exist (warning, not error - sandbox may not exist yet)
        if not self.project_root.exists():
            import structlog
            logger = structlog.get_logger()
            logger.warning(
                "project_root_does_not_exist",
                project_root=str(self.project_root),
                message="Project root directory does not exist. "
                        "This may be expected for new projects."
            )

        if not self.working_directory.exists():
            import structlog
            logger = structlog.get_logger()
            logger.warning(
                "working_directory_does_not_exist",
                working_directory=str(self.working_directory),
                message="Working directory does not exist. "
                        "Using project_root instead."
            )
            self.working_directory = self.project_root

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"AgentContext("
            f"project_root={self.project_root}, "
            f"working_directory={self.working_directory}, "
            f"metadata={self.metadata}, "
            f"allow_destructive={self.allow_destructive_operations}, "
            f"enable_network={self.enable_network})"
        )

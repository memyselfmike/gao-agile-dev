"""ProcessExecutor Service - Executes agent tasks via configured providers.

Refactored in Epic 11, Story 11.4 to use provider abstraction while maintaining
100% backward compatibility with existing code.

Responsibilities:
- Execute agent tasks via provider abstraction
- Stream output to caller
- Handle process timeouts
- Validate provider configuration
- Log execution details

Design Pattern: Strategy Pattern (provider abstraction)
"""

import structlog
from typing import AsyncGenerator, Optional, List, Dict
from pathlib import Path

logger = structlog.get_logger()


class ProcessExecutionError(Exception):
    """Raised when a process execution fails."""
    pass


class ProcessExecutor:
    """
    Executes agent tasks via configurable provider.

    Refactored to use provider abstraction while maintaining
    100% backward compatibility with existing code.

    New API (Recommended):
        ```python
        # Option 1: Provider instance injection
        provider = ClaudeCodeProvider()
        executor = ProcessExecutor(project_root, provider=provider)

        # Option 2: Provider name with config
        executor = ProcessExecutor(
            project_root,
            provider_name="claude-code",
            provider_config={"api_key": "sk-..."}
        )

        # Option 3: Provider name only (uses defaults)
        executor = ProcessExecutor(project_root, provider_name="claude-code")
        ```

    Legacy API (Still Supported):
        ```python
        # Old constructor still works exactly as before
        executor = ProcessExecutor(
            project_root=Path("/project"),
            cli_path=Path("/usr/bin/claude"),
            api_key="sk-ant-..."
        )
        ```
    """

    DEFAULT_TIMEOUT = 3600  # 1 hour

    def __init__(
        self,
        project_root: Path,
        provider: Optional["IAgentProvider"] = None,
        provider_name: str = "claude-code",
        provider_config: Optional[Dict] = None,
        # Legacy parameters (deprecated but supported)
        cli_path: Optional[Path] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize executor with provider.

        Args:
            project_root: Project root directory
            provider: Pre-configured provider instance (takes precedence)
            provider_name: Provider name if creating new instance
            provider_config: Provider-specific configuration
            cli_path: DEPRECATED - Use provider_config instead
            api_key: DEPRECATED - Use provider_config instead

        Example (New API):
            ```python
            executor = ProcessExecutor(
                project_root=Path("/project"),
                provider_name="claude-code",
                provider_config={"api_key": "sk-..."}
            )
            ```

        Example (Legacy API - still works):
            ```python
            executor = ProcessExecutor(
                project_root=Path("/project"),
                cli_path=Path("/usr/bin/claude"),
                api_key="sk-ant-..."
            )
            ```
        """
        self.project_root = project_root

        # Store legacy attributes for backward compatibility with existing tests
        self.cli_path = cli_path
        self.api_key = api_key

        # Import here to avoid circular dependencies
        from ..providers import ProviderFactory, AgentContext
        import os

        # Handle legacy constructor (backward compatibility)
        if provider is None and (cli_path is not None or api_key is not None):
            # Legacy mode: create ClaudeCodeProvider with old params
            logger.info(
                "process_executor_legacy_mode",
                message="Using legacy constructor. Consider migrating to provider-based API.",
                migration_guide="See docs/MIGRATION_PROVIDER.md"
            )

            # Fill in api_key from environment if not provided (maintain old behavior)
            effective_api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            self.api_key = effective_api_key

            factory = ProviderFactory()
            legacy_config = {}
            if cli_path is not None:
                legacy_config["cli_path"] = cli_path
            if effective_api_key is not None:
                legacy_config["api_key"] = effective_api_key

            self.provider = factory.create_provider("claude-code", config=legacy_config)

        # Use provided provider instance
        elif provider is not None:
            self.provider = provider
            logger.info(
                "process_executor_provider_injected",
                provider=provider.name,
                provider_version=provider.version
            )

        # Create provider from factory
        else:
            factory = ProviderFactory()
            self.provider = factory.create_provider(provider_name, config=provider_config)
            logger.info(
                "process_executor_provider_created",
                provider_name=provider_name,
                has_config=provider_config is not None
            )

        logger.info(
            "process_executor_initialized",
            project_root=str(project_root),
            provider=self.provider.name,
            provider_version=self.provider.version
        )

    async def execute_agent_task(
        self,
        task: str,
        model: str = "sonnet-4.5",
        tools: Optional[List[str]] = None,
        timeout: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        Execute agent task via configured provider.

        Args:
            task: Task description/prompt
            model: Canonical model name (provider translates)
            tools: List of tool names to enable
            timeout: Optional timeout in seconds

        Yields:
            Progress messages and results

        Raises:
            ValueError: If provider not properly configured
            ProviderExecutionError: If execution fails
            ProviderTimeoutError: If execution times out
        """
        # Import here to avoid circular dependencies
        from ..providers import AgentContext

        # Validate provider configuration
        is_valid = await self.provider.validate_configuration()
        if not is_valid:
            logger.error(
                "provider_not_configured",
                provider=self.provider.name
            )
            raise ValueError(
                f"Provider '{self.provider.name}' not properly configured. "
                f"Check API keys and CLI installation. "
                f"See: gao-dev providers validate"
            )

        # Create execution context
        context = AgentContext(project_root=self.project_root)

        # Delegate to provider
        logger.info(
            "executing_task_via_provider",
            provider=self.provider.name,
            model=model,
            tools=tools,
            timeout=timeout or self.DEFAULT_TIMEOUT
        )

        try:
            async for message in self.provider.execute_task(
                task=task,
                context=context,
                model=model,
                tools=tools or [],
                timeout=timeout or self.DEFAULT_TIMEOUT
            ):
                yield message

            logger.info(
                "task_execution_completed",
                provider=self.provider.name
            )

        except Exception as e:
            logger.error(
                "task_execution_failed",
                provider=self.provider.name,
                error=str(e),
                exc_info=True
            )
            raise

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ProcessExecutor("
            f"project_root={self.project_root}, "
            f"provider={self.provider.name})"
        )

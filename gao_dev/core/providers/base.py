"""Provider interface for agent execution backends.

This module defines the IAgentProvider abstract interface that all
providers (built-in and plugin) must implement to be compatible with
GAO-Dev's execution system.

Design Pattern: Strategy Pattern
- Context: ProcessExecutor
- Strategy: IAgentProvider
- Concrete Strategies: ClaudeCodeProvider, OpenCodeProvider, DirectAPIProvider
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Dict, Optional


class IAgentProvider(ABC):
    """
    Abstract interface for agent execution providers.

    All providers (built-in and plugin) must implement this interface
    to be compatible with GAO-Dev's execution system.

    This interface abstracts the execution backend, enabling GAO-Dev to
    support multiple AI providers (Claude Code CLI, OpenCode CLI, direct
    APIs, custom providers) without changing high-level orchestration code.

    Example:
        ```python
        class CustomProvider(IAgentProvider):
            @property
            def name(self) -> str:
                return "custom-provider"

            @property
            def version(self) -> str:
                return "1.0.0"

            async def execute_task(self, task, context, model, tools, timeout):
                # Implementation
                yield "Processing..."
                yield "Complete!"

            def supports_tool(self, tool_name: str) -> bool:
                return tool_name in ["Read", "Write", "Bash"]

            def get_supported_models(self) -> List[str]:
                return ["sonnet-4.5", "opus-3"]

            def translate_model_name(self, canonical_name: str) -> str:
                # Map canonical names to provider-specific IDs
                return canonical_name

            async def validate_configuration(self) -> bool:
                # Check if provider is properly configured
                return True

            def get_configuration_schema(self) -> Dict:
                return {"type": "object", "properties": {}}

            async def initialize(self) -> None:
                # Initialize resources
                pass

            async def cleanup(self) -> None:
                # Cleanup resources
                pass
        ```
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique provider identifier.

        This name is used for:
        - Provider registration and lookup
        - Configuration file references
        - Logging and metrics
        - User-facing provider selection

        Returns:
            Provider name (lowercase, hyphen-separated)

        Example:
            'claude-code', 'opencode', 'direct-api', 'custom-ollama'
        """
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """
        Provider version for compatibility tracking.

        Used for:
        - Compatibility verification
        - Debugging and support
        - Migration planning
        - Feature availability checks

        Returns:
            Semantic version string (e.g., '1.0.0')

        Example:
            '1.0.0', '2.3.1', '0.1.0-beta'
        """
        pass

    @abstractmethod
    async def execute_task(
        self,
        task: str,
        context: "AgentContext",
        model: str,
        tools: List[str],
        timeout: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Execute an agent task using this provider.

        This is the core method that delegates task execution to the
        underlying provider (CLI subprocess, API call, etc.).

        The method uses an async generator pattern to stream results,
        enabling real-time progress updates and cancellation support.

        Args:
            task: Task description/prompt for the AI agent
            context: Execution context (project root, metadata, etc.)
            model: Canonical model name (provider translates to specific ID)
            tools: List of tool names to enable (e.g., ['Read', 'Write', 'Bash'])
            timeout: Optional timeout in seconds (None = use provider default)
            **kwargs: Provider-specific additional arguments

        Yields:
            Progress messages and results from provider execution.
            Providers should yield incrementally to enable streaming UX.

        Raises:
            ProviderExecutionError: If execution fails
            ProviderTimeoutError: If execution exceeds timeout
            ProviderConfigurationError: If provider not properly configured
            AuthenticationError: If API key invalid/missing
            RateLimitError: If rate limit exceeded
            ModelNotFoundError: If model not supported

        Example:
            ```python
            # Simple execution
            async for message in provider.execute_task(
                task="Implement feature X",
                context=AgentContext(project_root=Path("/project")),
                model="sonnet-4.5",
                tools=["Read", "Write", "Edit"],
                timeout=3600
            ):
                print(message)

            # With error handling
            try:
                async for message in provider.execute_task(...):
                    print(message)
            except AuthenticationError as e:
                print(f"Authentication failed: {e.message}")
            except RateLimitError as e:
                print(f"Rate limited. Retry after {e.retry_after} seconds")
            except ProviderTimeoutError as e:
                print(f"Execution timed out: {e.message}")
            ```
        """
        pass

    @abstractmethod
    def supports_tool(self, tool_name: str) -> bool:
        """
        Check if provider supports a specific tool.

        Different providers may support different tool sets. This method
        enables runtime validation and graceful degradation.

        Providers should be permissive: if a tool is "close enough" to
        a supported tool, return True and handle translation internally.

        Args:
            tool_name: Tool name (e.g., 'Read', 'Write', 'Bash')

        Returns:
            True if tool is supported, False otherwise

        Example:
            ```python
            # Check before using tool
            if provider.supports_tool("Bash"):
                # Use Bash tool
                tools = ["Read", "Write", "Bash"]
            else:
                # Fallback: use alternative or skip
                tools = ["Read", "Write"]
                logger.warning("Provider doesn't support Bash, using workaround")

            # Provider implementation
            def supports_tool(self, tool_name: str) -> bool:
                SUPPORTED_TOOLS = {
                    "Read", "Write", "Edit", "MultiEdit",
                    "Bash", "Grep", "Glob", "Task"
                }
                return tool_name in SUPPORTED_TOOLS
            ```
        """
        pass

    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """
        Get list of canonical model names supported by this provider.

        Returns canonical names, not provider-specific IDs. This enables
        model discovery and validation without provider-specific knowledge.

        Returns:
            List of canonical model names (sorted by capability/recency)

        Example:
            ```python
            # Provider returns canonical names
            models = provider.get_supported_models()
            # ['sonnet-4.5', 'sonnet-3.5', 'opus-3', 'haiku-3']

            # Use for validation
            if model_name in provider.get_supported_models():
                # Model supported
                pass
            else:
                # Model not supported, show alternatives
                print(f"Supported models: {', '.join(models)}")

            # Provider implementation
            def get_supported_models(self) -> List[str]:
                return [
                    "sonnet-4.5",   # Latest and greatest
                    "sonnet-3.5",   # Stable
                    "opus-3",       # Most capable
                    "haiku-3"       # Fastest
                ]
            ```
        """
        pass

    @abstractmethod
    def translate_model_name(self, canonical_name: str) -> str:
        """
        Translate canonical model name to provider-specific identifier.

        GAO-Dev uses canonical names (e.g., 'sonnet-4.5') that are
        provider-agnostic. Each provider translates to its specific format.

        This abstraction enables:
        - Switching providers without changing model references
        - Cross-provider benchmarking with "equivalent" models
        - User-friendly model names

        Args:
            canonical_name: Canonical model name (e.g., 'sonnet-4.5')

        Returns:
            Provider-specific model identifier

        Raises:
            ModelNotFoundError: If model not supported by provider

        Examples:
            ```python
            # ClaudeCodeProvider
            translate_model_name("sonnet-4.5")
            # -> "claude-sonnet-4-5-20250929"

            # OpenCodeProvider
            translate_model_name("sonnet-4.5")
            # -> "anthropic/claude-sonnet-4.5"

            translate_model_name("gpt-4")
            # -> "openai/gpt-4-turbo-preview"

            # DirectAPIProvider
            translate_model_name("sonnet-4.5")
            # -> "claude-sonnet-4-5-20250929"

            # Provider implementation
            def translate_model_name(self, canonical_name: str) -> str:
                MODEL_MAPPING = {
                    "sonnet-4.5": "claude-sonnet-4-5-20250929",
                    "sonnet-3.5": "claude-sonnet-3-5-20241022",
                    "opus-3": "claude-opus-3-20250219",
                }

                if canonical_name in MODEL_MAPPING:
                    return MODEL_MAPPING[canonical_name]

                # Check if already provider-specific (passthrough)
                if canonical_name.startswith("claude-"):
                    return canonical_name

                # Not found
                raise ModelNotFoundError(
                    provider_name=self.name,
                    model_name=canonical_name
                )
            ```
        """
        pass

    @abstractmethod
    async def validate_configuration(self) -> bool:
        """
        Validate that provider is properly configured and ready to use.

        This method performs pre-flight checks to ensure the provider
        can execute tasks successfully. It should check:

        For CLI providers:
        - CLI executable exists and is executable
        - CLI version is compatible (if applicable)
        - Required dependencies installed

        For API providers:
        - API keys are set (check environment variables)
        - Network connectivity (optional: ping API endpoint)
        - Base URL is valid (if configurable)

        For all providers:
        - Required configuration fields are set
        - Configuration values are valid

        Returns:
            True if configuration valid and ready, False otherwise

        Side Effects:
            May log warnings for configuration issues.
            Should NOT raise exceptions (return False instead).

        Example:
            ```python
            # Check before execution
            if not await provider.validate_configuration():
                logger.error("Provider not configured")
                # Fallback to alternative provider or show setup instructions
                print(f"Please configure {provider.name}:")
                print("  1. Install CLI: npm install -g @sst/opencode")
                print("  2. Set API key: export ANTHROPIC_API_KEY=...")
                return

            # Provider implementation
            async def validate_configuration(self) -> bool:
                # Check CLI exists
                if not self.cli_path or not self.cli_path.exists():
                    logger.warning(
                        "cli_not_found",
                        cli_path=str(self.cli_path)
                    )
                    return False

                # Check API key
                if not self.api_key:
                    logger.warning(
                        "api_key_not_set",
                        env_var=self.get_api_key_env_var()
                    )
                    return False

                # Optional: test CLI execution
                try:
                    result = subprocess.run(
                        [str(self.cli_path), "--version"],
                        capture_output=True,
                        timeout=5
                    )
                    if result.returncode != 0:
                        logger.warning("cli_test_failed")
                        return False
                except Exception as e:
                    logger.warning("cli_test_error", error=str(e))
                    return False

                return True
            ```
        """
        pass

    @abstractmethod
    def get_configuration_schema(self) -> Dict:
        """
        Get JSON Schema for provider-specific configuration.

        This schema is used for:
        - Configuration validation (before execution)
        - Documentation generation (auto-generate docs from schema)
        - IDE autocomplete (if IDE supports JSON Schema)
        - UI generation (for graphical configuration tools)

        Returns:
            JSON Schema dict describing configuration options

        Example:
            ```python
            # Simple schema
            {
                "type": "object",
                "properties": {
                    "cli_path": {
                        "type": "string",
                        "description": "Path to CLI executable"
                    },
                    "api_key": {
                        "type": "string",
                        "description": "API key for authentication"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Default timeout in seconds",
                        "default": 3600,
                        "minimum": 1
                    }
                },
                "required": ["api_key"]
            }

            # Advanced schema with validation
            {
                "type": "object",
                "properties": {
                    "base_url": {
                        "type": "string",
                        "format": "uri",
                        "pattern": "^https://",
                        "description": "API base URL (must be HTTPS)"
                    },
                    "model": {
                        "type": "string",
                        "enum": ["sonnet-4.5", "opus-3", "haiku-3"],
                        "description": "Default model"
                    },
                    "retry_config": {
                        "type": "object",
                        "properties": {
                            "max_retries": {"type": "integer", "default": 3},
                            "retry_delay": {"type": "number", "default": 1.0}
                        }
                    }
                },
                "required": ["base_url"]
            }

            # Provider implementation
            def get_configuration_schema(self) -> Dict:
                return {
                    "type": "object",
                    "properties": {
                        "cli_path": {
                            "type": "string",
                            "description": "Path to Claude CLI executable"
                        },
                        "api_key": {
                            "type": "string",
                            "description": "Anthropic API key"
                        }
                    },
                    "required": []  # Both optional (auto-detected)
                }
            ```
        """
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize provider resources (connections, subprocess, etc.).

        Called before first execution. Must be idempotent - can be called
        multiple times without side effects (should check if already initialized).

        Use cases:
        - Open persistent HTTP connections (connection pooling)
        - Start background processes
        - Load configuration files
        - Authenticate with API
        - Allocate resources

        Raises:
            ProviderInitializationError: If initialization fails

        Example:
            ```python
            # Minimal implementation
            async def initialize(self) -> None:
                if self._initialized:
                    return  # Already initialized

                logger.info("initializing_provider", provider=self.name)
                self._initialized = True

            # HTTP client initialization
            async def initialize(self) -> None:
                if self._initialized:
                    return

                try:
                    # Create persistent HTTP client
                    self.client = httpx.AsyncClient(
                        base_url=self.base_url,
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        timeout=httpx.Timeout(timeout=60.0),
                        limits=httpx.Limits(max_keepalive_connections=10)
                    )

                    # Test connection
                    response = await self.client.get("/health")
                    if response.status_code != 200:
                        raise ProviderInitializationError(
                            f"Health check failed: {response.status_code}",
                            provider_name=self.name
                        )

                    self._initialized = True
                    logger.info("provider_initialized", provider=self.name)

                except Exception as e:
                    logger.error("provider_initialization_failed", error=str(e))
                    raise ProviderInitializationError(
                        f"Failed to initialize provider: {e}",
                        provider_name=self.name,
                        original_error=e
                    )
            ```
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """
        Clean up provider resources (close connections, kill processes, etc.).

        Called after last execution or on error. Should be safe to call
        even if initialization failed (check state before cleanup).

        Use cases:
        - Close HTTP connections
        - Kill background processes
        - Release file handles
        - Clear caches
        - Deallocate resources

        This method should NOT raise exceptions - log errors instead.

        Example:
            ```python
            # Minimal implementation
            async def cleanup(self) -> None:
                self._initialized = False
                logger.info("provider_cleaned_up", provider=self.name)

            # HTTP client cleanup
            async def cleanup(self) -> None:
                if not self._initialized:
                    return  # Nothing to clean up

                try:
                    # Close HTTP client
                    if hasattr(self, 'client') and self.client:
                        await self.client.aclose()
                        self.client = None

                    self._initialized = False
                    logger.info("provider_cleaned_up", provider=self.name)

                except Exception as e:
                    # Log but don't raise
                    logger.error(
                        "provider_cleanup_error",
                        provider=self.name,
                        error=str(e)
                    )

            # Process cleanup
            async def cleanup(self) -> None:
                try:
                    # Kill any running subprocesses
                    if hasattr(self, '_process') and self._process:
                        self._process.kill()
                        await asyncio.sleep(0.1)  # Give it time to die
                        if self._process.poll() is None:
                            self._process.terminate()

                    # Clear subprocess reference
                    self._process = None
                    self._initialized = False

                except Exception as e:
                    logger.error("cleanup_error", error=str(e))
            ```
        """
        pass

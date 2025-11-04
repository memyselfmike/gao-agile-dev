"""OpenCode CLI provider implementation.

This provider enables GAO-Dev to use OpenCode as an execution backend,
providing multi-provider AI support (Anthropic, OpenAI, Google, and 75+ more)
through OpenCode's Models.dev integration.

Key Differences from Claude Code:
- OpenCode is a TUI-first application (not a simple CLI tool)
- Uses 'opencode run' command for non-interactive execution
- Supports multiple AI providers (not just Anthropic)
- Model format: provider/model (e.g., 'anthropic/claude-sonnet-4.5')

Implementation Notes:
- Based on OpenCode research (Story 11.6)
- Uses subprocess execution with 'opencode run' command
- Multi-provider support through ai_provider parameter
- Model name translation for each provider
- Tool support limited compared to Claude Code (see tool mapping docs)

Extracted for: Epic 11 - Agent Provider Abstraction
Story: 11.7 - Implement OpenCodeProvider
"""

from pathlib import Path
from typing import AsyncGenerator, List, Dict, Optional
import subprocess
import os
import structlog

from .base import IAgentProvider
from .models import AgentContext
from .exceptions import (
    ProviderExecutionError,
    ProviderTimeoutError,
    ProviderConfigurationError,
    ModelNotSupportedError
)

logger = structlog.get_logger()


class OpenCodeProvider(IAgentProvider):
    """
    Provider for OpenCode CLI execution with multi-AI-provider support.

    OpenCode is an open-source AI coding agent that supports multiple
    AI providers (Anthropic, OpenAI, Google, and 75+ more) through
    Models.dev integration.

    Execution Model: Subprocess (OpenCode CLI 'run' command)
    Backend: Multiple (Anthropic, OpenAI, Google, local)

    Example:
        ```python
        # Use with Anthropic
        provider = OpenCodeProvider(ai_provider="anthropic")

        async for result in provider.execute_task(
            task="Write a hello world script",
            context=AgentContext(project_root=Path("/project")),
            model="sonnet-4.5",
            tools=["Read", "Write", "Bash"],
            timeout=3600
        ):
            print(result)

        # Use with OpenAI
        provider = OpenCodeProvider(ai_provider="openai")

        async for result in provider.execute_task(
            task="Add tests to the API",
            context=AgentContext(project_root=Path("/project")),
            model="gpt-4",
            tools=["Read", "Write"],
            timeout=3600
        ):
            print(result)
        ```

    Tool Support:
        - Excellent: Read, Write, Edit, Bash, Glob (90-100% compatible)
        - Partial: MultiEdit, Grep (60-70% compatible)
        - Limited: Task, WebFetch, WebSearch, TodoWrite (not supported)

    See also:
        - OpenCode Research: docs/opencode-research.md
        - Setup Guide: docs/opencode-setup-guide.md
        - CLI Reference: docs/opencode-cli-reference.md
        - Tool Mapping: docs/opencode-tool-mapping.md
    """

    # Tool mapping: GAO-Dev tool name → OpenCode capability
    # Based on OpenCode research (Story 11.6)
    TOOL_MAPPING = {
        # Core file operations (excellent support)
        "Read": True,
        "Write": True,
        "Edit": True,
        "Bash": True,
        "Glob": True,

        # Partial support
        "MultiEdit": True,  # Sequential, not atomic
        "Grep": True,       # LSP-based, not regex

        # Not supported
        "Task": False,
        "WebFetch": False,
        "WebSearch": False,
        "TodoWrite": False,
        "AskUserQuestion": False,  # Non-interactive mode
        "NotebookEdit": False,
        "Skill": False,
        "SlashCommand": False,
    }

    # Model translation per AI provider
    # Canonical → OpenCode format (provider/model)
    MODEL_MAPPING = {
        "anthropic": {
            # Canonical names
            "sonnet-4.5": "anthropic/claude-sonnet-4.5",
            "sonnet-3.5": "anthropic/claude-sonnet-3.5",
            "opus-3": "anthropic/claude-opus-3",
            "haiku-3": "anthropic/claude-haiku-3",
            "opus-4.1": "anthropic/claude-opus-4.1",
            "sonnet-4": "anthropic/claude-sonnet-4",

            # Passthrough for OpenCode format
            "anthropic/claude-sonnet-4.5": "anthropic/claude-sonnet-4.5",
            "anthropic/claude-opus-4.1": "anthropic/claude-opus-4.1",
            "anthropic/claude-sonnet-4": "anthropic/claude-sonnet-4",
            "anthropic/claude-sonnet-3.5": "anthropic/claude-sonnet-3.5",
            "anthropic/claude-opus-3": "anthropic/claude-opus-3",
            "anthropic/claude-haiku-3": "anthropic/claude-haiku-3",
        },
        "openai": {
            # Canonical names
            "gpt-5": "openai/gpt-5",
            "gpt-5-codex": "openai/gpt-5-codex",
            "gpt-4": "openai/gpt-4",
            "gpt-4-turbo": "openai/gpt-4-turbo",
            "gpt-3.5-turbo": "openai/gpt-3.5-turbo",

            # Passthrough for OpenCode format
            "openai/gpt-5": "openai/gpt-5",
            "openai/gpt-5-codex": "openai/gpt-5-codex",
            "openai/gpt-4": "openai/gpt-4",
            "openai/gpt-4-turbo": "openai/gpt-4-turbo",
            "openai/gpt-3.5-turbo": "openai/gpt-3.5-turbo",
        },
        "google": {
            # Canonical names
            "gemini-2.5-pro": "google/gemini-2.5-pro",
            "gemini-pro": "google/gemini-pro",
            "gemini-flash": "google/gemini-flash",

            # Passthrough for OpenCode format
            "google/gemini-2.5-pro": "google/gemini-2.5-pro",
            "google/gemini-pro": "google/gemini-pro",
            "google/gemini-flash": "google/gemini-flash",
        }
    }

    # API key environment variables per provider
    API_KEY_ENV_VARS = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "google": "GOOGLE_API_KEY",
    }

    DEFAULT_TIMEOUT = 3600  # 1 hour

    def __init__(
        self,
        cli_path: Optional[Path] = None,
        ai_provider: str = "anthropic",
        api_key: Optional[str] = None
    ):
        """
        Initialize OpenCode provider.

        Args:
            cli_path: Path to OpenCode CLI (auto-detected if None)
            ai_provider: AI provider to use (anthropic, openai, google)
            api_key: API key (uses env var if None)

        Example:
            ```python
            # With Anthropic (default)
            provider = OpenCodeProvider()

            # With OpenAI
            provider = OpenCodeProvider(ai_provider="openai")

            # With custom CLI path
            provider = OpenCodeProvider(
                cli_path=Path("/usr/local/bin/opencode"),
                ai_provider="anthropic"
            )
            ```
        """
        self.cli_path = cli_path or self._detect_opencode_cli()
        self.ai_provider = ai_provider.lower()

        # Get API key from parameter or environment
        if api_key:
            self.api_key = api_key
        else:
            env_var = self.API_KEY_ENV_VARS.get(self.ai_provider)
            self.api_key = os.getenv(env_var) if env_var else None

        self._initialized = False

        logger.info(
            "opencode_provider_initialized",
            has_cli_path=self.cli_path is not None,
            ai_provider=self.ai_provider,
            has_api_key=bool(self.api_key),
            cli_path=str(self.cli_path) if self.cli_path else None
        )

    @property
    def name(self) -> str:
        """Provider name."""
        return "opencode"

    @property
    def version(self) -> str:
        """Provider version."""
        return "1.0.0"

    async def execute_task(
        self,
        task: str,
        context: AgentContext,
        model: str,
        tools: List[str],
        timeout: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Execute task via OpenCode CLI.

        Uses 'opencode run' command for non-interactive execution.
        Results are streamed from stdout.

        Args:
            task: Task description/prompt
            context: Execution context
            model: Canonical model name (e.g., 'sonnet-4.5', 'gpt-4')
            tools: List of tool names (validated but not passed to CLI)
            timeout: Timeout in seconds
            **kwargs: Additional arguments (ignored)

        Yields:
            Output from OpenCode CLI

        Raises:
            ProviderExecutionError: If execution fails
            ProviderTimeoutError: If execution times out
            ProviderConfigurationError: If not configured
            ModelNotSupportedError: If model not supported for provider

        Example:
            ```python
            async for result in provider.execute_task(
                task="Create hello.py with hello world function",
                context=AgentContext(project_root=Path("/project")),
                model="sonnet-4.5",
                tools=["Read", "Write"],
                timeout=60
            ):
                print(result)
            ```
        """
        if not self.cli_path:
            raise ProviderConfigurationError(
                "OpenCode CLI not found. Install OpenCode or set cli_path. "
                "See: docs/opencode-setup-guide.md",
                provider_name=self.name
            )

        # Translate model name (raises ModelNotSupportedError if invalid)
        model_id = self.translate_model_name(model)

        # Build command
        # Format: opencode run --model PROVIDER/MODEL "TASK"
        cmd = [str(self.cli_path)]
        cmd.extend(['run'])
        cmd.extend(['--model', model_id])
        # Note: OpenCode 'run' uses current directory as project root
        # We set cwd to context.project_root below

        # Set environment
        env = os.environ.copy()
        if self.api_key:
            env_var = self.API_KEY_ENV_VARS.get(self.ai_provider)
            if env_var:
                env[env_var] = self.api_key

        # Log execution
        logger.info(
            "executing_opencode_cli",
            ai_provider=self.ai_provider,
            model=model_id,
            tools=tools,
            timeout=timeout or self.DEFAULT_TIMEOUT,
            project_root=str(context.project_root),
            has_api_key=bool(self.api_key)
        )

        try:
            # Execute subprocess
            # IMPORTANT: encoding='utf-8' is required for Windows compatibility
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',  # Windows compatibility
                env=env,
                cwd=str(context.project_root)  # Set working directory
            )

            # Communicate with timeout
            # Send task via stdin
            stdout, stderr = process.communicate(
                input=task,
                timeout=timeout or self.DEFAULT_TIMEOUT
            )

            # Log completion
            logger.info(
                "opencode_cli_completed",
                return_code=process.returncode,
                ai_provider=self.ai_provider,
                stdout_length=len(stdout) if stdout else 0,
                stderr_length=len(stderr) if stderr else 0,
                stdout_preview=stdout[:200] if stdout else "(empty)",
                stderr_preview=stderr[:200] if stderr else "(empty)"
            )

            # Log stderr if present
            if stderr:
                logger.warning("opencode_cli_stderr", stderr=stderr[:1000])

            # Yield output (even if return code isn't 0, similar to ClaudeCodeProvider)
            if stdout:
                yield stdout

            # Check exit code
            if process.returncode != 0:
                error_msg = (
                    f"OpenCode CLI failed with exit code {process.returncode} "
                    f"(provider: {self.ai_provider}, model: {model_id})"
                )
                if stderr:
                    error_msg += f": {stderr[:500]}"
                if not stdout and not stderr:
                    error_msg += " (no output - check if opencode is installed correctly)"

                logger.error(
                    "opencode_cli_execution_failed",
                    exit_code=process.returncode,
                    error=error_msg,
                    ai_provider=self.ai_provider,
                    model=model_id
                )
                raise ProviderExecutionError(error_msg, provider_name=self.name)

        except subprocess.TimeoutExpired:
            process.kill()
            logger.error(
                "opencode_cli_timeout",
                timeout=timeout or self.DEFAULT_TIMEOUT,
                task_preview=task[:100],
                ai_provider=self.ai_provider,
                model=model_id
            )
            raise ProviderTimeoutError(
                f"Execution timed out after {timeout or self.DEFAULT_TIMEOUT} seconds "
                f"(provider: {self.ai_provider}, model: {model_id})",
                provider_name=self.name
            )

        except ProviderExecutionError:
            # Re-raise our own exceptions
            raise

        except Exception as e:
            logger.error(
                "opencode_cli_execution_error",
                error=str(e),
                ai_provider=self.ai_provider,
                model=model_id,
                exc_info=True
            )
            raise ProviderExecutionError(
                f"Process execution failed ({self.ai_provider}): {str(e)}",
                provider_name=self.name
            ) from e

    def supports_tool(self, tool_name: str) -> bool:
        """
        Check if OpenCode supports this tool.

        Based on research from Story 11.6 (opencode-tool-mapping.md).

        Excellent support (90-100%):
        - Read, Write, Edit, Bash, Glob

        Partial support (60-70%):
        - MultiEdit (sequential, not atomic)
        - Grep (LSP-based, not regex)

        Not supported:
        - Task, WebFetch, WebSearch, TodoWrite, AskUserQuestion,
          NotebookEdit, Skill, SlashCommand

        Args:
            tool_name: Tool name to check

        Returns:
            True if tool is supported (fully or partially), False otherwise

        Example:
            ```python
            if provider.supports_tool("Read"):
                # Can use Read tool
                pass

            if not provider.supports_tool("WebFetch"):
                # Cannot use WebFetch
                logger.warning("WebFetch not supported by OpenCode")
            ```
        """
        return self.TOOL_MAPPING.get(tool_name, False)

    def get_supported_models(self) -> List[str]:
        """
        Get supported models for current AI provider.

        Returns canonical names only (not provider/model format).

        Returns:
            List of canonical model names

        Example:
            ```python
            # Anthropic provider
            provider = OpenCodeProvider(ai_provider="anthropic")
            models = provider.get_supported_models()
            # ['sonnet-4.5', 'opus-3', 'haiku-3', ...]

            # OpenAI provider
            provider = OpenCodeProvider(ai_provider="openai")
            models = provider.get_supported_models()
            # ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo', ...]
            ```
        """
        provider_models = self.MODEL_MAPPING.get(self.ai_provider, {})

        # Filter out passthrough mappings (those that start with provider/)
        canonical_names = [
            name for name in provider_models.keys()
            if not name.startswith(f"{self.ai_provider}/")
        ]

        return canonical_names

    def translate_model_name(self, canonical_name: str) -> str:
        """
        Translate canonical name to OpenCode model ID.

        OpenCode uses 'provider/model' format:
        - anthropic/claude-sonnet-4.5
        - openai/gpt-4
        - google/gemini-2.5-pro

        Args:
            canonical_name: Canonical model name (e.g., 'sonnet-4.5', 'gpt-4')

        Returns:
            OpenCode-specific model ID (provider/model format)

        Raises:
            ModelNotSupportedError: If model not supported for current provider

        Example:
            ```python
            # Anthropic provider
            provider = OpenCodeProvider(ai_provider="anthropic")
            provider.translate_model_name("sonnet-4.5")
            # -> "anthropic/claude-sonnet-4.5"

            # OpenAI provider
            provider = OpenCodeProvider(ai_provider="openai")
            provider.translate_model_name("gpt-4")
            # -> "openai/gpt-4"

            # Invalid model for provider
            provider = OpenCodeProvider(ai_provider="anthropic")
            provider.translate_model_name("gpt-4")
            # -> Raises ModelNotSupportedError
            ```
        """
        provider_models = self.MODEL_MAPPING.get(self.ai_provider, {})

        if canonical_name not in provider_models:
            supported = self.get_supported_models()
            logger.error(
                "model_not_supported",
                canonical_name=canonical_name,
                ai_provider=self.ai_provider,
                supported_models=supported
            )
            raise ModelNotSupportedError(
                provider_name=self.name,
                model_name=canonical_name,
                context={
                    "ai_provider": self.ai_provider,
                    "supported_models": supported
                }
            )

        translated = provider_models[canonical_name]

        logger.debug(
            "model_name_translated",
            canonical=canonical_name,
            translated=translated,
            ai_provider=self.ai_provider
        )

        return translated

    async def validate_configuration(self) -> bool:
        """
        Validate OpenCode configuration.

        Checks:
        - CLI executable exists
        - AI provider is valid
        - API key is set

        Returns:
            True if valid, False otherwise

        Example:
            ```python
            provider = OpenCodeProvider()

            if await provider.validate_configuration():
                # Ready to use
                result = await provider.execute_task(...)
            else:
                # Not configured
                print("Please configure OpenCode:")
                print("1. Install: npm install -g opencode-ai@latest")
                print("2. Set API key: export ANTHROPIC_API_KEY=...")
            ```
        """
        is_valid = True

        # Check CLI
        if not self.cli_path or not self.cli_path.exists():
            logger.warning(
                "opencode_cli_not_found",
                cli_path=str(self.cli_path) if self.cli_path else None,
                message="OpenCode CLI not found. Install: npm install -g opencode-ai@latest"
            )
            is_valid = False

        # Check provider
        if self.ai_provider not in self.MODEL_MAPPING:
            logger.warning(
                "invalid_ai_provider",
                ai_provider=self.ai_provider,
                valid_providers=list(self.MODEL_MAPPING.keys()),
                message=f"Invalid AI provider: {self.ai_provider}"
            )
            is_valid = False

        # Check API key
        if not self.api_key:
            env_var = self.API_KEY_ENV_VARS.get(self.ai_provider)
            logger.warning(
                "api_key_not_set",
                ai_provider=self.ai_provider,
                env_var=env_var,
                message=f"API key not set. Set {env_var} environment variable."
            )
            is_valid = False

        logger.info(
            "opencode_configuration_validated",
            is_valid=is_valid,
            ai_provider=self.ai_provider,
            has_cli=bool(self.cli_path and self.cli_path.exists()),
            has_api_key=bool(self.api_key)
        )

        return is_valid

    def get_configuration_schema(self) -> Dict:
        """
        Get configuration schema for OpenCode.

        Returns:
            JSON Schema dict describing configuration options

        Example:
            ```python
            schema = provider.get_configuration_schema()
            # Use for validation or documentation
            ```
        """
        return {
            "type": "object",
            "properties": {
                "cli_path": {
                    "type": "string",
                    "description": "Path to OpenCode CLI executable"
                },
                "ai_provider": {
                    "type": "string",
                    "enum": ["anthropic", "openai", "google"],
                    "description": "AI provider to use",
                    "default": "anthropic"
                },
                "api_key": {
                    "type": "string",
                    "description": "API key for the AI provider"
                }
            },
            "required": ["ai_provider"]
        }

    async def initialize(self) -> None:
        """
        Initialize provider.

        No-op for CLI provider (no persistent connections).

        Example:
            ```python
            await provider.initialize()
            # Provider ready to use
            ```
        """
        self._initialized = True
        logger.debug(
            "opencode_provider_initialized",
            ai_provider=self.ai_provider
        )

    async def cleanup(self) -> None:
        """
        Cleanup provider.

        No-op for CLI provider (no persistent connections).

        Example:
            ```python
            await provider.cleanup()
            # Provider cleaned up
            ```
        """
        self._initialized = False
        logger.debug(
            "opencode_provider_cleaned_up",
            ai_provider=self.ai_provider
        )

    def _detect_opencode_cli(self) -> Optional[Path]:
        """
        Auto-detect OpenCode CLI installation.

        Searches common installation paths for opencode executable.

        Returns:
            Path to OpenCode CLI if found, None otherwise

        Example:
            ```python
            cli_path = provider._detect_opencode_cli()
            if cli_path:
                print(f"Found OpenCode at: {cli_path}")
            else:
                print("OpenCode not found. Please install.")
            ```
        """
        # Common installation paths
        search_paths = [
            Path.home() / ".opencode" / "bin" / "opencode",
            Path.home() / "bin" / "opencode",
            Path("/usr/local/bin/opencode"),
            Path("/usr/bin/opencode"),
        ]

        # Windows paths
        if os.name == 'nt':
            search_paths.extend([
                Path(os.environ.get("LOCALAPPDATA", "")) / "opencode" / "bin" / "opencode.exe",
                Path.home() / ".opencode" / "bin" / "opencode.exe",
                Path("C:/Program Files/opencode/opencode.exe"),
            ])

        for path in search_paths:
            if path.exists() and path.is_file():
                logger.info("opencode_cli_detected", path=str(path))
                return path

        logger.warning(
            "opencode_cli_not_detected",
            searched_paths=[str(p) for p in search_paths],
            message="OpenCode CLI not found. Install: npm install -g opencode-ai@latest"
        )
        return None

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"OpenCodeProvider("
            f"ai_provider={self.ai_provider}, "
            f"has_api_key={bool(self.api_key)}, "
            f"has_cli={bool(self.cli_path)})"
        )

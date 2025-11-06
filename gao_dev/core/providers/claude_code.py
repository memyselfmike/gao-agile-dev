"""Claude Code CLI provider implementation.

This provider maintains the exact behavior of the original ProcessExecutor
implementation, extracted into a provider for multi-provider support.

Extracted from: gao_dev.core.services.process_executor.ProcessExecutor
Epic: 11 - Agent Provider Abstraction
Story: 11.2 - Implement ClaudeCodeProvider
"""

from pathlib import Path
from typing import AsyncGenerator, List, Dict, Optional, Any
import subprocess
import os
import structlog

from .base import IAgentProvider
from .models import AgentContext
from .exceptions import (
    ProviderExecutionError,
    ProviderTimeoutError,
    ProviderConfigurationError
)
from ..cli_detector import find_claude_cli

logger = structlog.get_logger()


class ClaudeCodeProvider(IAgentProvider):
    """
    Provider for Claude Code CLI execution.

    This provider maintains the exact behavior of the original
    ProcessExecutor implementation, extracted into a provider
    for multi-provider support.

    Execution Model: Subprocess (Claude CLI)
    Backend: Anthropic Claude

    Example:
        ```python
        provider = ClaudeCodeProvider()

        if await provider.validate_configuration():
            async for result in provider.execute_task(
                task="Write a hello world script",
                context=AgentContext(project_root=Path("/project")),
                model="sonnet-4.5",
                tools=["Read", "Write", "Bash"],
                timeout=3600
            ):
                print(result)
        ```
    """

    # Tool mapping: GAO-Dev tool name → Claude Code tool name
    TOOL_MAPPING = {
        "Read": "read",
        "Write": "write",
        "Edit": "edit",
        "MultiEdit": "multiedit",
        "Bash": "bash",
        "Grep": "grep",
        "Glob": "glob",
        "Task": "task",
        "WebFetch": "webfetch",
        "WebSearch": "websearch",
        "TodoWrite": "todowrite",
        "AskUserQuestion": "askuserquestion",
    }

    # Model translation: Canonical → Claude-specific
    MODEL_MAPPING = {
        # Canonical names
        "sonnet-4.5": "claude-sonnet-4-5-20250929",
        "sonnet-3.5": "claude-sonnet-3-5-20241022",
        "opus-3": "claude-opus-3-20250219",
        "haiku-3": "claude-haiku-3-20250219",

        # Passthrough for full model IDs
        "claude-sonnet-4-5-20250929": "claude-sonnet-4-5-20250929",
        "claude-sonnet-3-5-20241022": "claude-sonnet-3-5-20241022",
        "claude-opus-3-20250219": "claude-opus-3-20250219",
        "claude-haiku-3-20250219": "claude-haiku-3-20250219",
    }

    DEFAULT_TIMEOUT = 3600  # 1 hour

    def __init__(
        self,
        cli_path: Optional[Path] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize Claude Code provider.

        Args:
            cli_path: Path to Claude CLI executable (auto-detected if None)
            api_key: Anthropic API key (uses ANTHROPIC_API_KEY env if None)
        """
        # Convert cli_path to Path if it's a string (defensive for JSON deserialization)
        if cli_path is not None and isinstance(cli_path, str):
            cli_path = Path(cli_path)

        self.cli_path = cli_path or find_claude_cli()
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self._initialized = False

        logger.info(
            "claude_code_provider_initialized",
            has_cli_path=self.cli_path is not None,
            has_api_key=bool(self.api_key),
            cli_path=str(self.cli_path) if self.cli_path else None
        )

    @property
    def name(self) -> str:
        """Provider name."""
        return "claude-code"

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
        Execute task via Claude Code CLI.

        This method maintains 100% behavioral compatibility with the original
        ProcessExecutor.execute_agent_task() implementation.

        Args:
            task: Task description/prompt
            context: Execution context
            model: Canonical model name
            tools: List of tool names
            timeout: Timeout in seconds
            **kwargs: Additional arguments (ignored)

        Yields:
            Output from Claude CLI

        Raises:
            ProviderExecutionError: If execution fails
            ProviderTimeoutError: If execution times out
            ProviderConfigurationError: If not configured
        """
        if not self.cli_path:
            raise ProviderConfigurationError(
                "Claude CLI not found. Install Claude Code or set cli_path.",
                provider_name=self.name
            )

        # Translate model name
        model_id = self.translate_model_name(model)

        # Build command (exact same flags as original ProcessExecutor)
        cmd = [str(self.cli_path)]
        cmd.extend(['--print'])
        cmd.extend(['--dangerously-skip-permissions'])
        cmd.extend(['--model', model_id])
        cmd.extend(['--add-dir', str(context.project_root)])

        # Set environment
        env = os.environ.copy()
        if self.api_key:
            env['ANTHROPIC_API_KEY'] = self.api_key

        # Log execution (exact same format as ProcessExecutor)
        logger.info(
            "executing_claude_cli",
            cli=str(self.cli_path),
            timeout=timeout or self.DEFAULT_TIMEOUT,
            has_api_key=bool(self.api_key),
            command_preview=f"{cmd[0]} {' '.join(cmd[1:4])}..."
        )

        try:
            # Execute subprocess (exact same as ProcessExecutor)
            # IMPORTANT: encoding='utf-8' is required for Windows compatibility
            # Windows defaults to 'charmap' which doesn't support Unicode characters
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',  # Windows compatibility
                env=env,
                cwd=str(context.project_root)
            )

            # Communicate with timeout
            stdout, stderr = process.communicate(
                input=task,
                timeout=timeout or self.DEFAULT_TIMEOUT
            )

            # Log completion (exact same format as ProcessExecutor)
            logger.info(
                "claude_cli_completed",
                return_code=process.returncode,
                stdout_length=len(stdout) if stdout else 0,
                stderr_length=len(stderr) if stderr else 0,
                stdout_preview=stdout[:200] if stdout else "(empty)",
                stderr_preview=stderr[:200] if stderr else "(empty)"
            )

            # Log stderr if present (exact same as ProcessExecutor)
            if stderr:
                logger.warning("claude_cli_stderr", stderr=stderr[:1000])

            # Yield output even if return code isn't 0 (exact same as ProcessExecutor)
            if stdout:
                yield stdout

            # Check exit code (exact same error message as ProcessExecutor)
            if process.returncode != 0:
                error_msg = f"Claude CLI failed with exit code {process.returncode}"
                if stderr:
                    error_msg += f": {stderr[:500]}"
                if not stdout and not stderr:
                    error_msg += " (no output - check if claude.bat is configured correctly)"

                logger.error(
                    "claude_cli_execution_failed",
                    exit_code=process.returncode,
                    error=error_msg
                )
                raise ProviderExecutionError(error_msg, provider_name=self.name)

        except subprocess.TimeoutExpired:
            process.kill()
            logger.error(
                "claude_cli_timeout",
                timeout=timeout or self.DEFAULT_TIMEOUT,
                task_preview=task[:100]
            )
            raise ProviderTimeoutError(
                f"Execution timed out after {timeout or self.DEFAULT_TIMEOUT} seconds",
                provider_name=self.name
            )

        except ProviderExecutionError:
            # Re-raise our own exceptions
            raise

        except Exception as e:
            logger.error(
                "claude_cli_execution_error",
                error=str(e),
                exc_info=True
            )
            raise ProviderExecutionError(
                f"Process execution failed: {str(e)}",
                provider_name=self.name
            ) from e

    def supports_tool(self, tool_name: str) -> bool:
        """Check if Claude Code supports this tool."""
        return tool_name in self.TOOL_MAPPING

    def get_supported_models(self) -> List[str]:
        """Get supported Claude models (canonical names only)."""
        # Return only canonical names, not full IDs
        return ["sonnet-4.5", "sonnet-3.5", "opus-3", "haiku-3"]

    def translate_model_name(self, canonical_name: str) -> str:
        """
        Translate canonical name to Claude model ID.

        Args:
            canonical_name: Canonical model name

        Returns:
            Claude-specific model ID

        Example:
            translate_model_name("sonnet-4.5") -> "claude-sonnet-4-5-20250929"
        """
        # Try mapping, fallback to passthrough
        translated = self.MODEL_MAPPING.get(canonical_name, canonical_name)

        logger.debug(
            "model_name_translated",
            canonical=canonical_name,
            translated=translated
        )

        return translated

    async def validate_configuration(self) -> bool:
        """
        Validate Claude Code configuration.

        Checks:
        - CLI executable exists
        - API key is set

        Returns:
            True if valid, False otherwise
        """
        is_valid = True

        if not self.cli_path or not self.cli_path.exists():
            logger.warning(
                "claude_cli_not_found",
                cli_path=str(self.cli_path) if self.cli_path else None
            )
            is_valid = False

        if not self.api_key:
            logger.warning("anthropic_api_key_not_set")
            is_valid = False

        logger.info(
            "claude_code_configuration_validated",
            is_valid=is_valid
        )

        return is_valid

    def get_configuration_schema(self) -> Dict[str, Any]:
        """Get configuration schema for Claude Code."""
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

    async def initialize(self) -> None:
        """Initialize provider (no-op for CLI provider)."""
        self._initialized = True
        logger.debug("claude_code_provider_initialized")

    async def cleanup(self) -> None:
        """Cleanup provider (no-op for CLI provider)."""
        self._initialized = False
        logger.debug("claude_code_provider_cleaned_up")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ClaudeCodeProvider("
            f"cli_path={self.cli_path}, "
            f"has_api_key={bool(self.api_key)})"
        )

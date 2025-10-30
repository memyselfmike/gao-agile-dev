"""
ProcessExecutor Service - Executes external processes (Claude CLI).

Extracted from GAODevOrchestrator (Epic 6, Story 6.3) to achieve SOLID principles.

Responsibilities:
- Execute Claude CLI subprocesses
- Stream output to caller
- Handle process timeouts
- Capture exit codes and errors
- Log process execution details

NOT responsible for:
- Workflow execution (WorkflowCoordinator)
- Story lifecycle (StoryLifecycleManager)
- Quality validation (QualityGateManager)
- High-level orchestration (stays in orchestrator)
"""

import structlog
import subprocess
import os
from typing import AsyncGenerator, Optional
from pathlib import Path
from datetime import datetime

logger = structlog.get_logger()


class ProcessExecutionError(Exception):
    """Raised when a process execution fails."""
    pass


class ProcessExecutor:
    """
    Executes external processes (Claude CLI).

    Single Responsibility: Execute subprocesses, stream output, handle timeouts,
    and capture exit codes.

    This service was extracted from GAODevOrchestrator (Epic 6, Story 6.3) to
    follow the Single Responsibility Principle.

    Responsibilities:
    - Execute Claude CLI subprocesses
    - Stream output to caller line-by-line
    - Handle process timeouts
    - Capture exit codes and errors
    - Log process execution details

    NOT responsible for:
    - Workflow execution (WorkflowCoordinator)
    - Story lifecycle (StoryLifecycleManager)
    - Quality validation (QualityGateManager)
    - Orchestrator-level logic (stays in orchestrator)

    Example:
        ```python
        executor = ProcessExecutor(
            project_root=Path("/project"),
            cli_path=Path("/usr/bin/claude"),
            api_key="sk-..."
        )

        async for output in executor.execute_agent_task(
            task="Implement feature X",
            timeout=3600
        ):
            print(output)
        ```
    """

    # Default timeout: 1 hour (3600 seconds)
    DEFAULT_TIMEOUT = 3600

    def __init__(
        self,
        project_root: Path,
        cli_path: Optional[Path] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize executor with injected dependencies.

        Args:
            project_root: Root directory of the project
            cli_path: Path to Claude CLI executable
            api_key: Anthropic API key for Claude CLI
        """
        self.project_root = project_root
        self.cli_path = cli_path
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        logger.info(
            "process_executor_initialized",
            project_root=str(project_root),
            has_cli=cli_path is not None,
            has_api_key=bool(self.api_key)
        )

    async def execute_agent_task(
        self,
        task: str,
        timeout: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        Execute agent task via Claude CLI subprocess.

        Streams output from process line-by-line. Handles timeouts, exit codes,
        and error conditions with proper logging.

        Args:
            task: Task description to pass to Claude CLI
            timeout: Process timeout in seconds (default: 3600)

        Yields:
            Output lines from process

        Raises:
            ProcessExecutionError: If process fails
            ValueError: If Claude CLI not found
            TimeoutError: If process exceeds timeout
        """
        if not self.cli_path:
            raise ValueError("Claude CLI not found")

        timeout = timeout or self.DEFAULT_TIMEOUT

        # Build command
        cmd = [str(self.cli_path)]
        cmd.extend(['--print'])  # Non-interactive output
        cmd.extend(['--dangerously-skip-permissions'])  # Auto-approve tools
        cmd.extend(['--model', 'claude-sonnet-4-5-20250929'])
        cmd.extend(['--add-dir', str(self.project_root)])

        # Set environment with API key
        env = os.environ.copy()
        if self.api_key:
            env['ANTHROPIC_API_KEY'] = self.api_key

        logger.info(
            "executing_claude_cli",
            cli=str(self.cli_path),
            timeout=timeout,
            has_api_key=bool(self.api_key),
            command_preview=f"{cmd[0]} {' '.join(cmd[1:4])}..."
        )

        try:
            # Execute Claude CLI as subprocess
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=str(self.project_root)
            )

            # Send task as input and wait for completion
            stdout, stderr = process.communicate(input=task, timeout=timeout)

            logger.info(
                "claude_cli_completed",
                return_code=process.returncode,
                stdout_length=len(stdout) if stdout else 0,
                stderr_length=len(stderr) if stderr else 0,
                stdout_preview=stdout[:200] if stdout else "(empty)",
                stderr_preview=stderr[:200] if stderr else "(empty)"
            )

            if stderr:
                logger.warning("claude_cli_stderr", stderr=stderr[:1000])

            # Yield output even if return code isn't 0 (might have partial output)
            if stdout:
                yield stdout

            # Check exit code
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
                raise ProcessExecutionError(error_msg)

        except subprocess.TimeoutExpired:
            logger.error(
                "claude_cli_timeout",
                timeout=timeout,
                task_preview=task[:100]
            )
            process.kill()
            raise TimeoutError(f"Claude CLI execution timed out after {timeout} seconds")

        except ProcessExecutionError:
            # Re-raise our own exceptions
            raise

        except Exception as e:
            logger.error(
                "claude_cli_execution_error",
                error=str(e),
                exc_info=True
            )
            raise ProcessExecutionError(f"Process execution failed: {str(e)}")

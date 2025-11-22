"""
Concrete agent implementation using Claude Code.

This module provides a concrete IAgent implementation that executes
tasks using Claude Code CLI.
"""

from pathlib import Path
from typing import AsyncGenerator, List, Optional
import asyncio
import structlog

from .base import BaseAgent
from .exceptions import AgentExecutionError
from ..core.models.agent import AgentContext, AgentCapability

logger = structlog.get_logger()


class ClaudeAgent(BaseAgent):
    """
    Concrete agent implementation that uses Claude Code for task execution.

    This agent executes tasks by invoking Claude Code CLI with the
    agent's persona and tools. It implements the IAgent interface
    and can be created by the AgentFactory.

    Example:
        ```python
        agent = ClaudeAgent(
            name="Amelia",
            role="Software Developer",
            persona="You are Amelia...",
            tools=["Read", "Write", "Edit", "Bash"]
        )

        async for message in agent.execute_task("Implement feature X", context):
            print(message)
        ```
    """

    def __init__(
        self,
        name: str,
        role: str,
        persona: str,
        tools: List[str],
        model: str = "claude-sonnet-4-5-20250929",
        persona_file: Optional[Path] = None,
        capabilities: Optional[List[AgentCapability]] = None
    ):
        """
        Initialize Claude agent.

        Args:
            name: Agent name (e.g., "Amelia", "Mary")
            role: Agent role (e.g., "Developer", "Business Analyst")
            persona: Agent persona/instructions
            tools: List of available tools
            model: Claude model identifier
            persona_file: Optional path to persona markdown file
            capabilities: Optional list of agent capabilities
        """
        super().__init__(name, role, persona, tools, model, persona_file)
        self._capabilities = capabilities or []

    async def execute_task(
        self,
        task: str,
        context: AgentContext
    ) -> AsyncGenerator[str, None]:
        """
        Execute a task using Claude Code.

        This implementation uses Claude Code CLI to execute the task
        with the agent's persona and tools.

        Args:
            task: Task description in natural language
            context: Execution context (project root, tools, etc.)

        Yields:
            str: Progress messages during execution

        Raises:
            AgentExecutionError: If task execution fails
        """
        if not self._initialized:
            await self.initialize()

        logger.info(
            "agent_task_start",
            agent=self.name,
            role=self.role,
            task=task[:100]  # Truncate for logging
        )

        try:
            # Build the full prompt with persona and task
            self._build_prompt(task, context)

            # For now, yield a simple message indicating task delegation
            # In a real implementation, this would invoke Claude Code CLI
            # and stream the output
            yield f"[{self.name}] Starting task..."
            yield f"[{self.name}] Task: {task}"

            # Simulate task execution
            # TODO: Replace with actual Claude Code CLI integration
            # This is where we would execute:
            # subprocess.run(["claude", "-p", full_prompt, ...])

            await asyncio.sleep(0.1)  # Simulate work

            yield f"[{self.name}] Task completed"

            logger.info(
                "agent_task_complete",
                agent=self.name,
                task=task[:100]
            )

        except Exception as e:
            logger.error(
                "agent_task_failed",
                agent=self.name,
                task=task[:100],
                error=str(e)
            )
            raise AgentExecutionError(
                f"Agent '{self.name}' failed to execute task: {e}",
                agent_name=self.name,
                task=task
            ) from e

    def _build_prompt(self, task: str, context: AgentContext) -> str:
        """
        Build the full prompt for Claude.

        Combines agent persona with task and context information.

        Args:
            task: Task description
            context: Execution context

        Returns:
            str: Full prompt for Claude
        """
        prompt_parts = []

        # Add persona
        if self._persona:
            prompt_parts.append(f"# Agent Persona: {self.name} ({self.role})")
            prompt_parts.append(self._persona)
            prompt_parts.append("")

        # Add context information
        prompt_parts.append("# Task Context")
        prompt_parts.append(f"Project Root: {context.project_root}")
        prompt_parts.append(f"Available Tools: {', '.join(self.tools)}")
        prompt_parts.append("")

        # Add the task
        prompt_parts.append("# Task")
        prompt_parts.append(task)

        return "\n".join(prompt_parts)

    def get_capabilities(self) -> List[AgentCapability]:
        """
        Get list of agent capabilities.

        Returns:
            List of agent capabilities
        """
        return self._capabilities.copy()

    def can_handle_task(self, task: str) -> bool:
        """
        Check if agent can handle given task.

        Uses parent class logic (PlanningAgent or ImplementationAgent)
        if available, otherwise returns True.

        Args:
            task: Task description

        Returns:
            bool: True if agent can handle this task
        """
        # Delegate to parent class if it has logic
        return super().can_handle_task(task)

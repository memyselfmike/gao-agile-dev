"""Example agent implementation for testing."""

from typing import AsyncGenerator
from gao_dev.agents.base import BaseAgent
from gao_dev.core.models.agent import AgentContext


class ExampleAgent(BaseAgent):
    """Example agent for plugin system testing.

    This agent demonstrates how to create a custom agent that
    can be registered via the plugin system.
    """

    def __init__(self, **kwargs):
        """Initialize example agent with default or provided configuration."""
        # Use provided values or defaults
        super().__init__(
            name=kwargs.get("name", "ExampleAgent"),
            role=kwargs.get("role", "Example Role"),
            persona=kwargs.get("persona", "I am an example agent for testing the plugin system."),
            tools=kwargs.get("tools", ["Read", "Grep"]),
            model=kwargs.get("model", "claude-sonnet-4-5-20250929")
        )

    async def execute_task(
        self,
        task: str,
        context: AgentContext
    ) -> AsyncGenerator[str, None]:
        """Execute a task and yield progress messages.

        Args:
            task: Task description
            context: Execution context

        Yields:
            Progress messages
        """
        yield f"ExampleAgent starting task: {task}"
        yield "ExampleAgent processing..."
        yield f"ExampleAgent completed task successfully"

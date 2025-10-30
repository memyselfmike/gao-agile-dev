"""Test agent implementation."""

from gao_dev.agents.base import BaseAgent


class TestAgent(BaseAgent):
    """Test agent for plugin system testing."""

    async def execute_task(self, task, context):
        """Execute test task."""
        yield f"TestAgent executing: {task}"

"""Example agent plugin for testing."""

from typing import Type
from gao_dev.plugins import BaseAgentPlugin, AgentMetadata
from gao_dev.core.interfaces.agent import IAgent
from .agent import ExampleAgent


class ExampleAgentPlugin(BaseAgentPlugin):
    """Example agent plugin demonstrating the plugin API.

    This plugin shows how to:
    - Extend BaseAgentPlugin
    - Provide agent class, name, and metadata
    - Integrate with GAO-Dev's agent system
    """

    def get_agent_class(self) -> Type[IAgent]:
        """Return the ExampleAgent class."""
        return ExampleAgent

    def get_agent_name(self) -> str:
        """Return the unique agent name."""
        return "ExampleAgent"

    def get_agent_metadata(self) -> AgentMetadata:
        """Return agent metadata."""
        return AgentMetadata(
            name="ExampleAgent",
            role="Example Role",
            description="Example agent for testing plugin system",
            capabilities=["testing", "demonstration"],
            tools=["Read", "Grep"],
            model="claude-sonnet-4-5-20250929"
        )

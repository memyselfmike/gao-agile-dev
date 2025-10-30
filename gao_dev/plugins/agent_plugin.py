"""Agent plugin API for GAO-Dev.

This module provides the plugin API for creating custom agent plugins.
"""

from abc import abstractmethod
from typing import Type
import structlog

from .base_plugin import BasePlugin
from .models import AgentMetadata
from ..core.interfaces.agent import IAgent
from .exceptions import PluginError

logger = structlog.get_logger(__name__)


class BaseAgentPlugin(BasePlugin):
    """Base class for agent plugins.

    Agent plugins provide custom agents that integrate with GAO-Dev's
    agent system. Plugin agents have access to the same tools and
    capabilities as built-in agents.

    Subclasses must implement:
    - get_agent_class(): Return agent class implementing IAgent
    - get_agent_name(): Return unique agent name
    - get_agent_metadata(): Return agent metadata

    Example:
        ```python
        from gao_dev.plugins import BaseAgentPlugin, AgentMetadata
        from gao_dev.agents.base import BaseAgent

        class DomainExpertAgent(BaseAgent):
            async def execute_task(self, task, context):
                yield "DomainExpert processing..."
                # Implementation
                yield "Task complete"

        class DomainExpertPlugin(BaseAgentPlugin):
            def get_agent_class(self):
                return DomainExpertAgent

            def get_agent_name(self):
                return "DomainExpert"

            def get_agent_metadata(self):
                return AgentMetadata(
                    name="DomainExpert",
                    role="Domain Expert",
                    description="Expert in specific domain knowledge",
                    capabilities=["analysis", "consultation"],
                    tools=["Read", "Grep", "WebFetch"]
                )
        ```
    """

    @abstractmethod
    def get_agent_class(self) -> Type[IAgent]:
        """Get the agent class to register.

        Returns:
            Agent class implementing IAgent interface

        Raises:
            PluginError: If agent class doesn't implement IAgent
        """
        pass

    @abstractmethod
    def get_agent_name(self) -> str:
        """Get unique agent name.

        This name will be used to register the agent with AgentFactory.
        Must be unique across all agents (built-in and plugins).

        Returns:
            Unique agent name (e.g., "DomainExpert", "DataAnalyst")
        """
        pass

    @abstractmethod
    def get_agent_metadata(self) -> AgentMetadata:
        """Get agent metadata.

        Returns:
            AgentMetadata with agent details (role, description, capabilities, tools)
        """
        pass

    def validate_agent_class(self) -> None:
        """Validate that agent class implements IAgent interface.

        Raises:
            PluginError: If agent class doesn't implement IAgent
        """
        agent_class = self.get_agent_class()

        if not isinstance(agent_class, type):
            raise PluginError(
                f"get_agent_class() must return a class, got {type(agent_class)}"
            )

        if not issubclass(agent_class, IAgent):
            raise PluginError(
                f"Agent class '{agent_class.__name__}' must implement IAgent interface"
            )

        logger.debug(
            "agent_class_validated",
            agent_class=agent_class.__name__,
            agent_name=self.get_agent_name()
        )

"""
Agent interfaces for GAO-Dev agent system.

This module defines the contract for all agents (built-in and plugin-based).
Agents are specialized AI entities with specific capabilities and responsibilities.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Optional


class IAgent(ABC):
    """
    Interface for all GAO-Dev agents (built-in and plugins).

    An agent is a specialized AI entity with specific capabilities
    and responsibilities (e.g., Product Manager, Developer, QA).
    Each agent has a persona, tools, and the ability to execute tasks.

    Example:
        ```python
        class AmeliaAgent(IAgent):
            @property
            def name(self) -> str:
                return "Amelia"

            @property
            def role(self) -> str:
                return "Software Developer"

            async def execute_task(self, task: str, context: AgentContext):
                # Implementation
                async for message in self._run_claude_cli(task):
                    yield message
        ```
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Agent's unique name.

        Returns:
            str: Agent name (e.g., "Mary", "John", "Amelia")
        """
        pass

    @property
    @abstractmethod
    def role(self) -> str:
        """
        Agent's role/specialty.

        Returns:
            str: Role description (e.g., "Business Analyst", "Developer", "QA")
        """
        pass

    @abstractmethod
    async def execute_task(
        self,
        task: str,
        context: 'AgentContext'  # Forward reference
    ) -> AsyncGenerator[str, None]:
        """
        Execute a task and yield progress messages.

        This is the primary method for agent execution. The agent receives
        a task description in natural language and yields progress updates
        as it works.

        Args:
            task: Task description in natural language
            context: Execution context (project root, tools, etc.)

        Yields:
            str: Progress messages during execution

        Raises:
            AgentExecutionError: If task execution fails
            ValidationError: If task or context invalid
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> List['AgentCapability']:  # Forward reference
        """
        Get list of agent capabilities.

        Capabilities define what kinds of tasks this agent can handle.
        For example: PLANNING, IMPLEMENTATION, TESTING, CODE_REVIEW

        Returns:
            List of capabilities this agent possesses
        """
        pass

    @abstractmethod
    def can_handle_task(self, task: str) -> bool:
        """
        Check if agent can handle given task.

        This method allows for task routing - assigning tasks to agents
        that are best suited to handle them.

        Args:
            task: Task description in natural language

        Returns:
            bool: True if agent can handle this task, False otherwise
        """
        pass


class IAgentFactory(ABC):
    """
    Factory interface for creating agent instances.

    The factory pattern centralizes agent creation and allows for
    configuration-driven instantiation. This enables plugin agents
    to be created alongside built-in agents.

    Example:
        ```python
        factory = DefaultAgentFactory(agent_registry)
        amelia = factory.create_agent("amelia", config)
        custom = factory.create_agent("domain-expert", config)
        ```
    """

    @abstractmethod
    def create_agent(
        self,
        agent_type: str,
        config: Optional['AgentConfig'] = None  # Forward reference
    ) -> IAgent:
        """
        Create an agent instance of the specified type.

        Args:
            agent_type: Agent type identifier (e.g., "amelia", "john")
            config: Optional configuration for the agent

        Returns:
            IAgent: Configured agent instance

        Raises:
            AgentNotFoundError: If agent type not registered
            AgentCreationError: If agent creation fails
            ValidationError: If config invalid
        """
        pass

    @abstractmethod
    def register_agent_class(
        self,
        agent_type: str,
        agent_class: type
    ) -> None:
        """
        Register an agent class for a given type.

        This allows plugins to register custom agent types that can
        be created via the factory.

        Args:
            agent_type: Agent type identifier
            agent_class: Agent class (must implement IAgent)

        Raises:
            RegistrationError: If agent_class doesn't implement IAgent
            DuplicateRegistrationError: If type already registered
        """
        pass

    @abstractmethod
    def list_available_agents(self) -> List[str]:
        """
        List all registered agent types.

        Returns:
            List of agent type identifiers
        """
        pass

    @abstractmethod
    def agent_exists(self, agent_type: str) -> bool:
        """
        Check if an agent type is registered.

        Args:
            agent_type: Agent type identifier

        Returns:
            bool: True if agent type registered, False otherwise
        """
        pass

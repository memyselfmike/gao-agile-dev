"""
Agent Factory implementation.

This module implements the Factory Pattern for creating agent instances.
It provides centralized agent creation with support for both built-in and
plugin agents.
"""

from pathlib import Path
from typing import Dict, List, Optional, Type
import structlog

from ..interfaces.agent import IAgent, IAgentFactory
from ..models.agent import AgentConfig, AgentCapability, CommonCapabilities
from ...agents.claude_agent import ClaudeAgent
from ...agents.exceptions import (
    AgentNotFoundError,
    AgentCreationError,
    RegistrationError,
    DuplicateRegistrationError
)

logger = structlog.get_logger()


class AgentFactory(IAgentFactory):
    """
    Concrete factory for creating agent instances.

    Uses registry pattern to manage agent types. Supports both
    built-in agents and plugin agents. Centralizes all agent
    creation logic for consistency and testability.

    Example:
        ```python
        factory = AgentFactory(agents_dir)
        amelia = factory.create_agent("amelia")
        custom = factory.create_agent("domain-expert", config)
        ```

    Attributes:
        _registry: Internal registry mapping agent types to classes
        _agents_dir: Directory containing agent persona files
        _agent_configs: Built-in agent configurations
    """

    def __init__(self, agents_dir: Path):
        """
        Initialize agent factory.

        Args:
            agents_dir: Path to directory containing agent persona files
        """
        self._registry: Dict[str, Type[IAgent]] = {}
        self._agents_dir = Path(agents_dir)
        self._agent_configs: Dict[str, Dict] = {}

        # Register built-in agent class
        self._register_builtin_agents()

        logger.info(
            "agent_factory_initialized",
            agents_dir=str(self._agents_dir),
            registered_agents=self.list_available_agents()
        )

    def create_agent(
        self,
        agent_type: str,
        config: Optional[AgentConfig] = None
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
        """
        agent_type_lower = agent_type.lower()

        # Check if agent type exists
        if not self.agent_exists(agent_type_lower):
            available = ", ".join(self.list_available_agents())
            raise AgentNotFoundError(
                f"Agent type '{agent_type}' not registered. "
                f"Available agents: {available}"
            )

        # Get agent class from registry
        agent_class = self._registry[agent_type_lower]

        # Get built-in config if not provided
        if config is None and agent_type_lower in self._agent_configs:
            builtin_config = self._agent_configs[agent_type_lower]
            config = AgentConfig(
                name=builtin_config["name"],
                role=builtin_config["role"],
                persona_file=builtin_config.get("persona_file"),
                tools=builtin_config.get("tools", []),
            )

        try:
            # Load persona from file if it exists
            persona_file = self._agents_dir / f"{agent_type_lower}.md"
            persona = ""

            if persona_file.exists():
                try:
                    persona = persona_file.read_text(encoding="utf-8")
                except Exception as e:
                    logger.warning(
                        "failed_to_load_persona",
                        agent_type=agent_type,
                        persona_file=str(persona_file),
                        error=str(e)
                    )

            # Get capabilities from builtin config
            capabilities = None
            if agent_type_lower in self._agent_configs:
                capabilities = self._agent_configs[agent_type_lower].get("capabilities", [])

            # Create agent instance
            agent = agent_class(
                name=config.name if config else agent_type.capitalize(),
                role=config.role if config else "",
                persona=persona,
                tools=config.tools if config else [],
                model="claude-sonnet-4-5-20250929",
                persona_file=persona_file if persona_file.exists() else None,
                capabilities=capabilities
            )

            logger.info(
                "agent_created",
                agent_type=agent_type,
                name=agent.name,
                role=agent.role
            )

            return agent

        except Exception as e:
            logger.error(
                "agent_creation_failed",
                agent_type=agent_type,
                error=str(e)
            )
            raise AgentCreationError(
                f"Failed to create agent '{agent_type}': {e}"
            ) from e

    def register_agent_class(
        self,
        agent_type: str,
        agent_class: Type[IAgent]
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
        # Validate that class implements IAgent
        if not issubclass(agent_class, IAgent):
            raise RegistrationError(
                f"Agent class '{agent_class.__name__}' must implement IAgent interface"
            )

        agent_type_lower = agent_type.lower()

        # Check for duplicates
        if agent_type_lower in self._registry:
            raise DuplicateRegistrationError(
                f"Agent type '{agent_type}' is already registered"
            )

        # Register
        self._registry[agent_type_lower] = agent_class

        logger.info(
            "agent_registered",
            agent_type=agent_type,
            agent_class=agent_class.__name__
        )

    def list_available_agents(self) -> List[str]:
        """
        List all registered agent types.

        Returns:
            List of agent type identifiers (sorted alphabetically)
        """
        return sorted(self._registry.keys())

    def agent_exists(self, agent_type: str) -> bool:
        """
        Check if an agent type is registered.

        Args:
            agent_type: Agent type identifier

        Returns:
            bool: True if agent type registered, False otherwise
        """
        return agent_type.lower() in self._registry

    def _register_builtin_agents(self) -> None:
        """
        Register all built-in GAO-Dev agents.

        This method registers all 8 core agents: Mary, John, Winston,
        Sally, Bob, Amelia, Murat, and Brian.
        """
        # Define built-in agent configurations
        builtin_agents = {
            "mary": {
                "name": "Mary",
                "role": "Business Analyst",
                "tools": ["Read", "Write", "Grep", "Glob", "WebSearch", "WebFetch"],
                "capabilities": [CommonCapabilities.ANALYSIS]
            },
            "john": {
                "name": "John",
                "role": "Product Manager",
                "tools": ["Read", "Write", "Grep", "Glob"],
                "capabilities": [CommonCapabilities.PLANNING, CommonCapabilities.PROJECT_MANAGEMENT]
            },
            "winston": {
                "name": "Winston",
                "role": "Technical Architect",
                "tools": ["Read", "Write", "Edit", "Grep", "Glob"],
                "capabilities": [CommonCapabilities.ARCHITECTURE]
            },
            "sally": {
                "name": "Sally",
                "role": "UX Designer",
                "tools": ["Read", "Write", "Grep", "Glob"],
                "capabilities": [CommonCapabilities.UX_DESIGN]
            },
            "bob": {
                "name": "Bob",
                "role": "Scrum Master",
                "tools": ["Read", "Write", "Grep", "Glob"],
                "capabilities": [CommonCapabilities.SCRUM_MASTER, CommonCapabilities.PROJECT_MANAGEMENT]
            },
            "amelia": {
                "name": "Amelia",
                "role": "Software Developer",
                "tools": ["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
                "capabilities": [CommonCapabilities.IMPLEMENTATION, CommonCapabilities.CODE_REVIEW]
            },
            "murat": {
                "name": "Murat",
                "role": "Test Architect",
                "tools": ["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
                "capabilities": [CommonCapabilities.TESTING]
            },
            "brian": {
                "name": "Brian",
                "role": "Workflow Coordinator",
                "tools": ["Read", "Write", "Grep", "Glob"],
                "capabilities": [CommonCapabilities.PROJECT_MANAGEMENT, CommonCapabilities.PLANNING]
            }
        }

        # Store configurations
        self._agent_configs = builtin_agents

        # Register ClaudeAgent class for all built-in agents
        for agent_type in builtin_agents.keys():
            self._registry[agent_type] = ClaudeAgent

        logger.info(
            "builtin_agents_registered",
            count=len(builtin_agents),
            agents=list(builtin_agents.keys())
        )

"""
Agent Factory implementation.

This module implements the Factory Pattern for creating agent instances.
It provides centralized agent creation with support for both built-in and
plugin agents.
"""

from pathlib import Path
from typing import Dict, List, Optional, Type
import structlog
import os

from ..interfaces.agent import IAgent, IAgentFactory
from ..models.agent import AgentConfig, AgentCapability, CommonCapabilities
from ..agent_config_loader import AgentConfigLoader
from ..models.agent_config import AgentConfig as YAMLAgentConfig
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
        self._yaml_agent_configs: Dict[str, YAMLAgentConfig] = {}

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

        # Get YAML config if available, otherwise fall back to old config
        yaml_config = self._yaml_agent_configs.get(agent_type_lower)

        # Get built-in config if not provided
        if config is None:
            if yaml_config:
                # Use YAML config
                config = AgentConfig(
                    name=yaml_config.name,
                    role=yaml_config.role,
                    persona_file=self._agents_dir / f"{agent_type_lower}.md",
                    tools=yaml_config.tools,
                )
            elif agent_type_lower in self._agent_configs:
                # Use legacy config
                builtin_config = self._agent_configs[agent_type_lower]
                config = AgentConfig(
                    name=builtin_config["name"],
                    role=builtin_config["role"],
                    persona_file=builtin_config.get("persona_file"),
                    tools=builtin_config.get("tools", []),
                )

        try:
            # Use persona from YAML config if available
            if yaml_config:
                persona = yaml_config.persona
                persona_file = self._agents_dir / f"{agent_type_lower}.md"
            else:
                # Load persona from file if it exists (legacy path)
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

            # Get capabilities from YAML config or legacy config
            capabilities = None
            if yaml_config:
                # Convert string capabilities to AgentCapability objects
                capabilities = []
                for cap_str in yaml_config.capabilities:
                    # Map string capability to CommonCapabilities
                    cap_map = {
                        "analysis": CommonCapabilities.ANALYSIS,
                        "planning": CommonCapabilities.PLANNING,
                        "architecture": CommonCapabilities.ARCHITECTURE,
                        "ux-design": CommonCapabilities.UX_DESIGN,
                        "implementation": CommonCapabilities.IMPLEMENTATION,
                        "code-review": CommonCapabilities.CODE_REVIEW,
                        "testing": CommonCapabilities.TESTING,
                        "project-management": CommonCapabilities.PROJECT_MANAGEMENT,
                        "scrum-master": CommonCapabilities.SCRUM_MASTER,
                    }
                    if cap_str in cap_map:
                        capabilities.append(cap_map[cap_str])
            elif agent_type_lower in self._agent_configs:
                capabilities = self._agent_configs[agent_type_lower].get("capabilities", [])

            # Get model: environment variable > YAML config > default
            # GAO_DEV_MODEL allows global model override for testing different providers
            model = os.getenv("GAO_DEV_MODEL")
            if not model:
                model = yaml_config.model if yaml_config else "claude-sonnet-4-5-20250929"

            logger.info(
                "agent_model_selected",
                agent_type=agent_type,
                model=model,
                from_env=bool(os.getenv("GAO_DEV_MODEL")),
                from_yaml=bool(yaml_config and yaml_config.model)
            )

            # Create agent instance
            agent = agent_class(
                name=config.name if config else agent_type.capitalize(),
                role=config.role if config else "",
                persona=persona,
                tools=config.tools if config else [],
                model=model,
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

    def register_plugin_agent(
        self,
        agent_name: str,
        agent_class: Type[IAgent]
    ) -> None:
        """
        Register a plugin agent.

        This is a specialized method for plugin agents that provides
        additional validation and logging specific to plugins.

        Args:
            agent_name: Unique agent name (e.g., "DomainExpert")
            agent_class: Agent class implementing IAgent

        Raises:
            RegistrationError: If agent_class doesn't implement IAgent
            DuplicateRegistrationError: If agent name already registered
        """
        # Validate that class implements IAgent
        if not issubclass(agent_class, IAgent):
            raise RegistrationError(
                f"Plugin agent class '{agent_class.__name__}' must implement IAgent interface"
            )

        agent_name_lower = agent_name.lower()

        # Check for duplicates (with better error message for plugins)
        if agent_name_lower in self._registry:
            existing_class = self._registry[agent_name_lower]
            raise DuplicateRegistrationError(
                f"Agent '{agent_name}' is already registered as {existing_class.__name__}. "
                f"Plugin agents must have unique names."
            )

        # Register
        self._registry[agent_name_lower] = agent_class

        logger.info(
            "plugin_agent_registered",
            agent_name=agent_name,
            agent_class=agent_class.__name__,
            total_agents=len(self._registry)
        )

    def list_available_agents(self) -> List[str]:
        """
        List all registered agent types.

        Returns:
            List of agent type identifiers (sorted alphabetically)
        """
        return sorted(self._registry.keys())

    def list_agents(self) -> List[str]:
        """
        List all registered agent types (alias for list_available_agents).

        Returns:
            List of agent type identifiers (sorted alphabetically)
        """
        return self.list_available_agents()

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

        This method loads agent configurations from YAML files using
        AgentConfigLoader. It discovers all .agent.yaml files in the
        agents directory and registers them.

        All 8 core agents (Mary, John, Winston, Sally, Bob, Amelia,
        Murat, and Brian) are loaded from their respective YAML files.
        """
        try:
            # Initialize loader
            loader = AgentConfigLoader(self._agents_dir)

            # Discover and load all agents
            agent_names = loader.discover_agents()

            if not agent_names:
                logger.warning(
                    "no_agent_yaml_files_found",
                    agents_dir=str(self._agents_dir)
                )
                return

            # Load each agent configuration
            for agent_name in agent_names:
                try:
                    yaml_config = loader.load_agent(agent_name)
                    self._yaml_agent_configs[agent_name] = yaml_config

                    # Register ClaudeAgent class for this agent
                    self._registry[agent_name] = ClaudeAgent

                    logger.debug(
                        "agent_registered_from_yaml",
                        agent_name=agent_name,
                        name=yaml_config.name,
                        role=yaml_config.role
                    )

                except Exception as e:
                    logger.error(
                        "failed_to_load_agent_yaml",
                        agent_name=agent_name,
                        error=str(e)
                    )
                    # Continue loading other agents even if one fails

            logger.info(
                "builtin_agents_registered",
                count=len(self._yaml_agent_configs),
                agents=list(self._yaml_agent_configs.keys())
            )

        except Exception as e:
            logger.error(
                "failed_to_register_builtin_agents",
                error=str(e)
            )
            # Fall back to empty registry - agents can still be registered manually
            pass

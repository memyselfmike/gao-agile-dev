"""
Agent configuration loader for YAML-based agent definitions.

This module provides the AgentConfigLoader class which loads agent
configurations from YAML files following the BMAD agent schema pattern.
It handles loading both the YAML configuration and the associated persona
markdown files.
"""

import yaml
from pathlib import Path
from typing import List, Dict, Any
import structlog

from .models.agent_config import AgentConfig

logger = structlog.get_logger()


class AgentConfigLoader:
    """
    Load agent configurations from YAML files.

    This class provides functionality to load agent configurations from
    declarative YAML files and their associated persona markdown files.
    It supports both single agent loading and bulk discovery of all
    available agents.

    Attributes:
        agents_dir: Directory containing agent YAML and markdown files

    Example:
        ```python
        loader = AgentConfigLoader(Path("gao_dev/agents"))

        # Load single agent
        amelia = loader.load_agent("amelia")

        # Discover all agents
        agent_names = loader.discover_agents()

        # Load all agents
        configs = loader.load_all_agents()
        ```
    """

    def __init__(self, agents_dir: Path):
        """
        Initialize agent configuration loader.

        Args:
            agents_dir: Path to directory containing agent YAML and .md files
        """
        self.agents_dir = Path(agents_dir)

        if not self.agents_dir.exists():
            logger.warning(
                "agents_directory_not_found",
                agents_dir=str(self.agents_dir)
            )

    def load_agent(self, agent_name: str) -> AgentConfig:
        """
        Load agent configuration by name.

        Loads both the YAML configuration file and the persona markdown file
        for the specified agent. The agent name should match the filename
        without extensions (e.g., "amelia" for "amelia.agent.yaml").

        Args:
            agent_name: Agent name (e.g., "amelia", "john", "winston")

        Returns:
            AgentConfig: Loaded agent configuration with persona

        Raises:
            FileNotFoundError: If YAML or persona file not found
            ValueError: If YAML is invalid or missing required fields
            yaml.YAMLError: If YAML parsing fails

        Example:
            ```python
            loader = AgentConfigLoader(Path("gao_dev/agents"))
            amelia = loader.load_agent("amelia")

            print(f"Loaded {amelia.name} - {amelia.role}")
            print(f"Tools: {amelia.tools}")
            ```
        """
        # Construct paths
        yaml_path = self.agents_dir / f"{agent_name}.agent.yaml"

        # Validate YAML file exists
        if not yaml_path.exists():
            available = ", ".join(self.discover_agents())
            raise FileNotFoundError(
                f"Agent config not found: {yaml_path}. "
                f"Available agents: {available}"
            )

        # Load YAML
        try:
            with open(yaml_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.error(
                "yaml_parse_error",
                agent_name=agent_name,
                yaml_path=str(yaml_path),
                error=str(e)
            )
            raise ValueError(f"Failed to parse YAML for agent '{agent_name}': {e}") from e

        # Validate YAML structure
        if not data or "agent" not in data:
            raise ValueError(
                f"Invalid agent YAML structure in {yaml_path}. "
                f"Must have top-level 'agent' key."
            )

        # Load persona
        persona = self._load_persona(agent_name, data["agent"])

        # Create AgentConfig
        try:
            config = AgentConfig.from_dict(data["agent"], persona)

            logger.info(
                "agent_config_loaded",
                agent_name=agent_name,
                name=config.name,
                role=config.role,
                tools_count=len(config.tools),
                capabilities_count=len(config.capabilities)
            )

            return config

        except (KeyError, ValueError) as e:
            logger.error(
                "agent_config_creation_failed",
                agent_name=agent_name,
                error=str(e)
            )
            raise ValueError(
                f"Failed to create AgentConfig for '{agent_name}': {e}"
            ) from e

    def _load_persona(self, agent_name: str, agent_data: Dict[str, Any]) -> str:
        """
        Load persona text from file or YAML.

        Attempts to load persona from:
        1. persona_file reference in YAML (e.g., "./amelia.md")
        2. Direct persona text in YAML
        3. Default {agent_name}.md file

        Args:
            agent_name: Agent name for fallback lookup
            agent_data: Agent section from YAML

        Returns:
            str: Persona text

        Raises:
            FileNotFoundError: If persona file not found
            ValueError: If no persona source available
        """
        persona_file_ref = agent_data.get("persona_file")

        # Try persona_file reference
        if persona_file_ref:
            # Handle relative paths (e.g., "./amelia.md")
            if persona_file_ref.startswith("./"):
                persona_file_ref = persona_file_ref[2:]

            persona_path = self.agents_dir / persona_file_ref

            if not persona_path.exists():
                raise FileNotFoundError(
                    f"Persona file not found: {persona_path} "
                    f"(referenced in {agent_name}.agent.yaml)"
                )

            try:
                return persona_path.read_text(encoding="utf-8")
            except Exception as e:
                logger.error(
                    "persona_read_error",
                    agent_name=agent_name,
                    persona_path=str(persona_path),
                    error=str(e)
                )
                raise ValueError(
                    f"Failed to read persona file {persona_path}: {e}"
                ) from e

        # Try inline persona
        if "persona" in agent_data:
            return agent_data["persona"]

        # Try default {agent_name}.md file
        default_persona_path = self.agents_dir / f"{agent_name}.md"
        if default_persona_path.exists():
            try:
                return default_persona_path.read_text(encoding="utf-8")
            except Exception as e:
                logger.error(
                    "default_persona_read_error",
                    agent_name=agent_name,
                    persona_path=str(default_persona_path),
                    error=str(e)
                )
                raise ValueError(
                    f"Failed to read default persona file {default_persona_path}: {e}"
                ) from e

        # No persona found
        raise ValueError(
            f"No persona found for agent '{agent_name}'. "
            f"Expected persona_file reference, inline persona, or {agent_name}.md file."
        )

    def discover_agents(self) -> List[str]:
        """
        Discover all agent YAML files in the agents directory.

        Scans the agents directory for files matching the pattern
        "*.agent.yaml" and returns their names (without extensions).

        Returns:
            List[str]: List of agent names (sorted alphabetically)

        Example:
            ```python
            loader = AgentConfigLoader(Path("gao_dev/agents"))
            agents = loader.discover_agents()
            # ['amelia', 'bob', 'brian', 'john', 'mary', 'murat', 'sally', 'winston']
            ```
        """
        if not self.agents_dir.exists():
            logger.warning(
                "agents_directory_not_found_during_discovery",
                agents_dir=str(self.agents_dir)
            )
            return []

        agent_files = list(self.agents_dir.glob("*.agent.yaml"))

        # Extract agent names (remove .agent.yaml extension)
        agent_names = []
        for agent_file in agent_files:
            # agent_file.stem removes .yaml, need to remove .agent too
            name = agent_file.name.replace(".agent.yaml", "")
            agent_names.append(name)

        agent_names_sorted = sorted(agent_names)

        logger.info(
            "agents_discovered",
            agents_dir=str(self.agents_dir),
            count=len(agent_names_sorted),
            agents=agent_names_sorted
        )

        return agent_names_sorted

    def load_all_agents(self) -> Dict[str, AgentConfig]:
        """
        Load all discovered agents.

        Discovers all agent YAML files and loads their configurations.
        Returns a dictionary mapping agent names to their configurations.

        Returns:
            Dict[str, AgentConfig]: Dictionary of agent name to AgentConfig

        Raises:
            ValueError: If any agent fails to load

        Example:
            ```python
            loader = AgentConfigLoader(Path("gao_dev/agents"))
            all_configs = loader.load_all_agents()

            for name, config in all_configs.items():
                print(f"{name}: {config.role}")
            ```
        """
        agent_names = self.discover_agents()
        configs = {}

        for agent_name in agent_names:
            try:
                configs[agent_name] = self.load_agent(agent_name)
            except Exception as e:
                logger.error(
                    "failed_to_load_agent_during_bulk_load",
                    agent_name=agent_name,
                    error=str(e)
                )
                raise ValueError(
                    f"Failed to load agent '{agent_name}' during bulk load: {e}"
                ) from e

        logger.info(
            "all_agents_loaded",
            count=len(configs),
            agents=list(configs.keys())
        )

        return configs

    def validate_agent_file(self, agent_name: str) -> bool:
        """
        Validate that an agent configuration file is valid.

        Attempts to load the agent and returns True if successful,
        False otherwise. Useful for validation without raising exceptions.

        Args:
            agent_name: Agent name to validate

        Returns:
            bool: True if valid, False otherwise

        Example:
            ```python
            loader = AgentConfigLoader(Path("gao_dev/agents"))
            if loader.validate_agent_file("amelia"):
                print("Amelia config is valid")
            ```
        """
        try:
            self.load_agent(agent_name)
            return True
        except Exception as e:
            logger.warning(
                "agent_validation_failed",
                agent_name=agent_name,
                error=str(e)
            )
            return False

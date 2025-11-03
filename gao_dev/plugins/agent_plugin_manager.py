"""Agent plugin manager for GAO-Dev.

This module manages the discovery, loading, and registration of agent plugins.
"""

from typing import List, Dict, Optional
import structlog

from .discovery import PluginDiscovery
from .loader import PluginLoader
from .models import PluginMetadata, PluginType
from .agent_plugin import BaseAgentPlugin
from .exceptions import PluginError
from ..core.factories.agent_factory import AgentFactory
from ..core.models.agent_config import AgentConfig
from ..core.models.prompt_template import PromptTemplate

logger = structlog.get_logger(__name__)


class AgentPluginManager:
    """Manages agent plugins.

    Coordinates plugin discovery, loading, and registration with the AgentFactory.
    Provides a high-level API for working with agent plugins.

    Example:
        ```python
        # Initialize
        manager = AgentPluginManager(
            plugin_discovery=discovery,
            plugin_loader=loader,
            agent_factory=factory
        )

        # Discover and load all agent plugins
        results = manager.load_agent_plugins()
        print(f"Loaded: {results}")

        # Register with AgentFactory
        count = manager.register_agent_plugins()
        print(f"Registered {count} agent plugins")

        # Get all available agents (built-in + plugins)
        agents = manager.get_available_agents()
        print(f"Available agents: {agents}")
        ```
    """

    def __init__(
        self,
        plugin_discovery: PluginDiscovery,
        plugin_loader: PluginLoader,
        agent_factory: AgentFactory,
    ):
        """Initialize agent plugin manager.

        Args:
            plugin_discovery: Plugin discovery instance
            plugin_loader: Plugin loader instance
            agent_factory: Agent factory instance
        """
        self.discovery = plugin_discovery
        self.loader = plugin_loader
        self.factory = agent_factory

    def discover_agent_plugins(self) -> List[PluginMetadata]:
        """Discover all agent plugins from configured directories.

        Returns:
            List of discovered agent plugin metadata (type==AGENT only)
        """
        plugin_dirs = self.discovery.get_plugin_dirs()
        all_plugins = self.discovery.discover_plugins(plugin_dirs)

        # Filter for agent type only
        agent_plugins = [p for p in all_plugins if p.type == PluginType.AGENT]

        logger.info(
            "agent_plugins_discovered",
            total_plugins=len(all_plugins),
            agent_plugins=len(agent_plugins),
        )

        return agent_plugins

    def load_agent_plugins(self) -> Dict[str, str]:
        """Load all discovered agent plugins.

        Returns:
            Dictionary mapping plugin_name to status:
            - "loaded": Successfully loaded
            - "skipped (disabled)": Plugin disabled
            - "failed: <error>": Load error
        """
        agent_plugins = self.discover_agent_plugins()

        if not agent_plugins:
            logger.info("no_agent_plugins_found")
            return {}

        results = self.loader.load_all_enabled(agent_plugins)

        logger.info(
            "agent_plugins_loaded",
            total=len(agent_plugins),
            loaded=sum(1 for s in results.values() if s == "loaded"),
            skipped=sum(1 for s in results.values() if s.startswith("skipped")),
            failed=sum(1 for s in results.values() if s.startswith("failed")),
        )

        return results

    def register_agent_plugins(self) -> int:
        """Register loaded agent plugins with AgentFactory.

        Iterates through all loaded plugins, validates they are agent plugins,
        and registers them with the AgentFactory.

        Returns:
            Number of agent plugins successfully registered

        Raises:
            PluginError: If plugin is invalid (doesn't extend BaseAgentPlugin)
        """
        count = 0

        for plugin_name in self.loader.list_loaded_plugins():
            try:
                plugin = self.loader.get_loaded_plugin(plugin_name)
                metadata = self.loader.get_plugin_metadata(plugin_name)

                # Only process agent plugins
                if metadata.type != PluginType.AGENT:
                    logger.debug(
                        "skipping_non_agent_plugin",
                        plugin_name=plugin_name,
                        plugin_type=metadata.type.value,
                    )
                    continue

                # Verify it's an agent plugin
                if not isinstance(plugin, BaseAgentPlugin):
                    logger.warning(
                        "agent_plugin_invalid_type",
                        plugin_name=plugin_name,
                        plugin_type=type(plugin).__name__,
                        expected_type="BaseAgentPlugin",
                    )
                    continue

                # Validate agent class
                plugin.validate_agent_class()

                # Get agent details
                agent_class = plugin.get_agent_class()
                agent_name = plugin.get_agent_name()
                agent_metadata = plugin.get_agent_metadata()

                # Register with factory
                self.factory.register_plugin_agent(agent_name, agent_class)

                logger.info(
                    "agent_plugin_registered",
                    plugin_name=plugin_name,
                    agent_name=agent_name,
                    agent_role=agent_metadata.role,
                )

                count += 1

            except Exception as e:
                logger.error(
                    "agent_plugin_registration_failed",
                    plugin_name=plugin_name,
                    error=str(e),
                    exc_info=True,
                )

        logger.info("agent_plugin_registration_complete", registered_count=count)

        return count

    def get_available_agents(self) -> List[str]:
        """Get list of all available agents (built-in + plugins).

        Returns:
            List of agent names (sorted)
        """
        return sorted(self.factory.list_agents())

    def discover_load_and_register(self) -> Dict[str, any]:
        """Convenience method: discover, load, and register all agent plugins.

        Returns:
            Dictionary with operation results:
            - discovered: Number of agent plugins discovered
            - load_results: Dictionary of load results per plugin
            - registered: Number of plugins registered
            - available_agents: List of all available agents
        """
        # Discover
        discovered = self.discover_agent_plugins()

        # Load
        load_results = self.load_agent_plugins()

        # Register
        registered = self.register_agent_plugins()

        # Get available agents
        available_agents = self.get_available_agents()

        results = {
            "discovered": len(discovered),
            "load_results": load_results,
            "registered": registered,
            "available_agents": available_agents,
        }

        logger.info(
            "agent_plugin_setup_complete",
            discovered=results["discovered"],
            registered=results["registered"],
            total_agents=len(available_agents),
        )

        return results

    def load_agent_definitions_from_plugins(self) -> List[AgentConfig]:
        """Load agent definitions from all loaded plugins.

        Calls get_agent_definitions() on each loaded agent plugin and
        collects all returned AgentConfig instances.

        Returns:
            List of AgentConfig instances from all plugins
        """
        agent_configs = []

        for plugin_name in self.loader.list_loaded_plugins():
            try:
                plugin = self.loader.get_loaded_plugin(plugin_name)
                metadata = self.loader.get_plugin_metadata(plugin_name)

                # Only process agent plugins
                if metadata.type != PluginType.AGENT:
                    continue

                if not isinstance(plugin, BaseAgentPlugin):
                    continue

                # Get agent definitions from plugin
                configs = plugin.get_agent_definitions()
                if configs:
                    agent_configs.extend(configs)
                    logger.info(
                        "loaded_agent_definitions_from_plugin",
                        plugin_name=plugin_name,
                        count=len(configs),
                    )

            except Exception as e:
                logger.error(
                    "failed_to_load_agent_definitions_from_plugin",
                    plugin_name=plugin_name,
                    error=str(e),
                    exc_info=True,
                )

        logger.info("agent_definitions_loaded_from_plugins", total_configs=len(agent_configs))

        return agent_configs

    def load_prompt_templates_from_plugins(self) -> List[PromptTemplate]:
        """Load prompt templates from all loaded plugins.

        Calls get_prompt_templates() on each loaded agent plugin and
        collects all returned PromptTemplate instances.

        Returns:
            List of PromptTemplate instances from all plugins
        """
        prompt_templates = []

        for plugin_name in self.loader.list_loaded_plugins():
            try:
                plugin = self.loader.get_loaded_plugin(plugin_name)
                metadata = self.loader.get_plugin_metadata(plugin_name)

                # Only process agent plugins
                if metadata.type != PluginType.AGENT:
                    continue

                if not isinstance(plugin, BaseAgentPlugin):
                    continue

                # Get prompt templates from plugin
                templates = plugin.get_prompt_templates()
                if templates:
                    prompt_templates.extend(templates)
                    logger.info(
                        "loaded_prompt_templates_from_plugin",
                        plugin_name=plugin_name,
                        count=len(templates),
                    )

            except Exception as e:
                logger.error(
                    "failed_to_load_prompt_templates_from_plugin",
                    plugin_name=plugin_name,
                    error=str(e),
                    exc_info=True,
                )

        logger.info("prompt_templates_loaded_from_plugins", total_templates=len(prompt_templates))

        return prompt_templates

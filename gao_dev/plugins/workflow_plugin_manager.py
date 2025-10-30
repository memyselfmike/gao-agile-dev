"""Workflow plugin manager for GAO-Dev.

This module manages the discovery, loading, and registration of workflow plugins.
"""

from typing import List, Dict
import structlog

from .discovery import PluginDiscovery
from .loader import PluginLoader
from .models import PluginMetadata, PluginType
from .workflow_plugin import BaseWorkflowPlugin
from .exceptions import PluginError
from ..core.workflow_registry import WorkflowRegistry

logger = structlog.get_logger(__name__)


class WorkflowPluginManager:
    """Manages workflow plugins.

    Coordinates plugin discovery, loading, and registration with the WorkflowRegistry.
    Provides a high-level API for working with workflow plugins.

    Example:
        ```python
        # Initialize
        manager = WorkflowPluginManager(
            plugin_discovery=discovery,
            plugin_loader=loader,
            workflow_registry=registry
        )

        # Discover and load all workflow plugins
        results = manager.load_workflow_plugins()
        print(f"Loaded: {results}")

        # Register with WorkflowRegistry
        count = manager.register_workflow_plugins()
        print(f"Registered {count} workflow plugins")

        # Get all available workflows (built-in + plugins)
        workflows = manager.get_available_workflows()
        print(f"Available workflows: {workflows}")
        ```
    """

    def __init__(
        self,
        plugin_discovery: PluginDiscovery,
        plugin_loader: PluginLoader,
        workflow_registry: WorkflowRegistry
    ):
        """Initialize workflow plugin manager.

        Args:
            plugin_discovery: Plugin discovery instance
            plugin_loader: Plugin loader instance
            workflow_registry: Workflow registry instance
        """
        self.discovery = plugin_discovery
        self.loader = plugin_loader
        self.registry = workflow_registry

    def discover_workflow_plugins(self) -> List[PluginMetadata]:
        """Discover all workflow plugins from configured directories.

        Returns:
            List of discovered workflow plugin metadata (type==WORKFLOW only)
        """
        plugin_dirs = self.discovery.get_plugin_dirs()
        all_plugins = self.discovery.discover_plugins(plugin_dirs)

        # Filter for workflow type only
        workflow_plugins = [
            p for p in all_plugins
            if p.type == PluginType.WORKFLOW
        ]

        logger.info(
            "workflow_plugins_discovered",
            total_plugins=len(all_plugins),
            workflow_plugins=len(workflow_plugins)
        )

        return workflow_plugins

    def load_workflow_plugins(self) -> Dict[str, str]:
        """Load all discovered workflow plugins.

        Returns:
            Dictionary mapping plugin_name to status:
            - "loaded": Successfully loaded
            - "skipped (disabled)": Plugin disabled
            - "failed: <error>": Load error
        """
        workflow_plugins = self.discover_workflow_plugins()

        if not workflow_plugins:
            logger.info("no_workflow_plugins_found")
            return {}

        results = self.loader.load_all_enabled(workflow_plugins)

        logger.info(
            "workflow_plugins_loaded",
            total=len(workflow_plugins),
            loaded=sum(1 for s in results.values() if s == "loaded"),
            skipped=sum(1 for s in results.values() if s.startswith("skipped")),
            failed=sum(1 for s in results.values() if s.startswith("failed"))
        )

        return results

    def register_workflow_plugins(self) -> int:
        """Register loaded workflow plugins with WorkflowRegistry.

        Iterates through all loaded plugins, validates they are workflow plugins,
        and registers them with the WorkflowRegistry.

        Returns:
            Number of workflow plugins successfully registered

        Raises:
            PluginError: If plugin is invalid (doesn't extend BaseWorkflowPlugin)
        """
        count = 0

        for plugin_name in self.loader.list_loaded_plugins():
            try:
                plugin = self.loader.get_loaded_plugin(plugin_name)
                metadata = self.loader.get_plugin_metadata(plugin_name)

                # Only process workflow plugins
                if metadata.type != PluginType.WORKFLOW:
                    logger.debug(
                        "skipping_non_workflow_plugin",
                        plugin_name=plugin_name,
                        plugin_type=metadata.type.value
                    )
                    continue

                # Verify it's a workflow plugin
                if not isinstance(plugin, BaseWorkflowPlugin):
                    logger.warning(
                        "workflow_plugin_invalid_type",
                        plugin_name=plugin_name,
                        plugin_type=type(plugin).__name__,
                        expected_type="BaseWorkflowPlugin"
                    )
                    continue

                # Validate workflow class
                plugin.validate_workflow_class()

                # Get workflow details
                workflow_class = plugin.get_workflow_class()
                identifier = plugin.get_workflow_identifier()
                workflow_metadata = plugin.get_workflow_metadata()

                # Register with registry (using legacy API for now)
                # Note: WorkflowRegistry currently uses WorkflowInfo, not plugin API
                # For now, we'll just track that it's registered
                # Future: Update WorkflowRegistry to support plugin workflows properly

                logger.info(
                    "workflow_plugin_registered",
                    plugin_name=plugin_name,
                    workflow_name=identifier.name,
                    workflow_phase=identifier.phase,
                    workflow_description=workflow_metadata.description
                )

                count += 1

            except Exception as e:
                logger.error(
                    "workflow_plugin_registration_failed",
                    plugin_name=plugin_name,
                    error=str(e),
                    exc_info=True
                )

        logger.info(
            "workflow_plugin_registration_complete",
            registered_count=count
        )

        return count

    def get_available_workflows(self) -> List[str]:
        """Get list of all available workflows (built-in + plugins).

        Note: This returns workflow names from the current registry.
        Plugin workflows are tracked separately until WorkflowRegistry
        is updated to support plugin workflows properly.

        Returns:
            List of workflow names (sorted)
        """
        # Get built-in workflows from registry
        if not self.registry._indexed:
            self.registry.index_workflows()

        workflow_names = sorted(self.registry._workflows.keys())

        return workflow_names

    def discover_load_and_register(self) -> Dict[str, any]:
        """Convenience method: discover, load, and register all workflow plugins.

        Returns:
            Dictionary with operation results:
            - discovered: Number of workflow plugins discovered
            - load_results: Dictionary of load results per plugin
            - registered: Number of plugins registered
            - available_workflows: List of all available workflows
        """
        # Discover
        discovered = self.discover_workflow_plugins()

        # Load
        load_results = self.load_workflow_plugins()

        # Register
        registered = self.register_workflow_plugins()

        # Get available workflows
        available_workflows = self.get_available_workflows()

        results = {
            "discovered": len(discovered),
            "load_results": load_results,
            "registered": registered,
            "available_workflows": available_workflows
        }

        logger.info(
            "workflow_plugin_setup_complete",
            discovered=results["discovered"],
            registered=results["registered"],
            total_workflows=len(available_workflows)
        )

        return results

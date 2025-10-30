"""Plugin implementation for MY_PLUGIN.

Replace MY_PLUGIN, MyAgent, MyAgentPlugin with your names.
"""

from gao_dev.plugins import BaseAgentPlugin, AgentMetadata
from .agent import MyAgent  # Replace with your agent class


class MyAgentPlugin(BaseAgentPlugin):
    """Plugin that provides MyAgent.

    This class connects your custom agent to GAO-Dev's plugin system.
    """

    def get_agent_class(self):
        """Return the agent class to register.

        Returns:
            Type[IAgent]: Your agent class
        """
        return MyAgent

    def get_agent_name(self):
        """Return unique agent name.

        Returns:
            str: Agent name (should match agent.name)
        """
        return "MyAgent"  # Replace with your agent name

    def get_agent_metadata(self):
        """Return agent metadata.

        Returns:
            AgentMetadata: Metadata describing your agent
        """
        return AgentMetadata(
            name="MyAgent",  # Replace with your agent name
            role="My Role",  # Replace with agent role
            description="Brief description of what this agent does",  # Customize
            capabilities=["capability1", "capability2"],  # List capabilities
            tools=["Read", "Write", "Grep"],  # List required tools
            model="claude-sonnet-4-5-20250929"  # Claude model to use
        )

    def initialize(self):
        """Initialize plugin (optional).

        Called after plugin is loaded, before it's used.
        Use for setup: connections, resources, configuration.

        Returns:
            bool: True if successful, False to abort loading
        """
        # Add initialization code here
        return True

    def cleanup(self):
        """Cleanup plugin (optional).

        Called before plugin is unloaded.
        Use for teardown: close connections, release resources.
        """
        # Add cleanup code here
        pass

    def register_hooks(self):
        """Register lifecycle hooks (optional).

        Called after initialization. Register hooks to respond
        to lifecycle events.
        """
        if self._hook_manager:
            from gao_dev.core import HookEventType

            # Example: Register workflow start hook
            # self._hook_manager.register_hook(
            #     HookEventType.WORKFLOW_START,
            #     self._on_workflow_start,
            #     priority=100,
            #     plugin_name="my-plugin"
            # )
            pass

    def _on_workflow_start(self, event_data):
        """Handle workflow start event (example).

        Args:
            event_data: Dictionary with event data
        """
        # Add hook handler code here
        pass

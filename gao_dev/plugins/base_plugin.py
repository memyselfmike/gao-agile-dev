"""Base plugin class with lifecycle hooks."""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from gao_dev.core.hook_manager import HookManager


class BasePlugin:
    """Base class for plugins (optional but recommended).

    Plugins can inherit from this class to get default implementations
    of lifecycle hooks. Alternatively, plugins can implement these methods
    directly without inheriting from BasePlugin.

    Lifecycle:
        1. __init__() - Plugin instantiation
        2. initialize() - Called after instantiation, before use
        3. [Plugin is active and can be used]
        4. cleanup() - Called before unloading

    Example:
        ```python
        from gao_dev.plugins.base_plugin import BasePlugin

        class MyPlugin(BasePlugin):
            def initialize(self) -> bool:
                # Setup resources
                self.connection = create_connection()
                return True

            def register_hooks(self) -> None:
                # Register lifecycle hooks
                if self._hook_manager:
                    from gao_dev.core import HookEventType
                    self._hook_manager.register_hook(
                        HookEventType.WORKFLOW_START,
                        self._on_workflow_start,
                        priority=100
                    )

            def _on_workflow_start(self, event_data):
                # Handle workflow start event
                print("Workflow started!")

            def cleanup(self) -> None:
                # Release resources
                if hasattr(self, 'connection'):
                    self.connection.close()

            def my_plugin_method(self):
                # Plugin functionality
                pass
        ```
    """

    def __init__(self):
        """Initialize base plugin."""
        self._hook_manager: Optional["HookManager"] = None

    def initialize(self) -> bool:
        """Initialize plugin after loading.

        Called immediately after plugin instantiation. Use this method to:
        - Set up resources (connections, file handles, etc.)
        - Initialize state
        - Validate configuration
        - Perform startup checks

        Returns:
            True if initialization successful, False to abort loading

        Raises:
            Any exception will abort plugin loading with PluginLoadError

        Note:
            This method is optional. If not implemented or returns True,
            plugin loading continues. If returns False or raises exception,
            plugin loading is aborted.
        """
        return True

    def cleanup(self) -> None:
        """Cleanup plugin before unloading.

        Called before plugin is removed from registry. Use this method to:
        - Release resources (close connections, files, etc.)
        - Save state
        - Cancel pending operations
        - Cleanup temporary files

        Note:
            This method is optional. Exceptions during cleanup are logged
            but don't prevent plugin unloading.
        """
        pass

    def set_hook_manager(self, hook_manager: "HookManager") -> None:
        """Set the hook manager for this plugin.

        Called by the plugin loader to provide access to the hook system.
        Plugins can use this to register lifecycle hooks.

        Args:
            hook_manager: The HookManager instance to use

        Example:
            ```python
            # Called automatically by PluginLoader
            plugin.set_hook_manager(hook_manager)
            ```
        """
        self._hook_manager = hook_manager

    def register_hooks(self) -> None:
        """Register lifecycle hooks for this plugin.

        Override this method to register hooks that will be called at
        specific lifecycle events. This is called automatically after
        plugin initialization.

        Example:
            ```python
            def register_hooks(self) -> None:
                if self._hook_manager:
                    from gao_dev.core import HookEventType

                    self._hook_manager.register_hook(
                        HookEventType.WORKFLOW_START,
                        self._on_workflow_start,
                        priority=100,
                        plugin_name="my-plugin"
                    )

            def _on_workflow_start(self, event_data):
                # Handle workflow start
                workflow_id = event_data.get("workflow_id")
                print(f"Workflow {workflow_id} started")
            ```

        Note:
            This method is optional. Default implementation does nothing.
            Hooks are automatically unregistered during plugin cleanup.
        """
        pass

    def unregister_hooks(self) -> None:
        """Unregister all hooks registered by this plugin.

        Called automatically during plugin cleanup to ensure no orphaned
        hooks remain in the system.

        Note:
            Default implementation automatically removes all hooks
            registered by this plugin. Override only if you need
            custom cleanup logic.
        """
        if self._hook_manager and hasattr(self, '__class__'):
            plugin_name = getattr(self, 'name', self.__class__.__name__)
            self._hook_manager.unregister_plugin_hooks(plugin_name)

"""Base plugin class with lifecycle hooks."""


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

            def cleanup(self) -> None:
                # Release resources
                if hasattr(self, 'connection'):
                    self.connection.close()

            def my_plugin_method(self):
                # Plugin functionality
                pass
        ```
    """

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

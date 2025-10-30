"""Test plugin with lifecycle hooks."""

from gao_dev.plugins.base_plugin import BasePlugin


class LifecycleTestPlugin(BasePlugin):
    """Test plugin that tracks lifecycle method calls."""

    def __init__(self):
        """Initialize plugin."""
        self.initialized = False
        self.cleaned_up = False
        self.init_count = 0
        self.cleanup_count = 0

    def initialize(self) -> bool:
        """Initialize hook - tracks calls."""
        self.initialized = True
        self.init_count += 1
        return True

    def cleanup(self) -> None:
        """Cleanup hook - tracks calls."""
        self.cleaned_up = True
        self.cleanup_count += 1

    def do_something(self) -> str:
        """Test method."""
        return "lifecycle plugin working"

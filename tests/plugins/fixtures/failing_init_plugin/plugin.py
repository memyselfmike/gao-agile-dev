"""Test plugin that fails initialization."""

from gao_dev.plugins.base_plugin import BasePlugin


class FailingInitPlugin(BasePlugin):
    """Test plugin that fails to initialize."""

    def initialize(self) -> bool:
        """Initialize hook - returns False."""
        return False

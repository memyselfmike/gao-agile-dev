"""Tests for BasePlugin hook integration."""

import pytest
from typing import Dict, Any

from gao_dev.plugins.base_plugin import BasePlugin
from gao_dev.core.hook_manager import HookManager
from gao_dev.core.models.hook import HookEventType


# Test Fixtures

@pytest.fixture
def hook_manager():
    """Create HookManager instance."""
    return HookManager()


# Plugin Classes for Testing

class SamplePluginWithHooks(BasePlugin):
    """Sample plugin with hook registration for testing."""

    def __init__(self):
        super().__init__()
        self.name = "test-plugin"
        self.workflow_starts = []

    def register_hooks(self) -> None:
        """Register test hooks."""
        if self._hook_manager:
            self._hook_manager.register_hook(
                HookEventType.WORKFLOW_START,
                self._on_workflow_start,
                priority=100,
                plugin_name=self.name,
            )

    def _on_workflow_start(self, event_data: Dict[str, Any]) -> None:
        """Handle workflow start event."""
        self.workflow_starts.append(event_data)


class MinimalPluginSample(BasePlugin):
    """Minimal plugin without hook registration for testing."""

    def __init__(self):
        super().__init__()
        self.name = "minimal-plugin"


# Test BasePlugin Hook Integration

class TestBasePluginHooks:
    """Tests for BasePlugin hook integration."""

    def test_base_plugin_has_hook_manager_attribute(self):
        """Test that BasePlugin initializes _hook_manager."""
        plugin = BasePlugin()
        assert hasattr(plugin, "_hook_manager")
        assert plugin._hook_manager is None

    def test_set_hook_manager(self, hook_manager):
        """Test setting hook manager on plugin."""
        plugin = BasePlugin()
        plugin.set_hook_manager(hook_manager)

        assert plugin._hook_manager is hook_manager

    def test_register_hooks_default_implementation(self):
        """Test that default register_hooks does nothing."""
        plugin = BasePlugin()
        # Should not raise
        plugin.register_hooks()

    def test_unregister_hooks_default_implementation(self, hook_manager):
        """Test that default unregister_hooks works."""
        plugin = BasePlugin()
        plugin.set_hook_manager(hook_manager)

        # Should not raise even with no hooks registered
        plugin.unregister_hooks()


# Test Plugin Hook Registration

class TestPluginHookRegistration:
    """Tests for plugin hook registration."""

    @pytest.mark.asyncio
    async def test_plugin_can_register_hooks(self, hook_manager):
        """Test that plugin can register hooks."""
        plugin = SamplePluginWithHooks()
        plugin.set_hook_manager(hook_manager)
        plugin.register_hooks()

        # Verify hook was registered
        hooks = hook_manager.get_registered_hooks(HookEventType.WORKFLOW_START)
        assert len(hooks) == 1
        assert hooks[0].plugin_name == "test-plugin"

    @pytest.mark.asyncio
    async def test_plugin_hook_receives_events(self, hook_manager):
        """Test that plugin hook receives events."""
        plugin = SamplePluginWithHooks()
        plugin.set_hook_manager(hook_manager)
        plugin.register_hooks()

        # Fire event
        event_data = {"workflow_id": "test-workflow"}
        await hook_manager.execute_hooks(HookEventType.WORKFLOW_START, event_data)

        # Verify plugin received event
        assert len(plugin.workflow_starts) == 1
        assert plugin.workflow_starts[0] == event_data

    @pytest.mark.asyncio
    async def test_multiple_plugins_can_register_hooks(self, hook_manager):
        """Test that multiple plugins can register hooks for same event."""
        plugin1 = SamplePluginWithHooks()
        plugin1.name = "plugin1"
        plugin1.set_hook_manager(hook_manager)
        plugin1.register_hooks()

        plugin2 = SamplePluginWithHooks()
        plugin2.name = "plugin2"
        plugin2.set_hook_manager(hook_manager)
        plugin2.register_hooks()

        # Fire event
        event_data = {"workflow_id": "test-workflow"}
        await hook_manager.execute_hooks(HookEventType.WORKFLOW_START, event_data)

        # Both plugins should receive event
        assert len(plugin1.workflow_starts) == 1
        assert len(plugin2.workflow_starts) == 1


# Test Plugin Hook Unregistration

class TestPluginHookUnregistration:
    """Tests for plugin hook unregistration."""

    def test_unregister_plugin_hooks(self, hook_manager):
        """Test unregistering all hooks from a plugin."""
        plugin = SamplePluginWithHooks()
        plugin.set_hook_manager(hook_manager)
        plugin.register_hooks()

        # Verify hooks registered
        hooks = hook_manager.get_registered_hooks(HookEventType.WORKFLOW_START)
        assert len(hooks) == 1

        # Unregister plugin hooks
        plugin.unregister_hooks()

        # Verify hooks removed
        hooks = hook_manager.get_registered_hooks(HookEventType.WORKFLOW_START)
        assert len(hooks) == 0

    @pytest.mark.asyncio
    async def test_unregister_only_plugin_hooks(self, hook_manager):
        """Test that unregister only removes hooks from specific plugin."""
        plugin1 = SamplePluginWithHooks()
        plugin1.name = "plugin1"
        plugin1.set_hook_manager(hook_manager)
        plugin1.register_hooks()

        plugin2 = SamplePluginWithHooks()
        plugin2.name = "plugin2"
        plugin2.set_hook_manager(hook_manager)
        plugin2.register_hooks()

        # Unregister plugin1 hooks
        plugin1.unregister_hooks()

        # Plugin1 hooks removed, plugin2 hooks remain
        hooks = hook_manager.get_registered_hooks(HookEventType.WORKFLOW_START)
        assert len(hooks) == 1
        assert hooks[0].plugin_name == "plugin2"

        # Verify plugin2 still receives events
        event_data = {"workflow_id": "test"}
        await hook_manager.execute_hooks(HookEventType.WORKFLOW_START, event_data)
        assert len(plugin2.workflow_starts) == 1

    def test_unregister_hooks_without_hook_manager(self):
        """Test unregister when hook manager not set."""
        plugin = SamplePluginWithHooks()
        # Should not raise even without hook manager
        plugin.unregister_hooks()


# Test Plugin Lifecycle Integration

class TestPluginLifecycleIntegration:
    """Tests for plugin lifecycle with hooks."""

    @pytest.mark.asyncio
    async def test_full_plugin_lifecycle_with_hooks(self, hook_manager):
        """Test complete plugin lifecycle including hooks."""
        plugin = SamplePluginWithHooks()

        # 1. Initialize plugin
        assert plugin.initialize() is True

        # 2. Set hook manager
        plugin.set_hook_manager(hook_manager)

        # 3. Register hooks
        plugin.register_hooks()

        # 4. Verify hooks work
        event_data = {"workflow_id": "test"}
        await hook_manager.execute_hooks(HookEventType.WORKFLOW_START, event_data)
        assert len(plugin.workflow_starts) == 1

        # 5. Cleanup (including unregister hooks)
        plugin.unregister_hooks()
        plugin.cleanup()

        # 6. Verify hooks removed
        hooks = hook_manager.get_registered_hooks(HookEventType.WORKFLOW_START)
        assert len(hooks) == 0

    def test_plugin_without_hooks_still_works(self, hook_manager):
        """Test that plugin without hooks still functions."""
        plugin = MinimalPluginSample()

        # Full lifecycle should work without errors
        assert plugin.initialize() is True
        plugin.set_hook_manager(hook_manager)
        plugin.register_hooks()  # Does nothing
        plugin.unregister_hooks()  # Does nothing
        plugin.cleanup()


# Integration Test

class TestHookSystemIntegration:
    """Integration tests for complete hook system."""

    @pytest.mark.asyncio
    async def test_complete_hook_system_workflow(self, hook_manager):
        """Test complete workflow of hook system."""
        # Create multiple plugins
        plugins = []
        for i in range(3):
            plugin = SamplePluginWithHooks()
            plugin.name = f"plugin-{i}"
            plugin.set_hook_manager(hook_manager)
            plugin.register_hooks()
            plugins.append(plugin)

        # Fire events
        for workflow_num in range(5):
            await hook_manager.execute_hooks(
                HookEventType.WORKFLOW_START,
                {"workflow_id": f"workflow-{workflow_num}"},
            )

        # Verify all plugins received all events
        for plugin in plugins:
            assert len(plugin.workflow_starts) == 5

        # Cleanup plugins
        for plugin in plugins:
            plugin.unregister_hooks()

        # Verify all hooks removed
        hooks = hook_manager.get_registered_hooks()
        assert len(hooks) == 0

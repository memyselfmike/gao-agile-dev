"""Tests for ChecklistPluginManager."""

from pathlib import Path
from typing import Dict, List

import pytest

from gao_dev.core.checklists.plugin_manager import ChecklistPluginManager
from gao_dev.plugins.checklist_plugin import ChecklistPlugin


class MockChecklistPlugin(ChecklistPlugin):
    """Mock checklist plugin for testing."""

    def __init__(
        self,
        name: str = "mock-plugin",
        priority: int = 0,
        directories: List[Path] = None,
    ):
        super().__init__()
        self._name = name
        self._priority = priority
        self._directories = directories or [Path(f"checklists/{name}")]

    def get_checklist_directories(self) -> List[Path]:
        return self._directories

    def get_checklist_metadata(self) -> Dict:
        return {
            "name": self._name,
            "version": "1.0.0",
            "author": "Test Author",
            "priority": self._priority,
        }


def test_plugin_manager_initialization():
    """Test ChecklistPluginManager initialization."""
    manager = ChecklistPluginManager()
    assert manager is not None
    assert len(manager.plugins) == 0


def test_register_plugin():
    """Test manually registering a plugin."""
    manager = ChecklistPluginManager()
    plugin = MockChecklistPlugin(name="test-plugin", priority=50)

    manager.register_plugin(plugin)

    assert "test-plugin" in manager.plugins
    assert manager.get_plugin("test-plugin") == plugin


def test_register_plugin_with_custom_metadata():
    """Test registering plugin with custom metadata."""
    manager = ChecklistPluginManager()
    plugin = MockChecklistPlugin(name="custom-plugin", priority=100)

    custom_metadata = {
        "name": "custom-plugin",
        "version": "2.0.0",
        "author": "Custom Author",
        "priority": 100,
        "dependencies": ["dep1"],
    }

    manager.register_plugin(plugin, metadata=custom_metadata)

    assert "custom-plugin" in manager.plugins
    retrieved_metadata = manager._plugin_metadata["custom-plugin"]
    assert retrieved_metadata["version"] == "2.0.0"
    assert retrieved_metadata["dependencies"] == ["dep1"]


def test_get_plugin():
    """Test getting plugin by name."""
    manager = ChecklistPluginManager()
    plugin1 = MockChecklistPlugin(name="plugin1")
    plugin2 = MockChecklistPlugin(name="plugin2")

    manager.register_plugin(plugin1)
    manager.register_plugin(plugin2)

    assert manager.get_plugin("plugin1") == plugin1
    assert manager.get_plugin("plugin2") == plugin2
    assert manager.get_plugin("nonexistent") is None


def test_get_all_checklist_directories():
    """Test getting all checklist directories sorted by priority."""
    manager = ChecklistPluginManager()

    # Register plugins with different priorities
    plugin_low = MockChecklistPlugin(
        name="low-priority", priority=10, directories=[Path("checklists/low")]
    )
    plugin_high = MockChecklistPlugin(
        name="high-priority", priority=100, directories=[Path("checklists/high")]
    )
    plugin_medium = MockChecklistPlugin(
        name="medium-priority", priority=50, directories=[Path("checklists/medium")]
    )

    manager.register_plugin(plugin_low)
    manager.register_plugin(plugin_high)
    manager.register_plugin(plugin_medium)

    directories = manager.get_all_checklist_directories()

    # Should be sorted by priority descending (highest first)
    assert len(directories) == 3
    assert directories[0] == (Path("checklists/high"), "high-priority", 100)
    assert directories[1] == (Path("checklists/medium"), "medium-priority", 50)
    assert directories[2] == (Path("checklists/low"), "low-priority", 10)


def test_get_all_checklist_directories_multiple_dirs():
    """Test plugin with multiple directories."""
    manager = ChecklistPluginManager()

    plugin = MockChecklistPlugin(
        name="multi-dir",
        priority=50,
        directories=[Path("dir1"), Path("dir2"), Path("dir3")],
    )

    manager.register_plugin(plugin)
    directories = manager.get_all_checklist_directories()

    assert len(directories) == 3
    assert all(plugin_name == "multi-dir" for _, plugin_name, _ in directories)
    assert all(priority == 50 for _, _, priority in directories)


def test_validate_dependencies_success():
    """Test dependency validation when all dependencies satisfied."""
    manager = ChecklistPluginManager()

    # Register base plugin
    base_plugin = MockChecklistPlugin(name="base-plugin")
    manager.register_plugin(base_plugin)

    # Register dependent plugin
    dependent_plugin = MockChecklistPlugin(name="dependent-plugin")
    dependent_metadata = {
        "name": "dependent-plugin",
        "version": "1.0.0",
        "author": "Test",
        "priority": 0,
        "dependencies": ["base-plugin"],
    }
    manager.register_plugin(dependent_plugin, metadata=dependent_metadata)

    # Validation should succeed
    assert manager.validate_dependencies() is True


def test_validate_dependencies_failure():
    """Test dependency validation when dependencies missing."""
    manager = ChecklistPluginManager()

    # Register plugin with missing dependency
    plugin = MockChecklistPlugin(name="dependent-plugin")
    metadata = {
        "name": "dependent-plugin",
        "version": "1.0.0",
        "author": "Test",
        "priority": 0,
        "dependencies": ["missing-plugin"],
    }
    manager.register_plugin(plugin, metadata=metadata)

    # Validation should fail
    assert manager.validate_dependencies() is False


def test_validate_dependencies_no_deps():
    """Test dependency validation with no dependencies."""
    manager = ChecklistPluginManager()

    plugin = MockChecklistPlugin(name="independent-plugin")
    manager.register_plugin(plugin)

    # Should succeed (no dependencies)
    assert manager.validate_dependencies() is True


def test_list_plugins():
    """Test listing all registered plugins."""
    manager = ChecklistPluginManager()

    plugin1 = MockChecklistPlugin(name="plugin1", priority=10)
    plugin2 = MockChecklistPlugin(name="plugin2", priority=20)

    manager.register_plugin(plugin1)
    manager.register_plugin(plugin2)

    plugins = manager.list_plugins()

    assert len(plugins) == 2
    plugin_names = [name for name, _ in plugins]
    assert "plugin1" in plugin_names
    assert "plugin2" in plugin_names


def test_enable_disable_plugin():
    """Test enabling and disabling plugins."""
    manager = ChecklistPluginManager()

    plugin = MockChecklistPlugin(name="test-plugin")
    manager.register_plugin(plugin)

    # Should be enabled by default
    assert manager.is_plugin_enabled("test-plugin") is True

    # Disable plugin
    assert manager.disable_plugin("test-plugin") is True
    assert manager.is_plugin_enabled("test-plugin") is False

    # Enable plugin
    assert manager.enable_plugin("test-plugin") is True
    assert manager.is_plugin_enabled("test-plugin") is True


def test_enable_disable_nonexistent_plugin():
    """Test enabling/disabling nonexistent plugin."""
    manager = ChecklistPluginManager()

    assert manager.enable_plugin("nonexistent") is False
    assert manager.disable_plugin("nonexistent") is False
    assert manager.is_plugin_enabled("nonexistent") is False


def test_cleanup():
    """Test cleanup method."""
    manager = ChecklistPluginManager()

    # Track cleanup calls
    cleanup_called = []

    class TrackingPlugin(MockChecklistPlugin):
        def cleanup(self):
            cleanup_called.append(self._name)

    plugin1 = TrackingPlugin(name="plugin1")
    plugin2 = TrackingPlugin(name="plugin2")

    manager.register_plugin(plugin1)
    manager.register_plugin(plugin2)

    # Call cleanup
    manager.cleanup()

    # Both plugins should be cleaned up
    assert "plugin1" in cleanup_called
    assert "plugin2" in cleanup_called

    # Manager should be empty
    assert len(manager.plugins) == 0
    assert len(manager._plugin_priority) == 0
    assert len(manager._plugin_metadata) == 0


def test_plugin_priority_ordering():
    """Test that plugins are ordered correctly by priority."""
    manager = ChecklistPluginManager()

    # Register plugins in random order
    manager.register_plugin(MockChecklistPlugin(name="p3", priority=30))
    manager.register_plugin(MockChecklistPlugin(name="p1", priority=10))
    manager.register_plugin(MockChecklistPlugin(name="p5", priority=50))
    manager.register_plugin(MockChecklistPlugin(name="p2", priority=20))

    directories = manager.get_all_checklist_directories()

    # Should be sorted by priority descending
    priorities = [priority for _, _, priority in directories]
    assert priorities == [50, 30, 20, 10]


def test_register_plugin_without_name():
    """Test registering plugin without name in metadata."""
    manager = ChecklistPluginManager()

    plugin = MockChecklistPlugin(name="test")
    metadata = {
        "version": "1.0.0",
        "author": "Test",
        # Missing 'name' field
    }

    with pytest.raises(ValueError, match="must include 'name' field"):
        manager.register_plugin(plugin, metadata=metadata)


def test_discover_plugins_no_dir():
    """Test discovery when plugins directory doesn't exist."""
    manager = ChecklistPluginManager(plugins_dir=Path("nonexistent"))
    plugins = manager.discover_plugins()

    assert len(plugins) == 0


def test_discover_plugins_none_dir():
    """Test discovery when no plugins directory configured."""
    manager = ChecklistPluginManager(plugins_dir=None)
    plugins = manager.discover_plugins()

    assert len(plugins) == 0

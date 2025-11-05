"""Integration tests for ChecklistLoader with plugin support."""

import tempfile
from pathlib import Path
from typing import Dict, List

import pytest

from gao_dev.core.checklists.checklist_loader import ChecklistLoader
from gao_dev.core.checklists.plugin_manager import ChecklistPluginManager
from gao_dev.plugins.checklist_plugin import ChecklistPlugin


class MockPlugin(ChecklistPlugin):
    """Mock plugin for testing."""

    def __init__(
        self, name: str, priority: int, checklist_dir: Path, enabled: bool = True
    ):
        super().__init__()
        self._name = name
        self._priority = priority
        self._checklist_dir = checklist_dir
        self._enabled = enabled
        self.loaded_checklists = []

    def get_checklist_directories(self) -> List[Path]:
        return [self._checklist_dir]

    def get_checklist_metadata(self) -> Dict:
        return {
            "name": self._name,
            "version": "1.0.0",
            "author": "Test",
            "priority": self._priority,
            "enabled": self._enabled,
        }

    def on_checklist_loaded(self, checklist_name: str, checklist: Dict):
        self.loaded_checklists.append(checklist_name)


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        core_dir = tmppath / "core"
        plugin1_dir = tmppath / "plugin1"
        plugin2_dir = tmppath / "plugin2"
        schema_path = tmppath / "schema.json"

        core_dir.mkdir()
        plugin1_dir.mkdir()
        plugin2_dir.mkdir()

        # Create schema file
        schema_path.write_text(
            """{
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["checklist"],
            "properties": {
                "checklist": {
                    "type": "object",
                    "required": ["name", "category", "version", "items"],
                    "properties": {
                        "name": {"type": "string"},
                        "category": {"type": "string"},
                        "version": {"type": "string"},
                        "description": {"type": "string"},
                        "extends": {"type": "string"},
                        "metadata": {"type": "object"},
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["id", "text", "severity"],
                                "properties": {
                                    "id": {"type": "string"},
                                    "text": {"type": "string"},
                                    "severity": {"type": "string"},
                                    "category": {"type": "string"},
                                    "help_text": {"type": "string"},
                                    "references": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }"""
        )

        yield {
            "tmppath": tmppath,
            "core_dir": core_dir,
            "plugin1_dir": plugin1_dir,
            "plugin2_dir": plugin2_dir,
            "schema_path": schema_path,
        }


def create_checklist_yaml(path: Path, name: str, description: str = "Test checklist"):
    """Helper to create a checklist YAML file."""
    content = f"""checklist:
  name: {name}
  category: test
  version: 1.0.0
  description: {description}

  metadata:
    owner: Test

  items:
    - id: item-1
      text: Test item 1
      severity: high
      category: test
"""
    path.write_text(content)


def test_load_core_checklist_without_plugins(temp_dirs):
    """Test loading core checklist when no plugins configured."""
    core_dir = temp_dirs["core_dir"]
    schema_path = temp_dirs["schema_path"]

    # Create core checklist
    create_checklist_yaml(core_dir / "test-checklist.yaml", "test-checklist")

    # Initialize loader without plugin manager
    loader = ChecklistLoader([core_dir], schema_path, plugin_manager=None)

    # Load checklist
    checklist = loader.load_checklist("test-checklist")

    assert checklist.name == "test-checklist"
    assert loader.get_checklist_source("test-checklist") == "core"


def test_load_plugin_checklist(temp_dirs):
    """Test loading checklist from plugin."""
    core_dir = temp_dirs["core_dir"]
    plugin1_dir = temp_dirs["plugin1_dir"]
    schema_path = temp_dirs["schema_path"]

    # Create plugin checklist
    create_checklist_yaml(
        plugin1_dir / "plugin-checklist.yaml",
        "plugin-checklist",
        "Plugin checklist",
    )

    # Setup plugin manager
    plugin_mgr = ChecklistPluginManager()
    plugin = MockPlugin("plugin1", priority=50, checklist_dir=plugin1_dir)
    plugin_mgr.register_plugin(plugin)

    # Initialize loader with plugins
    loader = ChecklistLoader([core_dir], schema_path, plugin_manager=plugin_mgr)

    # Load plugin checklist
    checklist = loader.load_checklist("plugin-checklist")

    assert checklist.name == "plugin-checklist"
    assert loader.get_checklist_source("plugin-checklist") == "plugin1"
    assert "plugin-checklist" in plugin.loaded_checklists


def test_plugin_overrides_core(temp_dirs):
    """Test that plugin checklist overrides core checklist."""
    core_dir = temp_dirs["core_dir"]
    plugin1_dir = temp_dirs["plugin1_dir"]
    schema_path = temp_dirs["schema_path"]

    # Create core checklist
    create_checklist_yaml(
        core_dir / "override-test.yaml", "override-test", "Core version"
    )

    # Create plugin checklist with same name
    create_checklist_yaml(
        plugin1_dir / "override-test.yaml", "override-test", "Plugin version"
    )

    # Setup plugin
    plugin_mgr = ChecklistPluginManager()
    plugin = MockPlugin("plugin1", priority=50, checklist_dir=plugin1_dir)
    plugin_mgr.register_plugin(plugin)

    # Initialize loader
    loader = ChecklistLoader([core_dir], schema_path, plugin_manager=plugin_mgr)

    # Load checklist - should get plugin version
    checklist = loader.load_checklist("override-test")

    assert checklist.description == "Plugin version"
    assert loader.get_checklist_source("override-test") == "plugin1"


def test_priority_ordering(temp_dirs):
    """Test that higher priority plugins override lower priority."""
    core_dir = temp_dirs["core_dir"]
    plugin1_dir = temp_dirs["plugin1_dir"]
    plugin2_dir = temp_dirs["plugin2_dir"]
    schema_path = temp_dirs["schema_path"]

    # Create checklists in both plugins
    create_checklist_yaml(
        plugin1_dir / "priority-test.yaml", "priority-test", "Low priority"
    )
    create_checklist_yaml(
        plugin2_dir / "priority-test.yaml", "priority-test", "High priority"
    )

    # Setup plugins with different priorities
    plugin_mgr = ChecklistPluginManager()
    plugin1 = MockPlugin("plugin1", priority=50, checklist_dir=plugin1_dir)
    plugin2 = MockPlugin("plugin2", priority=100, checklist_dir=plugin2_dir)

    plugin_mgr.register_plugin(plugin1)
    plugin_mgr.register_plugin(plugin2)

    # Initialize loader
    loader = ChecklistLoader([core_dir], schema_path, plugin_manager=plugin_mgr)

    # Load checklist - should get high priority version
    checklist = loader.load_checklist("priority-test")

    assert checklist.description == "High priority"
    assert loader.get_checklist_source("priority-test") == "plugin2"


def test_list_checklists_with_plugins(temp_dirs):
    """Test listing checklists shows sources correctly."""
    core_dir = temp_dirs["core_dir"]
    plugin1_dir = temp_dirs["plugin1_dir"]
    schema_path = temp_dirs["schema_path"]

    # Create core checklist
    create_checklist_yaml(core_dir / "core-checklist.yaml", "core-checklist")

    # Create plugin checklist
    create_checklist_yaml(plugin1_dir / "plugin-checklist.yaml", "plugin-checklist")

    # Create override checklist
    create_checklist_yaml(core_dir / "override-test.yaml", "override-test")
    create_checklist_yaml(plugin1_dir / "override-test.yaml", "override-test")

    # Setup plugin
    plugin_mgr = ChecklistPluginManager()
    plugin = MockPlugin("plugin1", priority=50, checklist_dir=plugin1_dir)
    plugin_mgr.register_plugin(plugin)

    # Initialize loader
    loader = ChecklistLoader([core_dir], schema_path, plugin_manager=plugin_mgr)

    # List checklists
    checklists = loader.list_checklists()
    checklist_dict = dict(checklists)

    assert checklist_dict["core-checklist"] == "core"
    assert checklist_dict["plugin-checklist"] == "plugin1"
    assert checklist_dict["override-test"] == "plugin1"  # Plugin overrides


def test_disabled_plugin_not_loaded(temp_dirs):
    """Test that disabled plugins are skipped."""
    core_dir = temp_dirs["core_dir"]
    plugin1_dir = temp_dirs["plugin1_dir"]
    schema_path = temp_dirs["schema_path"]

    # Create plugin checklist
    create_checklist_yaml(plugin1_dir / "disabled-test.yaml", "disabled-test")

    # Setup plugin
    plugin_mgr = ChecklistPluginManager()
    plugin = MockPlugin("plugin1", priority=50, checklist_dir=plugin1_dir)
    plugin_mgr.register_plugin(plugin)

    # Disable plugin
    plugin_mgr.disable_plugin("plugin1")

    # Initialize loader
    loader = ChecklistLoader([core_dir], schema_path, plugin_manager=plugin_mgr)

    # Try to load - should fail (no core version)
    with pytest.raises(Exception):  # ChecklistNotFoundError
        loader.load_checklist("disabled-test")


def test_plugin_hook_called(temp_dirs):
    """Test that plugin hooks are called on checklist load."""
    core_dir = temp_dirs["core_dir"]
    plugin1_dir = temp_dirs["plugin1_dir"]
    schema_path = temp_dirs["schema_path"]

    # Create plugin checklist
    create_checklist_yaml(plugin1_dir / "hook-test.yaml", "hook-test")

    # Setup plugin
    plugin_mgr = ChecklistPluginManager()
    plugin = MockPlugin("plugin1", priority=50, checklist_dir=plugin1_dir)
    plugin_mgr.register_plugin(plugin)

    # Initialize loader
    loader = ChecklistLoader([core_dir], schema_path, plugin_manager=plugin_mgr)

    # Load checklist
    loader.load_checklist("hook-test")

    # Verify hook was called
    assert "hook-test" in plugin.loaded_checklists


def test_cache_works_with_plugins(temp_dirs):
    """Test that caching works correctly with plugins."""
    core_dir = temp_dirs["core_dir"]
    plugin1_dir = temp_dirs["plugin1_dir"]
    schema_path = temp_dirs["schema_path"]

    # Create plugin checklist
    create_checklist_yaml(plugin1_dir / "cache-test.yaml", "cache-test")

    # Setup plugin
    plugin_mgr = ChecklistPluginManager()
    plugin = MockPlugin("plugin1", priority=50, checklist_dir=plugin1_dir)
    plugin_mgr.register_plugin(plugin)

    # Initialize loader
    loader = ChecklistLoader([core_dir], schema_path, plugin_manager=plugin_mgr)

    # Load checklist twice
    checklist1 = loader.load_checklist("cache-test")
    checklist2 = loader.load_checklist("cache-test")

    # Should be same instance (from cache)
    assert checklist1 is checklist2

    # Hook should only be called once
    assert plugin.loaded_checklists.count("cache-test") == 1


def test_invalid_plugin_checklist_skipped(temp_dirs):
    """Test that invalid plugin checklists are skipped."""
    core_dir = temp_dirs["core_dir"]
    plugin1_dir = temp_dirs["plugin1_dir"]
    schema_path = temp_dirs["schema_path"]

    # Create invalid plugin checklist (missing required fields)
    invalid_content = """checklist:
  name: invalid-checklist
  # Missing category, version, items
"""
    (plugin1_dir / "invalid-checklist.yaml").write_text(invalid_content)

    # Create valid core version
    create_checklist_yaml(core_dir / "invalid-checklist.yaml", "invalid-checklist")

    # Setup plugin
    plugin_mgr = ChecklistPluginManager()
    plugin = MockPlugin("plugin1", priority=50, checklist_dir=plugin1_dir)
    plugin_mgr.register_plugin(plugin)

    # Initialize loader
    loader = ChecklistLoader([core_dir], schema_path, plugin_manager=plugin_mgr)

    # Load checklist - should fall back to core
    checklist = loader.load_checklist("invalid-checklist")

    assert checklist.name == "invalid-checklist"
    assert loader.get_checklist_source("invalid-checklist") == "core"

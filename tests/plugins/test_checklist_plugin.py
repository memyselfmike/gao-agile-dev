"""Tests for ChecklistPlugin base class."""

from pathlib import Path
from typing import Dict, List

import pytest

from gao_dev.plugins.checklist_plugin import ChecklistPlugin


class MockChecklistPluginForTesting(ChecklistPlugin):
    """Mock implementation of ChecklistPlugin for testing."""

    def __init__(self, metadata: Dict = None):
        super().__init__()
        self._metadata = metadata or {
            "name": "test-plugin",
            "version": "1.0.0",
            "author": "Test Author",
            "priority": 50,
        }
        self._checklist_dirs = [Path("test_checklists")]

    def get_checklist_directories(self) -> List[Path]:
        return self._checklist_dirs

    def get_checklist_metadata(self) -> Dict:
        return self._metadata


def test_checklist_plugin_base_class():
    """Test that ChecklistPlugin can be instantiated via concrete subclass."""
    plugin = MockChecklistPluginForTesting()
    assert plugin is not None


def test_get_checklist_directories():
    """Test get_checklist_directories method."""
    plugin = MockChecklistPluginForTesting()
    dirs = plugin.get_checklist_directories()

    assert len(dirs) == 1
    assert dirs[0] == Path("test_checklists")


def test_get_checklist_metadata():
    """Test get_checklist_metadata method."""
    plugin = MockChecklistPluginForTesting()
    metadata = plugin.get_checklist_metadata()

    assert metadata["name"] == "test-plugin"
    assert metadata["version"] == "1.0.0"
    assert metadata["author"] == "Test Author"
    assert metadata["priority"] == 50


def test_custom_metadata():
    """Test plugin with custom metadata."""
    custom_metadata = {
        "name": "custom-plugin",
        "version": "2.0.0",
        "author": "Custom Author",
        "priority": 100,
        "dependencies": ["other-plugin"],
    }

    plugin = MockChecklistPluginForTesting(metadata=custom_metadata)
    metadata = plugin.get_checklist_metadata()

    assert metadata["name"] == "custom-plugin"
    assert metadata["version"] == "2.0.0"
    assert metadata["priority"] == 100
    assert metadata["dependencies"] == ["other-plugin"]


def test_validate_checklist_default():
    """Test default validate_checklist implementation."""
    plugin = MockChecklistPluginForTesting()
    checklist = {"checklist": {"name": "test", "items": []}}

    # Default implementation should return True
    assert plugin.validate_checklist(checklist) is True


def test_validate_checklist_custom():
    """Test custom validate_checklist implementation."""

    class CustomValidationPlugin(MockChecklistPluginForTesting):
        def validate_checklist(self, checklist: Dict) -> bool:
            # Custom validation: require 'owner' in metadata
            checklist_data = checklist.get("checklist", {})
            metadata = checklist_data.get("metadata", {})
            return "owner" in metadata

    plugin = CustomValidationPlugin()

    # Valid checklist with owner
    valid_checklist = {
        "checklist": {"name": "test", "metadata": {"owner": "Team"}, "items": []}
    }
    assert plugin.validate_checklist(valid_checklist) is True

    # Invalid checklist without owner
    invalid_checklist = {"checklist": {"name": "test", "metadata": {}, "items": []}}
    assert plugin.validate_checklist(invalid_checklist) is False


def test_lifecycle_hooks():
    """Test lifecycle hooks are callable."""

    class HookTrackingPlugin(MockChecklistPluginForTesting):
        def __init__(self):
            super().__init__()
            self.loaded_checklists = []
            self.executed_checklists = []
            self.failed_checklists = []

        def on_checklist_loaded(self, checklist_name: str, checklist: Dict):
            self.loaded_checklists.append(checklist_name)

        def on_checklist_executed(
            self, checklist_name: str, execution_id: int, status: str
        ):
            self.executed_checklists.append(
                (checklist_name, execution_id, status)
            )

        def on_checklist_failed(
            self, checklist_name: str, execution_id: int, errors: List[str]
        ):
            self.failed_checklists.append((checklist_name, execution_id, errors))

    plugin = HookTrackingPlugin()

    # Test on_checklist_loaded
    plugin.on_checklist_loaded("test-checklist", {"checklist": {}})
    assert "test-checklist" in plugin.loaded_checklists

    # Test on_checklist_executed
    plugin.on_checklist_executed("test-checklist", 1, "pass")
    assert ("test-checklist", 1, "pass") in plugin.executed_checklists

    # Test on_checklist_failed
    plugin.on_checklist_failed("test-checklist", 2, ["error1", "error2"])
    assert ("test-checklist", 2, ["error1", "error2"]) in plugin.failed_checklists


def test_plugin_initialization():
    """Test plugin initialize method."""
    plugin = MockChecklistPluginForTesting()

    # initialize() should return True by default (inherited from BasePlugin)
    assert plugin.initialize() is True


def test_plugin_cleanup():
    """Test plugin cleanup method."""
    plugin = MockChecklistPluginForTesting()

    # cleanup() should not raise exceptions (inherited from BasePlugin)
    plugin.cleanup()  # Should complete without error


def test_abstract_methods_required():
    """Test that abstract methods must be implemented."""

    # This should fail if we try to instantiate without implementing abstract methods
    with pytest.raises(TypeError):
        # Directly instantiate ChecklistPlugin (should fail)
        ChecklistPlugin()  # type: ignore


def test_multiple_checklist_directories():
    """Test plugin with multiple checklist directories."""

    class MultiDirPlugin(MockChecklistPluginForTesting):
        def get_checklist_directories(self) -> List[Path]:
            return [
                Path("checklists/legal"),
                Path("checklists/compliance"),
                Path("checklists/security"),
            ]

    plugin = MultiDirPlugin()
    dirs = plugin.get_checklist_directories()

    assert len(dirs) == 3
    assert Path("checklists/legal") in dirs
    assert Path("checklists/compliance") in dirs
    assert Path("checklists/security") in dirs


def test_plugin_metadata_optional_fields():
    """Test plugin metadata with optional fields."""
    metadata = {
        "name": "full-plugin",
        "version": "1.0.0",
        "author": "Test Author",
        "description": "Test plugin with all fields",
        "priority": 100,
        "dependencies": ["dep1", "dep2"],
        "checklist_prefix": "test-",
    }

    plugin = MockChecklistPluginForTesting(metadata=metadata)
    result = plugin.get_checklist_metadata()

    assert result["description"] == "Test plugin with all fields"
    assert result["checklist_prefix"] == "test-"
    assert result["dependencies"] == ["dep1", "dep2"]

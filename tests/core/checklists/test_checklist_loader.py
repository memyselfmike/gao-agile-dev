"""
Tests for ChecklistLoader.

Comprehensive test suite covering:
- Loading simple checklists
- Inheritance resolution
- Multi-level inheritance
- Circular dependency detection
- Validation
- Caching
- Discovery
- Rendering
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from gao_dev.core.checklists.checklist_loader import ChecklistLoader
from gao_dev.core.checklists.exceptions import (
    ChecklistInheritanceError,
    ChecklistNotFoundError,
    ChecklistValidationError,
)
from gao_dev.core.checklists.models import Checklist, ChecklistItem


@pytest.fixture
def schema_path():
    """Path to checklist JSON schema."""
    return Path("gao_dev/config/schemas/checklist_schema.json")


@pytest.fixture
def config_checklists_dir():
    """Path to config checklists directory."""
    return Path("gao_dev/config/checklists")


@pytest.fixture
def temp_checklist_dir():
    """Create a temporary directory for test checklists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def simple_checklist_data():
    """Simple checklist data for testing."""
    return {
        "checklist": {
            "name": "Simple Test Checklist",
            "category": "testing",
            "version": "1.0.0",
            "description": "A simple test checklist",
            "items": [
                {
                    "id": "item-1",
                    "text": "First test item",
                    "severity": "high",
                    "help_text": "Help for item 1",
                },
                {
                    "id": "item-2",
                    "text": "Second test item",
                    "severity": "medium",
                },
            ],
            "metadata": {"domain": "software-engineering", "tags": ["test"]},
        }
    }


@pytest.fixture
def loader_with_config(schema_path, config_checklists_dir):
    """Loader with config checklists directory."""
    return ChecklistLoader([config_checklists_dir], schema_path)


class TestChecklistLoaderBasic:
    """Test basic loading functionality."""

    def test_load_simple_checklist(
        self, temp_checklist_dir, schema_path, simple_checklist_data
    ):
        """Test loading a simple checklist without inheritance."""
        # Create checklist file
        checklist_path = temp_checklist_dir / "simple.yaml"
        with open(checklist_path, "w", encoding="utf-8") as f:
            yaml.dump(simple_checklist_data, f)

        # Load checklist
        loader = ChecklistLoader([temp_checklist_dir], schema_path)
        checklist = loader.load_checklist("simple")

        # Verify
        assert isinstance(checklist, Checklist)
        assert checklist.name == "Simple Test Checklist"
        assert checklist.category == "testing"
        assert checklist.version == "1.0.0"
        assert checklist.description == "A simple test checklist"
        assert len(checklist.items) == 2
        assert checklist.metadata["domain"] == "software-engineering"

        # Verify items
        item1 = checklist.items[0]
        assert isinstance(item1, ChecklistItem)
        assert item1.id == "item-1"
        assert item1.text == "First test item"
        assert item1.severity == "high"
        assert item1.help_text == "Help for item 1"

        item2 = checklist.items[1]
        assert item2.id == "item-2"
        assert item2.text == "Second test item"
        assert item2.severity == "medium"
        assert item2.help_text is None

    def test_load_from_config_directory(self, loader_with_config):
        """Test loading checklists from the config directory."""
        # Load the OWASP checklist (no inheritance)
        checklist = loader_with_config.load_checklist("security/owasp-top-10")

        assert checklist.name == "OWASP Top 10 Security Checklist"
        assert checklist.category == "security"
        assert len(checklist.items) > 0

    def test_checklist_not_found(self, loader_with_config):
        """Test error when checklist doesn't exist."""
        with pytest.raises(ChecklistNotFoundError) as exc_info:
            loader_with_config.load_checklist("nonexistent/checklist")

        assert "not found" in str(exc_info.value).lower()


class TestChecklistInheritance:
    """Test inheritance resolution."""

    def test_load_checklist_with_inheritance(self, loader_with_config):
        """Test loading a checklist that extends another."""
        # Load unit-test-standards which extends base-testing-standards
        checklist = loader_with_config.load_checklist("testing/unit-test-standards")

        assert checklist.name == "Unit Test Standards"
        assert checklist.category == "testing"

        # Should have parent items + child items
        # Base has 4 items, child adds 8 more = 12 total
        assert len(checklist.items) >= 10

        # Check that parent items are included
        item_ids = [item.id for item in checklist.items]
        assert "test-exists" in item_ids  # From base
        assert "test-passing" in item_ids  # From base
        assert "test-coverage" in item_ids  # From child

    def test_child_overrides_parent_item(
        self, temp_checklist_dir, schema_path, simple_checklist_data
    ):
        """Test that child items override parent items with same ID."""
        # Create parent checklist
        parent_path = temp_checklist_dir / "parent.yaml"
        with open(parent_path, "w", encoding="utf-8") as f:
            yaml.dump(simple_checklist_data, f)

        # Create child checklist that extends parent and overrides item-1
        child_data = {
            "checklist": {
                "name": "Child Checklist",
                "category": "testing",
                "version": "1.0.0",
                "extends": "parent",
                "items": [
                    {
                        "id": "item-1",  # Override parent's item-1
                        "text": "Overridden first item",
                        "severity": "critical",
                    },
                    {
                        "id": "item-3",  # New item
                        "text": "Third item from child",
                        "severity": "low",
                    },
                ],
                "metadata": {"domain": "operations"},
            }
        }
        child_path = temp_checklist_dir / "child.yaml"
        with open(child_path, "w", encoding="utf-8") as f:
            yaml.dump(child_data, f)

        # Load child
        loader = ChecklistLoader([temp_checklist_dir], schema_path)
        checklist = loader.load_checklist("child")

        # Should have 3 items: overridden item-1, inherited item-2, new item-3
        assert len(checklist.items) == 3

        item_dict = {item.id: item for item in checklist.items}
        assert item_dict["item-1"].text == "Overridden first item"
        assert item_dict["item-1"].severity == "critical"
        assert item_dict["item-2"].text == "Second test item"  # From parent
        assert item_dict["item-3"].text == "Third item from child"

        # Metadata merged (child overrides)
        assert checklist.metadata["domain"] == "operations"

    def test_multi_level_inheritance(self, temp_checklist_dir, schema_path):
        """Test grandparent -> parent -> child inheritance."""
        # Create grandparent
        grandparent_data = {
            "checklist": {
                "name": "Grandparent",
                "category": "testing",
                "version": "1.0.0",
                "items": [
                    {"id": "item-1", "text": "This is item 1 from grandparent", "severity": "high"},
                ],
                "metadata": {"level": "grandparent"},
            }
        }
        with open(temp_checklist_dir / "grandparent.yaml", "w", encoding="utf-8") as f:
            yaml.dump(grandparent_data, f)

        # Create parent
        parent_data = {
            "checklist": {
                "name": "Parent",
                "category": "testing",
                "version": "1.0.0",
                "extends": "grandparent",
                "items": [
                    {"id": "item-2", "text": "This is item 2 from parent", "severity": "medium"},
                ],
                "metadata": {"level": "parent"},
            }
        }
        with open(temp_checklist_dir / "parent.yaml", "w", encoding="utf-8") as f:
            yaml.dump(parent_data, f)

        # Create child
        child_data = {
            "checklist": {
                "name": "Child",
                "category": "testing",
                "version": "1.0.0",
                "extends": "parent",
                "items": [
                    {"id": "item-3", "text": "This is item 3 from child", "severity": "low"},
                ],
                "metadata": {"level": "child"},
            }
        }
        with open(temp_checklist_dir / "child.yaml", "w", encoding="utf-8") as f:
            yaml.dump(child_data, f)

        # Load child
        loader = ChecklistLoader([temp_checklist_dir], schema_path)
        checklist = loader.load_checklist("child")

        # Should have all 3 items
        assert len(checklist.items) == 3
        item_ids = [item.id for item in checklist.items]
        assert "item-1" in item_ids  # From grandparent
        assert "item-2" in item_ids  # From parent
        assert "item-3" in item_ids  # From child

        # Metadata should be from child (last override wins)
        assert checklist.metadata["level"] == "child"

    def test_circular_inheritance_detected(self, temp_checklist_dir, schema_path):
        """Test that circular inheritance is detected and prevented."""
        # Create A -> B -> A circular dependency
        a_data = {
            "checklist": {
                "name": "Checklist A",
                "category": "testing",
                "version": "1.0.0",
                "extends": "b",
                "items": [{"id": "item-a", "text": "This is item A from checklist A", "severity": "high"}],
            }
        }
        with open(temp_checklist_dir / "a.yaml", "w", encoding="utf-8") as f:
            yaml.dump(a_data, f)

        b_data = {
            "checklist": {
                "name": "Checklist B",
                "category": "testing",
                "version": "1.0.0",
                "extends": "a",
                "items": [{"id": "item-b", "text": "This is item B from checklist B", "severity": "medium"}],
            }
        }
        with open(temp_checklist_dir / "b.yaml", "w", encoding="utf-8") as f:
            yaml.dump(b_data, f)

        # Try to load - should raise CircularInheritanceError
        loader = ChecklistLoader([temp_checklist_dir], schema_path)
        with pytest.raises(ChecklistInheritanceError) as exc_info:
            loader.load_checklist("a")

        assert "circular" in str(exc_info.value).lower()

    def test_parent_not_found(self, temp_checklist_dir, schema_path):
        """Test error when parent checklist doesn't exist."""
        child_data = {
            "checklist": {
                "name": "Child",
                "category": "testing",
                "version": "1.0.0",
                "extends": "nonexistent-parent",
                "items": [{"id": "item-1", "text": "This is item 1 from child", "severity": "high"}],
            }
        }
        with open(temp_checklist_dir / "child.yaml", "w", encoding="utf-8") as f:
            yaml.dump(child_data, f)

        loader = ChecklistLoader([temp_checklist_dir], schema_path)
        with pytest.raises(ChecklistNotFoundError):
            loader.load_checklist("child")


class TestChecklistValidation:
    """Test schema validation."""

    def test_invalid_checklist_rejected(self, temp_checklist_dir, schema_path):
        """Test that invalid checklists are rejected."""
        # Missing required 'name' field
        invalid_data = {
            "checklist": {
                "category": "testing",
                "version": "1.0.0",
                "items": [{"id": "item-1", "text": "Item 1", "severity": "high"}],
            }
        }
        with open(temp_checklist_dir / "invalid.yaml", "w", encoding="utf-8") as f:
            yaml.dump(invalid_data, f)

        loader = ChecklistLoader([temp_checklist_dir], schema_path)
        with pytest.raises(ChecklistValidationError) as exc_info:
            loader.load_checklist("invalid")

        assert "validation failed" in str(exc_info.value).lower()

    def test_invalid_severity(self, temp_checklist_dir, schema_path):
        """Test that invalid severity values are rejected."""
        invalid_data = {
            "checklist": {
                "name": "Test",
                "category": "testing",
                "version": "1.0.0",
                "items": [
                    {"id": "item-1", "text": "Item 1", "severity": "invalid-severity"}
                ],
            }
        }
        with open(temp_checklist_dir / "invalid.yaml", "w", encoding="utf-8") as f:
            yaml.dump(invalid_data, f)

        loader = ChecklistLoader([temp_checklist_dir], schema_path)
        with pytest.raises(ChecklistValidationError):
            loader.load_checklist("invalid")


class TestChecklistCaching:
    """Test caching functionality."""

    def test_cache_hit_returns_cached_value(
        self, temp_checklist_dir, schema_path, simple_checklist_data
    ):
        """Test that loading the same checklist twice uses cache."""
        checklist_path = temp_checklist_dir / "cached.yaml"
        with open(checklist_path, "w", encoding="utf-8") as f:
            yaml.dump(simple_checklist_data, f)

        loader = ChecklistLoader([temp_checklist_dir], schema_path)

        # Load first time
        checklist1 = loader.load_checklist("cached")

        # Load second time (should be from cache)
        checklist2 = loader.load_checklist("cached")

        # Should be the exact same object
        assert checklist1 is checklist2

    def test_parent_cached_during_inheritance(
        self, temp_checklist_dir, schema_path, simple_checklist_data
    ):
        """Test that parent checklists are cached during inheritance resolution."""
        # Create parent
        with open(temp_checklist_dir / "parent.yaml", "w", encoding="utf-8") as f:
            yaml.dump(simple_checklist_data, f)

        # Create child
        child_data = {
            "checklist": {
                "name": "Child",
                "category": "testing",
                "version": "1.0.0",
                "extends": "parent",
                "items": [{"id": "item-3", "text": "This is item 3 from child", "severity": "low"}],
            }
        }
        with open(temp_checklist_dir / "child.yaml", "w", encoding="utf-8") as f:
            yaml.dump(child_data, f)

        loader = ChecklistLoader([temp_checklist_dir], schema_path)

        # Load child (parent should be cached)
        loader.load_checklist("child")

        # Now load parent directly (should come from cache)
        assert "parent" in loader._cache


class TestChecklistDiscovery:
    """Test checklist discovery."""

    def test_list_checklists(self, loader_with_config):
        """Test discovering all available checklists."""
        checklists = loader_with_config.list_checklists()

        assert isinstance(checklists, list)
        assert len(checklists) > 0

        # list_checklists returns tuples of (name, source)
        checklist_names = [name for name, source in checklists]

        # Should include known checklists
        assert "testing/unit-test-standards" in checklist_names
        assert "security/owasp-top-10" in checklist_names
        assert "testing/base-testing-standards" in checklist_names

        # Should be sorted
        assert checklist_names == sorted(checklist_names)

    def test_list_checklists_unique(self, temp_checklist_dir, schema_path):
        """Test that list_checklists returns unique names."""
        # Create two directories with overlapping checklists
        dir1 = temp_checklist_dir / "dir1"
        dir2 = temp_checklist_dir / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        checklist_data = {
            "checklist": {
                "name": "Test",
                "category": "testing",
                "version": "1.0.0",
                "items": [{"id": "item-1", "text": "Item 1", "severity": "high"}],
            }
        }

        # Create same checklist in both directories
        with open(dir1 / "test.yaml", "w", encoding="utf-8") as f:
            yaml.dump(checklist_data, f)
        with open(dir2 / "test.yaml", "w", encoding="utf-8") as f:
            yaml.dump(checklist_data, f)

        loader = ChecklistLoader([dir1, dir2], schema_path)
        checklists = loader.list_checklists()

        # list_checklists returns tuples of (name, source)
        checklist_names = [name for name, source in checklists]

        # Should only appear once
        assert checklist_names.count("test") == 1

    def test_list_checklists_nested(self, temp_checklist_dir, schema_path):
        """Test discovering checklists in nested directories."""
        nested_dir = temp_checklist_dir / "category" / "subcategory"
        nested_dir.mkdir(parents=True)

        checklist_data = {
            "checklist": {
                "name": "Nested",
                "category": "testing",
                "version": "1.0.0",
                "items": [{"id": "item-1", "text": "Item 1", "severity": "high"}],
            }
        }
        with open(nested_dir / "nested.yaml", "w", encoding="utf-8") as f:
            yaml.dump(checklist_data, f)

        loader = ChecklistLoader([temp_checklist_dir], schema_path)
        checklists = loader.list_checklists()

        # list_checklists returns tuples of (name, source)
        checklist_names = [name for name, source in checklists]

        # Should use forward slashes even on Windows
        assert "category/subcategory/nested" in checklist_names


class TestChecklistRendering:
    """Test markdown rendering."""

    def test_render_simple_checklist(
        self, temp_checklist_dir, schema_path, simple_checklist_data
    ):
        """Test rendering a checklist as markdown."""
        with open(temp_checklist_dir / "simple.yaml", "w", encoding="utf-8") as f:
            yaml.dump(simple_checklist_data, f)

        loader = ChecklistLoader([temp_checklist_dir], schema_path)
        checklist = loader.load_checklist("simple")
        markdown = loader.render_checklist(checklist)

        # Verify markdown structure
        assert "# Simple Test Checklist" in markdown
        assert "A simple test checklist" in markdown
        assert "- [ ] **[HIGH]** First test item" in markdown
        assert "- [ ] **[MEDIUM]** Second test item" in markdown
        assert "- Help for item 1" in markdown

    def test_render_without_description(self, temp_checklist_dir, schema_path):
        """Test rendering a checklist without description."""
        data = {
            "checklist": {
                "name": "No Description",
                "category": "testing",
                "version": "1.0.0",
                "items": [{"id": "item-1", "text": "This is item 1 without description", "severity": "high"}],
            }
        }
        with open(temp_checklist_dir / "nodesc.yaml", "w", encoding="utf-8") as f:
            yaml.dump(data, f)

        loader = ChecklistLoader([temp_checklist_dir], schema_path)
        checklist = loader.load_checklist("nodesc")
        markdown = loader.render_checklist(checklist)

        assert "# No Description" in markdown
        assert "- [ ] **[HIGH]** This is item 1 without description" in markdown


class TestChecklistMultipleDirectories:
    """Test loading from multiple directories."""

    def test_plugin_override_core(self, temp_checklist_dir, schema_path):
        """Test that plugin checklists override core checklists."""
        # Create core directory
        core_dir = temp_checklist_dir / "core"
        core_dir.mkdir()

        # Create plugin directory
        plugin_dir = temp_checklist_dir / "plugin"
        plugin_dir.mkdir()

        # Create core checklist
        core_data = {
            "checklist": {
                "name": "Core Checklist",
                "category": "testing",
                "version": "1.0.0",
                "items": [{"id": "item-1", "text": "Core item", "severity": "high"}],
            }
        }
        with open(core_dir / "shared.yaml", "w", encoding="utf-8") as f:
            yaml.dump(core_data, f)

        # Create plugin checklist with same name
        plugin_data = {
            "checklist": {
                "name": "Plugin Checklist",
                "category": "testing",
                "version": "2.0.0",
                "items": [{"id": "item-1", "text": "Plugin item", "severity": "critical"}],
            }
        }
        with open(plugin_dir / "shared.yaml", "w", encoding="utf-8") as f:
            yaml.dump(plugin_data, f)

        # Load with plugin dir first (should take precedence)
        loader = ChecklistLoader([plugin_dir, core_dir], schema_path)
        checklist = loader.load_checklist("shared")

        # Should get plugin version
        assert checklist.name == "Plugin Checklist"
        assert checklist.version == "2.0.0"
        assert checklist.items[0].text == "Plugin item"

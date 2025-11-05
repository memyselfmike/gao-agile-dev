"""Tests for Legal Team Plugin example."""

from pathlib import Path

import pytest

# Import the legal checklist plugin
import sys

legal_plugin_path = Path(__file__).parent.parent.parent / "docs" / "examples" / "legal-team-plugin"
sys.path.insert(0, str(legal_plugin_path))

from legal_checklist_plugin import LegalChecklistPlugin


def test_legal_plugin_instantiation():
    """Test that LegalChecklistPlugin can be instantiated."""
    plugin = LegalChecklistPlugin()
    assert plugin is not None


def test_legal_plugin_metadata():
    """Test legal plugin metadata."""
    plugin = LegalChecklistPlugin()
    metadata = plugin.get_checklist_metadata()

    assert metadata["name"] == "legal-team"
    assert metadata["version"] == "1.0.0"
    assert metadata["author"] == "GAO Legal Team"
    assert metadata["priority"] == 100
    assert metadata["checklist_prefix"] == "legal-"
    assert metadata["dependencies"] == []


def test_legal_plugin_checklist_directories():
    """Test legal plugin returns correct checklist directories."""
    plugin = LegalChecklistPlugin()
    directories = plugin.get_checklist_directories()

    assert len(directories) == 1
    assert directories[0].name == "legal"
    assert "checklists" in str(directories[0])


def test_legal_plugin_checklist_files_exist():
    """Test that all expected legal checklists exist."""
    plugin = LegalChecklistPlugin()
    directories = plugin.get_checklist_directories()

    expected_checklists = [
        "contract-review.yaml",
        "compliance-check.yaml",
        "legal-review.yaml",
        "data-privacy.yaml",
    ]

    for directory in directories:
        if directory.exists():
            for checklist_name in expected_checklists:
                checklist_path = directory / checklist_name
                assert checklist_path.exists(), f"Expected checklist not found: {checklist_path}"


def test_legal_plugin_validate_checklist():
    """Test custom validation for legal checklists."""
    plugin = LegalChecklistPlugin()

    # Valid checklist with compliance tags
    valid_checklist = {
        "checklist": {
            "name": "test",
            "metadata": {"compliance_tags": ["legal", "gdpr"]},
        }
    }
    assert plugin.validate_checklist(valid_checklist) is True

    # Checklist without compliance tags (warning but still valid)
    no_tags_checklist = {"checklist": {"name": "test", "metadata": {}}}
    assert plugin.validate_checklist(no_tags_checklist) is True


def test_legal_plugin_lifecycle_hooks():
    """Test that lifecycle hooks are callable."""
    plugin = LegalChecklistPlugin()

    # Test on_checklist_loaded
    plugin.on_checklist_loaded("contract-review", {"checklist": {}})

    # Test on_checklist_executed
    plugin.on_checklist_executed("contract-review", 1, "pass")
    plugin.on_checklist_executed("contract-review", 2, "fail")

    # Test on_checklist_failed
    plugin.on_checklist_failed("contract-review", 3, ["error1", "error2"])


def test_legal_plugin_initialization():
    """Test plugin initialization."""
    plugin = LegalChecklistPlugin()
    assert plugin.initialize() is True


def test_legal_plugin_cleanup():
    """Test plugin cleanup."""
    plugin = LegalChecklistPlugin()
    plugin.cleanup()  # Should not raise exception


@pytest.mark.skipif(
    not (legal_plugin_path / "checklists" / "legal").exists(),
    reason="Legal plugin checklists not available",
)
def test_contract_review_checklist_structure():
    """Test contract-review checklist has correct structure."""
    import yaml

    checklist_path = legal_plugin_path / "checklists" / "legal" / "contract-review.yaml"

    with open(checklist_path, "r") as f:
        data = yaml.safe_load(f)

    assert "checklist" in data
    checklist = data["checklist"]

    assert checklist["name"] == "contract-review"
    assert checklist["category"] == "legal"
    assert checklist["version"] == "1.0.0"
    assert "items" in checklist
    assert len(checklist["items"]) > 0

    # Check metadata
    metadata = checklist.get("metadata", {})
    assert "compliance_tags" in metadata
    assert "legal" in metadata["compliance_tags"]


@pytest.mark.skipif(
    not (legal_plugin_path / "checklists" / "legal").exists(),
    reason="Legal plugin checklists not available",
)
def test_compliance_check_checklist_structure():
    """Test compliance-check checklist has correct structure."""
    import yaml

    checklist_path = legal_plugin_path / "checklists" / "legal" / "compliance-check.yaml"

    with open(checklist_path, "r") as f:
        data = yaml.safe_load(f)

    assert "checklist" in data
    checklist = data["checklist"]

    assert checklist["name"] == "compliance-check"
    assert checklist["category"] == "legal"
    assert "items" in checklist
    assert len(checklist["items"]) > 0


@pytest.mark.skipif(
    not (legal_plugin_path / "checklists" / "legal").exists(),
    reason="Legal plugin checklists not available",
)
def test_legal_review_checklist_structure():
    """Test legal-review checklist has correct structure."""
    import yaml

    checklist_path = legal_plugin_path / "checklists" / "legal" / "legal-review.yaml"

    with open(checklist_path, "r") as f:
        data = yaml.safe_load(f)

    assert "checklist" in data
    checklist = data["checklist"]

    assert checklist["name"] == "legal-review"
    assert checklist["category"] == "legal"
    assert "items" in checklist


@pytest.mark.skipif(
    not (legal_plugin_path / "checklists" / "legal").exists(),
    reason="Legal plugin checklists not available",
)
def test_data_privacy_checklist_structure():
    """Test data-privacy checklist has correct structure."""
    import yaml

    checklist_path = legal_plugin_path / "checklists" / "legal" / "data-privacy.yaml"

    with open(checklist_path, "r") as f:
        data = yaml.safe_load(f)

    assert "checklist" in data
    checklist = data["checklist"]

    assert checklist["name"] == "data-privacy"
    assert checklist["category"] == "legal"
    assert "items" in checklist

    # Check for GDPR-specific items
    metadata = checklist.get("metadata", {})
    assert "gdpr" in metadata.get("compliance_tags", [])


@pytest.mark.skipif(
    not (legal_plugin_path / "checklists" / "legal").exists(),
    reason="Legal plugin checklists not available",
)
def test_all_legal_checklists_have_high_severity_items():
    """Test that all legal checklists have at least one high severity item."""
    import yaml

    checklist_files = [
        "contract-review.yaml",
        "compliance-check.yaml",
        "legal-review.yaml",
        "data-privacy.yaml",
    ]

    for checklist_file in checklist_files:
        checklist_path = legal_plugin_path / "checklists" / "legal" / checklist_file

        with open(checklist_path, "r") as f:
            data = yaml.safe_load(f)

        checklist = data["checklist"]
        items = checklist["items"]

        # Should have at least one high severity item
        high_severity_items = [item for item in items if item["severity"] == "high"]
        assert len(high_severity_items) > 0, f"{checklist_file} has no high severity items"

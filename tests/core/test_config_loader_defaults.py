"""Tests for ConfigLoader workflow defaults functionality (Story 18.4)."""

import pytest
import yaml
from pathlib import Path
from typing import Dict

from gao_dev.core.config_loader import ConfigLoader


class TestConfigLoaderWorkflowDefaults:
    """Test workflow defaults loading and validation."""

    @pytest.fixture
    def temp_project_dir(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        return tmp_path / "test_project"

    @pytest.fixture
    def config_loader(self, temp_project_dir: Path) -> ConfigLoader:
        """Create a ConfigLoader instance."""
        temp_project_dir.mkdir(parents=True, exist_ok=True)
        return ConfigLoader(temp_project_dir)

    def test_get_workflow_defaults_returns_dict(self, config_loader: ConfigLoader):
        """Test that get_workflow_defaults returns a dictionary."""
        defaults = config_loader.get_workflow_defaults()
        assert isinstance(defaults, dict)

    def test_workflow_defaults_contain_expected_keys(self, config_loader: ConfigLoader):
        """Test that workflow defaults contain expected common variables."""
        defaults = config_loader.get_workflow_defaults()

        # Check for expected keys based on Story 18.4 requirements
        expected_keys = [
            "prd_location",
            "architecture_location",
            "tech_spec_location",
            "dev_story_location",
            "epic_location",
            "output_folder",
            "sprint_status_location",
            "workflow_status_location",
        ]

        for key in expected_keys:
            assert key in defaults, f"Expected key '{key}' not found in workflow defaults"

    def test_workflow_defaults_all_string_values(self, config_loader: ConfigLoader):
        """Test that all workflow default values are strings (path values)."""
        defaults = config_loader.get_workflow_defaults()

        for key, value in defaults.items():
            assert isinstance(value, str), f"Default for '{key}' is not a string: {type(value)}"

    def test_workflow_defaults_match_gao_dev_conventions(self, config_loader: ConfigLoader):
        """Test that default paths follow GAO-Dev project conventions."""
        defaults = config_loader.get_workflow_defaults()

        # All paths should use forward slashes (cross-platform)
        for key, value in defaults.items():
            if "\\" in value:
                pytest.fail(f"Default '{key}' contains backslashes: {value}")

        # Check specific conventions
        assert defaults["prd_location"] == "docs/PRD.md"
        assert defaults["architecture_location"] == "docs/ARCHITECTURE.md"
        assert defaults["tech_spec_location"] == "docs/TECHNICAL_SPEC.md"
        assert defaults["dev_story_location"] == "docs/stories"
        assert defaults["epic_location"] == "docs/epics.md"
        assert defaults["output_folder"] == "docs"

    def test_workflow_defaults_cached_on_first_access(self, config_loader: ConfigLoader):
        """Test that workflow defaults are cached after first access."""
        # First call loads and caches
        defaults1 = config_loader.get_workflow_defaults()

        # Second call should return cached version (but as a copy)
        defaults2 = config_loader.get_workflow_defaults()

        assert defaults1 == defaults2
        assert defaults1 is not defaults2  # Should be a copy, not same reference

    def test_workflow_defaults_returns_copy(self, config_loader: ConfigLoader):
        """Test that get_workflow_defaults returns a copy, not the internal dict."""
        defaults1 = config_loader.get_workflow_defaults()
        defaults2 = config_loader.get_workflow_defaults()

        # Modify first dict
        defaults1["new_key"] = "new_value"

        # Second dict should be unaffected
        assert "new_key" not in defaults2

    def test_user_config_overrides_embedded_defaults(self, temp_project_dir: Path):
        """Test that user config workflow_defaults override embedded defaults."""
        # Create user config with override
        user_config = {
            "workflow_defaults": {
                "prd_location": "custom/PRD.md",
                "output_folder": "custom_docs"
            }
        }

        user_config_path = temp_project_dir / "gao-dev.yaml"
        temp_project_dir.mkdir(parents=True, exist_ok=True)
        with open(user_config_path, "w", encoding="utf-8") as f:
            yaml.dump(user_config, f)

        # Create config loader
        config_loader = ConfigLoader(temp_project_dir)
        defaults = config_loader.get_workflow_defaults()

        # Check overrides applied
        assert defaults["prd_location"] == "custom/PRD.md"
        assert defaults["output_folder"] == "custom_docs"

        # Check other defaults still present
        assert "architecture_location" in defaults
        assert defaults["architecture_location"] == "docs/ARCHITECTURE.md"

    def test_workflow_defaults_validates_string_types(self, temp_project_dir: Path):
        """Test that non-string values in workflow_defaults are filtered out."""
        # Create user config with invalid type
        user_config = {
            "workflow_defaults": {
                "prd_location": "docs/PRD.md",
                "invalid_number": 123,
                "invalid_bool": True,
                "invalid_dict": {"key": "value"},
                "valid_string": "docs/valid.md"
            }
        }

        user_config_path = temp_project_dir / "gao-dev.yaml"
        temp_project_dir.mkdir(parents=True, exist_ok=True)
        with open(user_config_path, "w", encoding="utf-8") as f:
            yaml.dump(user_config, f)

        # Create config loader
        config_loader = ConfigLoader(temp_project_dir)
        defaults = config_loader.get_workflow_defaults()

        # Valid strings should be present
        assert defaults["prd_location"] == "docs/PRD.md"
        assert defaults["valid_string"] == "docs/valid.md"

        # Invalid types should be filtered out
        assert "invalid_number" not in defaults
        assert "invalid_bool" not in defaults
        assert "invalid_dict" not in defaults

    def test_workflow_defaults_handles_missing_section_gracefully(
        self, temp_project_dir: Path
    ):
        """Test that missing workflow_defaults section returns empty dict for overrides."""
        # Create user config without workflow_defaults section
        user_config = {
            "git_auto_commit": True,
            "claude_model": "claude-sonnet-4"
        }

        user_config_path = temp_project_dir / "gao-dev.yaml"
        temp_project_dir.mkdir(parents=True, exist_ok=True)
        with open(user_config_path, "w", encoding="utf-8") as f:
            yaml.dump(user_config, f)

        # Create config loader
        config_loader = ConfigLoader(temp_project_dir)
        defaults = config_loader.get_workflow_defaults()

        # Should still return embedded defaults
        assert isinstance(defaults, dict)
        assert len(defaults) > 0
        assert "prd_location" in defaults

    def test_workflow_defaults_handles_empty_section(self, temp_project_dir: Path):
        """Test that empty workflow_defaults section works correctly."""
        # Create user config with empty workflow_defaults
        user_config = {"workflow_defaults": {}}

        user_config_path = temp_project_dir / "gao-dev.yaml"
        temp_project_dir.mkdir(parents=True, exist_ok=True)
        with open(user_config_path, "w", encoding="utf-8") as f:
            yaml.dump(user_config, f)

        # Create config loader
        config_loader = ConfigLoader(temp_project_dir)
        defaults = config_loader.get_workflow_defaults()

        # Should return embedded defaults
        assert isinstance(defaults, dict)
        assert len(defaults) > 0

    def test_workflow_defaults_error_handling(self, config_loader: ConfigLoader, monkeypatch):
        """Test that errors in loading defaults are handled gracefully."""
        # Force an error by making defaults attribute invalid
        def mock_get_with_error(key, default=None):
            if key == "workflow_defaults":
                raise RuntimeError("Simulated error")
            return default

        # Patch the defaults dictionary to cause an error
        original_defaults = config_loader.defaults
        monkeypatch.setattr(config_loader, "defaults", None)

        # Clear cache if exists
        if hasattr(config_loader, "_workflow_defaults"):
            delattr(config_loader, "_workflow_defaults")

        # Should return empty dict on error
        defaults = config_loader.get_workflow_defaults()
        assert defaults == {}

        # Restore
        monkeypatch.setattr(config_loader, "defaults", original_defaults)


class TestConfigLoaderWorkflowDefaultsIntegration:
    """Integration tests for workflow defaults with ConfigLoader."""

    @pytest.fixture
    def temp_project_dir(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        project_dir = tmp_path / "integration_project"
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir

    def test_workflow_defaults_available_after_construction(self, temp_project_dir: Path):
        """Test that workflow defaults are available immediately after construction."""
        config_loader = ConfigLoader(temp_project_dir)

        # Should be able to get defaults without additional setup
        defaults = config_loader.get_workflow_defaults()
        assert len(defaults) > 0

    def test_workflow_defaults_persist_across_calls(self, temp_project_dir: Path):
        """Test that workflow defaults persist correctly across multiple calls."""
        config_loader = ConfigLoader(temp_project_dir)

        # Make multiple calls
        defaults1 = config_loader.get_workflow_defaults()
        defaults2 = config_loader.get_workflow_defaults()
        defaults3 = config_loader.get_workflow_defaults()

        # All should return same values
        assert defaults1 == defaults2 == defaults3

    def test_workflow_defaults_with_complex_user_config(self, temp_project_dir: Path):
        """Test workflow defaults with complex user configuration."""
        # Create comprehensive user config
        user_config = {
            "workflow_defaults": {
                "prd_location": "custom/docs/PRD.md",
                "architecture_location": "custom/docs/ARCH.md",
                "output_folder": "custom_output",
                "custom_variable": "custom/path/file.md"
            },
            "git_auto_commit": True,
            "claude_model": "claude-sonnet-4",
            "features": {
                "provider_abstraction_enabled": True
            }
        }

        user_config_path = temp_project_dir / "gao-dev.yaml"
        with open(user_config_path, "w", encoding="utf-8") as f:
            yaml.dump(user_config, f)

        # Create config loader
        config_loader = ConfigLoader(temp_project_dir)
        defaults = config_loader.get_workflow_defaults()

        # Check custom overrides applied
        assert defaults["prd_location"] == "custom/docs/PRD.md"
        assert defaults["architecture_location"] == "custom/docs/ARCH.md"
        assert defaults["output_folder"] == "custom_output"
        assert defaults["custom_variable"] == "custom/path/file.md"

        # Check embedded defaults still present for non-overridden values
        assert "epic_location" in defaults
        assert "dev_story_location" in defaults

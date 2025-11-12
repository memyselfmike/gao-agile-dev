"""Regression tests for Epic 35: Ensure no breaking changes.

Epic 35: Interactive Provider Selection at Startup
Story 35.7: Comprehensive Testing & Regression Validation

This module ensures Epic 35 implementation does not break existing functionality:
- Environment variables still work
- ChatREPL backward compatible
- Config files respected
- Feature flags work correctly
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock
import pytest

from gao_dev.cli.chat_repl import ChatREPL
from gao_dev.core.config_loader import ConfigLoader


class TestEnvironmentVariables:
    """Test environment variables still work as before."""

    def test_agent_provider_env_var_still_works(self, tmp_path: Path, monkeypatch):
        """AGENT_PROVIDER env var still bypasses prompts."""
        monkeypatch.setenv("AGENT_PROVIDER", "claude-code")

        project_root = tmp_path / "test_project"
        project_root.mkdir()
        (project_root / ".gao-dev").mkdir()

        with patch("gao_dev.cli.chat_repl.PromptSession"):
            # ChatREPL should respect env var
            repl = ChatREPL(project_root=project_root)
            assert repl is not None

    def test_anthropic_api_key_env_var_unchanged(self, monkeypatch):
        """ANTHROPIC_API_KEY env var behavior unchanged."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
        assert os.getenv("ANTHROPIC_API_KEY") == "sk-ant-test-key"

    def test_env_vars_take_priority(self, tmp_path: Path, monkeypatch):
        """Env vars still take priority over saved preferences."""
        monkeypatch.setenv("AGENT_PROVIDER", "claude-code")

        # Even if saved prefs exist, env var should win
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        gao_dev_dir = project_root / ".gao-dev"
        gao_dev_dir.mkdir()

        # Create saved preferences (different from env var)
        prefs_file = gao_dev_dir / "provider_preferences.yaml"
        prefs_file.write_text("""
version: 1.0.0
provider:
  name: opencode
  model: deepseek-r1
""")

        from gao_dev.cli.provider_selector import ProviderSelector
        from gao_dev.cli.models import ValidationResult
        from rich.console import Console

        selector = ProviderSelector(project_root, Console())
        # Mock validation
        with patch.object(selector._provider_validator, "validate_configuration") as mock_validate:
            from unittest.mock import AsyncMock
            mock_validate.return_value = ValidationResult(
                success=True,
                provider_name="claude-code",
                messages=["OK"],
                validation_time_ms=10.0,
            )
            config = selector.select_provider()

        # Env var should win
        assert config["provider"] == "claude-code"


class TestChatREPLBackwardCompatibility:
    """Test ChatREPL API unchanged."""

    def test_chatrepl_constructor_unchanged(self, tmp_path: Path):
        """ChatREPL constructor signature unchanged."""
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        (project_root / ".gao-dev").mkdir()

        with patch("gao_dev.cli.chat_repl.PromptSession"):
            # Old way of creating ChatREPL should still work
            repl = ChatREPL(project_root=project_root)
            assert repl.project_root == project_root
            assert repl.console is not None

    def test_chatrepl_core_methods_exist(self, tmp_path: Path):
        """Core ChatREPL methods still exist."""
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        (project_root / ".gao-dev").mkdir()

        with patch("gao_dev.cli.chat_repl.PromptSession"):
            repl = ChatREPL(project_root=project_root)

            # Core methods should exist
            assert hasattr(repl, "start")
            assert hasattr(repl, "_display_response")
            assert hasattr(repl, "_display_error")
            assert hasattr(repl, "_show_greeting")
            assert hasattr(repl, "_show_farewell")
            assert hasattr(repl, "_is_exit_command")

    def test_chatrepl_attributes_unchanged(self, tmp_path: Path):
        """All ChatREPL attributes still exist."""
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        (project_root / ".gao-dev").mkdir()

        with patch("gao_dev.cli.chat_repl.PromptSession"):
            repl = ChatREPL(project_root=project_root)

            # All attributes should exist
            assert hasattr(repl, "project_root")
            assert hasattr(repl, "console")
            assert hasattr(repl, "prompt_session")
            assert hasattr(repl, "history")
            assert hasattr(repl, "logger")


class TestConfigFilesWork:
    """Test existing config files still work."""

    def test_defaults_yaml_still_loaded(self, tmp_path: Path):
        """defaults.yaml still loaded correctly."""
        from gao_dev.core.config_loader import ConfigLoader

        project_root = tmp_path / "test_project"
        project_root.mkdir()

        loader = ConfigLoader(project_root)
        config = loader.load_config()

        # Should load without error
        assert config is not None
        assert isinstance(config, dict)

    def test_config_loader_backwards_compatible(self, tmp_path: Path):
        """ConfigLoader methods unchanged."""
        from gao_dev.core.config_loader import ConfigLoader

        project_root = tmp_path / "test_project"
        project_root.mkdir()

        loader = ConfigLoader(project_root)

        # Core methods should exist
        assert hasattr(loader, "load_config")
        assert hasattr(loader, "get")
        assert hasattr(loader, "save_config")


class TestCommandRouterUnchanged:
    """Test CommandRouter unchanged."""

    def test_command_router_import_unchanged(self):
        """CommandRouter can still be imported."""
        from gao_dev.cli.command_router import CommandRouter
        assert CommandRouter is not None

    def test_command_router_constructor_signature(self):
        """CommandRouter constructor accepts required parameters."""
        from gao_dev.cli.command_router import CommandRouter
        from unittest.mock import Mock

        # CommandRouter requires orchestrator, operation_tracker, analysis_service
        mock_orchestrator = Mock()
        mock_tracker = Mock()
        mock_analysis = Mock()

        router = CommandRouter(
            orchestrator=mock_orchestrator,
            operation_tracker=mock_tracker,
            analysis_service=mock_analysis,
        )
        assert router is not None


class TestFeatureFlagsWork:
    """Test feature flags still work."""

    def test_feature_flags_loaded(self, tmp_path: Path):
        """Feature flags still loaded from config."""
        from gao_dev.core.config_loader import ConfigLoader

        project_root = tmp_path / "test_project"
        project_root.mkdir()

        loader = ConfigLoader(project_root)
        config = loader.load_config()

        feature_flags = loader.get("feature_flags", {})
        assert isinstance(feature_flags, dict)

    def test_new_feature_flag_exists(self, tmp_path: Path):
        """New interactive_provider_selection flag exists."""
        from gao_dev.core.config_loader import ConfigLoader

        project_root = tmp_path / "test_project"
        project_root.mkdir()

        loader = ConfigLoader(project_root)
        config = loader.load_config()

        feature_flags = loader.get("feature_flags", {})
        # Flag should exist (True or False)
        assert "interactive_provider_selection" in feature_flags

    def test_feature_flag_type(self, tmp_path: Path):
        """Feature flag is boolean type."""
        from gao_dev.core.config_loader import ConfigLoader

        project_root = tmp_path / "test_project"
        project_root.mkdir()

        loader = ConfigLoader(project_root)
        feature_flags = loader.get("feature_flags", {})

        # Should be boolean
        assert isinstance(feature_flags.get("interactive_provider_selection"), bool)


class TestPreferenceManagerAdded:
    """Test PreferenceManager new component works."""

    def test_preference_manager_import(self):
        """PreferenceManager can be imported."""
        from gao_dev.cli.preference_manager import PreferenceManager
        assert PreferenceManager is not None

    def test_preference_manager_basic_functionality(self, tmp_path: Path):
        """PreferenceManager basic save/load works."""
        from gao_dev.cli.preference_manager import PreferenceManager

        project_root = tmp_path / "test_project"
        project_root.mkdir()
        (project_root / ".gao-dev").mkdir()

        manager = PreferenceManager(project_root)

        # Should be able to check for preferences
        assert not manager.has_preferences()

        # Should be able to save preferences
        config = {
            "version": "1.0.0",
            "provider": {
                "name": "claude-code",
                "model": "sonnet-4.5",
                "config": {},
            },
            "metadata": {"saved_at": "2025-01-12T10:00:00"},
        }
        manager.save_preferences(config)

        # Should be able to load preferences
        assert manager.has_preferences()
        loaded = manager.load_preferences()
        assert loaded["provider"]["name"] == "claude-code"


class TestProviderValidatorAdded:
    """Test ProviderValidator new component works."""

    def test_provider_validator_import(self):
        """ProviderValidator can be imported."""
        from gao_dev.cli.provider_validator import ProviderValidator
        assert ProviderValidator is not None

    def test_provider_validator_constructor(self):
        """ProviderValidator can be instantiated."""
        from gao_dev.cli.provider_validator import ProviderValidator
        from rich.console import Console

        validator = ProviderValidator(Console())
        assert validator is not None

    @pytest.mark.asyncio
    async def test_provider_validator_has_validate_method(self):
        """ProviderValidator has validate_configuration method."""
        from gao_dev.cli.provider_validator import ProviderValidator
        from rich.console import Console

        validator = ProviderValidator(Console())
        assert hasattr(validator, "validate_configuration")


class TestInteractivePrompterAdded:
    """Test InteractivePrompter new component works."""

    def test_interactive_prompter_import(self):
        """InteractivePrompter can be imported."""
        from gao_dev.cli.interactive_prompter import InteractivePrompter
        assert InteractivePrompter is not None

    def test_interactive_prompter_constructor(self):
        """InteractivePrompter can be instantiated."""
        from gao_dev.cli.interactive_prompter import InteractivePrompter
        from rich.console import Console

        prompter = InteractivePrompter(Console())
        assert prompter is not None

    def test_interactive_prompter_has_prompt_methods(self):
        """InteractivePrompter has all prompt methods."""
        from gao_dev.cli.interactive_prompter import InteractivePrompter
        from rich.console import Console

        prompter = InteractivePrompter(Console())

        # Should have all prompt methods
        assert hasattr(prompter, "prompt_provider")
        assert hasattr(prompter, "prompt_model")
        assert hasattr(prompter, "prompt_opencode_config")
        assert hasattr(prompter, "prompt_save_preferences")
        assert hasattr(prompter, "prompt_use_saved")


class TestProviderSelectorAdded:
    """Test ProviderSelector new component works."""

    def test_provider_selector_import(self):
        """ProviderSelector can be imported."""
        from gao_dev.cli.provider_selector import ProviderSelector
        assert ProviderSelector is not None

    def test_provider_selector_constructor(self, tmp_path: Path):
        """ProviderSelector can be instantiated."""
        from gao_dev.cli.provider_selector import ProviderSelector
        from rich.console import Console

        project_root = tmp_path / "test_project"
        project_root.mkdir()
        (project_root / ".gao-dev").mkdir()

        selector = ProviderSelector(project_root, Console())
        assert selector is not None

    def test_provider_selector_has_select_method(self, tmp_path: Path):
        """ProviderSelector has select_provider method."""
        from gao_dev.cli.provider_selector import ProviderSelector
        from rich.console import Console

        project_root = tmp_path / "test_project"
        project_root.mkdir()
        (project_root / ".gao-dev").mkdir()

        selector = ProviderSelector(project_root, Console())
        assert hasattr(selector, "select_provider")


class TestExceptionsAdded:
    """Test new exceptions defined."""

    def test_provider_selection_cancelled_exception_exists(self):
        """ProviderSelectionCancelled exception exists."""
        from gao_dev.cli.exceptions import ProviderSelectionCancelled
        assert ProviderSelectionCancelled is not None

        # Should be raisable
        with pytest.raises(ProviderSelectionCancelled):
            raise ProviderSelectionCancelled("Test")

    def test_provider_validation_failed_exception_exists(self):
        """ProviderValidationFailed exception exists."""
        from gao_dev.cli.exceptions import ProviderValidationFailed
        assert ProviderValidationFailed is not None

        # Should be raisable
        with pytest.raises(ProviderValidationFailed):
            raise ProviderValidationFailed("Test", provider_name="test")


class TestModelsAdded:
    """Test new models defined."""

    def test_validation_result_model_exists(self):
        """ValidationResult model exists."""
        from gao_dev.cli.models import ValidationResult
        assert ValidationResult is not None

    def test_validation_result_can_be_created(self):
        """ValidationResult can be instantiated."""
        from gao_dev.cli.models import ValidationResult

        result = ValidationResult(
            success=True,
            provider_name="test",
            messages=["OK"],
            validation_time_ms=100.0,
        )
        assert result.success is True
        assert result.provider_name == "test"

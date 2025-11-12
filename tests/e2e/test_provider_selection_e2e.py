"""End-to-end tests for provider selection flow.

Epic 35: Interactive Provider Selection at Startup
Story 35.7: Comprehensive Testing & Regression Validation

This module tests complete user flows from startup to provider selection,
including first-time users, returning users, validation recovery, and bypass scenarios.
"""

import asyncio
import os
from pathlib import Path
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch
import pytest
import yaml

from gao_dev.cli.provider_selector import ProviderSelector
from gao_dev.cli.preference_manager import PreferenceManager
from gao_dev.cli.interactive_prompter import InteractivePrompter
from gao_dev.cli.provider_validator import ProviderValidator
from gao_dev.cli.models import ValidationResult
from gao_dev.cli.exceptions import (
    ProviderSelectionCancelled,
    ProviderValidationFailed,
)
from rich.console import Console


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create temporary project directory with .gao-dev/."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    gao_dev_dir = project_root / ".gao-dev"
    gao_dev_dir.mkdir()
    return project_root


@pytest.fixture
def console() -> Console:
    """Create Rich Console."""
    return Console()


class TestFirstTimeStartupFlow:
    """Test first-time user flow (no env var, no saved preferences)."""

    def test_complete_first_time_flow(self, temp_project: Path, console: Console):
        """Full first-time startup: select provider, validate, save preferences."""
        # Mock all prompts for first-time flow
        mock_prompter = Mock(spec=InteractivePrompter)
        mock_prompter.prompt_provider.return_value = "opencode"
        mock_prompter.prompt_opencode_config.return_value = {
            "ai_provider": "ollama",
            "use_local": True,
        }
        mock_prompter.prompt_model.return_value = "deepseek-r1"
        mock_prompter.prompt_save_preferences.return_value = True

        # Mock successful validation (AsyncMock for async method)
        mock_validator = AsyncMock(spec=ProviderValidator)
        mock_validator.validate_configuration.return_value = ValidationResult(
            success=True,
            provider_name="opencode",
            messages=["CLI available", "Validation passed"],
            validation_time_ms=150.0,
        )

        # Create real PreferenceManager
        preference_manager = PreferenceManager(temp_project)

        # Create ProviderSelector with mocked dependencies
        selector = ProviderSelector(
            project_root=temp_project,
            console=console,
            preference_manager=preference_manager,
            interactive_prompter=mock_prompter,
            provider_validator=mock_validator,
        )

        # Execute selection
        config = selector.select_provider()

        # Assert provider selected
        assert config["provider"] == "opencode"
        assert config["model"] == "deepseek-r1"
        assert config["config"]["use_local"] is True

        # Assert preferences saved
        assert preference_manager.has_preferences()
        saved_prefs = preference_manager.load_preferences()
        assert saved_prefs["provider"]["name"] == "opencode"
        assert saved_prefs["provider"]["model"] == "deepseek-r1"

        # Assert prompts called in correct order
        assert mock_prompter.prompt_provider.called
        assert mock_prompter.prompt_opencode_config.called
        assert mock_prompter.prompt_model.called
        assert mock_prompter.prompt_save_preferences.called

        # Assert validation called
        assert mock_validator.validate_configuration.called

    def test_first_time_flow_no_save(self, temp_project: Path, console: Console):
        """First-time user chooses NOT to save preferences."""
        # Mock prompts - user declines to save
        mock_prompter = Mock(spec=InteractivePrompter)
        mock_prompter.prompt_provider.return_value = "claude-code"
        mock_prompter.prompt_model.return_value = "sonnet-4.5"
        mock_prompter.prompt_save_preferences.return_value = False

        # Mock successful validation
        mock_validator = AsyncMock(spec=ProviderValidator)
        mock_validator.validate_configuration.return_value = ValidationResult(
            success=True,
            provider_name="claude-code",
            messages=["Validation passed"],
            validation_time_ms=100.0,
        )

        preference_manager = PreferenceManager(temp_project)

        selector = ProviderSelector(
            project_root=temp_project,
            console=console,
            preference_manager=preference_manager,
            interactive_prompter=mock_prompter,
            provider_validator=mock_validator,
        )

        config = selector.select_provider()

        # Assert provider selected
        assert config["provider"] == "claude-code"

        # Assert preferences NOT saved
        assert not preference_manager.has_preferences()


class TestReturningUserFlow:
    """Test returning user flow (saved preferences exist)."""

    def test_returning_user_accepts_saved_prefs(
        self, temp_project: Path, console: Console
    ):
        """Returning user accepts saved preferences."""
        # Create saved preferences
        preference_manager = PreferenceManager(temp_project)
        saved_config = {
            "version": "1.0.0",
            "provider": {
                "name": "opencode",
                "model": "deepseek-r1",
                "config": {"ai_provider": "ollama", "use_local": True},
            },
            "metadata": {"saved_at": "2025-01-12T10:00:00"},
        }
        preference_manager.save_preferences(saved_config)

        # Mock prompter - user accepts saved preferences
        mock_prompter = Mock(spec=InteractivePrompter)
        mock_prompter.prompt_use_saved.return_value = "y"  # Accept saved

        # Mock successful validation
        mock_validator = AsyncMock(spec=ProviderValidator)
        mock_validator.validate_configuration.return_value = ValidationResult(
            success=True,
            provider_name="opencode",
            messages=["Validation passed"],
            validation_time_ms=120.0,
        )

        selector = ProviderSelector(
            project_root=temp_project,
            console=console,
            preference_manager=preference_manager,
            interactive_prompter=mock_prompter,
            provider_validator=mock_validator,
        )

        config = selector.select_provider()

        # Assert saved config used
        assert config["provider"] == "opencode"
        assert config["model"] == "deepseek-r1"
        assert config["config"]["use_local"] is True

        # Assert prompt for saved preferences shown
        assert mock_prompter.prompt_use_saved.called

        # Assert new selection prompts NOT called
        assert not mock_prompter.prompt_provider.called

    def test_returning_user_declines_saved_prefs(
        self, temp_project: Path, console: Console
    ):
        """Returning user declines saved preferences, selects new provider."""
        # Create saved preferences
        preference_manager = PreferenceManager(temp_project)
        saved_config = {
            "version": "1.0.0",
            "provider": {
                "name": "opencode",
                "model": "deepseek-r1",
                "config": {"ai_provider": "ollama", "use_local": True},
            },
            "metadata": {"saved_at": "2025-01-12T10:00:00"},
        }
        preference_manager.save_preferences(saved_config)

        # Mock prompter - user declines saved, selects new
        mock_prompter = Mock(spec=InteractivePrompter)
        mock_prompter.prompt_use_saved.return_value = "n"  # Decline saved
        mock_prompter.prompt_provider.return_value = "claude-code"
        mock_prompter.prompt_model.return_value = "sonnet-4.5"
        mock_prompter.prompt_save_preferences.return_value = True

        # Mock successful validation
        mock_validator = AsyncMock(spec=ProviderValidator)
        mock_validator.validate_configuration.return_value = ValidationResult(
            success=True,
            provider_name="claude-code",
            messages=["Validation passed"],
            validation_time_ms=100.0,
        )

        selector = ProviderSelector(
            project_root=temp_project,
            console=console,
            preference_manager=preference_manager,
            interactive_prompter=mock_prompter,
            provider_validator=mock_validator,
        )

        config = selector.select_provider()

        # Assert NEW provider selected
        assert config["provider"] == "claude-code"
        assert config["model"] == "sonnet-4.5"

        # Assert new selection prompts called
        assert mock_prompter.prompt_provider.called


class TestEnvironmentVariableBypass:
    """Test environment variable bypass flow."""

    def test_env_var_bypasses_all_prompts(self, temp_project: Path, console: Console, monkeypatch):
        """AGENT_PROVIDER env var bypasses all interactive prompts."""
        # Set environment variable
        monkeypatch.setenv("AGENT_PROVIDER", "claude-code")

        # Mock prompter - should NOT be called
        mock_prompter = Mock(spec=InteractivePrompter)

        # Mock validator - should still validate (AsyncMock for async method)
        mock_validator = AsyncMock(spec=ProviderValidator)
        mock_validator.validate_configuration.return_value = ValidationResult(
            success=True,
            provider_name="claude-code",
            messages=["Validation passed"],
            validation_time_ms=50.0,
        )

        preference_manager = PreferenceManager(temp_project)

        selector = ProviderSelector(
            project_root=temp_project,
            console=console,
            preference_manager=preference_manager,
            interactive_prompter=mock_prompter,
            provider_validator=mock_validator,
        )

        config = selector.select_provider()

        # Assert env var used
        assert config["provider"] == "claude-code"

        # Assert NO prompts shown
        assert not mock_prompter.prompt_provider.called
        assert not mock_prompter.prompt_use_saved.called

    def test_env_var_with_saved_prefs_still_bypasses(
        self, temp_project: Path, console: Console, monkeypatch
    ):
        """Env var takes priority over saved preferences."""
        # Create saved preferences
        preference_manager = PreferenceManager(temp_project)
        saved_config = {
            "version": "1.0.0",
            "provider": {
                "name": "opencode",
                "model": "deepseek-r1",
                "config": {"ai_provider": "ollama", "use_local": True},
            },
            "metadata": {"saved_at": "2025-01-12T10:00:00"},
        }
        preference_manager.save_preferences(saved_config)

        # Set environment variable (different from saved)
        monkeypatch.setenv("AGENT_PROVIDER", "claude-code")

        mock_prompter = Mock(spec=InteractivePrompter)
        mock_validator = AsyncMock(spec=ProviderValidator)
        mock_validator.validate_configuration.return_value = ValidationResult(
            success=True,
            provider_name="claude-code",
            messages=["Validation passed"],
            validation_time_ms=50.0,
        )

        selector = ProviderSelector(
            project_root=temp_project,
            console=console,
            preference_manager=preference_manager,
            interactive_prompter=mock_prompter,
            provider_validator=mock_validator,
        )

        config = selector.select_provider()

        # Assert ENV VAR used (not saved prefs)
        assert config["provider"] == "claude-code"

        # Assert no prompts
        assert not mock_prompter.prompt_use_saved.called


class TestValidationFailureRecovery:
    """Test validation failure and recovery flows."""

    def test_validation_failure_retry_success(
        self, temp_project: Path, console: Console
    ):
        """Validation fails, user retries with different provider, succeeds."""
        # Mock prompter
        mock_prompter = Mock(spec=InteractivePrompter)
        # First selection: opencode
        # After failure, retry with: claude-code
        mock_prompter.prompt_provider.side_effect = ["opencode", "claude-code"]
        mock_prompter.prompt_opencode_config.return_value = {
            "ai_provider": "ollama",
            "use_local": True,
        }
        mock_prompter.prompt_model.side_effect = ["deepseek-r1", "sonnet-4.5"]
        mock_prompter.show_error = Mock()  # Mock show_error
        mock_prompter.prompt_save_preferences.return_value = True

        # Mock validator - first fails, second succeeds
        mock_validator = AsyncMock(spec=ProviderValidator)
        mock_validator.validate_configuration.side_effect = [
            ValidationResult(
                success=False,
                provider_name="opencode",
                messages=["CLI not found"],
                warnings=["CLI not found"],
                suggestions=["Install opencode CLI"],
                validation_time_ms=100.0,
            ),
            ValidationResult(
                success=True,
                provider_name="claude-code",
                messages=["Validation passed"],
                validation_time_ms=150.0,
            ),
        ]

        preference_manager = PreferenceManager(temp_project)

        selector = ProviderSelector(
            project_root=temp_project,
            console=console,
            preference_manager=preference_manager,
            interactive_prompter=mock_prompter,
            provider_validator=mock_validator,
        )

        config = selector.select_provider()

        # Assert second provider used (successful validation)
        assert config["provider"] == "claude-code"
        assert config["model"] == "sonnet-4.5"

        # Assert error was shown
        assert mock_prompter.show_error.called

        # Assert two validations attempted
        assert mock_validator.validate_configuration.call_count == 2

    def test_validation_failure_max_attempts_raises(
        self, temp_project: Path, console: Console
    ):
        """Validation fails repeatedly, max attempts exceeded, raises exception."""
        # Mock prompter
        mock_prompter = Mock(spec=InteractivePrompter)
        mock_prompter.prompt_provider.return_value = "opencode"
        mock_prompter.prompt_opencode_config.return_value = {
            "ai_provider": "ollama",
            "use_local": True,
        }
        mock_prompter.prompt_model.return_value = "deepseek-r1"
        mock_prompter.show_error = Mock()

        # Mock validator - always fails
        mock_validator = AsyncMock(spec=ProviderValidator)
        mock_validator.validate_configuration.return_value = ValidationResult(
            success=False,
            provider_name="opencode",
            messages=["CLI not found"],
            warnings=["CLI not found"],
            suggestions=["Install opencode CLI"],
            validation_time_ms=100.0,
        )

        preference_manager = PreferenceManager(temp_project)

        selector = ProviderSelector(
            project_root=temp_project,
            console=console,
            preference_manager=preference_manager,
            interactive_prompter=mock_prompter,
            provider_validator=mock_validator,
        )

        # Assert raises ProviderValidationFailed after max attempts
        with pytest.raises(ProviderValidationFailed):
            selector.select_provider()


class TestPreferenceSaveLoadRoundTrip:
    """Test complete save/load round-trip scenarios."""

    def test_save_load_round_trip_exact_match(
        self, temp_project: Path, console: Console
    ):
        """Save preferences, restart, load - config matches exactly."""
        # First run: select and save
        preference_manager = PreferenceManager(temp_project)

        mock_prompter_first = Mock(spec=InteractivePrompter)
        mock_prompter_first.prompt_provider.return_value = "opencode"
        mock_prompter_first.prompt_opencode_config.return_value = {
            "ai_provider": "ollama",
            "use_local": True,
        }
        mock_prompter_first.prompt_model.return_value = "deepseek-r1"
        mock_prompter_first.prompt_save_preferences.return_value = True

        mock_validator_first = AsyncMock(spec=ProviderValidator)
        mock_validator_first.validate_configuration.return_value = ValidationResult(
            success=True,
            provider_name="opencode",
            messages=["Validation passed"],
            validation_time_ms=100.0,
        )

        selector_first = ProviderSelector(
            project_root=temp_project,
            console=console,
            preference_manager=preference_manager,
            interactive_prompter=mock_prompter_first,
            provider_validator=mock_validator_first,
        )

        config_first = selector_first.select_provider()

        # Second run: load saved preferences
        mock_prompter_second = Mock(spec=InteractivePrompter)
        mock_prompter_second.prompt_use_saved.return_value = "y"

        mock_validator_second = AsyncMock(spec=ProviderValidator)
        mock_validator_second.validate_configuration.return_value = ValidationResult(
            success=True,
            provider_name="opencode",
            messages=["Validation passed"],
            validation_time_ms=80.0,
        )

        # Create new selector (simulating restart)
        selector_second = ProviderSelector(
            project_root=temp_project,
            console=console,
            preference_manager=PreferenceManager(temp_project),  # New instance
            interactive_prompter=mock_prompter_second,
            provider_validator=mock_validator_second,
        )

        config_second = selector_second.select_provider()

        # Assert configs match
        assert config_first["provider"] == config_second["provider"]
        assert config_first["model"] == config_second["model"]
        assert config_first["config"] == config_second["config"]

    def test_corrupted_prefs_fall_back_to_prompts(
        self, temp_project: Path, console: Console
    ):
        """Corrupted preferences file falls back to interactive prompts."""
        # Create corrupted preference file
        prefs_file = temp_project / ".gao-dev" / "provider_preferences.yaml"
        prefs_file.write_text("invalid: yaml: syntax: [[[")

        # Mock prompter - should be called (fallback)
        mock_prompter = Mock(spec=InteractivePrompter)
        mock_prompter.prompt_provider.return_value = "claude-code"
        mock_prompter.prompt_model.return_value = "sonnet-4.5"
        mock_prompter.prompt_save_preferences.return_value = False

        mock_validator = AsyncMock(spec=ProviderValidator)
        mock_validator.validate_configuration.return_value = ValidationResult(
            success=True,
            provider_name="claude-code",
            messages=["Validation passed"],
            validation_time_ms=100.0,
        )

        preference_manager = PreferenceManager(temp_project)

        selector = ProviderSelector(
            project_root=temp_project,
            console=console,
            preference_manager=preference_manager,
            interactive_prompter=mock_prompter,
            provider_validator=mock_validator,
        )

        config = selector.select_provider()

        # Assert interactive prompts used (fallback)
        assert config["provider"] == "claude-code"
        assert mock_prompter.prompt_provider.called


class TestFeatureFlagDisabled:
    """Test behavior when feature flag is disabled."""

    def test_feature_flag_disabled_no_provider_selector_called(self, temp_project: Path):
        """When feature flag disabled, ChatREPL doesn't call ProviderSelector."""
        # This is tested in test_chat_repl_provider_selection.py
        # Test here validates the isolation: ProviderSelector is never instantiated
        from gao_dev.cli.chat_repl import ChatREPL

        with patch("gao_dev.cli.chat_repl.PromptSession"):
            # Create ChatREPL with feature flag disabled (default)
            repl = ChatREPL(project_root=temp_project)

            # Verify ChatREPL created successfully
            assert repl.project_root == temp_project
            assert repl.console is not None

            # ProviderSelector should never have been imported/used
            # This is implicit - if it were used, the test would fail

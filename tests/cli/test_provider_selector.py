"""Tests for ProviderSelector orchestrator.

Epic 35: Interactive Provider Selection at Startup
Story 35.5: ProviderSelector Implementation

CRAAP Resolution: All tests use mocked dependencies for isolation.
"""

import asyncio
import os
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from rich.console import Console

from gao_dev.cli.exceptions import (
    ProviderSelectionCancelled,
    ProviderValidationFailed,
)
from gao_dev.cli.models import ValidationResult
from gao_dev.cli.preference_manager import PreferenceManager
from gao_dev.cli.interactive_prompter import InteractivePrompter
from gao_dev.cli.provider_validator import ProviderValidator
from gao_dev.cli.provider_selector import ProviderSelector


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Create temporary project root."""
    gao_dev_dir = tmp_path / ".gao-dev"
    gao_dev_dir.mkdir(parents=True, exist_ok=True)
    return tmp_path


@pytest.fixture
def console() -> Console:
    """Create Rich Console."""
    return Console()


@pytest.fixture
def mock_preference_manager() -> Mock:
    """Create mocked PreferenceManager."""
    mock = Mock(spec=PreferenceManager)
    mock.has_preferences = Mock(return_value=False)
    mock.load_preferences = Mock(return_value=None)
    mock.save_preferences = Mock()
    return mock


@pytest.fixture
def mock_interactive_prompter() -> Mock:
    """Create mocked InteractivePrompter."""
    mock = Mock(spec=InteractivePrompter)
    mock.prompt_provider = Mock(return_value="claude-code")
    mock.prompt_model = Mock(return_value="sonnet-4.5")
    mock.prompt_opencode_config = Mock(
        return_value={"ai_provider": "ollama", "use_local": True}
    )
    mock.prompt_save_preferences = Mock(return_value=False)
    mock.prompt_use_saved = Mock(return_value="y")
    mock.show_error = Mock()
    return mock


@pytest.fixture
def mock_provider_validator() -> Mock:
    """Create mocked ProviderValidator."""
    mock = Mock(spec=ProviderValidator)
    # Make validate_configuration async
    async def async_validate(*args: Any, **kwargs: Any) -> ValidationResult:
        return ValidationResult(
            success=True,
            provider_name="claude-code",
            messages=["Validation passed"],
        )

    mock.validate_configuration = AsyncMock(side_effect=async_validate)
    return mock


@pytest.fixture
def selector(
    project_root: Path,
    console: Console,
    mock_preference_manager: Mock,
    mock_interactive_prompter: Mock,
    mock_provider_validator: Mock,
) -> ProviderSelector:
    """Create ProviderSelector with mocked dependencies."""
    return ProviderSelector(
        project_root=project_root,
        console=console,
        preference_manager=mock_preference_manager,
        interactive_prompter=mock_interactive_prompter,
        provider_validator=mock_provider_validator,
    )


# ============================================================================
# Priority 1: Environment Variable Tests
# ============================================================================


def test_use_environment_variable_set(
    selector: ProviderSelector, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Environment variable returns config when set."""
    monkeypatch.setenv("AGENT_PROVIDER", "claude-code")

    result = selector.use_environment_variable()

    assert result is not None
    assert result["provider"] == "claude-code"
    assert "model" in result
    assert "config" in result


def test_use_environment_variable_not_set(selector: ProviderSelector) -> None:
    """Returns None when environment variable not set."""
    result = selector.use_environment_variable()
    assert result is None


def test_use_environment_variable_empty(
    selector: ProviderSelector, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Empty environment variable returns None."""
    monkeypatch.setenv("AGENT_PROVIDER", "")

    result = selector.use_environment_variable()
    assert result is None


def test_select_provider_env_var_bypasses_prompts(
    selector: ProviderSelector,
    mock_interactive_prompter: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Environment variable bypasses all prompts."""
    monkeypatch.setenv("AGENT_PROVIDER", "opencode")

    result = selector.select_provider()

    assert result["provider"] == "opencode"
    # No prompts should be called
    mock_interactive_prompter.prompt_provider.assert_not_called()
    mock_interactive_prompter.prompt_use_saved.assert_not_called()


# ============================================================================
# Priority 2: Saved Preferences Tests
# ============================================================================


def test_has_saved_preferences_true(
    selector: ProviderSelector, mock_preference_manager: Mock
) -> None:
    """Returns True when valid preferences exist."""
    mock_preference_manager.has_preferences.return_value = True

    assert selector.has_saved_preferences() is True


def test_has_saved_preferences_false(
    selector: ProviderSelector, mock_preference_manager: Mock
) -> None:
    """Returns False when no preferences exist."""
    mock_preference_manager.has_preferences.return_value = False

    assert selector.has_saved_preferences() is False


def test_select_provider_saved_accepted(
    selector: ProviderSelector,
    mock_preference_manager: Mock,
    mock_interactive_prompter: Mock,
) -> None:
    """Saved preferences used when accepted."""
    saved_prefs = {
        "version": "1.0.0",
        "provider": {
            "name": "opencode",
            "model": "deepseek-r1",
            "config": {"ai_provider": "ollama", "use_local": True},
        },
    }
    mock_preference_manager.has_preferences.return_value = True
    mock_preference_manager.load_preferences.return_value = saved_prefs
    mock_interactive_prompter.prompt_use_saved.return_value = "y"

    result = selector.select_provider()

    assert result["provider"] == "opencode"
    assert result["model"] == "deepseek-r1"
    mock_interactive_prompter.prompt_use_saved.assert_called_once()
    # Should not prompt for new provider
    mock_interactive_prompter.prompt_provider.assert_not_called()


def test_select_provider_saved_rejected(
    selector: ProviderSelector,
    mock_preference_manager: Mock,
    mock_interactive_prompter: Mock,
) -> None:
    """Interactive prompts when saved rejected."""
    saved_prefs = {
        "version": "1.0.0",
        "provider": {
            "name": "opencode",
            "model": "deepseek-r1",
            "config": {},
        },
    }
    mock_preference_manager.has_preferences.return_value = True
    mock_preference_manager.load_preferences.return_value = saved_prefs
    mock_interactive_prompter.prompt_use_saved.return_value = "n"
    mock_interactive_prompter.prompt_provider.return_value = "claude-code"
    mock_interactive_prompter.prompt_model.return_value = "sonnet-4.5"

    result = selector.select_provider()

    assert result["provider"] == "claude-code"
    mock_interactive_prompter.prompt_use_saved.assert_called_once()
    mock_interactive_prompter.prompt_provider.assert_called_once()


# ============================================================================
# Priority 3: Interactive Prompts Tests
# ============================================================================


def test_select_provider_no_saved(
    selector: ProviderSelector,
    mock_preference_manager: Mock,
    mock_interactive_prompter: Mock,
) -> None:
    """Interactive prompts when no saved prefs."""
    mock_preference_manager.has_preferences.return_value = False
    mock_interactive_prompter.prompt_provider.return_value = "claude-code"
    mock_interactive_prompter.prompt_model.return_value = "sonnet-4.5"

    result = selector.select_provider()

    assert result["provider"] == "claude-code"
    assert result["model"] == "sonnet-4.5"
    mock_interactive_prompter.prompt_provider.assert_called_once()
    mock_interactive_prompter.prompt_model.assert_called_once()


def test_select_provider_opencode_prompts_config(
    selector: ProviderSelector,
    mock_preference_manager: Mock,
    mock_interactive_prompter: Mock,
) -> None:
    """OpenCode selection prompts for additional config."""
    mock_preference_manager.has_preferences.return_value = False
    mock_interactive_prompter.prompt_provider.return_value = "opencode"
    mock_interactive_prompter.prompt_opencode_config.return_value = {
        "ai_provider": "anthropic",
        "use_local": False,
    }
    mock_interactive_prompter.prompt_model.return_value = "sonnet-4.5"

    result = selector.select_provider()

    assert result["provider"] == "opencode"
    assert result["config"]["ai_provider"] == "anthropic"
    assert result["config"]["use_local"] is False
    mock_interactive_prompter.prompt_opencode_config.assert_called_once()


# ============================================================================
# Validation Tests
# ============================================================================


def test_select_provider_validation_passes(
    selector: ProviderSelector,
    mock_preference_manager: Mock,
    mock_provider_validator: Mock,
) -> None:
    """Provider is validated before returning."""
    mock_preference_manager.has_preferences.return_value = False

    result = selector.select_provider()

    assert result["provider"] == "claude-code"
    # Validate was called
    mock_provider_validator.validate_configuration.assert_called_once()


def test_select_provider_validation_fails_retry(
    selector: ProviderSelector,
    mock_preference_manager: Mock,
    mock_interactive_prompter: Mock,
    mock_provider_validator: Mock,
) -> None:
    """Validation failure prompts retry."""
    mock_preference_manager.has_preferences.return_value = False

    # First validation fails, second succeeds
    async def validation_side_effect(*args: Any, **kwargs: Any) -> ValidationResult:
        # Use call count to alternate
        if mock_provider_validator.validate_configuration.call_count == 1:
            return ValidationResult(
                success=False,
                provider_name="claude-code",
                warnings=["CLI not found"],
                suggestions=["Install Claude Code"],
            )
        else:
            return ValidationResult(
                success=True,
                provider_name="opencode",
                messages=["Validation passed"],
            )

    mock_provider_validator.validate_configuration = AsyncMock(
        side_effect=validation_side_effect
    )

    # First prompt returns claude-code (fails), second returns opencode (succeeds)
    mock_interactive_prompter.prompt_provider.side_effect = [
        "claude-code",
        "opencode",
    ]
    mock_interactive_prompter.prompt_model.return_value = "deepseek-r1"
    mock_interactive_prompter.prompt_opencode_config.return_value = {
        "ai_provider": "ollama",
        "use_local": True,
    }

    result = selector.select_provider()

    # Should return the second provider (opencode)
    assert result["provider"] == "opencode"
    # Show error should be called once (for first failure)
    mock_interactive_prompter.show_error.assert_called_once()
    # Two prompts (first failed, retry succeeded)
    assert mock_interactive_prompter.prompt_provider.call_count == 2


def test_select_provider_validation_max_attempts(
    selector: ProviderSelector,
    mock_preference_manager: Mock,
    mock_interactive_prompter: Mock,
    mock_provider_validator: Mock,
) -> None:
    """Raises error after 3 validation failures."""
    mock_preference_manager.has_preferences.return_value = False

    # Always fail validation
    async def always_fail(*args: Any, **kwargs: Any) -> ValidationResult:
        return ValidationResult(
            success=False,
            provider_name="claude-code",
            warnings=["CLI not found"],
        )

    mock_provider_validator.validate_configuration = AsyncMock(side_effect=always_fail)
    mock_interactive_prompter.prompt_provider.return_value = "claude-code"
    mock_interactive_prompter.prompt_model.return_value = "sonnet-4.5"

    with pytest.raises(ProviderValidationFailed) as exc_info:
        selector.select_provider()

    assert "max attempts" in str(exc_info.value).lower()
    # Should have called prompt 3 times
    assert mock_interactive_prompter.prompt_provider.call_count == 3


# ============================================================================
# Cancellation Tests
# ============================================================================


def test_select_provider_cancelled_keyboard_interrupt(
    selector: ProviderSelector,
    mock_preference_manager: Mock,
    mock_interactive_prompter: Mock,
) -> None:
    """Ctrl+C raises ProviderSelectionCancelled."""
    mock_preference_manager.has_preferences.return_value = False
    mock_interactive_prompter.prompt_provider.side_effect = KeyboardInterrupt()

    with pytest.raises(ProviderSelectionCancelled) as exc_info:
        selector.select_provider()

    assert "cancelled" in str(exc_info.value).lower()


# ============================================================================
# Preference Saving Tests
# ============================================================================


def test_select_provider_saves_preferences(
    selector: ProviderSelector,
    mock_preference_manager: Mock,
    mock_interactive_prompter: Mock,
) -> None:
    """Preferences saved when user agrees."""
    mock_preference_manager.has_preferences.return_value = False
    mock_interactive_prompter.prompt_provider.return_value = "claude-code"
    mock_interactive_prompter.prompt_model.return_value = "sonnet-4.5"
    mock_interactive_prompter.prompt_save_preferences.return_value = True

    result = selector.select_provider()

    assert result["provider"] == "claude-code"
    # save_preferences should be called
    mock_preference_manager.save_preferences.assert_called_once()
    saved_data = mock_preference_manager.save_preferences.call_args[0][0]
    assert saved_data["provider"]["name"] == "claude-code"
    assert saved_data["provider"]["model"] == "sonnet-4.5"


def test_select_provider_no_save(
    selector: ProviderSelector,
    mock_preference_manager: Mock,
    mock_interactive_prompter: Mock,
) -> None:
    """Preferences not saved when user declines."""
    mock_preference_manager.has_preferences.return_value = False
    mock_interactive_prompter.prompt_provider.return_value = "claude-code"
    mock_interactive_prompter.prompt_model.return_value = "sonnet-4.5"
    mock_interactive_prompter.prompt_save_preferences.return_value = False

    result = selector.select_provider()

    assert result["provider"] == "claude-code"
    # save_preferences should NOT be called
    mock_preference_manager.save_preferences.assert_not_called()


# ============================================================================
# Dependency Injection Tests
# ============================================================================


def test_selector_creates_real_dependencies(
    project_root: Path, console: Console
) -> None:
    """ProviderSelector creates real instances when None provided."""
    selector = ProviderSelector(project_root, console)

    # Should have created real instances
    assert selector._preference_manager is not None
    assert isinstance(selector._preference_manager, PreferenceManager)
    assert selector._interactive_prompter is not None
    assert isinstance(selector._interactive_prompter, InteractivePrompter)
    assert selector._provider_validator is not None
    assert isinstance(selector._provider_validator, ProviderValidator)


# ============================================================================
# Integration Tests (Real Dependencies)
# ============================================================================


@pytest.mark.integration
def test_full_flow_first_time_integration(
    project_root: Path, console: Console
) -> None:
    """Full flow for first-time user with real dependencies."""
    selector = ProviderSelector(project_root, console)

    # Mock user input
    with patch.object(
        selector._interactive_prompter,
        "prompt_provider",
        return_value="claude-code",
    ):
        with patch.object(
            selector._interactive_prompter,
            "prompt_model",
            return_value="sonnet-4.5",
        ):
            with patch.object(
                selector._interactive_prompter,
                "prompt_save_preferences",
                return_value=False,
            ):
                # Mock validation to pass
                async def mock_validate(*args: Any, **kwargs: Any) -> ValidationResult:
                    return ValidationResult(
                        success=True,
                        provider_name="claude-code",
                    )

                with patch.object(
                    selector._provider_validator,
                    "validate_configuration",
                    side_effect=mock_validate,
                ):
                    result = selector.select_provider()

                    assert result["provider"] == "claude-code"
                    assert result["model"] == "sonnet-4.5"


@pytest.mark.integration
def test_full_flow_returning_user_integration(
    project_root: Path, console: Console
) -> None:
    """Full flow for returning user with saved preferences."""
    selector = ProviderSelector(project_root, console)

    # Create saved preferences
    saved_prefs = {
        "version": "1.0.0",
        "provider": {
            "name": "opencode",
            "model": "deepseek-r1",
            "config": {"ai_provider": "ollama", "use_local": True},
        },
        "metadata": {"last_updated": "2025-01-12T10:00:00Z"},
    }
    selector._preference_manager.save_preferences(saved_prefs)

    # Mock user accepting saved config
    with patch.object(
        selector._interactive_prompter,
        "prompt_use_saved",
        return_value="y",
    ):
        # Mock validation to pass
        async def mock_validate(*args: Any, **kwargs: Any) -> ValidationResult:
            return ValidationResult(
                success=True,
                provider_name="opencode",
            )

        with patch.object(
            selector._provider_validator,
            "validate_configuration",
            side_effect=mock_validate,
        ):
            result = selector.select_provider()

            assert result["provider"] == "opencode"
            assert result["model"] == "deepseek-r1"


# ============================================================================
# Edge Cases
# ============================================================================


def test_select_provider_handles_change_option(
    selector: ProviderSelector,
    mock_preference_manager: Mock,
    mock_interactive_prompter: Mock,
) -> None:
    """Handles 'c' (change) option for saved preferences."""
    saved_prefs = {
        "version": "1.0.0",
        "provider": {
            "name": "opencode",
            "model": "deepseek-r1",
            "config": {},
        },
    }
    mock_preference_manager.has_preferences.return_value = True
    mock_preference_manager.load_preferences.return_value = saved_prefs
    mock_interactive_prompter.prompt_use_saved.return_value = "c"  # Change
    mock_interactive_prompter.prompt_provider.return_value = "claude-code"
    mock_interactive_prompter.prompt_model.return_value = "sonnet-4.5"

    result = selector.select_provider()

    # Should prompt for new selection
    assert result["provider"] == "claude-code"
    mock_interactive_prompter.prompt_provider.assert_called_once()


def test_use_environment_variable_with_model(
    selector: ProviderSelector, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Environment variable can specify provider:model format."""
    monkeypatch.setenv("AGENT_PROVIDER", "opencode:deepseek-r1")

    result = selector.use_environment_variable()

    assert result is not None
    assert result["provider"] == "opencode"
    assert result["model"] == "deepseek-r1"


def test_select_provider_env_var_with_validation_failure(
    selector: ProviderSelector,
    mock_interactive_prompter: Mock,
    mock_provider_validator: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Environment variable validated, falls back if invalid."""
    monkeypatch.setenv("AGENT_PROVIDER", "invalid-provider")

    # Validation fails for env var, succeeds for interactive
    call_count = 0

    async def conditional_validate(*args: Any, **kwargs: Any) -> ValidationResult:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call (env var) fails
            return ValidationResult(
                success=False,
                provider_name="invalid-provider",
                warnings=["Provider not found"],
            )
        else:
            # Second call (interactive) succeeds
            return ValidationResult(
                success=True,
                provider_name="claude-code",
            )

    mock_provider_validator.validate_configuration = AsyncMock(
        side_effect=conditional_validate
    )

    # Should fall back to prompts after env var validation fails
    result = selector.select_provider()

    # Falls back to interactive prompts (mock returns claude-code)
    assert result["provider"] == "claude-code"
    mock_interactive_prompter.prompt_provider.assert_called_once()

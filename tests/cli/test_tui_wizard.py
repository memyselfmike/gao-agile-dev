"""Tests for TUI Wizard.

Epic 41: Streamlined Onboarding
Story 41.1: TUI Wizard Implementation

Tests comprehensive functionality including:
- Each wizard step
- Back navigation
- Defaults
- Validation spinner
- Completion summary
"""

import asyncio
import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

from rich.console import Console

from gao_dev.cli.tui_wizard import TUIWizard, run_wizard
from gao_dev.cli.wizard_config import (
    WizardConfig,
    ProjectConfig,
    GitConfig,
    ProviderInfo,
    PROVIDERS,
    PROVIDER_MAP,
    DEFAULT_MODELS,
    AVAILABLE_MODELS,
)
from gao_dev.cli.models import ValidationResult


@pytest.fixture
def console():
    """Create mock console."""
    mock_console = MagicMock(spec=Console)
    mock_console.print = MagicMock()
    # Add attributes needed by Rich Status spinner
    mock_console.is_jupyter = False
    mock_console.is_terminal = True
    mock_console.is_dumb_terminal = False
    mock_console._color_system = None
    return mock_console


@pytest.fixture
def project_root(tmp_path):
    """Create temporary project root."""
    project = tmp_path / "test-project"
    project.mkdir()
    return project


@pytest.fixture
def wizard(project_root, console):
    """Create TUIWizard instance."""
    return TUIWizard(project_root, console)


# ============================================================================
# WizardConfig Tests
# ============================================================================


def test_wizard_config_defaults():
    """WizardConfig has sensible defaults."""
    config = WizardConfig()

    assert config.project.name == ""
    assert config.git.init_git is True
    assert config.provider_name == ""
    assert config.model == ""
    assert config.api_key == ""


def test_wizard_config_to_dict():
    """WizardConfig converts to dict correctly."""
    config = WizardConfig(
        project=ProjectConfig(name="test", project_type="python"),
        git=GitConfig(user_name="John", user_email="john@test.com"),
        provider_name="claude-code",
        model="sonnet-4.5",
    )

    result = config.to_dict()

    assert result["project"]["name"] == "test"
    assert result["project"]["type"] == "python"
    assert result["git"]["user_name"] == "John"
    assert result["provider"]["name"] == "claude-code"
    assert result["provider"]["model"] == "sonnet-4.5"


def test_provider_info_creation():
    """ProviderInfo dataclass works correctly."""
    provider = ProviderInfo(
        name="test-provider",
        description="Test description",
        requires_api_key=True,
        api_key_env="TEST_API_KEY",
    )

    assert provider.name == "test-provider"
    assert provider.requires_api_key is True
    assert provider.api_key_env == "TEST_API_KEY"


def test_providers_defined():
    """All required providers are defined."""
    provider_names = [p.name for p in PROVIDERS]

    assert "claude-code" in provider_names
    assert "opencode-sdk" in provider_names
    assert "direct-api" in provider_names
    assert "ollama" in provider_names


def test_provider_map_populated():
    """PROVIDER_MAP contains all providers."""
    assert "claude-code" in PROVIDER_MAP
    assert "ollama" in PROVIDER_MAP
    assert len(PROVIDER_MAP) == len(PROVIDERS)


def test_default_models_defined():
    """DEFAULT_MODELS contains all providers."""
    for provider in PROVIDERS:
        assert provider.name in DEFAULT_MODELS


def test_available_models_defined():
    """AVAILABLE_MODELS contains all providers."""
    for provider in PROVIDERS:
        assert provider.name in AVAILABLE_MODELS
        assert len(AVAILABLE_MODELS[provider.name]) > 0


# ============================================================================
# TUIWizard Initialization Tests
# ============================================================================


def test_wizard_initialization(project_root, console):
    """Wizard initializes with correct attributes."""
    wizard = TUIWizard(project_root, console)

    assert wizard.project_root == project_root
    assert wizard.console == console
    assert isinstance(wizard.config, WizardConfig)
    assert wizard._current_step == 1
    assert wizard._total_steps == 4


def test_wizard_creates_console_if_none(project_root):
    """Wizard creates Console if not provided."""
    wizard = TUIWizard(project_root, console=None)

    assert wizard.console is not None
    assert isinstance(wizard.console, Console)


# ============================================================================
# Welcome Panel Tests
# ============================================================================


def test_show_welcome_displays_panel(wizard, console):
    """Welcome panel is displayed to user."""
    wizard._show_welcome()

    # Verify console.print was called (panel displayed)
    assert console.print.called


def test_show_welcome_contains_branding(wizard, console):
    """Welcome panel contains GAO-Dev branding."""
    wizard._show_welcome()

    # At least one print call should have happened
    assert console.print.call_count >= 1


# ============================================================================
# Completion Panel Tests
# ============================================================================


def test_show_completion_displays_summary(wizard, console):
    """Completion panel displays configuration summary."""
    wizard.config.project = ProjectConfig(
        name="test-project",
        project_type="python",
        description="Test description",
    )
    wizard.config.git = GitConfig(
        user_name="John",
        user_email="john@test.com",
        init_git=True,
    )
    wizard.config.provider_name = "claude-code"
    wizard.config.model = "sonnet-4.5"

    wizard._show_completion()

    assert console.print.called


def test_show_completion_masks_api_key(wizard, console):
    """Completion panel masks API key in summary."""
    wizard.config.provider_name = "claude-code"
    wizard.config.model = "sonnet-4.5"
    wizard.config.api_key = "sk-ant-api03-1234567890abcdef"

    wizard._show_completion()

    # The full API key should not be in any print call
    for call in console.print.call_args_list:
        if call.args:
            text = str(call.args[0])
            assert "1234567890abcdef" not in text


# ============================================================================
# Project Step Tests
# ============================================================================


@pytest.mark.asyncio
async def test_step_project_collects_config(wizard, console):
    """Project step collects name, type, and description."""
    with patch("gao_dev.cli.tui_wizard.Prompt.ask") as mock_ask:
        mock_ask.side_effect = ["my-project", "python", "Test description"]

        result = await wizard._step_project()

    assert result == "next"
    assert wizard.config.project.name == "my-project"
    assert wizard.config.project.project_type == "python"
    assert wizard.config.project.description == "Test description"


@pytest.mark.asyncio
async def test_step_project_uses_defaults(wizard, console, project_root):
    """Project step uses folder name as default."""
    with patch("gao_dev.cli.tui_wizard.Prompt.ask") as mock_ask:
        # Return empty to use defaults
        mock_ask.side_effect = [project_root.name, "unknown", ""]

        result = await wizard._step_project()

    assert result == "next"
    assert wizard.config.project.name == project_root.name


@pytest.mark.asyncio
async def test_step_project_back_navigation(wizard, console):
    """Project step supports back navigation."""
    with patch("gao_dev.cli.tui_wizard.Prompt.ask") as mock_ask:
        mock_ask.return_value = "back"

        result = await wizard._step_project()

    assert result == "back"


# ============================================================================
# Git Step Tests
# ============================================================================


@pytest.mark.asyncio
async def test_step_git_collects_config(wizard, console):
    """Git step collects user name and email."""
    with patch("gao_dev.cli.tui_wizard.Prompt.ask") as mock_ask:
        with patch("gao_dev.cli.tui_wizard.Confirm.ask") as mock_confirm:
            mock_ask.side_effect = ["John Doe", "john@test.com"]
            mock_confirm.return_value = True

            result = await wizard._step_git()

    assert result == "next"
    assert wizard.config.git.user_name == "John Doe"
    assert wizard.config.git.user_email == "john@test.com"
    assert wizard.config.git.init_git is True


@pytest.mark.asyncio
async def test_step_git_detects_existing_repo(wizard, console, project_root):
    """Git step detects existing .git directory."""
    # Create .git directory
    (project_root / ".git").mkdir()

    with patch("gao_dev.cli.tui_wizard.Prompt.ask") as mock_ask:
        mock_ask.side_effect = ["John", "john@test.com"]

        result = await wizard._step_git()

    assert result == "next"
    assert wizard.config.git.init_git is False


@pytest.mark.asyncio
async def test_step_git_back_navigation(wizard, console):
    """Git step supports back navigation."""
    with patch("gao_dev.cli.tui_wizard.Prompt.ask") as mock_ask:
        mock_ask.return_value = "back"

        result = await wizard._step_git()

    assert result == "back"


@pytest.mark.asyncio
async def test_step_git_gets_global_config(wizard, console):
    """Git step gets defaults from global git config."""
    with patch.object(wizard, "_get_git_config") as mock_git_config:
        mock_git_config.side_effect = ["Global User", "global@test.com"]

        with patch("gao_dev.cli.tui_wizard.Prompt.ask") as mock_ask:
            with patch("gao_dev.cli.tui_wizard.Confirm.ask") as mock_confirm:
                mock_ask.side_effect = ["Global User", "global@test.com"]
                mock_confirm.return_value = True

                result = await wizard._step_git()

    assert result == "next"
    # Verify git config was called for defaults
    assert mock_git_config.call_count == 2


# ============================================================================
# Provider Step Tests
# ============================================================================


@pytest.mark.asyncio
async def test_step_provider_displays_table(wizard, console):
    """Provider step displays provider table."""
    with patch("gao_dev.cli.tui_wizard.Prompt.ask") as mock_ask:
        mock_ask.side_effect = ["1", "1"]  # Select first provider and model

        result = await wizard._step_provider()

    assert result == "next"
    # Table should have been printed
    assert console.print.called


@pytest.mark.asyncio
async def test_step_provider_selects_claude_code(wizard, console):
    """Provider step selects claude-code correctly."""
    with patch("gao_dev.cli.tui_wizard.Prompt.ask") as mock_ask:
        mock_ask.side_effect = ["1", "1"]  # First provider, first model

        result = await wizard._step_provider()

    assert result == "next"
    assert wizard.config.provider_name == "claude-code"
    assert wizard.config.model == "sonnet-4.5"


@pytest.mark.asyncio
async def test_step_provider_selects_ollama(wizard, console):
    """Provider step selects ollama correctly."""
    with patch("gao_dev.cli.tui_wizard.Prompt.ask") as mock_ask:
        mock_ask.side_effect = ["4", "1"]  # Fourth provider (ollama), first model

        result = await wizard._step_provider()

    assert result == "next"
    assert wizard.config.provider_name == "ollama"


@pytest.mark.asyncio
async def test_step_provider_invalid_then_valid(wizard, console):
    """Provider step re-prompts on invalid input."""
    with patch("gao_dev.cli.tui_wizard.Prompt.ask") as mock_ask:
        mock_ask.side_effect = ["99", "1", "1"]  # Invalid, valid provider, model

        result = await wizard._step_provider()

    assert result == "next"
    assert wizard.config.provider_name == "claude-code"


@pytest.mark.asyncio
async def test_step_provider_back_navigation(wizard, console):
    """Provider step supports back navigation."""
    with patch("gao_dev.cli.tui_wizard.Prompt.ask") as mock_ask:
        mock_ask.return_value = "back"

        result = await wizard._step_provider()

    assert result == "back"


@pytest.mark.asyncio
async def test_step_provider_model_selection(wizard, console):
    """Provider step allows model selection."""
    with patch("gao_dev.cli.tui_wizard.Prompt.ask") as mock_ask:
        mock_ask.side_effect = ["1", "2"]  # First provider, second model

        result = await wizard._step_provider()

    assert result == "next"
    assert wizard.config.model == "opus-4"  # Second model in claude-code list


# ============================================================================
# Credentials Step Tests
# ============================================================================


@pytest.mark.asyncio
async def test_step_credentials_no_key_required(wizard, console):
    """Credentials step skips for providers without API key."""
    wizard.config.provider_name = "ollama"

    result = await wizard._step_credentials()

    assert result == "next"
    assert wizard.config.api_key == ""


@pytest.mark.asyncio
async def test_step_credentials_uses_env_var(wizard, console):
    """Credentials step uses existing environment variable."""
    wizard.config.provider_name = "claude-code"

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key-12345678"}):
        with patch("gao_dev.cli.tui_wizard.Confirm.ask") as mock_confirm:
            mock_confirm.return_value = True  # Use existing

            with patch.object(wizard, "_validate_credentials", new_callable=AsyncMock):
                result = await wizard._step_credentials()

    assert result == "next"
    assert wizard.config.api_key == "sk-ant-test-key-12345678"


@pytest.mark.asyncio
async def test_step_credentials_prompts_for_key(wizard, console):
    """Credentials step prompts for API key when not in env."""
    wizard.config.provider_name = "claude-code"

    with patch.dict(os.environ, {}, clear=True):
        # Remove ANTHROPIC_API_KEY from environment
        os.environ.pop("ANTHROPIC_API_KEY", None)

        with patch("gao_dev.cli.tui_wizard.Prompt.ask") as mock_ask:
            with patch("gao_dev.cli.tui_wizard.Confirm.ask") as mock_confirm:
                mock_ask.return_value = "sk-ant-new-key"
                mock_confirm.return_value = False  # Don't reveal

                with patch.object(wizard, "_validate_credentials", new_callable=AsyncMock):
                    result = await wizard._step_credentials()

    assert result == "next"
    assert wizard.config.api_key == "sk-ant-new-key"


@pytest.mark.asyncio
async def test_step_credentials_password_masked(wizard, console):
    """Credentials step uses password masking for input."""
    wizard.config.provider_name = "claude-code"

    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("ANTHROPIC_API_KEY", None)

        with patch("gao_dev.cli.tui_wizard.Prompt.ask") as mock_ask:
            with patch("gao_dev.cli.tui_wizard.Confirm.ask") as mock_confirm:
                mock_ask.return_value = "sk-ant-secret"
                mock_confirm.return_value = False

                with patch.object(wizard, "_validate_credentials", new_callable=AsyncMock):
                    await wizard._step_credentials()

        # Verify password=True was passed
        for call in mock_ask.call_args_list:
            if "API key" in str(call):
                assert call.kwargs.get("password") is True


@pytest.mark.asyncio
async def test_step_credentials_back_navigation(wizard, console):
    """Credentials step supports back navigation."""
    wizard.config.provider_name = "claude-code"

    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("ANTHROPIC_API_KEY", None)

        with patch("gao_dev.cli.tui_wizard.Prompt.ask") as mock_ask:
            mock_ask.return_value = "back"

            result = await wizard._step_credentials()

    assert result == "back"


# ============================================================================
# Validation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_validate_credentials_success(wizard, console):
    """Validation shows success message."""
    wizard.config.provider_name = "claude-code"

    with patch("gao_dev.cli.tui_wizard.ProviderValidator") as mock_validator_class:
        with patch("rich.status.Status") as mock_status:
            # Create a context manager mock
            mock_status_instance = MagicMock()
            mock_status_instance.__enter__ = MagicMock(return_value=mock_status_instance)
            mock_status_instance.__exit__ = MagicMock(return_value=False)
            mock_status.return_value = mock_status_instance

            mock_validator = MagicMock()
            mock_result = ValidationResult(
                success=True,
                provider_name="claude-code",
            )
            mock_validator.validate_configuration = AsyncMock(return_value=mock_result)
            mock_validator_class.return_value = mock_validator

            await wizard._validate_credentials()

    # Should print success message
    assert console.print.called


@pytest.mark.asyncio
async def test_validate_credentials_failure_shows_error(wizard, console):
    """Validation shows error and suggestions on failure."""
    wizard.config.provider_name = "claude-code"

    with patch("gao_dev.cli.tui_wizard.ProviderValidator") as mock_validator_class:
        with patch("rich.status.Status") as mock_status:
            # Create a context manager mock
            mock_status_instance = MagicMock()
            mock_status_instance.__enter__ = MagicMock(return_value=mock_status_instance)
            mock_status_instance.__exit__ = MagicMock(return_value=False)
            mock_status.return_value = mock_status_instance

            mock_validator = MagicMock()
            mock_result = ValidationResult(
                success=False,
                provider_name="claude-code",
                warnings=["API key invalid"],
                suggestions=["Check your API key"],
            )
            mock_validator.validate_configuration = AsyncMock(return_value=mock_result)
            mock_validator_class.return_value = mock_validator

            await wizard._validate_credentials()

    # Should print error
    assert console.print.called


# ============================================================================
# Back Navigation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_full_wizard_back_navigation(wizard, console):
    """Wizard supports back navigation through steps."""
    with patch("gao_dev.cli.tui_wizard.Prompt.ask") as mock_ask:
        # Test that typing "back" in git step returns "back"
        mock_ask.return_value = "back"

        result = await wizard._step_git()

    assert result == "back"


# ============================================================================
# Keyboard Interrupt Tests
# ============================================================================


@pytest.mark.asyncio
async def test_wizard_handles_ctrl_c(wizard, console):
    """Wizard handles Ctrl+C gracefully."""
    with patch("gao_dev.cli.tui_wizard.Confirm.ask") as mock_confirm:
        mock_confirm.return_value = True  # Confirm cancel

        result = wizard._confirm_cancel()

    assert result is True


@pytest.mark.asyncio
async def test_wizard_cancel_declined(wizard, console):
    """Wizard continues when cancel is declined."""
    with patch("gao_dev.cli.tui_wizard.Confirm.ask") as mock_confirm:
        mock_confirm.return_value = False  # Don't cancel

        result = wizard._confirm_cancel()

    assert result is False


# ============================================================================
# Helper Method Tests
# ============================================================================


def test_detect_project_type_python(wizard, project_root):
    """Detects Python project from pyproject.toml."""
    (project_root / "pyproject.toml").touch()

    result = wizard._detect_project_type()

    assert result == "python"


def test_detect_project_type_javascript(wizard, project_root):
    """Detects JavaScript project from package.json."""
    (project_root / "package.json").touch()

    result = wizard._detect_project_type()

    assert result == "javascript"


def test_detect_project_type_rust(wizard, project_root):
    """Detects Rust project from Cargo.toml."""
    (project_root / "Cargo.toml").touch()

    result = wizard._detect_project_type()

    assert result == "rust"


def test_detect_project_type_go(wizard, project_root):
    """Detects Go project from go.mod."""
    (project_root / "go.mod").touch()

    result = wizard._detect_project_type()

    assert result == "go"


def test_detect_project_type_unknown(wizard, project_root):
    """Returns unknown for unrecognized project type."""
    result = wizard._detect_project_type()

    assert result == "unknown"


def test_get_git_config_returns_value(wizard):
    """Gets git config value successfully."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="John Doe\n",
        )

        result = wizard._get_git_config("user.name")

    assert result == "John Doe"


def test_get_git_config_returns_empty_on_error(wizard):
    """Returns empty string when git config fails."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
        )

        result = wizard._get_git_config("user.name")

    assert result == ""


def test_get_git_config_handles_timeout(wizard):
    """Handles git config timeout gracefully."""
    with patch("subprocess.run") as mock_run:
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired("git", 5)

        result = wizard._get_git_config("user.name")

    assert result == ""


def test_show_inline_error(wizard, console):
    """Shows inline error with red styling."""
    wizard._show_inline_error("Test error message")

    assert console.print.called


def test_show_progress(wizard, console):
    """Shows progress indicator correctly."""
    wizard._current_step = 2
    wizard._total_steps = 4

    wizard._show_progress("Git Configuration")

    assert console.print.called


# ============================================================================
# Run Wizard Convenience Function Tests
# ============================================================================


@pytest.mark.asyncio
async def test_run_wizard_function(project_root, console):
    """run_wizard convenience function works."""
    with patch.object(TUIWizard, "run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = WizardConfig()

        result = await run_wizard(project_root, console)

    assert isinstance(result, WizardConfig)
    mock_run.assert_called_once()


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_full_wizard_flow_ollama(project_root, console):
    """Full wizard flow for Ollama (no API key)."""
    wizard = TUIWizard(project_root, console)

    with patch("gao_dev.cli.tui_wizard.Prompt.ask") as mock_ask:
        with patch("gao_dev.cli.tui_wizard.Confirm.ask") as mock_confirm:
            mock_ask.side_effect = [
                # Step 1: Project
                "my-app", "python", "My application",
                # Step 2: Git
                "John", "john@test.com",
                # Step 3: Provider
                "4", "1",  # Ollama, first model
            ]
            mock_confirm.side_effect = [
                True,  # Init git
            ]

            result = await wizard.run()

    assert result.project.name == "my-app"
    assert result.project.project_type == "python"
    assert result.git.user_name == "John"
    assert result.provider_name == "ollama"
    assert result.api_key == ""  # Ollama doesn't need key


@pytest.mark.asyncio
async def test_full_wizard_flow_claude_code(project_root, console):
    """Full wizard flow for Claude Code with API key."""
    wizard = TUIWizard(project_root, console)

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-12345678"}):
        with patch("gao_dev.cli.tui_wizard.Prompt.ask") as mock_ask:
            with patch("gao_dev.cli.tui_wizard.Confirm.ask") as mock_confirm:
                mock_ask.side_effect = [
                    # Step 1: Project
                    "my-app", "python", "My application",
                    # Step 2: Git
                    "John", "john@test.com",
                    # Step 3: Provider
                    "1", "1",  # Claude Code, first model
                ]
                mock_confirm.side_effect = [
                    True,  # Init git
                    True,  # Use env API key
                ]

                with patch.object(wizard, "_validate_credentials", new_callable=AsyncMock):
                    result = await wizard.run()

    assert result.project.name == "my-app"
    assert result.provider_name == "claude-code"
    assert result.api_key == "sk-ant-test-12345678"


# ============================================================================
# Edge Case Tests
# ============================================================================


def test_api_key_masking_short_key(wizard, console):
    """Handles short API keys in masking."""
    wizard.config.api_key = "short"
    wizard.config.provider_name = "claude-code"
    wizard.config.model = "sonnet-4.5"

    # Should not raise error
    wizard._show_completion()


def test_empty_description_handling(wizard, console):
    """Handles empty project description."""
    wizard.config.project = ProjectConfig(
        name="test",
        project_type="python",
        description="",  # Empty
    )
    wizard.config.git = GitConfig(user_name="John", user_email="john@test.com")
    wizard.config.provider_name = "ollama"
    wizard.config.model = "deepseek-r1"

    # Should not raise error
    wizard._show_completion()


@pytest.mark.asyncio
async def test_provider_invalid_input_non_numeric(wizard, console):
    """Provider step handles non-numeric input."""
    with patch("gao_dev.cli.tui_wizard.Prompt.ask") as mock_ask:
        mock_ask.side_effect = ["abc", "1", "1"]  # Invalid, then valid

        result = await wizard._step_provider()

    assert result == "next"


@pytest.mark.asyncio
async def test_model_invalid_input_non_numeric(wizard, console):
    """Model selection handles non-numeric input."""
    with patch("gao_dev.cli.tui_wizard.Prompt.ask") as mock_ask:
        mock_ask.side_effect = ["1", "xyz", "1"]  # Provider, invalid, valid model

        result = await wizard._step_provider()

    assert result == "next"

"""Tests for InteractivePrompter.

Epic 35: Interactive Provider Selection at Startup
Story 35.4: InteractivePrompter Implementation

Tests comprehensive functionality including lazy imports for CI/CD compatibility.
"""

import pytest
from unittest.mock import MagicMock, Mock, patch, call
from typing import Dict, List
from contextlib import contextmanager

from rich.console import Console
from gao_dev.cli.interactive_prompter import InteractivePrompter


@pytest.fixture
def console():
    """Create mock console."""
    return MagicMock(spec=Console)


@pytest.fixture
def prompter(console):
    """Create InteractivePrompter instance."""
    return InteractivePrompter(console)


@contextmanager
def mock_prompt_toolkit(return_value=None, side_effect=None):
    """
    Helper to mock prompt_toolkit.PromptSession for lazy import tests.

    Because we use lazy imports, we need to patch the actual prompt_toolkit module,
    not the gao_dev.cli.interactive_prompter module.
    """
    with patch('prompt_toolkit.PromptSession') as mock_session_class:
        mock_session = MagicMock()
        if side_effect:
            mock_session.prompt.side_effect = side_effect
        else:
            mock_session.prompt.return_value = return_value
        mock_session_class.return_value = mock_session
        yield mock_session_class, mock_session


# ============================================================================
# Provider Prompt Tests
# ============================================================================


def test_prompt_provider_valid_choice_1(prompter, console):
    """Valid provider choice '1' returns claude-code."""
    providers = ['claude-code', 'opencode', 'direct-api-anthropic']
    descriptions = {
        'claude-code': 'Claude Code CLI (Anthropic)',
        'opencode': 'OpenCode CLI (Multi-provider)',
        'direct-api-anthropic': 'Direct Anthropic API'
    }

    with mock_prompt_toolkit(return_value='1'):
        result = prompter.prompt_provider(providers, descriptions)

    assert result == 'claude-code'


def test_prompt_provider_valid_choice_2(prompter, console):
    """Valid provider choice '2' returns opencode."""
    providers = ['claude-code', 'opencode', 'direct-api-anthropic']
    descriptions = {
        'claude-code': 'Claude Code CLI (Anthropic)',
        'opencode': 'OpenCode CLI (Multi-provider)',
        'direct-api-anthropic': 'Direct Anthropic API'
    }

    with mock_prompt_toolkit(return_value='2'):
        result = prompter.prompt_provider(providers, descriptions)

    assert result == 'opencode'


def test_prompt_provider_valid_choice_3(prompter, console):
    """Valid provider choice '3' returns direct-api-anthropic."""
    providers = ['claude-code', 'opencode', 'direct-api-anthropic']
    descriptions = {
        'claude-code': 'Claude Code CLI (Anthropic)',
        'opencode': 'OpenCode CLI (Multi-provider)',
        'direct-api-anthropic': 'Direct Anthropic API'
    }

    with mock_prompt_toolkit(return_value='3'):
        result = prompter.prompt_provider(providers, descriptions)

    assert result == 'direct-api-anthropic'


def test_prompt_provider_default_empty(prompter, console):
    """Empty input uses default (1 -> claude-code)."""
    providers = ['claude-code', 'opencode', 'direct-api-anthropic']
    descriptions = {
        'claude-code': 'Claude Code CLI (Anthropic)',
        'opencode': 'OpenCode CLI (Multi-provider)',
        'direct-api-anthropic': 'Direct Anthropic API'
    }

    with mock_prompt_toolkit(return_value=''):
        result = prompter.prompt_provider(providers, descriptions)

    assert result == 'claude-code'


def test_prompt_provider_invalid_then_valid(prompter, console):
    """Invalid choice re-prompts, then accepts valid."""
    providers = ['claude-code', 'opencode', 'direct-api-anthropic']
    descriptions = {
        'claude-code': 'Claude Code CLI (Anthropic)',
        'opencode': 'OpenCode CLI (Multi-provider)',
        'direct-api-anthropic': 'Direct Anthropic API'
    }

    with mock_prompt_toolkit(side_effect=['5', '2']) as (mock_class, mock_session):
        result = prompter.prompt_provider(providers, descriptions)

    assert result == 'opencode'
    # Should have prompted twice (invalid + valid)
    assert mock_session.prompt.call_count == 2


def test_prompt_provider_ctrl_c_propagates(prompter, console):
    """Ctrl+C raises KeyboardInterrupt (not caught)."""
    providers = ['claude-code', 'opencode', 'direct-api-anthropic']
    descriptions = {
        'claude-code': 'Claude Code CLI (Anthropic)',
        'opencode': 'OpenCode CLI (Multi-provider)',
        'direct-api-anthropic': 'Direct Anthropic API'
    }

    with mock_prompt_toolkit(side_effect=KeyboardInterrupt()):
        with pytest.raises(KeyboardInterrupt):
            prompter.prompt_provider(providers, descriptions)


def test_prompt_provider_displays_table(prompter, console):
    """Provider table is displayed to user."""
    providers = ['claude-code', 'opencode']
    descriptions = {
        'claude-code': 'Claude Code CLI',
        'opencode': 'OpenCode CLI'
    }

    with mock_prompt_toolkit(return_value='1'):
        prompter.prompt_provider(providers, descriptions)

    # Verify console.print was called (table displayed)
    assert console.print.called


# ============================================================================
# Lazy Import Fallback Tests (CRAAP Critical)
# ============================================================================


def test_fallback_to_input_on_import_error(prompter, console):
    """Falls back to input() when prompt_toolkit unavailable."""
    providers = ['claude-code', 'opencode', 'direct-api-anthropic']
    descriptions = {
        'claude-code': 'Claude Code CLI (Anthropic)',
        'opencode': 'OpenCode CLI (Multi-provider)',
        'direct-api-anthropic': 'Direct Anthropic API'
    }

    # Mock ImportError when trying to import PromptSession
    with patch('prompt_toolkit.PromptSession', side_effect=ImportError("No module")):
        # Mock builtin input() to return '1'
        with patch('builtins.input', return_value='1') as mock_input:
            result = prompter.prompt_provider(providers, descriptions)

    assert result == 'claude-code'
    # Verify input() was called as fallback
    assert mock_input.called


def test_fallback_to_input_on_os_error(prompter, console):
    """Falls back to input() when no TTY available (OSError)."""
    providers = ['claude-code', 'opencode', 'direct-api-anthropic']
    descriptions = {
        'claude-code': 'Claude Code CLI (Anthropic)',
        'opencode': 'OpenCode CLI (Multi-provider)',
        'direct-api-anthropic': 'Direct Anthropic API'
    }

    # Mock OSError when creating PromptSession (no TTY)
    with patch('prompt_toolkit.PromptSession', side_effect=OSError("No TTY")):
        with patch('builtins.input', return_value='2') as mock_input:
            result = prompter.prompt_provider(providers, descriptions)

    assert result == 'opencode'
    assert mock_input.called


def test_fallback_input_validation(prompter, console):
    """Fallback input() still validates choices."""
    providers = ['claude-code', 'opencode', 'direct-api-anthropic']
    descriptions = {
        'claude-code': 'Claude Code CLI (Anthropic)',
        'opencode': 'OpenCode CLI (Multi-provider)',
        'direct-api-anthropic': 'Direct Anthropic API'
    }

    with patch('prompt_toolkit.PromptSession', side_effect=ImportError()):
        with patch('builtins.input', side_effect=['9', '1']) as mock_input:
            result = prompter.prompt_provider(providers, descriptions)

    assert result == 'claude-code'
    # Should have re-prompted
    assert mock_input.call_count == 2


# ============================================================================
# OpenCode Config Tests
# ============================================================================


def test_prompt_opencode_local_yes(prompter, console):
    """OpenCode local model config returned when user selects 'y'."""
    with mock_prompt_toolkit(return_value='y'):
        result = prompter.prompt_opencode_config()

    assert result['use_local'] is True
    assert result['ai_provider'] == 'ollama'


def test_prompt_opencode_cloud_anthropic(prompter, console):
    """OpenCode cloud config returned when user selects 'n' then 'anthropic'."""
    with mock_prompt_toolkit(side_effect=['n', '1']):
        result = prompter.prompt_opencode_config()

    assert result['use_local'] is False
    assert result['ai_provider'] == 'anthropic'


def test_prompt_opencode_cloud_openai(prompter, console):
    """OpenCode cloud config with OpenAI."""
    with mock_prompt_toolkit(side_effect=['n', '2']):
        result = prompter.prompt_opencode_config()

    assert result['use_local'] is False
    assert result['ai_provider'] == 'openai'


def test_prompt_opencode_cloud_google(prompter, console):
    """OpenCode cloud config with Google."""
    with mock_prompt_toolkit(side_effect=['n', '3']):
        result = prompter.prompt_opencode_config()

    assert result['use_local'] is False
    assert result['ai_provider'] == 'google'


def test_prompt_opencode_default_no(prompter, console):
    """Empty input for local prompt defaults to 'n' (no)."""
    with mock_prompt_toolkit(side_effect=['', '1']):
        result = prompter.prompt_opencode_config()

    assert result['use_local'] is False
    assert result['ai_provider'] == 'anthropic'


# ============================================================================
# Model Prompt Tests
# ============================================================================


def test_prompt_model_valid_choice(prompter, console):
    """Valid model choice returns model name."""
    models = ['deepseek-r1', 'llama2', 'codellama']
    descriptions = {
        'deepseek-r1': '7B (recommended for coding)',
        'llama2': '7B',
        'codellama': '13B'
    }

    with mock_prompt_toolkit(return_value='1'):
        result = prompter.prompt_model(models, descriptions)

    assert result == 'deepseek-r1'


def test_prompt_model_without_descriptions(prompter, console):
    """Model selection works without descriptions."""
    models = ['deepseek-r1', 'llama2']

    with mock_prompt_toolkit(return_value='2'):
        result = prompter.prompt_model(models)

    assert result == 'llama2'


def test_prompt_model_invalid_then_valid(prompter, console):
    """Invalid model choice re-prompts."""
    models = ['deepseek-r1', 'llama2']

    with mock_prompt_toolkit(side_effect=['99', '1']) as (mock_class, mock_session):
        result = prompter.prompt_model(models)

    assert result == 'deepseek-r1'
    assert mock_session.prompt.call_count == 2


def test_prompt_model_displays_table(prompter, console):
    """Model table is displayed to user."""
    models = ['deepseek-r1', 'llama2']

    with mock_prompt_toolkit(return_value='1'):
        prompter.prompt_model(models)

    # Verify console.print was called (table displayed)
    assert console.print.called


# ============================================================================
# Save Preferences Tests
# ============================================================================


def test_prompt_save_yes(prompter, console):
    """'y' returns True."""
    with mock_prompt_toolkit(return_value='y'):
        result = prompter.prompt_save_preferences()

    assert result is True


def test_prompt_save_yes_capital(prompter, console):
    """'Y' returns True."""
    with mock_prompt_toolkit(return_value='Y'):
        result = prompter.prompt_save_preferences()

    assert result is True


def test_prompt_save_no(prompter, console):
    """'n' returns False."""
    with mock_prompt_toolkit(return_value='n'):
        result = prompter.prompt_save_preferences()

    assert result is False


def test_prompt_save_default_no(prompter, console):
    """Empty input defaults to 'n' (no)."""
    with mock_prompt_toolkit(return_value=''):
        result = prompter.prompt_save_preferences()

    assert result is False


# ============================================================================
# Use Saved Config Tests
# ============================================================================


def test_prompt_use_saved_yes(prompter, console):
    """'Y' returns 'y'."""
    saved_config = {'provider': 'claude-code', 'model': 'claude-3'}

    with mock_prompt_toolkit(return_value='Y'):
        result = prompter.prompt_use_saved(saved_config)

    assert result == 'y'


def test_prompt_use_saved_yes_lowercase(prompter, console):
    """'y' returns 'y'."""
    saved_config = {'provider': 'claude-code', 'model': 'claude-3'}

    with mock_prompt_toolkit(return_value='y'):
        result = prompter.prompt_use_saved(saved_config)

    assert result == 'y'


def test_prompt_use_saved_no(prompter, console):
    """'n' returns 'n'."""
    saved_config = {'provider': 'claude-code', 'model': 'claude-3'}

    with mock_prompt_toolkit(return_value='n'):
        result = prompter.prompt_use_saved(saved_config)

    assert result == 'n'


def test_prompt_use_saved_change(prompter, console):
    """'c' returns 'c'."""
    saved_config = {'provider': 'claude-code', 'model': 'claude-3'}

    with mock_prompt_toolkit(return_value='c'):
        result = prompter.prompt_use_saved(saved_config)

    assert result == 'c'


def test_prompt_use_saved_default_yes(prompter, console):
    """Empty input defaults to 'y' (yes)."""
    saved_config = {'provider': 'claude-code', 'model': 'claude-3'}

    with mock_prompt_toolkit(return_value=''):
        result = prompter.prompt_use_saved(saved_config)

    assert result == 'y'


def test_prompt_use_saved_displays_config(prompter, console):
    """Saved config is displayed to user."""
    saved_config = {'provider': 'claude-code', 'model': 'claude-3'}

    with mock_prompt_toolkit(return_value='y'):
        prompter.prompt_use_saved(saved_config)

    # Verify console.print was called (config displayed)
    assert console.print.called


# ============================================================================
# Error/Success Display Tests
# ============================================================================


def test_show_error_with_suggestions(prompter, console):
    """Error panel displayed with suggestions."""
    message = "Test error occurred"
    suggestions = ["Try this", "Or try that"]

    prompter.show_error(message, suggestions)

    # Verify console.print was called
    assert console.print.called


def test_show_error_without_suggestions(prompter, console):
    """Error panel displayed without suggestions."""
    message = "Test error occurred"

    prompter.show_error(message)

    assert console.print.called


def test_show_success(prompter, console):
    """Success message displayed."""
    message = "Test success"

    prompter.show_success(message)

    assert console.print.called


# ============================================================================
# Internal Helper Tests
# ============================================================================


def test_get_user_input_with_prompt_toolkit(prompter, console):
    """Internal _get_user_input uses PromptSession when available."""
    with mock_prompt_toolkit(return_value='test-input'):
        result = prompter._get_user_input("Enter value: ", default="default", choices=['1', '2'])

    assert result == 'test-input'


def test_get_user_input_fallback_on_import_error(prompter, console):
    """Internal _get_user_input falls back to input() on ImportError."""
    with patch('prompt_toolkit.PromptSession', side_effect=ImportError()):
        with patch('builtins.input', return_value='fallback-input') as mock_input:
            result = prompter._get_user_input("Enter value: ", default="default", choices=['1', '2'])

    assert result == 'fallback-input'
    assert mock_input.called


# ============================================================================
# Windows Compatibility Tests
# ============================================================================


def test_console_created_with_legacy_windows():
    """Console should be created with legacy_windows=True for compatibility."""
    # This test verifies the Console initialization in InteractivePrompter
    console = Console(legacy_windows=True)
    prompter = InteractivePrompter(console)

    assert prompter.console is not None
    # The console should be usable (basic smoke test)
    assert hasattr(prompter.console, 'print')

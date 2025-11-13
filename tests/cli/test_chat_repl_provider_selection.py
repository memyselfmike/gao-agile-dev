"""Integration tests for ChatREPL provider selection (Story 35.6).

This module tests the integration of ProviderSelector into ChatREPL.__init__()
with various scenarios: env vars, saved preferences, first-time startup,
cancellation, and feature flag disabled.
"""

import pytest
from unittest.mock import patch, Mock
from pathlib import Path


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create temporary project directory with .gao-dev/."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    gao_dev_dir = project_root / ".gao-dev"
    gao_dev_dir.mkdir()
    return project_root


@pytest.fixture
def mock_prompt_session():
    """Mock PromptSession to avoid console issues in tests."""
    with patch("gao_dev.cli.chat_repl.PromptSession") as mock:
        yield mock


def test_chatrepl_feature_flag_disabled_by_default(tmp_project: Path, mock_prompt_session):
    """ChatREPL uses default behavior when feature flag is disabled (default)."""
    # This tests the current state where feature flag is FALSE by default
    from gao_dev.cli.chat_repl import ChatREPL

    # Create ChatREPL - should NOT call ProviderSelector
    repl = ChatREPL(project_root=tmp_project)

    # Verify ChatREPL initialized successfully
    assert repl.project_root == tmp_project
    assert repl.console is not None


def test_chatrepl_feature_flag_enabled_integration():
    """Integration test: ChatREPL with feature flag enabled calls ProviderSelector."""
    # Create temp project
    from pathlib import Path
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        gao_dev_dir = project_root / ".gao-dev"
        gao_dev_dir.mkdir()

        # Mock the entire flow
        with patch("gao_dev.cli.chat_repl.PromptSession"), \
             patch("gao_dev.core.config_loader.ConfigLoader") as mock_config_loader_class, \
             patch("gao_dev.cli.provider_selector.ProviderSelector") as mock_selector_class:

            # Setup config with feature flag enabled
            mock_config = Mock()
            mock_config_loader_class.return_value = mock_config
            mock_config.get.return_value = {"interactive_provider_selection": True}

            # Setup ProviderSelector mock
            mock_selector = Mock()
            mock_selector_class.return_value = mock_selector
            mock_selector.select_provider.return_value = {
                "provider": "claude-code",
                "model": "sonnet-4.5",
                "config": {},
            }

            # Import and create ChatREPL
            from gao_dev.cli.chat_repl import ChatREPL
            repl = ChatREPL(project_root=project_root)

            # Verify ProviderSelector was called
            assert mock_selector_class.called
            assert mock_selector.select_provider.called


def test_chatrepl_cancellation_handling():
    """ChatREPL handles ProviderSelectionCancelled exception."""
    from pathlib import Path
    import tempfile
    from gao_dev.cli.exceptions import ProviderSelectionCancelled

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        gao_dev_dir = project_root / ".gao-dev"
        gao_dev_dir.mkdir()

        # Mock dependencies
        with patch("gao_dev.cli.chat_repl.PromptSession"), \
             patch("gao_dev.core.config_loader.ConfigLoader") as mock_config_loader_class, \
             patch("gao_dev.cli.provider_selector.ProviderSelector") as mock_selector_class:

            # Setup config with feature flag enabled
            mock_config = Mock()
            mock_config_loader_class.return_value = mock_config
            mock_config.get.return_value = {"interactive_provider_selection": True}

            # Setup ProviderSelector to raise cancellation
            mock_selector = Mock()
            mock_selector_class.return_value = mock_selector
            mock_selector.select_provider.side_effect = ProviderSelectionCancelled("User cancelled")

            # Import and create ChatREPL - should raise SystemExit
            from gao_dev.cli.chat_repl import ChatREPL

            # Expect SystemExit(0)
            with pytest.raises(SystemExit) as exc_info:
                repl = ChatREPL(project_root=project_root)

            # Verify exit code is 0
            assert exc_info.value.code == 0


def test_chatrepl_validation_failure_handling():
    """ChatREPL handles ProviderValidationFailed exception."""
    from pathlib import Path
    import tempfile
    from gao_dev.cli.exceptions import ProviderValidationFailed

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        gao_dev_dir = project_root / ".gao-dev"
        gao_dev_dir.mkdir()

        # Mock dependencies
        with patch("gao_dev.cli.chat_repl.PromptSession"), \
             patch("gao_dev.core.config_loader.ConfigLoader") as mock_config_loader_class, \
             patch("gao_dev.cli.provider_selector.ProviderSelector") as mock_selector_class:

            # Setup config with feature flag enabled
            mock_config = Mock()
            mock_config_loader_class.return_value = mock_config
            mock_config.get.return_value = {"interactive_provider_selection": True}

            # Setup ProviderSelector to raise validation failure
            mock_selector = Mock()
            mock_selector_class.return_value = mock_selector
            mock_selector.select_provider.side_effect = ProviderValidationFailed(
                "Validation failed",
                provider_name="claude-code",
                suggestions=["Install CLI"]
            )

            # Import and create ChatREPL - should raise SystemExit
            from gao_dev.cli.chat_repl import ChatREPL

            # Expect SystemExit(1)
            with pytest.raises(SystemExit) as exc_info:
                repl = ChatREPL(project_root=project_root)

            # Verify exit code is 1
            assert exc_info.value.code == 1


def test_chatrepl_backward_compatibility(tmp_project: Path, mock_prompt_session):
    """ChatREPL maintains backward compatibility with existing functionality."""
    from gao_dev.cli.chat_repl import ChatREPL

    # Create ChatREPL
    repl = ChatREPL(project_root=tmp_project)

    # Verify all existing attributes still exist
    assert repl.project_root == tmp_project
    assert repl.console is not None
    assert repl.prompt_session is not None
    assert repl.history is not None
    assert repl.logger is not None

    # Verify exit command detection still works
    assert repl._is_exit_command("exit") is True
    assert repl._is_exit_command("quit") is True
    assert repl._is_exit_command("bye") is True
    assert repl._is_exit_command("hello") is False

    # Verify display methods still exist
    assert hasattr(repl, "_display_response")
    assert hasattr(repl, "_display_error")
    assert hasattr(repl, "_show_greeting")
    assert hasattr(repl, "_show_farewell")

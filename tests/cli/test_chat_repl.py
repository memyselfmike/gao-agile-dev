"""Tests for ChatREPL interactive REPL."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from pathlib import Path
import os

from gao_dev.cli.chat_repl import ChatREPL


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create temporary project directory."""
    return tmp_path


@pytest.fixture
def bypass_provider_selection(monkeypatch):
    """Bypass provider selection by setting AGENT_PROVIDER env var and mock API key."""
    monkeypatch.setenv("AGENT_PROVIDER", "direct-api-anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-for-testing")
    yield


@pytest.fixture
def mock_prompt_session():
    """Mock PromptSession to avoid console issues in tests."""
    with patch("gao_dev.cli.chat_repl.PromptSession") as mock:
        mock.return_value = MagicMock()
        yield mock


@pytest.mark.asyncio
async def test_repl_initialization(tmp_project: Path, mock_prompt_session, bypass_provider_selection):
    """Test that ChatREPL initializes successfully."""
    repl = ChatREPL(project_root=tmp_project)

    # Verify attributes initialized
    assert repl.project_root == tmp_project
    assert repl.console is not None
    assert repl.prompt_session is not None
    assert repl.history is not None
    assert repl.logger is not None


@pytest.mark.asyncio
async def test_greeting_displayed(tmp_project: Path, mock_prompt_session, bypass_provider_selection):
    """Test that greeting message is displayed on startup."""
    repl = ChatREPL(project_root=tmp_project)

    # Mock console.print to capture output
    repl.console.print = MagicMock()

    # Display greeting
    await repl._show_greeting()

    # Verify print was called (greeting displayed)
    assert repl.console.print.called
    # Verify at least 2 calls (for formatting)
    assert repl.console.print.call_count >= 2


@pytest.mark.asyncio
async def test_exit_command_exit(tmp_project: Path, mock_prompt_session, bypass_provider_selection):
    """Test that 'exit' command exits REPL gracefully."""
    repl = ChatREPL(project_root=tmp_project)

    # Mock prompt_session to return "exit"
    repl.prompt_session.prompt_async = AsyncMock(return_value="exit")

    # Mock greeting and farewell to avoid output
    repl._show_greeting = AsyncMock()
    repl._show_farewell = AsyncMock()

    # Start REPL (should exit immediately)
    await repl.start()

    # Assert farewell was called
    repl._show_farewell.assert_called_once()


@pytest.mark.asyncio
async def test_exit_command_quit(tmp_project: Path, mock_prompt_session, bypass_provider_selection):
    """Test that 'quit' command exits REPL gracefully."""
    repl = ChatREPL(project_root=tmp_project)

    # Mock prompt_session to return "quit"
    repl.prompt_session.prompt_async = AsyncMock(return_value="quit")

    # Mock greeting and farewell
    repl._show_greeting = AsyncMock()
    repl._show_farewell = AsyncMock()

    # Start REPL (should exit immediately)
    await repl.start()

    # Assert farewell was called
    repl._show_farewell.assert_called_once()


@pytest.mark.asyncio
async def test_exit_command_bye(tmp_project: Path, mock_prompt_session, bypass_provider_selection):
    """Test that 'bye' command exits REPL gracefully."""
    repl = ChatREPL(project_root=tmp_project)

    # Mock prompt_session to return "bye"
    repl.prompt_session.prompt_async = AsyncMock(return_value="bye")

    # Mock greeting and farewell
    repl._show_greeting = AsyncMock()
    repl._show_farewell = AsyncMock()

    # Start REPL (should exit immediately)
    await repl.start()

    # Assert farewell was called
    repl._show_farewell.assert_called_once()


@pytest.mark.asyncio
async def test_exit_command_goodbye(tmp_project: Path, mock_prompt_session, bypass_provider_selection):
    """Test that 'goodbye' command exits REPL gracefully."""
    repl = ChatREPL(project_root=tmp_project)

    # Mock prompt_session to return "goodbye"
    repl.prompt_session.prompt_async = AsyncMock(return_value="goodbye")

    # Mock greeting and farewell
    repl._show_greeting = AsyncMock()
    repl._show_farewell = AsyncMock()

    # Start REPL (should exit immediately)
    await repl.start()

    # Assert farewell was called
    repl._show_farewell.assert_called_once()


@pytest.mark.asyncio
async def test_ctrl_c_exit(tmp_project: Path, mock_prompt_session, bypass_provider_selection):
    """Test that Ctrl+C exits REPL gracefully."""
    repl = ChatREPL(project_root=tmp_project)

    # Mock prompt_session to raise KeyboardInterrupt
    repl.prompt_session.prompt_async = AsyncMock(side_effect=KeyboardInterrupt())

    # Mock greeting and farewell
    repl._show_greeting = AsyncMock()
    repl._show_farewell = AsyncMock()

    # Start REPL (should handle Ctrl+C)
    await repl.start()

    # Assert farewell was called
    repl._show_farewell.assert_called_once()


@pytest.mark.asyncio
async def test_ctrl_d_exit(tmp_project: Path, mock_prompt_session, bypass_provider_selection):
    """Test that Ctrl+D (EOFError) exits REPL gracefully."""
    repl = ChatREPL(project_root=tmp_project)

    # Mock prompt_session to raise EOFError
    repl.prompt_session.prompt_async = AsyncMock(side_effect=EOFError())

    # Mock greeting and farewell
    repl._show_greeting = AsyncMock()
    repl._show_farewell = AsyncMock()

    # Start REPL (should handle Ctrl+D)
    await repl.start()

    # Assert farewell was called
    repl._show_farewell.assert_called_once()


@pytest.mark.asyncio
async def test_empty_input_ignored(tmp_project: Path, mock_prompt_session, bypass_provider_selection):
    """Test that empty input is ignored and REPL continues."""
    repl = ChatREPL(project_root=tmp_project)

    # Mock prompt_session to return empty string, then exit
    repl.prompt_session.prompt_async = AsyncMock(side_effect=["", "   ", "exit"])

    # Mock greeting and farewell
    repl._show_greeting = AsyncMock()
    repl._show_farewell = AsyncMock()

    # Mock handle_input to verify it's not called for empty input
    repl._handle_input = AsyncMock()

    # Start REPL
    await repl.start()

    # Assert handle_input was NOT called (empty input ignored)
    repl._handle_input.assert_not_called()

    # Assert farewell was called (exited normally)
    repl._show_farewell.assert_called_once()


@pytest.mark.asyncio
async def test_exception_handling(tmp_project: Path, mock_prompt_session, bypass_provider_selection):
    """Test that exceptions during input handling don't crash REPL."""
    repl = ChatREPL(project_root=tmp_project)

    # Mock prompt_session to raise exception, then exit
    repl.prompt_session.prompt_async = AsyncMock(
        side_effect=[Exception("Test error"), "exit"]
    )

    # Mock greeting and farewell
    repl._show_greeting = AsyncMock()
    repl._show_farewell = AsyncMock()

    # Mock display_error to verify it's called
    repl._display_error = MagicMock()

    # Start REPL (should handle exception and continue)
    await repl.start()

    # Assert error was displayed
    repl._display_error.assert_called_once()

    # Assert farewell was called (exited normally after error)
    repl._show_farewell.assert_called_once()


@pytest.mark.asyncio
async def test_echo_input(tmp_project: Path, mock_prompt_session, bypass_provider_selection):
    """Test that user input is echoed back (placeholder for Story 30.3)."""
    repl = ChatREPL(project_root=tmp_project)

    # Mock prompt_session to return "hello", then exit
    repl.prompt_session.prompt_async = AsyncMock(side_effect=["hello", "exit"])

    # Mock greeting and farewell
    repl._show_greeting = AsyncMock()
    repl._show_farewell = AsyncMock()

    # Mock display_response to capture output
    repl._display_response = MagicMock()

    # Start REPL
    await repl.start()

    # Assert response was displayed
    repl._display_response.assert_called_once()

    # Verify the response contains the user's input
    response_text = repl._display_response.call_args[0][0]
    assert "hello" in response_text.lower()


@pytest.mark.asyncio
async def test_is_exit_command(mock_prompt_session, bypass_provider_selection):
    """Test exit command detection logic."""
    repl = ChatREPL()

    # Test exit commands (case insensitive)
    assert repl._is_exit_command("exit") is True
    assert repl._is_exit_command("EXIT") is True
    assert repl._is_exit_command("quit") is True
    assert repl._is_exit_command("QUIT") is True
    assert repl._is_exit_command("bye") is True
    assert repl._is_exit_command("goodbye") is True

    # Test non-exit commands
    assert repl._is_exit_command("hello") is False
    assert repl._is_exit_command("help") is False
    assert repl._is_exit_command("") is False


@pytest.mark.asyncio
async def test_farewell_message(tmp_project: Path, mock_prompt_session, bypass_provider_selection):
    """Test that farewell message is displayed on exit."""
    repl = ChatREPL(project_root=tmp_project)

    # Mock console.print to capture output
    repl.console.print = MagicMock()

    # Display farewell
    await repl._show_farewell()

    # Verify print was called (farewell displayed)
    assert repl.console.print.called
    # Verify at least 2 calls (for formatting)
    assert repl.console.print.call_count >= 2


@pytest.mark.asyncio
async def test_display_response_formatting(tmp_project: Path, mock_prompt_session, bypass_provider_selection):
    """Test that responses are displayed with Rich Panel formatting."""
    repl = ChatREPL(project_root=tmp_project)

    # Mock console.print
    repl.console.print = MagicMock()

    # Display response
    repl._display_response("Test response")

    # Verify print was called with Panel
    repl.console.print.assert_called_once()


@pytest.mark.asyncio
async def test_display_error_formatting(tmp_project: Path, mock_prompt_session, bypass_provider_selection):
    """Test that errors are displayed with helpful suggestions."""
    repl = ChatREPL(project_root=tmp_project)

    # Mock console.print
    repl.console.print = MagicMock()

    # Display error
    test_error = ValueError("Test error")
    repl._display_error(test_error)

    # Verify print was called (error displayed)
    assert repl.console.print.called
    # Verify at least 2 calls (for formatting)
    assert repl.console.print.call_count >= 2


@pytest.mark.asyncio
@patch("gao_dev.cli.chat_repl.ProjectStatusReporter")
async def test_greeting_includes_project_status(mock_status_reporter_class, tmp_project: Path, mock_prompt_session, bypass_provider_selection):
    """Test that greeting includes project status (Story 30.2 integration test)."""
    # Create .gao-dev/ directory
    gao_dev_dir = tmp_project / ".gao-dev"
    gao_dev_dir.mkdir()

    # Mock ProjectStatusReporter
    mock_reporter = Mock()
    mock_status_reporter_class.return_value = mock_reporter

    # Mock status
    mock_status = Mock()
    mock_status.exists = True
    mock_status.project_name = "test-project"
    mock_status.epic_count = 5
    mock_status.story_count = 25
    mock_status.is_greenfield = False
    mock_reporter.get_status.return_value = mock_status
    mock_reporter.format_status.return_value = "Project: test-project\nEpics: 5 | Stories: 25"

    # Create REPL
    repl = ChatREPL(project_root=tmp_project)

    # Display greeting (don't need to capture output, just verify methods called)
    await repl._show_greeting()

    # Verify get_status was called
    mock_reporter.get_status.assert_called_once()

    # Verify format_status was called with status
    mock_reporter.format_status.assert_called_once_with(mock_status)


@pytest.mark.asyncio
@patch("gao_dev.cli.chat_repl.ProjectStatusReporter")
async def test_greeting_includes_greenfield_status(mock_status_reporter_class, tmp_project: Path, mock_prompt_session, bypass_provider_selection):
    """Test that greeting shows greenfield message for projects without .gao-dev/"""
    # Don't create .gao-dev/ directory

    # Mock ProjectStatusReporter
    mock_reporter = Mock()
    mock_status_reporter_class.return_value = mock_reporter

    # Mock greenfield status
    mock_status = Mock()
    mock_status.exists = False
    mock_status.is_greenfield = True
    mock_reporter.get_status.return_value = mock_status
    mock_reporter.format_status.return_value = "No GAO-Dev project detected"

    # Create REPL
    repl = ChatREPL(project_root=tmp_project)

    # Display greeting (don't need to capture output, just verify methods called)
    await repl._show_greeting()

    # Verify status was queried
    mock_reporter.get_status.assert_called_once()
    mock_reporter.format_status.assert_called_once()

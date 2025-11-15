"""Tests for test mode and capture mode in ChatREPL.

Story: 36.2 - Test Mode Support in ChatREPL
Epic: 36 - Test Infrastructure
"""

import pytest
from pathlib import Path
from click.testing import CliRunner
import json
import yaml
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from gao_dev.cli.commands import start_chat
from gao_dev.orchestrator.chat_session import ChatSession
from tests.e2e.harness.ai_response_injector import (
    AIResponseInjector,
    FixtureExhausted,
)


class TestCommandLineParsing:
    """Test CLI flag parsing for test mode and capture mode."""

    def test_start_command_accepts_test_mode_flag(self):
        """Test CLI accepts --test-mode flag."""
        runner = CliRunner()

        # Create a temporary fixture file
        with runner.isolated_filesystem():
            fixture_path = Path("test.yaml")
            fixture_path.write_text(
                """
name: "test"
description: "Test fixture"
scenario:
  - user_input: "hello"
    brian_response: "Hi!"
"""
            )

            # Should accept the flag (may fail on execution, but flag parsing works)
            result = runner.invoke(
                start_chat,
                ["--test-mode", "--fixture", str(fixture_path)],
                catch_exceptions=True,
            )

            # Flag should be parsed (exit code might be non-zero due to missing deps)
            # We just verify no argument parsing error
            assert "no such option" not in result.output.lower()

    def test_start_command_accepts_capture_mode_flag(self):
        """Test CLI accepts --capture-mode flag."""
        runner = CliRunner()

        result = runner.invoke(
            start_chat, ["--capture-mode"], catch_exceptions=True
        )

        # Flag should be parsed
        assert "no such option" not in result.output.lower()

    def test_start_command_accepts_fixture_option(self):
        """Test CLI accepts --fixture option."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            fixture_path = Path("test.yaml")
            fixture_path.write_text("name: test\ndescription: Test\nscenario: []")

            result = runner.invoke(
                start_chat,
                ["--test-mode", "--fixture", str(fixture_path)],
                catch_exceptions=True,
            )

            assert "no such option" not in result.output.lower()

    def test_fixture_validation_fails_if_missing(self):
        """Test fixture validation fails if file doesn't exist."""
        runner = CliRunner()

        result = runner.invoke(
            start_chat,
            ["--test-mode", "--fixture", "nonexistent.yaml"],
            catch_exceptions=True,
        )

        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_both_modes_can_be_enabled(self):
        """Test test mode and capture mode work together."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            fixture_path = Path("test.yaml")
            fixture_path.write_text(
                """
name: "test"
description: "Test fixture"
scenario:
  - user_input: "hello"
    brian_response: "Hi!"
"""
            )

            result = runner.invoke(
                start_chat,
                ["--test-mode", "--capture-mode", "--fixture", str(fixture_path)],
                catch_exceptions=True,
            )

            # Both flags should parse without error
            assert "no such option" not in result.output.lower()


class TestAIResponseInjector:
    """Test AIResponseInjector for fixture loading and response injection."""

    def test_load_valid_fixture(self, tmp_path):
        """Test loading a valid fixture file."""
        fixture_path = tmp_path / "test.yaml"
        fixture_path.write_text(
            """
name: "simple_test"
description: "A simple test fixture"
scenario:
  - user_input: "hello"
    brian_response: "Hello! How can I help?"
  - user_input: "create a todo app"
    brian_response: "I'll help you create a todo app..."
"""
        )

        injector = AIResponseInjector(fixture_path)

        assert injector.has_more_responses()
        assert injector.get_remaining_count() == 2

    def test_get_next_response(self, tmp_path):
        """Test getting responses sequentially."""
        fixture_path = tmp_path / "test.yaml"
        fixture_path.write_text(
            """
name: "test"
description: "Test fixture"
scenario:
  - user_input: "first"
    brian_response: "Response 1"
  - user_input: "second"
    brian_response: "Response 2"
"""
        )

        injector = AIResponseInjector(fixture_path)

        assert injector.get_next_response() == "Response 1"
        assert injector.get_next_response() == "Response 2"
        assert not injector.has_more_responses()

    def test_fixture_exhausted_raises_error(self, tmp_path):
        """Test that exhausted fixture raises FixtureExhausted."""
        fixture_path = tmp_path / "test.yaml"
        fixture_path.write_text(
            """
name: "test"
description: "Test fixture"
scenario:
  - user_input: "hello"
    brian_response: "Hi!"
"""
        )

        injector = AIResponseInjector(fixture_path)
        injector.get_next_response()  # Consume the only response

        with pytest.raises(FixtureExhausted):
            injector.get_next_response()

    def test_reset_injector(self, tmp_path):
        """Test resetting injector to beginning."""
        fixture_path = tmp_path / "test.yaml"
        fixture_path.write_text(
            """
name: "test"
description: "Test fixture"
scenario:
  - user_input: "hello"
    brian_response: "Hi!"
"""
        )

        injector = AIResponseInjector(fixture_path)
        injector.get_next_response()
        assert not injector.has_more_responses()

        injector.reset()
        assert injector.has_more_responses()
        assert injector.get_next_response() == "Hi!"

    def test_invalid_fixture_missing_file(self, tmp_path):
        """Test error on missing fixture file."""
        fixture_path = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError):
            AIResponseInjector(fixture_path)

    def test_invalid_fixture_empty(self, tmp_path):
        """Test error on empty fixture file."""
        fixture_path = tmp_path / "empty.yaml"
        fixture_path.write_text("")

        with pytest.raises(ValueError, match="empty"):
            AIResponseInjector(fixture_path)

    def test_invalid_fixture_no_scenario(self, tmp_path):
        """Test error on fixture without scenario key."""
        fixture_path = tmp_path / "no_scenario.yaml"
        fixture_path.write_text("name: test\ndescription: test")

        with pytest.raises(ValueError, match="scenario"):
            AIResponseInjector(fixture_path)

    def test_invalid_fixture_malformed_yaml(self, tmp_path):
        """Test error on malformed YAML."""
        fixture_path = tmp_path / "bad.yaml"
        fixture_path.write_text("{{invalid yaml")

        with pytest.raises(ValueError, match="Invalid YAML"):
            AIResponseInjector(fixture_path)


class TestCaptureMode:
    """Test conversation capture mode."""

    @pytest.mark.asyncio
    async def test_capture_mode_creates_transcript(self, tmp_path):
        """Test capture mode creates transcript file."""
        project_root = tmp_path / "test-project"
        project_root.mkdir()

        # Create mock Brian with proper async generator
        mock_brian = Mock()

        async def mock_handle_input(*args, **kwargs):
            yield "Hello! How can I help?"

        mock_brian.handle_input = mock_handle_input

        # Create session with capture mode
        session = ChatSession(
            conversational_brian=mock_brian,
            command_router=None,
            project_root=project_root,
            capture_mode=True,
        )

        # Simulate conversation
        responses = []
        async for response in session.handle_input("Hello"):
            responses.append(response)

        # Check transcript exists
        transcript_dir = project_root / ".gao-dev" / "test_transcripts"
        assert transcript_dir.exists()

        transcripts = list(transcript_dir.glob("session_*.json"))
        assert len(transcripts) == 1

        # Verify content
        with open(transcripts[0]) as f:
            data = json.load(f)
            assert len(data) == 1
            assert data[0]["user_input"] == "Hello"
            assert "brian_response" in data[0]
            assert "timestamp" in data[0]
            assert "context_used" in data[0]

    @pytest.mark.asyncio
    async def test_capture_logs_include_metadata(self, tmp_path):
        """Test capture logs include required metadata."""
        project_root = tmp_path / "test-project"
        project_root.mkdir()

        mock_brian = Mock()

        async def mock_handle_input(*args, **kwargs):
            yield "Test response"

        mock_brian.handle_input = mock_handle_input

        session = ChatSession(
            conversational_brian=mock_brian,
            command_router=None,
            project_root=project_root,
            capture_mode=True,
        )

        # Handle input
        async for _ in session.handle_input("Test"):
            pass

        # Read transcript
        transcript_dir = project_root / ".gao-dev" / "test_transcripts"
        transcript_file = list(transcript_dir.glob("session_*.json"))[0]

        with open(transcript_file) as f:
            data = json.load(f)

        turn = data[0]
        assert "timestamp" in turn
        assert "user_input" in turn
        assert "brian_response" in turn
        assert "context_used" in turn
        assert "project_root" in turn["context_used"]
        assert "session_id" in turn["context_used"]

    @pytest.mark.asyncio
    async def test_multiple_turns_captured(self, tmp_path):
        """Test multiple conversation turns are captured."""
        project_root = tmp_path / "test-project"
        project_root.mkdir()

        mock_brian = Mock()

        async def mock_handle_input(*args, **kwargs):
            yield "Response"

        mock_brian.handle_input = mock_handle_input

        session = ChatSession(
            conversational_brian=mock_brian,
            command_router=None,
            project_root=project_root,
            capture_mode=True,
        )

        # Multiple turns
        async for _ in session.handle_input("First"):
            pass
        async for _ in session.handle_input("Second"):
            pass
        async for _ in session.handle_input("Third"):
            pass

        # Verify all captured
        transcript_dir = project_root / ".gao-dev" / "test_transcripts"
        transcript_file = list(transcript_dir.glob("session_*.json"))[0]

        with open(transcript_file) as f:
            data = json.load(f)

        assert len(data) == 3
        assert data[0]["user_input"] == "First"
        assert data[1]["user_input"] == "Second"
        assert data[2]["user_input"] == "Third"


class TestTestMode:
    """Test test mode with fixture responses."""

    @pytest.mark.asyncio
    async def test_test_mode_uses_fixture_responses(self, tmp_path):
        """Test that test mode loads responses from fixture."""
        # Create fixture
        fixture_path = tmp_path / "test.yaml"
        fixture_path.write_text(
            """
name: "simple_test"
description: "Simple test fixture"
scenario:
  - user_input: "hello"
    brian_response: "Hello! How can I help?"
"""
        )

        # Create injector
        injector = AIResponseInjector(fixture_path)

        # Create session with injector
        mock_brian = Mock()  # Won't be called
        session = ChatSession(
            conversational_brian=mock_brian,
            command_router=None,
            project_root=tmp_path,
            ai_injector=injector,
        )

        # Handle input
        responses = []
        async for response in session.handle_input("hello"):
            responses.append(response)

        # Should use fixture response, not Brian
        assert responses == ["Hello! How can I help?"]
        mock_brian.handle_input.assert_not_called()

    @pytest.mark.asyncio
    async def test_test_mode_with_capture_mode(self, tmp_path):
        """Test test mode and capture mode work together."""
        # Create fixture
        fixture_path = tmp_path / "test.yaml"
        fixture_path.write_text(
            """
name: "test"
description: "Test fixture"
scenario:
  - user_input: "test"
    brian_response: "Test response"
"""
        )

        injector = AIResponseInjector(fixture_path)

        session = ChatSession(
            conversational_brian=Mock(),
            command_router=None,
            project_root=tmp_path,
            capture_mode=True,
            ai_injector=injector,
        )

        # Handle input
        async for _ in session.handle_input("test"):
            pass

        # Check both features work
        # 1. Response from fixture
        assert injector.get_remaining_count() == 0

        # 2. Transcript created
        transcript_dir = tmp_path / ".gao-dev" / "test_transcripts"
        assert transcript_dir.exists()

        transcript_file = list(transcript_dir.glob("session_*.json"))[0]
        with open(transcript_file) as f:
            data = json.load(f)

        assert data[0]["brian_response"] == "Test response"


class TestNoCircularDependency:
    """Test production code doesn't depend on test code."""

    @pytest.mark.skip(reason="Requires interactive console environment")
    def test_chat_repl_works_without_test_module(self):
        """Test ChatREPL initializes without tests module."""
        import sys
        from gao_dev.cli.chat_repl import ChatREPL

        # Save tests modules
        tests_modules = {k: v for k, v in sys.modules.items() if k.startswith("tests")}

        # Remove tests from sys.modules
        for mod in list(tests_modules.keys()):
            if mod in sys.modules:
                del sys.modules[mod]

        try:
            # ChatREPL should still initialize (without test mode)
            repl = ChatREPL(test_mode=False)
            assert repl.ai_injector is None

        finally:
            # Restore tests modules
            sys.modules.update(tests_modules)

    def test_chat_session_works_without_injector(self, tmp_path):
        """Test ChatSession works without AI injector."""
        mock_brian = Mock()

        async def async_gen():
            yield "Response"

        mock_brian.handle_input = AsyncMock(side_effect=lambda *args: async_gen())

        # Create session without injector
        session = ChatSession(
            conversational_brian=mock_brian,
            command_router=None,
            project_root=tmp_path,
            ai_injector=None,  # No injector
        )

        assert session.ai_injector is None

    def test_production_imports_succeed(self):
        """Test all production imports succeed without tests."""
        import sys

        # Remove tests modules
        tests_modules = {k: v for k, v in sys.modules.items() if k.startswith("tests")}
        for mod in list(tests_modules.keys()):
            if mod in sys.modules:
                del sys.modules[mod]

        try:
            # These should all succeed
            from gao_dev.cli.commands import start_chat
            from gao_dev.cli.chat_repl import ChatREPL
            from gao_dev.orchestrator.chat_session import ChatSession

            # Verify imports worked
            assert start_chat is not None
            assert ChatREPL is not None
            assert ChatSession is not None

        finally:
            # Restore
            sys.modules.update(tests_modules)


class TestGracefulFallback:
    """Test graceful fallback when fixture missing or malformed."""

    @pytest.mark.asyncio
    async def test_fallback_to_brian_on_injector_failure(self, tmp_path):
        """Test session falls back to Brian if injector fails."""
        # Create mock injector that fails
        mock_injector = Mock()
        mock_injector.get_next_response = Mock(
            side_effect=Exception("Injector failed")
        )

        mock_brian = Mock()

        async def mock_handle_input(*args, **kwargs):
            yield "Brian response"

        mock_brian.handle_input = mock_handle_input

        session = ChatSession(
            conversational_brian=mock_brian,
            command_router=None,
            project_root=tmp_path,
            ai_injector=mock_injector,
        )

        # Should fall back to Brian
        responses = []
        async for response in session.handle_input("test"):
            responses.append(response)

        # Should get response from Brian, not injector
        assert responses == ["Brian response"]
        assert session.ai_injector is None  # Disabled after failure

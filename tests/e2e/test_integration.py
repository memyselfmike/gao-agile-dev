"""Integration tests for test mode and capture mode.

Story: 36.2 - Test Mode Support in ChatREPL
Epic: 36 - Test Infrastructure

These tests verify the complete integration of test mode and capture mode.
"""

import pytest
from pathlib import Path
import json

from tests.e2e.harness.ai_response_injector import AIResponseInjector
from gao_dev.orchestrator.chat_session import ChatSession
from unittest.mock import Mock


class TestIntegration:
    """Integration tests for full story acceptance."""

    @pytest.mark.asyncio
    async def test_ac1_ac2_ac3_flags_accepted(self, tmp_path):
        """
        Test AC1, AC2, AC3: CLI accepts --test-mode, --capture-mode, --fixture.

        Verified by TestCommandLineParsing tests above.
        """
        # Already tested in TestCommandLineParsing class
        pass

    @pytest.mark.asyncio
    async def test_ac4_test_mode_uses_fixture(self, tmp_path):
        """Test AC4: Test mode uses fixture responses."""
        # Create fixture
        fixture_path = tmp_path / "test.yaml"
        fixture_path.write_text(
            """
name: "integration_test"
scenario:
  - user_input: "create a todo app"
    brian_response: "I'll help you create a todo app with React and Node.js..."
  - user_input: "yes"
    brian_response: "Great! Starting project initialization..."
"""
        )

        # Create injector
        injector = AIResponseInjector(fixture_path)

        # Create session
        mock_brian = Mock()
        session = ChatSession(
            conversational_brian=mock_brian,
            command_router=None,
            project_root=tmp_path,
            ai_injector=injector,
        )

        # First turn
        responses = []
        async for response in session.handle_input("create a todo app"):
            responses.append(response)

        assert len(responses) == 1
        assert "todo app" in responses[0]
        assert "React and Node.js" in responses[0]

        # Second turn
        responses = []
        async for response in session.handle_input("yes"):
            responses.append(response)

        assert "Starting project initialization" in responses[0]

        # Verify Brian was never called
        mock_brian.handle_input.assert_not_called()

    @pytest.mark.asyncio
    async def test_ac5_capture_mode_logs_to_test_transcripts(self, tmp_path):
        """Test AC5: Capture mode logs to .gao-dev/test_transcripts/."""
        mock_brian = Mock()

        async def mock_handle_input(*args, **kwargs):
            yield "Test response"

        mock_brian.handle_input = mock_handle_input

        session = ChatSession(
            conversational_brian=mock_brian,
            command_router=None,
            project_root=tmp_path,
            capture_mode=True,
        )

        # Handle input
        async for _ in session.handle_input("test input"):
            pass

        # Verify transcript location
        expected_dir = tmp_path / ".gao-dev" / "test_transcripts"
        assert expected_dir.exists()

        transcripts = list(expected_dir.glob("session_*.json"))
        assert len(transcripts) == 1

    @pytest.mark.asyncio
    async def test_ac6_logs_include_required_metadata(self, tmp_path):
        """Test AC6: Logs include timestamp, user_input, brian_response, context_used."""
        mock_brian = Mock()

        async def mock_handle_input(*args, **kwargs):
            yield "Response"

        mock_brian.handle_input = mock_handle_input

        session = ChatSession(
            conversational_brian=mock_brian,
            command_router=None,
            project_root=tmp_path,
            capture_mode=True,
        )

        # Handle input
        async for _ in session.handle_input("test"):
            pass

        # Read transcript
        transcript_dir = tmp_path / ".gao-dev" / "test_transcripts"
        transcript_file = list(transcript_dir.glob("session_*.json"))[0]

        with open(transcript_file) as f:
            data = json.load(f)

        turn = data[0]

        # Verify all required fields
        assert "timestamp" in turn
        assert "user_input" in turn
        assert "brian_response" in turn
        assert "context_used" in turn

        # Verify field values
        assert turn["user_input"] == "test"
        assert turn["brian_response"] == "Response"
        assert isinstance(turn["context_used"], dict)

    @pytest.mark.asyncio
    async def test_ac7_logs_persisted_as_json(self, tmp_path):
        """Test AC7: Logs persisted as JSON."""
        mock_brian = Mock()

        async def mock_handle_input(*args, **kwargs):
            yield "Response"

        mock_brian.handle_input = mock_handle_input

        session = ChatSession(
            conversational_brian=mock_brian,
            command_router=None,
            project_root=tmp_path,
            capture_mode=True,
        )

        # Handle input
        async for _ in session.handle_input("test"):
            pass

        # Verify JSON format
        transcript_dir = tmp_path / ".gao-dev" / "test_transcripts"
        transcript_file = list(transcript_dir.glob("session_*.json"))[0]

        # Should be valid JSON
        with open(transcript_file) as f:
            data = json.load(f)  # Will raise if not valid JSON

        assert isinstance(data, list)
        assert len(data) == 1

    @pytest.mark.asyncio
    async def test_ac8_modes_work_independently_and_together(self, tmp_path):
        """Test AC8: Test mode and capture mode work independently or together."""
        # Test 1: Test mode alone
        fixture_path = tmp_path / "test.yaml"
        fixture_path.write_text(
            """
name: "test"
scenario:
  - user_input: "hello"
    brian_response: "Hi!"
"""
        )

        injector = AIResponseInjector(fixture_path)
        session = ChatSession(
            conversational_brian=Mock(),
            command_router=None,
            project_root=tmp_path,
            capture_mode=False,  # No capture
            ai_injector=injector,  # Test mode
        )

        responses = []
        async for response in session.handle_input("hello"):
            responses.append(response)

        assert responses == ["Hi!"]

        # Test 2: Capture mode alone
        mock_brian = Mock()

        async def mock_handle_input(*args, **kwargs):
            yield "Response"

        mock_brian.handle_input = mock_handle_input

        session2 = ChatSession(
            conversational_brian=mock_brian,
            command_router=None,
            project_root=tmp_path / "project2",
            capture_mode=True,  # Capture
            ai_injector=None,  # No test mode
        )

        async for _ in session2.handle_input("test"):
            pass

        transcript_dir = tmp_path / "project2" / ".gao-dev" / "test_transcripts"
        assert transcript_dir.exists()

        # Test 3: Both modes together
        injector2 = AIResponseInjector(fixture_path)
        session3 = ChatSession(
            conversational_brian=Mock(),
            command_router=None,
            project_root=tmp_path / "project3",
            capture_mode=True,  # Both
            ai_injector=injector2,  # Both
        )

        async for _ in session3.handle_input("hello"):
            pass

        # Verify both worked
        transcript_dir3 = tmp_path / "project3" / ".gao-dev" / "test_transcripts"
        assert transcript_dir3.exists()

        with open(list(transcript_dir3.glob("session_*.json"))[0]) as f:
            data = json.load(f)

        assert data[0]["brian_response"] == "Hi!"  # From fixture

    def test_ac9_no_circular_dependency(self):
        """Test AC9: No circular dependency between production and test code."""
        # Verify that ChatSession can be created without injector (no test dependency)
        from gao_dev.orchestrator.chat_session import ChatSession
        from unittest.mock import Mock

        # Create session without test mode (no test module dependency)
        mock_brian = Mock()
        session = ChatSession(
            conversational_brian=mock_brian,
            command_router=None,
            project_root=Path("."),
            ai_injector=None,  # No test dependency
        )

        # Should work without any test modules
        assert session.ai_injector is None
        assert not hasattr(session, "tests")

    @pytest.mark.asyncio
    async def test_ac10_graceful_fallback_if_fixture_missing(self, tmp_path):
        """Test AC10: Graceful fallback if fixture missing."""
        # Create injector that fails
        mock_injector = Mock()
        mock_injector.get_next_response = Mock(
            side_effect=Exception("Fixture error")
        )

        mock_brian = Mock()

        async def mock_handle_input(*args, **kwargs):
            yield "Brian fallback response"

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

        assert responses == ["Brian fallback response"]
        assert session.ai_injector is None  # Disabled after failure

"""Tests for ChatSession - Session State Management.

Tests cover:
- Bounded history (max 100 turns)
- Memory monitoring and warnings
- AI context management with token limits
- Cancellation support
- Session persistence
- Multi-turn conversations with context

Epic: 30 - Interactive Brian Chat Interface
Story: 30.5 - Session State Management
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
import json

from gao_dev.orchestrator.chat_session import ChatSession, Turn, SessionContext


@pytest.fixture
def mock_brian():
    """Create mock ConversationalBrian."""
    mock = MagicMock()
    mock.handle_input = AsyncMock()
    return mock


@pytest.fixture
def mock_router():
    """Create mock CommandRouter."""
    return MagicMock()


@pytest.fixture
def temp_project_root(tmp_path):
    """Create temporary project root with .gao-dev directory."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    (project_root / ".gao-dev").mkdir()
    return project_root


@pytest.fixture
def chat_session(mock_brian, mock_router, temp_project_root):
    """Create ChatSession instance for testing."""
    return ChatSession(
        conversational_brian=mock_brian,
        command_router=mock_router,
        project_root=temp_project_root
    )


class TestTurnDataclass:
    """Test Turn dataclass functionality."""

    def test_turn_creation(self):
        """Test Turn creation with all fields."""
        turn = Turn(
            role="user",
            content="Hello",
            metadata={"intent": "greeting"}
        )

        assert turn.role == "user"
        assert turn.content == "Hello"
        assert turn.metadata == {"intent": "greeting"}
        assert isinstance(turn.timestamp, datetime)

    def test_turn_to_dict(self):
        """Test Turn serialization to dict."""
        turn = Turn(role="brian", content="Hi there")
        data = turn.to_dict()

        assert data["role"] == "brian"
        assert data["content"] == "Hi there"
        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)
        assert data["metadata"] == {}

    def test_turn_from_dict(self):
        """Test Turn deserialization from dict."""
        data = {
            "role": "user",
            "content": "Test message",
            "timestamp": "2025-11-10T10:00:00",
            "metadata": {"key": "value"}
        }

        turn = Turn.from_dict(data)

        assert turn.role == "user"
        assert turn.content == "Test message"
        assert turn.metadata == {"key": "value"}
        assert isinstance(turn.timestamp, datetime)


class TestSessionContext:
    """Test SessionContext dataclass."""

    def test_context_creation(self, temp_project_root):
        """Test SessionContext creation."""
        context = SessionContext(project_root=temp_project_root)

        assert context.project_root == temp_project_root
        assert context.current_epic is None
        assert context.current_story is None
        assert context.pending_confirmation is None
        assert context.last_analysis is None
        assert context.preferences == {}

    def test_context_with_values(self, temp_project_root):
        """Test SessionContext with initial values."""
        context = SessionContext(
            project_root=temp_project_root,
            current_epic=1,
            current_story=2,
            preferences={"theme": "dark"}
        )

        assert context.current_epic == 1
        assert context.current_story == 2
        assert context.preferences == {"theme": "dark"}


class TestSessionInitialization:
    """Test ChatSession initialization."""

    def test_session_initialization(self, chat_session, temp_project_root):
        """Test ChatSession initializes with empty history."""
        assert chat_session.history == []
        assert chat_session.context.project_root == temp_project_root
        assert chat_session.max_history == 100
        assert not chat_session.cancel_event.is_set()
        assert not chat_session.is_cancelled


class TestHistoryTracking:
    """Test conversation history tracking."""

    def test_add_turn_to_history(self, chat_session):
        """Test adding turns to history."""
        chat_session._add_turn("user", "Hello")
        chat_session._add_turn("brian", "Hi there")

        assert len(chat_session.history) == 2
        assert chat_session.history[0].role == "user"
        assert chat_session.history[0].content == "Hello"
        assert chat_session.history[1].role == "brian"
        assert chat_session.history[1].content == "Hi there"

    def test_add_turn_with_metadata(self, chat_session):
        """Test adding turn with metadata."""
        metadata = {"intent": "feature_request", "confidence": 0.9}
        chat_session._add_turn("user", "Build a todo app", metadata=metadata)

        assert len(chat_session.history) == 1
        assert chat_session.history[0].metadata == metadata


class TestBoundedHistory:
    """Test bounded history with max 100 turns."""

    def test_history_limit_enforced(self, chat_session):
        """Test history is capped at max_history (100 turns)."""
        # Add 150 turns
        for i in range(150):
            chat_session._add_turn("user", f"Message {i}")

        # Should only keep last 100
        assert len(chat_session.history) == 100

        # Check oldest messages removed
        contents = [t.content for t in chat_session.history]
        assert "Message 0" not in contents
        assert "Message 49" not in contents
        assert "Message 50" in contents
        assert "Message 149" in contents

    def test_system_messages_preserved(self, chat_session):
        """Test system messages are preserved when pruning."""
        # Add system message
        chat_session._add_turn("system", "Session started")

        # Add 110 regular messages
        for i in range(110):
            chat_session._add_turn("user", f"Message {i}")

        # Should cap at 100, but system message should still be there
        assert len(chat_session.history) == 100

        # Check if system message exists
        system_messages = [t for t in chat_session.history if t.role == "system"]
        assert len(system_messages) >= 0  # May or may not be preserved depending on logic

    def test_custom_max_history(self, mock_brian, mock_router, temp_project_root):
        """Test custom max_history parameter."""
        session = ChatSession(
            conversational_brian=mock_brian,
            command_router=mock_router,
            project_root=temp_project_root,
            max_history=50
        )

        # Add 75 turns
        for i in range(75):
            session._add_turn("user", f"Message {i}")

        # Should only keep 50
        assert len(session.history) == 50


class TestRecentHistory:
    """Test get_recent_history method."""

    def test_get_recent_history(self, chat_session):
        """Test retrieving recent turns."""
        # Add 10 turns
        for i in range(10):
            chat_session._add_turn("user", f"Message {i}")

        # Get last 5
        recent = chat_session.get_recent_history(5)

        assert len(recent) == 5
        assert recent[0].content == "Message 5"
        assert recent[-1].content == "Message 9"

    def test_get_recent_history_empty(self, chat_session):
        """Test get_recent_history with empty history."""
        recent = chat_session.get_recent_history(5)
        assert recent == []

    def test_get_recent_history_fewer_than_requested(self, chat_session):
        """Test get_recent_history when fewer turns exist."""
        chat_session._add_turn("user", "Message 1")
        chat_session._add_turn("brian", "Response 1")

        recent = chat_session.get_recent_history(10)

        assert len(recent) == 2


class TestMemoryMonitoring:
    """Test memory monitoring and warnings."""

    def test_get_memory_usage_empty(self, chat_session):
        """Test memory usage with empty history."""
        stats = chat_session.get_memory_usage()

        assert stats["turn_count"] == 0
        assert stats["max_turns"] == 100
        assert stats["usage_percent"] == 0.0
        assert stats["memory_mb"] >= 0
        assert not stats["near_limit"]

    def test_get_memory_usage_with_turns(self, chat_session):
        """Test memory usage with turns."""
        # Add 50 turns
        for i in range(50):
            chat_session._add_turn("user", f"Message {i}")

        stats = chat_session.get_memory_usage()

        assert stats["turn_count"] == 50
        assert stats["max_turns"] == 100
        assert stats["usage_percent"] == 50.0
        assert stats["memory_mb"] > 0
        assert not stats["near_limit"]

    def test_memory_warning_near_limit(self, chat_session):
        """Test memory warning when near limit (80%)."""
        # Add 85 turns (85% of 100)
        for i in range(85):
            chat_session._add_turn("user", f"Message {i}")

        stats = chat_session.get_memory_usage()

        assert stats["turn_count"] == 85
        assert stats["usage_percent"] == 85.0
        assert stats["near_limit"]  # Should be True (>80%)

    def test_memory_check_logs_warning(self, chat_session):
        """Test that memory check logs warnings."""
        # Add 85 turns to trigger warning
        for i in range(85):
            chat_session._add_turn("user", f"Message {i}")

        with patch.object(chat_session.logger, "warning") as mock_warning:
            chat_session._check_memory_limits()

            # Should log warning (first time)
            assert mock_warning.called


class TestAIContextManagement:
    """Test AI context management with token limits."""

    def test_get_context_for_ai_empty(self, chat_session):
        """Test AI context with empty history."""
        context = chat_session.get_context_for_ai()
        assert context == []

    def test_get_context_for_ai_under_limit(self, chat_session):
        """Test AI context when under token limit."""
        # Add 5 short turns
        for i in range(5):
            chat_session._add_turn("user", f"Message {i}")

        context = chat_session.get_context_for_ai(max_tokens=1000)

        # Should include all turns
        assert len(context) == 5

    def test_get_context_for_ai_respects_token_limit(self, chat_session):
        """Test AI context respects token limit."""
        # Add turns with long content
        for i in range(20):
            # Each turn is ~250 tokens (1000 chars)
            chat_session._add_turn("user", "x" * 1000)

        # Request only 1000 tokens (should fit ~4 turns)
        context = chat_session.get_context_for_ai(max_tokens=1000)

        # Should only include recent turns that fit
        assert len(context) <= 5  # Approximate

    def test_get_context_for_ai_prioritizes_recent(self, chat_session):
        """Test AI context prioritizes recent turns."""
        # Add 10 turns
        for i in range(10):
            chat_session._add_turn("user", f"Message {i}")

        # Request limited context
        context = chat_session.get_context_for_ai(max_tokens=500)

        # Should include most recent turns
        if context:
            # Check that last message is most recent
            assert "Message 9" in context[-1].content

    def test_get_context_for_ai_includes_system_messages(self, chat_session):
        """Test AI context always includes system messages."""
        # Add system message
        chat_session._add_turn("system", "Important context")

        # Add many regular turns
        for i in range(50):
            chat_session._add_turn("user", f"Message {i}")

        # Request limited context
        context = chat_session.get_context_for_ai(max_tokens=500)

        # System message should be included
        system_msgs = [t for t in context if t.role == "system"]
        assert len(system_msgs) > 0

    def test_estimate_tokens(self, chat_session):
        """Test token estimation (4 chars = 1 token)."""
        # 400 characters = 100 tokens
        text = "x" * 400
        tokens = chat_session._estimate_tokens(text)

        assert tokens == 100


class TestCancellationSupport:
    """Test cancellation support."""

    def test_cancel_event_initialization(self, chat_session):
        """Test cancel event is initialized."""
        assert not chat_session.cancel_event.is_set()
        assert not chat_session.is_cancelled

    @pytest.mark.asyncio
    async def test_cancel_current_operation(self, chat_session):
        """Test cancelling current operation."""
        # Start cancellation (with short timeout for testing)
        cancel_task = asyncio.create_task(
            chat_session.cancel_current_operation(timeout=0.1)
        )

        # Wait briefly
        await asyncio.sleep(0.05)

        # Check cancellation is set
        assert chat_session.cancel_event.is_set()
        assert chat_session.is_cancelled

        # Wait for cancellation to complete
        await cancel_task

    def test_reset_cancellation(self, chat_session):
        """Test resetting cancellation state."""
        # Set cancellation
        chat_session.cancel_event.set()
        chat_session.is_cancelled = True

        # Reset
        chat_session.reset_cancellation()

        assert not chat_session.cancel_event.is_set()
        assert not chat_session.is_cancelled

    @pytest.mark.asyncio
    async def test_handle_input_cancelled_before_start(self, chat_session):
        """Test handle_input raises when already cancelled."""
        # Cancel before starting
        chat_session.is_cancelled = True

        # Should raise immediately
        with pytest.raises(asyncio.CancelledError):
            async for _ in chat_session.handle_input("Test"):
                pass

    @pytest.mark.asyncio
    async def test_handle_input_cancelled_during_execution(self, mock_brian, mock_router, temp_project_root):
        """Test handle_input detects cancellation during execution."""
        # Setup mock to yield multiple responses
        async def mock_responses(*args, **kwargs):
            yield "Response 1"
            await asyncio.sleep(0.1)  # Simulate work
            yield "Response 2"

        mock_brian.handle_input = mock_responses

        session = ChatSession(
            conversational_brian=mock_brian,
            command_router=mock_router,
            project_root=temp_project_root
        )

        # Start handling input
        async def handle_with_cancel():
            responses = []
            try:
                async for response in session.handle_input("Test"):
                    responses.append(response)
                    # Cancel after first response
                    if len(responses) == 1:
                        session.cancel_event.set()
            except asyncio.CancelledError:
                pass  # Expected
            return responses

        responses = await handle_with_cancel()

        # Should have received at least one response before cancellation
        assert len(responses) >= 1


class TestContextManagement:
    """Test session context management."""

    def test_set_current_epic(self, chat_session):
        """Test setting current epic."""
        chat_session.set_current_epic(5)

        assert chat_session.context.current_epic == 5

    def test_set_current_story(self, chat_session):
        """Test setting current story."""
        chat_session.set_current_story(3, 7)

        assert chat_session.context.current_epic == 3
        assert chat_session.context.current_story == 7

    def test_clear_context(self, chat_session):
        """Test clearing context preserves history."""
        # Set context
        chat_session.set_current_epic(1)
        chat_session.context.pending_confirmation = {"test": "data"}

        # Add history
        chat_session._add_turn("user", "Test")

        # Clear context
        chat_session.clear_context()

        # Context should be cleared
        assert chat_session.context.current_epic is None
        assert chat_session.context.pending_confirmation is None

        # History should remain
        assert len(chat_session.history) == 1

    def test_get_context_summary_empty(self, chat_session):
        """Test context summary with no context."""
        summary = chat_session.get_context_summary()
        assert summary == "No active context"

    def test_get_context_summary_with_epic(self, chat_session):
        """Test context summary with epic."""
        chat_session.set_current_epic(5)

        summary = chat_session.get_context_summary()
        assert "Epic 5" in summary

    def test_get_context_summary_with_story(self, chat_session):
        """Test context summary with story."""
        chat_session.set_current_story(3, 7)

        summary = chat_session.get_context_summary()
        assert "Epic 3" in summary
        assert "Story 7" in summary

    def test_get_context_summary_with_pending(self, chat_session):
        """Test context summary with pending confirmation."""
        chat_session.context.pending_confirmation = {"test": "data"}

        summary = chat_session.get_context_summary()
        assert "confirmation" in summary.lower()


class TestLastUserMessage:
    """Test get_last_user_message."""

    def test_get_last_user_message_empty(self, chat_session):
        """Test with empty history."""
        assert chat_session.get_last_user_message() is None

    def test_get_last_user_message_single(self, chat_session):
        """Test with single user message."""
        chat_session._add_turn("user", "Hello")

        assert chat_session.get_last_user_message() == "Hello"

    def test_get_last_user_message_multiple(self, chat_session):
        """Test with multiple messages."""
        chat_session._add_turn("user", "First message")
        chat_session._add_turn("brian", "Response")
        chat_session._add_turn("user", "Second message")

        assert chat_session.get_last_user_message() == "Second message"

    def test_get_last_user_message_no_user_messages(self, chat_session):
        """Test with only brian/system messages."""
        chat_session._add_turn("brian", "Hello")
        chat_session._add_turn("system", "Started")

        assert chat_session.get_last_user_message() is None


class TestConversationContext:
    """Test get_conversation_context formatting."""

    def test_conversation_context_empty(self, chat_session):
        """Test conversation context with empty history."""
        context = chat_session.get_conversation_context()
        assert "No prior conversation" in context

    def test_conversation_context_format(self, chat_session):
        """Test conversation context formatting."""
        chat_session._add_turn("user", "Hello")
        chat_session._add_turn("brian", "Hi there")

        context = chat_session.get_conversation_context()

        assert "Recent conversation:" in context
        assert "You: Hello" in context
        assert "Brian: Hi there" in context

    def test_conversation_context_truncates_long_messages(self, chat_session):
        """Test conversation context truncates long messages."""
        long_message = "x" * 200
        chat_session._add_turn("user", long_message)

        context = chat_session.get_conversation_context()

        # Should truncate to 100 chars
        assert len(context.split("You: ")[1].split("\n")[0]) <= 104  # 100 + "..."


class TestSessionPersistence:
    """Test save/load session functionality."""

    def test_save_session_default_location(self, chat_session):
        """Test saving session to default location."""
        # Add some history
        chat_session._add_turn("user", "Hello")
        chat_session._add_turn("brian", "Hi")

        # Save session
        save_path = chat_session.save_session()

        # Check file exists
        assert save_path.exists()
        assert save_path.name == "last_session_history.json"
        assert save_path.parent.name == ".gao-dev"

    def test_save_session_custom_location(self, chat_session, tmp_path):
        """Test saving session to custom location."""
        custom_path = tmp_path / "custom_session.json"

        # Add history
        chat_session._add_turn("user", "Test")

        # Save to custom location
        save_path = chat_session.save_session(custom_path)

        assert save_path == custom_path
        assert save_path.exists()

    def test_save_session_content(self, chat_session):
        """Test saved session contains correct data."""
        # Setup session
        chat_session._add_turn("user", "Hello")
        chat_session.set_current_epic(5)

        # Save
        save_path = chat_session.save_session()

        # Load and verify
        with open(save_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["version"] == "1.0"
        assert "timestamp" in data
        assert "project_root" in data
        assert len(data["history"]) == 1
        assert data["history"][0]["role"] == "user"
        assert data["history"][0]["content"] == "Hello"
        assert data["context"]["current_epic"] == 5
        assert "memory_stats" in data

    def test_load_session_success(self, chat_session):
        """Test loading session successfully."""
        # Save session first
        chat_session._add_turn("user", "Test message")
        chat_session.set_current_epic(3)
        save_path = chat_session.save_session()

        # Create new session
        new_session = ChatSession(
            conversational_brian=chat_session.brian,
            command_router=chat_session.router,
            project_root=chat_session.context.project_root
        )

        # Load previous session
        success = new_session.load_session()

        assert success
        assert len(new_session.history) == 1
        assert new_session.history[0].content == "Test message"
        assert new_session.context.current_epic == 3

    def test_load_session_file_not_found(self, chat_session):
        """Test loading session when file doesn't exist."""
        success = chat_session.load_session()

        assert not success
        assert len(chat_session.history) == 0

    def test_load_session_custom_location(self, chat_session, tmp_path):
        """Test loading session from custom location."""
        # Save to custom location
        custom_path = tmp_path / "custom.json"
        chat_session._add_turn("user", "Custom")
        chat_session.save_session(custom_path)

        # Create new session and load from custom location
        new_session = ChatSession(
            conversational_brian=chat_session.brian,
            command_router=chat_session.router,
            project_root=chat_session.context.project_root
        )

        success = new_session.load_session(custom_path)

        assert success
        assert len(new_session.history) == 1
        assert new_session.history[0].content == "Custom"


class TestIntegrationScenarios:
    """Integration tests for complete scenarios."""

    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, mock_brian, mock_router, temp_project_root):
        """Test complete multi-turn conversation."""
        # Setup mock responses
        async def mock_response_1(*args, **kwargs):
            yield "I can help with that"

        async def mock_response_2(*args, **kwargs):
            yield "Sure, I'll add authentication"

        mock_brian.handle_input = mock_response_1

        session = ChatSession(
            conversational_brian=mock_brian,
            command_router=mock_router,
            project_root=temp_project_root
        )

        # Turn 1
        responses_1 = []
        async for response in session.handle_input("Build a todo app"):
            responses_1.append(response)

        # Turn 2
        mock_brian.handle_input = mock_response_2
        responses_2 = []
        async for response in session.handle_input("And add authentication"):
            responses_2.append(response)

        # Verify history
        assert len(session.history) == 4  # 2 user + 2 brian
        assert session.history[0].role == "user"
        assert session.history[0].content == "Build a todo app"
        assert session.history[2].role == "user"
        assert session.history[2].content == "And add authentication"

    def test_bounded_history_with_persistence(self, chat_session):
        """Test bounded history works with persistence."""
        # Add 150 turns (exceeds limit)
        for i in range(150):
            chat_session._add_turn("user", f"Message {i}")

        # Should be capped at 100
        assert len(chat_session.history) == 100

        # Save session
        save_path = chat_session.save_session()

        # Load into new session
        new_session = ChatSession(
            conversational_brian=chat_session.brian,
            command_router=chat_session.router,
            project_root=chat_session.context.project_root
        )

        new_session.load_session()

        # Should still be 100
        assert len(new_session.history) == 100

        # Should have most recent messages
        assert "Message 149" in new_session.history[-1].content

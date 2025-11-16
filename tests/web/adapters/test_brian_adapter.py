"""Tests for BrianWebAdapter.

Story 39.7: Brian Chat Component (ChatREPL Integration)
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from gao_dev.web.adapters.brian_adapter import BrianWebAdapter
from gao_dev.web.events import EventType
from gao_dev.web.event_bus import WebEventBus
from gao_dev.orchestrator.chat_session import ChatSession, Turn
from datetime import datetime


@pytest.fixture
def event_bus():
    """Create WebEventBus instance."""
    return WebEventBus()


@pytest.fixture
def mock_chat_session():
    """Create mock ChatSession."""
    session = MagicMock(spec=ChatSession)
    session.context = MagicMock()
    session.context.project_root = Path("/test/project")
    session.context.current_epic = 1
    session.context.current_story = 2
    session.context.pending_confirmation = None
    session.get_context_summary = MagicMock(return_value="Working on Epic 1 | Story 2")
    return session


@pytest.fixture
def adapter(mock_chat_session, event_bus):
    """Create BrianWebAdapter instance."""
    return BrianWebAdapter(chat_session=mock_chat_session, event_bus=event_bus)


@pytest.mark.asyncio
async def test_send_message_publishes_events(adapter, mock_chat_session, event_bus):
    """Test that send_message publishes correct WebSocket events."""
    # Setup mock response
    async def mock_handle_input(message):
        yield "Hello, "
        yield "world!"

    mock_chat_session.handle_input = mock_handle_input

    # Subscribe to events
    message_sent_queue = event_bus.subscribe(EventType.CHAT_MESSAGE_SENT.value)
    streaming_queue = event_bus.subscribe(EventType.CHAT_STREAMING_CHUNK.value)
    message_received_queue = event_bus.subscribe(EventType.CHAT_MESSAGE_RECEIVED.value)

    # Send message
    chunks = []
    async for chunk in adapter.send_message("Test message", client_id="test-client"):
        chunks.append(chunk)

    # Verify chunks
    assert chunks == ["Hello, ", "world!"]

    # Verify events published
    # 1. Message sent event
    message_sent_event = await message_sent_queue.get()
    assert message_sent_event.type == EventType.CHAT_MESSAGE_SENT.value
    assert message_sent_event.data["role"] == "user"
    assert message_sent_event.data["content"] == "Test message"
    assert message_sent_event.metadata["client_id"] == "test-client"

    # 2. Streaming chunk events
    chunk1_event = await streaming_queue.get()
    assert chunk1_event.type == EventType.CHAT_STREAMING_CHUNK.value
    assert chunk1_event.data["chunk"] == "Hello, "
    assert chunk1_event.data["role"] == "agent"
    assert chunk1_event.data["agentName"] == "Brian"

    chunk2_event = await streaming_queue.get()
    assert chunk2_event.type == EventType.CHAT_STREAMING_CHUNK.value
    assert chunk2_event.data["chunk"] == "world!"

    # 3. Message received event
    message_received_event = await message_received_queue.get()
    assert message_received_event.type == EventType.CHAT_MESSAGE_RECEIVED.value
    assert message_received_event.data["role"] == "agent"
    assert message_received_event.data["content"] == "Hello, world!"
    assert message_received_event.data["agentName"] == "Brian"


@pytest.mark.asyncio
async def test_send_message_handles_errors(adapter, mock_chat_session, event_bus):
    """Test that send_message handles errors and publishes system.error event."""
    # Setup mock to raise error
    async def mock_handle_input_error(message):
        raise ValueError("Test error")
        yield  # Make it async generator

    mock_chat_session.handle_input = mock_handle_input_error

    # Subscribe to error events
    error_queue = event_bus.subscribe(EventType.SYSTEM_ERROR.value)

    # Send message and expect exception
    with pytest.raises(ValueError, match="Test error"):
        async for _ in adapter.send_message("Test message"):
            pass

    # Verify error event published
    error_event = await error_queue.get()
    assert error_event.type == EventType.SYSTEM_ERROR.value
    assert error_event.data["error"] == "Test error"
    assert error_event.data["context"] == "brian_chat"


def test_get_conversation_history(adapter, mock_chat_session):
    """Test getting conversation history."""
    # Setup mock history
    mock_turns = [
        Turn(role="user", content="Hello", timestamp=datetime(2024, 1, 1, 12, 0, 0)),
        Turn(role="brian", content="Hi there!", timestamp=datetime(2024, 1, 1, 12, 0, 1)),
    ]
    mock_chat_session.get_recent_history = MagicMock(return_value=mock_turns)

    # Get history
    history = adapter.get_conversation_history(max_turns=10)

    # Verify
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello"
    assert history[0]["timestamp"] == int(datetime(2024, 1, 1, 12, 0, 0).timestamp() * 1000)
    assert history[0]["agentName"] is None

    assert history[1]["role"] == "brian"
    assert history[1]["content"] == "Hi there!"
    assert history[1]["agentName"] == "Brian"

    mock_chat_session.get_recent_history.assert_called_once_with(10)


def test_get_session_context(adapter, mock_chat_session):
    """Test getting session context."""
    context = adapter.get_session_context()

    # Verify (use Path to normalize cross-platform)
    assert Path(context["projectRoot"]) == Path("/test/project")
    assert context["currentEpic"] == 1
    assert context["currentStory"] == 2
    assert context["pendingConfirmation"] is False
    assert context["contextSummary"] == "Working on Epic 1 | Story 2"


def test_get_session_context_with_pending_confirmation(adapter, mock_chat_session):
    """Test session context shows pending confirmation."""
    mock_chat_session.context.pending_confirmation = MagicMock()  # Not None

    context = adapter.get_session_context()

    assert context["pendingConfirmation"] is True


@pytest.mark.asyncio
async def test_send_message_without_client_id(adapter, mock_chat_session, event_bus):
    """Test sending message without client_id (metadata should be None)."""
    async def mock_handle_input(message):
        yield "Response"

    mock_chat_session.handle_input = mock_handle_input

    # Subscribe to events
    message_sent_queue = event_bus.subscribe(EventType.CHAT_MESSAGE_SENT.value)

    # Send message without client_id
    chunks = []
    async for chunk in adapter.send_message("Test"):
        chunks.append(chunk)

    # Verify event has None metadata
    message_sent_event = await message_sent_queue.get()
    assert message_sent_event.metadata is None or message_sent_event.metadata == {}

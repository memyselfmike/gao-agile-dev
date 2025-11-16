"""Unit tests for event models."""

import time
from datetime import datetime, timezone

import pytest

from gao_dev.web.events import EventType, WebEvent


class TestEventType:
    """Tests for EventType enum."""

    def test_workflow_event_types(self):
        """Test workflow event types are defined."""
        assert EventType.WORKFLOW_STARTED == "workflow.started"
        assert EventType.WORKFLOW_STEP_COMPLETED == "workflow.step_completed"
        assert EventType.WORKFLOW_FINISHED == "workflow.finished"
        assert EventType.WORKFLOW_FAILED == "workflow.failed"

    def test_chat_event_types(self):
        """Test chat event types are defined."""
        assert EventType.CHAT_MESSAGE_SENT == "chat.message_sent"
        assert EventType.CHAT_MESSAGE_RECEIVED == "chat.message_received"
        assert EventType.CHAT_THINKING_STARTED == "chat.thinking_started"
        assert EventType.CHAT_THINKING_FINISHED == "chat.thinking_finished"

    def test_file_event_types(self):
        """Test file event types are defined."""
        assert EventType.FILE_CREATED == "file.created"
        assert EventType.FILE_MODIFIED == "file.modified"
        assert EventType.FILE_DELETED == "file.deleted"

    def test_state_event_types(self):
        """Test state event types are defined."""
        assert EventType.STATE_EPIC_CREATED == "state.epic_created"
        assert EventType.STATE_STORY_CREATED == "state.story_created"
        assert EventType.STATE_STORY_TRANSITIONED == "state.story_transitioned"

    def test_git_event_types(self):
        """Test git event types are defined."""
        assert EventType.GIT_COMMIT_CREATED == "git.commit_created"

    def test_system_event_types(self):
        """Test system event types are defined."""
        assert EventType.SYSTEM_HEARTBEAT == "system.heartbeat"
        assert EventType.SYSTEM_ERROR == "system.error"


class TestWebEvent:
    """Tests for WebEvent dataclass."""

    def test_create_event_with_defaults(self):
        """Test creating event with default values."""
        event = WebEvent.create(
            event_type=EventType.WORKFLOW_STARTED,
            data={"workflow_id": "test-workflow"},
            sequence_number=1,
        )

        assert event.type == "workflow.started"
        assert event.data == {"workflow_id": "test-workflow"}
        assert event.sequence_number == 1
        assert event.metadata == {}
        assert isinstance(event.timestamp, str)

    def test_create_event_with_metadata(self):
        """Test creating event with metadata."""
        metadata = {"client_id": "test-client", "session_id": "test-session"}
        event = WebEvent.create(
            event_type=EventType.CHAT_MESSAGE_SENT,
            data={"message": "Hello"},
            sequence_number=5,
            metadata=metadata,
        )

        assert event.type == "chat.message_sent"
        assert event.data == {"message": "Hello"}
        assert event.sequence_number == 5
        assert event.metadata == metadata

    def test_timestamp_format(self):
        """Test timestamp is ISO 8601 with millisecond precision."""
        event = WebEvent.create(
            event_type=EventType.FILE_CREATED,
            data={"path": "/test/file.py"},
            sequence_number=10,
        )

        # Parse timestamp to verify format
        timestamp = datetime.fromisoformat(event.timestamp)
        assert timestamp.tzinfo == timezone.utc

        # Check millisecond precision (should have at least 3 decimal places)
        assert "." in event.timestamp
        fractional_part = event.timestamp.split(".")[-1].split("+")[0]
        assert len(fractional_part) >= 3

    def test_to_dict(self):
        """Test converting event to dictionary."""
        event = WebEvent.create(
            event_type=EventType.STATE_EPIC_CREATED,
            data={"epic_id": 1, "title": "Test Epic"},
            sequence_number=15,
            metadata={"user": "test"},
        )

        event_dict = event.to_dict()

        assert event_dict["type"] == "state.epic_created"
        assert event_dict["data"] == {"epic_id": 1, "title": "Test Epic"}
        assert event_dict["sequence_number"] == 15
        assert event_dict["metadata"] == {"user": "test"}
        assert "timestamp" in event_dict

    def test_from_dict(self):
        """Test creating event from dictionary."""
        data = {
            "type": "git.commit_created",
            "timestamp": "2024-01-01T12:00:00.123+00:00",
            "sequence_number": 20,
            "data": {"commit_hash": "abc123"},
            "metadata": {"branch": "main"},
        }

        event = WebEvent.from_dict(data)

        assert event.type == "git.commit_created"
        assert event.timestamp == "2024-01-01T12:00:00.123+00:00"
        assert event.sequence_number == 20
        assert event.data == {"commit_hash": "abc123"}
        assert event.metadata == {"branch": "main"}

    def test_from_dict_missing_required_fields(self):
        """Test from_dict raises error for missing required fields."""
        incomplete_data = {
            "type": "workflow.started",
            # Missing timestamp and sequence_number
        }

        with pytest.raises(ValueError, match="Missing required fields"):
            WebEvent.from_dict(incomplete_data)

    def test_from_dict_with_defaults(self):
        """Test from_dict uses defaults for optional fields."""
        minimal_data = {
            "type": "system.heartbeat",
            "timestamp": "2024-01-01T12:00:00.000+00:00",
            "sequence_number": 1,
            # No data or metadata
        }

        event = WebEvent.from_dict(minimal_data)

        assert event.data == {}
        assert event.metadata == {}

    def test_repr(self):
        """Test string representation of event."""
        event = WebEvent.create(
            event_type=EventType.WORKFLOW_FINISHED,
            data={"status": "success"},
            sequence_number=100,
        )

        repr_str = repr(event)

        assert "WebEvent" in repr_str
        assert "workflow.finished" in repr_str
        assert "seq=100" in repr_str
        assert event.timestamp in repr_str

    def test_round_trip_serialization(self):
        """Test event can be serialized and deserialized."""
        original = WebEvent.create(
            event_type=EventType.CHAT_MESSAGE_RECEIVED,
            data={"message": "Test message", "agent": "Brian"},
            sequence_number=42,
            metadata={"session": "abc-123"},
        )

        # Convert to dict and back
        event_dict = original.to_dict()
        restored = WebEvent.from_dict(event_dict)

        assert restored.type == original.type
        assert restored.timestamp == original.timestamp
        assert restored.sequence_number == original.sequence_number
        assert restored.data == original.data
        assert restored.metadata == original.metadata

    @pytest.mark.performance
    def test_event_creation_performance(self):
        """Test event creation is fast (<1ms)."""
        start = time.perf_counter()

        for i in range(1000):
            WebEvent.create(
                event_type=EventType.SYSTEM_HEARTBEAT,
                data={"count": i},
                sequence_number=i,
            )

        end = time.perf_counter()
        duration_ms = (end - start) * 1000

        # Should create 1000 events in under 100ms (0.1ms per event)
        assert duration_ms < 100, f"1000 events took {duration_ms:.2f}ms (should be <100ms)"

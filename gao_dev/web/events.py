"""Event models and schema for WebSocket communication."""

import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict


class EventType(str, Enum):
    """Standardized event types for WebSocket communication.

    Event types are namespaced by component:
    - workflow.*: Workflow execution events
    - chat.*: Brian chat/REPL events
    - file.*: File system events
    - state.*: State management events (epics, stories)
    - git.*: Git operations
    - ceremony.*: Ceremony orchestration (future)
    - kanban.*: Kanban board operations (future)
    """

    # Workflow events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_STEP_COMPLETED = "workflow.step_completed"
    WORKFLOW_FINISHED = "workflow.finished"
    WORKFLOW_FAILED = "workflow.failed"

    # Chat events
    CHAT_MESSAGE_SENT = "chat.message_sent"
    CHAT_MESSAGE_RECEIVED = "chat.message_received"
    CHAT_STREAMING_CHUNK = "chat.streaming_chunk"
    CHAT_THINKING_STARTED = "chat.thinking_started"
    CHAT_THINKING_FINISHED = "chat.thinking_finished"

    # File events
    FILE_CREATED = "file.created"
    FILE_MODIFIED = "file.modified"
    FILE_DELETED = "file.deleted"

    # State events
    STATE_EPIC_CREATED = "state.epic_created"
    STATE_STORY_CREATED = "state.story_created"
    STATE_STORY_TRANSITIONED = "state.story_transitioned"

    # Git events
    GIT_COMMIT_CREATED = "git.commit_created"

    # System events
    SYSTEM_HEARTBEAT = "system.heartbeat"
    SYSTEM_ERROR = "system.error"

    # Future event types (V1.1+)
    CEREMONY_STARTED = "ceremony.started"
    CEREMONY_MESSAGE = "ceremony.message"
    CEREMONY_ENDED = "ceremony.ended"
    KANBAN_CARD_MOVED = "kanban.card_moved"
    KANBAN_CARD_UPDATED = "kanban.card_updated"


@dataclass
class WebEvent:
    """Standardized event schema for WebSocket communication.

    All events follow this schema to ensure consistency and enable
    features like event replay, filtering, and sequencing.

    Attributes:
        type: Event type (from EventType enum)
        timestamp: ISO 8601 timestamp with millisecond precision
        sequence_number: Monotonically increasing sequence number
        data: Event-specific payload
        metadata: Optional metadata (client_id, session_id, etc.)
    """

    type: str
    timestamp: str
    sequence_number: int
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        event_type: EventType,
        data: Dict[str, Any],
        sequence_number: int,
        metadata: Dict[str, Any] | None = None,
    ) -> "WebEvent":
        """Create a new event with automatic timestamp.

        Args:
            event_type: Type of event
            data: Event payload
            sequence_number: Sequence number for ordering
            metadata: Optional metadata

        Returns:
            New WebEvent instance
        """
        # ISO 8601 timestamp with millisecond precision
        timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds")

        return cls(
            type=event_type.value,
            timestamp=timestamp,
            sequence_number=sequence_number,
            data=data,
            metadata=metadata or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the event
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebEvent":
        """Create event from dictionary.

        Args:
            data: Dictionary with event data

        Returns:
            WebEvent instance

        Raises:
            ValueError: If required fields are missing
        """
        required_fields = {"type", "timestamp", "sequence_number"}
        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        return cls(
            type=data["type"],
            timestamp=data["timestamp"],
            sequence_number=data["sequence_number"],
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        """String representation for logging."""
        return (
            f"WebEvent(type={self.type}, seq={self.sequence_number}, "
            f"timestamp={self.timestamp})"
        )

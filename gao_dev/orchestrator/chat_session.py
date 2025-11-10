"""Session state management for interactive chat.

Provides robust session management with:
- Bounded conversation history (max 100 turns)
- Memory monitoring and warnings
- AI context management with token limits
- Cancellation support with grace periods
- Session persistence for recovery

Epic: 30 - Interactive Brian Chat Interface
Story: 30.5 - Session State Management (3 pts + enhancements)
"""

from typing import AsyncIterator, Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import asyncio
import json
import sys
import structlog

logger = structlog.get_logger()


@dataclass
class Turn:
    """
    Single conversation turn.

    Attributes:
        role: "user" or "brian" or "system"
        content: Message content
        timestamp: When turn occurred
        metadata: Additional context (intent, workflow, etc.)
    """

    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Turn":
        """Create from dictionary (for deserialization)."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SessionContext:
    """
    Session-scoped context.

    Attributes:
        project_root: Project root path
        current_epic: Current epic being worked on
        current_story: Current story being worked on
        pending_confirmation: Workflow sequence awaiting confirmation
        last_analysis: Last Brian analysis result
        preferences: User preferences for this session
    """

    project_root: Path
    current_epic: Optional[int] = None
    current_story: Optional[int] = None
    pending_confirmation: Any = None
    last_analysis: Any = None
    preferences: Dict[str, Any] = field(default_factory=dict)


class ChatSession:
    """
    Manage conversation state for interactive chat session.

    Tracks conversation history with bounded limits, maintains context
    across turns, monitors memory usage, supports cancellation, and
    enables multi-turn refinement conversations.

    Features:
    - Bounded history: Max 100 turns (configurable)
    - Memory monitoring: Stats and warnings
    - AI context: Token-limited context for AI
    - Cancellation: asyncio.Event with grace periods
    - Persistence: Save/load session history
    """

    # Configuration constants
    MAX_HISTORY = 100  # Bounded history limit
    MEMORY_WARNING_THRESHOLD = 0.8  # 80% of max history
    MEMORY_SIZE_WARNING_MB = 10.0  # Warn if memory exceeds 10MB
    TOKEN_LIMIT_AI_CONTEXT = 4000  # Max tokens for AI context
    CHARS_PER_TOKEN = 4  # Simple token estimation
    CANCELLATION_GRACE_PERIOD = 5.0  # Seconds to allow cleanup
    SESSION_HISTORY_FILE = "last_session_history.json"

    def __init__(
        self,
        conversational_brian: Any,  # ConversationalBrian
        command_router: Any,  # CommandRouter
        project_root: Path,
        max_history: int = MAX_HISTORY,
    ):
        """
        Initialize chat session.

        Args:
            conversational_brian: ConversationalBrian instance
            command_router: CommandRouter instance
            project_root: Project root path
            max_history: Maximum conversation history (default: 100)
        """
        self.brian = conversational_brian
        self.router = command_router
        self.context = SessionContext(project_root=project_root)
        self.history: List[Turn] = []
        self.max_history = max_history
        self.logger = logger.bind(component="chat_session")

        # Cancellation support
        self.cancel_event = asyncio.Event()
        self.is_cancelled = False

        # Memory tracking
        self._last_memory_warning_at = 0

    async def handle_input(self, user_input: str) -> AsyncIterator[str]:
        """
        Handle user input with session context.

        Coordinates between Brian and router while tracking history
        and respecting cancellation.

        Args:
            user_input: User's message

        Yields:
            Brian's responses

        Raises:
            asyncio.CancelledError: If operation is cancelled
        """
        self.logger.info("handling_input", input_length=len(user_input))

        # Check if cancelled before starting
        if self.is_cancelled:
            self.logger.warning("operation_cancelled_before_start")
            raise asyncio.CancelledError("Session cancelled")

        # Add user turn to history
        self._add_turn("user", user_input)

        # Check memory limits
        self._check_memory_limits()

        try:
            # Get responses from Brian (with session context)
            brian_responses = []

            # Create context for backward compatibility with ConversationalBrian
            from gao_dev.orchestrator.conversational_brian import ConversationContext

            old_context = ConversationContext(
                project_root=str(self.context.project_root),
                session_history=self._format_history_for_legacy(),
                pending_confirmation=self.context.pending_confirmation,
                current_epic=self.context.current_epic,
                current_story=self.context.current_story,
            )

            async for response in self.brian.handle_input(user_input, old_context):
                # Check for cancellation
                if self.cancel_event.is_set():
                    self.logger.warning("operation_cancelled_during_execution")
                    brian_responses.append("[Operation cancelled by user]")
                    yield "[Operation cancelled by user]"
                    raise asyncio.CancelledError("Cancelled by user")

                brian_responses.append(response)
                yield response

            # Sync context back
            self.context.pending_confirmation = old_context.pending_confirmation
            self.context.current_epic = old_context.current_epic
            self.context.current_story = old_context.current_story

            # Add Brian's responses to history
            combined_response = "\n".join(brian_responses)
            self._add_turn("brian", combined_response)

        except asyncio.CancelledError:
            # Mark as cancelled and re-raise
            self.is_cancelled = True
            self._add_turn("system", "Operation cancelled by user")
            raise

        except Exception as e:
            self.logger.exception("error_handling_input", error=str(e))
            self._add_turn("system", f"Error: {str(e)}")
            raise

    def _add_turn(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Add turn to conversation history with bounded limit.

        Args:
            role: "user", "brian", or "system"
            content: Message content
            metadata: Optional metadata
        """
        turn = Turn(role=role, content=content, metadata=metadata or {})

        self.history.append(turn)

        # Trim history if exceeds max (keep system messages if possible)
        if len(self.history) > self.max_history:
            # Calculate how many to remove
            removed_count = len(self.history) - self.max_history

            # Separate system messages from others
            system_turns = [t for t in self.history if t.role == "system"]
            other_turns = [t for t in self.history if t.role != "system"]

            # Remove oldest non-system turns first
            if len(other_turns) > removed_count:
                other_turns = other_turns[removed_count:]
                self.history = system_turns + other_turns
            else:
                # If not enough non-system turns, remove from all
                self.history = self.history[removed_count:]

            self.logger.debug("history_trimmed", removed_count=removed_count)

    def get_recent_history(self, count: int = 5) -> List[Turn]:
        """
        Get recent conversation turns.

        Args:
            count: Number of recent turns to retrieve

        Returns:
            List of recent turns (most recent last)
        """
        return self.history[-count:] if self.history else []

    def get_context_summary(self) -> str:
        """
        Get summary of current session context.

        Returns:
            Human-readable context summary
        """
        parts = []

        if self.context.current_epic:
            parts.append(f"Working on Epic {self.context.current_epic}")

        if self.context.current_story:
            parts.append(f"Story {self.context.current_story}")

        if self.context.pending_confirmation:
            parts.append("Awaiting confirmation")

        if not parts:
            return "No active context"

        return " | ".join(parts)

    def get_context_for_ai(self, max_tokens: int = TOKEN_LIMIT_AI_CONTEXT) -> List[Turn]:
        """
        Get conversation history limited by token count for AI context.

        Prioritizes recent turns and always includes system messages.

        Args:
            max_tokens: Maximum tokens to include (default: 4000)

        Returns:
            List of turns that fit within token limit
        """
        # Separate system messages and conversation turns
        system_turns = [t for t in self.history if t.role == "system"]
        conversation_turns = [t for t in self.history if t.role != "system"]

        # Estimate tokens for system messages
        system_tokens = sum(self._estimate_tokens(t.content) for t in system_turns)

        # Calculate available tokens for conversation
        available_tokens = max_tokens - system_tokens

        if available_tokens <= 0:
            # Only return system messages if no room for conversation
            return system_turns

        # Add conversation turns from most recent, respecting token limit
        included_turns = []
        current_tokens = 0

        for turn in reversed(conversation_turns):
            turn_tokens = self._estimate_tokens(turn.content)

            if current_tokens + turn_tokens <= available_tokens:
                included_turns.insert(0, turn)  # Maintain chronological order
                current_tokens += turn_tokens
            else:
                break

        # Combine system messages + conversation (chronological order)
        return system_turns + included_turns

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Simple heuristic: 1 token ≈ 4 characters.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return len(text) // self.CHARS_PER_TOKEN

    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get memory usage statistics.

        Returns:
            Dictionary with:
            - turn_count: Number of turns in history
            - max_turns: Maximum allowed turns
            - usage_percent: Percentage of max history used
            - memory_mb: Estimated memory usage in MB
            - near_limit: True if near capacity (>80%)
        """
        turn_count = len(self.history)
        usage_percent = (turn_count / self.max_history) * 100

        # Estimate memory usage
        total_chars = sum(len(t.content) for t in self.history)
        memory_mb = (total_chars + len(self.history) * 100) / (1024 * 1024)  # Rough estimate

        return {
            "turn_count": turn_count,
            "max_turns": self.max_history,
            "usage_percent": usage_percent,
            "memory_mb": round(memory_mb, 2),
            "near_limit": usage_percent >= (self.MEMORY_WARNING_THRESHOLD * 100),
        }

    def _check_memory_limits(self):
        """Check memory limits and log warnings if needed."""
        stats = self.get_memory_usage()

        # Warning for turn count (80% threshold)
        if stats["near_limit"]:
            # Only warn once per session or every 10 turns
            current_turn = stats["turn_count"]
            if current_turn - self._last_memory_warning_at >= 10:
                self.logger.warning(
                    "history_near_limit",
                    turn_count=stats["turn_count"],
                    max_turns=stats["max_turns"],
                    usage_percent=stats["usage_percent"],
                )
                self._last_memory_warning_at = current_turn

        # Warning for memory size (10MB threshold)
        if stats["memory_mb"] >= self.MEMORY_SIZE_WARNING_MB:
            self.logger.warning(
                "memory_size_warning",
                memory_mb=stats["memory_mb"],
                threshold_mb=self.MEMORY_SIZE_WARNING_MB,
            )

    async def cancel_current_operation(self, timeout: float = CANCELLATION_GRACE_PERIOD):
        """
        Cancel current operation with grace period.

        Sets cancellation event and waits for grace period to allow
        cleanup. Forces cancellation after timeout.

        Args:
            timeout: Grace period in seconds (default: 5.0)
        """
        self.logger.info("cancelling_operation", grace_period=timeout)

        # Set cancellation event
        self.cancel_event.set()
        self.is_cancelled = True

        # Wait for grace period
        try:
            await asyncio.wait_for(asyncio.sleep(timeout), timeout=timeout)
        except asyncio.TimeoutError:
            pass

        self.logger.info("cancellation_completed")

    def reset_cancellation(self):
        """Reset cancellation state for new operation."""
        self.cancel_event.clear()
        self.is_cancelled = False

    def set_current_epic(self, epic_num: int):
        """Set current epic in context."""
        self.context.current_epic = epic_num
        self.logger.info("epic_context_set", epic=epic_num)

    def set_current_story(self, epic_num: int, story_num: int):
        """Set current story in context."""
        self.context.current_epic = epic_num
        self.context.current_story = story_num
        self.logger.info("story_context_set", epic=epic_num, story=story_num)

    def clear_context(self):
        """Clear session context (but keep history)."""
        self.context.current_epic = None
        self.context.current_story = None
        self.context.pending_confirmation = None
        self.context.last_analysis = None
        self.logger.info("context_cleared")

    def get_last_user_message(self) -> Optional[str]:
        """Get last user message from history."""
        for turn in reversed(self.history):
            if turn.role == "user":
                return turn.content
        return None

    def get_conversation_context(self, max_turns: int = 10) -> str:
        """
        Get conversation context as formatted string.

        Useful for passing to Brian for context-aware analysis.

        Args:
            max_turns: Maximum number of recent turns to include

        Returns:
            Formatted conversation context
        """
        recent = self.get_recent_history(max_turns)

        if not recent:
            return "No prior conversation"

        lines = ["Recent conversation:"]
        for turn in recent:
            role_label = "You" if turn.role == "user" else "Brian" if turn.role == "brian" else "System"
            content_preview = turn.content[:100]
            if len(turn.content) > 100:
                content_preview += "..."
            lines.append(f"  {role_label}: {content_preview}")

        return "\n".join(lines)

    def _format_history_for_legacy(self) -> List[str]:
        """Format history for legacy ConversationContext compatibility."""
        return [f"{t.role.capitalize()}: {t.content}" for t in self.history]

    def save_session(self, file_path: Optional[Path] = None) -> Path:
        """
        Save session history to JSON file.

        Args:
            file_path: Optional custom file path (default: .gao-dev/last_session_history.json)

        Returns:
            Path where session was saved
        """
        if file_path is None:
            gao_dev_dir = self.context.project_root / ".gao-dev"
            gao_dev_dir.mkdir(exist_ok=True)
            file_path = gao_dev_dir / self.SESSION_HISTORY_FILE

        session_data = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.context.project_root),
            "context": {
                "current_epic": self.context.current_epic,
                "current_story": self.context.current_story,
                "preferences": self.context.preferences,
            },
            "history": [turn.to_dict() for turn in self.history],
            "memory_stats": self.get_memory_usage(),
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)

        self.logger.info("session_saved", file_path=str(file_path))
        return file_path

    def load_session(self, file_path: Optional[Path] = None) -> bool:
        """
        Load session history from JSON file.

        Args:
            file_path: Optional custom file path (default: .gao-dev/last_session_history.json)

        Returns:
            True if loaded successfully, False otherwise
        """
        if file_path is None:
            gao_dev_dir = self.context.project_root / ".gao-dev"
            file_path = gao_dev_dir / self.SESSION_HISTORY_FILE

        if not file_path.exists():
            self.logger.info("no_session_file_found", file_path=str(file_path))
            return False

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                session_data = json.load(f)

            # Restore history
            self.history = [Turn.from_dict(t) for t in session_data.get("history", [])]

            # Restore context (partial)
            context_data = session_data.get("context", {})
            self.context.current_epic = context_data.get("current_epic")
            self.context.current_story = context_data.get("current_story")
            self.context.preferences = context_data.get("preferences", {})

            self.logger.info(
                "session_loaded",
                file_path=str(file_path),
                turn_count=len(self.history),
                timestamp=session_data.get("timestamp"),
            )
            return True

        except Exception as e:
            self.logger.error("session_load_failed", error=str(e), file_path=str(file_path))
            return False

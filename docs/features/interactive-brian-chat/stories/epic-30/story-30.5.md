# Story 30.5: Session State Management

**Epic**: Epic 30 - Interactive Brian Chat Interface
**Story ID**: 30.5
**Priority**: P1 (Important - Enhancement)
**Estimate**: 3 story points
**Duration**: 0.5-1 day
**Owner**: Amelia (Developer)
**Status**: Todo
**Dependencies**: Story 30.1 (REPL)

---

## Story Description

Implement robust session state management to track conversation history, maintain context across turns, and enable multi-turn refinement conversations. The session should remember what the user was working on and allow references like "and then add X" without repeating context.

This story enhances the conversational experience by making Brian context-aware within a session.

---

## User Story

**As a** user
**I want** Brian to remember context within our conversation
**So that** I don't have to repeat information in follow-up questions

---

## Acceptance Criteria

### Core Session Management
- [ ] ChatSession tracks conversation history (all turns)
- [ ] Context preserved across turns within session
- [ ] Can reference previous requests: "And then add authentication"
- [ ] Current epic/story tracked in session context
- [ ] Context includes project state, pending actions

### Bounded History (HIGH 2)
- [ ] BoundedHistory implemented with configurable max_size (default: 100)
- [ ] UI history (arrow-up/down) limited to 100 commands
- [ ] Conversation history limited to 100 turns
- [ ] System messages preserved even when pruning
- [ ] Oldest entries automatically removed when limit exceeded

### Memory Monitoring (HIGH 2)
- [ ] get_memory_usage() provides statistics (turn count, memory in MB)
- [ ] Warning shown when approaching history limit (80% = 80 turns)
- [ ] Warning logged when memory exceeds 10MB
- [ ] Memory stats included in session summary on exit

### AI Context Management (HIGH 2)
- [ ] get_context_for_ai() respects token limits (default: 4000 tokens)
- [ ] Recent turns prioritized for context
- [ ] System messages always included in AI context
- [ ] Token estimation prevents context overflow

### Cancellation Support (Critical 4)
- [ ] asyncio.Event for cancellation signaling
- [ ] 5-second grace period for cleanup
- [ ] Force cancellation after timeout
- [ ] Cancellation propagates through all layers (REPL → Session → Router → Orchestrator)
- [ ] Cancelled operations saved to database with status=cancelled
- [ ] Partial artifacts tracked

### State Persistence
- [ ] Conversation history saved to `.gao-dev/last_session_history.json` on exit
- [ ] History can be loaded on next session (optional feature)
- [ ] Memory usage statistics saved
- [ ] Session state saved on exit (integrated with Story 30.1)
- [ ] Database connections closed properly
- [ ] Cache cleared

### Testing
- [ ] Unit tests for BoundedHistory (UI history)
- [ ] Unit tests for BoundedConversationHistory (conversation history)
- [ ] Unit tests for token-limited context retrieval
- [ ] Unit tests for cancellation support
- [ ] Integration test: 150 turns → verify only last 100 kept
- [ ] Integration test: Cancellation during operation
- [ ] Performance test: Memory usage stays under 15MB for 100 turns
- [ ] Manual QA: Long session, verify memory limits work

---

## Files to Create/Modify

### New Files
- `gao_dev/orchestrator/chat_session.py` (~300 LOC)
  - `ChatSession` class
  - Conversation history tracking
  - Context management
  - Turn handling

- `tests/orchestrator/test_chat_session.py` (~200 LOC)
  - Tests for history tracking
  - Tests for context management
  - Tests for multi-turn conversations
  - Tests for memory limits

### Modified Files
- `gao_dev/cli/chat_repl.py` (~30 LOC modified)
  - Use ChatSession for input handling
  - Pass session to ConversationalBrian

- `gao_dev/orchestrator/conversational_brian.py` (~20 LOC modified)
  - Accept ChatSession instead of ConversationContext
  - Use session history for context

---

## Technical Design

### ChatSession Class

**Location**: `gao_dev/orchestrator/chat_session.py`

```python
"""Session state management for interactive chat."""

from typing import AsyncIterator, Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import structlog

from gao_dev.orchestrator.conversational_brian import ConversationalBrian
from gao_dev.cli.command_router import CommandRouter

logger = structlog.get_logger()


@dataclass
class Turn:
    """
    Single conversation turn.

    Attributes:
        role: "user" or "brian"
        content: Message content
        timestamp: When turn occurred
        metadata: Additional context (intent, workflow, etc.)
    """
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


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

    Tracks conversation history, maintains context across turns,
    enables multi-turn refinement conversations.
    """

    MAX_HISTORY = 100  # Limit history to prevent memory issues

    def __init__(
        self,
        conversational_brian: ConversationalBrian,
        command_router: CommandRouter,
        project_root: Path
    ):
        """
        Initialize chat session.

        Args:
            conversational_brian: ConversationalBrian instance
            command_router: CommandRouter instance
            project_root: Project root path
        """
        self.brian = conversational_brian
        self.router = command_router
        self.context = SessionContext(project_root=project_root)
        self.history: List[Turn] = []
        self.logger = logger.bind(component="chat_session")

    async def handle_input(self, user_input: str) -> AsyncIterator[str]:
        """
        Handle user input with session context.

        Args:
            user_input: User's message

        Yields:
            Brian's responses
        """
        self.logger.info("handling_input", input_length=len(user_input))

        # Add user turn to history
        self._add_turn("user", user_input)

        # Get responses from Brian (with session context)
        brian_responses = []
        async for response in self.brian.handle_input(user_input, self):
            brian_responses.append(response)
            yield response

        # Add Brian's responses to history
        combined_response = "\n".join(brian_responses)
        self._add_turn("brian", combined_response)

    def _add_turn(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Add turn to conversation history.

        Args:
            role: "user" or "brian"
            content: Message content
            metadata: Optional metadata
        """
        turn = Turn(
            role=role,
            content=content,
            metadata=metadata or {}
        )

        self.history.append(turn)

        # Trim history if exceeds max
        if len(self.history) > self.MAX_HISTORY:
            removed = len(self.history) - self.MAX_HISTORY
            self.history = self.history[removed:]
            self.logger.debug("history_trimmed", removed_count=removed)

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
            role_label = "You" if turn.role == "user" else "Brian"
            content_preview = turn.content[:100]
            lines.append(f"  {role_label}: {content_preview}...")

        return "\n".join(lines)
```

### ConversationalBrian Enhancement

**Location**: `gao_dev/orchestrator/conversational_brian.py` (modify)

```python
class ConversationalBrian:
    """Conversational wrapper around BrianOrchestrator."""

    async def handle_input(
        self,
        user_input: str,
        session: 'ChatSession'  # NEW: Accept ChatSession instead of context
    ) -> AsyncIterator[str]:
        """
        Handle user input conversationally.

        Args:
            user_input: User's message
            session: Chat session with history and context

        Yields:
            Conversational responses
        """
        self.logger.info("handling_input", input_length=len(user_input))

        # Parse intent
        intent = self.intent_parser.parse(user_input)

        # Route based on intent
        if intent.type == IntentType.CONFIRMATION:
            # Handle pending confirmation (use session context)
            async for response in self._handle_confirmation(intent, session):
                yield response

        elif intent.type == IntentType.FEATURE_REQUEST:
            # Analyze feature request with session context
            async for response in self._handle_feature_request(user_input, session):
                yield response

        # ... (rest of handlers)

    async def _handle_feature_request(
        self,
        user_input: str,
        session: 'ChatSession'  # NEW: Use session
    ) -> AsyncIterator[str]:
        """Handle feature/project request with session context."""
        self.logger.info("handling_feature_request")

        # NEW: Check if this is a follow-up request
        last_user_msg = session.get_last_user_message()
        if last_user_msg and self._is_follow_up(user_input):
            # Augment input with context from last request
            augmented_input = f"{last_user_msg}\n\nAdditionally: {user_input}"
            yield f"Building on your previous request..."
        else:
            augmented_input = user_input
            yield "Let me analyze that for you..."

        # Analyze with Brian (pass conversation context)
        context_summary = session.get_conversation_context()

        try:
            analysis = await self.brian.assess_and_select_workflows(
                augmented_input,
                project_root=str(session.context.project_root),
                conversation_context=context_summary  # NEW: Pass context
            )
        except Exception as e:
            # ... (error handling)

        # Store analysis in session context
        session.context.last_analysis = analysis

        # Present analysis
        yield self._format_analysis(analysis)

        # Store pending confirmation in session
        session.context.pending_confirmation = analysis

        yield "\nShall I proceed with this plan? (yes/no)"

    def _is_follow_up(self, user_input: str) -> bool:
        """
        Detect if input is a follow-up to previous request.

        Args:
            user_input: User's current input

        Returns:
            True if appears to be follow-up
        """
        follow_up_indicators = [
            "and then",
            "also add",
            "plus",
            "additionally",
            "after that",
            "then"
        ]

        user_lower = user_input.lower()
        return any(indicator in user_lower for indicator in follow_up_indicators)

    async def _handle_confirmation(
        self,
        intent: Intent,
        session: 'ChatSession'  # NEW: Use session
    ) -> AsyncIterator[str]:
        """Handle confirmation with session context."""
        if not session.context.pending_confirmation:
            yield "I'm not sure what you're confirming. What would you like to do?"
            return

        if intent.is_positive:
            yield "Great! I'll coordinate with the team to get started..."

            # Execute workflows
            async for message in self.command_router.execute_workflow_sequence(
                session.context.pending_confirmation,
                session.context.project_root
            ):
                yield message

            # Clear pending confirmation in session
            session.context.pending_confirmation = None

        else:
            yield "No problem! Let me know if you'd like to try a different approach."
            session.context.pending_confirmation = None
```

### ChatREPL Integration

**Location**: `gao_dev/cli/chat_repl.py` (modify)

```python
class ChatREPL:
    """Interactive REPL for conversational chat with Brian."""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize ChatREPL with session management."""
        self.project_root = project_root or Path.cwd()
        # ... (existing initialization)

        # NEW: Create ChatSession
        from gao_dev.orchestrator.chat_session import ChatSession

        self.session = ChatSession(
            conversational_brian=self.conversational_brian,
            command_router=self.command_router,
            project_root=self.project_root
        )

    async def _handle_input(self, user_input: str) -> None:
        """Handle user input via session."""
        # Use session to handle input (tracks history automatically)
        async for response in self.session.handle_input(user_input):
            self._display_response(response)
```

---

## Testing Strategy

### Unit Tests

**Location**: `tests/orchestrator/test_chat_session.py`

**Test Cases**:

1. **test_session_initialization**
   - ChatSession initializes with empty history
   - Context initialized with project root

2. **test_add_turn_to_history**
   - Add user turn → History contains turn
   - Add Brian turn → History contains both

3. **test_history_limit**
   - Add 150 turns → History capped at 100
   - Oldest turns removed

4. **test_get_recent_history**
   - Request last 5 turns → Returns correct turns
   - Most recent last

5. **test_context_management**
   - Set current epic → Context updated
   - Set current story → Context updated
   - Clear context → Context cleared but history remains

6. **test_pending_confirmation**
   - Store pending confirmation → Retrieved correctly
   - Clear after confirmation → No longer pending

7. **test_conversation_context_format**
   - Format conversation context → Human-readable string
   - Includes recent turns

8. **test_follow_up_detection**
   - "And then add X" → Detected as follow-up
   - Standalone request → Not follow-up

**Example Test**:
```python
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from gao_dev.orchestrator.chat_session import ChatSession, Turn


@pytest.mark.asyncio
async def test_session_tracks_history():
    """Test that session tracks conversation history."""
    # Mock dependencies
    mock_brian = MagicMock()
    mock_brian.handle_input = AsyncMock(return_value=iter(["Response"]))

    mock_router = MagicMock()

    # Create session
    session = ChatSession(
        conversational_brian=mock_brian,
        command_router=mock_router,
        project_root=Path("/test")
    )

    # Handle input
    responses = []
    async for response in session.handle_input("Hello"):
        responses.append(response)

    # Assert history tracked
    assert len(session.history) == 2  # User + Brian
    assert session.history[0].role == "user"
    assert session.history[0].content == "Hello"
    assert session.history[1].role == "brian"


def test_history_limit():
    """Test that history is limited to MAX_HISTORY."""
    mock_brian = MagicMock()
    mock_router = MagicMock()

    session = ChatSession(mock_brian, mock_router, Path("/test"))

    # Add 150 turns
    for i in range(150):
        session._add_turn("user", f"Message {i}")

    # Assert capped at 100
    assert len(session.history) == 100
    # Oldest messages removed
    assert "Message 149" in session.history[-1].content
    assert "Message 0" not in [t.content for t in session.history]
```

---

## Definition of Done

- [ ] Code written and follows GAO-Dev standards (DRY, SOLID, typed)
- [ ] 8+ unit tests written and passing
- [ ] Integration test: Multi-turn conversation uses context
- [ ] Manual testing: Follow-up requests work
- [ ] History tracking verified
- [ ] Memory limits enforced
- [ ] Code review completed
- [ ] Git commit: `feat(epic-30): Story 30.5 - Session State Management (3 pts)`
- [ ] Documentation updated (inline docstrings)

---

## Dependencies

### Internal Dependencies
- Story 30.1 (ChatREPL must exist)
- Story 30.3 (ConversationalBrian must exist)

### No New External Dependencies

---

## Implementation Notes

### History Management

**Efficiency**:
- Store only last 100 turns (MAX_HISTORY constant)
- Trim oldest turns when limit exceeded
- Low memory footprint (~20KB for 100 turns)

**Future Enhancement**: Persist history to disk for long-term memory

### Context vs History

**History**: Raw conversation turns (user + Brian)
**Context**: Structured session state (current epic, pending confirmation)

Both are useful:
- History for reference ("what did I ask before?")
- Context for state management ("what am I working on?")

### Follow-Up Detection

**Current Implementation**: Simple keyword matching
- "and then", "also add", "additionally"

**Future Enhancement**: Semantic similarity
- Use embeddings to detect if request is related
- More accurate follow-up detection

### Context Augmentation

**Pattern**:
1. Detect follow-up request
2. Retrieve last user message from history
3. Augment current input: "Previous: X\n\nAdditionally: Y"
4. Pass augmented input to Brian

**Benefit**: Brian sees full context, makes better recommendations

---

## Manual Testing Checklist

- [ ] Run `gao-dev start`
- [ ] Type: "I want to build a todo app"
  - [ ] Brian analyzes
- [ ] Type: "And then add authentication"
  - [ ] Brian acknowledges: "Building on your previous request..."
  - [ ] Analysis includes both todo app + auth
- [ ] Type: "What did I ask for?"
  - [ ] Brian references conversation history
- [ ] Type: "yes" (to confirm)
  - [ ] Workflows execute
  - [ ] Pending confirmation cleared
- [ ] Type: "What's pending?"
  - [ ] Brian says: "Nothing pending"
- [ ] Add 50 requests
  - [ ] History capped at 100 turns
  - [ ] No memory issues

---

## Next Steps

After Story 30.5 is complete:

**Story 30.6**: Add greenfield project initialization flow
**Story 30.7**: Testing and documentation

---

**Created**: 2025-11-10
**Status**: Ready to Implement

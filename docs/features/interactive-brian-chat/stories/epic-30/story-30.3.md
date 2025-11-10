# Story 30.3: Conversational Brian Integration

**Epic**: Epic 30 - Interactive Brian Chat Interface
**Story ID**: 30.3
**Priority**: P0 (Critical - Core Feature)
**Estimate**: 8 story points
**Duration**: 2-3 days
**Owner**: Amelia (Developer)
**Status**: Todo
**Dependencies**: Story 30.1 (REPL), Story 30.2 (Status)

---

## Story Description

Replace the simple echo placeholder with real conversational interaction with Brian. When users type natural language prompts, parse the intent, call BrianOrchestrator's `assess_and_select_workflows()`, format the analysis conversationally, and handle confirmation flows.

This is the **core value story** of Epic 30 - transforming Brian from a one-shot analyzer into a conversational partner.

---

## User Story

**As a** user
**I want** to chat naturally with Brian about what I want to build
**So that** Brian can analyze and recommend workflows conversationally

---

## Acceptance Criteria

- [ ] Natural language prompts parsed correctly
- [ ] Intent detection: Feature request vs question vs command
- [ ] BrianOrchestrator integration: Call `assess_and_select_workflows()`
- [ ] Analysis formatted conversationally (not JSON dump)
- [ ] Multi-turn confirmation flow: "Shall I proceed?" → User confirms → Execute
- [ ] Context passed to Brian (project state, session history)
- [ ] Helpful responses for unclear requests: "Could you clarify...?"
- [ ] Progress indicators during analysis: "Analyzing..."
- [ ] 12+ unit tests for conversation flow
- [ ] Integration test: Full feature request conversation

---

## Files to Create/Modify

### New Files
- `gao_dev/orchestrator/conversational_brian.py` (~350 LOC)
  - `ConversationalBrian` class
  - Intent parsing logic
  - Analysis formatting
  - Confirmation flow handling

- `gao_dev/orchestrator/intent_parser.py` (~200 LOC)
  - `IntentParser` class
  - Pattern matching for intents
  - Entity extraction (epic numbers, story IDs)

- `tests/orchestrator/test_conversational_brian.py` (~250 LOC)
  - Tests for intent parsing
  - Tests for analysis formatting
  - Tests for confirmation flows
  - Tests for error handling

### Modified Files
- `gao_dev/cli/chat_repl.py` (~50 LOC modified)
  - Replace `_handle_input()` echo with ConversationalBrian
  - Integrate intent parsing
  - Handle streaming responses

---

## Technical Design

### ConversationalBrian Class

**Location**: `gao_dev/orchestrator/conversational_brian.py`

```python
"""Conversational wrapper around BrianOrchestrator."""

from typing import AsyncIterator, Dict, Any, Optional
from dataclasses import dataclass
import structlog

from gao_dev.orchestrator.brian_orchestrator import BrianOrchestrator
from gao_dev.core.models.workflow_sequence import WorkflowSequence
from .intent_parser import IntentParser, Intent, IntentType

logger = structlog.get_logger()


@dataclass
class ConversationContext:
    """
    Context for conversation session.

    Attributes:
        project_root: Project root path
        session_history: List of conversation turns
        pending_confirmation: Workflow sequence awaiting confirmation
        current_epic: Current epic number (if any)
        current_story: Current story number (if any)
    """
    project_root: str
    session_history: list[str]
    pending_confirmation: Optional[WorkflowSequence] = None
    current_epic: Optional[int] = None
    current_story: Optional[int] = None


class ConversationalBrian:
    """
    Conversational wrapper around BrianOrchestrator.

    Transforms Brian's analytical capabilities into natural dialogue.
    Handles intent parsing, workflow analysis formatting, and
    confirmation flows.
    """

    def __init__(self, brian_orchestrator: BrianOrchestrator):
        """
        Initialize conversational Brian.

        Args:
            brian_orchestrator: BrianOrchestrator instance
        """
        self.brian = brian_orchestrator
        self.intent_parser = IntentParser()
        self.logger = logger.bind(component="conversational_brian")

    async def handle_input(
        self,
        user_input: str,
        context: ConversationContext
    ) -> AsyncIterator[str]:
        """
        Handle user input conversationally.

        Parses intent, routes to appropriate handler, yields
        conversational responses.

        Args:
            user_input: User's message
            context: Conversation context

        Yields:
            Conversational responses
        """
        self.logger.info("handling_input", input_length=len(user_input))

        # Parse intent
        intent = self.intent_parser.parse(user_input)

        # Route based on intent
        if intent.type == IntentType.CONFIRMATION:
            # Handle pending confirmation
            async for response in self._handle_confirmation(intent, context):
                yield response

        elif intent.type == IntentType.FEATURE_REQUEST:
            # Analyze feature request with Brian
            async for response in self._handle_feature_request(user_input, context):
                yield response

        elif intent.type == IntentType.QUESTION:
            # Answer question
            yield self._handle_question(user_input, context)

        elif intent.type == IntentType.HELP:
            # Show help
            yield self._show_help()

        else:
            # Unclear input
            yield self._handle_unclear(user_input)

    async def _handle_feature_request(
        self,
        user_input: str,
        context: ConversationContext
    ) -> AsyncIterator[str]:
        """
        Handle feature/project request with Brian.

        Args:
            user_input: User's request
            context: Conversation context

        Yields:
            Conversational responses
        """
        self.logger.info("handling_feature_request")

        # Phase 1: Acknowledge
        yield "Let me analyze that for you..."

        # Phase 2: Analyze with Brian
        try:
            analysis = await self.brian.assess_and_select_workflows(
                user_input,
                project_root=context.project_root
            )
        except Exception as e:
            self.logger.exception("analysis_failed", error=str(e))
            yield f"I encountered an error analyzing your request: {str(e)}"
            yield "Could you rephrase your request or provide more details?"
            return

        # Phase 3: Present analysis conversationally
        yield self._format_analysis(analysis)

        # Phase 4: Store pending confirmation
        context.pending_confirmation = analysis

        # Phase 5: Ask for confirmation
        yield "\nShall I proceed with this plan? (yes/no)"

    def _format_analysis(self, analysis: WorkflowSequence) -> str:
        """
        Format Brian's analysis as conversational message.

        Args:
            analysis: WorkflowSequence from Brian

        Returns:
            Formatted analysis message
        """
        # Format scale level
        scale_desc = self._describe_scale_level(analysis.scale_level)

        # Format workflows
        workflows_desc = self._format_workflows(analysis.workflows)

        # Estimate duration
        duration_desc = self._estimate_duration(analysis)

        return f"""
I've analyzed your request. Here's what I found:

**Scale Level**: {scale_desc}
**Project Type**: {analysis.project_type.value if hasattr(analysis, 'project_type') else 'Unknown'}

**Reasoning**: {analysis.rationale}

**Recommended Workflows**:
{workflows_desc}

**Estimated Duration**: {duration_desc}
        """.strip()

    def _describe_scale_level(self, scale_level: Any) -> str:
        """Describe scale level in natural language."""
        descriptions = {
            0: "Level 0 - Quick chore (< 1 hour, no planning needed)",
            1: "Level 1 - Bug fix (1-4 hours, minimal planning)",
            2: "Level 2 - Small feature (1-2 weeks, light planning)",
            3: "Level 3 - Medium feature (1-2 months, full planning)",
            4: "Level 4 - Greenfield app (2-6 months, comprehensive)"
        }
        level_num = scale_level.value if hasattr(scale_level, 'value') else scale_level
        return descriptions.get(level_num, f"Level {level_num}")

    def _format_workflows(self, workflows: list) -> str:
        """Format workflow list as bullet points."""
        if not workflows:
            return "  - Direct implementation (no formal workflows)"

        lines = []
        for i, workflow in enumerate(workflows, 1):
            workflow_name = workflow.name if hasattr(workflow, 'name') else str(workflow)
            lines.append(f"  {i}. {workflow_name}")

        return "\n".join(lines)

    def _estimate_duration(self, analysis: WorkflowSequence) -> str:
        """Estimate duration from workflow sequence."""
        # Simple heuristic based on workflow count
        workflow_count = len(analysis.workflows) if analysis.workflows else 1

        if workflow_count <= 2:
            return "Less than 1 hour"
        elif workflow_count <= 4:
            return "A few hours"
        elif workflow_count <= 8:
            return "1-2 days"
        else:
            return "Several days to weeks"

    async def _handle_confirmation(
        self,
        intent: Intent,
        context: ConversationContext
    ) -> AsyncIterator[str]:
        """
        Handle confirmation response.

        Args:
            intent: Parsed confirmation intent
            context: Conversation context

        Yields:
            Conversational responses
        """
        if not context.pending_confirmation:
            yield "I'm not sure what you're confirming. What would you like to do?"
            return

        if intent.is_positive:
            # User confirmed - execute will happen in Story 30.4
            yield "Great! I'll coordinate with the team to get started..."
            # NOTE: Actual execution will be handled by CommandRouter in Story 30.4
            # For now, just acknowledge
            yield "(Execution will be implemented in Story 30.4)"

            # Clear pending confirmation
            context.pending_confirmation = None

        else:
            # User declined
            yield "No problem! Let me know if you'd like to try a different approach."
            context.pending_confirmation = None

    def _handle_question(self, user_input: str, context: ConversationContext) -> str:
        """
        Handle user question.

        Args:
            user_input: User's question
            context: Conversation context

        Returns:
            Answer or guidance
        """
        # Simple keyword-based Q&A
        # Future: Could use RAG or semantic search

        user_lower = user_input.lower()

        if "status" in user_lower or "progress" in user_lower:
            return "To see project status, I check at startup. Type 'refresh' to reload."

        elif "workflow" in user_lower:
            return "I can select workflows based on your request. Just describe what you want to build!"

        elif "help" in user_lower or "what can" in user_lower:
            return self._show_help()

        else:
            return "I'm not sure about that. Could you ask in a different way, or type 'help' for guidance?"

    def _show_help(self) -> str:
        """Show help message."""
        return """
I'm here to help you build software! Here's what I can do:

**Feature Requests**: Just describe what you want to build
  - "I want to add authentication"
  - "Build a todo app with a REST API"
  - "Fix the bug in the login flow"

**Project Information**:
  - "What's the status?" - Current project state
  - "What should I work on next?" - Suggestions

**Commands**:
  - 'help' - Show this message
  - 'exit', 'quit', 'bye' - End session

Just type naturally and I'll figure out what you need!
        """.strip()

    def _handle_unclear(self, user_input: str) -> str:
        """
        Handle unclear input.

        Args:
            user_input: User's unclear message

        Returns:
            Helpful clarification request
        """
        return f"""
I'm not quite sure what you mean by "{user_input[:50]}...".

Could you rephrase that? For example:
  - "I want to build [feature]"
  - "Help me fix [bug]"
  - "What's the status?"

Or type 'help' for more guidance.
        """.strip()
```

### IntentParser Class

**Location**: `gao_dev/orchestrator/intent_parser.py`

```python
"""Intent parsing for conversational input."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional
import re


class IntentType(Enum):
    """Types of user intents."""
    FEATURE_REQUEST = "feature_request"
    CONFIRMATION = "confirmation"
    QUESTION = "question"
    HELP = "help"
    UNCLEAR = "unclear"


@dataclass
class Intent:
    """
    Parsed user intent.

    Attributes:
        type: Type of intent
        is_positive: For confirmations, whether yes or no
        entities: Extracted entities (epic numbers, story IDs, etc.)
    """
    type: IntentType
    is_positive: Optional[bool] = None
    entities: dict = None


class IntentParser:
    """
    Parse user input to detect intent.

    Uses simple pattern matching and keyword detection.
    Future: Could use NLP models for better accuracy.
    """

    def __init__(self):
        """Initialize parser with patterns."""
        self._confirmation_patterns = [
            r'\b(yes|yeah|yep|sure|ok|okay|proceed|go ahead)\b',
            r'\b(no|nope|nah|cancel|abort|stop)\b'
        ]

        self._feature_request_patterns = [
            r'\b(build|create|add|implement|make|develop)\b',
            r'\b(want|need|like)\s+(to\s+)?(build|create|add)',
            r'\b(fix|repair|debug)\b'
        ]

        self._question_patterns = [
            r'\b(what|how|why|when|where|who)\b',
            r'\b(status|progress|current)\b',
            r'\?$'
        ]

    def parse(self, user_input: str) -> Intent:
        """
        Parse user input to detect intent.

        Args:
            user_input: User's message

        Returns:
            Parsed Intent
        """
        user_lower = user_input.lower().strip()

        # Check for help
        if self._is_help_request(user_lower):
            return Intent(type=IntentType.HELP)

        # Check for confirmation
        confirmation = self._parse_confirmation(user_lower)
        if confirmation:
            return confirmation

        # Check for question
        if self._is_question(user_lower):
            return Intent(type=IntentType.QUESTION)

        # Check for feature request
        if self._is_feature_request(user_lower):
            return Intent(type=IntentType.FEATURE_REQUEST)

        # Default to unclear
        return Intent(type=IntentType.UNCLEAR)

    def _is_help_request(self, text: str) -> bool:
        """Check if input is help request."""
        return text in ["help", "?", "what can you do"]

    def _parse_confirmation(self, text: str) -> Optional[Intent]:
        """Parse confirmation (yes/no)."""
        # Check positive confirmation
        if re.search(self._confirmation_patterns[0], text, re.IGNORECASE):
            return Intent(type=IntentType.CONFIRMATION, is_positive=True)

        # Check negative confirmation
        if re.search(self._confirmation_patterns[1], text, re.IGNORECASE):
            return Intent(type=IntentType.CONFIRMATION, is_positive=False)

        return None

    def _is_question(self, text: str) -> bool:
        """Check if input is a question."""
        for pattern in self._question_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _is_feature_request(self, text: str) -> bool:
        """Check if input is a feature request."""
        for pattern in self._feature_request_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
```

### ChatREPL Integration

**Location**: `gao_dev/cli/chat_repl.py` (modify existing)

```python
class ChatREPL:
    """Interactive REPL for conversational chat with Brian."""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize ChatREPL."""
        self.project_root = project_root or Path.cwd()
        self.console = Console()
        self.history = InMemoryHistory()
        self.prompt_session = PromptSession(history=self.history)
        self.logger = logger.bind(component="chat_repl")

        # Status reporter (Story 30.2)
        self.status_reporter = ProjectStatusReporter(self.project_root)

        # NEW: Conversational Brian (Story 30.3)
        from gao_dev.orchestrator.brian_orchestrator import BrianOrchestrator
        from gao_dev.orchestrator.conversational_brian import (
            ConversationalBrian,
            ConversationContext
        )

        brian_orchestrator = BrianOrchestrator()
        self.conversational_brian = ConversationalBrian(brian_orchestrator)

        # Conversation context
        self.context = ConversationContext(
            project_root=str(self.project_root),
            session_history=[]
        )

    async def _handle_input(self, user_input: str) -> None:
        """
        Handle user input with conversational Brian.

        Replaces simple echo from Story 30.1 with real conversation.
        """
        # Add to session history
        self.context.session_history.append(f"User: {user_input}")

        # Get responses from conversational Brian
        async for response in self.conversational_brian.handle_input(
            user_input,
            self.context
        ):
            self._display_response(response)

            # Add to session history
            self.context.session_history.append(f"Brian: {response}")
```

---

## Testing Strategy

### Unit Tests

**Location**: `tests/orchestrator/test_conversational_brian.py`

**Test Cases**:

1. **test_intent_parsing_feature_request**
   - Input: "I want to build a todo app"
   - Intent: FEATURE_REQUEST

2. **test_intent_parsing_confirmation_yes**
   - Input: "yes" / "sure" / "go ahead"
   - Intent: CONFIRMATION, is_positive=True

3. **test_intent_parsing_confirmation_no**
   - Input: "no" / "cancel"
   - Intent: CONFIRMATION, is_positive=False

4. **test_intent_parsing_question**
   - Input: "What's the status?"
   - Intent: QUESTION

5. **test_feature_request_analysis**
   - User requests feature → Brian analyzes
   - Response includes scale level, workflows, duration

6. **test_confirmation_flow_positive**
   - Pending confirmation + "yes" → Acknowledge execution
   - Context.pending_confirmation cleared

7. **test_confirmation_flow_negative**
   - Pending confirmation + "no" → Acknowledge decline
   - Context.pending_confirmation cleared

8. **test_unclear_input_handling**
   - Random gibberish → Helpful clarification request
   - Doesn't crash

9. **test_help_request**
   - "help" → Shows help message
   - Includes examples and commands

10. **test_question_handling**
    - "What can you do?" → Descriptive answer
    - "What's the status?" → Status guidance

**Example Test**:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from gao_dev.orchestrator.conversational_brian import (
    ConversationalBrian,
    ConversationContext
)
from gao_dev.orchestrator.intent_parser import IntentType


@pytest.mark.asyncio
async def test_feature_request_analysis():
    """Test feature request analysis flow."""
    # Mock BrianOrchestrator
    mock_brian = MagicMock()
    mock_analysis = MagicMock()
    mock_analysis.scale_level = MagicMock(value=2)
    mock_analysis.rationale = "Small feature requiring PRD and stories"
    mock_analysis.workflows = [MagicMock(name="create_prd"), MagicMock(name="create_stories")]

    mock_brian.assess_and_select_workflows = AsyncMock(return_value=mock_analysis)

    # Create conversational Brian
    conv_brian = ConversationalBrian(mock_brian)

    # Context
    context = ConversationContext(
        project_root="/test/project",
        session_history=[]
    )

    # Handle feature request
    responses = []
    async for response in conv_brian.handle_input("I want to add authentication", context):
        responses.append(response)

    # Assert
    assert len(responses) >= 3
    assert "analyze" in responses[0].lower()
    assert "Level 2" in responses[1] or "Small feature" in responses[1]
    assert "Shall I proceed" in responses[-1]

    # Assert pending confirmation stored
    assert context.pending_confirmation is not None


def test_intent_parser_feature_request():
    """Test intent parsing for feature requests."""
    from gao_dev.orchestrator.intent_parser import IntentParser

    parser = IntentParser()

    # Test various feature request phrasings
    assert parser.parse("I want to build a todo app").type == IntentType.FEATURE_REQUEST
    assert parser.parse("Add authentication to my app").type == IntentType.FEATURE_REQUEST
    assert parser.parse("Fix the login bug").type == IntentType.FEATURE_REQUEST
```

---

## Definition of Done

- [ ] Code written and follows GAO-Dev standards (DRY, SOLID, typed)
- [ ] 12+ unit tests written and passing
- [ ] Integration test: Full feature request conversation
- [ ] Manual testing: Natural language prompts work
- [ ] Brian's responses feel conversational (not robotic)
- [ ] Confirmation flow works (yes/no)
- [ ] Code review completed
- [ ] Git commit: `feat(epic-30): Story 30.3 - Conversational Brian Integration (8 pts)`
- [ ] Documentation updated (inline docstrings)

---

## Dependencies

### Internal Dependencies
- Story 30.1 (ChatREPL must exist)
- Story 30.2 (Status reporter for context)
- BrianOrchestrator (Epic 7.2, 29)
- WorkflowSequence models (Epic 7.2)

### No New External Dependencies
All required libraries already in use.

---

## Implementation Notes

### Intent Parsing Approach

**Story 30.3 (This Story)**: Simple pattern matching
- Regex patterns for common intents
- Keyword detection
- Good enough for 80% of cases

**Future Enhancement**: NLP models
- spaCy for entity extraction
- Transformers for intent classification
- Semantic similarity for unclear inputs

### Conversational Tone

**Guidelines**:
- Friendly but professional
- Use "I" and "you" (not "the system" and "the user")
- Acknowledge before analyzing: "Let me analyze that..."
- Present findings clearly with structure
- Ask for confirmation: "Shall I proceed?"
- Be helpful on errors: "Could you rephrase...?"

**Anti-Patterns to Avoid**:
- Overly verbose responses
- Technical jargon without explanation
- JSON dumps or raw data
- Robotic phrasing: "Request processed. Output: ..."

### Multi-Turn Conversation

**Story 30.3 Scope**:
- Single-turn feature request
- Single-turn confirmation
- Session history tracked but not used yet

**Future Enhancement (Story 30.5)**:
- Context from previous turns
- "And then add X" references prior request
- "Tell me more about that" clarifications

### Error Handling

**Graceful Failures**:
- Analysis fails → Suggest rephrase
- Unclear input → Show examples
- No pending confirmation → Guide user
- Always offer helpful next steps

---

## Manual Testing Checklist

- [ ] Run `gao-dev start`
- [ ] Type: "I want to build a todo app"
  - [ ] Brian acknowledges: "Let me analyze..."
  - [ ] Brian presents analysis with scale level, workflows
  - [ ] Brian asks: "Shall I proceed?"
- [ ] Type: "yes"
  - [ ] Brian acknowledges: "Great! I'll coordinate..."
  - [ ] (Execution placeholder for Story 30.4)
- [ ] Type: "I want to add authentication"
  - [ ] Same flow as above
- [ ] Type: "no" after analysis
  - [ ] Brian acknowledges: "No problem!"
  - [ ] Clears pending confirmation
- [ ] Type: "What can you do?"
  - [ ] Brian shows help message
- [ ] Type: "gibberish asdf qwerty"
  - [ ] Brian asks for clarification
  - [ ] Provides examples
- [ ] Type: "help"
  - [ ] Shows comprehensive help

---

## Next Steps

After Story 30.3 is complete:

**Story 30.4**: Add command routing to actually execute workflows
**Story 30.5**: Enhance session state with context memory for multi-turn refinements

---

**Created**: 2025-11-10
**Status**: Ready to Implement

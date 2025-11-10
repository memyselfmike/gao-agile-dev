# Interactive Brian Chat Architecture

**Feature ID**: interactive-brian-chat
**Epic**: 30
**Version**: 1.0
**Created**: 2025-11-10
**Status**: Planning

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Principles](#architecture-principles)
3. [System Architecture](#system-architecture)
4. [Component Design](#component-design)
5. [Data Flow](#data-flow)
6. [Technology Stack](#technology-stack)
7. [Integration Points](#integration-points)
8. [Performance Considerations](#performance-considerations)
9. [Security & Safety](#security--safety)
10. [Testing Strategy](#testing-strategy)

---

## Overview

The Interactive Brian Chat Interface transforms GAO-Dev from a command-line tool into a conversational development partner. This is achieved by adding a thin REPL (Read-Eval-Print Loop) layer on top of existing orchestration infrastructure.

**Key Insight**: 95% of the functionality already exists (Epics 22-29). Epic 30 adds the 5% conversational wrapper that makes it accessible via natural dialogue.

### Design Goals

1. **Minimal New Code**: Leverage existing Brian, ConversationManager, orchestrator
2. **Thin Wrapper**: REPL is just I/O layer, business logic stays in orchestrator
3. **Non-Breaking**: All existing CLI commands continue to work
4. **Fast Startup**: <2 seconds from command to greeting
5. **Rich UX**: Beautiful terminal formatting with Rich library

---

## Architecture Principles

### 1. Separation of Concerns

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface Layer                  │
│  (REPL, Formatting, Input Parsing, Session Management)  │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Conversational Orchestration                │
│   (Intent Detection, Dialogue Flow, Response Generation) │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                 Business Logic Layer                     │
│  (BrianOrchestrator, GAODevOrchestrator, Workflows)    │
└──────────────────────────────────────────────────────────┘
```

**Principle**: REPL is stateless I/O. All state lives in orchestrator.

### 2. Composability

Every component is composable and testable in isolation:
- `ChatREPL` - Pure I/O loop
- `ChatSession` - Session state management
- `ConversationalBrian` - Dialogue wrapper around BrianOrchestrator
- `ProjectStatusReporter` - Project detection and status

### 3. Fail-Safe Defaults

- Empty input → Helpful prompt, don't crash
- Unknown command → Suggest alternatives, don't error
- Ctrl+C → Graceful exit with goodbye message
- Project not found → Offer to initialize

### 4. Progressive Enhancement

Start simple, add features incrementally:
1. Basic REPL loop (Story 30.1)
2. Add project detection (Story 30.2)
3. Add conversational Brian (Story 30.3)
4. Add command routing (Story 30.4)
5. Add session memory (Story 30.5)
6. Add greenfield init (Story 30.6)

---

## System Architecture

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                          Terminal                             │
│  User types: "I want to build a todo app"                    │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                     ChatREPL                                  │
│  • Infinite while loop                                        │
│  • Read user input (prompt-toolkit)                           │
│  • Pass to ChatSession.handle_input()                         │
│  • Display response (Rich formatting)                         │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                   ChatSession                                 │
│  • Session state (history, context)                           │
│  • Parse input intent                                         │
│  • Route to ConversationalBrian or CommandRouter              │
│  • Format responses conversationally                          │
└─────────────┬────────────────────────┬───────────────────────┘
              │                        │
       ┌──────▼──────┐         ┌──────▼──────────┐
       │Conversational│         │ CommandRouter   │
       │   Brian      │         │ (existing cmds) │
       └──────┬───────┘         └─────────────────┘
              │
       ┌──────▼────────────────────────────────────┐
       │      BrianOrchestrator                    │
       │  • assess_and_select_workflows()          │
       │  • Learning application                   │
       │  • Workflow adjustment                    │
       └──────┬────────────────────────────────────┘
              │
       ┌──────▼────────────────────────────────────┐
       │    GAODevOrchestrator                     │
       │  • Execute workflows                      │
       │  • Coordinate agents                      │
       │  • Create artifacts                       │
       └───────────────────────────────────────────┘
```

### Component Interaction Flow

**Scenario: User asks to build a feature**

1. **User Input**: Types "I want to add authentication"
2. **ChatREPL**: Captures input, passes to ChatSession
3. **ChatSession**: Parses intent → "feature request"
4. **ConversationalBrian**: Wraps BrianOrchestrator.assess_and_select_workflows()
5. **BrianOrchestrator**: Analyzes prompt, determines Scale Level 2, selects workflows
6. **ConversationalBrian**: Formats analysis conversationally, asks for confirmation
7. **ChatSession**: Presents to user: "This is a Level 2 feature... Proceed?"
8. **User**: Confirms "yes"
9. **CommandRouter**: Routes to GAODevOrchestrator.execute_workflow_sequence()
10. **GAODevOrchestrator**: Executes workflows (create PRD, stories, implementation)
11. **ChatSession**: Streams progress updates conversationally
12. **ChatREPL**: Displays formatted output to terminal
13. **Loop**: Returns to input prompt for next request

---

## Component Design

### 1. ChatREPL (Story 30.1)

**Location**: `gao_dev/cli/chat_repl.py`

**Responsibilities**:
- Infinite while loop for input/output
- Graceful startup and shutdown
- Integrate prompt-toolkit for enhanced REPL (history, autocomplete)
- Rich formatting for beautiful terminal output

**Key Methods**:
```python
class ChatREPL:
    def __init__(self, session: ChatSession):
        self.session = session
        self.prompt_session = PromptSession()

    async def start(self) -> None:
        """Start REPL loop."""
        # Display greeting
        await self._show_greeting()

        # Main loop
        while True:
            try:
                user_input = await self.prompt_session.prompt_async("You: ")

                # Check for exit commands
                if user_input.lower() in ["exit", "quit", "bye"]:
                    await self._show_farewell()
                    break

                # Handle input via session
                async for response in self.session.handle_input(user_input):
                    self._display_response(response)

            except KeyboardInterrupt:
                await self._show_farewell()
                break
            except Exception as e:
                self._display_error(e)

    def _display_response(self, response: str):
        """Display Brian's response with Rich formatting."""
        console.print(Panel(response, title="Brian", border_style="green"))
```

**Dependencies**:
- `prompt-toolkit` for enhanced REPL
- `rich` for terminal formatting (already in use)

---

### 2. ChatSession (Story 30.5)

**Location**: `gao_dev/orchestrator/chat_session.py`

**Responsibilities**:
- Maintain session state (history, context)
- Parse user input and detect intent
- Route to appropriate handler (Brian or commands)
- Format responses conversationally

**Key Methods**:
```python
class ChatSession:
    def __init__(
        self,
        conversational_brian: ConversationalBrian,
        command_router: CommandRouter,
        project_root: Path
    ):
        self.brian = conversational_brian
        self.router = command_router
        self.project_root = project_root
        self.history: List[Turn] = []
        self.context: Dict[str, Any] = {}

    async def handle_input(self, user_input: str) -> AsyncIterator[str]:
        """Handle user input and yield responses."""
        # Add to history
        self.history.append(Turn(role="user", content=user_input))

        # Parse intent
        intent = await self._parse_intent(user_input)

        # Route based on intent
        if intent.type == "feature_request":
            async for response in self.brian.handle_request(user_input, self.context):
                yield response
        elif intent.type == "command":
            async for response in self.router.execute(intent.command, intent.args):
                yield response
        elif intent.type == "question":
            yield await self._handle_question(user_input)
        else:
            yield "I'm not sure I understand. Could you rephrase that?"

    async def _parse_intent(self, user_input: str) -> Intent:
        """Parse user input to detect intent."""
        # Simple pattern matching + keyword detection
        # Future: Could use NLP models
        ...
```

**State Management**:
- `history`: List of conversation turns (user + Brian)
- `context`: Session-scoped context (current epic, story, etc.)
- `preferences`: User preferences (verbosity, confirmation prompts)

---

### 3. ConversationalBrian (Story 30.3)

**Location**: `gao_dev/orchestrator/conversational_brian.py`

**Responsibilities**:
- Wrap BrianOrchestrator for conversational interaction
- Format analysis results as dialogue
- Handle confirmation flows
- Support multi-turn clarifications

**Key Methods**:
```python
class ConversationalBrian:
    def __init__(self, brian_orchestrator: BrianOrchestrator):
        self.brian = brian_orchestrator

    async def handle_request(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> AsyncIterator[str]:
        """Handle feature/project request conversationally."""

        # Phase 1: Acknowledge request
        yield "Let me analyze that..."

        # Phase 2: Analyze with Brian
        analysis = await self.brian.assess_and_select_workflows(user_input)

        # Phase 3: Present analysis conversationally
        yield self._format_analysis(analysis)

        # Phase 4: Ask for confirmation
        yield "Shall I proceed with this plan?"

        # Wait for user response in context
        # (Handled by ChatSession, which will call execute_plan if confirmed)

    def _format_analysis(self, analysis: WorkflowSequence) -> str:
        """Format analysis results as conversational message."""
        return f"""
I've analyzed your request. Here's what I found:

- Scale Level: Level {analysis.scale_level.value} ({analysis.scale_level.name})
- Project Type: {analysis.project_type.value}
- Recommended Approach: {analysis.rationale}

I recommend these workflows:
{self._format_workflows(analysis.workflows)}

This should take approximately {self._estimate_duration(analysis)}.
        """.strip()
```

**Conversational Patterns**:
- Acknowledgment: "Let me analyze that..."
- Analysis: "I've found that this is a Level 2 feature..."
- Recommendation: "I recommend creating a PRD first..."
- Confirmation: "Shall I proceed?"
- Progress: "Creating PRD... Done! Next, I'll..."

---

### 4. ProjectStatusReporter (Story 30.2)

**Location**: `gao_dev/cli/project_status.py`

**Responsibilities**:
- Auto-detect `.gao-dev/` in current/parent directories
- Query project state (epics, stories, commits)
- Format status summary for display
- Detect greenfield projects

**Key Methods**:
```python
class ProjectStatusReporter:
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or self._auto_detect()

    def _auto_detect(self) -> Optional[Path]:
        """Auto-detect project root by searching for .gao-dev/"""
        # Use existing detect_project_root() from Epic 20
        from .project_detection import detect_project_root
        return detect_project_root()

    def get_status(self) -> ProjectStatus:
        """Get comprehensive project status."""
        if not self.project_root:
            return ProjectStatus(exists=False)

        # Load state from FastContextLoader
        context_loader = FastContextLoader(self.project_root / ".gao-dev" / "documents.db")

        return ProjectStatus(
            exists=True,
            project_name=self._get_project_name(),
            epic_count=len(context_loader.get_epics()),
            story_count=len(context_loader.get_stories()),
            recent_commits=self._get_recent_commits(5),
            current_epic=self._get_current_epic(),
            next_actions=self._suggest_next_actions()
        )

    def format_status(self, status: ProjectStatus) -> str:
        """Format status for display in chat."""
        if not status.exists:
            return "No GAO-Dev project detected in this directory."

        return f"""
Project: {status.project_name}
Epics: {status.epic_count} | Stories: {status.story_count}

Recent Activity:
{self._format_commits(status.recent_commits)}

Current Epic: {status.current_epic or "None"}
        """.strip()
```

**Status Information**:
- Project name
- Epic and story counts
- Recent commits (last 5)
- Current epic in progress
- Suggested next actions

---

### 5. CommandRouter (Story 30.4)

**Location**: `gao_dev/cli/command_router.py`

**Responsibilities**:
- Route parsed intents to existing CLI commands
- Wrap command outputs conversationally
- Stream progress updates
- Handle errors gracefully

**Key Methods**:
```python
class CommandRouter:
    def __init__(self, orchestrator: GAODevOrchestrator):
        self.orchestrator = orchestrator

    async def execute(
        self,
        command: str,
        args: Dict[str, Any]
    ) -> AsyncIterator[str]:
        """Execute command and yield conversational responses."""

        # Map command to orchestrator method
        if command == "create_prd":
            yield "Coordinating with John (Product Manager) to create the PRD..."
            async for message in self.orchestrator.create_prd(args["name"]):
                yield message
            yield "PRD complete! Ready for next steps?"

        elif command == "create_story":
            yield f"Coordinating with Bob (Scrum Master) for Story {args['epic']}.{args['story']}..."
            async for message in self.orchestrator.create_story(
                args["epic"], args["story"], args.get("title")
            ):
                yield message
            yield f"Story {args['epic']}.{args['story']} complete!"

        elif command == "implement_story":
            yield f"Amelia is implementing Story {args['epic']}.{args['story']}..."
            async for message in self.orchestrator.implement_story(
                args["epic"], args["story"]
            ):
                yield message
            yield f"Story {args['epic']}.{args['story']} implemented! Tests passing!"

        else:
            yield f"Unknown command: {command}"
```

**Command Mapping**:
- `create_prd` → `orchestrator.create_prd()`
- `create_story` → `orchestrator.create_story()`
- `implement_story` → `orchestrator.implement_story()`
- `ceremony hold` → `orchestrator.hold_ceremony()`
- `learning list` → `learning_service.get_learnings()`

---

### 6. GreenfieldInitializer (Story 30.6)

**Location**: `gao_dev/cli/greenfield_initializer.py`

**Responsibilities**:
- Guide new users through project setup
- Create `.gao-dev/` directory structure
- Initialize git repository
- Create initial documents (README, etc.)

**Key Methods**:
```python
class GreenfieldInitializer:
    def __init__(self, project_root: Path):
        self.project_root = project_root

    async def initialize(self) -> AsyncIterator[str]:
        """Initialize new GAO-Dev project with conversational guidance."""

        yield "Welcome! Let's set up your new GAO-Dev project."
        yield "I'll need to ask a few questions..."

        # Get project name
        project_name = await self._ask("What's your project name?")
        yield f"Great! Creating project: {project_name}"

        # Get project type
        project_type = await self._ask_choice(
            "What type of project?",
            ["Web Application", "CLI Tool", "Library", "Other"]
        )

        # Create structure
        yield "Creating project structure..."
        self._create_gao_dev_directory()
        yield "✓ .gao-dev/ directory created"

        self._initialize_git()
        yield "✓ Git repository initialized"

        self._create_initial_docs(project_name, project_type)
        yield "✓ Initial documentation created"

        yield f"All set! Your project '{project_name}' is ready."
        yield "What would you like to build first?"
```

---

## Data Flow

### Startup Sequence

```
1. User runs: gao-dev start
   ↓
2. ChatREPL.__init__()
   - Create ChatSession
   - Create ConversationalBrian
   - Create CommandRouter
   ↓
3. ProjectStatusReporter.auto_detect()
   - Search for .gao-dev/ in current/parent dirs
   - Load FastContextLoader if found
   ↓
4. ProjectStatusReporter.get_status()
   - Query epics, stories, commits
   - Format status summary
   ↓
5. ChatREPL.start()
   - Display greeting with status
   - Enter input loop
```

**Performance Target**: <2 seconds from command to greeting

---

### Input Processing Flow

```
1. User types: "I want to add authentication"
   ↓
2. ChatSession.handle_input()
   - Add to history
   - Parse intent → feature_request
   ↓
3. ConversationalBrian.handle_request()
   - Acknowledge: "Let me analyze that..."
   ↓
4. BrianOrchestrator.assess_and_select_workflows()
   - AI analysis
   - Learning application
   - Workflow adjustment
   - Returns: WorkflowSequence
   ↓
5. ConversationalBrian._format_analysis()
   - "Level 2 feature..."
   - "I recommend: PRD → Stories → Implementation"
   - "Shall I proceed?"
   ↓
6. ChatSession yields response to ChatREPL
   ↓
7. ChatREPL displays with Rich formatting
   ↓
8. User responds: "yes"
   ↓
9. CommandRouter.execute("create_prd")
   - "Coordinating with John..."
   - orchestrator.create_prd()
   - Streams output
   ↓
10. ChatREPL displays progress in real-time
```

---

## Technology Stack

### Core Dependencies (Existing)

- **Python 3.11+**: Async/await support
- **asyncio**: Asynchronous I/O
- **structlog**: Structured logging
- **rich**: Terminal formatting (already in use)
- **click**: CLI framework (already in use)

### New Dependencies (Epic 30)

- **prompt-toolkit**: Enhanced REPL with history, autocomplete
  - Input history (up/down arrow keys)
  - Tab completion
  - Multi-line editing
  - Syntax highlighting

**Installation**:
```bash
pip install prompt-toolkit
```

**Size**: ~200KB, no heavy dependencies

---

## Integration Points

### 1. Brian Orchestrator (Epic 7.2, 29)

**Interface**: `BrianOrchestrator.assess_and_select_workflows()`

**Integration**:
```python
# ConversationalBrian wraps Brian
conversational_brian = ConversationalBrian(brian_orchestrator)
analysis = await conversational_brian.handle_request(user_input, context)
```

**Data Flow**: User input → Brian analysis → Conversational formatting → User

---

### 2. GAODevOrchestrator (Epic 27)

**Interface**: All existing orchestrator methods

**Integration**:
```python
# CommandRouter uses orchestrator
router = CommandRouter(gao_dev_orchestrator)
async for response in router.execute("create_prd", {"name": "My Feature"}):
    print(response)
```

**Data Flow**: Command intent → Orchestrator method → Streaming output → User

---

### 3. FastContextLoader (Epic 25)

**Interface**: `FastContextLoader.get_epics()`, `get_stories()`, etc.

**Integration**:
```python
# ProjectStatusReporter uses context loader
context_loader = FastContextLoader(db_path)
status = ProjectStatus(
    epic_count=len(context_loader.get_epics()),
    story_count=len(context_loader.get_stories())
)
```

**Data Flow**: Query context → Format status → Display to user

---

### 4. Project Detection (Epic 20)

**Interface**: `detect_project_root()`

**Integration**:
```python
# ProjectStatusReporter auto-detects project
from gao_dev.cli.project_detection import detect_project_root
project_root = detect_project_root() or Path.cwd()
```

**Data Flow**: Search filesystem → Find .gao-dev/ → Return project root

---

## Performance Considerations

### Startup Performance

**Target**: <2 seconds from command to greeting

**Bottlenecks**:
- FastContextLoader initialization: <5ms (cache hit)
- Git operations: ~100ms
- Database queries: <50ms

**Optimization**:
- Lazy load orchestrator components
- Cache project status for session duration
- Async operations for non-blocking I/O

---

### Response Time

**Target**: <1 second for Brian's analysis

**Bottlenecks**:
- AI analysis: ~500ms (deepseek-r1 local) or ~1-2s (Claude API)
- Context loading: <5ms (FastContextLoader)
- Workflow selection: <50ms

**Optimization**:
- Stream analysis results (don't wait for full response)
- Cache workflow registry
- Use local models when possible (Epic 21)

---

### Memory Usage

**Target**: <100MB for REPL session

**Components**:
- REPL history: ~1MB (500 turns × 2KB)
- Session context: <1MB
- Orchestrator: ~20MB
- FastContextLoader cache: <10MB

**Optimization**:
- Limit history to last 100 turns
- Clear context between major operations
- LRU cache for frequently accessed data

---

## Security & Safety

### Input Validation

**Risks**:
- Command injection via user input
- Path traversal attacks
- Malicious file operations

**Mitigations**:
- Sanitize all user input before passing to shell
- Validate file paths (no `..` allowed)
- Use allowlist for commands (not blocklist)
- All file operations via GitIntegratedStateManager (atomic, safe)

---

### Session Isolation

**Risks**:
- Session state leaks between users
- Context pollution across sessions

**Mitigations**:
- Clear session state on exit
- No global mutable state
- Each session creates new ChatSession instance
- Stateless command execution (idempotent)

---

### Error Handling

**Principles**:
- Never crash the REPL (catch all exceptions)
- Always provide helpful error messages
- Suggest remediation steps
- Log errors for debugging

**Example**:
```python
try:
    async for response in self.session.handle_input(user_input):
        self._display_response(response)
except WorkflowNotFoundError as e:
    self._display_error(
        f"Workflow not found: {e.workflow_name}",
        suggestion="Try 'list workflows' to see available workflows"
    )
except Exception as e:
    logger.exception("Unexpected error in REPL")
    self._display_error(
        "Sorry, I encountered an error.",
        suggestion="Please try again or report this issue"
    )
```

---

## Testing Strategy

### Unit Tests

**Coverage Target**: >90% for new code

**Components to Test**:
- `ChatSession.handle_input()` - Intent parsing
- `ConversationalBrian._format_analysis()` - Response formatting
- `ProjectStatusReporter.get_status()` - Status queries
- `CommandRouter.execute()` - Command routing
- `GreenfieldInitializer.initialize()` - Project setup

**Test Framework**: pytest with pytest-asyncio

---

### Integration Tests

**Coverage Target**: 25+ tests

**Scenarios**:
1. New user starts REPL, sees greeting
2. Project detected, status displayed
3. User requests feature, Brian analyzes
4. User confirms, workflows execute
5. User asks question, gets help
6. User types invalid input, gets error with suggestion
7. User exits gracefully (exit command)
8. User exits via Ctrl+C (graceful shutdown)
9. Greenfield project: Initialize new project
10. Multi-turn conversation: Clarifications work

**Test Approach**:
- Mock user input (simulate typing)
- Capture output (Rich console to string)
- Assert conversation flow matches expected

**Example**:
```python
async def test_feature_request_flow():
    """Test full feature request conversation."""
    # Setup
    session = ChatSession(mock_brian, mock_router, project_root)

    # Simulate user input
    responses = []
    async for response in session.handle_input("I want to add auth"):
        responses.append(response)

    # Assert
    assert "Let me analyze" in responses[0]
    assert "Level 2 feature" in responses[1]
    assert "Shall I proceed" in responses[2]
```

---

### Manual QA Scenarios

**Coverage**: 5+ real user scenarios

**Scenarios**:
1. **New Developer**: First time using GAO-Dev, guided through setup
2. **Greenfield App**: Build complete app from scratch in one session
3. **Bug Fix**: Report bug, implement fix, verify in one session
4. **Feature Addition**: Add feature to existing project
5. **Exploration**: Ask questions, explore capabilities, learn system

**QA Checklist**:
- [ ] Startup feels fast (<2s)
- [ ] Greeting is friendly and informative
- [ ] Status summary is accurate
- [ ] Brian's responses feel natural
- [ ] Progress updates stream in real-time
- [ ] Errors are helpful, not cryptic
- [ ] Exit is graceful (no crashes)
- [ ] Session history works (up/down arrows)

---

## Implementation Notes

### Story Order

**Week 1**:
1. Story 30.1 (REPL) - Foundation for everything
2. Story 30.2 (Status) - User needs context
3. Story 30.3 (Brian) - Core conversational experience

**Week 2**:
4. Story 30.4 (Routing) - Execute commands
5. Story 30.5 (Session) - Remember context
6. Story 30.6 (Greenfield) - Help new users
7. Story 30.7 (Testing) - Validate everything

**Rationale**: Build foundation first (I/O loop), add intelligence (Brian), add features (routing, session, init), validate (testing).

---

### Code Locations

```
gao_dev/
├── cli/
│   ├── chat_repl.py           # Story 30.1 - Main REPL loop
│   ├── project_status.py      # Story 30.2 - Project detection
│   ├── command_router.py      # Story 30.4 - Command routing
│   └── greenfield_initializer.py  # Story 30.6 - Project init
│
├── orchestrator/
│   ├── chat_session.py        # Story 30.5 - Session state
│   └── conversational_brian.py  # Story 30.3 - Brian wrapper
│
tests/
├── cli/
│   ├── test_chat_repl.py      # Story 30.7 - REPL tests
│   ├── test_project_status.py # Story 30.7 - Status tests
│   └── test_command_router.py # Story 30.7 - Routing tests
│
└── orchestrator/
    ├── test_chat_session.py   # Story 30.7 - Session tests
    └── test_conversational_brian.py  # Story 30.7 - Brian tests
```

---

## Future Enhancements

### Phase 2: Advanced NLP (Beyond Epic 30)

- Intent classification with ML models (spaCy, transformers)
- Entity extraction (epic numbers, story IDs, dates)
- Sentiment analysis (detect user frustration)
- Contextual autocomplete (predict next command)

### Phase 3: Multi-Modal Interface

- Voice input/output (speech recognition)
- Web-based chat UI (browser interface)
- IDE integration (VSCode, JetBrains)
- Collaborative sessions (multi-user)

### Phase 4: Proactive AI

- Brian suggests next steps without prompting
- Automated daily standups
- Predictive issue detection
- Learning from all GAO-Dev installations (federated learning)

---

## References

- [PRD.md](./PRD.md) - Product requirements
- [Epic 30](./epics/epic-30-interactive-chat.md) - Epic breakdown
- [Brian Orchestrator](../../gao_dev/orchestrator/brian_orchestrator.py) - Existing Brian implementation
- [ConversationManager](../../gao_dev/orchestrator/conversation_manager.py) - Multi-agent dialogue (Epic 26)
- [prompt-toolkit Documentation](https://python-prompt-toolkit.readthedocs.io/) - REPL library
- [Rich Documentation](https://rich.readthedocs.io/) - Terminal formatting

---

**Version**: 1.0
**Status**: Ready for Implementation
**Next Steps**: Create story files and begin Story 30.1

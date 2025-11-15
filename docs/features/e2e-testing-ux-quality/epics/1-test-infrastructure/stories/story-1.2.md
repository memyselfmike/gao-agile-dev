# Story 1.2: Test Mode Support in ChatREPL

**Story ID**: 1.2
**Epic**: 1 - Test Infrastructure
**Feature**: e2e-testing-ux-quality
**Status**: Not Started
**Story Points**: 5
**Priority**: Critical

---

## User Story

**As a** test framework
**I want** `gao-dev start` to support `--test-mode` and `--capture-mode` flags
**So that** I can control Brian's behavior during testing and capture conversations for analysis

---

## Business Value

Without test mode and capture mode support, we cannot:
- Use scripted AI responses for deterministic testing (test mode)
- Capture conversation transcripts for quality analysis (capture mode)
- Test Brian's behavior in a controlled, repeatable way

This story enables:
- Deterministic regression tests (Mode 3)
- Conversation quality analysis (Mode 2)
- Interactive debugging workflows (Mode 1)

---

## Acceptance Criteria

- [ ] **AC1**: ChatREPL accepts `--test-mode` flag and passes to ChatSession
- [ ] **AC2**: ChatREPL accepts `--capture-mode` flag and passes to ChatSession
- [ ] **AC3**: ChatREPL accepts `--fixture <path>` option for fixture file location
- [ ] **AC4**: In test mode, responses loaded from fixture instead of calling AI
- [ ] **AC5**: In capture mode, full conversation logged to `.gao-dev/test_transcripts/`
- [ ] **AC6**: Conversation logs include: timestamp, user input, Brian response, context used
- [ ] **AC7**: Conversation logs persisted to JSON format with session timestamp
- [ ] **AC8**: Test mode and capture mode can be used independently or together
- [ ] **AC9**: No circular dependency between production code (`gao_dev/`) and test code (`tests/`)
- [ ] **AC10**: Graceful fallback if fixture file missing or malformed

---

## Technical Context

### Architecture References

From Architecture document sections 4.1-4.3:

**ChatREPL Modifications**:
- Add `--test-mode`, `--capture-mode`, `--fixture` flags to CLI command
- Initialize AIResponseInjector lazily when test mode enabled
- Pass flags through to ChatSession

**ChatSession Modifications**:
- Add conversation capture in capture mode
- Save transcripts to `.gao-dev/test_transcripts/`
- Include context metadata in captured turns

**Circular Dependency Prevention**:
- Production code NEVER imports test code at module level
- Use lazy conditional imports inside test mode blocks
- Graceful fallback if test modules unavailable

### Implementation Details

**CLI Command Update** (`gao_dev/cli/commands.py`):
```python
@cli.command("start")
@click.option("--project", type=Path, help="Project root (default: auto-detect)")
@click.option("--test-mode", is_flag=True, help="Enable test mode with fixture responses")
@click.option("--capture-mode", is_flag=True, help="Enable conversation capture logging")
@click.option("--fixture", type=Path, help="Fixture file for test mode")
def start_chat(
    project: Optional[Path],
    test_mode: bool,
    capture_mode: bool,
    fixture: Optional[Path]
):
    """Start interactive chat with Brian."""
    from .chat_repl import ChatREPL

    # Validate fixture exists if test mode enabled
    if test_mode and fixture and not fixture.exists():
        click.echo(f"[ERROR] Fixture file not found: {fixture}", err=True)
        sys.exit(1)

    # Create REPL with test flags
    repl = ChatREPL(
        project_root=project,
        test_mode=test_mode,
        capture_mode=capture_mode,
        fixture_path=fixture
    )

    # Start async loop
    try:
        asyncio.run(repl.start())
    except Exception as e:
        click.echo(f"[ERROR] Failed to start REPL: {e}", err=True)
        sys.exit(1)
```

**ChatREPL Update** (`gao_dev/cli/chat_repl.py`):
```python
class ChatREPL:
    def __init__(
        self,
        project_root: Optional[Path] = None,
        test_mode: bool = False,
        capture_mode: bool = False,
        fixture_path: Optional[Path] = None
    ):
        self.project_root = project_root or Path.cwd()
        self.test_mode = test_mode
        self.capture_mode = capture_mode
        self.fixture_path = fixture_path

        # Lazy import to avoid circular dependency
        self.ai_injector = None
        if self.test_mode and self.fixture_path:
            try:
                # Import only when test mode is active
                from tests.e2e.harness.ai_response_injector import AIResponseInjector
                self.ai_injector = AIResponseInjector(self.fixture_path)
            except ImportError:
                # Graceful fallback - production code works without tests module
                logger.warning("Test mode enabled but tests module not available")
                pass

        # ... existing initialization ...

        # Create ChatSession with flags
        self.session = ChatSession(
            conversational_brian=self.brian,
            command_router=self.command_router,
            project_root=self.project_root,
            capture_mode=self.capture_mode,
            ai_injector=self.ai_injector  # Pass injector to session
        )
```

**ChatSession Update** (`gao_dev/orchestrator/chat_session.py`):
```python
class ChatSession:
    def __init__(
        self,
        conversational_brian,
        command_router,
        project_root: Path,
        capture_mode: bool = False,
        ai_injector=None  # Optional test mode injector
    ):
        self.conversational_brian = conversational_brian
        self.command_router = command_router
        self.project_root = project_root
        self.capture_mode = capture_mode
        self.ai_injector = ai_injector
        self.conversation_transcript = []

        if self.capture_mode:
            self.transcript_path = self._init_transcript()

    async def handle_input(self, user_input: str) -> str:
        """Handle user input with optional capture."""
        # Capture turn start
        if self.capture_mode:
            turn = {
                "timestamp": datetime.now().isoformat(),
                "user_input": user_input,
                "brian_response": None,
                "context_used": self._get_active_context(),
            }

        # Get Brian's response (from fixture or AI)
        if self.ai_injector:
            response = self.ai_injector.get_next_response()
        else:
            response = await self.conversational_brian.handle_message(user_input)

        # Capture turn end
        if self.capture_mode:
            turn["brian_response"] = response
            self.conversation_transcript.append(turn)
            self._save_transcript()

        return response

    def _init_transcript(self) -> Path:
        """Initialize transcript file."""
        gao_dev_dir = self.project_root / ".gao-dev" / "test_transcripts"
        gao_dev_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return gao_dev_dir / f"session_{timestamp}.json"

    def _save_transcript(self):
        """Save transcript to disk."""
        with open(self.transcript_path, 'w') as f:
            json.dump(self.conversation_transcript, f, indent=2)

    def _get_active_context(self) -> dict:
        """Get current context for conversation turn."""
        return {
            "project_root": str(self.project_root),
            "session_id": id(self),
            # Add more context as needed
        }
```

### Dependencies

- **Depends On**: Story 1.1 (provider configuration)
- **Blocks**: Story 1.3 (ChatHarness needs test mode flags)
- Epic 30: ChatREPL and ChatSession implementations
- click library for CLI options

---

## Test Scenarios

### Test 1: Test Mode Flag Parsing
```python
def test_start_command_accepts_test_mode_flag():
    """Test CLI accepts --test-mode flag."""
    runner = CliRunner()
    result = runner.invoke(start_chat, ["--test-mode", "--fixture", "test.yaml"])

    # Should parse successfully (may fail on execution if fixture missing)
    assert "--test-mode" in result.output or result.exit_code in [0, 1]
```

### Test 2: Capture Mode Creates Transcript
```python
def test_capture_mode_creates_transcript(tmp_path):
    """Test capture mode creates transcript file."""
    project_root = tmp_path / "test-project"
    project_root.mkdir()

    session = ChatSession(
        conversational_brian=MockBrian(),
        command_router=MockRouter(),
        project_root=project_root,
        capture_mode=True
    )

    # Simulate conversation
    await session.handle_input("Hello")

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
        assert "timestamp" in data[0]
        assert "brian_response" in data[0]
```

### Test 3: Test Mode Uses Fixture Responses
```python
def test_test_mode_uses_fixture_responses(tmp_path):
    """Test that test mode loads responses from fixture."""
    # Create mock fixture
    fixture_path = tmp_path / "test.yaml"
    fixture_path.write_text("""
name: "simple_test"
description: "Test fixture"
scenario:
  - user_input: "hello"
    brian_response: "Hello! How can I help?"
""")

    # Create AIResponseInjector
    from tests.e2e.harness.ai_response_injector import AIResponseInjector
    injector = AIResponseInjector(fixture_path)

    # Create session with injector
    session = ChatSession(
        conversational_brian=MockBrian(),  # Won't be called
        command_router=MockRouter(),
        project_root=tmp_path,
        ai_injector=injector
    )

    response = await session.handle_input("hello")

    assert response == "Hello! How can I help?"
```

### Test 4: No Circular Dependency
```python
def test_no_circular_dependency():
    """Test production code works without tests module."""
    # Temporarily remove tests from sys.modules
    import sys
    tests_modules = [m for m in sys.modules if m.startswith('tests')]

    for mod in tests_modules:
        del sys.modules[mod]

    # ChatREPL should still initialize (without test mode)
    from gao_dev.cli.chat_repl import ChatREPL

    repl = ChatREPL(test_mode=False)
    assert repl.ai_injector is None  # Should be None, not import error
```

---

## Definition of Done

- [ ] CLI flags implemented and tested
- [ ] ChatREPL modifications complete
- [ ] ChatSession modifications complete
- [ ] Conversation capture working and tested
- [ ] Test mode response injection working
- [ ] No circular dependencies verified
- [ ] Unit tests passing (4+ tests)
- [ ] Integration test with real ChatREPL passing
- [ ] Code reviewed and approved
- [ ] Documentation updated (CLI help, README)

---

## Implementation Notes

### Files to Create/Modify

**Modified Files**:
- `gao_dev/cli/commands.py` - Add flags to start command
- `gao_dev/cli/chat_repl.py` - Accept flags, lazy import injector
- `gao_dev/orchestrator/chat_session.py` - Add capture and injection logic

**New Files**:
- `tests/e2e/harness/ai_response_injector.py` - Response injection (created in Story 1.4)

### Transcript Format

```json
[
  {
    "timestamp": "2025-11-15T09:30:45.123456",
    "user_input": "I want to build a todo app",
    "brian_response": "I'll help you create a todo app...",
    "context_used": {
      "project_root": "/path/to/project",
      "session_id": 12345
    }
  },
  {
    "timestamp": "2025-11-15T09:31:12.789012",
    "user_input": "yes",
    "brian_response": "Great! Initializing...",
    "context_used": {
      "project_root": "/path/to/project",
      "session_id": 12345
    }
  }
]
```

### Directory Structure

```
.gao-dev/
└── test_transcripts/          # Gitignored
    ├── session_2025-11-15_09-30-45.json
    ├── session_2025-11-15_10-15-20.json
    └── .gitignore
```

Add to `.gitignore`:
```
.gao-dev/test_transcripts/
```

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Circular dependency breaks production build | Medium | High | Lazy imports, graceful fallback, unit tests |
| Fixture file malformed crashes REPL | Medium | Medium | Validation in FixtureLoader, try-except blocks |
| Transcripts fill disk space | Low | Medium | Document cleanup strategy, add auto-cleanup |
| Context capture exposes sensitive data | Low | High | Document privacy implications, gitignore transcripts |

---

## Related Stories

- **Depends On**: Story 1.1 (provider configuration)
- **Blocks**: Story 1.3 (ChatHarness), Story 1.4 (FixtureLoader)
- **Related**: Story 2.2 (Conversation Instrumentation - uses capture mode)

---

## References

- PRD Section: FR2 (Test Modes)
- Architecture Section: 4. Integration with ChatREPL
- Architecture Section: Dependency Management - Circular Dependency Prevention
- CRAAP Review: Priority Issue #2 (Resolve Circular Dependency)

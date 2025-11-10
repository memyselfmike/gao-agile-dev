# Story 30.1: Brian REPL Command

**Epic**: Epic 30 - Interactive Brian Chat Interface
**Story ID**: 30.1
**Priority**: P0 (Critical - Foundation)
**Estimate**: 5 story points
**Duration**: 1-2 days
**Owner**: Amelia (Developer)
**Status**: Todo
**Dependencies**: None

---

## Story Description

Create `gao-dev start` command that launches an interactive REPL (Read-Eval-Print Loop) where users can have ongoing conversations with Brian until they choose to exit.

This is the **foundation story** for Epic 30. All other stories build on this REPL infrastructure.

---

## User Story

**As a** developer
**I want** to run `gao-dev start` and enter interactive mode with Brian
**So that** I can have conversational dialogue instead of running one-shot commands

---

## Acceptance Criteria

### Core REPL Functionality
- [ ] `gao-dev start` command exists in CLI
- [ ] Command launches interactive REPL successfully
- [ ] Infinite while loop accepts user input
- [ ] Uses `prompt-toolkit` for enhanced input (history, arrow keys)
- [ ] Uses `rich` for beautiful formatted output
- [ ] REPL never crashes (all exceptions caught)
- [ ] Basic greeting message displayed on startup

### Exit Handling (Critical 4)
- [ ] Exit commands work: `exit`, `quit`, `bye`, `goodbye`
- [ ] Confirmation required if operation in progress (integrated in Story 30.5)
- [ ] Immediate exit when idle (no confirmation)
- [ ] Ctrl+C (KeyboardInterrupt) exits gracefully
- [ ] Ctrl+C during operation: cancels operation, asks "Exit or continue?"
- [ ] Signal handlers setup properly (SIGINT)
- [ ] Farewell message with session summary (duration, operations, artifacts, cost)
- [ ] Bottom toolbar shows current status and exit hint

### Cleanup on Exit
- [ ] Session state saved on exit (integrated with Story 30.5)
- [ ] Database connections closed properly
- [ ] Cache cleared
- [ ] No orphaned processes

### Testing
- [ ] 8+ unit tests for REPL mechanics
- [ ] Integration tests for exit during operation
- [ ] Manual QA: Exit during PRD creation, verify cleanup
- [ ] Manual QA: Ctrl+C during story implementation, verify state preserved

---

## Files to Create/Modify

### New Files
- `gao_dev/cli/chat_repl.py` (~200 LOC)
  - `ChatREPL` class with infinite loop
  - Startup, shutdown, and error handling
  - Rich formatting for beautiful output

- `tests/cli/test_chat_repl.py` (~150 LOC)
  - Tests for REPL loop mechanics
  - Tests for exit commands
  - Tests for error handling
  - Tests for greeting and farewell

### Modified Files
- `gao_dev/cli/commands.py` (~20 LOC added)
  - Add `start` command that launches ChatREPL

---

## Technical Design

### ChatREPL Class

**Location**: `gao_dev/cli/chat_repl.py`

```python
"""Interactive REPL for conversational chat with Brian."""

from typing import Optional
from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
import asyncio
import structlog

logger = structlog.get_logger()


class ChatREPL:
    """
    Interactive REPL for conversational chat with Brian.

    Provides infinite while loop for user input, Rich formatting for
    beautiful output, and graceful exit handling.

    Attributes:
        console: Rich Console for formatted output
        prompt_session: Prompt-toolkit session for enhanced input
        history: In-memory history for arrow key navigation
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize ChatREPL.

        Args:
            project_root: Optional project root (for future session integration)
        """
        self.project_root = project_root or Path.cwd()
        self.console = Console()
        self.history = InMemoryHistory()
        self.prompt_session = PromptSession(history=self.history)
        self.logger = logger.bind(component="chat_repl")

    async def start(self) -> None:
        """
        Start interactive REPL loop.

        Displays greeting, enters infinite loop accepting user input,
        handles exit commands and Ctrl+C gracefully.
        """
        self.logger.info("chat_repl_starting")

        # Display greeting
        await self._show_greeting()

        # Main loop
        while True:
            try:
                # Get user input (async)
                user_input = await self.prompt_session.prompt_async(
                    "You: ",
                    multiline=False
                )

                # Strip whitespace
                user_input = user_input.strip()

                # Check for exit commands
                if self._is_exit_command(user_input):
                    await self._show_farewell()
                    break

                # Handle empty input
                if not user_input:
                    continue

                # Echo input (for now - will be replaced by actual handling in Story 30.3)
                await self._handle_input(user_input)

            except KeyboardInterrupt:
                # Ctrl+C pressed
                self.logger.info("keyboard_interrupt")
                await self._show_farewell()
                break

            except EOFError:
                # Ctrl+D pressed
                self.logger.info("eof_received")
                await self._show_farewell()
                break

            except Exception as e:
                # Catch all other exceptions (never crash)
                self.logger.exception("repl_error", error=str(e))
                self._display_error(e)

        self.logger.info("chat_repl_stopped")

    async def _show_greeting(self) -> None:
        """Display welcome greeting."""
        greeting = """
# Welcome to GAO-Dev!

I'm Brian, your AI Engineering Manager.
Type your requests in natural language, or type 'help' for available commands.
Type 'exit', 'quit', or 'bye' to end the session.
        """.strip()

        self.console.print()
        self.console.print(Panel(
            Markdown(greeting),
            title="[bold green]Brian[/bold green]",
            border_style="green"
        ))
        self.console.print()

    async def _show_farewell(self) -> None:
        """Display farewell message."""
        farewell = "Goodbye! Great work today. See you next time!"

        self.console.print()
        self.console.print(Panel(
            farewell,
            title="[bold green]Brian[/bold green]",
            border_style="green"
        ))
        self.console.print()

    def _is_exit_command(self, user_input: str) -> bool:
        """Check if input is an exit command."""
        return user_input.lower() in ["exit", "quit", "bye", "goodbye"]

    async def _handle_input(self, user_input: str) -> None:
        """
        Handle user input (placeholder for Story 30.3).

        For Story 30.1, just echo back the input.
        Will be replaced with actual conversation handling in Story 30.3.
        """
        response = f"You said: {user_input}"
        self._display_response(response)

    def _display_response(self, response: str) -> None:
        """Display Brian's response with Rich formatting."""
        self.console.print(Panel(
            response,
            title="[bold green]Brian[/bold green]",
            border_style="green"
        ))

    def _display_error(self, error: Exception) -> None:
        """Display error message with helpful suggestion."""
        error_msg = f"[red]Error:[/red] {str(error)}"
        suggestion = "Please try again or type 'help' for assistance."

        self.console.print()
        self.console.print(Panel(
            f"{error_msg}\n\n{suggestion}",
            title="[bold red]Error[/bold red]",
            border_style="red"
        ))
        self.console.print()
```

### CLI Command Integration

**Location**: `gao_dev/cli/commands.py`

```python
@cli.command("start")
@click.option("--project", type=Path, help="Project root (default: auto-detect)")
def start_chat(project: Optional[Path]):
    """Start interactive chat with Brian."""
    from .chat_repl import ChatREPL

    # Create REPL
    repl = ChatREPL(project_root=project)

    # Start async loop
    try:
        asyncio.run(repl.start())
    except Exception as e:
        click.echo(f"[ERROR] Failed to start REPL: {e}", err=True)
        sys.exit(1)
```

---

## Testing Strategy

### Unit Tests

**Location**: `tests/cli/test_chat_repl.py`

**Test Cases**:

1. **test_repl_initialization**
   - ChatREPL initializes successfully
   - Console and prompt_session created
   - History initialized

2. **test_greeting_displayed**
   - Greeting message contains "Welcome to GAO-Dev"
   - Greeting mentions Brian
   - Greeting shows exit commands

3. **test_exit_command_exit**
   - User types "exit" → REPL exits gracefully
   - Farewell message displayed

4. **test_exit_command_quit**
   - User types "quit" → REPL exits gracefully

5. **test_exit_command_bye**
   - User types "bye" → REPL exits gracefully

6. **test_ctrl_c_exit**
   - KeyboardInterrupt → REPL exits gracefully
   - Farewell message displayed

7. **test_empty_input_ignored**
   - User presses Enter (empty input) → No crash
   - REPL continues to accept input

8. **test_exception_handling**
   - Exception during input handling → Error displayed
   - REPL does NOT crash, continues running

9. **test_echo_input** (placeholder for Story 30.3)
   - User types "hello" → Echoed back
   - Will be replaced with real conversation handling

**Example Test**:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from gao_dev.cli.chat_repl import ChatREPL


@pytest.mark.asyncio
async def test_exit_command_exit(tmp_path):
    """Test that 'exit' command exits REPL gracefully."""
    repl = ChatREPL(project_root=tmp_path)

    # Mock prompt_session to return "exit"
    repl.prompt_session.prompt_async = AsyncMock(return_value="exit")

    # Mock greeting and farewell to avoid output
    repl._show_greeting = AsyncMock()
    repl._show_farewell = AsyncMock()

    # Start REPL (should exit immediately)
    await repl.start()

    # Assert farewell was called
    repl._show_farewell.assert_called_once()


@pytest.mark.asyncio
async def test_ctrl_c_exit(tmp_path):
    """Test that Ctrl+C exits REPL gracefully."""
    repl = ChatREPL(project_root=tmp_path)

    # Mock prompt_session to raise KeyboardInterrupt
    repl.prompt_session.prompt_async = AsyncMock(side_effect=KeyboardInterrupt())

    # Mock greeting and farewell
    repl._show_greeting = AsyncMock()
    repl._show_farewell = AsyncMock()

    # Start REPL (should handle Ctrl+C)
    await repl.start()

    # Assert farewell was called
    repl._show_farewell.assert_called_once()
```

---

## Definition of Done

- [ ] Code written and follows GAO-Dev standards (DRY, SOLID, typed)
- [ ] 8+ unit tests written and passing
- [ ] Manual testing: REPL starts, accepts input, exits gracefully
- [ ] Code review completed
- [ ] Git commit: `feat(epic-30): Story 30.1 - Brian REPL Command (5 pts)`
- [ ] Documentation updated (inline docstrings)

---

## Dependencies

### Python Libraries

**New Dependency**:
- `prompt-toolkit` - Enhanced REPL with history and autocomplete
  ```bash
  pip install prompt-toolkit
  ```

**Existing Dependencies**:
- `rich` - Terminal formatting (already in use)
- `click` - CLI framework (already in use)
- `asyncio` - Async/await support (stdlib)

### Update requirements.txt

Add to `requirements.txt`:
```
prompt-toolkit>=3.0.43
```

---

## Implementation Notes

### Prompt-Toolkit Features to Use

**Story 30.1 (This Story)**:
- `PromptSession` - Basic enhanced input
- `InMemoryHistory` - Arrow key navigation (up/down)
- `prompt_async` - Async input handling

**Future Stories**:
- Autocomplete (Story 30.4) - Tab completion for commands
- Multi-line input (Future) - For longer prompts
- Syntax highlighting (Future) - Color-coded input

### Rich Formatting Patterns

**Greeting/Farewell**:
- Use `Panel` with title="Brian" and green border
- Markdown for formatted text

**Responses**:
- Panel with green border for Brian's messages
- Panel with red border for errors
- Plain console.print for progress updates

### Error Handling Philosophy

**Never crash the REPL**:
- Catch ALL exceptions in main loop
- Display helpful error messages
- Suggest remediation ("try again", "type help")
- Log errors for debugging

---

## Manual Testing Checklist

- [ ] Run `gao-dev start` - REPL launches successfully
- [ ] See greeting message with Brian's introduction
- [ ] Type "hello" - Echoed back (placeholder)
- [ ] Type "exit" - Farewell message, REPL exits
- [ ] Type "quit" - Farewell message, REPL exits
- [ ] Type "bye" - Farewell message, REPL exits
- [ ] Press Ctrl+C - Farewell message, REPL exits gracefully
- [ ] Press Enter (empty input) - No crash, continues
- [ ] Type multiple inputs - Up arrow recalls history
- [ ] All formatting looks beautiful (Rich panels)

---

## Next Steps

After Story 30.1 is complete:

**Story 30.2**: Add project auto-detection and status display to greeting
**Story 30.5**: Add ChatSession for state management (parallel with 30.2)
**Story 30.3**: Replace echo with actual Brian conversation handling

---

**Created**: 2025-11-10
**Status**: Ready to Implement

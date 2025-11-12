# Story 35.4: InteractivePrompter Implementation

**Epic**: Epic 35 - Interactive Provider Selection at Startup
**Story ID**: 35.4
**Story Points**: 8
**Owner**: Amelia (Software Developer)
**Dependencies**: Story 35.1
**Priority**: P0
**Status**: Todo

---

## Description

Implement `InteractivePrompter` class for user interaction using Rich and prompt_toolkit, providing beautiful formatted tables and clear prompts for provider and model selection. **Includes lazy import pattern for CI/CD compatibility**.

This story focuses on:
- Rich-formatted tables and panels for beautiful UI
- prompt_toolkit for interactive input with history
- **Lazy import pattern for headless CI/CD environments**
- OpenCode-specific configuration prompts
- Input validation and error handling
- Comprehensive test coverage (>85%)

---

## Acceptance Criteria

- [ ] `InteractivePrompter` class fully implemented in `gao_dev/cli/interactive_prompter.py`:
  - [ ] `prompt_provider()` - shows provider table, gets selection
  - [ ] `prompt_opencode_config()` - OpenCode-specific prompts (local vs cloud)
  - [ ] `prompt_model()` - shows model table, gets selection
  - [ ] `prompt_save_preferences()` - asks about saving preferences
  - [ ] `prompt_use_saved()` - asks about using saved config
  - [ ] `show_error()` - displays error panel with suggestions
  - [ ] `show_success()` - displays success message
  - [ ] `_get_user_input()` - internal method with lazy import
- [ ] **CI/CD Compatibility: Lazy import pattern** (CRAAP Critical Resolution):
  - [ ] Import `prompt_toolkit` and `rich.prompt` **lazily inside methods**, not at module level
  - [ ] Catch `ImportError` (library missing) and `OSError` (no TTY) gracefully
  - [ ] Fallback to standard `input()` function in headless environments
  - [ ] Example pattern:
    ```python
    def prompt_provider(self):
        try:
            from prompt_toolkit import PromptSession
            # Use PromptSession for interactive input
        except (ImportError, OSError):
            # Fallback to input() for CI/CD
            return input("Select provider [1/2/3]: ")
    ```
  - [ ] Apply to all interactive methods
  - [ ] Log when using fallback mode
- [ ] Rich formatting:
  - [ ] Tables with styled columns (cyan headers, green data, borders)
  - [ ] Panels for errors (red) and success (green)
  - [ ] Clear descriptions for each option
  - [ ] Proper line wrapping for long text
  - [ ] Use `Console(legacy_windows=True)` for Windows CMD compatibility
- [ ] Input validation:
  - [ ] Only accept valid choices (1/2/3 for providers, etc.)
  - [ ] Handle invalid input gracefully (re-prompt with error)
  - [ ] Default values provided (press Enter for default)
  - [ ] Show default in prompt: "Select [1/2/3] (default: 1):"
- [ ] Keyboard shortcuts:
  - [ ] Enter → accept default
  - [ ] Ctrl+C → cancel (raises KeyboardInterrupt, not caught)
  - [ ] Arrow keys → navigate history (prompt_toolkit feature)
  - [ ] Tab → autocomplete (if applicable)
- [ ] OpenCode-specific flow:
  - [ ] "Use local model (Ollama)?" [y/N]
  - [ ] If no: "Cloud AI provider?" [anthropic/openai/google]
  - [ ] If yes: Continue to Ollama model selection
  - [ ] Show clear descriptions of each choice
- [ ] Model selection enhancements:
  - [ ] Show model descriptions/sizes if available
  - [ ] Highlight recommended models (bold, green)
  - [ ] Group models by provider if multiple sources
  - [ ] Pagination for >10 models (show 10, then "Show more?")
- [ ] Error display with suggestions:
  - [ ] Error panel in red with title
  - [ ] Bullet-pointed suggestions
  - [ ] "Try again?" prompt after error
  - [ ] Clear, actionable language
- [ ] Comprehensive test coverage (>85%):
  - [ ] Mock Rich Console output
  - [ ] Mock prompt_toolkit PromptSession
  - [ ] Mock user input (simulate typing)
  - [ ] Test all prompt paths
  - [ ] Test error handling
  - [ ] **Test lazy import fallback** (simulate headless environment)
  - [ ] Test invalid input re-prompting
  - [ ] Test Ctrl+C handling (should propagate KeyboardInterrupt)
- [ ] Type hints throughout, MyPy passes strict mode

---

## Tasks

- [ ] Implement provider prompt with Rich table
  - [ ] Create table with columns: Option, Provider, Description
  - [ ] Add rows for claude-code, opencode, direct-api
  - [ ] Use Rich colors (cyan headers, green text)
  - [ ] Get user input with validation
- [ ] Implement model prompt with Rich table
  - [ ] Create table with columns: Option, Model, Size, Description
  - [ ] Highlight recommended models
  - [ ] Handle pagination for >10 models
  - [ ] Get user input with validation
- [ ] Implement OpenCode-specific prompts
  - [ ] "Use local?" prompt (y/N)
  - [ ] "Cloud provider?" prompt if not local
  - [ ] Show clear explanations
- [ ] Implement error/success displays
  - [ ] Error panel with red border
  - [ ] Success panel with green border
  - [ ] Format suggestions as bullet list
- [ ] **Implement lazy import pattern** (CRAAP Critical)
  - [ ] Move all `import prompt_toolkit` inside methods
  - [ ] Wrap in try/except for ImportError and OSError
  - [ ] Implement fallback to `input()` function
  - [ ] Log when using fallback: "Running in headless mode, using basic input"
  - [ ] Test in Docker container without TTY
- [ ] Add input validation
  - [ ] Validate choice is in allowed range
  - [ ] Re-prompt on invalid input with error message
  - [ ] Show default value clearly
  - [ ] Allow Enter for default
- [ ] **Enable Windows compatibility** (CRAAP Moderate)
  - [ ] Use `Console(legacy_windows=True)` for CMD support
  - [ ] Test in Windows CMD, PowerShell, Git Bash
  - [ ] Handle ANSI color codes properly
- [ ] Write 25+ unit tests
  - [ ] Mock Console.print() calls
  - [ ] Mock PromptSession input
  - [ ] Test valid/invalid inputs
  - [ ] Test defaults
  - [ ] Test Ctrl+C handling
  - [ ] **Test lazy import fallback** (mock ImportError)
  - [ ] **Test no-TTY environment** (mock OSError)
- [ ] Add integration tests with mocked input
  - [ ] Full provider selection flow
  - [ ] Full model selection flow
  - [ ] Error recovery flow
- [ ] Test keyboard shortcuts
  - [ ] Enter for default
  - [ ] Ctrl+C propagation
- [ ] Run MyPy and fix issues
  - [ ] `mypy gao_dev/cli/interactive_prompter.py --strict`

---

## Test Cases

```python
# Provider prompts
def test_prompt_provider_valid_choice():
    """Valid provider choice returns provider name."""
    # Mock PromptSession to return '1'
    # Call prompt_provider()
    # Assert returns 'claude-code'

def test_prompt_provider_invalid_then_valid():
    """Invalid choice re-prompts, then accepts valid."""
    # Mock PromptSession to return '5' then '2'
    # Call prompt_provider()
    # Assert re-prompted once
    # Assert returns 'opencode'

def test_prompt_provider_default():
    """Empty input uses default (1)."""
    # Mock PromptSession to return ''
    # Call prompt_provider()
    # Assert returns 'claude-code' (default)

def test_prompt_provider_ctrl_c():
    """Ctrl+C raises KeyboardInterrupt."""
    # Mock PromptSession to raise KeyboardInterrupt
    # Call prompt_provider()
    # Assert KeyboardInterrupt propagates

# OpenCode prompts
def test_prompt_opencode_local():
    """OpenCode local model config returned."""
    # Mock PromptSession to return 'y'
    # Call prompt_opencode_config()
    # Assert returns {'use_local': True}

def test_prompt_opencode_cloud():
    """OpenCode cloud config returned."""
    # Mock PromptSession to return 'n' then 'anthropic'
    # Call prompt_opencode_config()
    # Assert returns {'use_local': False, 'ai_provider': 'anthropic'}

# Model prompts
def test_prompt_model_valid():
    """Valid model choice returns model name."""
    # Mock PromptSession to return '1'
    # Call prompt_model(['deepseek-r1', 'llama2'])
    # Assert returns 'deepseek-r1'

def test_prompt_model_pagination():
    """Pagination works for >10 models."""
    # Mock PromptSession with 15 models
    # Call prompt_model()
    # Assert shows first 10
    # Assert prompts "Show more?"

# Save preferences
def test_prompt_save_yes():
    """'y' returns True."""
    # Mock PromptSession to return 'y'
    # Call prompt_save_preferences()
    # Assert returns True

def test_prompt_save_no():
    """'n' returns False."""
    # Mock PromptSession to return 'n'
    # Call prompt_save_preferences()
    # Assert returns False

# Use saved preferences
def test_prompt_use_saved_yes():
    """'Y' returns 'y'."""
    # Mock PromptSession to return 'Y'
    # Call prompt_use_saved()
    # Assert returns 'y'

def test_prompt_use_saved_change():
    """'c' returns 'c'."""
    # Mock PromptSession to return 'c'
    # Call prompt_use_saved()
    # Assert returns 'c'

# Error/Success display
def test_show_error():
    """Error panel displayed with suggestions."""
    # Mock Console.print()
    # Call show_error("Test error", ["Suggestion 1"])
    # Assert Panel created with red style
    # Assert suggestions formatted as bullets

def test_show_success():
    """Success message displayed."""
    # Mock Console.print()
    # Call show_success("Test success")
    # Assert Panel created with green style

# Lazy import fallback (CRAAP Critical)
def test_fallback_to_input_on_import_error():
    """Falls back to input() when prompt_toolkit unavailable."""
    # Mock ImportError on 'from prompt_toolkit import PromptSession'
    # Mock input() to return '1'
    # Call prompt_provider()
    # Assert returns 'claude-code'
    # Assert warning logged about fallback mode

def test_fallback_to_input_on_no_tty():
    """Falls back to input() when no TTY available."""
    # Mock OSError on PromptSession() creation
    # Mock input() to return '2'
    # Call prompt_provider()
    # Assert returns 'opencode'
    # Assert warning logged about headless mode

def test_fallback_input_validation():
    """Fallback input() still validates choices."""
    # Mock input() to return '9' then '1'
    # Call prompt_provider()
    # Assert re-prompted
    # Assert returns 'claude-code'

# Windows compatibility
def test_windows_console_compatibility():
    """Rich Console works on Windows CMD."""
    # Mock platform.system() to return 'Windows'
    # Create Console with legacy_windows=True
    # Call prompt_provider()
    # Assert no ANSI errors
```

---

## Definition of Done

- [ ] All methods implemented and working
- [ ] Lazy import pattern implemented (CRAAP resolution)
- [ ] Windows compatibility enabled (legacy_windows=True)
- [ ] 25+ tests passing, >85% coverage
- [ ] Headless environment test passes (Docker, no TTY)
- [ ] Manual testing of UI (screenshots/recordings)
- [ ] MyPy passes strict mode
- [ ] Documentation complete (docstrings)
- [ ] Code reviewed
- [ ] Commit message: `feat(epic-35): Story 35.4 - InteractivePrompter Implementation (8 pts)`

---

## Notes

### CRAAP Resolutions Incorporated

**Lazy Import Pattern for CI/CD (CRAAP Critical - Issue #1)**:
- **Risk**: `prompt_toolkit` import fails in headless Docker containers
- **Impact**: CI/CD pipelines break, even with AGENT_PROVIDER env var set
- **Mitigation**:
  ```python
  def prompt_provider(self) -> str:
      try:
          from prompt_toolkit import PromptSession
          from rich.prompt import Prompt
          # Use interactive tools
          session = PromptSession()
          choice = session.prompt("Select provider: ")
      except (ImportError, OSError):
          # Fallback for headless environments
          logger.warning("Running in headless mode, using basic input")
          choice = input("Select provider [1/2/3]: ")
      return self._validate_choice(choice)
  ```
- **Testing**: Docker test without TTY, mock ImportError/OSError

**Windows CMD Compatibility (CRAAP Moderate - Issue #4)**:
- **Risk**: Rich ANSI codes broken in Windows CMD
- **Mitigation**:
  ```python
  from rich.console import Console
  console = Console(
      legacy_windows=True,  # Enable Windows compatibility
      force_terminal=None,  # Auto-detect
  )
  ```
- **Testing**: Manual testing on Windows CMD, PowerShell, Git Bash

### Rich Table Example

```python
from rich.table import Table
from rich.console import Console

def prompt_provider(self) -> str:
    console = Console(legacy_windows=True)

    table = Table(title="Available AI Providers", border_style="cyan")
    table.add_column("Option", style="cyan", justify="center")
    table.add_column("Provider", style="green")
    table.add_column("Description", style="white")

    table.add_row("1", "claude-code", "Claude Code CLI (Anthropic)")
    table.add_row("2", "opencode", "OpenCode CLI (Multi-provider)")
    table.add_row("3", "direct-api", "Direct Anthropic API")

    console.print(table)

    # Get input with lazy import fallback...
```

### Input Validation Pattern

```python
def _validate_provider_choice(self, choice: str) -> str:
    """Validate and convert provider choice to provider name."""
    choice = choice.strip().lower()

    if choice == '' or choice == '1':
        return 'claude-code'  # Default
    elif choice == '2':
        return 'opencode'
    elif choice == '3':
        return 'direct-api-anthropic'
    else:
        raise ValueError(f"Invalid choice: {choice}. Choose 1, 2, or 3.")
```

### Error Handling Flow

```python
def prompt_provider(self) -> str:
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            choice = self._get_user_input("Select provider [1/2/3]: ")
            return self._validate_provider_choice(choice)
        except ValueError as e:
            if attempt < max_attempts - 1:
                self.show_error(str(e), [])
            else:
                raise ProviderSelectionError("Too many invalid attempts")
```

### Performance Considerations

- Rendering Rich tables: <10ms
- Getting user input: synchronous, waits for user
- Validation: <1ms
- Overall: Limited by user typing speed

### Dependencies for Next Stories

After this story completes:
- Story 35.5 (ProviderSelector) can integrate InteractivePrompter
- Can be developed in parallel with Stories 35.2 and 35.3

---

**Story Status**: Todo
**Next Action**: Begin implementation after Story 35.1 completes (can be parallel with 35.2, 35.3)
**Created**: 2025-01-12
**Last Updated**: 2025-01-12

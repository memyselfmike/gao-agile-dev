# Story 41.1: TUI Wizard Implementation

## User Story

As a developer working in Docker, SSH, or WSL environments,
I want a terminal-based onboarding wizard that guides me through setup,
So that I can configure GAO-Dev without requiring a browser or GUI.

## Acceptance Criteria

- [ ] AC1: TUI wizard uses Rich library for formatted terminal output
- [ ] AC2: Displays welcome panel with GAO-Dev branding and setup context
- [ ] AC3: Implements 4-step flow: Project, Git, Provider, Credentials
- [ ] AC4: Shows progress indicator (e.g., "Step 2 of 4: Git Configuration")
- [ ] AC5: Provider selection displays Rich Table with options, descriptions, and API key requirements
- [ ] AC6: Credential input uses password masking with optional reveal
- [ ] AC7: Shows validation spinner during API key validation
- [ ] AC8: Supports back navigation to previous steps
- [ ] AC9: Displays success panel with configuration summary on completion
- [ ] AC10: Handles keyboard interrupt (Ctrl+C) gracefully with confirmation prompt
- [ ] AC11: All inputs have sensible defaults pre-filled (e.g., folder name for project)
- [ ] AC12: Error messages displayed inline with red styling

## Technical Notes

### Implementation Details

Create `gao_dev/cli/tui_wizard.py`:

```python
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress

class TUIWizard:
    """Terminal User Interface wizard using Rich library."""

    def __init__(self, console: Console = None):
        self.console = console or Console()
        self.steps = ['project', 'git', 'provider', 'credentials']
        self.current_step = 0
        self.data = {}

    async def run(self) -> Config:
        """Run the 4-step TUI wizard."""
        self._show_welcome()

        while self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            result = await self._run_step(step)

            if result == 'back' and self.current_step > 0:
                self.current_step -= 1
            elif result == 'next':
                self.current_step += 1
            elif result == 'cancel':
                if Confirm.ask("Are you sure you want to cancel setup?"):
                    raise KeyboardInterrupt

        self._show_completion()
        return self._build_config()
```

### Step Implementations

#### Project Step
- Project name (default: folder name)
- Project type display (greenfield/brownfield)
- Optional description

#### Git Step
- Git user.name (default: global config if available)
- Git user.email (default: global config if available)
- Initialize git repository checkbox (if not already init)

#### Provider Step
- Table with providers: Claude Code, OpenCode SDK, Direct API, Ollama
- Show which require API keys
- Model selection per provider

#### Credentials Step
- Check environment variables first
- Password-masked input
- Validation with spinner
- Retry/Skip options

### Rich Components Used

- `Panel.fit()` for bordered sections
- `Table()` for provider selection
- `Prompt.ask()` for text input
- `Prompt.ask(password=True)` for credentials
- `Confirm.ask()` for boolean choices
- `Status()` for spinners

## Test Scenarios

1. **Welcome display**: Given TUI wizard starts, When welcome panel shown, Then displays GAO-Dev branding and context

2. **Project step defaults**: Given folder named "my-app", When project step runs, Then project name defaults to "my-app"

3. **Git step pre-fill**: Given global git config exists, When git step runs, Then name and email pre-filled

4. **Provider table display**: Given provider step runs, When table displayed, Then shows all providers with descriptions

5. **Credential masking**: Given credential input, When user types, Then characters are masked with asterisks

6. **Validation spinner**: Given API key entered, When validation runs, Then spinner shows "Validating..."

7. **Back navigation**: Given on step 3, When user selects "back", Then returns to step 2

8. **Ctrl+C handling**: Given wizard in progress, When Ctrl+C pressed, Then confirmation prompt appears

9. **Completion summary**: Given all steps complete, When completion shown, Then displays configuration summary

10. **Environment variable detection**: Given `$ANTHROPIC_API_KEY` set, When credentials step runs, Then shows "Found API key in environment"

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit tests written (>80% coverage)
- [ ] Integration tests for complete wizard flow
- [ ] Tested on bash, zsh, PowerShell, cmd terminals
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Type hints complete (no `Any`)

## Story Points: 8

## Dependencies

- Story 40.1: Environment Detection
- Story 40.2: Global and Project State Detection
- Story 41.4: CredentialManager (for credential operations)
- Story 41.6: API Key Validation

## Notes

- Test terminal width handling for small windows
- Consider color scheme for accessibility (avoid red/green only)
- Use `structlog` for logging user interactions
- Ensure Unicode characters work on Windows cmd
- Provider selection should match Epic 35 provider list exactly

# Story 40.3: StartupOrchestrator Implementation

## User Story

As a developer,
I want a central coordinator that manages the entire startup flow based on detected environment and state,
So that I get a seamless, context-appropriate onboarding experience without manual intervention.

## Acceptance Criteria

- [ ] AC1: StartupOrchestrator coordinates environment detection, state detection, wizard selection, and interface launch
- [ ] AC2: Selects Web wizard for Desktop GUI environments
- [ ] AC3: Selects TUI wizard for Docker, SSH, WSL, and Remote Dev environments
- [ ] AC4: Skips all wizards for HEADLESS environments (CI/CD), using environment variables only
- [ ] AC5: Skips onboarding for returning users with existing GAO-Dev projects
- [ ] AC6: Provides abbreviated flow for returning users creating new projects
- [ ] AC7: Handles credential validation before launching interface
- [ ] AC8: Initializes project directory structure when needed
- [ ] AC9: Launches appropriate interface (web server or CLI REPL) after onboarding
- [ ] AC10: Provides clear error messages when startup fails at any phase
- [ ] AC11: Supports `--headless`, `--no-browser`, and `--port` command-line options
- [ ] AC12: Total startup time <2 seconds from command to interface ready

## Technical Notes

### Implementation Details

Create `gao_dev/cli/startup_orchestrator.py`:

```python
class StartupOrchestrator:
    """Coordinates the entire startup flow based on environment detection."""

    def __init__(self):
        self.environment = detect_environment()
        self.credential_manager = CredentialManager(self.environment)
        self.config_manager = ConfigManager()

    async def start(
        self,
        project_path: Optional[Path] = None,
        headless: bool = False,
        no_browser: bool = False,
        port: int = 3000
    ) -> None:
        """Execute the complete startup flow."""
        pass

    async def _run_onboarding(self) -> Config:
        """Run environment-appropriate onboarding wizard."""
        pass

    async def _launch_interface(self, config: Config) -> None:
        """Launch web server or CLI based on configuration."""
        pass
```

### Startup Phases

1. **Detection Phase**: Environment + Global + Project state
2. **Decision Phase**: Determine if onboarding needed, which wizard type
3. **Onboarding Phase**: Run appropriate wizard (or skip)
4. **Validation Phase**: Validate credentials work
5. **Initialization Phase**: Create project structure if needed
6. **Launch Phase**: Start web server or CLI REPL

### Wizard Selection Matrix

| Environment | Global State | Project State | Wizard |
|-------------|--------------|---------------|--------|
| Desktop | First-time | Empty | Web (full) |
| Desktop | Returning | Empty | Web (abbreviated) |
| Desktop | * | GAO-Dev | None (direct launch) |
| Docker/SSH | First-time | * | TUI (full) |
| Docker/SSH | Returning | Empty | TUI (abbreviated) |
| Headless | * | * | None (env vars only) |

### Error Handling Strategy

- Phase failures should provide actionable error messages
- Partial onboarding should be recoverable (see Story 41.5)
- Credential validation failures should offer retry or skip options

## Test Scenarios

1. **Desktop first-time empty**: Given Desktop environment and first-time user with empty directory, When `start()` is called, Then Web wizard runs with full flow

2. **Docker first-time**: Given Docker environment and first-time user, When `start()` is called, Then TUI wizard runs with full flow

3. **Returning user new project**: Given returning user with empty directory, When `start()` is called, Then abbreviated wizard runs

4. **Existing project**: Given existing GAO-Dev project, When `start()` is called, Then wizard is skipped and interface launches directly

5. **Headless mode**: Given `$GAO_DEV_HEADLESS=1`, When `start()` is called, Then no wizard runs and env vars are used for configuration

6. **CLI override**: Given `--headless` flag provided, When `start()` is called, Then headless mode is forced regardless of environment

7. **No-browser option**: Given `--no-browser` flag, When `start()` is called in Desktop environment, Then web server starts but browser does not open

8. **Port option**: Given `--port 8080`, When `start()` is called, Then web server starts on port 8080

9. **Credential validation failure**: Given invalid API key, When `start()` is called, Then error message shown with fix suggestions

10. **Startup performance**: Given any valid configuration, When `start()` is called, Then interface is ready in <2 seconds

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit tests written (>80% coverage)
- [ ] Integration tests for each startup path
- [ ] Performance benchmarks pass (<2s startup)
- [ ] Code reviewed
- [ ] Documentation updated with flow diagrams
- [ ] Type hints complete (no `Any`)
- [ ] Error messages reviewed for actionability

## Story Points: 8

## Dependencies

- Story 40.1: Environment Detection
- Story 40.2: Global and Project State Detection

## Notes

- Use `async/await` for non-blocking operations
- Consider progress indicators for longer operations (validation, server start)
- Log startup phases at INFO level for debugging
- The orchestrator should be testable with mocked dependencies
- Consider making wizard selection logic pluggable for future extensibility

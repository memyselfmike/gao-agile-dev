# Story 40.4: Unified `gao-dev start` Command

## User Story

As a developer,
I want `gao-dev start` to be the single entry point that works in any context,
So that I don't need to remember multiple commands or understand the difference between `init`, `start`, and `web start`.

## Acceptance Criteria

- [ ] AC1: `gao-dev start` invokes StartupOrchestrator with appropriate options
- [ ] AC2: Works in any directory (empty, existing code, existing GAO-Dev project)
- [ ] AC3: Supports `--headless` flag to force headless mode (no browser, no interactive prompts)
- [ ] AC4: Supports `--no-browser` flag to start web server without opening browser
- [ ] AC5: Supports `--port` option to specify web server port (default 3000)
- [ ] AC6: Supports `--tui` flag to force TUI wizard even in Desktop environment
- [ ] AC7: Supports `--project` option to specify project path (defaults to current directory)
- [ ] AC8: Shows helpful startup message with detected context before proceeding
- [ ] AC9: Handles Ctrl+C gracefully during startup, leaving system in valid state
- [ ] AC10: Returns appropriate exit codes (0 for success, 1 for error, 130 for interrupt)

## Technical Notes

### Implementation Details

Modify `gao_dev/cli/commands.py`:

```python
@click.command('start')
@click.option('--headless', is_flag=True, help='Run without browser or interactive prompts')
@click.option('--no-browser', is_flag=True, help='Start web server without opening browser')
@click.option('--port', default=3000, type=int, help='Web server port (default: 3000)')
@click.option('--tui', is_flag=True, help='Force TUI wizard instead of web')
@click.option('--project', type=click.Path(), help='Project directory path')
def start_command(headless, no_browser, port, tui, project):
    """Start GAO-Dev with auto-detection and guided setup."""
    pass
```

### Startup Message Format

```
GAO-Dev v2.0.0

Detected:
  Environment: Desktop (macOS)
  User: First-time setup
  Project: Empty directory

Starting web-based onboarding wizard...
```

### Signal Handling

- Register SIGINT handler to cleanup gracefully
- Ensure any partial state is valid before exit
- Log interruption at INFO level

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 130 | Interrupted (Ctrl+C) |

## Test Scenarios

1. **Basic invocation**: Given empty directory, When `gao-dev start` is run, Then StartupOrchestrator is invoked with defaults

2. **Headless flag**: Given `--headless` flag, When command runs, Then `headless=True` passed to orchestrator

3. **No-browser flag**: Given `--no-browser` flag, When command runs, Then `no_browser=True` passed to orchestrator

4. **Custom port**: Given `--port 8080`, When command runs, Then `port=8080` passed to orchestrator

5. **TUI override**: Given `--tui` flag in Desktop environment, When command runs, Then TUI wizard is selected

6. **Custom project path**: Given `--project /path/to/project`, When command runs, Then `/path/to/project` used as project path

7. **Invalid project path**: Given `--project /nonexistent`, When command runs, Then error message shown and exit code 1

8. **Startup message**: Given any context, When command runs, Then startup message shows detected environment

9. **Ctrl+C handling**: Given startup in progress, When Ctrl+C pressed, Then cleanup runs and exit code 130

10. **Help text**: Given `gao-dev start --help`, When command runs, Then shows all options with descriptions

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit tests written (>80% coverage)
- [ ] Integration tests for CLI invocation
- [ ] Help text reviewed for clarity
- [ ] Code reviewed
- [ ] Documentation updated (CLAUDE.md, README)
- [ ] Type hints complete (no `Any`)

## Story Points: 5

## Dependencies

- Story 40.3: StartupOrchestrator Implementation

## Notes

- Consider adding `--verbose` flag for debugging
- Document all flags in `gao-dev start --help` comprehensively
- Test flag combinations (e.g., `--headless` with `--port`)
- The startup message should use Rich formatting for visual appeal
- Consider short aliases for common flags (e.g., `-H` for `--headless`)

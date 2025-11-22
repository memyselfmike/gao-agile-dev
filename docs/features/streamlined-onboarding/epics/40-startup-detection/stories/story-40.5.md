# Story 40.5: Deprecated Command Handling

## User Story

As a developer using legacy GAO-Dev commands,
I want to see clear deprecation warnings that guide me to the new unified command,
So that I can update my workflows before the old commands are removed.

## Acceptance Criteria

- [ ] AC1: `gao-dev init` shows deprecation warning with migration guidance
- [ ] AC2: `gao-dev web start` shows deprecation warning with migration guidance
- [ ] AC3: Deprecation warnings use Rich Panel with yellow border for visibility
- [ ] AC4: Warnings include the replacement command (`gao-dev start`)
- [ ] AC5: Warnings include removal timeline (e.g., "Will be removed in v2.0")
- [ ] AC6: After showing warning, deprecated commands redirect to `gao-dev start` after 5-second delay
- [ ] AC7: Users can skip delay with `--no-wait` flag
- [ ] AC8: Deprecation warnings logged at WARNING level
- [ ] AC9: Help text for deprecated commands marks them as `[DEPRECATED]`
- [ ] AC10: `--quiet` flag suppresses warning (for scripts migrating gradually)

## Technical Notes

### Implementation Details

Modify both commands in `gao_dev/cli/commands.py`:

```python
import time
from rich.panel import Panel

def show_deprecation_warning(old_command: str, new_command: str, removal_version: str):
    """Display a deprecation warning with migration guidance."""
    console.print(Panel.fit(
        f"[yellow]DEPRECATION WARNING[/yellow]\n\n"
        f"The '{old_command}' command is deprecated and will be removed in {removal_version}.\n\n"
        f"Use '{new_command}' instead - it will automatically handle\n"
        f"initialization with a guided setup wizard.\n\n"
        f"[dim]This command will redirect to '{new_command}' in 5 seconds...[/dim]\n"
        f"[dim]Use --no-wait to skip this delay, or --quiet to suppress this warning.[/dim]",
        border_style="yellow"
    ))

@click.command('init')
@click.option('--no-wait', is_flag=True, help='Skip the 5-second delay')
@click.option('--quiet', is_flag=True, help='Suppress deprecation warning')
def init_command(no_wait, quiet):
    """[DEPRECATED] Initialize a GAO-Dev project. Use 'gao-dev start' instead."""
    if not quiet:
        show_deprecation_warning('gao-dev init', 'gao-dev start', 'v2.0')
        if not no_wait:
            time.sleep(5)

    ctx = click.get_current_context()
    ctx.invoke(start_command)

@click.command('web')
@click.pass_context
def web_group(ctx):
    """[DEPRECATED] Web interface commands. Use 'gao-dev start' instead."""
    pass

@web_group.command('start')
@click.option('--no-wait', is_flag=True, help='Skip the 5-second delay')
@click.option('--quiet', is_flag=True, help='Suppress deprecation warning')
def web_start_command(no_wait, quiet):
    """[DEPRECATED] Start web interface. Use 'gao-dev start' instead."""
    if not quiet:
        show_deprecation_warning('gao-dev web start', 'gao-dev start', 'v2.0')
        if not no_wait:
            time.sleep(5)

    ctx = click.get_current_context()
    ctx.invoke(start_command)
```

### Warning Format

```
+---------------------------------------------------+
|              DEPRECATION WARNING                  |
|                                                   |
| The 'gao-dev init' command is deprecated and      |
| will be removed in v2.0.                          |
|                                                   |
| Use 'gao-dev start' instead - it will             |
| automatically handle initialization with a        |
| guided setup wizard.                              |
|                                                   |
| This command will redirect to 'gao-dev start'     |
| in 5 seconds...                                   |
|                                                   |
| Use --no-wait to skip this delay, or --quiet      |
| to suppress this warning.                         |
+---------------------------------------------------+
```

### Logging

Log deprecation usage for telemetry (if enabled):

```python
logger.warning(
    "deprecated_command_used",
    command=old_command,
    replacement=new_command,
    removal_version=removal_version
)
```

## Test Scenarios

1. **Init deprecation warning**: Given `gao-dev init` is run, When command executes, Then deprecation warning is shown with yellow panel

2. **Web start deprecation**: Given `gao-dev web start` is run, When command executes, Then deprecation warning is shown

3. **Redirect after delay**: Given deprecation warning shown, When 5 seconds pass, Then `gao-dev start` is invoked

4. **No-wait flag**: Given `gao-dev init --no-wait`, When command executes, Then redirects immediately without delay

5. **Quiet flag**: Given `gao-dev init --quiet`, When command executes, Then no warning shown and redirects immediately

6. **Help text marking**: Given `gao-dev init --help`, When help displayed, Then shows "[DEPRECATED]" in description

7. **Warning logged**: Given deprecation warning shown, When logged, Then log entry at WARNING level with command details

8. **Combined flags**: Given `gao-dev init --no-wait --quiet`, When command executes, Then redirects immediately with no output

9. **Removal version**: Given deprecation warning shown, When displayed, Then shows "v2.0" as removal version

10. **Context passed**: Given `gao-dev init` in specific directory, When redirected to start, Then start uses same directory context

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit tests written (>80% coverage)
- [ ] Integration tests for redirect behavior
- [ ] Help text updated for deprecated commands
- [ ] Code reviewed
- [ ] Documentation updated with deprecation notice
- [ ] Type hints complete (no `Any`)

## Story Points: 3

## Dependencies

- Story 40.4: Unified `gao-dev start` Command

## Notes

- Consider adding deprecation warnings to CHANGELOG
- Update any documentation that references old commands
- Ensure CI/CD scripts using old commands are identified for migration
- The 5-second delay gives users time to read the message
- Consider tracking deprecated command usage for telemetry
- Add deprecation notices to any tutorials or guides

# Story 1.1: Sandbox CLI Command Structure

**Epic**: Epic 1 - Sandbox Infrastructure
**Status**: Draft
**Priority**: P0 (Critical)
**Estimated Effort**: 3 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27

---

## User Story

**As a** developer using GAO-Dev
**I want** dedicated sandbox CLI commands
**So that** I can manage sandbox projects separately from regular GAO-Dev operations

---

## Acceptance Criteria

### AC1: Sandbox Command Group Created
- ✅ `gao-dev sandbox` command group exists
- ✅ `gao-dev sandbox --help` shows all subcommands
- ✅ Follows Click command group pattern
- ✅ Integrates with existing GAO-Dev CLI

### AC2: Help Documentation
- ✅ Each subcommand has clear help text
- ✅ Examples provided in help output
- ✅ Options documented with descriptions
- ✅ Command usage shown correctly

### AC3: Error Handling
- ✅ Unknown subcommands show helpful error
- ✅ Missing arguments display usage
- ✅ Invalid options show clear error messages
- ✅ Errors exit with code 1

### AC4: Code Organization
- ✅ New file: `gao_dev/cli/sandbox_commands.py`
- ✅ Imported in main CLI module
- ✅ Follows existing code style
- ✅ Type hints included

---

## Technical Details

### File Structure
```
gao_dev/cli/
├── __init__.py
├── commands.py              # Existing commands
└── sandbox_commands.py      # NEW: Sandbox commands
```

### Implementation Approach

**Step 1: Create sandbox_commands.py**
```python
"""CLI commands for GAO-Dev sandbox management."""

import click
from pathlib import Path

@click.group()
def sandbox():
    """
    Manage sandbox projects for testing and benchmarking.

    Sandbox projects are isolated environments for validating
    GAO-Dev's autonomous capabilities.
    """
    pass

@sandbox.command()
@click.argument("project_name")
@click.option("--config", type=click.Path(), help="Configuration file")
def init(project_name: str, config: str):
    """Initialize a new sandbox project."""
    click.echo(f">> Initializing sandbox project: {project_name}")
    # Implementation in next story
    pass

@sandbox.command()
@click.argument("project_name", required=False)
def clean(project_name: str):
    """Reset sandbox project to clean state."""
    click.echo(f">> Cleaning sandbox project: {project_name}")
    # Implementation in next story
    pass

@sandbox.command()
@click.option("--status", type=str, help="Filter by status")
def list(status: str):
    """List all sandbox projects."""
    click.echo(">> Listing sandbox projects")
    # Implementation in next story
    pass

@sandbox.command()
@click.argument("benchmark_config", type=click.Path(exists=True))
def run(benchmark_config: str):
    """Execute a benchmark run."""
    click.echo(f">> Running benchmark: {benchmark_config}")
    # Implementation in later epic
    pass

@sandbox.command()
@click.argument("run_id")
def report(run_id: str):
    """Generate report for benchmark run."""
    click.echo(f">> Generating report for run: {run_id}")
    # Implementation in later epic
    pass

@sandbox.command()
@click.argument("run1")
@click.argument("run2")
def compare(run1: str, run2: str):
    """Compare two benchmark runs."""
    click.echo(f">> Comparing runs: {run1} vs {run2}")
    # Implementation in later epic
    pass
```

**Step 2: Register in main CLI**
```python
# gao_dev/cli/commands.py

from .sandbox_commands import sandbox

@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    GAO-Dev - Software Engineering Team for Generative Autonomous Organisation.
    """
    pass

# Add sandbox command group
cli.add_command(sandbox)
```

**Step 3: Update __init__.py**
```python
# gao_dev/cli/__init__.py

from .commands import cli
from .sandbox_commands import sandbox

__all__ = ["cli", "sandbox"]
```

---

## Testing Approach

### Manual Testing
```bash
# Test command group exists
python -m gao_dev.cli.commands sandbox --help

# Test subcommands
python -m gao_dev.cli.commands sandbox init --help
python -m gao_dev.cli.commands sandbox clean --help
python -m gao_dev.cli.commands sandbox list --help
python -m gao_dev.cli.commands sandbox run --help
python -m gao_dev.cli.commands sandbox report --help
python -m gao_dev.cli.commands sandbox compare --help

# Test error handling
python -m gao_dev.cli.commands sandbox invalid-command
python -m gao_dev.cli.commands sandbox init  # Missing argument
```

### Expected Output
```
>> Sandbox Commands Available:
   init      Initialize a new sandbox project
   clean     Reset sandbox project to clean state
   list      List all sandbox projects
   run       Execute a benchmark run
   report    Generate report for benchmark run
   compare   Compare two benchmark runs

Use "gao-dev sandbox COMMAND --help" for more information.
```

---

## Dependencies

### Required Packages
- ✅ Click (already installed)
- ✅ Python 3.11+ (already required)

### Code Dependencies
- Existing GAO-Dev CLI structure
- Click command group pattern

---

## Definition of Done

- [ ] File `gao_dev/cli/sandbox_commands.py` created
- [ ] All 6 subcommands defined (init, clean, list, run, report, compare)
- [ ] Command group registered in main CLI
- [ ] Help text for all commands complete
- [ ] Manual testing completed successfully
- [ ] Code follows existing style (ASCII-only, type hints)
- [ ] Committed to git with conventional commit message

---

## Related Stories

**Depends On**: None (foundational story)
**Blocks**:
- Story 1.4 (sandbox init implementation)
- Story 1.5 (sandbox clean implementation)
- Story 1.6 (sandbox list implementation)

---

## Notes

This story creates the CLI structure only - actual implementation happens in subsequent stories. The focus is on:
1. Clean command structure
2. Good UX (help text, error messages)
3. Integration with existing CLI
4. Extensibility for future commands

The placeholder implementations (`pass` statements) will be filled in by later stories.

---

## Acceptance Testing

### Test Case 1: Command Group Exists
```bash
$ python -m gao_dev.cli.commands sandbox --help
Usage: python -m gao_dev.cli.commands sandbox [OPTIONS] COMMAND [ARGS]...

  Manage sandbox projects for testing and benchmarking.
  ...
```
**Expected**: Help text displays with all subcommands

### Test Case 2: Subcommand Help
```bash
$ python -m gao_dev.cli.commands sandbox init --help
Usage: ... sandbox init [OPTIONS] PROJECT_NAME

  Initialize a new sandbox project.

Options:
  --config PATH  Configuration file
  --help         Show this message and exit.
```
**Expected**: Detailed help for init command

### Test Case 3: Error Handling
```bash
$ python -m gao_dev.cli.commands sandbox invalid
Error: No such command 'invalid'.
```
**Expected**: Clear error message, exit code 1

---

**Created by**: Bob (Scrum Master) via BMAD workflow
**Ready for Implementation**: Yes
**Estimated Completion**: 1 day

---

*This story is part of the GAO-Dev Sandbox & Benchmarking System project.*

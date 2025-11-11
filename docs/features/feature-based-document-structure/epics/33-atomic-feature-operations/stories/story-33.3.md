---
document:
  type: "story"
  state: "ready"
  created: "2025-11-11"
  epic: 33
  story: 3
  feature: "feature-based-document-structure"
  points: 2
---

# Story 33.3: CLI Commands (2 points)

**Epic:** 33 - Atomic Feature Operations
**Feature:** Feature-Based Document Structure
**Status:** Ready
**Owner:** Unassigned
**Points:** 2

## User Story

As a **developer using GAO-Dev CLI**,
I want **create-feature, list-features, and validate-structure commands**,
So that **I can manage features from the command line without writing code**.

## Acceptance Criteria

### AC1: create-feature Command
- [ ] Create `gao_dev/cli/commands/create_feature.py`
- [ ] CLI signature: `gao-dev create-feature <name> [OPTIONS]`
- [ ] Options:
  - `--scale-level INTEGER` (0-4, default: 3)
  - `--scope TEXT` (mvp/feature, default: feature)
  - `--description TEXT` (optional)
  - `--owner TEXT` (optional)
- [ ] Wraps GitIntegratedStateManager.create_feature()
- [ ] Rich formatted output (success message, next steps)
- [ ] Error handling with helpful messages

### AC2: list-features Command
- [ ] Create `gao_dev/cli/commands/list_features.py`
- [ ] CLI signature: `gao-dev list-features [OPTIONS]`
- [ ] Options:
  - `--scope TEXT` (filter by mvp/feature)
  - `--status TEXT` (filter by planning/active/complete/archived)
- [ ] Wraps StateCoordinator.list_features()
- [ ] Rich table output with columns: Name, Scope, Status, Scale, Owner, Created
- [ ] Empty state message if no features

### AC3: validate-structure Command
- [ ] Create `gao_dev/cli/commands/validate_structure.py`
- [ ] CLI signature: `gao-dev validate-structure [OPTIONS]`
- [ ] Options:
  - `--feature TEXT` (validate specific feature, optional)
  - `--all` (validate all features)
- [ ] Wraps FeaturePathValidator.validate_structure()
- [ ] Rich formatted output showing violations
- [ ] Exit code 0 if compliant, 1 if violations found
- [ ] Actionable suggestions for fixing violations

### AC4: Rich CLI Output
- [ ] Use Rich library for formatted output
- [ ] Success messages in green
- [ ] Error messages in red
- [ ] Tables for list-features
- [ ] Panels for validation results
- [ ] Progress spinners for long operations

### AC5: Testing
- [ ] 20+ CLI test scenarios covering:
  - create-feature success and error cases
  - list-features with various filters
  - validate-structure compliance and violations
  - Rich output verification
  - Exit codes

## Technical Notes

### Implementation Approach

**create-feature Command:**

```python
# Location: gao_dev/cli/commands/create_feature.py

import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
import structlog

from gao_dev.core.services.git_integrated_state_manager import GitIntegratedStateManager
from gao_dev.core.state.feature_state_service import FeatureScope, FeatureStatus

logger = structlog.get_logger(__name__)
console = Console()


@click.command("create-feature")
@click.argument("name")
@click.option(
    "--scale-level",
    type=click.IntRange(0, 4),
    default=3,
    help="Project scale level (0=chore, 1=bug, 2=small, 3=medium, 4=large)"
)
@click.option(
    "--scope",
    type=click.Choice(["mvp", "feature"], case_sensitive=False),
    default="feature",
    help="Feature scope (mvp for initial scope, feature for subsequent)"
)
@click.option(
    "--description",
    type=str,
    default=None,
    help="Feature description"
)
@click.option(
    "--owner",
    type=str,
    default=None,
    help="Feature owner"
)
def create_feature(
    name: str,
    scale_level: int,
    scope: str,
    description: str,
    owner: str
):
    """
    Create a new feature with atomic file + DB + git operation.

    Creates feature folder structure, registers in database, and commits to git
    in a single atomic operation. If any step fails, all changes are rolled back.

    Examples:

        # Create a feature with default settings
        gao-dev create-feature user-auth

        # Create MVP with custom scale level
        gao-dev create-feature mvp --scope mvp --scale-level 4

        # Create feature with full metadata
        gao-dev create-feature payment-processing \\
            --scale-level 3 \\
            --description "Payment gateway integration" \\
            --owner "john@example.com"
    """
    try:
        console.print(f"\n[bold cyan]Creating feature:[/bold cyan] {name}")

        # Auto-detect project root
        project_root = _find_project_root()

        # Initialize GitIntegratedStateManager
        manager = _init_state_manager(project_root)

        # Create feature (atomic operation)
        with console.status(f"[bold green]Creating {name}...", spinner="dots"):
            feature = manager.create_feature(
                name=name,
                scope=FeatureScope(scope.upper()),
                scale_level=scale_level,
                description=description,
                owner=owner
            )

        # Success output
        console.print(Panel(
            f"[bold green]✓ Feature created successfully![/bold green]\n\n"
            f"Name: {feature.name}\n"
            f"Scope: {feature.scope.value}\n"
            f"Scale Level: {feature.scale_level}\n"
            f"Status: {feature.status.value}\n"
            f"Location: docs/features/{name}/\n\n"
            f"[bold]Next Steps:[/bold]\n"
            f"1. Review PRD: docs/features/{name}/PRD.md\n"
            f"2. Review Architecture: docs/features/{name}/ARCHITECTURE.md\n"
            f"3. Create epics: gao-dev create-epic {name} <epic-title>\n"
            f"4. View features: gao-dev list-features",
            title="Feature Created",
            border_style="green"
        ))

    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise click.Abort()
    except Exception as e:
        logger.error("Feature creation failed", error=str(e), exc_info=True)
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}")
        raise click.Abort()


def _find_project_root() -> Path:
    """Find project root by searching for .gao-dev/ or .git/."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".gao-dev").exists() or (current / ".git").exists():
            return current
        current = current.parent
    raise ValueError("Not in a GAO-Dev project. Run from project directory.")


def _init_state_manager(project_root: Path) -> GitIntegratedStateManager:
    """Initialize GitIntegratedStateManager with all dependencies."""
    # Import and instantiate all required services
    # (Full implementation would initialize all services)
    # For brevity, showing signature only
    pass
```

**list-features Command:**

```python
# Location: gao_dev/cli/commands/list_features.py

import click
from rich.console import Console
from rich.table import Table
import structlog

from gao_dev.core.state.state_coordinator import StateCoordinator
from gao_dev.core.state.feature_state_service import FeatureScope, FeatureStatus

console = Console()


@click.command("list-features")
@click.option(
    "--scope",
    type=click.Choice(["mvp", "feature"], case_sensitive=False),
    default=None,
    help="Filter by scope"
)
@click.option(
    "--status",
    type=click.Choice(["planning", "active", "complete", "archived"], case_sensitive=False),
    default=None,
    help="Filter by status"
)
def list_features(scope: str, status: str):
    """
    List all features in the project.

    Displays features in a formatted table with filtering options.

    Examples:

        # List all features
        gao-dev list-features

        # List only MVP features
        gao-dev list-features --scope mvp

        # List active features
        gao-dev list-features --status active

        # List active MVP features
        gao-dev list-features --scope mvp --status active
    """
    try:
        # Auto-detect project root
        project_root = _find_project_root()

        # Initialize StateCoordinator
        coordinator = _init_state_coordinator(project_root)

        # Query features
        scope_filter = FeatureScope(scope.upper()) if scope else None
        status_filter = FeatureStatus(status.upper()) if status else None

        features = coordinator.list_features(
            scope=scope_filter,
            status=status_filter
        )

        # Display results
        if not features:
            console.print("\n[yellow]No features found.[/yellow]")
            console.print("\nCreate a feature with: [bold]gao-dev create-feature <name>[/bold]\n")
            return

        # Create Rich table
        table = Table(title=f"Features ({len(features)} total)")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Scope", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Scale", justify="right")
        table.add_column("Owner")
        table.add_column("Created")

        for feature in features:
            table.add_row(
                feature.name,
                feature.scope.value,
                feature.status.value,
                str(feature.scale_level),
                feature.owner or "—",
                feature.created_at[:10]  # Just date
            )

        console.print(table)
        console.print()

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise click.Abort()
```

**validate-structure Command:**

```python
# Location: gao_dev/cli/commands/validate_structure.py

import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
import structlog

from gao_dev.core.services.feature_path_validator import FeaturePathValidator

console = Console()


@click.command("validate-structure")
@click.option(
    "--feature",
    type=str,
    default=None,
    help="Validate specific feature (name)"
)
@click.option(
    "--all",
    is_flag=True,
    help="Validate all features"
)
def validate_structure(feature: str, all: bool):
    """
    Validate feature folder structure compliance.

    Checks that feature folders follow the required structure:
    - Required files: PRD.md, ARCHITECTURE.md, README.md
    - Required folders: epics/, QA/
    - Co-located epic-story structure

    Exit code 0 if compliant, 1 if violations found.

    Examples:

        # Validate specific feature
        gao-dev validate-structure --feature user-auth

        # Validate all features
        gao-dev validate-structure --all

        # Auto-detect from current directory
        cd docs/features/user-auth
        gao-dev validate-structure
    """
    try:
        project_root = _find_project_root()
        validator = FeaturePathValidator()

        if all:
            # Validate all features
            features_dir = project_root / "docs" / "features"
            violations_found = False

            for feature_path in features_dir.iterdir():
                if feature_path.is_dir():
                    violations = validator.validate_structure(feature_path)
                    if violations:
                        violations_found = True
                        _display_violations(feature_path.name, violations)
                    else:
                        console.print(f"[green]✓ {feature_path.name}[/green]")

            if not violations_found:
                console.print("\n[bold green]All features are compliant![/bold green]\n")
                raise SystemExit(0)
            else:
                raise SystemExit(1)

        elif feature:
            # Validate specific feature
            feature_path = project_root / "docs" / "features" / feature
            violations = validator.validate_structure(feature_path)

            if violations:
                _display_violations(feature, violations)
                raise SystemExit(1)
            else:
                console.print(Panel(
                    f"[bold green]✓ Feature '{feature}' is compliant![/bold green]",
                    border_style="green"
                ))
                raise SystemExit(0)

        else:
            # Auto-detect from CWD
            cwd = Path.cwd()
            if "docs/features/" in str(cwd):
                # Extract feature name from path
                parts = cwd.parts
                feature_idx = parts.index("features") + 1
                feature_name = parts[feature_idx]
                feature_path = project_root / "docs" / "features" / feature_name

                violations = validator.validate_structure(feature_path)

                if violations:
                    _display_violations(feature_name, violations)
                    raise SystemExit(1)
                else:
                    console.print(Panel(
                        f"[bold green]✓ Feature '{feature_name}' is compliant![/bold green]",
                        border_style="green"
                    ))
                    raise SystemExit(0)
            else:
                console.print("[yellow]Specify --feature <name> or --all[/yellow]")
                raise click.Abort()

    except SystemExit:
        raise
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise click.Abort()


def _display_violations(feature_name: str, violations: list[str]):
    """Display validation violations with Rich formatting."""
    console.print(Panel(
        f"[bold red]✗ Feature '{feature_name}' has violations:[/bold red]\n\n" +
        "\n".join(f"  • {v}" for v in violations) +
        "\n\n[bold]Suggested Fixes:[/bold]\n"
        "  1. Add missing files/folders\n"
        "  2. Migrate to co-located epic-story structure\n"
        "  3. Run 'gao-dev validate-structure --all' to check all features",
        title="Structure Violations",
        border_style="red"
    ))
```

### Code Locations

**New Files:**
- `gao_dev/cli/commands/create_feature.py`
- `gao_dev/cli/commands/list_features.py`
- `gao_dev/cli/commands/validate_structure.py`

**Files to Update:**
- `gao_dev/cli/cli.py` (register new commands)
- `setup.py` (ensure Click and Rich are dependencies)

### Dependencies

**Required Before Starting:**
- Story 33.2: GitIntegratedStateManager.create_feature() (COMPLETE)
- Story 32.2: StateCoordinator.list_features() (COMPLETE)
- Story 32.3: FeaturePathValidator (COMPLETE)

**Blocks:**
- None (final story in Epic 33)

### Integration Points

1. **GitIntegratedStateManager**: create-feature command
2. **StateCoordinator**: list-features command
3. **FeaturePathValidator**: validate-structure command
4. **Rich Library**: All CLI output formatting

## Testing Requirements

### CLI Tests (20+ scenarios)

**Location:** `tests/cli/test_create_feature.py`, `tests/cli/test_list_features.py`, `tests/cli/test_validate_structure.py`

**Test Coverage:**

1. **create-feature Command (8 scenarios)**
   - Create feature with default options
   - Create feature with all options
   - Create MVP feature
   - Invalid feature name (error)
   - Duplicate feature name (error)
   - Invalid scale level (error)
   - Rich output verification
   - Exit code 0 on success

2. **list-features Command (6 scenarios)**
   - List all features
   - Filter by scope (mvp)
   - Filter by scope (feature)
   - Filter by status (active)
   - Combined filters
   - Empty state (no features)
   - Rich table output verification

3. **validate-structure Command (6 scenarios)**
   - Validate compliant feature (exit 0)
   - Validate non-compliant feature (exit 1)
   - Validate all features
   - Auto-detect from CWD
   - Feature not found (error)
   - Rich output verification (violations displayed)

## Definition of Done

- [ ] All 3 CLI commands implemented
- [ ] Rich formatted output for all commands
- [ ] Error handling with helpful messages
- [ ] 20+ CLI test scenarios passing
- [ ] Commands registered in gao_dev/cli/cli.py
- [ ] Help text clear and comprehensive
- [ ] Exit codes correct (0 success, 1 failure)
- [ ] Code reviewed and approved
- [ ] Type hints throughout (mypy passes)
- [ ] Structlog logging for all operations

## References

- **PRD:** `docs/features/feature-based-document-structure/PRD.md` (Section: Epic 3 - CLI Commands)
- **Architecture:** `docs/features/feature-based-document-structure/ARCHITECTURE.md` (Section: CLI Commands Layer)
- **Rich Documentation:** https://rich.readthedocs.io/
- **Click Documentation:** https://click.palletsprojects.com/

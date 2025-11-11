"""CLI command for validating feature structure.

This module provides the validate-structure command for checking
feature folder compliance with required structure.

Epic: 33 - Atomic Feature Operations
Story: 33.3 - CLI Commands
"""

import click
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

import structlog

from ..core.services.feature_path_validator import FeaturePathValidator

logger = structlog.get_logger(__name__)

# Initialize console for Rich output
if RICH_AVAILABLE:
    console = Console()


def _find_project_root() -> Path:
    """Find project root by searching for .gao-dev/ or .git/."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".gao-dev").exists() or (current / ".git").exists():
            return current
        current = current.parent
    raise ValueError("Not in a GAO-Dev project. Run from project directory.")


def _display_violations(feature_name: str, violations: list):
    """Display validation violations with Rich formatting."""
    if RICH_AVAILABLE:
        console.print(Panel(
            f"[bold red]Feature '{feature_name}' has violations:[/bold red]\n\n" +
            "\n".join(f"  * {v}" for v in violations) +
            "\n\n[bold]Suggested Fixes:[/bold]\n"
            "  1. Add missing files/folders\n"
            "  2. Migrate to co-located epic-story structure\n"
            "  3. Run 'gao-dev validate-structure --all' to check all features",
            title="Structure Violations",
            border_style="red"
        ))
    else:
        click.echo(f"\n[ERROR] Feature '{feature_name}' has violations:")
        for v in violations:
            click.echo(f"  * {v}")
        click.echo("\nSuggested Fixes:")
        click.echo("  1. Add missing files/folders")
        click.echo("  2. Migrate to co-located epic-story structure")
        click.echo("  3. Run 'gao-dev validate-structure --all' to check all features")


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
def validate_structure(feature: Optional[str], all: bool):
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

            if not features_dir.exists():
                if RICH_AVAILABLE:
                    console.print("[yellow]No features directory found.[/yellow]")
                else:
                    click.echo("No features directory found.")
                raise SystemExit(0)

            violations_found = False

            for feature_path in features_dir.iterdir():
                if feature_path.is_dir():
                    violations = validator.validate_structure(feature_path)
                    if violations:
                        violations_found = True
                        _display_violations(feature_path.name, violations)
                    else:
                        if RICH_AVAILABLE:
                            console.print(f"[green]Feature '{feature_path.name}' is compliant[/green]")
                        else:
                            click.echo(f"[OK] Feature '{feature_path.name}' is compliant")

            if not violations_found:
                if RICH_AVAILABLE:
                    console.print("\n[bold green]All features are compliant![/bold green]\n")
                else:
                    click.echo("\n[OK] All features are compliant!\n")
                raise SystemExit(0)
            else:
                raise SystemExit(1)

        elif feature:
            # Validate specific feature
            feature_path = project_root / "docs" / "features" / feature

            if not feature_path.exists():
                if RICH_AVAILABLE:
                    console.print(f"[bold red]Error:[/bold red] Feature '{feature}' not found")
                else:
                    click.echo(f"Error: Feature '{feature}' not found", err=True)
                raise SystemExit(1)

            violations = validator.validate_structure(feature_path)

            if violations:
                _display_violations(feature, violations)
                raise SystemExit(1)
            else:
                if RICH_AVAILABLE:
                    console.print(Panel(
                        f"[bold green]Feature '{feature}' is compliant![/bold green]",
                        border_style="green"
                    ))
                else:
                    click.echo(f"\n[OK] Feature '{feature}' is compliant!\n")
                raise SystemExit(0)

        else:
            # Auto-detect from CWD
            cwd = Path.cwd()
            if "features" in cwd.parts:
                # Extract feature name from path
                parts = cwd.parts
                try:
                    feature_idx = parts.index("features") + 1
                    if feature_idx < len(parts):
                        feature_name = parts[feature_idx]
                        feature_path = project_root / "docs" / "features" / feature_name

                        violations = validator.validate_structure(feature_path)

                        if violations:
                            _display_violations(feature_name, violations)
                            raise SystemExit(1)
                        else:
                            if RICH_AVAILABLE:
                                console.print(Panel(
                                    f"[bold green]Feature '{feature_name}' is compliant![/bold green]",
                                    border_style="green"
                                ))
                            else:
                                click.echo(f"\n[OK] Feature '{feature_name}' is compliant!\n")
                            raise SystemExit(0)
                except (ValueError, IndexError):
                    pass

            # No auto-detection possible
            if RICH_AVAILABLE:
                console.print("[yellow]Specify --feature <name> or --all[/yellow]")
            else:
                click.echo("Specify --feature <name> or --all")
            raise click.Abort()

    except SystemExit:
        raise
    except ValueError as e:
        if RICH_AVAILABLE:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
        else:
            click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()
    except Exception as e:
        logger.error("Validation failed", error=str(e), exc_info=True)
        if RICH_AVAILABLE:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
        else:
            click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

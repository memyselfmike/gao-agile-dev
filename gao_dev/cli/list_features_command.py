"""CLI command for listing features.

This module provides the list-features command for querying features
with filtering by scope and status.

Epic: 33 - Atomic Feature Operations
Story: 33.3 - CLI Commands
"""

import click
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

import structlog

from ..core.state_coordinator import StateCoordinator
from ..core.services.feature_state_service import FeatureScope, FeatureStatus

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


def _init_state_coordinator(project_root: Path) -> StateCoordinator:
    """Initialize StateCoordinator."""
    db_path = project_root / ".gao-dev" / "documents.db"

    # Create .gao-dev directory if it doesn't exist
    db_path.parent.mkdir(parents=True, exist_ok=True)

    coordinator = StateCoordinator(
        db_path=db_path,
        project_root=project_root
    )

    return coordinator


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
def list_features(scope: Optional[str], status: Optional[str]):
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
        scope_filter = FeatureScope[scope.upper()] if scope else None
        status_filter = FeatureStatus[status.upper()] if status else None

        features = coordinator.list_features(
            scope=scope_filter,
            status=status_filter
        )

        # Display results
        if not features:
            if RICH_AVAILABLE:
                console.print("\n[yellow]No features found.[/yellow]")
                console.print("\nCreate a feature with: [bold]gao-dev create-feature <name>[/bold]\n")
            else:
                click.echo("\nNo features found.")
                click.echo("\nCreate a feature with: gao-dev create-feature <name>\n")
            return

        # Create Rich table or plain text
        if RICH_AVAILABLE:
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
        else:
            # Plain text output
            click.echo(f"\nFeatures ({len(features)} total)")
            click.echo("-" * 80)
            click.echo(f"{'Name':<30} {'Scope':<10} {'Status':<12} {'Scale':<8} {'Owner':<15} {'Created'}")
            click.echo("-" * 80)
            for feature in features:
                click.echo(
                    f"{feature.name:<30} "
                    f"{feature.scope.value:<10} "
                    f"{feature.status.value:<12} "
                    f"{feature.scale_level:<8} "
                    f"{(feature.owner or '—'):<15} "
                    f"{feature.created_at[:10]}"
                )
            click.echo()

    except ValueError as e:
        if RICH_AVAILABLE:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
        else:
            click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()
    except Exception as e:
        logger.error("Failed to list features", error=str(e), exc_info=True)
        if RICH_AVAILABLE:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
        else:
            click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

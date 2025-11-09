"""CLI commands for learning management."""

import click
from pathlib import Path

try:
    from rich.console import Console
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from ..core.services.learning_maintenance_job import LearningMaintenanceJob


# Initialize console for rich output
if RICH_AVAILABLE:
    console = Console()


def get_db_path() -> Path:
    """
    Get database path.

    Returns:
        Path to documents.db

    Raises:
        click.ClickException: If database not found
    """
    from ..core.config import get_database_path

    db_path = get_database_path()
    if not db_path.exists():
        raise click.ClickException(
            f"State database not found: {db_path}\n"
            f"Run 'gao-dev state init' to create database."
        )
    return db_path


@click.group()
def learning():
    """Manage learning index and maintenance."""
    pass


@learning.command()
@click.option("--dry-run", is_flag=True, help="Preview changes without committing")
@click.option("--verbose", is_flag=True, help="Show detailed output")
def maintain(dry_run: bool, verbose: bool):
    """
    Run learning maintenance job.

    Performs:
    - Decay factor updates (smooth exponential)
    - Low confidence deactivation (confidence < 0.2, success_rate < 0.3, apps >= 5)
    - Supersede outdated learnings (same category, newer > old + 0.2)
    - Prune old applications (>1 year)

    Performance target: <5 seconds for 1000 learnings
    """
    db_path = get_db_path()

    mode_str = "[DRY RUN] " if dry_run else ""
    click.echo(f"{mode_str}Running learning maintenance job...")

    try:
        job = LearningMaintenanceJob(db_path=db_path)
        report = job.run_maintenance(dry_run=dry_run, verbose=verbose)

        # Display results
        if RICH_AVAILABLE:
            _display_rich_report(report, dry_run)
        else:
            _display_plain_report(report, dry_run)

        # Performance check
        if report.execution_time_ms > 5000:
            click.echo(
                f"\n[WARNING] Maintenance took {report.execution_time_ms:.0f}ms "
                f"(target: <5000ms)",
                err=True,
            )

        if dry_run:
            click.echo("\n[INFO] Dry run completed - no changes were made")

    except Exception as e:
        raise click.ClickException(f"Maintenance failed: {e}")


def _display_rich_report(report, dry_run: bool):
    """Display maintenance report using rich formatting."""
    table = Table(title="Learning Maintenance Report" + (" [DRY RUN]" if dry_run else ""))

    table.add_column("Operation", style="cyan")
    table.add_column("Count", justify="right", style="green")

    table.add_row("Decay updates", str(report.decay_updates))
    table.add_row("Deactivated learnings", str(report.deactivated_count))
    table.add_row("Superseded learnings", str(report.superseded_count))
    table.add_row("Pruned applications", str(report.pruned_applications))
    table.add_row("Execution time (ms)", f"{report.execution_time_ms:.2f}")

    console.print(table)


def _display_plain_report(report, dry_run: bool):
    """Display maintenance report using plain text."""
    mode = "[DRY RUN] " if dry_run else ""
    click.echo(f"\n{mode}Maintenance Report:")
    click.echo(f"  Decay updates:         {report.decay_updates}")
    click.echo(f"  Deactivated learnings: {report.deactivated_count}")
    click.echo(f"  Superseded learnings:  {report.superseded_count}")
    click.echo(f"  Pruned applications:   {report.pruned_applications}")
    click.echo(f"  Execution time:        {report.execution_time_ms:.2f}ms")

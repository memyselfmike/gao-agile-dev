"""CLI commands for database migration management."""

import click
from pathlib import Path
from typing import Optional
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from ..core.context.migrations import MigrationRunner

console = Console()


@click.group()
def db():
    """Database migration management commands."""
    pass


@db.command("migrate")
@click.option("--target", type=int, help="Target version (default: latest)")
@click.option("--db-path", type=click.Path(), help="Database path (default: ./gao_dev.db)")
@click.option("--dry-run", is_flag=True, help="Show pending migrations without applying")
def migrate(target: Optional[int], db_path: Optional[str], dry_run: bool):
    """
    Apply pending database migrations.

    Examples:
        gao-dev db migrate                    # Apply all pending migrations
        gao-dev db migrate --target 3         # Migrate to version 3
        gao-dev db migrate --dry-run          # Show what would be applied
    """
    try:
        # Determine database path
        if db_path:
            target_db = Path(db_path)
        else:
            target_db = Path.cwd() / "gao_dev.db"

        # Create migration runner
        runner = MigrationRunner(target_db)

        # Get pending migrations
        pending = runner.get_pending_migrations()

        if target is not None:
            pending = [m for m in pending if m.version <= target]

        if not pending:
            console.print("[green]No pending migrations[/green]")
            return

        # Show pending migrations
        console.print(Panel(
            f"[bold cyan]Pending Migrations[/bold cyan]\n"
            f"Database: [yellow]{target_db}[/yellow]",
            box=box.ROUNDED
        ))

        table = Table(title=f"{len(pending)} Pending Migrations", box=box.ROUNDED)
        table.add_column("Version", style="cyan", justify="center")
        table.add_column("Name", style="white")
        table.add_column("Status", style="yellow")

        for migration in pending:
            table.add_row(
                f"{migration.version:03d}",
                migration.name,
                "pending"
            )

        console.print(table)

        # Exit if dry-run
        if dry_run:
            console.print("\n[yellow]Dry-run mode: No migrations applied[/yellow]")
            return

        # Confirm before applying
        if not click.confirm("\nApply these migrations?"):
            console.print("[yellow]Migration cancelled[/yellow]")
            return

        # Apply migrations
        console.print("\n[cyan]Applying migrations...[/cyan]\n")

        with console.status("[bold cyan]Running migrations..."):
            applied = runner.migrate(target_version=target)

        # Show results
        if applied:
            console.print(Panel(
                f"[bold green]Migrations Applied Successfully[/bold green]\n"
                f"Applied [yellow]{len(applied)}[/yellow] migrations",
                box=box.ROUNDED
            ))

            # Show applied migrations
            table = Table(title="Applied Migrations", box=box.SIMPLE)
            table.add_column("Version", style="cyan", justify="center")
            table.add_column("Name", style="white")
            table.add_column("Applied At", style="green")

            for migration in applied:
                applied_time = migration.applied_at[:19] if migration.applied_at else "N/A"
                table.add_row(
                    f"{migration.version:03d}",
                    migration.name,
                    applied_time
                )

            console.print(table)
        else:
            console.print("[yellow]No migrations applied[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@db.command("rollback")
@click.option("--steps", type=int, default=1, help="Number of migrations to rollback")
@click.option("--db-path", type=click.Path(), help="Database path (default: ./gao_dev.db)")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
def rollback(steps: int, db_path: Optional[str], confirm: bool):
    """
    Rollback last N migrations.

    Examples:
        gao-dev db rollback                   # Rollback last migration
        gao-dev db rollback --steps 2         # Rollback last 2 migrations
        gao-dev db rollback --confirm         # Skip confirmation
    """
    try:
        # Determine database path
        if db_path:
            target_db = Path(db_path)
        else:
            target_db = Path.cwd() / "gao_dev.db"

        # Create migration runner
        runner = MigrationRunner(target_db)

        # Get applied migrations
        all_migrations = runner.get_migration_status()
        applied = [m for m in all_migrations if m.is_applied]

        if not applied:
            console.print("[yellow]No migrations to rollback[/yellow]")
            return

        # Determine which migrations will be rolled back
        applied.reverse()  # Most recent first
        to_rollback = applied[:steps]

        # Show migrations to rollback
        console.print(Panel(
            f"[bold yellow]Rollback Migrations[/bold yellow]\n"
            f"Database: [yellow]{target_db}[/yellow]",
            box=box.ROUNDED
        ))

        table = Table(title=f"{len(to_rollback)} Migrations to Rollback", box=box.ROUNDED)
        table.add_column("Version", style="cyan", justify="center")
        table.add_column("Name", style="white")
        table.add_column("Applied At", style="yellow")

        for migration in to_rollback:
            applied_time = migration.applied_at[:19] if migration.applied_at else "N/A"
            table.add_row(
                f"{migration.version:03d}",
                migration.name,
                applied_time
            )

        console.print(table)

        # Confirm before rolling back
        if not confirm:
            console.print("\n[bold red]WARNING: Rollback will undo schema changes and may result in data loss![/bold red]")
            if not click.confirm("\nProceed with rollback?"):
                console.print("[yellow]Rollback cancelled[/yellow]")
                return

        # Execute rollback
        console.print("\n[cyan]Rolling back migrations...[/cyan]\n")

        with console.status("[bold cyan]Executing rollback..."):
            rolled_back = runner.rollback(steps=steps)

        # Show results
        if rolled_back:
            console.print(Panel(
                f"[bold green]Rollback Completed Successfully[/bold green]\n"
                f"Rolled back [yellow]{len(rolled_back)}[/yellow] migrations",
                box=box.ROUNDED
            ))

            # Show rolled back migrations
            table = Table(title="Rolled Back Migrations", box=box.SIMPLE)
            table.add_column("Version", style="cyan", justify="center")
            table.add_column("Name", style="white")
            table.add_column("Status", style="green")

            for migration in rolled_back:
                table.add_row(
                    f"{migration.version:03d}",
                    migration.name,
                    "rolled back"
                )

            console.print(table)
        else:
            console.print("[yellow]No migrations rolled back[/yellow]")

    except NotImplementedError as e:
        console.print(f"[red]Rollback not supported: {e}[/red]")
        console.print("[yellow]Note: Some migrations may not implement rollback functionality[/yellow]")
        raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@db.command("status")
@click.option("--db-path", type=click.Path(), help="Database path (default: ./gao_dev.db)")
@click.option("--verbose", is_flag=True, help="Show detailed information")
def status(db_path: Optional[str], verbose: bool):
    """
    Show database migration status.

    Examples:
        gao-dev db status                     # Show migration status
        gao-dev db status --verbose           # Show detailed information
    """
    try:
        # Determine database path
        if db_path:
            target_db = Path(db_path)
        else:
            target_db = Path.cwd() / "gao_dev.db"

        # Create migration runner
        runner = MigrationRunner(target_db)

        # Get migration status
        all_migrations = runner.get_migration_status()
        current_version = runner.get_current_version()

        if not all_migrations:
            console.print("[yellow]No migrations found[/yellow]")
            return

        # Count applied and pending
        applied = [m for m in all_migrations if m.is_applied]
        pending = [m for m in all_migrations if not m.is_applied]

        # Show header
        console.print(Panel(
            f"[bold cyan]Database Migration Status[/bold cyan]\n"
            f"Database: [yellow]{target_db}[/yellow]\n"
            f"Current Version: [green]{current_version if current_version else 'N/A'}[/green]",
            box=box.ROUNDED
        ))

        # Show summary
        summary_table = Table(title="Summary", box=box.SIMPLE)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Count", style="yellow", justify="right")

        summary_table.add_row("Total Migrations", str(len(all_migrations)))
        summary_table.add_row("Applied", str(len(applied)))
        summary_table.add_row("Pending", str(len(pending)))

        console.print(summary_table)

        # Show all migrations
        console.print()
        migrations_table = Table(title="Migrations", box=box.ROUNDED)
        migrations_table.add_column("Version", style="cyan", justify="center")
        migrations_table.add_column("Name", style="white")
        migrations_table.add_column("Status", style="yellow")
        if verbose:
            migrations_table.add_column("Applied At", style="green")

        for migration in all_migrations:
            status_emoji = "[green]applied[/green]" if migration.is_applied else "[yellow]pending[/yellow]"

            if verbose and migration.is_applied:
                applied_time = migration.applied_at[:19] if migration.applied_at else "N/A"
                migrations_table.add_row(
                    f"{migration.version:03d}",
                    migration.name,
                    status_emoji,
                    applied_time
                )
            else:
                migrations_table.add_row(
                    f"{migration.version:03d}",
                    migration.name,
                    status_emoji
                )

        console.print(migrations_table)

        # Show pending migrations prominently if any
        if pending:
            console.print()
            console.print(Panel(
                f"[bold yellow]{len(pending)} pending migrations[/bold yellow]\n"
                f"Run [cyan]gao-dev db migrate[/cyan] to apply",
                box=box.ROUNDED
            ))

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@db.command("validate")
@click.option("--db-path", type=click.Path(), help="Database path (default: ./gao_dev.db)")
def validate(db_path: Optional[str]):
    """
    Validate migration files for common issues.

    Examples:
        gao-dev db validate
    """
    try:
        # Determine database path
        if db_path:
            target_db = Path(db_path)
        else:
            target_db = Path.cwd() / "gao_dev.db"

        # Create migration runner
        runner = MigrationRunner(target_db)

        # Validate migrations
        console.print("[cyan]Validating migration files...[/cyan]\n")

        is_valid, errors = runner.validate_migrations()

        if is_valid:
            console.print(Panel(
                "[bold green]All migrations are valid[/bold green]",
                box=box.ROUNDED
            ))
        else:
            console.print(Panel(
                f"[bold red]Validation Failed[/bold red]\n"
                f"Found [yellow]{len(errors)}[/yellow] issues",
                box=box.ROUNDED
            ))

            console.print("\n[bold red]Errors:[/bold red]")
            for error in errors:
                console.print(f"  - {error}")

            raise click.Abort()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()

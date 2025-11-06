"""CLI commands for state management."""

import click
import json
import csv
import sys
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from ..core.state.state_tracker import StateTracker
from ..core.state.query_builder import QueryBuilder
from ..core.state.markdown_syncer import MarkdownSyncer
from ..core.state.importer import StateImporter
from ..core.state.exceptions import RecordNotFoundError


# Initialize console for rich output
if RICH_AVAILABLE:
    console = Console()


def get_state_tracker() -> StateTracker:
    """Get StateTracker instance.

    Returns:
        StateTracker instance for unified database

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
    return StateTracker(db_path)


@click.group()
def state():
    """Manage GAO-Dev state database."""
    pass


@state.command()
@click.option("--force", is_flag=True, help="Overwrite existing database")
@click.option("--migrate", is_flag=True, help="Migrate data from legacy databases")
def init(force: bool, migrate: bool):
    """Initialize unified state database."""
    from ..core.config import get_database_path, get_legacy_state_db_path, get_legacy_context_db_path

    db_path = get_database_path()
    legacy_state_db = get_legacy_state_db_path()
    legacy_context_db = get_legacy_context_db_path()

    if db_path.exists() and not force:
        click.echo(
            f"Database already exists: {db_path}\n"
            f"Use --force to overwrite."
        )
        return

    # Delete existing if force
    if force and db_path.exists():
        db_path.unlink()

    # Create schema using migrations
    from ..core.state.migrations.migration_001_create_state_schema import Migration001
    from ..core.context.migrations.migration_003_unify_database import Migration003

    try:
        # Create base state schema
        Migration001.upgrade(db_path)
        click.echo(f"[OK] Base schema created: {db_path}")

        # Run unification migration to add context tables and migrate data
        if migrate and (legacy_state_db.exists() or legacy_context_db.exists()):
            click.echo("[INFO] Migrating data from legacy databases...")
            Migration003.upgrade(db_path, backup=True)
            click.echo("[OK] Data migration completed")
            click.echo(f"[INFO] Legacy database backups created in .gao/backups/")
        else:
            # Just create the schema without migrating data
            Migration003.upgrade(db_path, backup=False)
            click.echo("[OK] Context tables created")

        click.echo(f"[OK] Unified database initialized: {db_path}")
    except Exception as e:
        raise click.ClickException(f"Failed to initialize database: {e}")


@state.command()
@click.argument("epic", type=int)
@click.argument("story", type=int)
@click.option("--format", type=click.Choice(["table", "json", "csv"]), default="table")
def story(epic: int, story: int, format: str):
    """Show story details.

    EPIC: Epic number
    STORY: Story number
    """
    try:
        tracker = get_state_tracker()
        story_obj = tracker.get_story(epic, story)

        if format == "json":
            data = {
                "id": story_obj.id,
                "epic": story_obj.epic,
                "story_num": story_obj.story_num,
                "full_id": story_obj.full_id,
                "title": story_obj.title,
                "status": story_obj.status,
                "owner": story_obj.owner,
                "points": story_obj.points,
                "priority": story_obj.priority,
                "sprint": story_obj.sprint,
                "created_at": story_obj.created_at,
                "updated_at": story_obj.updated_at,
            }
            click.echo(json.dumps(data, indent=2))

        elif format == "csv":
            writer = csv.writer(sys.stdout)
            writer.writerow([
                "id", "epic", "story_num", "full_id", "title", "status",
                "owner", "points", "priority", "sprint", "created_at", "updated_at"
            ])
            writer.writerow([
                story_obj.id, story_obj.epic, story_obj.story_num, story_obj.full_id,
                story_obj.title, story_obj.status, story_obj.owner, story_obj.points,
                story_obj.priority, story_obj.sprint, story_obj.created_at,
                story_obj.updated_at
            ])

        else:  # table
            if RICH_AVAILABLE:
                table = Table(title=f"Story {story_obj.full_id}")
                table.add_column("Field", style="cyan")
                table.add_column("Value", style="white")

                # Add status with color
                status_color = _get_status_color(story_obj.status)

                table.add_row("ID", str(story_obj.id))
                table.add_row("Epic", str(story_obj.epic))
                table.add_row("Story Number", str(story_obj.story_num))
                table.add_row("Full ID", story_obj.full_id)
                table.add_row("Title", story_obj.title)
                table.add_row("Status", f"[{status_color}]{story_obj.status}[/{status_color}]")
                table.add_row("Owner", story_obj.owner or "Unassigned")
                table.add_row("Points", str(story_obj.points))
                table.add_row("Priority", story_obj.priority)
                table.add_row("Sprint", str(story_obj.sprint) if story_obj.sprint else "Unassigned")
                table.add_row("Created", story_obj.created_at)
                table.add_row("Updated", story_obj.updated_at)

                console.print(table)
            else:
                click.echo(f"\nStory {story_obj.full_id}:")
                click.echo(f"  Title: {story_obj.title}")
                click.echo(f"  Status: {story_obj.status}")
                click.echo(f"  Owner: {story_obj.owner or 'Unassigned'}")
                click.echo(f"  Points: {story_obj.points}")
                click.echo(f"  Priority: {story_obj.priority}")
                click.echo(f"  Sprint: {story_obj.sprint or 'Unassigned'}")
                click.echo(f"  Created: {story_obj.created_at}")
                click.echo(f"  Updated: {story_obj.updated_at}")

    except RecordNotFoundError as e:
        raise click.ClickException(str(e))


@state.command()
@click.argument("epic_num", type=int)
@click.option("--format", type=click.Choice(["table", "json", "csv"]), default="table")
def epic(epic_num: int, format: str):
    """Show epic progress.

    EPIC_NUM: Epic number
    """
    try:
        tracker = get_state_tracker()
        builder = QueryBuilder(tracker)

        progress = builder.get_epic_summary(epic_num)

        if format == "json":
            click.echo(json.dumps(progress, indent=2))

        elif format == "csv":
            writer = csv.writer(sys.stdout)
            writer.writerow(progress.keys())
            writer.writerow(progress.values())

        else:  # table
            if RICH_AVAILABLE:
                table = Table(title=f"Epic {epic_num}: {progress['title']}")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="white")

                table.add_row("Feature", progress["feature"])
                table.add_row("Status", progress["status"])
                table.add_row("Progress", f"{progress['progress']:.1f}%")
                table.add_row("Total Points", str(progress["total_points"]))
                table.add_row("Completed Points", str(progress["completed_points"]))
                table.add_row("Stories Total", str(progress["stories_total"]))
                table.add_row("Stories Done", f"[green]{progress['stories_done']}[/green]")
                table.add_row("Stories In Progress", f"[yellow]{progress['stories_in_progress']}[/yellow]")
                table.add_row("Stories Blocked", f"[red]{progress['stories_blocked']}[/red]")
                table.add_row("Stories Pending", str(progress["stories_pending"]))
                table.add_row("Velocity", f"{progress['velocity']:.1%}")

                console.print(table)
            else:
                click.echo(f"\nEpic {epic_num}: {progress['title']}")
                click.echo(f"  Feature: {progress['feature']}")
                click.echo(f"  Status: {progress['status']}")
                click.echo(f"  Progress: {progress['progress']:.1f}%")
                click.echo(f"  Total Points: {progress['total_points']}")
                click.echo(f"  Completed Points: {progress['completed_points']}")
                click.echo(f"  Stories: {progress['stories_done']}/{progress['stories_total']} done")
                click.echo(f"  Velocity: {progress['velocity']:.1%}")

    except RecordNotFoundError as e:
        raise click.ClickException(str(e))


@state.command()
@click.argument("sprint_num", type=int, required=False)
@click.option("--format", type=click.Choice(["table", "json", "csv"]), default="table")
def sprint(sprint_num: Optional[int], format: str):
    """Show sprint details.

    SPRINT_NUM: Sprint number (optional, shows current sprint if not specified)
    """
    try:
        tracker = get_state_tracker()
        builder = QueryBuilder(tracker)

        # Get current sprint if not specified
        if sprint_num is None:
            current = tracker.get_current_sprint()
            if not current:
                raise click.ClickException("No active sprint found")
            sprint_num = current.sprint_num

        summary = builder.get_sprint_summary(sprint_num)

        if format == "json":
            click.echo(json.dumps(summary, indent=2))

        elif format == "csv":
            writer = csv.writer(sys.stdout)
            writer.writerow(summary.keys())
            writer.writerow(summary.values())

        else:  # table
            if RICH_AVAILABLE:
                table = Table(title=f"{summary['sprint_name']}")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="white")

                # Progress bar for completion
                completion_pct = summary["completion_rate"] * 100

                table.add_row("Sprint Number", str(summary["sprint_num"]))
                table.add_row("Velocity", f"{summary['velocity']} points")
                table.add_row("Total Points", str(summary["total_points"]))
                table.add_row("Completed Points", f"[green]{summary['completed_points']}[/green]")
                table.add_row("Remaining Points", str(summary["remaining_points"]))
                table.add_row("Completion Rate", f"{completion_pct:.1f}%")
                table.add_row("Stories Total", str(summary["stories_total"]))
                table.add_row("Stories Done", f"[green]{summary['stories_done']}[/green]")
                table.add_row("Stories In Progress", f"[yellow]{summary['stories_in_progress']}[/yellow]")
                table.add_row("Stories Blocked", f"[red]{summary['stories_blocked']}[/red]")

                console.print(table)
            else:
                click.echo(f"\n{summary['sprint_name']}")
                click.echo(f"  Velocity: {summary['velocity']} points")
                click.echo(f"  Total Points: {summary['total_points']}")
                click.echo(f"  Completed: {summary['completed_points']} points")
                click.echo(f"  Remaining: {summary['remaining_points']} points")
                click.echo(f"  Stories: {summary['stories_done']}/{summary['stories_total']} done")

    except RecordNotFoundError as e:
        raise click.ClickException(str(e))


@state.command()
@click.option("--stories-dir", multiple=True, type=click.Path(exists=True, path_type=Path))
def sync(stories_dir):
    """Manually trigger markdown sync."""
    try:
        tracker = get_state_tracker()
        syncer = MarkdownSyncer(tracker)

        # Default to docs/features if not specified
        if not stories_dir:
            stories_dir = [Path.cwd() / "docs" / "features"]

        total_created = 0
        total_updated = 0
        total_skipped = 0
        total_errors = 0

        for dir_path in stories_dir:
            if not dir_path.exists():
                click.echo(f"[WARNING] Directory not found: {dir_path}")
                continue

            click.echo(f"Syncing {dir_path}...")
            report = syncer.sync_directory(dir_path)

            total_created += report.stories_created
            total_updated += report.stories_updated
            total_skipped += report.files_skipped
            total_errors += len(report.errors)

            if report.errors:
                click.echo(f"  Errors: {len(report.errors)}")
                for error in report.errors:
                    click.echo(f"    - {error}")

        click.echo(f"\n[OK] Sync complete:")
        click.echo(f"  Created: {total_created}")
        click.echo(f"  Updated: {total_updated}")
        click.echo(f"  Skipped: {total_skipped}")
        click.echo(f"  Errors: {total_errors}")

    except Exception as e:
        raise click.ClickException(f"Sync failed: {e}")


@state.command()
@click.argument("query")
def query(query: str):
    """Execute custom SQL query (read-only).

    QUERY: SQL query to execute
    """
    try:
        tracker = get_state_tracker()

        # Verify read-only
        if any(keyword in query.upper() for keyword in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER"]):
            raise click.ClickException("Only SELECT queries are allowed")

        with tracker._get_connection() as conn:
            cursor = conn.execute(query)
            rows = cursor.fetchall()

            if not rows:
                click.echo("No results")
                return

            # Get column names
            columns = [description[0] for description in cursor.description]

            if RICH_AVAILABLE:
                table = Table()
                for col in columns:
                    table.add_column(col, style="cyan")

                for row in rows:
                    table.add_row(*[str(val) for val in row])

                console.print(table)
            else:
                # Simple table output
                click.echo("\t".join(columns))
                click.echo("-" * 80)
                for row in rows:
                    click.echo("\t".join(str(val) for val in row))

    except Exception as e:
        raise click.ClickException(f"Query failed: {e}")


@state.command()
@click.option("--sprint-status", type=click.Path(exists=True, path_type=Path))
@click.option("--stories-dir", multiple=True, type=click.Path(exists=True, path_type=Path))
@click.option("--dry-run", is_flag=True, help="Preview import without committing")
@click.option("--no-backup", is_flag=True, help="Skip backup creation")
def import_data(sprint_status, stories_dir, dry_run, no_backup):
    """Import existing data from markdown/YAML files."""
    try:
        tracker = get_state_tracker()
        importer = StateImporter(tracker, dry_run=dry_run)

        # Default paths
        if not sprint_status:
            sprint_status = Path.cwd() / "docs" / "sprint-status.yaml"

        if not stories_dir:
            stories_dir = [Path.cwd() / "docs" / "features"]

        click.echo("Starting import...")
        if dry_run:
            click.echo("[DRY RUN] No changes will be committed")

        # Run import
        report = importer.import_all(
            sprint_status,
            list(stories_dir),
            create_backup=not no_backup,
        )

        click.echo(f"\n{report}")

        if report.errors:
            click.echo("\nErrors:")
            for error in report.errors:
                click.echo(f"  - {error}")

        if report.warnings:
            click.echo("\nWarnings:")
            for warning in report.warnings:
                click.echo(f"  - {warning}")

        if report.validation_errors:
            click.echo("\nValidation Errors:")
            for error in report.validation_errors:
                click.echo(f"  - {error}")

        if dry_run:
            click.echo("\n[DRY RUN] No changes were committed")
        else:
            click.echo("\n[OK] Import complete")

    except Exception as e:
        raise click.ClickException(f"Import failed: {e}")


@state.command()
def dashboard():
    """Show interactive dashboard (requires rich)."""
    if not RICH_AVAILABLE:
        raise click.ClickException(
            "Rich library not installed. Install with: pip install rich"
        )

    try:
        tracker = get_state_tracker()
        builder = QueryBuilder(tracker)

        # Get all active work
        work = builder.get_all_active_work()

        console.print("\n[bold cyan]GAO-Dev State Dashboard[/bold cyan]\n")

        # Stories in progress
        if work["stories_in_progress"]:
            table = Table(title="Stories In Progress")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="white")
            table.add_column("Owner", style="yellow")
            table.add_column("Points", style="green")

            for story in work["stories_in_progress"]:
                table.add_row(
                    story["full_id"],
                    story["title"],
                    story["owner"] or "Unassigned",
                    str(story["points"]),
                )

            console.print(table)
            console.print()

        # Blocked stories
        if work["stories_blocked"]:
            table = Table(title="Blocked Stories")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="white")
            table.add_column("Owner", style="yellow")

            for story in work["stories_blocked"]:
                table.add_row(
                    story["full_id"],
                    story["title"],
                    story["owner"] or "Unassigned",
                )

            console.print(table)
            console.print()

        # Active epics
        if work["active_epics"]:
            table = Table(title="Active Epics")
            table.add_column("Epic", style="cyan")
            table.add_column("Title", style="white")
            table.add_column("Progress", style="green")
            table.add_column("Stories", style="yellow")

            for epic in work["active_epics"]:
                table.add_row(
                    str(epic["epic_num"]),
                    epic["title"],
                    f"{epic['progress']:.1f}%",
                    f"{epic['completed_points']}/{epic['total_points']} pts",
                )

            console.print(table)
            console.print()

        # Current sprint
        if work.get("current_sprint"):
            sprint_data = work["current_sprint"]
            table = Table(title=sprint_data["sprint_name"])
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white")

            table.add_row("Velocity", f"{sprint_data['velocity']} points")
            table.add_row("Completion", f"{sprint_data['completion_rate'] * 100:.1f}%")
            table.add_row("Stories Done", f"{sprint_data['stories_done']}/{sprint_data['stories_total']}")

            console.print(table)

    except Exception as e:
        raise click.ClickException(f"Dashboard failed: {e}")


def _get_status_color(status: str) -> str:
    """Get color for status.

    Args:
        status: Story status

    Returns:
        Rich color name
    """
    colors = {
        "done": "green",
        "in_progress": "yellow",
        "blocked": "red",
        "pending": "white",
        "cancelled": "dim",
    }
    return colors.get(status, "white")

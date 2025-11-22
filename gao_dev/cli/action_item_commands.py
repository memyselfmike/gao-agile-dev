"""CLI commands for action item management."""

import click
from typing import Optional

try:
    from rich.console import Console
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from ..core.services.action_item_integration_service import (
    ActionItemIntegrationService,
    ActionItemPriority
)
from ..core.git_manager import GitManager
from ...lifecycle.exceptions import MaxConversionsExceededError

# Initialize console for rich output
if RICH_AVAILABLE:
    console = Console()


def get_service() -> ActionItemIntegrationService:
    """
    Get ActionItemIntegrationService instance.

    Returns:
        ActionItemIntegrationService for current project

    Raises:
        click.ClickException: If database not found
    """
    from ..core.config import get_database_path
    from .project_detection import find_project_root

    project_root = find_project_root()
    db_path = get_database_path()

    if not db_path.exists():
        raise click.ClickException(
            f"State database not found: {db_path}\n"
            f"Run 'gao-dev state init' to create database."
        )

    git_manager = GitManager(repo_path=project_root)

    return ActionItemIntegrationService(
        db_path=db_path,
        project_root=project_root,
        git_manager=git_manager
    )


@click.group(name="action-items")
def action_items():
    """Manage action items from ceremonies."""
    pass


@action_items.command()
@click.option("--epic", type=int, help="Filter by epic number")
@click.option("--priority", type=click.Choice(["critical", "high", "medium", "low"]), help="Filter by priority")
@click.option("--pending", is_flag=True, help="Show only pending items")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def list(epic: Optional[int], priority: Optional[str], pending: bool, format: str):
    """List action items with conversion eligibility.

    Examples:
        gao-dev action-items list --epic 5 --pending
        gao-dev action-items list --priority critical
        gao-dev action-items list --format json
    """
    service = get_service()

    # Convert priority string to enum
    priority_enum = ActionItemPriority[priority.upper()] if priority else None

    # Get action items
    if pending:
        items = service.get_pending_action_items(epic_num=epic, priority=priority_enum)
    else:
        # For non-pending, we need to query directly from action_service
        items = service.action_service.get_active(assignee=None)
        if epic:
            items = [item for item in items if item.get("epic_num") == epic]
        if priority_enum:
            items = [item for item in items if item.get("priority") == priority_enum.value]

    if format == "json":
        import json
        click.echo(json.dumps(items, indent=2, default=str))
        return

    # Table format (Rich or fallback)
    if RICH_AVAILABLE:
        table = Table(title="Action Items")
        table.add_column("ID", style="cyan")
        table.add_column("Epic", style="magenta")
        table.add_column("Priority", style="yellow")
        table.add_column("Title", style="white")
        table.add_column("Status", style="green")
        table.add_column("Age (days)", style="blue")
        table.add_column("Eligible", style="red")

        for item in items:
            # Calculate age
            from datetime import datetime
            created_at = datetime.fromisoformat(item["created_at"])
            age_days = (datetime.now() - created_at).days

            # Check conversion eligibility
            epic_num = item.get("epic_num")
            eligible = "No"
            if item.get("priority") == "critical" and epic_num:
                try:
                    has_converted = service._has_converted_action_item(epic_num)
                    eligible = "No (limit)" if has_converted else "Yes"
                except Exception:
                    eligible = "Unknown"

            table.add_row(
                str(item["id"]),
                str(item.get("epic_num", "N/A")),
                item.get("priority", "medium"),
                item.get("title", "")[:50],
                item.get("status", "pending"),
                str(age_days),
                eligible
            )

        console.print(table)
    else:
        # Fallback ASCII table
        click.echo(f"{'ID':<5} {'Epic':<6} {'Priority':<10} {'Title':<40} {'Status':<12} {'Age':<8} {'Eligible':<10}")
        click.echo("-" * 100)
        for item in items:
            from datetime import datetime
            created_at = datetime.fromisoformat(item["created_at"])
            age_days = (datetime.now() - created_at).days

            epic_num = item.get("epic_num")
            eligible = "No"
            if item.get("priority") == "critical" and epic_num:
                try:
                    has_converted = service._has_converted_action_item(epic_num)
                    eligible = "No (limit)" if has_converted else "Yes"
                except Exception:
                    eligible = "Unknown"

            click.echo(
                f"{item['id']:<5} "
                f"{str(item.get('epic_num', 'N/A')):<6} "
                f"{item.get('priority', 'medium'):<10} "
                f"{item.get('title', '')[:40]:<40} "
                f"{item.get('status', 'pending'):<12} "
                f"{age_days:<8} "
                f"{eligible:<10}"
            )

    click.echo(f"\nTotal items: {len(items)}")
    service.close()


@action_items.command()
@click.argument("item_id", type=int)
@click.option("--epic", type=int, help="Epic number to add story to")
@click.option("--force", is_flag=True, help="Force conversion even if C8 limit reached")
def promote(item_id: int, epic: Optional[int], force: bool):
    """Manually promote action item to story.

    Bypasses C8 limit if --force is used.

    Examples:
        gao-dev action-items promote 5 --epic 1
        gao-dev action-items promote 10 --epic 2 --force
    """
    service = get_service()

    try:
        # Get action item to determine epic if not provided
        action_item = service.action_service.get(item_id)

        if not epic:
            epic = action_item.get("epic_num")
            if not epic:
                raise click.ClickException(
                    f"Action item {item_id} has no epic number. "
                    f"Specify --epic to set target epic."
                )

        # Convert to story
        story_num = service.convert_to_story(
            action_item_id=item_id,
            epic_num=epic,
            manual_override=force
        )

        click.echo(
            f"[OK] Action item {item_id} converted to Story {epic}.{story_num}\n"
            f"Priority: {action_item.get('priority', 'unknown')}\n"
            f"Manual override: {force}"
        )

    except MaxConversionsExceededError as e:
        click.echo(
            f"[ERROR] {e}\n"
            f"Use --force to bypass C8 limit (max 1 conversion per epic).",
            err=True
        )
        raise click.Abort()
    except Exception as e:
        click.echo(f"[ERROR] Failed to promote action item: {e}", err=True)
        raise click.Abort()
    finally:
        service.close()


@action_items.command()
@click.argument("item_id", type=int)
@click.option("--reason", help="Completion reason")
def complete(item_id: int, reason: Optional[str]):
    """Mark action item as completed.

    Examples:
        gao-dev action-items complete 5
        gao-dev action-items complete 10 --reason "Fixed during Story 2.3"
    """
    service = get_service()

    try:
        service.mark_action_item_complete(
            action_item_id=item_id,
            completed_by="user",
            reason=reason
        )

        click.echo(
            f"[OK] Action item {item_id} marked as completed\n"
            f"Reason: {reason or 'None provided'}"
        )

    except Exception as e:
        click.echo(f"[ERROR] Failed to complete action item: {e}", err=True)
        raise click.Abort()
    finally:
        service.close()


@action_items.command()
@click.argument("item_id", type=int)
@click.option("--days", type=int, default=30, help="Number of days to defer (default: 30)")
def defer(item_id: int, days: int):
    """Defer action item by updating metadata.

    Examples:
        gao-dev action-items defer 5 --days 30
        gao-dev action-items defer 10 --days 60
    """
    service = get_service()

    try:
        # Get action item
        service.action_service.get(item_id)

        # Update metadata with defer date
        from datetime import datetime, timedelta
        defer_until = (datetime.now() + timedelta(days=days)).isoformat()

        # Update using raw SQL (action_service doesn't have update_metadata method)
        with service._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE action_items
                SET metadata = json_set(COALESCE(metadata, '{}'), '$.deferred_until', ?),
                    updated_at = ?
                WHERE id = ?
                """,
                (defer_until, datetime.now().isoformat(), item_id)
            )

        click.echo(
            f"[OK] Action item {item_id} deferred for {days} days\n"
            f"Review after: {defer_until[:10]}"
        )

    except Exception as e:
        click.echo(f"[ERROR] Failed to defer action item: {e}", err=True)
        raise click.Abort()
    finally:
        service.close()


@action_items.command()
@click.option("--days", type=int, default=30, help="Age threshold in days (default: 30)")
@click.option("--dry-run", is_flag=True, help="Show what would be completed without doing it")
def cleanup(days: int, dry_run: bool):
    """Auto-complete stale LOW priority items.

    Only affects LOW priority items older than threshold.

    Examples:
        gao-dev action-items cleanup --days 30
        gao-dev action-items cleanup --days 60 --dry-run
    """
    service = get_service()

    try:
        if dry_run:
            # Show what would be completed
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)

            with service._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, title, created_at FROM action_items
                    WHERE status IN ('pending', 'in_progress')
                      AND priority = 'low'
                      AND created_at < ?
                    """,
                    (cutoff_date.isoformat(),)
                )
                items = cursor.fetchall()

            click.echo(f"[DRY RUN] Would auto-complete {len(items)} LOW priority items:")
            for item in items:
                click.echo(f"  - {item['id']}: {item['title']} (created: {item['created_at'][:10]})")
        else:
            # Actually complete them
            count = service.auto_complete_stale_items(days_old=days)
            click.echo(
                f"[OK] Auto-completed {count} LOW priority items older than {days} days"
            )

    except Exception as e:
        click.echo(f"[ERROR] Failed to cleanup stale items: {e}", err=True)
        raise click.Abort()
    finally:
        service.close()

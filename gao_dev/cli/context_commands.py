"""CLI commands for context management."""

import json
import click
from typing import Optional
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich import box

from ..core.context.context_api import _get_global_cache, _get_global_tracker
from ..core.context.context_persistence import ContextPersistence
from ..core.context.context_lineage import ContextLineageTracker

console = Console()


@click.group()
def context():
    """Context management commands."""
    pass


@context.command("show")
@click.argument("workflow_id")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def show_context(workflow_id: str, json_output: bool):
    """
    Show context details for a workflow execution.

    Examples:
        gao-dev context show abc123
        gao-dev context show abc123 --json
    """
    try:
        persistence = ContextPersistence()
        ctx = persistence.load_context(workflow_id)

        if json_output:
            click.echo(ctx.to_json())
            return

        # Rich formatted output
        console.print(Panel(
            f"[bold cyan]Workflow Context[/bold cyan]\n"
            f"ID: [yellow]{ctx.workflow_id}[/yellow]",
            box=box.ROUNDED
        ))

        # Create details table
        table = Table(title="Context Details", box=box.SIMPLE)
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        table.add_row("Epic", str(ctx.epic_num))
        table.add_row("Story", str(ctx.story_num) if ctx.story_num else "N/A")
        table.add_row("Feature", ctx.feature)
        table.add_row("Workflow", ctx.workflow_name)
        table.add_row("Phase", ctx.current_phase)
        table.add_row("Status", ctx.status)
        table.add_row("Created", ctx.created_at)
        table.add_row("Updated", ctx.updated_at)

        console.print(table)

        # Show decisions if any
        if ctx.decisions:
            console.print("\n[bold cyan]Decisions:[/bold cyan]")
            decisions_table = Table(box=box.SIMPLE)
            decisions_table.add_column("Decision", style="yellow")
            decisions_table.add_column("Value", style="white")
            for key, value in ctx.decisions.items():
                decisions_table.add_row(key, str(value))
            console.print(decisions_table)

        # Show artifacts if any
        if ctx.artifacts:
            console.print("\n[bold cyan]Artifacts:[/bold cyan]")
            for artifact in ctx.artifacts:
                console.print(f"  - {artifact}")

        # Show errors if any
        if ctx.errors:
            console.print("\n[bold red]Errors:[/bold red]")
            for error in ctx.errors:
                console.print(f"  - {error}")

        # Show phase history
        if ctx.phase_history:
            console.print("\n[bold cyan]Phase History:[/bold cyan]")
            history_table = Table(box=box.SIMPLE)
            history_table.add_column("Phase", style="cyan")
            history_table.add_column("Timestamp", style="white")
            history_table.add_column("Duration (s)", style="yellow", justify="right")
            for phase_transition in ctx.phase_history:
                duration = f"{phase_transition.duration:.2f}" if phase_transition.duration else "N/A"
                history_table.add_row(
                    phase_transition.phase,
                    phase_transition.timestamp,
                    duration
                )
            console.print(history_table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@context.command("list")
@click.option("--epic", type=int, help="Filter by epic number")
@click.option("--feature", help="Filter by feature name")
@click.option("--status", help="Filter by status (running, completed, failed)")
@click.option("--limit", type=int, default=20, help="Maximum number of results")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def list_contexts(epic: Optional[int], feature: Optional[str], status: Optional[str],
                  limit: int, json_output: bool):
    """
    List recent workflow contexts.

    Examples:
        gao-dev context list
        gao-dev context list --epic 17
        gao-dev context list --status running
        gao-dev context list --feature context-system --limit 10
    """
    try:
        persistence = ContextPersistence()

        # Build filters
        filters = {}
        if epic is not None:
            filters['epic_num'] = epic
        if feature:
            filters['feature'] = feature
        if status:
            filters['status'] = status

        # Query contexts
        contexts = persistence.search_contexts(filters=filters, limit=limit)

        if json_output:
            output = [ctx.to_dict() for ctx in contexts]
            click.echo(json.dumps(output, indent=2))
            return

        if not contexts:
            console.print("[yellow]No contexts found matching criteria[/yellow]")
            return

        # Rich formatted table
        table = Table(title=f"Recent Workflow Contexts ({len(contexts)} found)", box=box.ROUNDED)
        table.add_column("Workflow ID", style="cyan", no_wrap=True)
        table.add_column("Epic.Story", style="yellow", justify="center")
        table.add_column("Feature", style="white")
        table.add_column("Workflow", style="magenta")
        table.add_column("Phase", style="blue")
        table.add_column("Status", style="green")
        table.add_column("Updated", style="white")

        for ctx in contexts:
            story_id = f"{ctx.epic_num}.{ctx.story_num}" if ctx.story_num else f"{ctx.epic_num}"
            workflow_id_short = ctx.workflow_id[:8] + "..."

            # Color status
            status_style = {
                "running": "[yellow]running[/yellow]",
                "completed": "[green]completed[/green]",
                "failed": "[red]failed[/red]",
                "paused": "[blue]paused[/blue]"
            }.get(ctx.status, ctx.status)

            # Format updated time
            try:
                updated_dt = datetime.fromisoformat(ctx.updated_at)
                updated_str = updated_dt.strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                updated_str = ctx.updated_at[:16]

            table.add_row(
                workflow_id_short,
                story_id,
                ctx.feature,
                ctx.workflow_name,
                ctx.current_phase,
                status_style,
                updated_str
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@context.command("history")
@click.argument("epic", type=int)
@click.argument("story", type=int)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def show_history(epic: int, story: int, json_output: bool):
    """
    Show all context versions for a story.

    Examples:
        gao-dev context history 17 5
        gao-dev context history 17 5 --json
    """
    try:
        persistence = ContextPersistence()
        contexts = persistence.get_context_versions(epic_num=epic, story_num=story)

        if not contexts:
            console.print(f"[yellow]No context history found for Story {epic}.{story}[/yellow]")
            return

        if json_output:
            output = [ctx.to_dict() for ctx in contexts]
            click.echo(json.dumps(output, indent=2))
            return

        # Rich formatted output
        console.print(Panel(
            f"[bold cyan]Context History for Story {epic}.{story}[/bold cyan]\n"
            f"Total versions: [yellow]{len(contexts)}[/yellow]",
            box=box.ROUNDED
        ))

        # Create history table
        table = Table(title=f"Story {epic}.{story} - Context Versions", box=box.ROUNDED)
        table.add_column("#", style="cyan", justify="center")
        table.add_column("Workflow ID", style="yellow", no_wrap=True)
        table.add_column("Workflow", style="magenta")
        table.add_column("Phase", style="blue")
        table.add_column("Status", style="green")
        table.add_column("Created", style="white")
        table.add_column("Artifacts", style="cyan", justify="right")

        for idx, ctx in enumerate(contexts, 1):
            workflow_id_short = ctx.workflow_id[:8] + "..."

            # Color status
            status_style = {
                "running": "[yellow]running[/yellow]",
                "completed": "[green]completed[/green]",
                "failed": "[red]failed[/red]",
                "paused": "[blue]paused[/blue]"
            }.get(ctx.status, ctx.status)

            # Format created time
            try:
                created_dt = datetime.fromisoformat(ctx.created_at)
                created_str = created_dt.strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                created_str = ctx.created_at[:16]

            table.add_row(
                str(idx),
                workflow_id_short,
                ctx.workflow_name,
                ctx.current_phase,
                status_style,
                created_str,
                str(len(ctx.artifacts))
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@context.command("lineage")
@click.argument("epic", type=int)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def show_lineage(epic: int, json_output: bool):
    """
    Show document lineage for an epic.

    Examples:
        gao-dev context lineage 17
        gao-dev context lineage 17 --json
    """
    try:
        tracker = ContextLineageTracker()

        if json_output:
            report = tracker.generate_lineage_report(epic=epic, output_format="json")
            click.echo(report)
            return

        # Generate markdown report
        report = tracker.generate_lineage_report(epic=epic, output_format="markdown")

        # Display with syntax highlighting
        console.print(Panel(
            f"[bold cyan]Document Lineage - Epic {epic}[/bold cyan]",
            box=box.ROUNDED
        ))

        syntax = Syntax(report, "markdown", theme="monokai", line_numbers=False)
        console.print(syntax)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@context.command("stats")
@click.option("--workflow-id", help="Filter by workflow ID")
@click.option("--context-key", help="Filter by context key")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def show_stats(workflow_id: Optional[str], context_key: Optional[str], json_output: bool):
    """
    Show cache and usage statistics.

    Examples:
        gao-dev context stats
        gao-dev context stats --workflow-id abc123
        gao-dev context stats --context-key epic_definition
    """
    try:
        cache = _get_global_cache()
        tracker = _get_global_tracker()

        # Get cache statistics
        cache_stats = cache.get_statistics()

        # Get usage statistics
        usage_stats = tracker.get_cache_hit_rate(
            workflow_id=workflow_id,
            context_key=context_key
        )

        if json_output:
            output = {
                "cache": cache_stats,
                "usage": usage_stats
            }
            click.echo(json.dumps(output, indent=2))
            return

        # Rich formatted output
        console.print(Panel(
            "[bold cyan]Context Cache & Usage Statistics[/bold cyan]",
            box=box.ROUNDED
        ))

        # Cache statistics table
        cache_table = Table(title="Cache Statistics", box=box.SIMPLE)
        cache_table.add_column("Metric", style="cyan")
        cache_table.add_column("Value", style="yellow", justify="right")

        cache_table.add_row("Cache Size", f"{cache_stats['size']} / {cache_stats['max_size']}")
        cache_table.add_row("Cache Hits", str(cache_stats['hits']))
        cache_table.add_row("Cache Misses", str(cache_stats['misses']))
        cache_table.add_row("Hit Rate", f"{cache_stats['hit_rate']:.2%}")
        cache_table.add_row("Evictions", str(cache_stats['evictions']))
        cache_table.add_row("Expirations", str(cache_stats['expirations']))
        cache_table.add_row("Memory Usage", f"{cache_stats['memory_usage']:,} bytes")

        console.print(cache_table)

        # Usage statistics table
        console.print()
        usage_table = Table(title="Usage Statistics", box=box.SIMPLE)
        usage_table.add_column("Metric", style="cyan")
        usage_table.add_column("Value", style="yellow", justify="right")

        usage_table.add_row("Total Accesses", str(usage_stats['total']))
        usage_table.add_row("Cache Hits", str(usage_stats['hits']))
        usage_table.add_row("Cache Misses", str(usage_stats['misses']))
        usage_table.add_row("Hit Rate", f"{usage_stats['hit_rate']:.2%}")

        console.print(usage_table)

        # Show filter info if applied
        if workflow_id or context_key:
            console.print("\n[yellow]Filters applied:[/yellow]")
            if workflow_id:
                console.print(f"  Workflow ID: {workflow_id}")
            if context_key:
                console.print(f"  Context Key: {context_key}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@context.command("clear-cache")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
def clear_cache(confirm: bool):
    """
    Clear the context cache.

    Examples:
        gao-dev context clear-cache
        gao-dev context clear-cache --confirm
    """
    try:
        if not confirm:
            if not click.confirm("Are you sure you want to clear the context cache?"):
                console.print("[yellow]Cache clear cancelled[/yellow]")
                return

        cache = _get_global_cache()

        # Get stats before clearing
        stats_before = cache.get_statistics()
        size_before = stats_before['size']

        # Clear cache
        cache.clear()

        # Get stats after clearing
        stats_after = cache.get_statistics()

        console.print(Panel(
            f"[bold green]Cache Cleared Successfully[/bold green]\n"
            f"Removed [yellow]{size_before}[/yellow] entries",
            box=box.ROUNDED
        ))

        # Show before/after stats
        table = Table(title="Cache Statistics", box=box.SIMPLE)
        table.add_column("Metric", style="cyan")
        table.add_column("Before", style="yellow", justify="right")
        table.add_column("After", style="green", justify="right")

        table.add_row("Size", str(size_before), str(stats_after['size']))
        table.add_row("Memory Usage",
                     f"{stats_before['memory_usage']:,} bytes",
                     f"{stats_after['memory_usage']:,} bytes")

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()

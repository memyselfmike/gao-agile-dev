"""CLI commands for ceremony management.

Epic: 28 - Ceremony-Driven Workflow Integration
Story: 28.5 - CLI Commands & Testing

Commands:
- hold: Hold a ceremony manually
- list: List ceremonies for an epic
- show: Show ceremony details
- evaluate: Evaluate which ceremonies would trigger
- safety: Check ceremony safety status
"""

import click
from pathlib import Path
from tabulate import tabulate
from datetime import datetime
from typing import Optional
import json
import structlog

from gao_dev.orchestrator.ceremony_orchestrator import CeremonyOrchestrator
from gao_dev.core.services.ceremony_trigger_engine import (
    CeremonyTriggerEngine,
    TriggerContext
)
from gao_dev.core.services.ceremony_service import CeremonyService
from gao_dev.methodologies.adaptive_agile.scale_levels import ScaleLevel
from gao_dev.core.config_loader import ConfigLoader

logger = structlog.get_logger(__name__)


@click.group()
def ceremony():
    """Ceremony management commands."""
    pass


@ceremony.command()
@click.argument('ceremony_type', type=click.Choice(['planning', 'standup', 'retrospective']))
@click.option('--epic', required=True, type=int, help='Epic number')
@click.option('--story', type=int, help='Story number (for standup)')
@click.option('--participants', help='Comma-separated participant list (default: team)')
@click.option('--dry-run', is_flag=True, help='Simulate without saving')
def hold(ceremony_type: str, epic: int, story: Optional[int], participants: Optional[str], dry_run: bool):
    """Hold a ceremony manually.

    Examples:
        gao-dev ceremony hold planning --epic 1
        gao-dev ceremony hold standup --epic 1 --story 3
        gao-dev ceremony hold retrospective --epic 1 --participants "Bob,Amelia,John"
    """
    try:
        project_root = Path.cwd()
        db_path = project_root / ".gao-dev" / "documents.db"

        if not db_path.exists():
            click.echo("Error: Not in a GAO-Dev project (no .gao-dev/documents.db)", err=True)
            return 1

        if dry_run:
            click.echo(f"[DRY RUN] Would hold {ceremony_type} ceremony for epic {epic}")
            if story:
                click.echo(f"[DRY RUN]   Story: {story}")
            if participants:
                click.echo(f"[DRY RUN]   Participants: {participants}")
            return 0

        # Initialize orchestrator
        config = ConfigLoader()
        orchestrator = CeremonyOrchestrator(
            config=config,
            project_root=project_root,
            db_path=db_path
        )

        participant_list = participants.split(',') if participants else ["team"]

        click.echo(f"Holding {ceremony_type} ceremony for epic {epic}...")

        result = orchestrator.hold_ceremony(
            ceremony_type=ceremony_type,
            epic_num=epic,
            participants=participant_list,
            story_num=story
        )

        click.echo("Ceremony completed successfully")
        click.echo(f"  Ceremony ID: {result['ceremony_id']}")
        click.echo(f"  Transcript: {result['transcript_path']}")
        click.echo(f"  Action items: {len(result.get('action_items', []))}")
        if ceremony_type == 'retrospective':
            click.echo(f"  Learnings: {len(result.get('learnings', []))}")

        return 0

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        logger.exception("ceremony_hold_failed", ceremony_type=ceremony_type, epic=epic)
        return 1


@ceremony.command(name='list')
@click.option('--epic', required=True, type=int, help='Epic number')
@click.option('--type', 'ceremony_type', type=click.Choice(['planning', 'standup', 'retrospective']), help='Filter by type')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']), default='table', help='Output format')
def list_cmd(epic: int, ceremony_type: Optional[str], format: str):
    """List ceremonies for an epic.

    Examples:
        gao-dev ceremony list --epic 1
        gao-dev ceremony list --epic 1 --type retrospective
        gao-dev ceremony list --epic 1 --format json
    """
    try:
        project_root = Path.cwd()
        db_path = project_root / ".gao-dev" / "documents.db"

        if not db_path.exists():
            click.echo("Error: Not in a GAO-Dev project (no .gao-dev/documents.db)", err=True)
            return 1

        service = CeremonyService(db_path=db_path)

        # Get ceremonies using the service's get_recent method
        # Filter by epic_num by checking each ceremony
        all_ceremonies = service.get_recent(ceremony_type=ceremony_type, limit=100)
        ceremonies = [c for c in all_ceremonies if c.get('epic_num') == epic]

        if not ceremonies:
            click.echo(f"No ceremonies found for epic {epic}")
            return 0

        if format == 'table':
            headers = ['ID', 'Type', 'Date', 'Participants', 'Summary']
            rows = []
            for c in ceremonies:
                participants_str = c.get('participants', 'N/A')
                if participants_str and len(participants_str) > 30:
                    participants_str = participants_str[:27] + '...'

                summary_str = c.get('summary', 'N/A')
                if summary_str and len(summary_str) > 50:
                    summary_str = summary_str[:47] + '...'

                date_str = c.get('held_at', 'N/A')
                if date_str and len(date_str) > 10:
                    date_str = date_str[:10]  # Date only

                rows.append([
                    c.get('id', 'N/A'),
                    c.get('ceremony_type', 'N/A'),
                    date_str,
                    participants_str,
                    summary_str
                ])
            click.echo(tabulate(rows, headers=headers, tablefmt='grid'))

        elif format == 'json':
            click.echo(json.dumps(ceremonies, indent=2))

        elif format == 'yaml':
            import yaml as yaml_lib
            click.echo(yaml_lib.dump(ceremonies, default_flow_style=False))

        return 0

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        logger.exception("ceremony_list_failed", epic=epic)
        return 1


@ceremony.command()
@click.argument('ceremony_id', type=int)
@click.option('--full', is_flag=True, help='Show full transcript')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']), default='table', help='Output format')
def show(ceremony_id: int, full: bool, format: str):
    """Show ceremony details.

    Examples:
        gao-dev ceremony show 1
        gao-dev ceremony show 1 --full
        gao-dev ceremony show 1 --format json
    """
    try:
        project_root = Path.cwd()
        db_path = project_root / ".gao-dev" / "documents.db"

        if not db_path.exists():
            click.echo("Error: Not in a GAO-Dev project (no .gao-dev/documents.db)", err=True)
            return 1

        service = CeremonyService(db_path=db_path)

        try:
            ceremony = service.get(ceremony_id)
        except ValueError:
            click.echo(f"Error: Ceremony {ceremony_id} not found", err=True)
            return 1

        if format == 'table':
            click.echo(f"\nCeremony #{ceremony_id}")
            click.echo(f"  Type: {ceremony.get('ceremony_type', 'N/A')}")
            click.echo(f"  Epic: {ceremony.get('epic_num', 'N/A')}")
            if ceremony.get('story_num'):
                click.echo(f"  Story: {ceremony.get('story_num')}")
            click.echo(f"  Date: {ceremony.get('held_at', 'N/A')}")
            click.echo(f"  Participants: {ceremony.get('participants', 'N/A')}")

            click.echo("\n  Summary:")
            summary = ceremony.get('summary', 'N/A')
            for line in summary.split('\n'):
                click.echo(f"    {line}")

            if ceremony.get('decisions'):
                click.echo("\n  Decisions:")
                for line in ceremony.get('decisions', '').split('\n'):
                    click.echo(f"    {line}")

            if ceremony.get('action_items'):
                click.echo("\n  Action Items:")
                for line in ceremony.get('action_items', '').split('\n'):
                    click.echo(f"    {line}")

            # Note: Transcript path is not stored in ceremony_summaries table
            # This is a placeholder for future implementation
            click.echo("\n  (Transcript storage not yet implemented)")

        elif format == 'json':
            click.echo(json.dumps(ceremony, indent=2, default=str))

        elif format == 'yaml':
            import yaml as yaml_lib
            click.echo(yaml_lib.dump(ceremony, default_flow_style=False))

        return 0

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        logger.exception("ceremony_show_failed", ceremony_id=ceremony_id)
        return 1


@ceremony.command()
@click.option('--epic', required=True, type=int, help='Epic number')
@click.option('--level', required=True, type=int, help='Scale level (0-4)')
@click.option('--stories-completed', type=int, default=0, help='Stories completed')
@click.option('--total-stories', type=int, default=1, help='Total stories')
@click.option('--quality-gates-passed/--quality-gates-failed', default=True, help='Quality gate status')
def evaluate(epic: int, level: int, stories_completed: int, total_stories: int, quality_gates_passed: bool):
    """Evaluate which ceremonies would trigger (dry-run).

    Examples:
        gao-dev ceremony evaluate --epic 1 --level 3 --stories-completed 4 --total-stories 8
        gao-dev ceremony evaluate --epic 1 --level 2 --stories-completed 3 --total-stories 5 --quality-gates-failed
    """
    try:
        project_root = Path.cwd()
        db_path = project_root / ".gao-dev" / "documents.db"

        if not db_path.exists():
            click.echo("Error: Not in a GAO-Dev project (no .gao-dev/documents.db)", err=True)
            return 1

        if level < 0 or level > 4:
            click.echo("Error: Scale level must be 0-4", err=True)
            return 1

        engine = CeremonyTriggerEngine(db_path=db_path)

        context = TriggerContext(
            epic_num=epic,
            scale_level=ScaleLevel(level),
            stories_completed=stories_completed,
            total_stories=total_stories,
            quality_gates_passed=quality_gates_passed,
            failure_count=0,
            project_type='feature'
        )

        ceremonies = engine.evaluate_all_triggers(context)

        click.echo(f"\nTrigger Evaluation for Epic {epic} (Level {level})")
        click.echo(f"  Stories: {stories_completed}/{total_stories} ({context.progress_percentage:.0%})")
        click.echo(f"  Quality Gates: {'Passed' if quality_gates_passed else 'Failed'}")
        click.echo()

        if ceremonies:
            click.echo("Ceremonies that would trigger:")
            for ceremony in ceremonies:
                click.echo(f"  - {ceremony.value}")
        else:
            click.echo("No ceremonies would trigger")

        # Show safety status
        click.echo("\nSafety Status:")
        count = engine._get_ceremony_count(epic)
        click.echo(f"  Ceremonies held: {count}/{engine.MAX_CEREMONIES_PER_EPIC}")
        if count >= 8:
            click.echo("  WARNING: Approaching ceremony limit!")

        return 0

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        logger.exception("ceremony_evaluate_failed", epic=epic, level=level)
        return 1


@ceremony.command()
@click.option('--epic', required=True, type=int, help='Epic number')
def safety(epic: int):
    """Check ceremony safety status for an epic.

    Examples:
        gao-dev ceremony safety --epic 1
    """
    try:
        project_root = Path.cwd()
        db_path = project_root / ".gao-dev" / "documents.db"

        if not db_path.exists():
            click.echo("Error: Not in a GAO-Dev project (no .gao-dev/documents.db)", err=True)
            return 1

        engine = CeremonyTriggerEngine(db_path=db_path)

        # Get total count
        total_count = engine._get_ceremony_count(epic)

        click.echo(f"\nCeremony Safety Status for Epic {epic}")
        click.echo(f"\nTotal Ceremonies: {total_count}/{engine.MAX_CEREMONIES_PER_EPIC}")
        if total_count >= engine.MAX_CEREMONIES_PER_EPIC:
            click.echo("  ERROR: MAX LIMIT REACHED")
        elif total_count >= 8:
            click.echo("  WARNING: Approaching limit")

        # Get counts by type
        service = CeremonyService(db_path=db_path)
        all_ceremonies = service.get_recent(limit=100)
        epic_ceremonies = [c for c in all_ceremonies if c.get('epic_num') == epic]

        planning_count = len([c for c in epic_ceremonies if c.get('ceremony_type') == 'planning'])
        standup_count = len([c for c in epic_ceremonies if c.get('ceremony_type') == 'standup'])
        retro_count = len([c for c in epic_ceremonies if c.get('ceremony_type') == 'retrospective'])

        click.echo("\nBy Type:")
        click.echo(f"  Planning: {planning_count}")
        click.echo(f"  Standup: {standup_count}")
        click.echo(f"  Retrospective: {retro_count}")

        # Check cooldowns
        click.echo("\nCooldown Status:")
        for ceremony_type in ['planning', 'standup', 'retrospective']:
            last_time = engine._get_last_ceremony_time(epic, ceremony_type)
            if last_time:
                hours_since = (datetime.now() - last_time).total_seconds() / 3600
                cooldown_hours = engine.COOLDOWN_HOURS[ceremony_type]
                if hours_since >= cooldown_hours:
                    status = "Elapsed"
                else:
                    status = f"Active ({cooldown_hours - hours_since:.1f}h remaining)"
                click.echo(f"  {ceremony_type.capitalize()}: {status}")
            else:
                click.echo(f"  {ceremony_type.capitalize()}: Never held")

        # Check circuit breaker
        click.echo("\nCircuit Breaker:")
        for ceremony_type in ['planning', 'standup', 'retrospective']:
            is_open = engine.circuit_open.get((epic, ceremony_type), False)
            status = 'OPEN (disabled)' if is_open else 'Closed (active)'
            click.echo(f"  {ceremony_type.capitalize()}: {status}")

        return 0

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        logger.exception("ceremony_safety_failed", epic=epic)
        return 1


# Register commands with main CLI
def register_ceremony_commands(cli_group):
    """Register ceremony commands with main CLI."""
    cli_group.add_command(ceremony)

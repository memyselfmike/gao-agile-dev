"""CLI command for force unlocking sessions.

Provides administrative command to remove stale session locks.
"""

from pathlib import Path

import click
import structlog

from ..core.session_lock import SessionLock

logger = structlog.get_logger(__name__)


@click.command()
@click.option("--force", is_flag=True, help="Force remove lock file (use with caution)")
@click.pass_context
def unlock(ctx: click.Context, force: bool) -> None:
    """Remove stale session lock.

    Args:
        ctx: Click context
        force: Force remove lock file
    """
    project_root = Path.cwd()

    # Detect project root by looking for .gao-dev directory
    current = project_root
    while current != current.parent:
        if (current / ".gao-dev").exists():
            project_root = current
            break
        current = current.parent

    session_lock = SessionLock(project_root)

    if not session_lock.lock_file.exists():
        click.echo("No session lock found.")
        logger.info("unlock_no_lock", project_root=str(project_root))
        return

    # Show lock info
    lock_state = session_lock.get_lock_state()
    if lock_state["holder"]:
        click.echo(f"Session locked by: {lock_state['holder']}")
        click.echo(f"Lock timestamp: {lock_state['timestamp']}")

    if not force:
        click.echo("Use --force to remove lock file")
        return

    # Force unlock
    try:
        session_lock.force_unlock()
        click.echo("Lock removed successfully.")
        logger.warning(
            "force_unlock_successful",
            project_root=str(project_root),
            previous_holder=lock_state.get("holder", "unknown"),
        )
    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        logger.error("force_unlock_failed", error=str(e))
        ctx.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        logger.exception("force_unlock_exception", error=str(e))
        ctx.exit(1)

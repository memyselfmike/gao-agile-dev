"""CLI commands for GAO-Dev web interface."""

import asyncio
import sys
import time
from pathlib import Path

import click
import structlog
from rich.console import Console
from rich.panel import Panel

from ..web.config import WebConfig
from ..web.server import start_server

logger = structlog.get_logger(__name__)


def show_web_deprecation_warning(
    console: Console,
    quiet: bool = False,
    no_wait: bool = False,
    delay_seconds: int = 5,
) -> None:
    """Show deprecation warning panel for web start command.

    Args:
        console: Rich console for output
        quiet: If True, suppress the warning display
        no_wait: If True, skip the delay
        delay_seconds: Number of seconds to wait before redirect
    """
    # Track deprecation usage for telemetry
    from ..core.deprecation_tracker import track_deprecated_command
    track_deprecated_command(
        "gao-dev web start",
        "gao-dev start",
        "v3.0",
    )

    # Log at WARNING level regardless of quiet setting
    logger.warning(
        "deprecated_command_used",
        old_command="gao-dev web start",
        new_command="gao-dev start",
        removal_version="v3.0",
    )

    if quiet:
        return

    # Build warning message
    message = """[bold yellow]DEPRECATION WARNING[/bold yellow]

The 'gao-dev web start' command is deprecated and
will be removed in v3.0 (Q2 2026).

Use 'gao-dev start' instead - it will
automatically handle initialization with a
guided setup wizard.

This command will redirect to 'gao-dev start'
in 5 seconds...

Use --no-wait to skip delay, --quiet to suppress

See: docs/migration/deprecated-commands.md"""

    console.print(Panel(
        message,
        border_style="yellow",
        title="Deprecation Notice",
    ))

    # Wait before redirect unless --no-wait specified
    if not no_wait:
        console.print()
        for i in range(delay_seconds, 0, -1):
            console.print(f"  Redirecting in {i}...", end="\r")
            time.sleep(1)
        console.print("  Redirecting now...   ")
        console.print()


@click.group(name="web")
def web() -> None:
    """Web interface commands."""
    pass


@web.command(name="start")
@click.option("--port", type=int, default=3000, help="Server port (default: 3000)")
@click.option(
    "--host",
    type=str,
    default="127.0.0.1",
    help="Server host (default: 127.0.0.1, localhost only)",
)
@click.option("--no-browser", is_flag=True, help="Don't auto-open browser on startup")
@click.option("--no-wait", is_flag=True, help="Skip deprecation warning delay")
@click.option("--quiet", is_flag=True, help="Suppress deprecation warning (for scripts)")
def start_web(port: int, host: str, no_browser: bool, no_wait: bool, quiet: bool) -> None:
    """[DEPRECATED] Start GAO-Dev web interface.

    This command is deprecated and will be removed in v3.0 (Q2 2026).
    Use 'gao-dev start' instead for the new unified onboarding experience.

    Examples:
        gao-dev web start                    # Start with defaults
        gao-dev web start --port 3001        # Custom port
        gao-dev web start --no-browser       # Don't auto-open browser
    """
    console = Console()

    # Show deprecation warning
    show_web_deprecation_warning(
        console=console,
        quiet=quiet,
        no_wait=no_wait,
    )

    # Redirect to start command
    from .startup_orchestrator import StartupOrchestrator
    from .startup_result import StartupError
    from ..__version__ import __version__

    project_path = Path.cwd()

    # Create orchestrator
    orchestrator = StartupOrchestrator(
        project_path=project_path,
        headless=False,
        no_browser=no_browser,
        port=port,
    )

    # Run startup
    try:
        result = asyncio.run(orchestrator.start())

        if result.success:
            console.print()
            console.print(f"[green][OK] Startup complete in {result.total_duration_ms:.0f}ms[/green]")

            # Show interface info
            if result.interface_launched == "web":
                console.print(f"[cyan]Web interface available at http://localhost:{port}[/cyan]")
            else:
                console.print("[cyan]CLI interface ready[/cyan]")

            sys.exit(0)
        else:
            console.print(f"[red][ERROR] Startup failed: {result.error}[/red]")
            sys.exit(1)

    except StartupError as e:
        console.print()
        console.print(f"[red][ERROR] {e}[/red]")
        if e.suggestions:
            console.print()
            console.print("[yellow]Suggestions:[/yellow]")
            for suggestion in e.suggestions:
                console.print(f"  - {suggestion}")
        sys.exit(1)

    except KeyboardInterrupt:
        console.print()
        console.print("[yellow]Startup interrupted by user[/yellow]")
        sys.exit(130)

    except Exception as e:
        logger.exception("web_server_error", error=str(e))
        console.print()
        console.print(f"[red][ERROR] Unexpected error: {e}[/red]")
        sys.exit(1)

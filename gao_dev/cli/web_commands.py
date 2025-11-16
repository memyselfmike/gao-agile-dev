"""CLI commands for GAO-Dev web interface."""

import sys
from typing import Optional

import click
import structlog

from ..web.config import WebConfig
from ..web.server import start_server

logger = structlog.get_logger(__name__)


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
def start_web(port: int, host: str, no_browser: bool) -> None:
    """Start GAO-Dev web interface.

    Examples:
        gao-dev web start                    # Start with defaults
        gao-dev web start --port 3001        # Custom port
        gao-dev web start --no-browser       # Don't auto-open browser
    """
    try:
        # Create config
        config = WebConfig(host=host, port=port, auto_open=not no_browser)

        # Start server
        start_server(config=config)

    except OSError as e:
        if "Port" in str(e) and "already in use" in str(e):
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
        raise
    except KeyboardInterrupt:
        click.echo("\nShutting down...")
        sys.exit(0)
    except Exception as e:
        logger.exception("web_server_error", error=str(e))
        click.echo(f"Error: Failed to start web server: {e}", err=True)
        sys.exit(1)

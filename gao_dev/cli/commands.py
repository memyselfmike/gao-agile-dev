"""CLI commands for GAO-Dev."""

import click
from pathlib import Path
from typing import Optional
import sys
import asyncio
import os
import time

import structlog
from rich.console import Console
from rich.panel import Panel

# Fix Windows console encoding issues
if sys.platform == "win32":
    import io
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    # Reconfigure stdout and stderr to use UTF-8 encoding
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logger = structlog.get_logger(__name__)


def show_deprecation_warning(
    console: Console,
    old_command: str,
    new_command: str,
    removal_version: str = "v2.0",
    quiet: bool = False,
    no_wait: bool = False,
    delay_seconds: int = 5,
) -> None:
    """Show deprecation warning panel for a deprecated command.

    Args:
        console: Rich console for output
        old_command: The deprecated command name
        new_command: The replacement command name
        removal_version: Version when the command will be removed
        quiet: If True, suppress the warning display
        no_wait: If True, skip the delay
        delay_seconds: Number of seconds to wait before redirect
    """
    # Log at WARNING level regardless of quiet setting
    logger.warning(
        "deprecated_command_used",
        old_command=old_command,
        new_command=new_command,
        removal_version=removal_version,
    )

    if quiet:
        return

    # Build warning message
    message = f"""[bold yellow]DEPRECATION WARNING[/bold yellow]

The '{old_command}' command is deprecated and
will be removed in {removal_version}.

Use '{new_command}' instead - it will
automatically handle initialization with a
guided setup wizard.

This command will redirect to '{new_command}'
in {delay_seconds} seconds...

Use --no-wait to skip delay, --quiet to suppress"""

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

from ..core import (
    ConfigLoader,
    WorkflowRegistry,
    WorkflowExecutor,
    GitManager,
    HealthCheck,
)
from ..orchestrator import GAODevOrchestrator
from .sandbox_commands import sandbox
from .lifecycle_commands import lifecycle
from .state_commands import state
from .context_commands import context
from .db_commands import db
from .migration_commands import migrate_group
from .ceremony_commands import ceremony
from .learning_commands import learning
from .create_feature_command import create_feature
from .list_features_command import list_features
from .validate_structure_command import validate_structure
from .web_commands import web
from .unlock_command import unlock


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    GAO-Dev - Software Engineering Team for Generative Autonomous Organisation.

    Autonomous AI development orchestration system.
    """
    pass


@cli.command()
@click.option("--name", default="My Project", help="Project name")
@click.option("--no-wait", is_flag=True, help="Skip deprecation warning delay")
@click.option("--quiet", is_flag=True, help="Suppress deprecation warning (for scripts)")
def init(name: str, no_wait: bool, quiet: bool):
    """[DEPRECATED] Initialize a new GAO-Dev project.

    This command is deprecated and will be removed in v2.0.
    Use 'gao-dev start' instead for the new unified onboarding experience.
    """
    console = Console()

    # Show deprecation warning
    show_deprecation_warning(
        console=console,
        old_command="gao-dev init",
        new_command="gao-dev start",
        quiet=quiet,
        no_wait=no_wait,
    )

    # Redirect to start command
    from .startup_orchestrator import StartupOrchestrator
    from .startup_result import StartupError

    project_path = Path.cwd()

    # Create orchestrator
    orchestrator = StartupOrchestrator(
        project_path=project_path,
        headless=False,
        no_browser=True,  # Don't auto-open browser for init redirect
        port=3000,
    )

    # Run startup
    try:
        result = asyncio.run(orchestrator.start())

        if result.success:
            console.print()
            console.print(f"[green][OK] Startup complete in {result.total_duration_ms:.0f}ms[/green]")
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
        console.print()
        console.print(f"[red][ERROR] Unexpected error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--format", type=click.Choice(["json", "markdown"]), default="markdown")
def health(format: str):
    """Run system health check."""
    project_root = Path.cwd()
    config = ConfigLoader(project_root)
    health_check = HealthCheck(config)

    click.echo(">> Running GAO-Dev Health Check...\n")

    result = health_check.run_all_checks()

    if format == "json":
        import json
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        # Pretty print markdown
        click.echo(f"Overall Status: {result.status.value.upper()}")
        click.echo(f"Summary: {result.summary}\n")

        for check in result.checks:
            status_icon = (
                "[OK]" if check.status.value == "healthy"
                else "[WARN]" if check.status.value == "warning"
                else "[FAIL]"
            )
            click.echo(f"{status_icon} {check.name}: {check.message}")
            if check.remediation:
                click.echo(f"  > {check.remediation}")


@cli.command("list-workflows")
@click.option("--phase", type=int, help="Filter by phase (0-4)")
def list_workflows_cmd(phase: int):
    """List available workflows."""
    project_root = Path.cwd()
    config = ConfigLoader(project_root)
    registry = WorkflowRegistry(config)
    registry.index_workflows()

    workflows = registry.list_workflows(phase=phase)

    if not workflows:
        click.echo("No workflows found.")
        return

    click.echo(f"\n>> Available Workflows ({len(workflows)} total):\n")

    current_phase = None
    for workflow in workflows:
        if workflow.phase != current_phase:
            current_phase = workflow.phase
            phase_names = {
                0: "Meta",
                1: "Analysis",
                2: "Planning",
                3: "Solutioning",
                4: "Implementation"
            }
            click.echo(f"\n  Phase {workflow.phase}: {phase_names.get(workflow.phase, 'Unknown')}")

        click.echo(f"    - {workflow.name}")
        click.echo(f"      {workflow.description}")
        if workflow.author:
            click.echo(f"      Author: {workflow.author}")


@cli.command()
@click.argument("workflow_name")
@click.option("--param", "-p", multiple=True, help="Parameters (key=value)")
def execute(workflow_name: str, param: tuple):
    """Execute a workflow."""
    project_root = Path.cwd()
    config = ConfigLoader(project_root)
    registry = WorkflowRegistry(config)
    executor = WorkflowExecutor(config)

    click.echo(f"\n>> Executing workflow: {workflow_name}\n")

    # Get workflow
    workflow = registry.get_workflow(workflow_name)
    if not workflow:
        click.echo(f"❌ Workflow '{workflow_name}' not found.", err=True)
        click.echo("Run 'gao-dev list-workflows' to see available workflows.")
        sys.exit(1)

    # Parse parameters
    params = {}
    for p in param:
        if "=" in p:
            key, value = p.split("=", 1)
            params[key] = value

    try:
        # Execute workflow
        result = executor.execute(workflow, params)

        if result["success"]:
            click.echo("[OK] Workflow executed successfully!\n")

            # Show instructions
            if result["instructions"]:
                click.echo(">> Instructions:")
                click.echo(result["instructions"][:500] + "..." if len(result["instructions"]) > 500 else result["instructions"])

            # Show output file
            if result["output_file"]:
                click.echo(f"\n>> Output file: {result['output_file']}")

            # Show required tools
            if result["required_tools"]:
                click.echo(f"\n>> Required tools: {', '.join(result['required_tools'])}")

    except ValueError as e:
        click.echo(f"[ERROR] {e}", err=True)
        sys.exit(1)


@cli.command("list-agents")
def list_agents_cmd():
    """List available agent personas."""
    project_root = Path.cwd()
    config = ConfigLoader(project_root)
    agents_path = config.get_agents_path()

    agents = []
    if agents_path.exists():
        for agent_file in agents_path.glob("*.md"):
            agents.append(agent_file.stem)

    if not agents:
        click.echo("No agent personas found.")
        return

    click.echo(f"\n>> Available Agents ({len(agents)} total):\n")
    for agent in sorted(agents):
        click.echo(f"  - {agent}")


@cli.command()
def version():
    """Show GAO-Dev version information."""
    from ..__version__ import __version__, __title__, __description__

    click.echo(f"{__title__} v{__version__}")
    click.echo(__description__)


# ============================================================================
# AUTONOMOUS ORCHESTRATOR COMMANDS
# ============================================================================

@cli.command("create-prd")
@click.option("--name", required=True, help="Project name")
def create_prd(name: str):
    """Create a Product Requirements Document using John (PM)."""
    click.echo(f"\n>> Creating PRD for: {name}")
    click.echo(">> Delegating to John (Product Manager)...\n")

    project_root = Path.cwd()
    orchestrator = GAODevOrchestrator.create_default(project_root)

    async def run():
        async for message in orchestrator.create_prd(name):
            click.echo(message, nl=False)

    try:
        asyncio.run(run())
        click.echo("\n\n[OK] PRD creation complete!")
        if orchestrator.git_state_manager:
            click.echo("[INFO] Changes committed via git transaction")
    except Exception as e:
        click.echo(f"\n[ERROR] {e}", err=True)
        sys.exit(1)
    finally:
        orchestrator.close()


@cli.command("create-story")
@click.option("--epic", type=int, required=True, help="Epic number")
@click.option("--story", type=int, required=True, help="Story number")
@click.option("--title", help="Story title (optional)")
def create_story(epic: int, story: int, title: str):
    """Create a user story using Bob (Scrum Master)."""
    click.echo(f"\n>> Creating Story {epic}.{story}")
    if title:
        click.echo(f">> Title: {title}")
    click.echo(">> Delegating to Bob (Scrum Master)...\n")

    project_root = Path.cwd()
    orchestrator = GAODevOrchestrator.create_default(project_root)

    async def run():
        async for message in orchestrator.create_story(epic, story, title):
            click.echo(message, nl=False)

    try:
        asyncio.run(run())
        click.echo("\n\n[OK] Story creation complete!")
        if orchestrator.git_state_manager:
            click.echo("[INFO] Changes committed via git transaction")
    except Exception as e:
        click.echo(f"\n[ERROR] {e}", err=True)
        sys.exit(1)
    finally:
        orchestrator.close()


@cli.command("implement-story")
@click.option("--epic", type=int, required=True, help="Epic number")
@click.option("--story", type=int, required=True, help="Story number")
def implement_story(epic: int, story: int):
    """Implement a story using the full workflow (Bob > Amelia > Bob)."""
    click.echo(f"\n>> Implementing Story {epic}.{story}")
    click.echo(">> Coordinating Bob (Scrum Master) and Amelia (Developer)...\n")

    project_root = Path.cwd()
    orchestrator = GAODevOrchestrator.create_default(project_root)

    async def run():
        async for message in orchestrator.implement_story(epic, story):
            click.echo(message, nl=False)

    try:
        asyncio.run(run())
        click.echo("\n\n[OK] Story implementation complete!")
        if orchestrator.git_state_manager:
            click.echo("[INFO] Changes committed via git transaction")
    except Exception as e:
        click.echo(f"\n[ERROR] {e}", err=True)
        sys.exit(1)
    finally:
        orchestrator.close()


@cli.command("create-architecture")
@click.option("--name", required=True, help="Project name")
def create_architecture(name: str):
    """Create system architecture using Winston (Architect)."""
    click.echo(f"\n>> Creating architecture for: {name}")
    click.echo(">> Delegating to Winston (Technical Architect)...\n")

    project_root = Path.cwd()
    orchestrator = GAODevOrchestrator.create_default(project_root)

    async def run():
        async for message in orchestrator.create_architecture(name):
            click.echo(message, nl=False)

    try:
        asyncio.run(run())
        click.echo("\n\n[OK] Architecture creation complete!")
        if orchestrator.git_state_manager:
            click.echo("[INFO] Changes committed via git transaction")
    except Exception as e:
        click.echo(f"\n[ERROR] {e}", err=True)
        sys.exit(1)
    finally:
        orchestrator.close()


@cli.command("run-health-check")
def run_health_check():
    """Run autonomous health check using the orchestrator."""
    click.echo("\n>> Running autonomous health check...")
    click.echo(">> Using GAO-Dev orchestrator...\n")

    project_root = Path.cwd()
    orchestrator = GAODevOrchestrator(project_root)

    async def run():
        async for message in orchestrator.run_health_check():
            click.echo(message, nl=False)

    try:
        asyncio.run(run())
        click.echo("\n\n[OK] Health check complete!")
    except Exception as e:
        click.echo(f"\n[ERROR] {e}", err=True)
        sys.exit(1)


# ============================================================================
# METRICS COMMANDS
# ============================================================================

@cli.group()
def metrics():
    """Metrics management commands."""
    pass


@metrics.command("export")
@click.option(
    "--format",
    type=click.Choice(["json", "csv"]),
    default="json",
    help="Export format (json or csv)",
)
@click.option(
    "--output",
    type=click.Path(),
    required=True,
    help="Output path (file for JSON, directory for CSV)",
)
@click.option("--run-id", help="Specific run ID to export")
@click.option("--project", help="Export all runs for project")
@click.option("--benchmark", help="Export all runs for benchmark")
@click.option("--since", help="Export runs since date (YYYY-MM-DD)")
@click.option("--until", help="Export runs until date (YYYY-MM-DD)")
@click.option(
    "--limit",
    type=int,
    default=100,
    help="Maximum number of runs to export (default: 100)",
)
def metrics_export(format, output, run_id, project, benchmark, since, until, limit):
    """Export metrics to JSON or CSV format.

    Examples:

      # Export single run to JSON
      gao-dev metrics export --format json --run-id abc123 --output metrics.json

      # Export all runs for project to CSV
      gao-dev metrics export --format csv --project todo-app --output ./exports

      # Export recent runs since date
      gao-dev metrics export --format json --since 2025-10-01 --output recent.json

      # Export specific benchmark runs
      gao-dev metrics export --format csv --benchmark full-stack --output ./data
    """
    from pathlib import Path
    from gao_dev.sandbox.metrics.export import MetricsExporter
    from gao_dev.sandbox.metrics.storage import MetricsStorage

    try:
        storage = MetricsStorage()
        exporter = MetricsExporter(storage)
        output_path = Path(output)

        # Export single run by ID
        if run_id:
            click.echo(f">> Exporting run: {run_id}")
            exporter.export_run(run_id, output_path, format=format)

            if format == "json":
                click.echo(f"[OK] Exported to {output_path}")
            else:
                click.echo(f"[OK] Exported CSV files to {output_path.parent}/")

        # Export with filters
        else:
            # Convert date formats if provided
            start_date = None
            end_date = None
            if since:
                start_date = f"{since}T00:00:00Z"
            if until:
                end_date = f"{until}T23:59:59Z"

            click.echo(">> Exporting metrics with filters:")
            if project:
                click.echo(f"  Project: {project}")
            if benchmark:
                click.echo(f"  Benchmark: {benchmark}")
            if since:
                click.echo(f"  Since: {since}")
            if until:
                click.echo(f"  Until: {until}")

            count = exporter.export_filtered(
                output_path,
                format=format,
                project_name=project,
                benchmark_name=benchmark,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )

            if count == 0:
                click.echo("[WARN] No metrics found matching filters")
            elif format == "json":
                click.echo(f"[OK] Exported {count} run(s) to {output_path}")
            else:
                click.echo(f"[OK] Exported {count} run(s) to {output_path}/")

    except ValueError as e:
        click.echo(f"[ERROR] {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"[ERROR] Export failed: {e}", err=True)
        sys.exit(1)


# ============================================================================
# HEALTH CHECK COMMANDS
# ============================================================================

@cli.command("health-check")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
@click.option("--project", type=Path, help="Project path (default: current directory)")
def health_check(verbose: bool, project: Optional[Path]):
    """Run post-update system health check."""
    from ..core.system_health_check import SystemHealthCheck
    from rich.console import Console
    from rich.table import Table

    console = Console()

    project_path = project or Path.cwd()
    checker = SystemHealthCheck(project_path)

    console.print("\n[bold cyan]GAO-Dev System Health Check[/bold cyan]")
    console.print(f"Project: {project_path}\n")

    # Run health check
    report = checker.run_post_update_check(verbose=verbose)

    # Create results table
    table = Table(title="Health Check Results")
    table.add_column("Check", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Message", style="white")

    for result in report.results:
        status = "[green]PASS[/green]" if result.passed else "[red]FAIL[/red]"
        table.add_row(result.check_name, status, result.message)

    console.print(table)

    # Show summary
    console.print()
    if report.all_passed:
        console.print("[bold green]All checks passed![/bold green]")
    else:
        console.print(f"[bold red]{report.failed_count} check(s) failed[/bold red]")
        console.print()

        # Show fix suggestions
        for result in report.results:
            if not result.passed and result.fix_suggestion:
                console.print(f"[yellow]Fix for {result.check_name}:[/yellow]")
                console.print(f"  {result.fix_suggestion}")

        sys.exit(1)


# ============================================================================
# SANDBOX COMMANDS
# ============================================================================

# Register sandbox command group
cli.add_command(sandbox)

# ============================================================================
# LIFECYCLE COMMANDS
# ============================================================================

# Register lifecycle command group
cli.add_command(lifecycle)

# ============================================================================
# STATE COMMANDS
# ============================================================================

# Register state command group
cli.add_command(state)

# ============================================================================
# CONTEXT COMMANDS
# ============================================================================

# Register context command group
cli.add_command(context)

@cli.command("start")
@click.option("--project", type=Path, help="Project path (default: current directory)")
@click.option("--headless", is_flag=True, help="Force headless mode (no wizards, env vars only)")
@click.option("--no-browser", is_flag=True, help="Start web server without opening browser")
@click.option("--port", type=int, default=3000, help="Web server port (default: 3000)")
@click.option("--tui", is_flag=True, help="Force TUI wizard even in Desktop environment")
def start(
    project: Optional[Path],
    headless: bool,
    no_browser: bool,
    port: int,
    tui: bool,
):
    """Start GAO-Dev with intelligent environment detection.

    Automatically detects your environment and project state to provide
    the appropriate onboarding experience:

    - Empty directory: Full onboarding wizard
    - Existing code: Brownfield integration setup
    - GAO-Dev project: Direct launch

    Examples:

      gao-dev start                    # Auto-detect and start
      gao-dev start --headless         # CI/CD mode, env vars only
      gao-dev start --no-browser       # Web server without browser
      gao-dev start --port 8080        # Custom port
      gao-dev start --tui              # Force TUI wizard
      gao-dev start --project /path    # Specific project path
    """
    from rich.console import Console
    from rich.panel import Panel
    from .startup_orchestrator import StartupOrchestrator
    from .startup_result import StartupError
    from ..__version__ import __version__

    console = Console()

    # Resolve project path
    project_path = project or Path.cwd()

    # Validate project path exists
    if not project_path.exists():
        console.print(f"[red][ERROR] Project path does not exist: {project_path}[/red]")
        sys.exit(2)

    if not project_path.is_dir():
        console.print(f"[red][ERROR] Project path is not a directory: {project_path}[/red]")
        sys.exit(2)

    # Create orchestrator
    orchestrator = StartupOrchestrator(
        project_path=project_path,
        headless=headless,
        no_browser=no_browser,
        port=port,
    )

    # Show startup message
    _show_startup_message(console, __version__, orchestrator, tui)

    # Run startup
    try:
        result = asyncio.run(orchestrator.start())

        if result.success:
            # Show success summary
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

        # Show suggestions
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
        console.print()
        console.print(f"[red][ERROR] Unexpected error: {e}[/red]")
        sys.exit(1)


def _show_startup_message(
    console,
    version: str,
    orchestrator,
    force_tui: bool,
) -> None:
    """Show startup message with detected context.

    Args:
        console: Rich console for output
        version: GAO-Dev version string
        orchestrator: StartupOrchestrator with detection data
        force_tui: Whether --tui flag was passed
    """
    from rich.panel import Panel
    from .startup_result import WizardType
    from gao_dev.core.environment_detector import detect_environment, EnvironmentType
    from gao_dev.core.state_detector import detect_states, GlobalState, ProjectState

    # Detect environment for display (before orchestrator runs)
    if orchestrator.headless:
        env_type = EnvironmentType.HEADLESS
    else:
        env_type = detect_environment()

    global_state, project_state = detect_states(orchestrator.project_path)

    # Format environment name
    env_name = env_type.value.replace("_", " ").title()
    if sys.platform == "win32":
        env_name += " (Windows)"
    elif sys.platform == "darwin":
        env_name += " (macOS)"
    else:
        env_name += " (Linux)"

    # Format user state
    user_state = "First-time setup" if global_state == GlobalState.FIRST_TIME else "Returning user"

    # Format project state
    if project_state == ProjectState.EMPTY:
        project_desc = "Empty directory"
    elif project_state == ProjectState.BROWNFIELD:
        project_desc = "Existing code (brownfield)"
    else:
        project_desc = "GAO-Dev project"

    # Determine what will launch
    if force_tui:
        launch_desc = "Starting TUI onboarding wizard..."
    elif orchestrator.headless:
        launch_desc = "Starting in headless mode..."
    elif project_state == ProjectState.GAO_DEV_PROJECT:
        launch_desc = "Launching existing project..."
    elif env_type == EnvironmentType.DESKTOP and not orchestrator.no_browser:
        launch_desc = "Starting web-based onboarding wizard..."
    else:
        launch_desc = "Starting CLI onboarding..."

    # Build message
    message = f"""[bold cyan]GAO-Dev v{version}[/bold cyan]

[bold]Detected:[/bold]
  Environment: {env_name}
  User: {user_state}
  Project: {project_desc}

{launch_desc}"""

    console.print(Panel(message, title="Startup", border_style="cyan"))


@cli.command("chat")
@click.option("--project", type=Path, help="Project root (default: auto-detect)")
@click.option("--test-mode", is_flag=True, help="Enable test mode with fixture responses")
@click.option("--capture-mode", is_flag=True, help="Enable conversation capture logging")
@click.option("--fixture", type=Path, help="Fixture file for test mode (YAML format)")
def start_chat(
    project: Optional[Path],
    test_mode: bool,
    capture_mode: bool,
    fixture: Optional[Path]
):
    """Start interactive chat with Brian (legacy command).

    Note: Consider using 'gao-dev start' for the new unified startup experience.
    """
    from .chat_repl import ChatREPL

    # Validate fixture exists if test mode enabled
    if test_mode and fixture and not fixture.exists():
        click.echo(f"[ERROR] Fixture file not found: {fixture}", err=True)
        sys.exit(1)

    # Create REPL with test flags
    repl = ChatREPL(
        project_root=project,
        test_mode=test_mode,
        capture_mode=capture_mode,
        fixture_path=fixture
    )

    # Start async loop
    try:
        asyncio.run(repl.start())
    except Exception as e:
        click.echo(f"[ERROR] Failed to start REPL: {e}", err=True)
        sys.exit(1)


# ============================================================================
# Register db command group
# ============================================================================
cli.add_command(db)

# ============================================================================
# MIGRATION COMMANDS
# ============================================================================

# Register migration command group (migrate, consistency-check, consistency-repair)
cli.add_command(migrate_group, name="migrate")

# ============================================================================
# CEREMONY COMMANDS
# ============================================================================

# Register ceremony command group
cli.add_command(ceremony)

# ============================================================================
# LEARNING COMMANDS
# ============================================================================

# Register learning command group
cli.add_command(learning)

# ============================================================================
# FEATURE COMMANDS (Epic 33)
# ============================================================================

# Register feature command group
cli.add_command(create_feature)
cli.add_command(list_features)
cli.add_command(validate_structure)

# ============================================================================
# WEB INTERFACE COMMANDS (Epic 39)
# ============================================================================

# Register web command group
cli.add_command(web)

# Register unlock command
cli.add_command(unlock)


if __name__ == "__main__":
    cli()

"""CLI commands for GAO-Dev."""

import click
from pathlib import Path
import sys
import asyncio
import os

# Fix Windows console encoding issues
if sys.platform == "win32":
    import io
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    # Reconfigure stdout and stderr to use UTF-8 encoding
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from ..core import (
    ConfigLoader,
    WorkflowRegistry,
    WorkflowExecutor,
    StateManager,
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
def init(name: str):
    """Initialize a new GAO-Dev project."""
    click.echo(f">> Initializing GAO-Dev project: {name}")

    project_root = Path.cwd()

    # Create project structure
    folders = [
        "docs",
        "docs/stories",
        "docs/architecture",
    ]

    for folder in folders:
        folder_path = project_root / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        click.echo(f"  [+] Created {folder}/")

    # Create gao-dev.yaml
    config_path = project_root / "gao-dev.yaml"
    if not config_path.exists():
        config_content = f"""# GAO-Dev Configuration
project_name: "{name}"
project_level: 2
output_folder: "docs"
dev_story_location: "docs/stories"
git_auto_commit: true
qa_enabled: true
"""
        config_path.write_text(config_content)
        click.echo(f"  [+] Created gao-dev.yaml")

    # Initialize git if not already
    git_manager = GitManager(ConfigLoader(project_root))
    if not git_manager.is_git_repo():
        if git_manager.git_init():
            click.echo(f"  [+] Initialized git repository")

    # Run health check
    click.echo("\n>> Running health check...")
    config = ConfigLoader(project_root)
    health_check = HealthCheck(config)
    result = health_check.run_all_checks()

    click.echo(f"  Status: {result.status.value.upper()}")
    click.echo(f"  {result.summary}\n")

    click.echo("[OK] Project initialized successfully!")
    click.echo("\nNext steps:")
    click.echo("  1. Run 'gao-dev health' to check system status")
    click.echo("  2. Run 'gao-dev list-workflows' to see available workflows")
    click.echo("  3. Run 'gao-dev execute prd' to create a PRD")


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


if __name__ == "__main__":
    cli()

"""CLI commands for GAO-Dev sandbox management."""

import sys
import subprocess
import click
from pathlib import Path
from typing import Optional
from datetime import datetime
import os

# Fix Windows console encoding issues
if sys.platform == "win32":
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')


@click.group()
def sandbox():
    """
    Manage sandbox projects for testing and benchmarking.

    Sandbox projects are isolated environments for validating
    GAO-Dev's autonomous capabilities. Use these commands to
    create, manage, and benchmark test projects.

    Examples:
        gao-dev sandbox init my-project
        gao-dev sandbox list
        gao-dev sandbox run benchmarks/todo-baseline.yaml
    """
    pass


@sandbox.command()
@click.argument("project_name")
@click.option(
    "--config",
    type=click.Path(exists=True),
    help="Configuration file for sandbox project",
)
@click.option(
    "--boilerplate",
    type=str,
    help="Boilerplate repository URL or path",
)
@click.option(
    "--no-git",
    is_flag=True,
    help="Skip git initialization",
)
@click.option(
    "--tags",
    multiple=True,
    help="Project tags (can be specified multiple times)",
)
@click.option(
    "--description",
    type=str,
    default="",
    help="Project description",
)
def init(
    project_name: str,
    config: Optional[str],
    boilerplate: Optional[str],
    no_git: bool,
    tags: tuple,
    description: str,
):
    """
    Initialize a new sandbox project.

    Creates an isolated sandbox environment for testing GAO-Dev
    capabilities. The project will be created in the sandbox/projects/
    directory.

    Examples:
        gao-dev sandbox init todo-app-001
        gao-dev sandbox init my-project --boilerplate https://github.com/user/starter
        gao-dev sandbox init test-project --tags experiment --tags nextjs
    """
    try:
        from ..sandbox import SandboxManager, ProjectExistsError, InvalidProjectNameError

        click.echo(f">> Initializing sandbox project: {project_name}")

        # Get sandbox root (current directory/sandbox)
        sandbox_root = Path.cwd() / "sandbox"
        manager = SandboxManager(sandbox_root)

        # Check if project already exists
        if manager.project_exists(project_name):
            click.echo(f"\n[ERROR] Project '{project_name}' already exists", err=True)
            click.echo(f"  Use 'gao-dev sandbox clean {project_name}' to reset it")
            sys.exit(1)

        # Create project
        click.echo("  Creating project directory structure...")
        metadata = manager.create_project(
            name=project_name,
            boilerplate_url=boilerplate,
            tags=list(tags) if tags else [],
            description=description,
        )

        project_path = manager.get_project_path(project_name)
        click.echo("  [OK] Project directory created")

        # Create README
        _create_project_readme(project_path, metadata, boilerplate)
        click.echo("  [OK] README.md created")

        # Initialize git (unless --no-git)
        if not no_git:
            if _init_git_repo(project_path):
                click.echo("  [OK] Git repository initialized")
            else:
                click.echo("  [WARN] Git initialization failed (continuing anyway)")

        # Load config if provided
        if config:
            click.echo(f"  [INFO] Config file: {config}")
            # Config loading will be implemented in Epic 2

        # Success summary
        click.echo("\n[OK] Project initialized successfully!")
        click.echo(f"\n  Project: {project_name}")
        click.echo(f"  Location: {project_path}")
        click.echo(f"  Status: {metadata.status.value}")
        if tags:
            click.echo(f"  Tags: {', '.join(tags)}")
        if boilerplate:
            click.echo(f"  Boilerplate: {boilerplate}")

        click.echo("\nNext steps:")
        click.echo(f"  1. cd {project_path}")
        click.echo("  2. Add your project files")
        click.echo("  3. Run: gao-dev sandbox run <benchmark-config>")

    except InvalidProjectNameError as e:
        click.echo(f"\n[ERROR] Invalid project name: {e}", err=True)
        click.echo("\nProject names must:")
        click.echo("  - Be 3-50 characters long")
        click.echo("  - Start and end with alphanumeric character")
        click.echo("  - Contain only lowercase letters, numbers, and hyphens")
        click.echo("  - Not contain consecutive hyphens")
        sys.exit(1)

    except ProjectExistsError as e:
        click.echo(f"\n[ERROR] {e}", err=True)
        sys.exit(1)

    except Exception as e:
        click.echo(f"\n[ERROR] Unexpected error: {e}", err=True)
        sys.exit(1)


@sandbox.command()
@click.argument("project_name", required=False)
@click.option(
    "--all",
    is_flag=True,
    help="Clean all sandbox projects",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force clean without confirmation",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deleted without actually deleting",
)
@click.option(
    "--output-only",
    is_flag=True,
    help="Only remove generated output files",
)
@click.option(
    "--runs-only",
    is_flag=True,
    help="Only clear run history",
)
@click.option(
    "--full",
    is_flag=True,
    help="Full reset (removes all files except metadata)",
)
def clean(
    project_name: Optional[str],
    all: bool,
    force: bool,
    dry_run: bool,
    output_only: bool,
    runs_only: bool,
    full: bool,
):
    """
    Reset sandbox project to clean state.

    Removes generated files and resets the project to its initial state.
    Use --all to clean all sandbox projects, or specify a project name
    to clean a specific project.

    Examples:
        gao-dev sandbox clean todo-app-001
        gao-dev sandbox clean --all
        gao-dev sandbox clean my-project --force
        gao-dev sandbox clean test-project --output-only --dry-run
    """
    try:
        from ..sandbox import SandboxManager, ProjectNotFoundError

        # Validate arguments
        if not all and not project_name:
            click.echo("[ERROR] Please specify a project name or use --all", err=True)
            sys.exit(1)

        # Get manager
        sandbox_root = Path.cwd() / "sandbox"
        manager = SandboxManager(sandbox_root)

        # Get projects to clean
        if all:
            projects = [p.name for p in manager.list_projects()]
            if not projects:
                click.echo("[INFO] No projects to clean")
                return
        else:
            projects = [project_name]

        # Confirmation (unless --force or --dry-run)
        if not force and not dry_run:
            mode_str = "runs-only" if runs_only else "output-only" if output_only else "full" if full else "standard"
            project_list = ", ".join(projects)
            if not click.confirm(
                f"Clean {len(projects)} project(s) ({mode_str} mode): {project_list}?"
            ):
                click.echo("[CANCELLED] Cleaning cancelled")
                return

        # Clean projects
        total_stats = {"files_deleted": 0, "dirs_deleted": 0, "runs_cleared": 0}

        for proj_name in projects:
            try:
                if dry_run:
                    click.echo(f">> [DRY RUN] Would clean project: {proj_name}")
                else:
                    click.echo(f">> Cleaning project: {proj_name}")

                    stats = manager.clean_project(
                        proj_name,
                        full=full,
                        output_only=output_only,
                        runs_only=runs_only,
                    )

                    if runs_only:
                        click.echo(f"  [OK] Cleared {stats['runs_cleared']} run(s)")
                    else:
                        click.echo(
                            f"  [OK] Removed {stats['files_deleted']} file(s), "
                            f"{stats['dirs_deleted']} dir(s)"
                        )

                    # Update totals
                    for key in total_stats:
                        total_stats[key] += stats[key]

            except ProjectNotFoundError as e:
                click.echo(f"  [ERROR] {e}", err=True)
                continue

        # Summary
        if not dry_run:
            click.echo(f"\n[OK] Cleaned {len(projects)} project(s)")
            if runs_only:
                click.echo(f"  Total runs cleared: {total_stats['runs_cleared']}")
            else:
                click.echo(
                    f"  Total files deleted: {total_stats['files_deleted']}"
                )
                click.echo(f"  Total dirs deleted: {total_stats['dirs_deleted']}")

    except Exception as e:
        click.echo(f"\n[ERROR] Unexpected error: {e}", err=True)
        sys.exit(1)


@sandbox.command()
@click.option(
    "--status",
    type=click.Choice(["active", "completed", "failed", "archived", "all"]),
    default="all",
    help="Filter projects by status",
)
@click.option(
    "--format",
    type=click.Choice(["table", "json", "simple"]),
    default="table",
    help="Output format",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed information",
)
def list(status: str, format: str, verbose: bool):
    """
    List all sandbox projects.

    Displays information about sandbox projects including their status,
    creation date, and key metrics. Use filters to narrow down the list.

    Examples:
        gao-dev sandbox list
        gao-dev sandbox list --status active
        gao-dev sandbox list --format json
        gao-dev sandbox list --verbose
    """
    try:
        from ..sandbox import SandboxManager, ProjectStatus

        # Get manager
        sandbox_root = Path.cwd() / "sandbox"
        manager = SandboxManager(sandbox_root)

        # Get projects
        status_filter = ProjectStatus(status) if status != "all" else None
        projects = manager.list_projects(status=status_filter)

        if not projects:
            click.echo("[INFO] No projects found")
            return

        # Output based on format
        if format == "table":
            _print_table(projects, verbose)
        elif format == "json":
            _print_json(projects)
        elif format == "simple":
            _print_simple(projects)

    except Exception as e:
        click.echo(f"\n[ERROR] Unexpected error: {e}", err=True)
        sys.exit(1)


@sandbox.command()
@click.argument("benchmark_config", type=click.Path(exists=True))
@click.option(
    "--project",
    type=str,
    help="Use existing sandbox project (otherwise creates new one)",
)
@click.option(
    "--timeout",
    type=int,
    default=3600,
    help="Timeout in seconds (default: 3600 = 1 hour)",
)
@click.option(
    "--api-key",
    type=str,
    envvar="ANTHROPIC_API_KEY",
    help="Anthropic API key for agent spawning (or add to .env file)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Setup project but don't execute (for testing)",
)
def run(
    benchmark_config: str,
    project: Optional[str],
    timeout: int,
    api_key: Optional[str],
    dry_run: bool,
):
    """
    Execute a benchmark run with auto-generated run ID.

    Loads the benchmark configuration, auto-generates a sequential run ID,
    sets up the sandbox project, and executes the benchmark using GAO-Dev agents.

    The run ID follows the scientific method: benchmark-name-run-NNN

    Examples:
        gao-dev sandbox run benchmarks/todo-baseline.yaml
        gao-dev sandbox run benchmarks/custom.yaml --timeout 7200
        gao-dev sandbox run benchmarks/todo-baseline.yaml --dry-run

    This command now provides FULL AUTONOMOUS EXECUTION with real-time monitoring.
    """
    try:
        from pathlib import Path
        from gao_dev.sandbox import SandboxManager
        from gao_dev.sandbox.benchmark import BenchmarkRunner
        from gao_dev.sandbox.benchmark.config import BenchmarkConfig
        from gao_dev.sandbox.metrics.collector import MetricsCollector
        from gao_dev.core.env_config import get_env_config

        # Load environment config (.env file)
        env_config = get_env_config()

        # Get API key with fallback: CLI arg > .env file > environment variable
        api_key = env_config.get_anthropic_api_key(api_key)

        click.echo(f"\n>> Reading benchmark: {benchmark_config}")

        # Load and validate benchmark
        benchmark_file = Path(benchmark_config)
        try:
            config = BenchmarkConfig.from_yaml(benchmark_file)
        except Exception as e:
            click.echo(f"\n[ERROR] Failed to load benchmark: {e}", err=True)
            sys.exit(1)

        click.echo(f"  Benchmark: {config.name} v{config.version}")
        click.echo(f"  Complexity: Level {config.complexity_level}")
        click.echo(f"  Estimated: {config.estimated_duration_minutes} minutes")

        # Initialize sandbox manager
        sandbox_root = Path.cwd() / "sandbox"
        manager = SandboxManager(sandbox_root)

        # Check if using existing project or creating new one
        if project:
            # Use existing project
            if not manager.project_exists(project):
                click.echo(f"\n[ERROR] Project not found: {project}", err=True)
                sys.exit(1)

            click.echo(f"\n>> Using existing project: {project}")
            metadata = manager.get_project(project)
            run_id = project

        else:
            # Auto-generate run ID
            last_run = manager.get_last_run_number(config.name)
            next_run = last_run + 1

            click.echo("\n>> Auto-generating run ID...")
            if last_run > 0:
                click.echo(f"  Last run: {config.name}-run-{last_run:03d}")
            else:
                click.echo("  No previous runs found")

            click.echo(f"  Creating: {config.name}-run-{next_run:03d}")

            # Create project with auto-generated ID
            metadata = manager.create_run_project(benchmark_file, config)
            run_id = metadata.name

            click.echo(f"\n>> Project created: sandbox/projects/{run_id}")

            # Create project structure
            project_path = manager.get_project_path(run_id)
            _create_project_readme(project_path, metadata, config.boilerplate_url)

            if not config.boilerplate_url:
                click.echo("  Note: No boilerplate specified, starting from empty project")

        # Display prompt hash for verification
        click.echo("\n>> Benchmark Details:")
        click.echo(f"  Prompt hash: {config.prompt_hash[:16]}...")
        click.echo(f"  Description: {config.description}")

        # Display initial prompt (first 300 chars)
        prompt_preview = config.initial_prompt[:300].strip()
        if len(config.initial_prompt) > 300:
            prompt_preview += "..."

        click.echo("\n>> Initial Prompt:")
        click.echo("  " + "-" * 70)
        for line in prompt_preview.split("\n"):
            click.echo(f"  {line}")
        click.echo("  " + "-" * 70)

        if dry_run:
            click.echo("\n[DRY RUN] Stopping before execution")
            click.echo(f"  Project: sandbox/projects/{run_id}")
            click.echo("  Remove --dry-run flag to execute benchmark")
            return

        # Check for API key - optional now, interactive mode is preferred
        if not api_key:
            click.echo("\n[INFO] No API key detected - Interactive mode recommended")
            click.echo("")
            click.echo("For autonomous execution, you have three options:")
            click.echo("")
            click.echo("  Option 1: .env File (Recommended for development)")
            click.echo("    1. Copy .env.example to .env")
            click.echo("    2. Add your API key: ANTHROPIC_API_KEY=sk-ant-...")
            click.echo(f"    3. Run: gao-dev sandbox run {benchmark_config}")
            click.echo("")
            click.echo("  Option 2: Environment Variable")
            click.echo("    export ANTHROPIC_API_KEY=your-key  # Linux/Mac")
            click.echo("    set ANTHROPIC_API_KEY=your-key     # Windows CMD")
            click.echo(f"    gao-dev sandbox run {benchmark_config}")
            click.echo("")
            click.echo("  Option 3: Interactive Mode (No API Key Required)")
            click.echo("    Run this benchmark through Claude Code using Task tool:")
            click.echo("    Ask Claude: 'Please run this benchmark interactively:")
            click.echo(f"                  {benchmark_config}'")
            click.echo("")
            click.echo(f"Project setup completed. Run ID: {run_id}")
            click.echo("")
            return

        # Execute benchmark autonomously
        # Determine API key source for display
        api_key_source = "CLI argument"
        env_file = env_config.project_root / ".env"
        if env_file.exists() and not sys.argv.__contains__(api_key):
            api_key_source = ".env file"
        elif api_key and not sys.argv.__contains__(api_key):
            api_key_source = "environment variable"

        click.echo("\n>> Executing Benchmark Autonomously")
        click.echo("  Mode: Full autonomous execution with GAO-Dev agents")
        click.echo("  Real-time monitoring: ENABLED")
        click.echo("  Metrics collection: ENABLED")
        click.echo("  API: Anthropic Claude")
        click.echo(f"  API Key: {api_key[:10]}... (from {api_key_source})")
        click.echo("")

        # Initialize metrics collector
        metrics_collector = MetricsCollector()

        # Create benchmark runner with API key and pre-created project name
        runner = BenchmarkRunner(
            config=config,
            sandbox_manager=manager,
            metrics_collector=metrics_collector,
            sandbox_root=sandbox_root,
            api_key=api_key,
            project_name=run_id,  # Use the pre-created project
        )

        # Execute benchmark
        click.echo("=" * 80)
        click.echo("BENCHMARK EXECUTION STARTED")
        click.echo("=" * 80)
        click.echo("")

        result = runner.run()

        # Display results
        click.echo("")
        click.echo("=" * 80)
        click.echo("BENCHMARK EXECUTION COMPLETED")
        click.echo("=" * 80)
        click.echo("")
        click.echo(result.summary())

        if result.errors:
            click.echo("\n[ERRORS]")
            for error in result.errors:
                click.echo(f"  - {error}")

        if result.warnings:
            click.echo("\n[WARNINGS]")
            for warning in result.warnings:
                click.echo(f"  - {warning}")

        click.echo("\n>> Results saved to metrics database")
        click.echo(f"  Run ID: {result.run_id}")
        click.echo(f"  Generate report: gao-dev sandbox report run {result.run_id}")

        # Exit with appropriate code
        sys.exit(0 if result.status.value == "completed" else 1)

    except Exception as e:
        click.echo(f"\n[ERROR] Unexpected error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@sandbox.command(name="runs")
@click.argument("benchmark_name")
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed information for each run",
)
@click.option(
    "--format",
    type=click.Choice(["table", "json", "simple"]),
    default="table",
    help="Output format (default: table)",
)
def list_runs(benchmark_name: str, verbose: bool, format: str):
    """
    List all runs for a specific benchmark.

    Shows all benchmark runs in chronological order with key metrics.
    Use this to track improvement over time for a specific benchmark.

    Examples:
        gao-dev sandbox runs todo-app-baseline
        gao-dev sandbox runs simple-api-baseline -v
        gao-dev sandbox runs todo-app-baseline --format json
    """
    try:
        from pathlib import Path
        from gao_dev.sandbox import SandboxManager

        click.echo(f"\n>> Listing runs for: {benchmark_name}")

        # Initialize manager
        sandbox_root = Path.cwd() / "sandbox"
        manager = SandboxManager(sandbox_root)

        # Get all projects for this benchmark
        projects = manager.get_projects_for_benchmark(benchmark_name)

        if not projects:
            click.echo(f"\n[INFO] No runs found for benchmark: {benchmark_name}")
            click.echo(f"  Create a run with: gao-dev sandbox run benchmarks/{benchmark_name}.yaml")
            return

        # Sort by run number (extracted from name)
        def get_run_num(p):
            try:
                return int(p.name.split("-run-")[-1])
            except (ValueError, IndexError):
                return 0

        projects.sort(key=get_run_num)

        # Display based on format
        if format == "json":
            import json

            runs_data = []
            for p in projects:
                run_num = get_run_num(p)
                runs_data.append(
                    {
                        "run_number": run_num,
                        "run_id": p.name,
                        "status": p.status.value,
                        "created_at": p.created_at.isoformat(),
                        "run_count": p.get_run_count(),
                        "tags": p.tags,
                        "benchmark_info": p.benchmark_info,
                    }
                )

            click.echo(json.dumps(runs_data, indent=2))

        elif format == "simple":
            for p in projects:
                click.echo(p.name)

        else:
            # Table format
            click.echo(f"\nBenchmark: {benchmark_name}")
            click.echo("=" * 80)

            for p in projects:
                run_num = get_run_num(p)
                status_symbol = {
                    "active": "[ACTIVE]",
                    "completed": "[DONE]",
                    "failed": "[FAIL]",
                    "archived": "[ARCH]",
                }.get(p.status.value, "[????]")

                click.echo(f"\nRun {run_num:03d} | {status_symbol} | {p.name}")
                click.echo(f"  Created: {p.created_at.strftime('%Y-%m-%d %H:%M')}")

                if p.benchmark_info:
                    version = p.benchmark_info.get("benchmark_version", "unknown")
                    prompt_hash = p.benchmark_info.get("prompt_hash", "")[:16]
                    click.echo(f"  Version: {version} | Prompt: {prompt_hash}...")

                if verbose:
                    click.echo(f"  Description: {p.description}")
                    click.echo(f"  Tags: {', '.join(p.tags)}")
                    if p.get_run_count() > 0:
                        click.echo(f"  Runs: {p.get_run_count()}")

            click.echo("\n" + "=" * 80)
            click.echo(f"Total runs: {len(projects)}")

            # Show trend
            completed = sum(1 for p in projects if p.status.value == "completed")
            failed = sum(1 for p in projects if p.status.value == "failed")
            active = sum(1 for p in projects if p.status.value == "active")

            click.echo(f"\nStatus: {completed} completed | {failed} failed | {active} active")

        click.echo(f"\n[OK] Listed {len(projects)} runs for {benchmark_name}")

    except Exception as e:
        click.echo(f"\n[ERROR] Failed to list runs: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@sandbox.command()
@click.argument("run_id")
@click.option(
    "--output",
    type=click.Path(),
    help="Output file path (default: stdout)",
)
@click.option(
    "--format",
    type=click.Choice(["html", "markdown", "json"]),
    default="html",
    help="Report format",
)
def report(run_id: str, output: Optional[str], format: str):
    """
    Generate report for benchmark run.

    Creates a comprehensive report showing metrics, timeline, and results
    for a completed benchmark run.

    Examples:
        gao-dev sandbox report run-001
        gao-dev sandbox report run-001 --format markdown
        gao-dev sandbox report run-001 --output ./reports/run-001.html
    """
    click.echo(f">> Generating report for run: {run_id}")
    click.echo(f"  Format: {format}")

    if output:
        click.echo(f"  Output: {output}")
    else:
        click.echo("  Output: stdout")

    # Implementation will be added in Epic 5
    click.echo("\n  [PENDING] Report generation")
    click.echo("  [PENDING] This feature will be implemented in Epic 5")

    click.echo("\n[INFO] Sandbox report command structure ready")


@sandbox.command()
@click.argument("run1")
@click.argument("run2")
@click.option(
    "--output",
    type=click.Path(),
    help="Output file path (default: stdout)",
)
@click.option(
    "--format",
    type=click.Choice(["html", "markdown", "json", "table"]),
    default="table",
    help="Comparison format",
)
def compare(run1: str, run2: str, output: Optional[str], format: str):
    """
    Compare two benchmark runs.

    Shows side-by-side comparison of metrics, highlighting improvements
    or regressions between two benchmark runs.

    Examples:
        gao-dev sandbox compare run-001 run-002
        gao-dev sandbox compare baseline latest --format html
        gao-dev sandbox compare run-001 run-002 --output comparison.html
    """
    click.echo(f">> Comparing runs: {run1} vs {run2}")
    click.echo(f"  Format: {format}")

    if output:
        click.echo(f"  Output: {output}")
    else:
        click.echo("  Output: stdout")

    # Implementation will be added in Epic 5
    click.echo("\n  [PENDING] Run comparison")
    click.echo("  [PENDING] This feature will be implemented in Epic 5")

    click.echo("\n[INFO] Sandbox compare command structure ready")


@sandbox.command()
@click.argument("project_name")
@click.option(
    "--force",
    is_flag=True,
    help="Force delete without confirmation",
)
def delete(project_name: str, force: bool):
    """
    Delete a sandbox project.

    Permanently removes a sandbox project and all associated files.
    Use with caution - this cannot be undone.

    Examples:
        gao-dev sandbox delete old-project
        gao-dev sandbox delete test-project --force
    """
    click.echo(f">> Deleting sandbox project: {project_name}")

    if not force:
        if not click.confirm(f"Are you sure you want to delete '{project_name}'?"):
            click.echo("[CANCELLED] Project not deleted")
            return

    # Implementation will be added in Story 1.6 or Epic 2
    click.echo("\n  [PENDING] Project deletion")
    click.echo("  [PENDING] This feature will be implemented later")

    click.echo("\n[INFO] Sandbox delete command structure ready")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _create_project_readme(project_path: Path, metadata, boilerplate_url: Optional[str]) -> None:
    """Create README.md file for sandbox project."""
    from ..sandbox import ProjectMetadata

    metadata: ProjectMetadata = metadata

    readme_content = f"""# {metadata.name}

**Sandbox Project**

## Project Information

- **Created**: {metadata.created_at.strftime('%Y-%m-%d %H:%M:%S')}
- **Status**: {metadata.status.value}
- **Description**: {metadata.description or 'No description provided'}

## Tags

{', '.join(f'`{tag}`' for tag in metadata.tags) if metadata.tags else 'No tags'}

## Boilerplate

{f'This project uses boilerplate from: {boilerplate_url}' if boilerplate_url else 'No boilerplate specified'}

## Directory Structure

```
{metadata.name}/
├── docs/           # Documentation
├── src/            # Source code
├── tests/          # Test files
├── benchmarks/     # Benchmark configurations
├── .gao-dev/       # GAO-Dev metadata
├── .sandbox.yaml   # Sandbox metadata
└── README.md       # This file
```

## Usage

This is a GAO-Dev sandbox project for testing and benchmarking.

### Running Benchmarks

```bash
gao-dev sandbox run benchmarks/your-config.yaml
```

### Viewing Project Status

```bash
gao-dev sandbox list --format table
```

### Cleaning Project

```bash
gao-dev sandbox clean {metadata.name}
```

## Notes

- This project is managed by GAO-Dev's sandbox system
- Project metadata is stored in `.sandbox.yaml`
- Do not manually edit `.sandbox.yaml` unless you know what you're doing

---

*Generated by GAO-Dev Sandbox System on {datetime.now().strftime('%Y-%m-%d')}*
"""

    readme_path = project_path / "README.md"
    readme_path.write_text(readme_content, encoding="utf-8")


def _init_git_repo(project_path: Path) -> bool:
    """
    Initialize git repository in project directory.

    Returns True if successful, False otherwise.
    """
    try:
        # Check if git is available
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            cwd=project_path,
        )

        if result.returncode != 0:
            return False

        # Initialize git repo
        result = subprocess.run(
            ["git", "init"],
            capture_output=True,
            text=True,
            cwd=project_path,
        )

        if result.returncode != 0:
            return False

        # Create .gitignore
        gitignore_content = """# GAO-Dev Sandbox
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/

# Node
node_modules/
npm-debug.log
yarn-error.log

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Test coverage
.coverage
htmlcov/
.pytest_cache/

# Environments
.env
.venv
env/
venv/
"""
        gitignore_path = project_path / ".gitignore"
        gitignore_path.write_text(gitignore_content, encoding="utf-8")

        # Initial commit
        subprocess.run(["git", "add", "."], cwd=project_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit - GAO-Dev sandbox project"],
            cwd=project_path,
            capture_output=True,
        )

        return True

    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _print_table(projects: list, verbose: bool) -> None:
    """Print projects in table format."""
    from ..sandbox import ProjectMetadata

    projects_list: list[ProjectMetadata] = projects

    if not verbose:
        # Simple table
        click.echo("\n" + "-" * 80)
        click.echo(f"{'Project Name':<25} {'Status':<12} {'Created':<12} {'Runs':<8}")
        click.echo("-" * 80)

        for project in projects_list:
            created_str = project.created_at.strftime("%Y-%m-%d")
            runs = project.get_run_count()

            click.echo(
                f"{project.name:<25} {project.status.value:<12} "
                f"{created_str:<12} {runs:<8}"
            )

        click.echo("-" * 80)
        click.echo(f"Total: {len(projects_list)} project(s)\n")

    else:
        # Verbose table
        for project in projects_list:
            click.echo("\n" + "=" * 80)
            click.echo(f"Project: {project.name}")
            click.echo("=" * 80)
            click.echo(f"  Status: {project.status.value}")
            click.echo(f"  Created: {project.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo(f"  Modified: {project.last_modified.strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo(f"  Description: {project.description or 'No description'}")
            click.echo(f"  Tags: {', '.join(project.tags) if project.tags else 'None'}")
            click.echo(f"  Boilerplate: {project.boilerplate_url or 'None'}")
            click.echo(f"  Runs: {project.get_run_count()}")

            if project.runs:
                latest = project.get_latest_run()
                if latest:
                    click.echo(f"  Latest run: {latest.run_id} ({latest.status.value})")

        click.echo("\n" + "=" * 80)
        click.echo(f"Total: {len(projects_list)} project(s)\n")


def _print_json(projects: list) -> None:
    """Print projects in JSON format."""
    import json
    from ..sandbox import ProjectMetadata

    projects_list: list[ProjectMetadata] = projects

    data = [project.to_dict() for project in projects_list]
    click.echo(json.dumps(data, indent=2, default=str))


def _print_simple(projects: list) -> None:
    """Print projects in simple format (one per line)."""
    from ..sandbox import ProjectMetadata

    projects_list: list[ProjectMetadata] = projects

    for project in projects_list:
        click.echo(project.name)


# ============================================================================
# REPORT COMMANDS
# ============================================================================

# Import and register report commands
from .report_commands import report_group  # noqa: E402
sandbox.add_command(report_group)

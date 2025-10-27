"""CLI commands for GAO-Dev sandbox management."""

import sys
import subprocess
import click
from pathlib import Path
from typing import Optional
from datetime import datetime


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
        click.echo(f"  Creating project directory structure...")
        metadata = manager.create_project(
            name=project_name,
            boilerplate_url=boilerplate,
            tags=list(tags) if tags else [],
            description=description,
        )

        project_path = manager.get_project_path(project_name)
        click.echo(f"  [OK] Project directory created")

        # Create README
        _create_project_readme(project_path, metadata, boilerplate)
        click.echo(f"  [OK] README.md created")

        # Initialize git (unless --no-git)
        if not no_git:
            if _init_git_repo(project_path):
                click.echo(f"  [OK] Git repository initialized")
            else:
                click.echo(f"  [WARN] Git initialization failed (continuing anyway)")

        # Load config if provided
        if config:
            click.echo(f"  [INFO] Config file: {config}")
            # Config loading will be implemented in Epic 2

        # Success summary
        click.echo(f"\n[OK] Project initialized successfully!")
        click.echo(f"\n  Project: {project_name}")
        click.echo(f"  Location: {project_path}")
        click.echo(f"  Status: {metadata.status.value}")
        if tags:
            click.echo(f"  Tags: {', '.join(tags)}")
        if boilerplate:
            click.echo(f"  Boilerplate: {boilerplate}")

        click.echo(f"\nNext steps:")
        click.echo(f"  1. cd {project_path}")
        click.echo(f"  2. Add your project files")
        click.echo(f"  3. Run: gao-dev sandbox run <benchmark-config>")

    except InvalidProjectNameError as e:
        click.echo(f"\n[ERROR] Invalid project name: {e}", err=True)
        click.echo(f"\nProject names must:")
        click.echo(f"  - Be 3-50 characters long")
        click.echo(f"  - Start and end with alphanumeric character")
        click.echo(f"  - Contain only lowercase letters, numbers, and hyphens")
        click.echo(f"  - Not contain consecutive hyphens")
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
def clean(project_name: Optional[str], all: bool, force: bool):
    """
    Reset sandbox project to clean state.

    Removes generated files and resets the project to its initial state.
    Use --all to clean all sandbox projects, or specify a project name
    to clean a specific project.

    Examples:
        gao-dev sandbox clean todo-app-001
        gao-dev sandbox clean --all
        gao-dev sandbox clean my-project --force
    """
    if all:
        click.echo(">> Cleaning all sandbox projects")
    elif project_name:
        click.echo(f">> Cleaning sandbox project: {project_name}")
    else:
        click.echo("[ERROR] Please specify a project name or use --all")
        return

    # Implementation will be added in Story 1.5
    click.echo(f"  [PENDING] Project cleanup")
    click.echo(f"  [PENDING] This feature will be implemented in Story 1.5")

    if force:
        click.echo(f"  Force mode: enabled")

    click.echo("\n[INFO] Sandbox clean command structure ready")


@sandbox.command()
@click.option(
    "--status",
    type=click.Choice(["active", "completed", "failed", "all"]),
    default="all",
    help="Filter projects by status",
)
@click.option(
    "--format",
    type=click.Choice(["table", "json", "simple"]),
    default="table",
    help="Output format",
)
def list(status: str, format: str):
    """
    List all sandbox projects.

    Displays information about sandbox projects including their status,
    creation date, and key metrics. Use filters to narrow down the list.

    Examples:
        gao-dev sandbox list
        gao-dev sandbox list --status active
        gao-dev sandbox list --format json
    """
    click.echo(">> Listing sandbox projects")
    click.echo(f"  Filter: status={status}")
    click.echo(f"  Format: {format}")

    # Implementation will be added in Story 1.6
    click.echo(f"\n  [PENDING] Project listing")
    click.echo(f"  [PENDING] This feature will be implemented in Story 1.6")

    click.echo("\n[INFO] Sandbox list command structure ready")


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
    help="Anthropic API key (or set ANTHROPIC_API_KEY env var)",
)
def run(
    benchmark_config: str,
    project: Optional[str],
    timeout: int,
    api_key: Optional[str],
):
    """
    Execute a benchmark run.

    Runs a complete benchmark based on the provided configuration file.
    This executes the full BMAD workflow autonomously and collects metrics.

    Note: Requires Anthropic API key for autonomous agent execution.

    Examples:
        gao-dev sandbox run benchmarks/todo-baseline.yaml
        gao-dev sandbox run benchmarks/custom.yaml --timeout 7200
        gao-dev sandbox run benchmarks/test.yaml --project todo-app-001
    """
    click.echo(f">> Running benchmark: {benchmark_config}")

    if project:
        click.echo(f"  Using project: {project}")
    else:
        click.echo(f"  Creating new project")

    click.echo(f"  Timeout: {timeout}s")

    if not api_key:
        click.echo("\n[ERROR] Anthropic API key required")
        click.echo("  Set ANTHROPIC_API_KEY environment variable or use --api-key option")
        return

    # Implementation will be added in Epic 4
    click.echo(f"\n  [PENDING] Benchmark execution")
    click.echo(f"  [PENDING] This feature will be implemented in Epic 4")

    click.echo("\n[INFO] Sandbox run command structure ready")


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
        click.echo(f"  Output: stdout")

    # Implementation will be added in Epic 5
    click.echo(f"\n  [PENDING] Report generation")
    click.echo(f"  [PENDING] This feature will be implemented in Epic 5")

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
        click.echo(f"  Output: stdout")

    # Implementation will be added in Epic 5
    click.echo(f"\n  [PENDING] Run comparison")
    click.echo(f"  [PENDING] This feature will be implemented in Epic 5")

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
    click.echo(f"\n  [PENDING] Project deletion")
    click.echo(f"  [PENDING] This feature will be implemented later")

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

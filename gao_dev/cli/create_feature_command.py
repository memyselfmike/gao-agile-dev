"""CLI command for creating features.

This module provides the create-feature command for atomic feature creation
with file + database + git operations.

Epic: 33 - Atomic Feature Operations
Story: 33.3 - CLI Commands
"""

import click
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

import structlog

from ..core.services.git_integrated_state_manager import GitIntegratedStateManager
from ..core.services.document_structure_manager import DocumentStructureManager
from ..core.services.feature_state_service import FeatureScope
from ..core.git_manager import GitManager
from ..core.state_coordinator import StateCoordinator
from ..lifecycle.project_lifecycle import ProjectDocumentLifecycle

logger = structlog.get_logger(__name__)

# Initialize console for Rich output
if RICH_AVAILABLE:
    console = Console()


def _find_project_root() -> Path:
    """Find project root by searching for .gao-dev/ or .git/."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".gao-dev").exists() or (current / ".git").exists():
            return current
        current = current.parent
    raise ValueError("Not in a GAO-Dev project. Run from project directory.")


def _init_state_manager(project_root: Path) -> GitIntegratedStateManager:
    """Initialize GitIntegratedStateManager with all required dependencies.

    Sets up the full dependency chain:
    1. DocumentLifecycleManager (via ProjectDocumentLifecycle.initialize)
    2. GitManager
    3. DocumentStructureManager
    4. GitIntegratedStateManager
    """
    db_path = project_root / ".gao-dev" / "documents.db"

    # Create .gao-dev directory if it doesn't exist
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize document lifecycle
    doc_lifecycle = ProjectDocumentLifecycle.initialize(project_root, create_dirs=True)

    # Initialize GitManager
    git_manager = GitManager(project_path=project_root)

    # Initialize DocumentStructureManager
    doc_structure_manager = DocumentStructureManager(
        project_root=project_root,
        doc_lifecycle=doc_lifecycle,
        git_manager=git_manager
    )

    # Initialize GitIntegratedStateManager with doc_structure_manager
    manager = GitIntegratedStateManager(
        db_path=db_path,
        project_path=project_root,
        auto_commit=True,
        doc_structure_manager=doc_structure_manager
    )

    return manager


@click.command("create-feature")
@click.argument("name")
@click.option(
    "--scale-level",
    type=click.IntRange(0, 4),
    default=3,
    help="Project scale level (0=chore, 1=bug, 2=small, 3=medium, 4=large)"
)
@click.option(
    "--scope",
    type=click.Choice(["mvp", "feature"], case_sensitive=False),
    default="feature",
    help="Feature scope (mvp for initial scope, feature for subsequent)"
)
@click.option(
    "--description",
    type=str,
    default=None,
    help="Feature description"
)
@click.option(
    "--owner",
    type=str,
    default=None,
    help="Feature owner"
)
def create_feature(
    name: str,
    scale_level: int,
    scope: str,
    description: Optional[str],
    owner: Optional[str]
):
    """
    Create a new feature with atomic file + DB + git operation.

    Creates feature folder structure, registers in database, and commits to git
    in a single atomic operation. If any step fails, all changes are rolled back.

    Examples:

        # Create a feature with default settings
        gao-dev create-feature user-auth

        # Create MVP with custom scale level
        gao-dev create-feature mvp --scope mvp --scale-level 4

        # Create feature with full metadata
        gao-dev create-feature payment-processing \\
            --scale-level 3 \\
            --description "Payment gateway integration" \\
            --owner "john@example.com"
    """
    try:
        if RICH_AVAILABLE:
            console.print(f"\n[bold cyan]Creating feature:[/bold cyan] {name}")
        else:
            click.echo(f"\nCreating feature: {name}")

        # Auto-detect project root
        project_root = _find_project_root()

        # Initialize GitIntegratedStateManager
        manager = _init_state_manager(project_root)

        # Create feature (atomic operation)
        if RICH_AVAILABLE:
            with console.status(f"[bold green]Creating {name}...", spinner="dots"):
                feature = manager.create_feature(
                    name=name,
                    scope=FeatureScope[scope.upper()],
                    scale_level=scale_level,
                    description=description,
                    owner=owner
                )
        else:
            click.echo(f"Creating {name}...")
            feature = manager.create_feature(
                name=name,
                scope=FeatureScope[scope.upper()],
                scale_level=scale_level,
                description=description,
                owner=owner
            )

        # Success output
        if RICH_AVAILABLE:
            console.print(Panel(
                f"[bold green]Feature created successfully![/bold green]\n\n"
                f"Name: {feature.name}\n"
                f"Scope: {feature.scope.value}\n"
                f"Scale Level: {feature.scale_level}\n"
                f"Status: {feature.status.value}\n"
                f"Location: docs/features/{name}/\n\n"
                f"[bold]Next Steps:[/bold]\n"
                f"1. Review PRD: docs/features/{name}/PRD.md\n"
                f"2. Review Architecture: docs/features/{name}/ARCHITECTURE.md\n"
                f"3. Create epics: gao-dev create-epic {name} <epic-title>\n"
                f"4. View features: gao-dev list-features",
                title="Feature Created",
                border_style="green"
            ))
        else:
            click.echo("\n[OK] Feature created successfully!")
            click.echo(f"  Name: {feature.name}")
            click.echo(f"  Scope: {feature.scope.value}")
            click.echo(f"  Scale Level: {feature.scale_level}")
            click.echo(f"  Status: {feature.status.value}")
            click.echo(f"  Location: docs/features/{name}/")
            click.echo("\nNext steps:")
            click.echo(f"  1. Review PRD: docs/features/{name}/PRD.md")
            click.echo(f"  2. Review Architecture: docs/features/{name}/ARCHITECTURE.md")
            click.echo(f"  3. Create epics: gao-dev create-epic {name} <epic-title>")
            click.echo(f"  4. View features: gao-dev list-features")

    except ValueError as e:
        if RICH_AVAILABLE:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
        else:
            click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()
    except Exception as e:
        logger.error("Feature creation failed", error=str(e), exc_info=True)
        if RICH_AVAILABLE:
            console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}")
        else:
            click.echo(f"Unexpected error: {str(e)}", err=True)
        raise click.Abort()

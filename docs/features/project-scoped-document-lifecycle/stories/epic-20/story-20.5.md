# Story 20.5: Update Lifecycle CLI Commands

**Epic**: Epic 20 - Project-Scoped Document Lifecycle
**Status**: Ready
**Priority**: P1 (High)
**Estimated Effort**: 3 story points
**Owner**: Amelia (Developer)
**Created**: 2025-11-06

---

## User Story

**As a** GAO-Dev user
**I want** lifecycle CLI commands to operate on the correct project
**So that** document operations affect the intended project's `.gao-dev/` database

---

## Acceptance Criteria

### AC1: All Commands Use Project Detection

- ✅ `lifecycle list` detects project root
- ✅ `lifecycle register` detects project root
- ✅ `lifecycle update` detects project root
- ✅ `lifecycle archive` detects project root
- ✅ `lifecycle restore` detects project root
- ✅ All commands replace `Path.cwd()` with `detect_project_root()`

### AC2: --project Option Added

- ✅ All lifecycle commands accept `--project` option
- ✅ `--project` option overrides automatic detection
- ✅ `--project` validates that path exists
- ✅ Clear error message if project path invalid
- ✅ Help text explains project scoping

### AC3: Project Context Displayed

- ✅ Commands show which project they're operating on
- ✅ Project name displayed in output
- ✅ Project path logged for debugging
- ✅ Warning if operating outside known project

### AC4: Error Handling

- ✅ Clear error if `.gao-dev/` not initialized
- ✅ Helpful message suggesting initialization
- ✅ Validates project structure before operations
- ✅ Graceful handling of missing database

### AC5: Integration Tests

- ✅ Test: `test_lifecycle_list_detects_project()` - Auto-detection works
- ✅ Test: `test_lifecycle_with_project_option()` - Manual targeting works
- ✅ Test: `test_lifecycle_from_subdirectory()` - Works from subdirs
- ✅ Test: `test_lifecycle_uninitialized_project()` - Error handling
- ✅ All tests pass

---

## Technical Details

### File Structure

```
gao_dev/cli/
├── lifecycle_commands.py    # UPDATE: All lifecycle commands
└── project_detection.py     # EXISTING: Detection utilities
```

### Implementation Approach

**Step 1: Update lifecycle_commands.py - Common Utilities**

Add helper functions used by all commands:

```python
# In gao_dev/cli/lifecycle_commands.py

import click
from pathlib import Path
from typing import Optional
import structlog

from gao_dev.cli.project_detection import detect_project_root, is_project_root
from gao_dev.lifecycle.project_lifecycle import ProjectDocumentLifecycle
from gao_dev.lifecycle.manager import DocumentLifecycleManager

logger = structlog.get_logger(__name__)


def get_project_lifecycle(
    project: Optional[str],
    require_initialized: bool = True
) -> tuple[Path, DocumentLifecycleManager]:
    """
    Get project root and document lifecycle manager.

    Args:
        project: Optional explicit project path
        require_initialized: Whether to require .gao-dev/ to exist

    Returns:
        Tuple of (project_root, doc_manager)

    Raises:
        click.ClickException: If project invalid or not initialized
    """
    # Detect or use provided project
    if project:
        project_root = Path(project)
        if not project_root.exists():
            raise click.ClickException(f"Project path does not exist: {project}")
    else:
        project_root = detect_project_root()

    logger.debug("Project detected", project_root=str(project_root))

    # Check if initialized
    if require_initialized and not ProjectDocumentLifecycle.is_initialized(project_root):
        raise click.ClickException(
            f"Document lifecycle not initialized for project: {project_root.name}\n"
            f"Project path: {project_root}\n\n"
            f"To initialize, run:\n"
            f"  gao-dev sandbox init {project_root.name}  (for new projects)\n"
            f"Or contact a maintainer to initialize existing projects."
        )

    # Initialize lifecycle
    try:
        doc_manager = ProjectDocumentLifecycle.initialize(project_root)
        return project_root, doc_manager
    except Exception as e:
        logger.error("Failed to initialize lifecycle", error=str(e))
        raise click.ClickException(f"Failed to initialize document lifecycle: {e}")


def display_project_context(project_root: Path) -> None:
    """
    Display project context information.

    Args:
        project_root: Project root directory
    """
    click.echo(f"Project: {click.style(project_root.name, fg='cyan', bold=True)}")
    click.echo(f"Location: {project_root}")
    click.echo()
```

**Step 2: Update lifecycle list Command**

```python
@click.command()
@click.option(
    '--project',
    type=click.Path(exists=True),
    help='Project directory (defaults to detected project root)',
)
@click.option('--state', type=str, help='Filter by document state')
@click.option('--type', 'doc_type', type=str, help='Filter by document type')
def list(project: Optional[str], state: Optional[str], doc_type: Optional[str]):
    """
    List all documents in the project.

    Automatically detects the project root by searching for .gao-dev/
    or .sandbox.yaml markers. You can override this with --project.

    Examples:
        # List from within a project
        gao-dev lifecycle list

        # List specific project
        gao-dev lifecycle list --project sandbox/projects/my-app

        # Filter by state
        gao-dev lifecycle list --state active

        # Filter by type
        gao-dev lifecycle list --type product-requirements
    """
    # Get project and lifecycle manager
    project_root, doc_manager = get_project_lifecycle(project)

    # Display context
    display_project_context(project_root)

    # List documents with filters
    documents = doc_manager.registry.list_documents(
        state=state,
        doc_type=doc_type
    )

    if not documents:
        click.echo("No documents found.")
        return

    # Display results
    click.echo(f"Found {len(documents)} document(s):\n")

    for doc in documents:
        click.echo(f"  {click.style(doc.path, fg='green')}")
        click.echo(f"    Type: {doc.doc_type}")
        click.echo(f"    State: {doc.state}")
        if doc.metadata:
            click.echo(f"    Metadata: {doc.metadata}")
        click.echo()
```

**Step 3: Update lifecycle register Command**

```python
@click.command()
@click.argument('path', type=click.Path(exists=True))
@click.argument('doc_type')
@click.option(
    '--project',
    type=click.Path(exists=True),
    help='Project directory (defaults to detected project root)',
)
@click.option('--metadata', type=str, help='JSON metadata for the document')
def register(
    path: str,
    doc_type: str,
    project: Optional[str],
    metadata: Optional[str]
):
    """
    Register a document in the lifecycle system.

    PATH is the path to the document (relative to project root)
    DOC_TYPE is the type of document (e.g., product-requirements, architecture)

    Examples:
        # Register PRD
        gao-dev lifecycle register docs/PRD.md product-requirements

        # Register with metadata
        gao-dev lifecycle register docs/ARCH.md architecture --metadata '{"version": "1.0"}'

        # Register for specific project
        gao-dev lifecycle register docs/PRD.md product-requirements --project sandbox/projects/my-app
    """
    # Get project and lifecycle manager
    project_root, doc_manager = get_project_lifecycle(project)

    # Display context
    display_project_context(project_root)

    # Parse metadata if provided
    doc_metadata = {}
    if metadata:
        import json
        try:
            doc_metadata = json.loads(metadata)
        except json.JSONDecodeError as e:
            raise click.ClickException(f"Invalid JSON metadata: {e}")

    # Register document
    try:
        # Convert to relative path if absolute
        doc_path = Path(path)
        if doc_path.is_absolute():
            try:
                doc_path = doc_path.relative_to(project_root)
            except ValueError:
                raise click.ClickException(
                    f"Document path must be within project: {path}"
                )

        doc_manager.registry.register_document(
            path=str(doc_path),
            doc_type=doc_type,
            metadata=doc_metadata
        )

        click.echo(f"{click.style('SUCCESS', fg='green')} Document registered: {doc_path}")

    except Exception as e:
        logger.error("Failed to register document", error=str(e))
        raise click.ClickException(f"Failed to register document: {e}")
```

**Step 4: Update lifecycle update Command**

```python
@click.command()
@click.argument('path')
@click.option(
    '--project',
    type=click.Path(exists=True),
    help='Project directory (defaults to detected project root)',
)
@click.option('--state', type=str, help='New state for the document')
@click.option('--metadata', type=str, help='JSON metadata to update')
def update(
    path: str,
    project: Optional[str],
    state: Optional[str],
    metadata: Optional[str]
):
    """
    Update a document's metadata or state.

    Examples:
        # Update state
        gao-dev lifecycle update docs/PRD.md --state archived

        # Update metadata
        gao-dev lifecycle update docs/PRD.md --metadata '{"version": "2.0"}'

        # Update for specific project
        gao-dev lifecycle update docs/PRD.md --state active --project sandbox/projects/my-app
    """
    # Get project and lifecycle manager
    project_root, doc_manager = get_project_lifecycle(project)

    # Display context
    display_project_context(project_root)

    # Parse metadata if provided
    doc_metadata = None
    if metadata:
        import json
        try:
            doc_metadata = json.loads(metadata)
        except json.JSONDecodeError as e:
            raise click.ClickException(f"Invalid JSON metadata: {e}")

    # Update document
    try:
        doc_manager.registry.update_document(
            path=path,
            state=state,
            metadata=doc_metadata
        )

        click.echo(f"{click.style('SUCCESS', fg='green')} Document updated: {path}")

    except Exception as e:
        logger.error("Failed to update document", error=str(e))
        raise click.ClickException(f"Failed to update document: {e}")
```

**Step 5: Update lifecycle archive Command**

```python
@click.command()
@click.argument('path')
@click.option(
    '--project',
    type=click.Path(exists=True),
    help='Project directory (defaults to detected project root)',
)
@click.option('--reason', type=str, help='Reason for archiving')
def archive(path: str, project: Optional[str], reason: Optional[str]):
    """
    Archive a document.

    Moves the document to the .archive/ directory and updates its
    state in the registry.

    Examples:
        # Archive document
        gao-dev lifecycle archive docs/OLD_PRD.md

        # Archive with reason
        gao-dev lifecycle archive docs/OLD_PRD.md --reason "Replaced by v2"

        # Archive in specific project
        gao-dev lifecycle archive docs/OLD_PRD.md --project sandbox/projects/my-app
    """
    # Get project and lifecycle manager
    project_root, doc_manager = get_project_lifecycle(project)

    # Display context
    display_project_context(project_root)

    # Archive document
    try:
        doc_manager.archive_document(path, reason=reason)

        click.echo(f"{click.style('SUCCESS', fg='green')} Document archived: {path}")
        click.echo(f"Moved to: {project_root / '.archive'}")

    except Exception as e:
        logger.error("Failed to archive document", error=str(e))
        raise click.ClickException(f"Failed to archive document: {e}")
```

**Step 6: Update lifecycle restore Command**

```python
@click.command()
@click.argument('path')
@click.option(
    '--project',
    type=click.Path(exists=True),
    help='Project directory (defaults to detected project root)',
)
@click.option('--destination', type=str, help='Destination path (defaults to original)')
def restore(path: str, project: Optional[str], destination: Optional[str]):
    """
    Restore an archived document.

    Moves the document from .archive/ back to the docs/ directory
    and updates its state to active.

    Examples:
        # Restore document
        gao-dev lifecycle restore OLD_PRD.md

        # Restore to different location
        gao-dev lifecycle restore OLD_PRD.md --destination docs/archive/OLD_PRD.md

        # Restore in specific project
        gao-dev lifecycle restore OLD_PRD.md --project sandbox/projects/my-app
    """
    # Get project and lifecycle manager
    project_root, doc_manager = get_project_lifecycle(project)

    # Display context
    display_project_context(project_root)

    # Restore document
    try:
        doc_manager.restore_document(path, destination=destination)

        click.echo(f"{click.style('SUCCESS', fg='green')} Document restored: {path}")

    except Exception as e:
        logger.error("Failed to restore document", error=str(e))
        raise click.ClickException(f"Failed to restore document: {e}")
```

**Step 7: Update Command Group Registration**

```python
# At bottom of lifecycle_commands.py

# Create command group
@click.group()
def lifecycle():
    """
    Document lifecycle management commands.

    These commands help track and manage documentation throughout
    its lifecycle. All commands operate on project-scoped document
    lifecycle systems (.gao-dev/documents.db).

    The project root is automatically detected by searching for
    .gao-dev/ or .sandbox.yaml markers. You can override this
    with the --project option on any command.
    """
    pass


# Add commands to group
lifecycle.add_command(list)
lifecycle.add_command(register)
lifecycle.add_command(update)
lifecycle.add_command(archive)
lifecycle.add_command(restore)
```

---

## Testing Approach

### Integration Tests

Create `tests/cli/test_lifecycle_commands.py`:

```python
"""Integration tests for lifecycle CLI commands."""

import pytest
from pathlib import Path
from click.testing import CliRunner
import tempfile
import shutil

from gao_dev.cli.lifecycle_commands import lifecycle
from gao_dev.lifecycle.project_lifecycle import ProjectDocumentLifecycle


class TestLifecycleCommands:
    """Test suite for lifecycle CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def test_project(self):
        """Create test project with initialized lifecycle."""
        temp_dir = Path(tempfile.mkdtemp())
        project_dir = temp_dir / "test-app"
        project_dir.mkdir()

        # Initialize document lifecycle
        ProjectDocumentLifecycle.initialize(project_dir)

        # Create test document
        docs_dir = project_dir / "docs"
        docs_dir.mkdir()
        (docs_dir / "TEST.md").write_text("# Test Document")

        yield project_dir
        shutil.rmtree(temp_dir)

    def test_lifecycle_list_detects_project(self, runner, test_project, monkeypatch):
        """Test that list command detects project root."""
        # Change to project directory
        monkeypatch.chdir(test_project)

        # Run list command
        result = runner.invoke(lifecycle, ['list'])

        assert result.exit_code == 0
        assert test_project.name in result.output

    def test_lifecycle_with_project_option(self, runner, test_project):
        """Test explicit project targeting with --project option."""
        result = runner.invoke(lifecycle, ['list', '--project', str(test_project)])

        assert result.exit_code == 0
        assert test_project.name in result.output

    def test_lifecycle_from_subdirectory(self, runner, test_project, monkeypatch):
        """Test commands work from project subdirectories."""
        # Change to subdirectory
        subdir = test_project / "docs"
        monkeypatch.chdir(subdir)

        # Run list command
        result = runner.invoke(lifecycle, ['list'])

        assert result.exit_code == 0
        assert test_project.name in result.output

    def test_lifecycle_uninitialized_project(self, runner, tmp_path, monkeypatch):
        """Test error handling for uninitialized projects."""
        # Change to directory without .gao-dev/
        monkeypatch.chdir(tmp_path)

        # Run list command
        result = runner.invoke(lifecycle, ['list'])

        assert result.exit_code != 0
        assert "not initialized" in result.output.lower()

    def test_lifecycle_register_command(self, runner, test_project):
        """Test register command."""
        doc_path = test_project / "docs" / "TEST.md"

        result = runner.invoke(lifecycle, [
            'register',
            str(doc_path),
            'test-doc',
            '--project', str(test_project)
        ])

        assert result.exit_code == 0
        assert "SUCCESS" in result.output

    def test_lifecycle_update_command(self, runner, test_project):
        """Test update command."""
        # First register a document
        doc_manager = ProjectDocumentLifecycle.initialize(test_project)
        doc_manager.registry.register_document("docs/TEST.md", "test-doc", {})

        # Update it
        result = runner.invoke(lifecycle, [
            'update',
            'docs/TEST.md',
            '--state', 'archived',
            '--project', str(test_project)
        ])

        assert result.exit_code == 0
        assert "SUCCESS" in result.output

    def test_lifecycle_invalid_project_path(self, runner):
        """Test error handling for invalid project path."""
        result = runner.invoke(lifecycle, [
            'list',
            '--project', '/nonexistent/path'
        ])

        assert result.exit_code != 0
        assert "does not exist" in result.output.lower()

    def test_lifecycle_project_context_displayed(self, runner, test_project):
        """Test that project context is displayed in output."""
        result = runner.invoke(lifecycle, [
            'list',
            '--project', str(test_project)
        ])

        assert result.exit_code == 0
        assert "Project:" in result.output
        assert test_project.name in result.output
        assert "Location:" in result.output
```

Run tests:
```bash
pytest tests/cli/test_lifecycle_commands.py -v
```

---

## Dependencies

### Required Packages
- ✅ click (already installed)
- ✅ structlog (already installed)
- ✅ pytest (already installed)

### Code Dependencies
- Story 20.1: ProjectDocumentLifecycle factory class
- Story 20.4: Project root detection utilities
- `gao_dev.lifecycle.manager.DocumentLifecycleManager`

---

## Definition of Done

- [ ] All lifecycle commands updated to use `detect_project_root()`
- [ ] `--project` option added to all commands
- [ ] Helper functions `get_project_lifecycle()` and `display_project_context()` created
- [ ] Project context displayed in all command outputs
- [ ] Error handling for uninitialized projects
- [ ] Integration tests created and passing
- [ ] Help text updated with examples
- [ ] Code review completed
- [ ] Committed to git with conventional commit message

---

## Related Stories

**Depends On**:
- Story 20.1: Create ProjectDocumentLifecycle Factory Class
- Story 20.4: Add Project Root Detection

**Blocks**:
- Story 20.6: Documentation and Migration

---

## Notes

### Key Design Decisions

1. **Auto-Detection First**: Commands auto-detect project, with `--project` override
2. **Context Display**: Always show which project is being operated on
3. **Helpful Errors**: Clear messages when project not initialized
4. **Consistent UX**: All commands follow same pattern
5. **Relative Paths**: Documents referenced relative to project root

### User Experience Improvements

**Before (Story 20.5)**:
```bash
# Always operates on GAO-Dev's .gao-dev/
cd /anywhere
gao-dev lifecycle list  # Wrong database!
```

**After (Story 20.5)**:
```bash
# Auto-detects correct project
cd sandbox/projects/my-app/src
gao-dev lifecycle list  # Uses my-app's .gao-dev/

# Or explicit targeting
gao-dev lifecycle list --project sandbox/projects/my-app
```

---

## Acceptance Testing

### Test Case 1: Auto-Detection from Project Root

```bash
cd sandbox/projects/my-app
gao-dev lifecycle list

# Expected output:
# Project: my-app
# Location: /path/to/sandbox/projects/my-app
#
# Found 3 document(s):
# ...
```

### Test Case 2: Auto-Detection from Subdirectory

```bash
cd sandbox/projects/my-app/src/components
gao-dev lifecycle list

# Expected: Same as Test Case 1 (walks up to my-app)
```

### Test Case 3: Explicit Project Targeting

```bash
gao-dev lifecycle list --project sandbox/projects/other-app

# Expected output:
# Project: other-app
# Location: /path/to/sandbox/projects/other-app
# ...
```

### Test Case 4: Uninitialized Project Error

```bash
cd /tmp/not-a-project
gao-dev lifecycle list

# Expected output:
# Error: Document lifecycle not initialized for project: not-a-project
# ...
# To initialize, run: gao-dev sandbox init ...
```

---

**Created by**: Bob (Scrum Master)
**Ready for Implementation**: Yes
**Estimated Completion**: 1-2 days

---

*This story is part of Epic 20: Project-Scoped Document Lifecycle.*

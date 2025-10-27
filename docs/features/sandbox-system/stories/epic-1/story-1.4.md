# Story 1.4: Sandbox init Command Implementation

**Epic**: Epic 1 - Sandbox Infrastructure
**Status**: Draft
**Priority**: P0 (Critical)
**Estimated Effort**: 2 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27
**Depends On**: Stories 1.2, 1.3

---

## User Story

**As a** developer using GAO-Dev
**I want** to initialize sandbox projects via CLI
**So that** I can quickly create isolated test environments

---

## Acceptance Criteria

### AC1: Command Integration
- ✅ `gao-dev sandbox init` command fully functional
- ✅ Integrates with `SandboxManager` class
- ✅ Creates project successfully
- ✅ Outputs clear progress messages

### AC2: Project Creation
- ✅ Creates project directory structure
- ✅ Creates `.sandbox.yaml` metadata file
- ✅ Initializes git repository (optional)
- ✅ Creates README.md with project info

### AC3: Options Support
- ✅ `--config` option loads custom configuration
- ✅ `--boilerplate` option records boilerplate URL
- ✅ `--no-git` option skips git init
- ✅ `--tags` option adds project tags

### AC4: Validation & Errors
- ✅ Validates project name (alphanumeric, hyphens only)
- ✅ Checks project doesn't already exist
- ✅ Validates boilerplate URL format (if provided)
- ✅ Clear error messages for failures

### AC5: Output
- ✅ Shows project creation progress
- ✅ Displays created directory structure
- ✅ Shows next steps
- ✅ Provides project path

---

## Technical Details

### Implementation

Update `gao_dev/cli/sandbox_commands.py`:

```python
from ..sandbox import SandboxManager
from ..core import ConfigLoader

@sandbox.command()
@click.argument("project_name")
@click.option("--config", type=click.Path(exists=True), help="Configuration file")
@click.option("--boilerplate", type=str, help="Boilerplate repository URL")
@click.option("--no-git", is_flag=True, help="Skip git initialization")
@click.option("--tags", multiple=True, help="Project tags")
def init(
    project_name: str,
    config: Optional[str],
    boilerplate: Optional[str],
    no_git: bool,
    tags: tuple,
):
    """Initialize a new sandbox project."""
    try:
        # Validate project name
        if not _is_valid_project_name(project_name):
            click.echo("[ERROR] Invalid project name")
            return

        # Initialize sandbox manager
        sandbox_root = Path.cwd() / "sandbox"
        manager = SandboxManager(sandbox_root)

        # Check if exists
        if manager.project_exists(project_name):
            click.echo(f"[ERROR] Project '{project_name}' already exists")
            return

        # Create project
        click.echo(f">> Initializing sandbox project: {project_name}")

        metadata = manager.create_project(
            name=project_name,
            boilerplate_url=boilerplate,
            tags=list(tags) if tags else None,
        )

        project_path = manager.get_project_path(project_name)

        # Create README
        _create_readme(project_path, metadata)

        # Initialize git
        if not no_git:
            _init_git(project_path)

        # Success output
        click.echo(f"\n[OK] Project initialized successfully!")
        click.echo(f"  Location: {project_path}")
        click.echo(f"  Status: {metadata.status.value}")
        click.echo(f"\nNext steps:")
        click.echo(f"  cd {project_path}")
        click.echo(f"  gao-dev sandbox run <benchmark-config>")

    except Exception as e:
        click.echo(f"[ERROR] {e}", err=True)
        sys.exit(1)
```

---

## Testing Approach

### Manual Testing
```bash
# Test basic creation
gao-dev sandbox init test-project-001

# Test with options
gao-dev sandbox init test-project-002 --boilerplate https://github.com/user/starter

# Test with tags
gao-dev sandbox init test-project-003 --tags experiment --tags nextjs

# Test error: duplicate project
gao-dev sandbox init test-project-001  # Should fail

# Test error: invalid name
gao-dev sandbox init "Test Project!"  # Should fail
```

### Unit Tests
- Test command with valid inputs
- Test duplicate project error
- Test invalid name error
- Test git initialization (mock)

---

## Definition of Done

- [ ] Command implementation complete
- [ ] Integrates with SandboxManager
- [ ] All options work correctly
- [ ] Validation logic implemented
- [ ] Manual testing passed
- [ ] Unit tests written and passing
- [ ] Clear error messages
- [ ] Code reviewed and committed

---

## Related Stories

**Depends On**: Stories 1.2, 1.3
**Related**: Story 1.5 (clean), Story 1.6 (list)

---

**Estimated Completion**: 0.5-1 day

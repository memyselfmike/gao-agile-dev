# Story 1.5: Sandbox clean Command Implementation

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
**I want** to clean/reset sandbox projects
**So that** I can prepare projects for fresh benchmark runs

---

## Acceptance Criteria

### AC1: Single Project Clean
- ✅ Can clean specific project by name
- ✅ Removes generated files (in src/, docs/, tests/)
- ✅ Keeps configuration files
- ✅ Resets project status to ACTIVE

### AC2: Bulk Clean
- ✅ `--all` flag cleans all projects
- ✅ Shows progress for each project
- ✅ Continues on individual failures
- ✅ Summary report at end

### AC3: Safety Features
- ✅ Confirmation prompt (unless `--force`)
- ✅ Dry-run mode (`--dry-run`) shows what would be deleted
- ✅ Backup option (`--backup`) creates snapshot before clean
- ✅ Preserves important files (.sandbox.yaml, README.md)

### AC4: Selective Cleaning
- ✅ `--output-only` flag only cleans generated output
- ✅ `--runs-only` flag only clears benchmark run history
- ✅ `--full` flag does complete reset (including git)

---

## Technical Details

### Implementation

Add to `SandboxManager`:

```python
def clean_project(
    self,
    project_name: str,
    full: bool = False,
    backup: bool = False,
) -> dict:
    """
    Clean project to fresh state.

    Args:
        project_name: Project to clean
        full: If True, also reset git and remove all files
        backup: If True, create backup before cleaning

    Returns:
        Dictionary with cleanup statistics
    """
    pass
```

Update CLI command in `sandbox_commands.py`:

```python
@sandbox.command()
@click.argument("project_name", required=False)
@click.option("--all", is_flag=True, help="Clean all projects")
@click.option("--force", is_flag=True, help="Skip confirmation")
@click.option("--dry-run", is_flag=True, help="Show what would be deleted")
@click.option("--backup", is_flag=True, help="Create backup before cleaning")
@click.option("--output-only", is_flag=True, help="Only remove generated output")
@click.option("--runs-only", is_flag=True, help="Only clear run history")
@click.option("--full", is_flag=True, help="Full reset including git")
def clean(
    project_name: Optional[str],
    all: bool,
    force: bool,
    dry_run: bool,
    backup: bool,
    output_only: bool,
    runs_only: bool,
    full: bool,
):
    """Clean sandbox project(s) to fresh state."""
    pass
```

---

## Cleaning Logic

### Output-Only Clean
Removes:
- `src/*` (except templates)
- `docs/*` (except templates)
- `tests/*` (except templates)
- `.next`, `dist`, `build` directories
- `node_modules`, `__pycache__`

Keeps:
- `.sandbox.yaml`
- `README.md`
- Configuration files
- `.git/`

### Runs-Only Clean
- Clears benchmark run history from metadata
- Removes run artifacts
- Keeps source code

### Full Clean
- Removes everything except `.sandbox.yaml`
- Resets git repository
- Returns project to pristine state

---

## Testing Approach

### Manual Testing
```bash
# Dry run
gao-dev sandbox clean test-project --dry-run

# Clean with confirmation
gao-dev sandbox clean test-project

# Force clean
gao-dev sandbox clean test-project --force

# Clean all
gao-dev sandbox clean --all

# Output only
gao-dev sandbox clean test-project --output-only

# Full reset with backup
gao-dev sandbox clean test-project --full --backup
```

### Unit Tests
- Test output-only clean
- Test runs-only clean
- Test full clean
- Test backup creation
- Test dry-run mode
- Test confirmation logic

---

## Definition of Done

- [ ] Clean logic implemented in SandboxManager
- [ ] CLI command fully functional
- [ ] All cleaning modes work correctly
- [ ] Confirmation prompts work
- [ ] Backup functionality works
- [ ] Dry-run shows correct information
- [ ] Manual testing passed
- [ ] Unit tests written and passing
- [ ] Code reviewed and committed

---

## Related Stories

**Depends On**: Stories 1.2, 1.3
**Related**: Story 1.4 (init)

---

**Estimated Completion**: 1 day

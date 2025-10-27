# Story 1.6: Sandbox list Command Implementation

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
**I want** to list and view sandbox projects
**So that** I can see what projects exist and their status

---

## Acceptance Criteria

### AC1: Basic Listing
- ✅ Shows all sandbox projects
- ✅ Displays: name, status, created date, last run
- ✅ Sorts by last modified (newest first)
- ✅ Clean, readable output

### AC2: Filtering
- ✅ `--status` filters by project status (active/completed/failed/all)
- ✅ `--tags` filters by tags
- ✅ `--recent` shows only recent projects (N days)

### AC3: Output Formats
- ✅ Table format (default) - ASCII table
- ✅ JSON format - machine-readable
- ✅ Simple format - one per line, for scripting

### AC4: Project Details
- ✅ `--verbose` flag shows detailed information
- ✅ Shows run history
- ✅ Shows file counts and sizes
- ✅ Shows tags and metadata

---

## Technical Details

### Table Output Example
```
+------------------+-----------+-------------+-------------------+-------+
| Project Name     | Status    | Created     | Last Run          | Runs  |
+------------------+-----------+-------------+-------------------+-------+
| todo-app-003     | active    | 2025-10-25  | 2025-10-27 14:32  | 5     |
| todo-app-002     | completed | 2025-10-20  | 2025-10-22 09:15  | 12    |
| todo-app-001     | failed    | 2025-10-15  | 2025-10-16 11:22  | 3     |
+------------------+-----------+-------------+-------------------+-------+
```

### JSON Output Example
```json
[
  {
    "name": "todo-app-003",
    "status": "active",
    "created_at": "2025-10-25T10:30:00",
    "last_modified": "2025-10-27T14:32:00",
    "runs": 5,
    "tags": ["experiment", "nextjs"],
    "boilerplate_url": "https://github.com/..."
  }
]
```

### Simple Output Example
```
todo-app-003
todo-app-002
todo-app-001
```

---

## Implementation

Update CLI command:

```python
@sandbox.command()
@click.option(
    "--status",
    type=click.Choice(["active", "completed", "failed", "all"]),
    default="all",
)
@click.option("--format", type=click.Choice(["table", "json", "simple"]), default="table")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.option("--tags", multiple=True, help="Filter by tags")
@click.option("--recent", type=int, help="Show projects from last N days")
def list(
    status: str,
    format: str,
    verbose: bool,
    tags: tuple,
    recent: Optional[int],
):
    """List all sandbox projects."""
    try:
        sandbox_root = Path.cwd() / "sandbox"
        manager = SandboxManager(sandbox_root)

        # Get projects
        status_filter = ProjectStatus(status) if status != "all" else None
        projects = manager.list_projects(status=status_filter)

        # Apply filters
        if tags:
            projects = [p for p in projects if any(t in p.tags for t in tags)]

        if recent:
            cutoff = datetime.now() - timedelta(days=recent)
            projects = [p for p in projects if p.last_modified >= cutoff]

        # Output
        if format == "table":
            _print_table(projects, verbose)
        elif format == "json":
            _print_json(projects)
        elif format == "simple":
            _print_simple(projects)

    except Exception as e:
        click.echo(f"[ERROR] {e}", err=True)
        sys.exit(1)
```

---

## Testing Approach

### Manual Testing
```bash
# Basic list
gao-dev sandbox list

# Filter by status
gao-dev sandbox list --status active

# JSON output
gao-dev sandbox list --format json

# Verbose table
gao-dev sandbox list --verbose

# Filter by tags
gao-dev sandbox list --tags experiment

# Recent projects
gao-dev sandbox list --recent 7

# Combined filters
gao-dev sandbox list --status active --tags nextjs --format table
```

### Unit Tests
- Test filtering logic
- Test output formatting (table, JSON, simple)
- Test empty list handling
- Test verbose mode
- Test sorting

---

## Definition of Done

- [ ] List command fully implemented
- [ ] All output formats work correctly
- [ ] Filtering works (status, tags, recent)
- [ ] Table output is clean and readable
- [ ] JSON output is valid JSON
- [ ] Simple output works for scripting
- [ ] Verbose mode shows details
- [ ] Manual testing passed
- [ ] Unit tests written and passing
- [ ] Code reviewed and committed

---

## Related Stories

**Depends On**: Stories 1.2, 1.3
**Completes**: Epic 1 foundation

---

**Estimated Completion**: 1 day

---

## Notes

This story completes the foundational Epic 1. After this, users can:
- Initialize sandbox projects (`init`)
- Clean projects (`clean`)
- List projects (`list`)

The core infrastructure will be ready for Epic 2 (Boilerplate Integration) and Epic 3 (Metrics Collection).

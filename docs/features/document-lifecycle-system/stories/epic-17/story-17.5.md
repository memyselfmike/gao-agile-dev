# Story 17.5: CLI Commands for Context Management

**Epic:** 17 - Context System Integration
**Story Points:** 5
**Priority:** P1
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Add CLI commands for users to query and manage workflow context. This provides a user-friendly interface for inspecting context data, viewing lineage, checking statistics, and managing the context cache. The commands support both rich terminal output (with colors and tables) and JSON output for scripting, making context data accessible to developers, operators, and automation tools.

---

## Business Value

This story makes context data accessible and actionable:

- **Developer Experience**: Easy inspection of workflow context via CLI
- **Debugging**: Quick access to context data for troubleshooting
- **Observability**: View context lineage and usage patterns
- **Analytics**: Query statistics to understand cache performance
- **Automation**: JSON output enables scripting and integration
- **Operations**: Operators can inspect and manage context data
- **Cache Management**: Clear cache when needed
- **Workflow Traceability**: View full history for any epic/story
- **Performance Insights**: Cache hit rate and usage statistics
- **Production Ready**: Professional CLI with help and examples

---

## Acceptance Criteria

### Context Query Commands
- [ ] `gao-dev context show <workflow-id>` displays full context details
- [ ] Show includes: workflow_id, feature, epic, story, phase, status
- [ ] Show includes: decisions list (type, content, rationale)
- [ ] Show includes: artifacts list (type, path, description)
- [ ] Show includes: timestamps (created_at, updated_at)

### Context Listing Commands
- [ ] `gao-dev context list` shows recent workflow contexts (last 20)
- [ ] List includes: workflow_id, feature, epic/story, status, created_at
- [ ] List supports pagination (--limit, --offset)
- [ ] List supports filtering by status (--status=completed)
- [ ] List sorted by created_at descending (newest first)

### Context History Commands
- [ ] `gao-dev context history <epic> <story>` shows all context versions
- [ ] History shows all workflow executions for epic/story
- [ ] History includes status, timestamp, duration
- [ ] History sorted chronologically (oldest first)

### Lineage Commands
- [ ] `gao-dev context lineage <epic>` generates and displays lineage report
- [ ] Lineage shows document access flow (PRD -> Architecture -> Story)
- [ ] Lineage shows which agents accessed which documents
- [ ] Lineage includes access timestamps
- [ ] Lineage formatted as tree or graph

### Statistics Commands
- [ ] `gao-dev context stats` shows cache hit rate and usage statistics
- [ ] Stats include: hits, misses, hit rate percentage
- [ ] Stats include: evictions, expirations
- [ ] Stats include: current cache size, max size
- [ ] Stats include: memory usage estimate

### Cache Management Commands
- [ ] `gao-dev context clear-cache` clears ContextCache
- [ ] Clear cache confirms before deletion (--force to skip)
- [ ] Clear cache reports number of entries cleared

### Output Formats
- [ ] All commands support `--json` output for scripting
- [ ] Rich formatting with tables and colors for terminal
- [ ] JSON output is valid and parseable
- [ ] Terminal output uses Rich library for professional display

### Help and Examples
- [ ] Help text for all commands (`--help`)
- [ ] Examples in help text
- [ ] Clear error messages for invalid usage
- [ ] Command suggestions for typos

### Testing
- [ ] Unit tests for all CLI commands
- [ ] Test JSON output format
- [ ] Test Rich table formatting
- [ ] Test error handling (invalid workflow-id)
- [ ] Test pagination and filtering

---

## Technical Notes

### Implementation Approach

**File:** `gao_dev/cli/context_commands.py`

Create new CLI command module:

```python
import click
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
import json
from gao_dev.core.context import ContextPersistence, ContextUsageTracker, ContextLineageTracker, ContextCache
from gao_dev.core.config import get_gao_db_path

console = Console()

@click.group()
def context():
    """Manage workflow context and cache."""
    pass

@context.command()
@click.argument('workflow_id')
@click.option('--json', 'json_output', is_flag=True, help='Output as JSON')
def show(workflow_id: str, json_output: bool):
    """Display full context details for a workflow.

    Example:
        gao-dev context show abc123
        gao-dev context show abc123 --json
    """
    persistence = ContextPersistence()
    ctx = persistence.get_context(workflow_id)

    if not ctx:
        console.print(f"[red]Context not found: {workflow_id}[/red]")
        return

    if json_output:
        click.echo(json.dumps(ctx.to_dict(), indent=2))
    else:
        # Rich table output
        console.print(f"[bold cyan]Workflow Context: {workflow_id}[/bold cyan]")
        console.print(f"Feature: {ctx.feature_name}")
        console.print(f"Epic: {ctx.epic_number}, Story: {ctx.story_number}")
        console.print(f"Phase: {ctx.phase}, Status: {ctx.status}")
        console.print(f"Created: {ctx.created_at}, Updated: {ctx.updated_at}")

        # Decisions table
        if ctx.decisions:
            table = Table(title="Decisions")
            table.add_column("Type", style="cyan")
            table.add_column("Decision", style="green")
            table.add_column("Rationale", style="yellow")

            for decision in ctx.decisions:
                table.add_row(decision['type'], decision['decision'][:50], decision['rationale'][:50])

            console.print(table)

        # Artifacts table
        if ctx.artifacts:
            table = Table(title="Artifacts")
            table.add_column("Type", style="cyan")
            table.add_column("Path", style="green")
            table.add_column("Description", style="yellow")

            for artifact in ctx.artifacts:
                table.add_row(artifact['type'], artifact['path'], artifact['description'][:50])

            console.print(table)

@context.command()
@click.option('--limit', default=20, help='Number of results')
@click.option('--offset', default=0, help='Offset for pagination')
@click.option('--status', help='Filter by status')
@click.option('--json', 'json_output', is_flag=True, help='Output as JSON')
def list(limit: int, offset: int, status: str, json_output: bool):
    """List recent workflow contexts.

    Example:
        gao-dev context list
        gao-dev context list --limit 10 --status=completed
    """
    persistence = ContextPersistence()
    contexts = persistence.list_contexts(limit=limit, offset=offset, status=status)

    if json_output:
        click.echo(json.dumps([ctx.to_dict() for ctx in contexts], indent=2))
    else:
        table = Table(title=f"Workflow Contexts (showing {len(contexts)})")
        table.add_column("Workflow ID", style="cyan")
        table.add_column("Feature", style="green")
        table.add_column("Epic/Story", style="yellow")
        table.add_column("Status", style="magenta")
        table.add_column("Created", style="blue")

        for ctx in contexts:
            epic_story = f"{ctx.epic_number}.{ctx.story_number}" if ctx.story_number else f"Epic {ctx.epic_number}"
            table.add_row(ctx.id[:8], ctx.feature_name, epic_story, ctx.status, ctx.created_at.strftime("%Y-%m-%d %H:%M"))

        console.print(table)

@context.command()
@click.argument('epic', type=int)
@click.argument('story', type=int, required=False)
@click.option('--json', 'json_output', is_flag=True, help='Output as JSON')
def history(epic: int, story: int, json_output: bool):
    """Show all context versions for an epic/story.

    Example:
        gao-dev context history 17 1
        gao-dev context history 17
    """
    persistence = ContextPersistence()
    contexts = persistence.get_contexts_for_story(epic, story)

    if json_output:
        click.echo(json.dumps([ctx.to_dict() for ctx in contexts], indent=2))
    else:
        title = f"Context History: Epic {epic}" + (f".{story}" if story else "")
        table = Table(title=title)
        table.add_column("Workflow ID", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Phase", style="yellow")
        table.add_column("Created", style="blue")
        table.add_column("Duration", style="magenta")

        for ctx in contexts:
            duration = (ctx.updated_at - ctx.created_at).total_seconds()
            table.add_row(
                ctx.id[:8],
                ctx.status,
                ctx.phase,
                ctx.created_at.strftime("%Y-%m-%d %H:%M"),
                f"{duration:.1f}s"
            )

        console.print(table)

@context.command()
@click.argument('epic', type=int)
@click.option('--json', 'json_output', is_flag=True, help='Output as JSON')
def lineage(epic: int, json_output: bool):
    """Generate and display lineage report for an epic.

    Example:
        gao-dev context lineage 17
    """
    lineage_tracker = ContextLineageTracker()
    report = lineage_tracker.generate_lineage_report(epic)

    if json_output:
        click.echo(json.dumps(report, indent=2))
    else:
        console.print(f"[bold cyan]Context Lineage: Epic {epic}[/bold cyan]")

        # Build tree visualization
        tree = Tree(f"Epic {epic}")

        for doc_access in report['document_accesses']:
            node = tree.add(f"[green]{doc_access['document_type']}[/green]")
            node.add(f"Agent: {doc_access['agent_name']}")
            node.add(f"Time: {doc_access['access_time']}")

        console.print(tree)

@context.command()
@click.option('--json', 'json_output', is_flag=True, help='Output as JSON')
def stats(json_output: bool):
    """Show cache statistics.

    Example:
        gao-dev context stats
    """
    cache = ContextCache()  # Get global cache instance
    statistics = cache.get_statistics()

    if json_output:
        click.echo(json.dumps(statistics, indent=2))
    else:
        console.print("[bold cyan]Context Cache Statistics[/bold cyan]")
        console.print(f"Cache Size: {statistics['size']}/{statistics['max_size']}")
        console.print(f"Hit Rate: {statistics['hit_rate']:.2%}")
        console.print(f"Hits: {statistics['hits']}, Misses: {statistics['misses']}")
        console.print(f"Evictions: {statistics['evictions']}, Expirations: {statistics['expirations']}")
        console.print(f"Memory Usage: {statistics['memory_usage'] / 1024:.1f} KB")

@context.command()
@click.option('--force', is_flag=True, help='Skip confirmation')
def clear_cache(force: bool):
    """Clear the context cache.

    Example:
        gao-dev context clear-cache
        gao-dev context clear-cache --force
    """
    cache = ContextCache()
    size = len(cache)

    if not force:
        if not click.confirm(f"Clear {size} cache entries?"):
            console.print("[yellow]Cancelled[/yellow]")
            return

    cache.clear()
    console.print(f"[green]Cleared {size} cache entries[/green]")
```

**File:** `gao_dev/cli/commands.py`

Register context commands:

```python
from gao_dev.cli.context_commands import context

# Add to CLI group
cli.add_command(context)
```

**Files to Create:**
- `gao_dev/cli/context_commands.py` - CLI commands
- `tests/cli/test_context_commands.py` - Unit tests

**Files to Modify:**
- `gao_dev/cli/commands.py` - Register context command group

**Dependencies:**
- Story 17.2 (Database Unification)
- Story 17.3 (Orchestrator Integration)
- Story 16.3 (ContextPersistence)
- Story 16.4 (Usage/Lineage Trackers)

---

## Testing Requirements

### Unit Tests

**Show Command:**
- [ ] Test show displays full context details
- [ ] Test show with JSON output
- [ ] Test show with non-existent workflow-id
- [ ] Test show with decisions and artifacts

**List Command:**
- [ ] Test list displays recent contexts
- [ ] Test list with limit and offset
- [ ] Test list with status filter
- [ ] Test list with JSON output
- [ ] Test list with empty results

**History Command:**
- [ ] Test history for epic and story
- [ ] Test history for epic only
- [ ] Test history with JSON output
- [ ] Test history with no results

**Lineage Command:**
- [ ] Test lineage generates report
- [ ] Test lineage displays tree
- [ ] Test lineage with JSON output
- [ ] Test lineage with no data

**Stats Command:**
- [ ] Test stats displays cache metrics
- [ ] Test stats with JSON output
- [ ] Test stats with empty cache

**Clear Cache Command:**
- [ ] Test clear-cache with confirmation
- [ ] Test clear-cache with --force
- [ ] Test clear-cache reports count

### Integration Tests
- [ ] Test commands with real database
- [ ] Test pagination works correctly
- [ ] Test filtering works correctly
- [ ] Test Rich output renders correctly
- [ ] Test JSON output is valid

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Add CLI reference documentation
- [ ] Document all command options and arguments
- [ ] Add examples for each command
- [ ] Document JSON output format
- [ ] Add troubleshooting guide
- [ ] Document pagination and filtering
- [ ] Add screenshots or examples of Rich output
- [ ] Create video demo of CLI commands (optional)

---

## Implementation Details

### Development Approach

**Phase 1: Core Commands**
1. Create context_commands.py module
2. Implement show and list commands
3. Add basic Rich formatting

**Phase 2: Advanced Commands**
1. Implement history command
2. Implement lineage command with tree visualization
3. Implement stats and clear-cache commands

**Phase 3: JSON Output**
1. Add --json flag to all commands
2. Ensure JSON output is valid
3. Test JSON parsing

**Phase 4: Testing**
1. Write unit tests for all commands
2. Test Rich output rendering
3. Test JSON output format
4. Test error handling

### Quality Gates
- [ ] All unit tests pass
- [ ] Commands work with real database
- [ ] Rich output renders correctly
- [ ] JSON output is valid and parseable
- [ ] Help text clear and helpful
- [ ] Documentation complete with examples

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] `gao-dev context show` displays full context
- [ ] `gao-dev context list` shows recent contexts
- [ ] `gao-dev context history` shows version history
- [ ] `gao-dev context lineage` generates lineage report
- [ ] `gao-dev context stats` shows cache statistics
- [ ] `gao-dev context clear-cache` clears cache
- [ ] All commands support --json output
- [ ] Rich formatting with tables and colors
- [ ] Help text and examples for all commands
- [ ] Unit tests pass (>80% coverage)
- [ ] Commands registered in CLI
- [ ] Documentation complete with examples
- [ ] Code reviewed and approved
- [ ] No regression in existing functionality
- [ ] Committed with atomic commit message:
  ```
  feat(epic-17): implement Story 17.5 - CLI Commands for Context Management

  - Create gao-dev context command group
  - Implement context show command (full details)
  - Implement context list command (recent contexts)
  - Implement context history command (version history)
  - Implement context lineage command (document flow)
  - Implement context stats command (cache metrics)
  - Implement context clear-cache command (cache management)
  - Add Rich formatting with tables and colors
  - Support --json output for all commands
  - Add pagination and filtering support
  - Create comprehensive help text and examples
  - Add unit tests for all commands

  Generated with GAO-Dev
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```

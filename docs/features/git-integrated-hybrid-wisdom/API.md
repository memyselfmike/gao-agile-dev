# API Reference - Git-Integrated Hybrid Architecture

Complete API documentation for all services in the git-integrated hybrid architecture.

**Epic**: 27 - Integration & Migration
**Story**: 27.6 - Documentation & Migration Guide
**Last Updated**: 2025-11-09

---

## Table of Contents

1. [GitIntegratedStateManager](#gitintegratedstatemanager)
2. [FastContextLoader](#fastcontextloader)
3. [CeremonyOrchestrator](#ceremonyorchestrator)
4. [ConversationManager](#conversationmanager)
5. [GitMigrationManager](#gitmigrationmanager)
6. [GitAwareConsistencyChecker](#gitawareconsistencychecker)
7. [GAODevOrchestrator](#gaodevorchestr

ator)
8. [Code Examples](#code-examples)

---

## GitIntegratedStateManager

Central state management service providing atomic file + database + git operations.

### Class Definition

```python
from gao_dev.core.services.git_integrated_state_manager import GitIntegratedStateManager

manager = GitIntegratedStateManager(
    db_path=Path(".gao-dev/documents.db"),
    project_path=Path("/project")
)
```

### Constructor Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `db_path` | `Path` | Yes | Path to SQLite database file |
| `project_path` | `Path` | Yes | Path to project root (for git operations) |

### Methods

#### `create_epic()`

Create epic with atomic file + DB + git commit.

```python
epic = manager.create_epic(
    epic_num=1,
    title="Feature Implementation",
    description="Implement new feature",
    file_path=Path("docs/epics/epic-1.md"),
    content="# Epic 1: Feature Implementation\n...",
    status="planning"  # Optional, defaults to "planning"
)
```

**Parameters**:
- `epic_num` (int): Epic number (must be unique)
- `title` (str): Epic title
- `description` (str): Epic description
- `file_path` (Path): Path where epic file will be written
- `content` (str): Markdown content for epic file
- `status` (str, optional): Initial status (default: "planning")

**Returns**: `Dict[str, Any]` - Epic record from database

**Raises**:
- `GitIntegratedStateManagerError`: If epic_num already exists
- `WorkingTreeDirtyError`: If working tree has uncommitted changes
- `Exception`: If file write, DB insert, or git commit fails (triggers rollback)

**Atomicity**: All or nothing - if any step fails, everything rolls back.

---

#### `create_story()`

Create story with atomic file + DB + git commit.

```python
story = manager.create_story(
    epic_num=1,
    story_num=1,
    title="Implement login",
    description="Add user authentication",
    file_path=Path("docs/stories/epic-1/story-1.1.md"),
    content="# Story 1.1: Implement login\n...",
    status="planning"  # Optional, defaults to "planning"
)
```

**Parameters**:
- `epic_num` (int): Parent epic number (must exist)
- `story_num` (int): Story number within epic
- `title` (str): Story title
- `description` (str): Story description
- `file_path` (Path): Path where story file will be written
- `content` (str): Markdown content for story file
- `status` (str, optional): Initial status (default: "planning")

**Returns**: `Dict[str, Any]` - Story record from database

**Raises**:
- `GitIntegratedStateManagerError`: If epic doesn't exist or story already exists
- `WorkingTreeDirtyError`: If working tree has uncommitted changes
- `Exception`: If file write, DB insert, or git commit fails (triggers rollback)

**Atomicity**: All or nothing.

---

#### `update_epic()`

Update epic metadata with atomic DB + git commit.

```python
manager.update_epic(
    epic_num=1,
    title="Updated Title",  # Optional
    description="Updated description",  # Optional
    status="in_progress"  # Optional
)
```

**Parameters**:
- `epic_num` (int): Epic to update
- `title` (str, optional): New title
- `description` (str, optional): New description
- `status` (str, optional): New status

**Returns**: `Dict[str, Any]` - Updated epic record

**Raises**:
- `GitIntegratedStateManagerError`: If epic doesn't exist
- `WorkingTreeDirtyError`: If working tree dirty

---

#### `update_story()`

Update story metadata with atomic DB + git commit.

```python
manager.update_story(
    epic_num=1,
    story_num=1,
    title="Updated Story Title",  # Optional
    description="Updated description",  # Optional
    status="in_progress"  # Optional
)
```

**Parameters**:
- `epic_num` (int): Parent epic number
- `story_num` (int): Story to update
- `title` (str, optional): New title
- `description` (str, optional): New description
- `status` (str, optional): New status

**Returns**: `Dict[str, Any]` - Updated story record

**Raises**:
- `GitIntegratedStateManagerError`: If story doesn't exist
- `WorkingTreeDirtyError`: If working tree dirty

---

#### `transition_story_state()`

Transition story state with FSM validation.

```python
manager.transition_story_state(
    epic_num=1,
    story_num=1,
    new_state="in_progress"
)
```

**Parameters**:
- `epic_num` (int): Parent epic number
- `story_num` (int): Story to transition
- `new_state` (str): Target state

**Valid Transitions**:
- `planning` → `ready`
- `ready` → `in_progress`
- `in_progress` → `review` | `blocked`
- `review` → `completed` | `in_progress`
- `blocked` → `ready` | `in_progress`

**Returns**: `Dict[str, Any]` - Updated story record

**Raises**:
- `ValueError`: If transition invalid
- `GitIntegratedStateManagerError`: If story doesn't exist

---

### Properties

```python
# Check if working tree is clean
is_clean = manager.is_working_tree_clean()  # bool

# Get current git SHA
sha = manager.get_current_sha()  # str | None
```

---

## FastContextLoader

High-performance context loading with intelligent caching.

### Class Definition

```python
from gao_dev.core.context.fast_context_loader import FastContextLoader

loader = FastContextLoader(
    project_root=Path("/project"),
    cache_size=100,
    cache_ttl_seconds=300
)
```

### Constructor Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `project_root` | `Path` | Yes | - | Project root directory |
| `cache_size` | `int` | No | 100 | Max cache entries (LRU) |
| `cache_ttl_seconds` | `int` | No | 300 | Cache entry TTL (5 min) |

### Methods

#### `load_story_context()` (async)

Load complete story context with caching.

```python
context = await loader.load_story_context(
    epic_num=1,
    story_num=1
)

# Context includes:
# - epic: Epic metadata and content
# - story: Story metadata and content
# - dependencies: Related stories
# - architecture: System architecture
# - previous_context: Last execution context
```

**Parameters**:
- `epic_num` (int): Epic number
- `story_num` (int): Story number

**Returns**: `StoryContext` - Complete story context

**Performance**:
- Cache hit: <5ms
- Cache miss: <50ms
- Cache hit rate: >80% typical

**Raises**:
- `ContextLoaderError`: If story doesn't exist
- `FileNotFoundError`: If story file missing

---

#### `load_epic_context()` (async)

Load epic context.

```python
context = await loader.load_epic_context(epic_num=1)
```

**Parameters**:
- `epic_num` (int): Epic number

**Returns**: `EpicContext` - Epic context with metadata

---

#### `preload_contexts()` (async)

Preload contexts for cache warming.

```python
# Warm cache with epic 1, stories 1-5
await loader.preload_contexts(epic_num=1, story_nums=[1, 2, 3, 4, 5])
```

**Parameters**:
- `epic_num` (int): Epic to preload
- `story_nums` (List[int], optional): Stories to preload (default: all)

**Returns**: `int` - Number of contexts preloaded

---

#### `clear_cache()`

Clear all cached contexts.

```python
loader.clear_cache()
```

**Returns**: `None`

---

### Properties

```python
# Get cache statistics
stats = loader.get_cache_stats()
# Returns: {"hits": int, "misses": int, "hit_rate": float, "size": int}

# Get cache size
size = loader.cache_size  # int
```

---

## CeremonyOrchestrator

Multi-agent ceremony coordination service.

### Class Definition

```python
from gao_dev.core.services.ceremony_orchestrator import CeremonyOrchestrator

orchestrator = CeremonyOrchestrator(
    project_root=Path("/project"),
    context_loader=fast_context_loader,
    agent_factory=agent_factory
)
```

### Constructor Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_root` | `Path` | Yes | Project root directory |
| `context_loader` | `FastContextLoader` | Yes | Context loader instance |
| `agent_factory` | `AgentFactory` | Yes | Agent factory for creating agents |

### Methods

#### `run_planning_ceremony()` (async)

Execute planning ceremony with team.

```python
result = await orchestrator.run_planning_ceremony(
    epic_num=1,
    participants=["John", "Winston", "Bob"]
)
```

**Parameters**:
- `epic_num` (int): Epic to plan
- `participants` (List[str]): Agent names to participate

**Returns**: `CeremonyResult` - Ceremony outcomes and decisions

**Process**:
1. Load epic context (via FastContextLoader)
2. Initialize agents
3. Run planning discussion
4. Capture decisions
5. Commit outcomes to git

---

#### `run_daily_standup()` (async)

Execute daily standup ceremony.

```python
result = await orchestrator.run_daily_standup(
    epic_num=1,
    story_num=1
)
```

**Parameters**:
- `epic_num` (int): Current epic
- `story_num` (int): Current story

**Returns**: `CeremonyResult` - Standup outcomes

---

#### `run_retrospective()` (async)

Execute retrospective ceremony.

```python
result = await orchestrator.run_retrospective(epic_num=1)
```

**Parameters**:
- `epic_num` (int): Completed epic

**Returns**: `CeremonyResult` - Retrospective outcomes

---

## ConversationManager

Natural dialogue flow management.

### Class Definition

```python
from gao_dev.core.services.conversation_manager import ConversationManager

manager = ConversationManager(
    context_loader=fast_context_loader,
    max_history=10
)
```

### Constructor Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `context_loader` | `FastContextLoader` | Yes | - | Context loader instance |
| `max_history` | `int` | No | 10 | Max conversation history entries |

### Methods

#### `start_conversation()` (async)

Start new conversation with context.

```python
conversation_id = await manager.start_conversation(
    epic_num=1,
    story_num=1,
    agent_name="Bob"
)
```

**Parameters**:
- `epic_num` (int): Epic context
- `story_num` (int): Story context
- `agent_name` (str): Agent conducting conversation

**Returns**: `str` - Conversation ID (UUID)

---

#### `add_message()` (async)

Add message to conversation.

```python
await manager.add_message(
    conversation_id=conversation_id,
    role="user",
    content="What's the status?"
)
```

**Parameters**:
- `conversation_id` (str): Conversation ID
- `role` (str): "user" | "assistant" | "system"
- `content` (str): Message content

**Returns**: `None`

---

#### `get_conversation()` (async)

Get conversation history.

```python
history = await manager.get_conversation(conversation_id)
```

**Parameters**:
- `conversation_id` (str): Conversation ID

**Returns**: `List[Dict]` - Conversation history

---

## GitMigrationManager

Safe migration to hybrid architecture with rollback.

### Class Definition

```python
from gao_dev.core.services.git_migration_manager import GitMigrationManager

manager = GitMigrationManager(
    db_path=Path(".gao-dev/documents.db"),
    project_path=Path("/project")
)
```

### Constructor Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `db_path` | `Path` | Yes | Path to SQLite database |
| `project_path` | `Path` | Yes | Project root for git operations |

### Methods

#### `migrate_to_hybrid_architecture()`

Execute full 4-phase migration.

```python
result = manager.migrate_to_hybrid_architecture(
    create_branch=True,
    auto_merge=False
)

if result.success:
    print(f"Migrated {result.epics_count} epics, {result.stories_count} stories")
else:
    print(f"Migration failed: {result.error}")
```

**Parameters**:
- `create_branch` (bool, optional): Create migration branch (default: True)
- `auto_merge` (bool, optional): Auto-merge after success (default: False)

**Returns**: `MigrationResult`

**MigrationResult fields**:
- `success` (bool): Migration succeeded
- `phase_completed` (int): Last completed phase (1-4)
- `epics_count` (int): Epics migrated
- `stories_count` (int): Stories migrated
- `checkpoints` (Dict[str, str]): Phase → git SHA
- `summary` (str): Summary message
- `error` (str | None): Error message if failed
- `rollback_performed` (bool): Rollback executed

**Phases**:
1. Create database tables (Migration 005)
2. Backfill epics from filesystem
3. Backfill stories from filesystem (git-inferred state)
4. Validate migration completeness

**Rollback**: Automatic on failure, restores to pre-migration state.

---

## GitAwareConsistencyChecker

File-database consistency validation and repair.

### Class Definition

```python
from gao_dev.core.services.git_consistency_checker import GitAwareConsistencyChecker

checker = GitAwareConsistencyChecker(
    db_path=Path(".gao-dev/documents.db"),
    project_path=Path("/project")
)
```

### Constructor Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `db_path` | `Path` | Yes | Path to SQLite database |
| `project_path` | `Path` | Yes | Project root for git operations |

### Methods

#### `check_consistency()`

Check file-database consistency.

```python
report = checker.check_consistency()

if report.has_issues:
    print(f"Found {report.total_issues} issues:")
    print(f"  Orphaned records: {len(report.orphaned_records)}")
    print(f"  Unregistered files: {len(report.unregistered_files)}")
```

**Returns**: `ConsistencyReport`

**ConsistencyReport fields**:
- `timestamp` (datetime): Check timestamp
- `has_issues` (bool): Issues found
- `total_issues` (int): Total issue count
- `uncommitted_changes` (List[str]): Uncommitted files
- `orphaned_records` (List[ConsistencyIssue]): DB records without files
- `unregistered_files` (List[ConsistencyIssue]): Files without DB records
- `state_mismatches` (List[ConsistencyIssue]): DB state != git state

---

#### `repair()`

Repair consistency issues.

```python
checker.repair(
    report=report,
    create_commit=True
)
```

**Parameters**:
- `report` (ConsistencyReport): Report from check_consistency()
- `create_commit` (bool, optional): Create git commit after repair (default: True)

**Returns**: `None`

**Repair strategy**:
- Files are source of truth
- Register untracked files in DB
- Remove orphaned DB records
- Update stale DB records
- Atomic git commit after repair

---

## GAODevOrchestrator

Main entry point integrating all services.

### Class Definition

```python
from gao_dev.orchestrator import GAODevOrchestrator

# Recommended: Use factory method
orchestrator = GAODevOrchestrator.create_default(project_root=Path("/project"))

# Or manual initialization
orchestrator = GAODevOrchestrator(
    project_root=Path("/project"),
    config=config_loader,
    git_state_manager=git_state_manager,
    fast_context_loader=fast_context_loader,
    ceremony_orchestrator=ceremony_orchestrator,
    conversation_manager=conversation_manager
)
```

### Factory Method

#### `create_default()`

Create orchestrator with all services initialized.

```python
orchestrator = GAODevOrchestrator.create_default(
    project_root=Path("/project")
)
```

**Parameters**:
- `project_root` (Path): Project root directory

**Returns**: `GAODevOrchestrator` - Fully initialized orchestrator

**Services initialized**:
- GitIntegratedStateManager (atomic file+DB+git)
- FastContextLoader (5ms context loads)
- CeremonyOrchestrator (multi-agent coordination)
- ConversationManager (dialogue flow)

---

### Properties

```python
# Access services
orchestrator.git_state_manager      # GitIntegratedStateManager
orchestrator.fast_context_loader    # FastContextLoader
orchestrator.ceremony_orchestrator  # CeremonyOrchestrator
orchestrator.conversation_manager   # ConversationManager

# Check initialization
if orchestrator.git_state_manager:
    print("Git-integrated state management active")
```

---

### Methods

#### `create_prd()` (async generator)

Create PRD with John (PM).

```python
async for message in orchestrator.create_prd("MyApp"):
    print(message, end="")
```

**Parameters**:
- `project_name` (str): Project name

**Yields**: `str` - Streaming output from agent

---

#### `create_story()` (async generator)

Create story with Bob (Scrum Master).

```python
async for message in orchestrator.create_story(
    epic=1,
    story=1,
    title="Implement login"
):
    print(message, end="")
```

**Parameters**:
- `epic` (int): Epic number
- `story` (int): Story number
- `title` (str, optional): Story title

**Yields**: `str` - Streaming output

---

#### `implement_story()` (async generator)

Implement story with Amelia (Developer).

```python
async for message in orchestrator.implement_story(epic=1, story=1):
    print(message, end="")
```

**Parameters**:
- `epic` (int): Epic number
- `story` (int): Story number

**Yields**: `str` - Streaming output

---

#### `close()`

Close orchestrator and cleanup resources.

```python
orchestrator.close()
```

**Returns**: `None`

**Best practice**: Always call `close()` when done, or use context manager pattern (if implemented).

---

## Code Examples

### Example 1: Complete Workflow - Epic to Story

```python
import asyncio
from pathlib import Path
from gao_dev.orchestrator import GAODevOrchestrator

async def main():
    # Initialize
    project_root = Path("/my/project")
    orchestrator = GAODevOrchestrator.create_default(project_root)

    try:
        # Create PRD
        print("Creating PRD...")
        async for message in orchestrator.create_prd("MyApp"):
            print(message, end="")

        # Create epic
        epic_file = project_root / "docs/epics/epic-1.md"
        epic = orchestrator.git_state_manager.create_epic(
            epic_num=1,
            title="User Authentication",
            description="Implement user login/logout",
            file_path=epic_file,
            content="# Epic 1: User Authentication\n..."
        )
        print(f"\nEpic created: {epic['title']}")

        # Create story
        story_file = project_root / "docs/stories/epic-1/story-1.1.md"
        story = orchestrator.git_state_manager.create_story(
            epic_num=1,
            story_num=1,
            title="Implement login API",
            description="Create POST /login endpoint",
            file_path=story_file,
            content="# Story 1.1: Implement login API\n..."
        )
        print(f"Story created: {story['title']}")

        # Load context (fast!)
        context = await orchestrator.fast_context_loader.load_story_context(1, 1)
        print(f"Context loaded in <5ms: {context.epic_title}")

        # Transition story
        orchestrator.git_state_manager.transition_story_state(1, 1, "ready")
        orchestrator.git_state_manager.transition_story_state(1, 1, "in_progress")
        print("Story transitioned to in_progress")

    finally:
        orchestrator.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 2: Migration Workflow

```python
from pathlib import Path
from gao_dev.core.services.git_migration_manager import GitMigrationManager
from gao_dev.core.services.git_consistency_checker import GitAwareConsistencyChecker

def migrate_project(project_root: Path):
    db_path = project_root / ".gao-dev" / "documents.db"

    # Run migration
    migration_mgr = GitMigrationManager(db_path, project_root)
    result = migration_mgr.migrate_to_hybrid_architecture()

    if result.success:
        print(f"✓ Migration successful!")
        print(f"  Epics: {result.epics_count}")
        print(f"  Stories: {result.stories_count}")

        # Verify consistency
        checker = GitAwareConsistencyChecker(db_path, project_root)
        report = checker.check_consistency()

        if report.has_issues:
            print(f"⚠ Found {report.total_issues} issues. Repairing...")
            checker.repair(report)
            print("✓ Issues repaired")
        else:
            print("✓ No consistency issues")
    else:
        print(f"✗ Migration failed: {result.error}")
        if result.rollback_performed:
            print("  Automatic rollback performed")

if __name__ == "__main__":
    migrate_project(Path.cwd())
```

### Example 3: Fast Context Loading with Cache

```python
import asyncio
from pathlib import Path
from gao_dev.core.context.fast_context_loader import FastContextLoader

async def benchmark_context_loading():
    loader = FastContextLoader(
        project_root=Path.cwd()),
        cache_size=100,
        cache_ttl_seconds=300
    )

    # Cold load
    import time
    start = time.time()
    context1 = await loader.load_story_context(1, 1)
    cold_time = time.time() - start
    print(f"Cold load: {cold_time * 1000:.2f}ms")

    # Warm load (from cache)
    start = time.time()
    context2 = await loader.load_story_context(1, 1)
    warm_time = time.time() - start
    print(f"Warm load: {warm_time * 1000:.2f}ms")

    # Cache stats
    stats = loader.get_cache_stats()
    print(f"Cache hit rate: {stats['hit_rate']:.1%}")

if __name__ == "__main__":
    asyncio.run(benchmark_context_loading())
```

### Example 4: Ceremony Orchestration

```python
import asyncio
from pathlib import Path
from gao_dev.orchestrator import GAODevOrchestrator

async def run_planning_session():
    orchestrator = GAODevOrchestrator.create_default(Path.cwd())

    try:
        # Run planning ceremony for epic 1
        result = await orchestrator.ceremony_orchestrator.run_planning_ceremony(
            epic_num=1,
            participants=["John", "Winston", "Bob", "Sally"]
        )

        print(f"Planning ceremony complete:")
        print(f"  Decisions: {len(result.decisions)}")
        print(f"  Action items: {len(result.action_items)}")

        # Decisions automatically committed to git

    finally:
        orchestrator.close()

if __name__ == "__main__":
    asyncio.run(run_planning_session())
```

---

## Best Practices

### 1. Always Use Factory Method

```python
# ✓ Good
orchestrator = GAODevOrchestrator.create_default(project_root)

# ✗ Avoid (manual initialization complex)
orchestrator = GAODevOrchestrator(...)
```

### 2. Close Resources

```python
# ✓ Good
orchestrator = GAODevOrchestrator.create_default(project_root)
try:
    # Use orchestrator
    pass
finally:
    orchestrator.close()

# Or with context manager (if implemented)
async with GAODevOrchestrator.create_default(project_root) as orch:
    # Use orchestrator
    pass
```

### 3. Handle Errors Gracefully

```python
try:
    epic = manager.create_epic(...)
except WorkingTreeDirtyError:
    print("Please commit or stash changes first")
except GitIntegratedStateManagerError as e:
    print(f"State error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### 4. Use Async for Context Loading

```python
# ✓ Good (async)
context = await loader.load_story_context(1, 1)

# ✗ Avoid (blocking)
context = loader.load_story_context_sync(1, 1)  # Slower
```

### 5. Warm Cache for Performance

```python
# Preload contexts before batch operations
await loader.preload_contexts(epic_num=1, story_nums=range(1, 11))

# Now loads are <5ms
for story_num in range(1, 11):
    context = await loader.load_story_context(1, story_num)  # Fast!
```

---

## Error Handling

### Common Exceptions

```python
from gao_dev.core.services.git_integrated_state_manager import (
    GitIntegratedStateManagerError,
    WorkingTreeDirtyError
)
from gao_dev.core.context.fast_context_loader import ContextLoaderError
from gao_dev.core.services.git_migration_manager import GitMigrationManagerError
from gao_dev.core.services.git_consistency_checker import GitAwareConsistencyCheckerError
```

### Exception Hierarchy

```
Exception
├── GitIntegratedStateManagerError
│   └── WorkingTreeDirtyError
├── ContextLoaderError
├── GitMigrationManagerError
└── GitAwareConsistencyCheckerError
```

---

## Performance Guidelines

### Expected Performance

| Operation | Target | Typical |
|-----------|--------|---------|
| Epic creation | <1s | 200-500ms |
| Story creation | <200ms | 50-150ms |
| Context load (cache hit) | <5ms | 1-3ms |
| Context load (cache miss) | <50ms | 20-40ms |
| Orchestrator init | <500ms | 200-400ms |
| Migration (per file) | ~100ms | 80-120ms |
| Consistency check (1000 files) | <5s | 2-4s |

### Optimization Tips

1. **Use caching**: FastContextLoader cache reduces load from 50ms → 5ms
2. **Preload contexts**: Warm cache before batch operations
3. **Batch operations**: Group related operations for better git performance
4. **Avoid dirty tree**: Commit changes frequently to enable atomic operations
5. **Monitor cache hit rate**: Target >80% for optimal performance

---

## Next Steps

- **Migration Guide**: [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- **Architecture**: [ARCHITECTURE.md](./ARCHITECTURE.md)
- **CLAUDE.md**: Git-Integrated Architecture section

---

**API Reference Version**: 1.0.0
**Last Updated**: 2025-11-09
**Epic**: 27 - Integration & Migration
**Story**: 27.6 - Documentation & Migration Guide

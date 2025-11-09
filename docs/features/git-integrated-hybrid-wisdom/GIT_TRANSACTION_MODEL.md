# Git Transaction Model

**Epic**: 25 - Git-Integrated State Manager
**Status**: Complete
**Last Updated**: 2025-11-09

## Overview

This document describes the git transaction model used by the Git-Integrated State Manager to ensure atomic operations across filesystem, database, and git commits.

## Table of Contents

1. [Transaction Flow](#transaction-flow)
2. [Error Handling and Rollback](#error-handling-and-rollback)
3. [Service Interaction](#service-interaction)
4. [Best Practices](#best-practices)
5. [Troubleshooting](#troubleshooting)
6. [Code Examples](#code-examples)

---

## Transaction Flow

### High-Level Flow

Every state-changing operation in the Git-Integrated State Manager follows this atomic transaction pattern:

```
┌─────────────────────────────────────────────────────────────────┐
│                     TRANSACTION START                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Pre-Flight Check                                       │
│  ─────────────────────────                                       │
│  • Verify git working tree is clean                             │
│  • No uncommitted changes allowed                               │
│  • Raises: WorkingTreeDirtyError if dirty                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Begin Database Transaction                             │
│  ────────────────────────────────────                            │
│  • conn.execute("BEGIN IMMEDIATE")                              │
│  • Acquires exclusive lock on database                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Write Files to Filesystem                              │
│  ───────────────────────────────────                             │
│  • Create/update markdown files (epics, stories)                │
│  • Files written but not committed to git yet                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: Update Database                                        │
│  ──────────────────────                                          │
│  • Insert/update epic_state, story_state tables                 │
│  • Changes held in transaction (not committed yet)              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: Commit Database Transaction                            │
│  ─────────────────────────────────────                           │
│  • conn.commit()                                                 │
│  • Database changes are now persistent                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 6: Git Add and Commit (ATOMIC)                            │
│  ──────────────────────────────────────                          │
│  • git add <files>                                               │
│  • git commit -m "message"                                       │
│  • Creates permanent git commit                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TRANSACTION COMPLETE                         │
│  Result: Files + DB + Git all updated atomically                │
└─────────────────────────────────────────────────────────────────┘
```

### Error Scenarios

```
┌─────────────────────────────────────────────────────────────────┐
│  ERROR DURING ANY STEP                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ROLLBACK PROCEDURE                                             │
│  ──────────────────                                              │
│  1. Rollback database transaction (if active)                   │
│  2. Git reset --hard HEAD (undo file changes)                   │
│  3. Raise TransactionRollbackError                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Error Handling and Rollback

### Rollback Behavior

The Git-Integrated State Manager ensures atomicity through a comprehensive rollback strategy:

#### Database Rollback

```python
try:
    conn.execute("BEGIN IMMEDIATE")
    # ... perform database operations ...
    conn.commit()
except Exception as e:
    conn.rollback()  # Undo all database changes
    raise
```

#### Git Rollback

```python
try:
    # ... database operations committed ...
    self.git_manager.add_all()
    self.git_manager.commit(message)
except Exception as e:
    # Database is committed, but git failed
    # Must rollback both DB and git
    self.git_manager.reset_hard(original_sha)
    # Manual DB rollback needed here
    raise TransactionRollbackError(...)
```

### Exception Hierarchy

```
GitIntegratedStateManagerError (base)
    │
    ├─ WorkingTreeDirtyError
    │   └─ Raised when pre-flight check fails
    │      (working tree has uncommitted changes)
    │
    └─ TransactionRollbackError
        └─ Raised when transaction fails and rollback
           is performed (includes original error)
```

### Pre-Flight Checks

Before every operation, the manager checks:

1. **Working Tree Clean**: `git_manager.is_working_tree_clean()`
   - If false → raises `WorkingTreeDirtyError`
   - Ensures clean starting state for atomic operations

2. **Database Connection**: Verifies database is accessible
   - If not → raises `sqlite3.OperationalError`

3. **File Paths**: Validates file paths and parent directories
   - If invalid → raises `ValueError`

---

## Service Interaction

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                  GitIntegratedStateManager                      │
│                 (Orchestrates Transactions)                      │
└─────────────────────────────────────────────────────────────────┘
           │                │                    │
           │                │                    │
           ▼                ▼                    ▼
┌──────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ GitManager   │  │ StateCoordinator │  │ Filesystem      │
│              │  │                  │  │                 │
│ • add_all()  │  │ • epic_service   │  │ • Path.write()  │
│ • commit()   │  │ • story_service  │  │ • Path.read()   │
│ • reset_hard │  │ • action_service │  │                 │
│ • is_clean() │  │ • transaction()  │  │                 │
└──────────────┘  └─────────────────┘  └─────────────────┘
```

### Service Responsibilities

#### GitManager (Epic 23)

- **Purpose**: Low-level git operations
- **Key Methods**:
  - `is_working_tree_clean()` - Check for uncommitted changes
  - `add_all()` - Stage all changes
  - `commit(message)` - Create git commit
  - `reset_hard(sha)` - Rollback to specific commit
  - `get_head_sha()` - Get current commit SHA

#### StateCoordinator (Epic 24)

- **Purpose**: Database operations facade
- **Key Services**:
  - `epic_service` - Epic state management
  - `story_service` - Story state management
  - `action_service` - Action items
  - `ceremony_service` - Ceremonies (retrospectives, etc.)
  - `learning_service` - Learnings index

#### GitIntegratedStateManager (Epic 25)

- **Purpose**: Orchestrate atomic transactions
- **Key Operations**:
  - `create_epic()` - Create epic (file + DB + git)
  - `create_story()` - Create story (file + DB + git)
  - `transition_story()` - Change story status (DB + git)
  - `update_epic_file()` - Update epic file (file + DB + git)

### Transaction Coordination

```python
# Example: Create Epic (Atomic)
def create_epic(self, epic_num, title, file_path, content):
    # Pre-flight check
    if not self.git_manager.is_working_tree_clean():
        raise WorkingTreeDirtyError()

    original_sha = self.git_manager.get_head_sha()

    try:
        # Database transaction
        epic = self.coordinator.epic_service.create(
            epic_num=epic_num,
            title=title
        )

        # Write file
        file_path.write_text(content)

        # Git commit
        self.git_manager.add_all()
        self.git_manager.commit(f"feat: create epic-{epic_num}")

        return epic

    except Exception as e:
        # Rollback everything
        self.git_manager.reset_hard(original_sha)
        # DB already rolled back by service layer
        raise TransactionRollbackError(...) from e
```

---

## Best Practices

### When to Use Each Service

#### Use GitIntegratedStateManager When:

✅ Creating/updating epics or stories
✅ Transitioning story states
✅ Any operation that needs git commit tracking
✅ Building production features

#### Use GitMigrationManager When:

✅ Migrating from file-based to hybrid architecture
✅ Backfilling existing epic/story files into database
✅ One-time migration operations
✅ Creating git checkpoints during migration

#### Use GitAwareConsistencyChecker When:

✅ Detecting file-database inconsistencies
✅ Repairing orphaned records or unregistered files
✅ Auditing system integrity
✅ Post-migration validation

#### Use StateCoordinator Directly When:

✅ Read-only operations (get_epic_state, list_stories)
✅ Internal operations within GitIntegratedStateManager
✅ Testing database layer independently
✅ Performance-critical read paths

### Commit Message Conventions

Follow these commit message patterns for consistency:

```
# Epic creation
feat: create epic-{N} - {title}

# Story creation
feat: create story-{N}.{M} - {title}

# Story transition
chore: transition story-{N}.{M} to {status}

# Epic update
docs: update epic-{N} progress

# Migration checkpoints
migrate: phase {N} - {description}

# Consistency repairs
fix: repair consistency - {issue description}
```

### Performance Considerations

1. **Batch Operations**: Avoid in loops
   ```python
   # ❌ BAD: Multiple git commits
   for story_num in range(1, 10):
       manager.create_story(1, story_num, ...)  # 9 commits!

   # ✅ GOOD: Use lower-level APIs for batch
   # Or accept multiple commits for auditability
   ```

2. **Context Loading**: Use FastContextLoader
   ```python
   # Optimized path (using database indexes)
   epic_state = coordinator.get_epic_state(epic_num=1)
   # Returns: {"epic": {...}, "stories": [...]}
   # Target: <5ms p95
   ```

3. **Working Tree Checks**: Cached within transaction
   ```python
   # Check is performed once at start of transaction
   # Subsequent checks within same operation are free
   ```

---

## Troubleshooting

### Common Issues

#### Issue 1: WorkingTreeDirtyError

**Symptom**: Operation fails with "working tree has uncommitted changes"

**Cause**: Uncommitted files in git working directory

**Solution**:
```bash
# Option 1: Commit changes
git add .
git commit -m "your message"

# Option 2: Stash changes
git stash

# Option 3: Reset (careful!)
git reset --hard HEAD
```

#### Issue 2: Database Locked

**Symptom**: `sqlite3.OperationalError: database is locked`

**Cause**: Another process has exclusive lock on database

**Solution**:
```python
# 1. Ensure all connections are properly closed
coordinator.epic_service.close()
coordinator.story_service.close()
# ... close all services

# 2. Use connection pooling or shorter transactions
# 3. Avoid long-running transactions
```

#### Issue 3: Git Commit Failure

**Symptom**: Transaction fails at git commit step

**Cause**: Git configuration, permissions, or repository state issues

**Solution**:
```bash
# Check git config
git config user.name
git config user.email

# Verify repository is valid
git status

# Check file permissions
ls -la .git/
```

#### Issue 4: TransactionRollbackError

**Symptom**: Operation fails with rollback error

**Cause**: Error during transaction, rollback attempted but may have partially failed

**Solution**:
```python
# 1. Check git log to see if commit was created
git log -1

# 2. Check database state
# Use StateCoordinator to query epic/story state

# 3. Run consistency check
checker = GitAwareConsistencyChecker(db_path, project_path)
report = checker.check_consistency()

# 4. Repair if needed
if report.has_issues:
    checker.repair(report)
```

### Debugging Tools

#### Enable Debug Logging

```python
import structlog
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG)
)
```

#### Inspect Transaction State

```python
# Get current git state
sha = git_manager.get_head_sha()
commit_info = git_manager.get_commit_info()
is_clean = git_manager.is_working_tree_clean()

# Get database state
epic = coordinator.epic_service.get(epic_num)
stories = coordinator.story_service.list_by_epic(epic_num)

# Check consistency
checker = GitAwareConsistencyChecker(db_path, project_path)
report = checker.check_consistency()
print(f"Issues: {report.total_issues}")
```

---

## Code Examples

### Example 1: Create Epic with Custom Metadata

```python
from pathlib import Path
from gao_dev.core.services.git_integrated_state_manager import GitIntegratedStateManager

# Initialize manager
manager = GitIntegratedStateManager(
    db_path=Path(".gao-dev/documents.db"),
    project_path=Path("/project")
)

# Create epic with metadata
epic = manager.create_epic(
    epic_num=5,
    title="User Authentication System",
    file_path=Path("docs/epics/epic-5.md"),
    content="""# Epic 5: User Authentication System

## Overview
Implement comprehensive authentication system.

## Stories
- Story 5.1: OAuth2 integration
- Story 5.2: JWT token management
- Story 5.3: Role-based access control
""",
    metadata={"priority": "P0", "team": "backend"}
)

print(f"Epic created: {epic['title']}")
print(f"Git commit: {epic['git_sha']}")
```

### Example 2: Create Story and Transition

```python
# Create story
story = manager.create_story(
    epic_num=5,
    story_num=1,
    title="OAuth2 Integration",
    file_path=Path("docs/stories/story-5.1.md"),
    content="""# Story 5.1: OAuth2 Integration

## Acceptance Criteria
- [ ] Google OAuth2 provider configured
- [ ] Callback handler implemented
- [ ] User session management
- [ ] Error handling for auth failures
""",
    auto_update_epic=True  # Automatically update epic progress
)

# Transition to in_progress
story = manager.transition_story(
    epic_num=5,
    story_num=1,
    new_status="in_progress",
    commit_message="chore: start story-5.1 - OAuth2 integration",
    auto_update_epic=True
)

# Complete story
story = manager.transition_story(
    epic_num=5,
    story_num=1,
    new_status="completed",
    commit_message="feat: complete story-5.1 - OAuth2 integration",
    auto_update_epic=True
)

print(f"Story status: {story['status']}")
```

### Example 3: Update Epic File Content

```python
# Update epic file (e.g., add new story)
updated_epic = manager.update_epic_file(
    epic_num=5,
    file_path=Path("docs/epics/epic-5.md"),
    new_content="""# Epic 5: User Authentication System

## Overview
Implement comprehensive authentication system.

## Stories
- Story 5.1: OAuth2 integration ✓
- Story 5.2: JWT token management (IN PROGRESS)
- Story 5.3: Role-based access control
- Story 5.4: Multi-factor authentication (NEW)

## Progress
- Completed: 1/4 stories
- In Progress: 1/4 stories
""",
    commit_message="docs: update epic-5 with story 5.4"
)
```

### Example 4: Batch Story Creation with Error Handling

```python
import sys

# Create multiple stories with error handling
stories_to_create = [
    (1, "Login UI", "docs/stories/story-5.1.md", "# Story 5.1\n..."),
    (2, "Logout Flow", "docs/stories/story-5.2.md", "# Story 5.2\n..."),
    (3, "Password Reset", "docs/stories/story-5.3.md", "# Story 5.3\n..."),
]

for story_num, title, file_path, content in stories_to_create:
    try:
        story = manager.create_story(
            epic_num=5,
            story_num=story_num,
            title=title,
            file_path=Path(file_path),
            content=content,
            auto_update_epic=True
        )
        print(f"✓ Created story {story_num}: {title}")
    except Exception as e:
        print(f"✗ Failed to create story {story_num}: {e}", file=sys.stderr)
        # Continue with remaining stories
        continue
```

### Example 5: Context Loading for Agent

```python
# Load epic context for agent (fast path using indexes)
epic_state = manager.coordinator.get_epic_state(epic_num=5)

# Access epic metadata
epic = epic_state["epic"]
print(f"Epic: {epic['title']}")
print(f"Status: {epic['status']}")
print(f"Progress: {epic['completed_stories']}/{epic['total_stories']}")

# Access all stories
stories = epic_state["stories"]
for story in stories:
    print(f"  Story {story['story_num']}: {story['title']} [{story['status']}]")

# Filter stories by status
pending = [s for s in stories if s['status'] == 'pending']
in_progress = [s for s in stories if s['status'] == 'in_progress']
completed = [s for s in stories if s['status'] == 'completed']

print(f"\nPending: {len(pending)}")
print(f"In Progress: {len(in_progress)}")
print(f"Completed: {len(completed)}")
```

### Example 6: Migration and Consistency Check

```python
from gao_dev.core.services.git_migration_manager import GitMigrationManager
from gao_dev.core.services.git_consistency_checker import GitAwareConsistencyChecker

# Run migration
migration_mgr = GitMigrationManager(
    db_path=Path(".gao-dev/documents.db"),
    project_path=Path("/project")
)

result = migration_mgr.migrate_to_hybrid_architecture()

if result.success:
    print(f"Migration successful!")
    print(f"Epics migrated: {result.epics_count}")
    print(f"Stories migrated: {result.stories_count}")
    print(f"Checkpoints: {list(result.checkpoints.keys())}")
else:
    print(f"Migration failed: {result.error}")
    if result.rollback_performed:
        print("Rollback completed")

# Check consistency after migration
checker = GitAwareConsistencyChecker(
    db_path=Path(".gao-dev/documents.db"),
    project_path=Path("/project")
)

report = checker.check_consistency()

if report.has_issues:
    print(f"Found {report.total_issues} issues:")
    print(f"  Orphaned records: {len(report.orphaned_records)}")
    print(f"  Unregistered files: {len(report.unregistered_files)}")
    print(f"  State mismatches: {len(report.state_mismatches)}")

    # Repair automatically
    repair_result = checker.repair(report)
    if repair_result.success:
        print(f"Repaired {repair_result.issues_fixed} issues")
else:
    print("No consistency issues found")
```

---

## Performance Targets

| Operation | Target (p95) | Typical |
|-----------|--------------|---------|
| Epic context load | <5ms | 2-3ms |
| Agent context load | <5ms | 2-3ms |
| Story creation | <100ms | 50-80ms |
| Story transition | <50ms | 20-30ms |
| Epic creation | <100ms | 50-80ms |
| Consistency check | <500ms | 200-300ms |

---

## Related Documentation

- [EPIC_25_IMPLEMENTATION_STATUS.md](./EPIC_25_IMPLEMENTATION_STATUS.md) - Implementation status
- [API_REFERENCE.md](./API_REFERENCE.md) - Complete API reference
- [../../MIGRATION_GUIDE_EPIC_25.md](../../MIGRATION_GUIDE_EPIC_25.md) - Migration guide

---

**Last Updated**: 2025-11-09
**Epic**: 25 - Git-Integrated State Manager
**Stories**: 25.1-25.9 (Complete)

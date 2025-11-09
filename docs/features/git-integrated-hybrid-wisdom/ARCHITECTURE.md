# Technical Specification: Git-Integrated Hybrid Wisdom Architecture

**Feature**: Git-Integrated Hybrid Wisdom Architecture
**Version**: 1.0
**Date**: 2025-11-09
**Technical Architect**: Winston
**Status**: Draft

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [System Components](#system-components)
3. [Database Schema](#database-schema)
4. [Git Transaction Model](#git-transaction-model)
5. [API Design](#api-design)
6. [Performance Optimization](#performance-optimization)
7. [Error Handling & Rollback](#error-handling--rollback)
8. [Migration Strategy](#migration-strategy)
9. [Testing Strategy](#testing-strategy)
10. [Deployment Plan](#deployment-plan)

---

## Architecture Overview

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     Application Layer                            │
│  (Orchestrator, CLI Commands, Workflows)                        │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│              GitIntegratedStateManager                           │
│  Coordinates atomic operations via git commits                   │
│                                                                  │
│  Methods:                                                        │
│  - create_epic() → file + DB + git commit                       │
│  - create_story() → file + DB + git commit                      │
│  - transition_story() → DB update + git commit                  │
│  - complete_story() → DB update + git commit                    │
│  - hold_ceremony() → files + DB + git commit                    │
└──────────────────────────────────────────────────────────────────┘
                    │                            │
         ┌──────────┴──────────┐    ┌──────────┴──────────┐
         ↓                     ↓    ↓                     ↓
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  StateCoordinator│  │ GitManager      │  │DocumentLifecycle│
│  (Write Facade) │  │ (Git Ops)       │  │ (File Registry) │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                     │                    │
         ↓                     ↓                    ↓
┌─────────────────────────────────────────────────────────────────┐
│                     Data Layer                                   │
│  ┌────────────────────┐            ┌────────────────────┐      │
│  │ SQLite Database    │            │ File System        │      │
│  │ (.gao-dev/         │            │ (docs/            │      │
│  │  documents.db)     │            │  Markdown files)  │      │
│  │                    │            │                    │      │
│  │ Tables:            │            │ Files:             │      │
│  │ - epic_state       │            │ - PRD.md           │      │
│  │ - story_state      │            │ - epics/           │      │
│  │ - action_items     │            │ - stories/         │      │
│  │ - ceremony_summaries│           │ - ceremonies/      │      │
│  │ - learning_index   │            │ - learnings/       │      │
│  └────────────────────┘            └────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                     Git Repository                               │
│  (Version control for both database and files)                   │
│                                                                  │
│  Commits:                                                        │
│  - feat(story-5.3): create story                                │
│  - feat(story-5.3): transition to in_progress                   │
│  - docs(epic-5): hold stand-up - 3 action items                 │
└──────────────────────────────────────────────────────────────────┘
```

### Core Principles

1. **Git as Transaction Boundary**: Every state change = one atomic git commit
2. **Database for Speed**: SQLite provides <5ms queries with indexes
3. **Files for Humans**: Markdown provides readable documentation
4. **Single Source of Truth**: Database is derived from files, both committed together
5. **Consistency Enforcement**: Pre-checks ensure git working tree is clean

### Design Decisions

**Decision 1: Version Control the Database**
- ✅ **Chosen**: Include .gao-dev/documents.db in git
- **Rationale**: Atomic commits bundle files + DB together
- **Tradeoff**: Database is binary (less readable), but small (<50MB)

**Decision 2: Git Serialization for Concurrency**
- ✅ **Chosen**: Rely on git's natural commit serialization
- **Rationale**: Operations are fast (<100ms), git prevents concurrent commits
- **Tradeoff**: No true concurrent writes, but acceptable for our use case

**Decision 3: Service Decomposition**
- ✅ **Chosen**: Split StateTracker into 5 focused services
- **Rationale**: Avoid god class, maintain SRP
- **Services**: EpicStateService, StoryStateService, ActionItemService, CeremonyService, LearningIndexService

**Decision 4: Migration Branch Strategy**
- ✅ **Chosen**: Create migration/hybrid-architecture branch
- **Rationale**: Safe rollback by deleting branch
- **Tradeoff**: Requires git knowledge, but cleaner than manual rollback

---

## System Components

### Component 1: GitManager (Enhanced)

**Location**: `gao_dev/core/git_manager.py`

**Current LOC**: 616
**New LOC**: ~800 (adding ~200 LOC)

**New Methods** (10 additions):

```python
class GitManager:
    """Enhanced git operations for hybrid architecture."""

    # Transaction Support (CRITICAL)
    def is_working_tree_clean(self) -> bool:
        """Check no uncommitted changes."""

    def reset_hard(self, target: str = "HEAD") -> bool:
        """Rollback file changes (DESTRUCTIVE)."""

    def get_head_sha(self, short: bool = True) -> str:
        """Get current commit SHA."""

    def add_all(self) -> bool:
        """Stage all changes."""

    def commit(self, message: str, allow_empty: bool = False) -> str:
        """Create commit, return SHA."""

    # Branch Management
    def create_branch(self, name: str, checkout: bool = True) -> bool:
    def checkout(self, branch: str) -> bool:
    def delete_branch(self, name: str, force: bool = False) -> bool:

    # File History
    def get_last_commit_for_file(self, path: Path) -> Optional[Dict]:
    def is_file_tracked(self, path: Path) -> bool:
```

**Testing**: 30+ unit tests, 10+ integration tests

---

### Component 2: StateCoordinator (New)

**Location**: `gao_dev/core/services/state_coordinator.py`

**LOC**: ~300

**Purpose**: Facade coordinating 5 state services

**Architecture** (Facade Pattern):

```python
class StateCoordinator:
    """
    Coordinates state tracking services (facade).

    Delegates to specialized services:
    - EpicStateService: Epic state management
    - StoryStateService: Story state management
    - ActionItemService: Action item tracking
    - CeremonyService: Ceremony summary tracking
    - LearningIndexService: Learning indexing
    """

    def __init__(self, registry: DocumentRegistry):
        self.registry = registry
        self.epics = EpicStateService(registry)
        self.stories = StoryStateService(registry)
        self.actions = ActionItemService(registry)
        self.ceremonies = CeremonyService(registry)
        self.learnings = LearningIndexService(registry)

    def create_epic(self, epic_num: int, title: str) -> None:
        """Create epic state."""
        self.epics.create(epic_num, title)

    def create_story(
        self,
        story_id: str,
        epic_num: int,
        title: str,
        estimate: float
    ) -> None:
        """Create story state and update epic."""
        self.stories.create(story_id, epic_num, title, estimate)
        self.epics.update_progress(epic_num)

    def transition_story(self, story_id: str, new_state: str) -> None:
        """Transition story and update epic."""
        epic_num = self.stories.transition(story_id, new_state)
        self.epics.update_progress(epic_num)
```

**Services** (5 focused services, ~100-150 LOC each):

1. **EpicStateService**: `create()`, `update_progress()`, `archive()`
2. **StoryStateService**: `create()`, `transition()`, `complete()`
3. **ActionItemService**: `create()`, `complete()`, `get_active()`
4. **CeremonyService**: `create_summary()`, `get_recent()`
5. **LearningIndexService**: `index()`, `supersede()`, `search()`

**Total LOC**: ~800 (300 facade + 5×100 services)

**Testing**: 50+ unit tests (10 per service)

---

### Component 3: FastContextLoader (New)

**Location**: `gao_dev/core/services/fast_context_loader.py`

**LOC**: ~400

**Purpose**: Fast context queries (<5ms)

**Key Methods**:

```python
class FastContextLoader:
    """Load context from database with <5ms queries."""

    def get_epic_context(self, epic_num: int) -> EpicContext:
        """
        Get complete epic context in single query.

        Returns:
            EpicContext with:
            - Epic metadata (number, title, progress)
            - Active action items (JSON array)
            - Recent learnings (top 5)
            - Recent ceremonies (summaries)
            - Story breakdown (by state)

        Performance: <5ms for epics with 50 stories
        """

    def get_agent_context(
        self,
        agent_name: str,
        epic_num: int
    ) -> Dict[str, Any]:
        """
        Get role-specific context for agent.

        Bob (Scrum Master):
            - Story velocity, blocked stories, action items
        Amelia (Developer):
            - My stories, my action items, code learnings
        Murat (QA):
            - Test coverage, quality issues, quality learnings

        Performance: <5ms
        """

    def analyze_existing_project(self, path: Path) -> ProjectState:
        """
        Analyze existing project from database.

        Returns project state without reading files:
        - Active epics
        - Current story
        - Pending action items
        - Latest epic progress

        Performance: <10ms
        """
```

**Query Optimization**:
- Uses `json_group_array()` for aggregation
- Limits results (max 20 action items, 10 learnings, etc.)
- Indexed queries (all <5ms)

**Testing**: 20+ unit tests, performance benchmarks

---

### Component 4: GitIntegratedStateManager (New)

**Location**: `gao_dev/core/services/git_integrated_state_manager.py`

**LOC**: ~600

**Purpose**: Atomic operations via git commits

**Key Methods**:

```python
class GitIntegratedStateManager:
    """State manager using git as transaction layer."""

    def __init__(
        self,
        git_manager: GitManager,
        registry: DocumentRegistry,
        state_coordinator: StateCoordinator
    ):
        self.git = git_manager
        self.registry = registry
        self.state = state_coordinator

    def create_story(
        self,
        epic_num: int,
        story_num: int,
        content: str,
        metadata: Dict[str, Any]
    ) -> Story:
        """
        Create story with atomic git commit.

        Process:
        1. Pre-check: git working tree clean
        2. Begin DB transaction
        3. Write file
        4. Register document
        5. Create story state
        6. Update epic progress
        7. Commit DB transaction
        8. Git add + commit (ATOMIC)
        9. On error: rollback DB + git reset --hard

        Returns: Story object
        Raises: StateError if operation fails
        """

    def transition_story(
        self,
        story_id: str,
        new_state: str,
        actual_hours: Optional[float] = None
    ) -> None:
        """
        Transition story with atomic git commit.

        Process:
        1. Pre-check: git working tree clean
        2. Begin DB transaction
        3. Update story state
        4. Update epic progress
        5. Commit DB transaction
        6. Git add + commit (ATOMIC)
        7. On error: rollback DB + git reset --hard
        """

    def hold_ceremony(
        self,
        ceremony_type: str,
        epic_num: int,
        transcript: List[Dict],
        outcomes: List[str],
        action_items: List[Dict]
    ) -> None:
        """
        Record ceremony with atomic git commit.

        Process:
        1. Pre-check: git working tree clean
        2. Begin DB transaction
        3. Write transcript file
        4. Register document
        5. Create action item files
        6. Create action item state records
        7. Create ceremony summary
        8. Commit DB transaction
        9. Git add + commit (ATOMIC)
        10. On error: rollback DB + git reset --hard
        """
```

**Error Handling**:
- Every method has try/except with rollback
- Clear error messages with context
- Structured logging at every step

**Testing**: 30+ integration tests

---

### Component 5: GitMigrationManager (New)

**Location**: `gao_dev/core/services/git_migration_manager.py`

**LOC**: ~500

**Purpose**: Safe migration with git checkpoints

**Migration Phases**:

```python
class GitMigrationManager:
    """Migration with git checkpoints and rollback."""

    def migrate_to_hybrid_architecture(self) -> MigrationResult:
        """
        Migrate existing project to hybrid architecture.

        Process:
        1. Pre-flight checks (git clean, structure valid)
        2. Create checkpoint (current HEAD SHA)
        3. Create migration branch
        4. Phase 1: Create state tables (commit)
        5. Phase 2: Backfill epic state (commit)
        6. Phase 3: Backfill story state (commit)
        7. Phase 4: Validate migration (commit)
        8. Merge to main (if successful)
        9. On error: delete branch, checkout main

        Returns: MigrationResult (success/failure, details)
        """

    def _phase_1_create_tables(self) -> None:
        """Execute migration 005, commit."""

    def _phase_2_backfill_epics(self) -> None:
        """Parse epic files, create epic_state, commit."""

    def _phase_3_backfill_stories(self) -> None:
        """Parse story files, infer state from git, commit."""

    def _phase_4_validate(self) -> None:
        """Validate all state correct, commit."""

    def _infer_story_state_from_git(self, file: Path) -> str:
        """
        Infer story state from git history.

        Strategy:
        - Last commit message contains "complete" → "done"
        - Last commit message contains "in progress" → "in_progress"
        - File >30 days old → "done"
        - Otherwise → "todo"
        """
```

**Rollback Safety**:
- Each phase is a separate commit (checkpoint)
- On error: delete migration branch
- Main branch untouched (can always rollback)

**Testing**: 15+ migration tests

---

### Component 6: GitAwareConsistencyChecker (New)

**Location**: `gao_dev/core/services/git_consistency_checker.py`

**LOC**: ~300

**Purpose**: Detect and repair file-DB inconsistencies

**Methods**:

```python
class GitAwareConsistencyChecker:
    """Consistency checking using git."""

    def check_consistency(self) -> ConsistencyReport:
        """
        Check file-database consistency using git.

        Checks:
        1. Uncommitted changes (git status)
        2. Orphaned DB records (file deleted manually)
        3. Unregistered files (file created manually)
        4. State mismatches (file metadata ≠ DB state)

        Returns: ConsistencyReport with issues list
        """

    def repair(self, report: ConsistencyReport) -> None:
        """
        Repair consistency issues.

        Process:
        1. Begin DB transaction
        2. For each issue:
           - Sync DB to match files (file is source of truth)
           - Or remove orphaned DB records
           - Or register unregistered files
        3. Commit DB transaction
        4. Git add + commit (repairs are tracked)
        5. On error: rollback DB + git reset
        """

    def _sync_db_from_file(self, file_path: Path) -> None:
        """Update DB to match file metadata."""

    def _register_file(self, file_path: Path) -> None:
        """Register untracked file in DB."""
```

**Testing**: 20+ consistency tests

---

## Database Schema

### New Tables (Migration 005)

#### epic_state

```sql
CREATE TABLE epic_state (
    epic_num INTEGER PRIMARY KEY,
    epic_title TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('planning', 'active', 'complete', 'archived')),
    total_stories INTEGER NOT NULL DEFAULT 0,
    completed_stories INTEGER NOT NULL DEFAULT 0,
    in_progress_stories INTEGER NOT NULL DEFAULT 0,
    progress_percent REAL NOT NULL DEFAULT 0,
    current_story TEXT,  -- e.g., "5.3"
    start_date TEXT,
    target_date TEXT,
    actual_completion_date TEXT,
    metadata JSON
);

CREATE INDEX idx_epic_state_state ON epic_state(state);
```

**Purpose**: Fast epic progress queries
**Performance**: <1ms for single epic, <5ms for all active epics

---

#### story_state

```sql
CREATE TABLE story_state (
    story_id TEXT PRIMARY KEY,  -- e.g., "5.3"
    epic_num INTEGER NOT NULL REFERENCES epic_state(epic_num),
    story_title TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('todo', 'in_progress', 'review', 'done')),
    assignee TEXT,
    estimate_hours REAL,
    actual_hours REAL,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    metadata JSON
);

CREATE INDEX idx_story_state_epic ON story_state(epic_num);
CREATE INDEX idx_story_state_state ON story_state(state);
CREATE INDEX idx_story_state_assignee ON story_state(assignee);
```

**Purpose**: Fast story status queries
**Performance**: <1ms for single story, <5ms for epic's stories

---

#### action_items

```sql
CREATE TABLE action_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    summary TEXT NOT NULL,  -- 1 sentence
    description TEXT,  -- Optional longer description
    assignee TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('todo', 'in_progress', 'done')),
    priority TEXT NOT NULL CHECK(priority IN ('low', 'medium', 'high', 'critical')),
    due_date TEXT,
    epic_num INTEGER,
    source_doc_id INTEGER REFERENCES documents(id),  -- Link to ceremony
    created_at TEXT NOT NULL,
    completed_at TEXT,
    metadata JSON
);

CREATE INDEX idx_action_items_assignee ON action_items(assignee);
CREATE INDEX idx_action_items_state ON action_items(state);
CREATE INDEX idx_action_items_epic ON action_items(epic_num);
```

**Purpose**: Fast action item queries (by assignee, epic, state)
**Performance**: <1ms for active items per agent

---

#### ceremony_summaries

```sql
CREATE TABLE ceremony_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ceremony_type TEXT NOT NULL CHECK(ceremony_type IN ('standup', 'retrospective', 'planning', 'review')),
    epic_num INTEGER REFERENCES epic_state(epic_num),
    date TEXT NOT NULL,
    participants TEXT NOT NULL,  -- JSON array ["brian", "bob", "amelia"]
    duration_minutes INTEGER,
    key_outcomes TEXT,  -- JSON array ["Outcome 1", "Outcome 2"]
    action_items_created INTEGER DEFAULT 0,
    doc_id INTEGER REFERENCES documents(id),  -- Link to full transcript
    metadata JSON
);

CREATE INDEX idx_ceremony_summaries_epic ON ceremony_summaries(epic_num);
CREATE INDEX idx_ceremony_summaries_type ON ceremony_summaries(ceremony_type);
```

**Purpose**: Fast ceremony history queries
**Performance**: <1ms for recent ceremonies

---

#### learning_index

```sql
CREATE TABLE learning_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,  -- e.g., "error-handling", "testing"
    summary TEXT NOT NULL,  -- 1-2 sentence summary
    relevance TEXT NOT NULL CHECK(relevance IN ('high', 'medium', 'low')),
    contributor TEXT,  -- Who shared this learning
    epic_num INTEGER,
    source_doc_id INTEGER REFERENCES documents(id),  -- Link to full learning
    state TEXT NOT NULL CHECK(state IN ('active', 'obsolete')),
    created_at TEXT NOT NULL,
    superseded_by INTEGER REFERENCES learning_index(id),
    metadata JSON
);

CREATE INDEX idx_learning_index_topic ON learning_index(topic);
CREATE INDEX idx_learning_index_state ON learning_index(state);
```

**Purpose**: Fast learning queries by topic/relevance
**Performance**: <1ms for top learnings by topic

---

## Git Transaction Model

### Transaction Flow

```python
# Every operation follows this pattern:

def operation():
    # 1. Pre-check
    if not git.is_working_tree_clean():
        raise StateError("Working tree has uncommitted changes")

    # 2. Begin DB transaction
    registry.begin()

    try:
        # 3. Write files
        path.write_text(content)

        # 4. Update database
        registry.register_document(...)
        state.create_story(...)

        # 5. Commit DB transaction
        registry.commit()

        # 6. ATOMIC GIT COMMIT (persists both)
        git.add_all()
        git.commit(message)

        return success

    except Exception as e:
        # 7. ROLLBACK both
        registry.rollback()
        git.reset_hard()
        raise
```

### Commit Message Format

**Convention**: Conventional Commits

```
<type>(<scope>): <description>

<body>

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Examples**:

```
feat(story-5.3): create story - Implement user authentication

Created story 5.3: Implement user authentication
Epic 5 progress: 30% (3/10 stories complete)

Files modified:
- docs/stories/epic-5/story-5.3.md
- .gao-dev/documents.db

Co-Authored-By: Claude <noreply@anthropic.com>
```

```
feat(story-5.3): transition to in_progress

Story 5.3 started by Amelia
Estimated: 8.0h

Epic 5 progress: 30% (3/10 stories, 1 in progress)

Co-Authored-By: Claude <noreply@anthropic.com>
```

```
docs(epic-5): hold stand-up ceremony - 3 action items created

Participants: Brian, Bob, Amelia, Murat, John
Duration: 15 minutes

Key outcomes:
- Story 5.3 blocked on API design decision
- Created 3 action items (2 high, 1 medium priority)
- Epic 5 on track for completion by Friday

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## API Design

### GitIntegratedStateManager API

```python
# Create epic
epic = state_manager.create_epic(
    epic_num=5,
    epic_title="User Authentication",
    metadata={"feature": "auth", "owner": "john"}
)
# → Creates file, DB record, git commit

# Create story
story = state_manager.create_story(
    epic_num=5,
    story_num=3,
    content="## Story 5.3: Implement login\n\n...",
    metadata={
        "title": "Implement login",
        "estimate_hours": 8.0,
        "assignee": "amelia"
    }
)
# → Creates file, DB records, git commit

# Transition story
state_manager.transition_story(
    story_id="5.3",
    new_state="in_progress"
)
# → Updates DB, git commit

# Complete story
state_manager.complete_story(
    story_id="5.3",
    actual_hours=7.5
)
# → Updates DB, git commit

# Hold ceremony
state_manager.hold_ceremony(
    ceremony_type="standup",
    epic_num=5,
    transcript=[...],
    outcomes=["Outcome 1", "Outcome 2"],
    action_items=[
        {"summary": "Fix API bug", "assignee": "amelia", "priority": "high"},
        {"summary": "Update docs", "assignee": "bob", "priority": "medium"}
    ]
)
# → Creates files, DB records, git commit
```

### FastContextLoader API

```python
# Get epic context (fast)
context = fast_loader.get_epic_context(epic_num=5)
# → <5ms query, returns EpicContext dataclass

# Access context
print(f"Epic {context.epic_num}: {context.epic_title}")
print(f"Progress: {context.progress_percent}%")
print(f"Stories: {context.completed_stories}/{context.total_stories}")
print(f"Current: {context.current_story}")
print(f"Action items: {len(context.active_action_items)}")
print(f"Learnings: {len(context.recent_learnings)}")

# Get agent-specific context
amelia_context = fast_loader.get_agent_context("amelia", epic_num=5)
# → <5ms, returns dict with Amelia's stories, action items, learnings

# Analyze existing project
project_state = fast_loader.analyze_existing_project(Path("project"))
# → <10ms, returns ProjectState with active epics, current story, etc.
```

---

## Performance Optimization

### Query Optimization

**Indexes on All Foreign Keys**:
```sql
CREATE INDEX idx_story_state_epic ON story_state(epic_num);
CREATE INDEX idx_action_items_epic ON action_items(epic_num);
CREATE INDEX idx_ceremony_summaries_epic ON ceremony_summaries(epic_num);
```

**Composite Indexes for Common Queries**:
```sql
CREATE INDEX idx_action_items_state_assignee
ON action_items(state, assignee);

CREATE INDEX idx_story_state_epic_state
ON story_state(epic_num, state);
```

**JSON Aggregation with Limits**:
```python
# Don't fetch all action items, limit to top 20
(SELECT json_group_array(...)
 FROM action_items
 WHERE epic_num = ? AND state != 'done'
 ORDER BY priority DESC, created_at DESC
 LIMIT 20)
```

### Performance Benchmarks

**Target Performance**:

| Operation | Target | Measurement |
|-----------|--------|-------------|
| get_epic_context() | <5ms | pytest-benchmark |
| get_agent_context() | <5ms | pytest-benchmark |
| create_story() | <100ms | Including git commit |
| transition_story() | <50ms | DB update + git commit |
| analyze_existing_project() | <10ms | Database query only |

**Benchmark Suite**:

```python
# tests/performance/test_context_loading.py

def test_epic_context_performance(benchmark):
    """Benchmark epic context loading."""
    result = benchmark(
        fast_loader.get_epic_context,
        epic_num=5
    )

    # Assert <5ms
    assert benchmark.stats['mean'] < 0.005

def test_agent_context_performance(benchmark):
    """Benchmark agent context loading."""
    result = benchmark(
        fast_loader.get_agent_context,
        "amelia",
        epic_num=5
    )

    # Assert <5ms
    assert benchmark.stats['mean'] < 0.005
```

---

## Error Handling & Rollback

### Error Scenarios

**Scenario 1: File Write Fails**
```python
try:
    path.write_text(content)  # ← FAILS (disk full)
    registry.register_document(...)  # ← Never executes
except Exception as e:
    registry.rollback()  # ← No DB changes
    git.reset_hard()     # ← No file changes
    # System back to clean state
```

**Scenario 2: Database Update Fails**
```python
try:
    path.write_text(content)  # ← Success
    registry.register_document(...)  # ← FAILS (constraint violation)
except Exception as e:
    registry.rollback()  # ← Rolls back DB
    git.reset_hard()     # ← Removes file
    # System back to clean state
```

**Scenario 3: Git Commit Fails**
```python
try:
    path.write_text(content)  # ← Success
    registry.register_document(...)  # ← Success
    registry.commit()  # ← Success
    git.add_all()  # ← Success
    git.commit(message)  # ← FAILS (git error)
except Exception as e:
    registry.rollback()  # ← Already committed, can't rollback
    git.reset_hard()     # ← Removes uncommitted file
    # Problem: DB committed but git didn't

    # Solution: Re-open DB transaction, rollback manually
    # This is edge case, log error, require manual fix
```

### Rollback Testing

```python
def test_rollback_on_file_error():
    """Test rollback when file write fails."""
    # Mock file write to fail
    with patch('pathlib.Path.write_text', side_effect=IOError("Disk full")):
        with pytest.raises(StateError):
            state_manager.create_story(5, 3, content, metadata)

    # Verify rollback
    assert git.is_working_tree_clean()
    assert not Path("docs/stories/epic-5/story-5.3.md").exists()
    assert registry.get_by_path("docs/stories/epic-5/story-5.3.md") is None

def test_rollback_on_db_error():
    """Test rollback when DB update fails."""
    # Mock DB operation to fail
    with patch.object(registry, 'register_document', side_effect=IntegrityError):
        with pytest.raises(StateError):
            state_manager.create_story(5, 3, content, metadata)

    # Verify rollback
    assert git.is_working_tree_clean()
    assert not Path("docs/stories/epic-5/story-5.3.md").exists()
```

---

## Migration Strategy

### Migration Phases

**Phase 1: Create State Tables** (Migration 005)
```sql
-- Executed via DocumentRegistry migration system
-- File: gao_dev/lifecycle/migrations/005_add_state_tables.sql

-- Creates 5 new tables with indexes
-- Git commit: "migration: phase 1 - create state tables"
```

**Phase 2: Backfill Epic State**
```python
def _phase_2_backfill_epics(self):
    epic_files = glob("docs/epics/epic-*.md")

    for epic_file in epic_files:
        epic_num, title = parse_epic_file(epic_file)
        self.state.epics.create(epic_num, title)

    # Git commit: "migration: phase 2 - backfill 8 epics"
```

**Phase 3: Backfill Story State**
```python
def _phase_3_backfill_stories(self):
    story_files = glob("docs/stories/**/*.md", recursive=True)

    for story_file in story_files:
        story_id, data = parse_story_file(story_file)

        # Infer state from git history
        state = self._infer_story_state_from_git(story_file)

        self.state.stories.create(
            story_id, data['epic_num'], data['title'],
            data.get('estimate_hours', 0), state
        )

    # Git commit: "migration: phase 3 - backfill 42 stories"
```

**Phase 4: Validate Migration**
```python
def _phase_4_validate(self):
    # Validate epic totals match
    for epic in registry.get_all_documents(type=DocumentType.EPIC):
        epic_num = epic.epic
        db_state = self.state.epics.get(epic_num)
        file_count = len(glob(f"docs/stories/epic-{epic_num}/*.md"))

        assert db_state.total_stories == file_count

    # Git commit: "migration: phase 4 - validation passed"
```

### Rollback Strategy

```python
def rollback_migration(self, checkpoint_sha: str):
    """
    Rollback to checkpoint.

    Process:
    1. Delete migration branch
    2. Checkout main
    3. Verify at checkpoint SHA
    """
    self.git.delete_branch("migration/hybrid-architecture", force=True)
    self.git.checkout("main")

    current_sha = self.git.get_head_sha()
    assert current_sha == checkpoint_sha

    logger.info("Migration rolled back", checkpoint=checkpoint_sha)
```

---

## Testing Strategy

### Test Pyramid

```
           ┌──────────────┐
           │  E2E Tests   │  5 tests
           │ (Full flow)  │
           └──────────────┘
         ┌──────────────────┐
         │Integration Tests │  40 tests
         │ (Multi-component)│
         └──────────────────┘
     ┌────────────────────────┐
     │    Unit Tests          │  150 tests
     │ (Single component)     │
     └────────────────────────┘
```

### Unit Tests (~150 tests)

**GitManager Enhanced Methods** (30 tests):
- test_is_working_tree_clean_true()
- test_is_working_tree_clean_false()
- test_reset_hard_rollback()
- test_get_head_sha()
- test_delete_branch()
- test_get_last_commit_for_file()
- ... (24 more)

**StateCoordinator & Services** (50 tests):
- test_create_epic_state()
- test_create_story_state()
- test_transition_story()
- test_update_epic_progress()
- test_create_action_item()
- ... (45 more)

**FastContextLoader** (20 tests):
- test_get_epic_context_fast()
- test_get_agent_context_amelia()
- test_get_agent_context_bob()
- test_analyze_existing_project()
- ... (16 more)

**GitIntegratedStateManager** (30 tests):
- test_create_story_atomic()
- test_rollback_on_error()
- test_pre_check_fails_dirty_tree()
- test_transition_story_atomic()
- ... (26 more)

**GitMigrationManager** (15 tests):
- test_migration_success()
- test_migration_rollback_on_error()
- test_phase_1_create_tables()
- test_infer_story_state_from_git()
- ... (11 more)

**GitAwareConsistencyChecker** (20 tests):
- test_detect_uncommitted_changes()
- test_detect_orphaned_records()
- test_detect_unregistered_files()
- test_repair_sync_db_from_file()
- ... (16 more)

### Integration Tests (~40 tests)

**Git Transaction Integration** (15 tests):
- test_create_story_commits_to_git()
- test_rollback_undoes_file_and_db()
- test_concurrent_operations_serialized()
- ... (12 more)

**Migration Integration** (10 tests):
- test_full_migration_success()
- test_migration_rollback_complete()
- test_backfill_preserves_data()
- ... (7 more)

**Orchestrator Integration** (10 tests):
- test_orchestrator_uses_git_state_manager()
- test_cli_commands_create_git_commits()
- ... (8 more)

**Consistency Integration** (5 tests):
- test_consistency_check_full_flow()
- test_repair_restores_consistency()
- ... (3 more)

### E2E Tests (~5 tests)

**Complete Workflows**:
- test_e2e_create_epic_to_completion()
- test_e2e_ceremony_with_context_loading()
- test_e2e_existing_project_migration()
- test_e2e_error_recovery_full_rollback()
- test_e2e_multi_story_workflow()

### Performance Tests (~5 tests)

**Benchmarks**:
- test_benchmark_epic_context_under_5ms()
- test_benchmark_agent_context_under_5ms()
- test_benchmark_create_story_under_100ms()
- test_benchmark_existing_project_under_10ms()
- test_benchmark_large_epic_50_stories()

---

## Deployment Plan

### Week 1: Epic 22 - Orchestrator Decomposition

**Deliverables**:
- Decomposed orchestrator (<300 LOC facade)
- 4-5 focused services created
- 75+ refactoring tests
- Zero breaking changes

**Success Criteria**:
- Orchestrator god class eliminated
- All services <200 LOC
- All existing tests still pass
- Public API unchanged

**Deployment**: Internal refactoring (no user-facing changes)

---

### Week 2: Epic 23 - GitManager Enhancement

**Deliverables**:
- Enhanced GitManager with 14 new methods
- 30 unit tests
- API documentation

**Success Criteria**:
- All new methods tested
- No breaking changes to existing code
- GitCommitManager deprecated

**Deployment**: Internal library update (no user-facing changes)

---

### Week 3: Epic 24 - State Tables & Tracker

**Deliverables**:
- Migration 005 (state tables)
- StateCoordinator + 5 services
- 50 unit tests
- Database schema documentation

**Success Criteria**:
- Migration runs successfully
- All services <200 LOC
- Query performance <5ms

**Deployment**: Database schema update (automatic via migration system)

---

### Week 4: Epic 25 - Git-Integrated State Manager

**Deliverables**:
- GitIntegratedStateManager
- FastContextLoader
- GitMigrationManager
- GitAwareConsistencyChecker
- 70 tests (unit + integration)

**Success Criteria**:
- All atomic operations tested
- Rollback works 100%
- Context loading <5ms
- Migration safe with rollback

**Deployment**: New services ready for integration

---

### Week 5: Epic 26 - Multi-Agent Ceremonies

**Deliverables**:
- CeremonyOrchestrator fully implemented
- ConversationManager
- Stand-up, retrospective, planning ceremonies
- 35+ ceremony tests

**Success Criteria**:
- All ceremony types functional
- Ceremony artifacts tracked
- Context loading <5ms during ceremonies

**Deployment**: Ceremony system enabled

---

### Week 6: Epic 27 - Integration & Migration

**Deliverables**:
- Full orchestrator integration
- CLI command updates
- Migration tools
- Documentation (CLAUDE.md, migration guide)
- 15 E2E tests

**Success Criteria**:
- All tests passing (>80% coverage)
- Documentation complete
- Migration tested on real projects
- Performance targets met

**Deployment**: Full feature release

---

## Appendices

### Appendix A: File Structure

```
gao_dev/
├── core/
│   ├── git_manager.py (ENHANCED)
│   └── services/
│       ├── state_coordinator.py (NEW)
│       ├── epic_state_service.py (NEW)
│       ├── story_state_service.py (NEW)
│       ├── action_item_service.py (NEW)
│       ├── ceremony_service.py (NEW)
│       ├── learning_index_service.py (NEW)
│       ├── fast_context_loader.py (NEW)
│       ├── git_integrated_state_manager.py (NEW)
│       ├── git_migration_manager.py (NEW)
│       └── git_consistency_checker.py (NEW)
│
├── lifecycle/
│   └── migrations/
│       └── 005_add_state_tables.sql (NEW)
│
└── sandbox/
    ├── git_commit_manager.py (DEPRECATED - DELETE)
    └── git_cloner.py (KEEP - No changes)
```

### Appendix B: LOC Summary

| Component | LOC | Status |
|-----------|-----|--------|
| GitManager (enhanced) | +200 | Enhancement |
| StateCoordinator | 300 | New |
| 5× State Services | 5×100 = 500 | New |
| FastContextLoader | 400 | New |
| GitIntegratedStateManager | 600 | New |
| GitMigrationManager | 500 | New |
| GitAwareConsistencyChecker | 300 | New |
| Migration SQL | 100 | New |
| GitCommitManager | -259 | Deleted |
| **Total** | **+2,641 LOC** | |

### Appendix C: Performance Targets

| Metric | Target | Validation |
|--------|--------|------------|
| Epic context load | <5ms | pytest-benchmark |
| Agent context load | <5ms | pytest-benchmark |
| Story creation | <100ms | pytest-benchmark |
| Story transition | <50ms | pytest-benchmark |
| Existing project analysis | <10ms | pytest-benchmark |
| Database size (100 epics) | <50MB | Manual check |
| Test coverage | >80% | pytest --cov |

---

**Document Status**: Updated - Aligned with Gap Analysis
**Next Steps**: Bob to create story breakdown for 6 epics (22-27)
**Approval Required**: Technical Lead, Product Owner

---

**Version History**:
- v1.0 (2025-11-09): Initial technical specification
- v1.1 (2025-11-09): Updated for Epics 22-27 (gap analysis alignment)

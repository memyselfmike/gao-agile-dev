# Hybrid Wisdom Management Architecture
## Database for State, Files for Artifacts

**Date**: 2025-11-08
**Purpose**: Define efficient hybrid architecture - SQLite for state, Markdown for artifacts
**Status**: Architectural Solution

---

## Core Principle

> **"Leave clues as you go" - The database should tell the complete story**

**Files (.md)** = Long-form artifacts for humans
**Database (SQLite)** = Fast state tracking and context for machines

---

## The Problem with File-Only Approach

**Scenario**: Brian needs to start a stand-up for Epic 5

**Bad (File-Heavy)**:
```python
# Read 10+ files to build context
epic_doc = read_file("docs/epic-5.md")              # 5KB
story_1 = read_file("docs/stories/story-5.1.md")    # 2KB
story_2 = read_file("docs/stories/story-5.2.md")    # 2KB
# ... read 8 more stories
standup_1 = read_file("docs/ceremonies/epic-4-standup.md")  # 10KB
retro_1 = read_file("docs/ceremonies/epic-4-retro.md")      # 15KB
# ... parse, extract, aggregate

# Total: 50KB+ read, lots of parsing, slow
```

**Good (Database-First)**:
```python
# Single fast query
context = db.query("""
    SELECT
        epic_num, epic_title, progress_percent,
        completed_stories, total_stories, current_story,
        (SELECT json_group_array(json_object(
            'id', id, 'summary', summary, 'assignee', assignee
        )) FROM action_items WHERE epic_num = 5 AND state = 'active') as action_items,
        (SELECT json_group_array(json_object(
            'topic', topic, 'summary', summary
        )) FROM learnings WHERE state = 'active' LIMIT 5) as learnings
    FROM epic_state WHERE epic_num = 5
""")

# Total: <1ms, precise JSON, no parsing
```

**Difference**: **50KB + parsing vs <1KB + instant JSON**

---

## What Goes Where

### Files (.md) - Artifacts for Humans

**Purpose**: Long-form documentation that humans read and reference

| Artifact | Path | Size | When to Read |
|----------|------|------|--------------|
| PRD | `docs/PRD.md` | 5-20KB | PM needs requirements |
| Architecture | `docs/Architecture.md` | 10-50KB | Architect needs design |
| Epic | `docs/epics/epic-5.md` | 2-10KB | Rarely (overview only) |
| Story | `docs/stories/epic-5/story-5.1.md` | 1-5KB | Developer implementing |
| Stand-up Transcript | `docs/ceremonies/epic-5/standup.md` | 5-20KB | Review past decisions |
| Retrospective | `docs/ceremonies/epic-5/retro.md` | 10-30KB | Review learnings |
| Learning | `docs/learnings/error-handling.md` | 2-10KB | When pattern needed |
| ADR | `docs/decisions/adr-001-use-postgresql.md` | 2-10KB | When decision referenced |

**Total**: Hundreds of KB, but **rarely all read at once**

### Database (SQLite) - State for Machines

**Purpose**: Fast, structured, queryable state that tells the complete story

| State | Table | Typical Size | Query Time |
|-------|-------|--------------|------------|
| Document metadata | `documents` | 100s of rows | <1ms |
| Epic progress | `epic_state` | 10s of rows | <1ms |
| Story status | `story_state` | 100s of rows | <1ms |
| Action items | `action_items` | 10s of rows | <1ms |
| Ceremony summaries | `ceremony_summaries` | 10s of rows | <1ms |
| Learning index | `learning_index` | 10s of rows | <1ms |
| Relationships | `document_relationships` | 100s of rows | <1ms |

**Total**: <1MB database, all queries <5ms

---

## Extended Database Schema

### Current Tables (Already Exist)

```sql
-- Documents table (metadata only, not content)
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,  -- prd, epic, story, standup, learning, etc.
    state TEXT NOT NULL,  -- draft, active, obsolete, archived
    created_at TEXT NOT NULL,
    modified_at TEXT NOT NULL,
    author TEXT,
    feature TEXT,
    epic INTEGER,
    story TEXT,
    content_hash TEXT,
    owner TEXT,
    reviewer TEXT,
    review_due_date TEXT,
    metadata JSON  -- Extensible
);

-- Relationships
CREATE TABLE document_relationships (
    parent_id INTEGER NOT NULL REFERENCES documents(id),
    child_id INTEGER NOT NULL REFERENCES documents(id),
    relationship_type TEXT NOT NULL,  -- derived_from, implements, etc.
    PRIMARY KEY (parent_id, child_id, relationship_type)
);
```

### New Tables (For Efficient Context)

```sql
-- Epic state tracking (fast progress queries)
CREATE TABLE epic_state (
    epic_num INTEGER PRIMARY KEY,
    epic_title TEXT NOT NULL,
    state TEXT NOT NULL,  -- planning, active, complete, archived
    total_stories INTEGER NOT NULL,
    completed_stories INTEGER NOT NULL,
    in_progress_stories INTEGER NOT NULL,
    progress_percent REAL NOT NULL,
    current_story TEXT,  -- e.g., "5.3"
    start_date TEXT,
    target_date TEXT,
    actual_completion_date TEXT,
    metadata JSON
);

-- Story state tracking (fast status queries)
CREATE TABLE story_state (
    story_id TEXT PRIMARY KEY,  -- e.g., "5.3"
    epic_num INTEGER NOT NULL REFERENCES epic_state(epic_num),
    story_title TEXT NOT NULL,
    state TEXT NOT NULL,  -- todo, in_progress, review, done
    assignee TEXT,
    estimate_hours REAL,
    actual_hours REAL,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    metadata JSON
);

-- Action items (fast queries for active items)
CREATE TABLE action_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    summary TEXT NOT NULL,  -- Short summary (1 sentence)
    description TEXT,  -- Optional longer description
    assignee TEXT NOT NULL,
    state TEXT NOT NULL,  -- todo, in_progress, done
    priority TEXT NOT NULL,  -- low, medium, high, critical
    due_date TEXT,
    epic_num INTEGER,
    source_doc_id INTEGER REFERENCES documents(id),  -- Link to standup/retro
    created_at TEXT NOT NULL,
    completed_at TEXT,
    metadata JSON
);

-- Ceremony summaries (fast queries for past ceremonies)
CREATE TABLE ceremony_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ceremony_type TEXT NOT NULL,  -- standup, retrospective, planning, review
    epic_num INTEGER REFERENCES epic_state(epic_num),
    date TEXT NOT NULL,
    participants TEXT NOT NULL,  -- JSON array of agent names
    duration_minutes INTEGER,
    key_outcomes TEXT,  -- JSON array of key outcomes
    action_items_created INTEGER DEFAULT 0,
    doc_id INTEGER REFERENCES documents(id),  -- Link to full transcript
    metadata JSON
);

-- Learning index (fast queries for relevant learnings)
CREATE TABLE learning_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,  -- error-handling, testing, architecture, etc.
    summary TEXT NOT NULL,  -- 1-2 sentence summary
    relevance TEXT NOT NULL,  -- high, medium, low
    contributor TEXT,  -- Who shared this learning
    epic_num INTEGER,
    source_doc_id INTEGER REFERENCES documents(id),  -- Link to full learning doc
    state TEXT NOT NULL,  -- active, obsolete
    created_at TEXT NOT NULL,
    superseded_by INTEGER REFERENCES learning_index(id),
    metadata JSON
);

-- Indexes for fast queries
CREATE INDEX idx_epic_state_state ON epic_state(state);
CREATE INDEX idx_story_state_epic ON story_state(epic_num);
CREATE INDEX idx_story_state_state ON story_state(state);
CREATE INDEX idx_story_state_assignee ON story_state(assignee);
CREATE INDEX idx_action_items_assignee ON action_items(assignee);
CREATE INDEX idx_action_items_state ON action_items(state);
CREATE INDEX idx_action_items_epic ON action_items(epic_num);
CREATE INDEX idx_ceremony_summaries_epic ON ceremony_summaries(epic_num);
CREATE INDEX idx_ceremony_summaries_type ON ceremony_summaries(ceremony_type);
CREATE INDEX idx_learning_index_topic ON learning_index(topic);
CREATE INDEX idx_learning_index_state ON learning_index(state);
```

---

## Efficient Context Loading Patterns

### Pattern 1: Epic Context for Ceremonies

```python
class FastContextLoader:
    """Loads precise context from database (no file reads)."""

    def get_epic_context(self, epic_num: int) -> EpicContext:
        """Get epic context with single query (<5ms)."""

        query = """
        SELECT
            e.epic_num,
            e.epic_title,
            e.state,
            e.total_stories,
            e.completed_stories,
            e.in_progress_stories,
            e.progress_percent,
            e.current_story,
            e.start_date,
            e.target_date,

            -- Active action items (JSON array)
            (SELECT json_group_array(json_object(
                'id', id,
                'summary', summary,
                'assignee', assignee,
                'priority', priority,
                'due_date', due_date
            ))
            FROM action_items
            WHERE epic_num = e.epic_num AND state != 'done'
            ) as active_action_items,

            -- Recent learnings (JSON array, top 5 most relevant)
            (SELECT json_group_array(json_object(
                'topic', topic,
                'summary', summary,
                'relevance', relevance
            ))
            FROM learning_index
            WHERE state = 'active'
            ORDER BY relevance DESC, created_at DESC
            LIMIT 5
            ) as recent_learnings,

            -- Recent ceremonies (JSON array)
            (SELECT json_group_array(json_object(
                'type', ceremony_type,
                'date', date,
                'key_outcomes', key_outcomes
            ))
            FROM ceremony_summaries
            WHERE epic_num = e.epic_num
            ORDER BY date DESC
            ) as recent_ceremonies,

            -- Story breakdown by state (JSON)
            (SELECT json_object(
                'todo', COUNT(CASE WHEN state = 'todo' THEN 1 END),
                'in_progress', COUNT(CASE WHEN state = 'in_progress' THEN 1 END),
                'review', COUNT(CASE WHEN state = 'review' THEN 1 END),
                'done', COUNT(CASE WHEN state = 'done' THEN 1 END)
            )
            FROM story_state
            WHERE epic_num = e.epic_num
            ) as story_breakdown

        FROM epic_state e
        WHERE e.epic_num = ?
        """

        result = db.execute(query, (epic_num,)).fetchone()

        return EpicContext(
            epic_num=result['epic_num'],
            epic_title=result['epic_title'],
            progress=result['progress_percent'],
            completed_stories=result['completed_stories'],
            total_stories=result['total_stories'],
            current_story=result['current_story'],
            active_action_items=json.loads(result['active_action_items']),
            recent_learnings=json.loads(result['recent_learnings']),
            recent_ceremonies=json.loads(result['recent_ceremonies']),
            story_breakdown=json.loads(result['story_breakdown'])
        )

        # Total time: <5ms
        # Total data: <5KB precise JSON
        # No file reads required!
```

**Result**: Agent gets **exactly** what they need in **<5ms** with **no file reads**.

### Pattern 2: Agent-Specific Context

```python
def get_agent_context(self, agent_name: str, epic_num: int) -> Dict[str, Any]:
    """Get agent-specific context (role-based)."""

    base_context = self.get_epic_context(epic_num)

    if agent_name == "bob":  # Scrum Master
        return {
            **base_context,
            "my_action_items": db.execute("""
                SELECT id, summary, priority, due_date
                FROM action_items
                WHERE assignee = 'bob' AND state != 'done'
            """).fetchall(),
            "story_velocity": self._calculate_velocity(epic_num),
            "blocked_stories": db.execute("""
                SELECT story_id, story_title, metadata->>'blocker'
                FROM story_state
                WHERE epic_num = ? AND metadata->>'blocked' = 'true'
            """, (epic_num,)).fetchall()
        }

    elif agent_name == "amelia":  # Developer
        return {
            **base_context,
            "my_stories": db.execute("""
                SELECT story_id, story_title, state, estimate_hours
                FROM story_state
                WHERE epic_num = ? AND assignee = 'amelia'
            """, (epic_num,)).fetchall(),
            "my_action_items": db.execute("""
                SELECT id, summary, priority, due_date
                FROM action_items
                WHERE assignee = 'amelia' AND state != 'done'
            """).fetchall(),
            "relevant_learnings": db.execute("""
                SELECT topic, summary
                FROM learning_index
                WHERE topic IN ('code-quality', 'testing', 'debugging')
                AND state = 'active'
                ORDER BY relevance DESC LIMIT 3
            """).fetchall()
        }

    elif agent_name == "murat":  # QA
        return {
            **base_context,
            "test_coverage": self._get_test_coverage(epic_num),
            "quality_issues": db.execute("""
                SELECT story_id, metadata->>'coverage', metadata->>'issues'
                FROM story_state
                WHERE epic_num = ?
                AND (metadata->>'coverage' < '80' OR metadata->>'issues' IS NOT NULL)
            """, (epic_num,)).fetchall(),
            "quality_learnings": db.execute("""
                SELECT topic, summary
                FROM learning_index
                WHERE topic IN ('testing', 'quality', 'coverage')
                AND state = 'active'
            """).fetchall()
        }

    # Each query: <1ms
    # Total context: <2KB
    # Precisely what agent needs!
```

### Pattern 3: Existing Project Support

```python
def analyze_existing_project(self, project_path: Path) -> ProjectState:
    """
    Spin up GAO-Dev on existing project.

    Database tells us:
    - What documents exist
    - What state they're in
    - What epics/stories are active
    - What needs attention

    NO need to read all files!
    """

    # Query database for current state
    current_state = db.execute("""
        SELECT
            (SELECT COUNT(*) FROM documents WHERE type = 'epic' AND state = 'active') as active_epics,
            (SELECT COUNT(*) FROM documents WHERE type = 'story' AND state = 'active') as active_stories,
            (SELECT COUNT(*) FROM action_items WHERE state != 'done') as pending_actions,
            (SELECT epic_num FROM epic_state ORDER BY epic_num DESC LIMIT 1) as latest_epic,
            (SELECT current_story FROM epic_state WHERE state = 'active' LIMIT 1) as current_story
    """).fetchone()

    if current_state['active_epics'] > 0:
        # Project has active work
        current_epic = current_state['latest_epic']
        epic_context = self.get_epic_context(current_epic)

        return ProjectState(
            status="active",
            current_epic=current_epic,
            current_story=current_state['current_story'],
            epic_context=epic_context,
            pending_actions=current_state['pending_actions']
        )
    else:
        # Project needs initialization
        return ProjectState(
            status="needs_initialization",
            documents_found=self._count_documents(),
            suggest_actions=["Run 'gao-dev init' to start"]
        )

    # Total time: <10ms
    # Complete project status without reading any files!
```

---

## State Updates During Workflow

### When Agent Creates Document

```python
# 1. Agent creates file
Path("docs/stories/epic-5/story-5.3.md").write_text(content)

# 2. DocumentLifecycle registers it
doc = doc_lifecycle.register_document(
    path=Path("docs/stories/epic-5/story-5.3.md"),
    doc_type=DocumentType.STORY,
    author="bob",
    metadata={"epic_num": 5, "story_num": 3, "estimate_hours": 8}
)

# 3. StateTracker updates fast-query tables
state_tracker.create_story_state(
    story_id="5.3",
    epic_num=5,
    story_title=extract_title(content),
    estimate_hours=8,
    state="todo"
)

# 4. StateTracker updates epic progress
state_tracker.update_epic_progress(epic_num=5)
# Recalculates: total_stories, progress_percent, etc.

# Result: Database has clues, file has content
```

### When Agent Completes Story

```python
# 1. Agent commits code
git.commit("feat: implement story 5.3")

# 2. StateTracker updates story state
state_tracker.transition_story(
    story_id="5.3",
    new_state="done",
    actual_hours=7.5
)

# 3. StateTracker updates epic progress
state_tracker.update_epic_progress(epic_num=5)
# completed_stories += 1, progress_percent recalculated

# 4. If epic complete, trigger ceremony
if state_tracker.is_epic_complete(epic_num=5):
    ceremony_orchestrator.hold_standup(epic_num=5)

# Result: Database always current, no file reads needed
```

### When Ceremony Creates Artifacts

```python
async def hold_standup(self, epic_num: int):
    # 1. Load context from database (fast)
    context = fast_loader.get_epic_context(epic_num)

    # 2. Execute conversation (ephemeral)
    transcript = []
    async for turn in conversation.execute(context):
        transcript.append(turn)

    # 3. Write transcript file
    transcript_path = Path(f"docs/ceremonies/epic-{epic_num}/standup.md")
    transcript_path.write_text(format_transcript(transcript))

    # 4. Register document (metadata in DB)
    transcript_doc = doc_lifecycle.register_document(
        path=transcript_path,
        doc_type=DocumentType.STANDUP,
        metadata={"epic_num": epic_num, "participants": [...]}
    )

    # 5. Extract and store action items (summary in DB, detail in file)
    action_items = extract_action_items(transcript)
    for item in action_items:
        # Write detail to file
        item_path = Path(f"docs/action-items/epic-{epic_num}-ai-{item.id}.md")
        item_path.write_text(format_action_item(item))

        # Register document
        item_doc = doc_lifecycle.register_document(
            path=item_path,
            doc_type=DocumentType.ACTION_ITEM,
            metadata={"epic_num": epic_num, "assignee": item.assignee}
        )

        # Store summary in fast-query table
        state_tracker.create_action_item(
            summary=item.summary,  # 1 sentence
            assignee=item.assignee,
            priority=item.priority,
            epic_num=epic_num,
            source_doc_id=transcript_doc.id
        )

    # 6. Store ceremony summary (in DB for fast queries)
    state_tracker.create_ceremony_summary(
        ceremony_type="standup",
        epic_num=epic_num,
        participants=[...],
        key_outcomes=[...],  # Extracted summaries
        action_items_created=len(action_items),
        doc_id=transcript_doc.id
    )

    # Result:
    # - Files: Full detailed artifacts for humans
    # - Database: Fast-query summaries for agents
    # - Best of both worlds!
```

---

## Agent Prompt Construction

### Before (Inefficient)

```python
# Read many files, build large prompt
prompt = f"""
You are Amelia (Developer) in a stand-up for Epic 5.

<epic_document>
{read_file("docs/epic-5.md")}  # 5KB
</epic_document>

<previous_standup>
{read_file("docs/ceremonies/epic-4-standup.md")}  # 10KB
</previous_standup>

<your_stories>
{read_file("docs/stories/story-5.1.md")}  # 2KB
{read_file("docs/stories/story-5.2.md")}  # 2KB
{read_file("docs/stories/story-5.3.md")}  # 2KB
</your_stories>

<learnings>
{read_file("docs/learnings/error-handling.md")}  # 5KB
{read_file("docs/learnings/testing.md")}  # 5KB
</learnings>

...
"""
# Total: 31KB+ in prompt, lots of file I/O, slow
```

### After (Efficient)

```python
# Single fast query, precise JSON context
context = fast_loader.get_agent_context("amelia", epic_num=5)

prompt = f"""
You are Amelia (Developer) in a stand-up for Epic 5.

<epic_context>
Epic: {context.epic_title}
Progress: {context.progress}% ({context.completed_stories}/{context.total_stories} stories)
Current story: {context.current_story}
</epic_context>

<your_work>
Stories assigned to you:
{json.dumps(context.my_stories, indent=2)}

Action items for you:
{json.dumps(context.my_action_items, indent=2)}
</your_work>

<relevant_learnings>
{json.dumps(context.relevant_learnings, indent=2)}
</relevant_learnings>

<previous_outcomes>
Recent ceremony outcomes:
{json.dumps(context.recent_ceremonies, indent=2)}
</previous_outcomes>

Please provide your status update (2-3 sentences).
"""
# Total: <2KB precise JSON, <5ms query, no file reads
```

**Difference**: 31KB → 2KB, lots of files → 1 query, slow → <5ms

---

## StateTracker Service

```python
class StateTracker:
    """
    Maintains fast-query state tables.

    Automatically updates state tables whenever documents change.
    """

    def __init__(self, registry: DocumentRegistry):
        self.registry = registry

    def create_epic_state(self, epic_num: int, epic_title: str) -> None:
        """Initialize epic state tracking."""
        self.registry.execute("""
            INSERT INTO epic_state (
                epic_num, epic_title, state,
                total_stories, completed_stories, in_progress_stories,
                progress_percent, start_date
            ) VALUES (?, ?, 'planning', 0, 0, 0, 0, datetime('now'))
        """, (epic_num, epic_title))

    def create_story_state(
        self,
        story_id: str,
        epic_num: int,
        story_title: str,
        estimate_hours: float
    ) -> None:
        """Register new story."""
        self.registry.execute("""
            INSERT INTO story_state (
                story_id, epic_num, story_title, state,
                assignee, estimate_hours, created_at
            ) VALUES (?, ?, ?, 'todo', NULL, ?, datetime('now'))
        """, (story_id, epic_num, story_title, estimate_hours))

        # Update epic total
        self.update_epic_progress(epic_num)

    def transition_story(
        self,
        story_id: str,
        new_state: str,
        actual_hours: Optional[float] = None
    ) -> None:
        """Transition story to new state."""
        updates = {"state": new_state}
        if actual_hours:
            updates["actual_hours"] = actual_hours
        if new_state == "in_progress":
            updates["started_at"] = "datetime('now')"
        if new_state == "done":
            updates["completed_at"] = "datetime('now')"

        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        self.registry.execute(
            f"UPDATE story_state SET {set_clause} WHERE story_id = ?",
            list(updates.values()) + [story_id]
        )

        # Update epic progress
        epic_num = self.get_epic_for_story(story_id)
        self.update_epic_progress(epic_num)

    def update_epic_progress(self, epic_num: int) -> None:
        """Recalculate epic progress from story states."""
        result = self.registry.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN state = 'done' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN state = 'in_progress' THEN 1 ELSE 0 END) as in_progress
            FROM story_state WHERE epic_num = ?
        """, (epic_num,)).fetchone()

        total = result['total']
        completed = result['completed']
        in_progress = result['in_progress']
        progress = (completed / total * 100) if total > 0 else 0

        # Get current story (first non-done)
        current = self.registry.execute("""
            SELECT story_id FROM story_state
            WHERE epic_num = ? AND state != 'done'
            ORDER BY story_id LIMIT 1
        """, (epic_num,)).fetchone()

        self.registry.execute("""
            UPDATE epic_state SET
                total_stories = ?,
                completed_stories = ?,
                in_progress_stories = ?,
                progress_percent = ?,
                current_story = ?,
                state = CASE
                    WHEN ? = ? THEN 'complete'
                    WHEN ? > 0 THEN 'active'
                    ELSE 'planning'
                END
            WHERE epic_num = ?
        """, (
            total, completed, in_progress, progress,
            current['story_id'] if current else None,
            completed, total,  # For complete check
            completed,  # For active check
            epic_num
        ))

    def create_action_item(
        self,
        summary: str,
        assignee: str,
        priority: str,
        epic_num: int,
        source_doc_id: int
    ) -> int:
        """Create action item (summary in DB, details in file)."""
        cursor = self.registry.execute("""
            INSERT INTO action_items (
                summary, assignee, state, priority,
                epic_num, source_doc_id, created_at
            ) VALUES (?, ?, 'todo', ?, ?, ?, datetime('now'))
        """, (summary, assignee, priority, epic_num, source_doc_id))

        return cursor.lastrowid

    def create_ceremony_summary(
        self,
        ceremony_type: str,
        epic_num: int,
        participants: List[str],
        key_outcomes: List[str],
        action_items_created: int,
        doc_id: int
    ) -> None:
        """Store ceremony summary for fast queries."""
        self.registry.execute("""
            INSERT INTO ceremony_summaries (
                ceremony_type, epic_num, date, participants,
                key_outcomes, action_items_created, doc_id
            ) VALUES (?, ?, datetime('now'), ?, ?, ?, ?)
        """, (
            ceremony_type, epic_num,
            json.dumps(participants),
            json.dumps(key_outcomes),
            action_items_created, doc_id
        ))

    def create_learning_index(
        self,
        topic: str,
        summary: str,
        relevance: str,
        contributor: str,
        epic_num: int,
        source_doc_id: int
    ) -> int:
        """Index learning for fast queries (full content in file)."""
        cursor = self.registry.execute("""
            INSERT INTO learning_index (
                topic, summary, relevance, contributor,
                epic_num, source_doc_id, state, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'active', datetime('now'))
        """, (topic, summary, relevance, contributor, epic_num, source_doc_id))

        return cursor.lastrowid
```

---

## Benefits Summary

### 1. Performance

**Database queries**: <5ms for complete epic context
**File reads**: 50-100ms+ for same data
**Difference**: **10-20x faster**

### 2. Precision

**Database**: Exactly what agent needs (2KB)
**Files**: Everything (31KB), agent must parse and filter
**Difference**: **15x less data**

### 3. Existing Project Support

**Database**: Immediate project status query
**Files**: Must scan and read many files
**Difference**: **Instant vs minutes**

### 4. Scalability

**Database**: Performance constant (indexed queries)
**Files**: Performance degrades with size
**Difference**: **O(1) vs O(n)**

### 5. Simplicity

**Database**: Single query for complete context
**Files**: 10+ file reads + parsing + aggregation
**Difference**: **1 call vs 10+ calls**

---

## Implementation Plan

### Phase 1: Add State Tables (Week 1)

**Migration 005**: Add state tracking tables
- `epic_state`
- `story_state`
- `action_items`
- `ceremony_summaries`
- `learning_index`

### Phase 2: Create StateTracker (Week 1)

**Service**: `gao_dev/core/services/state_tracker.py`
- Epic state management
- Story state management
- Action item tracking
- Ceremony summaries
- Learning indexing

### Phase 3: Create FastContextLoader (Week 2)

**Service**: `gao_dev/core/services/fast_context_loader.py`
- `get_epic_context()` - Complete epic state
- `get_agent_context()` - Role-specific context
- `analyze_existing_project()` - Project status
- All queries <5ms, no file reads

### Phase 4: Integrate with Orchestration (Week 2)

- CeremonyOrchestrator uses FastContextLoader
- BrianCoordinator uses FastContextLoader
- Agents receive precise JSON context
- StateTracker auto-updates on document changes

---

## Conclusion

**Hybrid Architecture Solves All Problems**:

✅ **Fast Context Loading** - <5ms database queries vs 50ms+ file reads
✅ **Precise Context** - Agents get exactly what they need (2KB vs 31KB)
✅ **Existing Project Support** - Database tells complete story instantly
✅ **Scalability** - O(1) indexed queries vs O(n) file scans
✅ **Human-Readable Artifacts** - Full documents preserved as Markdown
✅ **Machine-Queryable State** - Structured data in SQLite

**Best of both worlds**: Files for humans, database for machines.

---

**Document Version**: 1.0
**Last Updated**: 2025-11-08
**Status**: Architectural Solution - Ready for Implementation

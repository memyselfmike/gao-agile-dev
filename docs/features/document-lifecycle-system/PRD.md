# Product Requirements Document
## GAO-Dev Document Lifecycle & Context Management System

**Version:** 1.0.0
**Date:** 2025-11-04
**Status:** Draft
**Author:** John (Product Manager)
**Epic:** Document Lifecycle Management (Epics 11-15)

---

## Executive Summary

### Vision
Transform GAO-Dev's document and context management from ad-hoc file creation to a comprehensive lifecycle system that tracks document states, manages context across workflows, provides dynamic meta-prompts, and ensures domain-agnostic operation across all GAO teams (dev, ops, legal, research).

### The Problem
GAO-Dev creates dozens of documents during development (PRDs, architectures, stories, test reports, QA validations) but has NO systematic way to:
- Track document lifecycle states (draft, active, obsolete, archived)
- Inject relevant context into agent prompts dynamically
- Reuse quality checklists across different domains
- Maintain state across workflow boundaries
- Archive or clean up stale documents
- Query document relationships and dependencies

This leads to:
- Agents re-reading ALL documents to find relevant context
- No automatic archival when documents become obsolete
- Manual context management in every prompt
- Domain-specific hardcoded checklists
- State tracking spread across markdown files and memory
- No lineage tracking for artifacts

### The Solution
Build an integrated Document Lifecycle & Context Management System with five major components:

1. **Document Lifecycle Manager** - Tracks document states, metadata, and relationships
2. **Meta-Prompt Engine** - Dynamically injects context into prompts using references
3. **Checklist Plugin System** - YAML-based reusable checklists (like Epic 10 prompts)
4. **State Tracking Database** - SQLite for queryable workflow/story state
5. **Context Persistence Layer** - Manages context across workflow boundaries

### Goals
1. **Lifecycle Management**: Track every document from creation to archival
2. **Context Automation**: Automatically inject relevant context into agent prompts
3. **Reusability**: Share checklists across domains (dev, ops, legal, research)
4. **State Queryability**: Fast queries for story status, epic progress, document lineage
5. **Domain Agnostic**: Work seamlessly across all GAO teams
6. **Performance**: <5% overhead from lifecycle management

---

## Problem Statement

### Current State: Document Chaos

#### Documents Created Today (Identified from Codebase Analysis)

**Pre-Development Phase:**
- `docs/PRD.md` - Product Requirements Document
- `docs/ARCHITECTURE.md` - System architecture
- `docs/tech-spec.md` - Technical specifications
- `docs/epics.md` - Epic definitions
- `docs/user-story.md` - User stories (Level 0/1)

**During Development:**
- `docs/stories/epic-N/story-N.M.md` - Story files (hundreds)
- `docs/bmm-workflow-status.md` - Current workflow status
- `docs/sprint-status.yaml` - Sprint tracking
- Implementation files (`src/**/*.py`, `tests/**/*.py`)
- Git commit messages and history

**Post-Development:**
- `docs/features/<feature-name>/QA_VALIDATION_*.md` - QA reports
- `docs/features/<feature-name>/TEST_REPORT_*.md` - Test results
- `docs/features/<feature-name>/FINAL_QA_REPORT_*.md` - Final QA
- `sandbox/projects/<project>/metrics.db` - Benchmark metrics
- HTML reports in `sandbox/reports/`

**Quality Gates:**
- `gao_dev/checklists/qa-comprehensive.md` - Quality checklist (only ONE exists!)
- Acceptance criteria in story files
- Workflow validation templates

#### The Problems

**1. No Lifecycle Tracking**
- Documents are created but never marked as obsolete
- No way to know which PRD is "current" vs archived
- Story files accumulate indefinitely
- No automatic archival strategy

**2. Manual Context Injection**
- Agents must manually specify which documents to read
- No automatic injection of epic context into stories
- No automatic injection of architecture into implementations
- Every prompt manually lists context files

**3. Hardcoded Checklists**
- Only ONE checklist file: `qa-comprehensive.md`
- Domain-specific (software engineering only)
- Cannot reuse for ops, legal, research
- Not plugin-extensible

**4. State Tracking Fragmentation**
- Story status: Markdown files (`**Status**: Done`)
- Sprint status: YAML file (`sprint-status.yaml`)
- Benchmark state: SQLite database (`metrics.db`)
- Workflow status: Markdown file (`bmm-workflow-status.md`)
- No unified query interface

**5. No Context Persistence**
- Context lost between workflow executions
- Agents re-read same documents repeatedly
- No cache of "current epic context"
- No lineage tracking (which story affects which files)

**6. Document Discovery Problems**
- No index of all documents
- No metadata (author, created date, last modified, state)
- No relationships (PRD → Architecture → Epics → Stories)
- No search capability

### Target State: Managed Document Lifecycle

**What We Want:**

```yaml
# Document with full lifecycle metadata
document:
  path: "docs/features/sandbox-system/PRD.md"
  type: "prd"
  state: "active"  # draft, active, obsolete, archived
  created: "2025-10-27"
  last_modified: "2025-11-03"
  author: "John"
  related_documents:
    - "docs/features/sandbox-system/ARCHITECTURE.md"
    - "docs/features/sandbox-system/epics.md"
  replaces: null
  replaced_by: null
  metadata:
    feature: "sandbox-system"
    epic: null
    story: null
```

```yaml
# Meta-prompt with automatic context injection
prompt_template:
  name: "implement_story"
  user_prompt: |
    Implement Story {{story_num}}.

    Story Requirements:
    @doc:stories/epic-{{epic_num}}/story-{{story_num}}.md

    Epic Context:
    @doc:features/{{feature_name}}/epics.md#epic-{{epic_num}}

    Architecture Guidelines:
    @doc:features/{{feature_name}}/ARCHITECTURE.md

    Quality Checklist:
    @checklist:testing/unit-test-standards
    @checklist:code-quality/solid-principles
```

```python
# Unified state tracking
state_db.query(
    "SELECT * FROM stories WHERE epic = 3 AND status = 'in_progress'"
)
state_db.get_epic_progress(epic_num=3)
state_db.get_document_lineage(path="docs/PRD.md")
```

---

## User Stories

### Epic 11: Document Lifecycle Management

**US-11.1: As a system administrator, I want all documents tracked with lifecycle metadata so I can understand document states and relationships**
- Documents have state (draft, active, obsolete, archived)
- Metadata includes author, dates, type, relationships
- Query interface for finding documents
- Automatic state transitions

**US-11.2: As a developer, I want obsolete documents automatically archived so the docs folder doesn't accumulate stale files**
- Configurable archival rules
- Automatic archival on state transition
- Archived documents moved to `.archive/` subdirectory
- Metadata preserved in lifecycle database

**US-11.3: As an agent, I want to query current documents so I only read relevant, up-to-date information**
- `get_current_prd()` returns active PRD
- `get_current_architecture()` returns active architecture
- `get_epic_context(epic_num)` returns epic definition + related docs
- Performance: <100ms for queries

**US-11.4: As a product manager, I want to track document lineage so I understand which documents led to which implementations**
- PRD → Architecture → Epics → Stories → Implementations
- Query: "Which stories relate to this PRD?"
- Query: "Which code files were created for this story?"
- Visual lineage graph generation

### Epic 12: Meta-Prompt System & Context Injection

**US-12.1: As a prompt engineer, I want to use @doc: references in prompts so context is automatically injected**
- `@doc:path/to/file.md` - Inject full document
- `@doc:path/to/file.md#section` - Inject specific section
- `@doc:stories/epic-3/story-3.1.md@acceptance_criteria` - Inject specific part
- Support for glob patterns: `@doc:stories/epic-3/*.md`

**US-12.2: As an agent developer, I want context automatically injected based on workflow phase so prompts don't need manual context management**
- `create_story` workflow automatically injects epic context
- `implement_story` workflow automatically injects story + architecture
- `validate_story` workflow automatically injects checklist + acceptance criteria
- Configurable per-workflow

**US-12.3: As a system designer, I want @config: references extended to support queries so prompts can access dynamic data**
- `@config:current_epic` - Current epic number
- `@config:project_name` - Project name
- `@query:stories.where(epic=3, status='done')` - Query results
- `@context:epic_definition` - Cached context

**US-12.4: As a domain expert, I want meta-prompts to work across domains so gao-ops/gao-legal can reuse the system**
- Domain-agnostic reference resolution
- Customizable document paths per domain
- Support for domain-specific document types
- No hardcoded software engineering assumptions

### Epic 13: Checklist Plugin System

**US-13.1: As a quality engineer, I want checklists defined in YAML like prompts so they're reusable and version-controlled**
- YAML format: `gao_dev/config/checklists/`
- Categories: testing, code-quality, security, deployment, operations, legal, compliance
- Inherit from base checklists
- Plugin-extensible

**US-13.2: As an agent, I want to inject checklists into prompts using @checklist: references so I have clear guidelines**
- `@checklist:testing/unit-test-standards`
- `@checklist:code-quality/solid-principles`
- `@checklist:security/owasp-top-10`
- `@checklist:legal/contract-review`

**US-13.3: As a plugin developer, I want to provide domain-specific checklists so my plugin adds value**
- Legal plugin provides contract review checklists
- Ops plugin provides deployment checklists
- Research plugin provides peer review checklists
- Loaded via plugin system like prompts

**US-13.4: As a QA engineer, I want checklist results tracked in lifecycle database so I can query compliance**
- Checklist execution tracked per story/artifact
- Pass/fail status per checklist item
- Query: "Which stories passed security checklist?"
- Generate compliance reports

### Epic 14: State Tracking Database (SQLite)

**US-14.1: As a system architect, I want unified state tracking in SQLite so state is queryable and performant**
- Tables: stories, epics, workflows, documents
- Relationships: epics → stories → artifacts
- Fast queries: <50ms for status checks
- Replaces: markdown status, YAML sprint status

**US-14.2: As a developer, I want story status tracked in database so I can query progress**
- `state_db.get_story_status(epic=3, story=1)` → "in_progress"
- `state_db.get_epic_progress(epic=3)` → {completed: 7, total: 9}
- `state_db.get_stories_by_status("in_progress")` → list
- Real-time updates

**US-14.3: As a product manager, I want sprint tracking in database so I can generate reports**
- Sprint definition and goals
- Story assignment to sprints
- Velocity tracking
- Burndown data generation
- Historical sprint data

**US-14.4: As an architect, I want markdown files synced to database so existing workflows continue working**
- Two-way sync: markdown ↔ SQLite
- Update markdown → update database
- Query database → generate markdown report
- Hybrid approach: human-readable + queryable

### Epic 15: Context Persistence Layer

**US-15.1: As an orchestrator, I want to cache frequently accessed context so agents don't re-read documents**
- Cache: current epic definition, architecture, coding standards
- TTL: 5 minutes (configurable)
- Invalidation: on document update
- Performance: 10x faster than re-reading

**US-15.2: As a workflow engine, I want to pass context between workflow steps so context persists**
- Workflow context object: carries state across steps
- Contains: current epic, story, architecture, decisions
- Passed to all agents in workflow
- Persisted to database between executions

**US-15.3: As an agent, I want to access context without specifying files so prompts are simpler**
- `context.get_epic_definition()` - Current epic
- `context.get_architecture_decisions()` - Key decisions
- `context.get_coding_standards()` - Standards for current project
- `context.get_acceptance_criteria()` - Current story criteria

**US-15.4: As a system designer, I want context lineage tracked so I understand context flow**
- Track: which context was used for which decision
- Query: "What architecture version was used for Story 3.1?"
- Query: "Which stories used outdated PRD?"
- Audit trail for compliance

---

## Features & Requirements

### Feature 1: Document Lifecycle Manager

#### 1.1 Document Registry

**Requirements:**
- REQ-1.1.1: Maintain SQLite database of all documents
- REQ-1.1.2: Track metadata: path, type, state, dates, author, relationships
- REQ-1.1.3: Support document types: prd, architecture, epic, story, test-report, qa-report, checklist, code, config
- REQ-1.1.4: Index documents for fast search (<100ms)
- REQ-1.1.5: Watch filesystem for document changes (optional)

**Schema:**
```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('draft', 'active', 'obsolete', 'archived')),
    created_at TEXT NOT NULL,
    modified_at TEXT NOT NULL,
    author TEXT,
    feature TEXT,
    epic INTEGER,
    story TEXT,
    metadata JSON,
    content_hash TEXT
);

CREATE TABLE document_relationships (
    parent_id INTEGER REFERENCES documents(id),
    child_id INTEGER REFERENCES documents(id),
    relationship_type TEXT NOT NULL,
    PRIMARY KEY (parent_id, child_id)
);
```

#### 1.2 Lifecycle State Machine

**States:**
- `draft` - Being created/edited
- `active` - Current version in use
- `obsolete` - Superseded but kept for reference
- `archived` - Moved to archive directory

**Transitions:**
- draft → active (on approval/completion)
- active → obsolete (on replacement)
- obsolete → archived (manual or automatic after N days)
- active → archived (if marked as no longer needed)

**Requirements:**
- REQ-1.2.1: Implement state machine with validation
- REQ-1.2.2: Only one active document per type+feature
- REQ-1.2.3: Automatic state transitions on events
- REQ-1.2.4: Hooks for custom state transition logic

#### 1.3 Archival System

**Requirements:**
- REQ-1.3.1: Move archived documents to `.archive/` subdirectory
- REQ-1.3.2: Preserve directory structure in archive
- REQ-1.3.3: Configurable archival rules (age, state, conditions)
- REQ-1.3.4: Archival metadata preserved in database
- REQ-1.3.5: Restore from archive capability

**Configuration:**
```yaml
archival:
  enabled: true
  rules:
    - type: "prd"
      state: "obsolete"
      age_days: 30
      action: "archive"
    - type: "story"
      state: "obsolete"
      age_days: 90
      action: "archive"
```

#### 1.4 Document Query Interface

**Requirements:**
- REQ-1.4.1: Query documents by type, state, feature, epic, story
- REQ-1.4.2: Get current/active document for type+feature
- REQ-1.4.3: Get document lineage (ancestors + descendants)
- REQ-1.4.4: Full-text search in document content
- REQ-1.4.5: Query performance <100ms for simple queries

**API:**
```python
# Query interface
doc_mgr.get_current("prd", feature="sandbox-system")
doc_mgr.get_document_by_path("docs/PRD.md")
doc_mgr.get_documents_by_type("story", state="active")
doc_mgr.get_epic_documents(epic_num=3)
doc_mgr.get_document_lineage("docs/PRD.md")
doc_mgr.search("authentication", doc_type="story")
```

### Feature 2: Meta-Prompt Engine

#### 2.1 Reference Syntax Extension

**New Reference Types:**
- `@doc:path/to/file.md` - Inject full document
- `@doc:path/to/file.md#section` - Inject markdown section
- `@doc:path/to/file.md@yaml_key` - Inject YAML field
- `@doc:glob:stories/epic-3/*.md` - Inject multiple documents
- `@checklist:category/name` - Inject checklist
- `@query:table.where(condition)` - Inject query results
- `@context:key` - Inject cached context

**Requirements:**
- REQ-2.1.1: Extend PromptLoader to support new reference types
- REQ-2.1.2: Resolve references at render time
- REQ-2.1.3: Cache resolved references for performance
- REQ-2.1.4: Handle missing references gracefully (warning + empty string)
- REQ-2.1.5: Support nested references (reference inside referenced file)

#### 2.2 Section Extraction

**Requirements:**
- REQ-2.2.1: Extract markdown sections by heading: `#section`
- REQ-2.2.2: Extract YAML fields: `@yaml_key`
- REQ-2.2.3: Extract acceptance criteria from stories
- REQ-2.2.4: Extract code blocks from markdown
- REQ-2.2.5: Preserve formatting in extracted content

**Example:**
```yaml
# Story file: docs/stories/epic-3/story-3.1.md
# Extract acceptance criteria only:
@doc:stories/epic-3/story-3.1.md#acceptance-criteria

# Extract technical details section:
@doc:features/sandbox-system/ARCHITECTURE.md#component-design
```

#### 2.3 Automatic Context Injection

**Requirements:**
- REQ-2.3.1: Configure per-workflow automatic context
- REQ-2.3.2: Inject epic context for story workflows
- REQ-2.3.3: Inject architecture for implementation workflows
- REQ-2.3.4: Inject checklists for validation workflows
- REQ-2.3.5: Override automatic context with explicit references

**Configuration:**
```yaml
# Workflow: implement_story
automatic_context:
  - "@doc:stories/epic-{{epic}}/story-{{story}}.md"
  - "@doc:features/{{feature}}/epics.md#epic-{{epic}}"
  - "@doc:features/{{feature}}/ARCHITECTURE.md"
  - "@checklist:testing/unit-test-standards"
  - "@config:coding_standards"
```

#### 2.4 Query References

**Requirements:**
- REQ-2.4.1: Support SQL-like queries in references
- REQ-2.4.2: Format query results as markdown
- REQ-2.4.3: Limit query result size (max 1000 chars)
- REQ-2.4.4: Query performance <100ms

**Example:**
```yaml
user_prompt: |
  Review the following completed stories:

  @query:stories.where(epic={{epic}}, status='done').format('markdown')

  Ensure consistency across implementations.
```

### Feature 3: Checklist Plugin System

#### 3.1 Checklist YAML Format

**Requirements:**
- REQ-3.1.1: YAML format similar to prompt templates
- REQ-3.1.2: Support categories and subcategories
- REQ-3.1.3: Support checklist inheritance (extends)
- REQ-3.1.4: Markdown formatting in items
- REQ-3.1.5: Metadata: name, description, version, author

**Format:**
```yaml
# gao_dev/config/checklists/testing/unit-test-standards.yaml
checklist:
  name: "Unit Test Standards"
  category: "testing"
  version: "1.0.0"
  description: "Standards for unit tests in GAO-Dev"

  extends: "testing/base-testing-standards"

  items:
    - id: "test-coverage"
      text: "Test coverage is >80% for all new code"
      severity: "high"

    - id: "test-isolation"
      text: "Tests are isolated and do not depend on execution order"
      severity: "high"

    - id: "test-performance"
      text: "All tests complete in <5 seconds"
      severity: "medium"

  metadata:
    domain: "software-engineering"
    applicable_to: ["story-implementation", "code-review"]
```

#### 3.2 Checklist Loader

**Requirements:**
- REQ-3.2.1: Load checklists from YAML files
- REQ-3.2.2: Validate against JSON schema
- REQ-3.2.3: Resolve inheritance (extends)
- REQ-3.2.4: Cache loaded checklists
- REQ-3.2.5: Plugin checklists override core checklists

**API:**
```python
checklist_loader = ChecklistLoader(config_dir / "checklists")
checklist = checklist_loader.load_checklist("testing/unit-test-standards")
rendered = checklist_loader.render_checklist(checklist)
```

#### 3.3 Checklist Registry

**Requirements:**
- REQ-3.3.1: Centralized registry of all checklists
- REQ-3.3.2: Discover checklists from core + plugins
- REQ-3.3.3: Query checklists by category, domain, tags
- REQ-3.3.4: List available checklists for CLI
- REQ-3.3.5: Validate checklist uniqueness

#### 3.4 Checklist Execution Tracking

**Requirements:**
- REQ-3.4.1: Track checklist execution per story/artifact
- REQ-3.4.2: Record pass/fail per checklist item
- REQ-3.4.3: Store execution results in state database
- REQ-3.4.4: Generate compliance reports
- REQ-3.4.5: Query: "Which stories failed security checklist?"

**Schema:**
```sql
CREATE TABLE checklist_executions (
    id INTEGER PRIMARY KEY,
    checklist_name TEXT NOT NULL,
    artifact_type TEXT NOT NULL,  -- story, pr, deployment, contract
    artifact_id TEXT NOT NULL,
    executed_at TEXT NOT NULL,
    executed_by TEXT,
    overall_status TEXT CHECK(overall_status IN ('pass', 'fail', 'partial'))
);

CREATE TABLE checklist_results (
    id INTEGER PRIMARY KEY,
    execution_id INTEGER REFERENCES checklist_executions(id),
    item_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pass', 'fail', 'skip', 'na')),
    notes TEXT
);
```

### Feature 4: State Tracking Database

#### 4.1 Database Schema

**Requirements:**
- REQ-4.1.1: Stories table with full lifecycle tracking
- REQ-4.1.2: Epics table with goals and progress
- REQ-4.1.3: Sprints table for sprint planning
- REQ-4.1.4: Workflows table for workflow execution tracking
- REQ-4.1.5: Relationships: sprints → epics → stories → artifacts

**Schema:**
```sql
-- Epics
CREATE TABLE epics (
    id INTEGER PRIMARY KEY,
    epic_num INTEGER UNIQUE NOT NULL,
    name TEXT NOT NULL,
    feature TEXT,
    goal TEXT,
    status TEXT CHECK(status IN ('planned', 'active', 'completed', 'cancelled')),
    created_at TEXT NOT NULL,
    completed_at TEXT,
    total_points INTEGER DEFAULT 0,
    completed_points INTEGER DEFAULT 0
);

-- Stories
CREATE TABLE stories (
    id INTEGER PRIMARY KEY,
    epic_num INTEGER NOT NULL REFERENCES epics(epic_num),
    story_num INTEGER NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending', 'in_progress', 'done', 'blocked', 'cancelled')),
    priority TEXT CHECK(priority IN ('P0', 'P1', 'P2', 'P3')),
    points INTEGER,
    owner TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    file_path TEXT,
    UNIQUE(epic_num, story_num)
);

-- Sprints
CREATE TABLE sprints (
    id INTEGER PRIMARY KEY,
    sprint_num INTEGER UNIQUE NOT NULL,
    name TEXT NOT NULL,
    goal TEXT,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT CHECK(status IN ('planned', 'active', 'completed'))
);

-- Story-Sprint Assignment
CREATE TABLE story_assignments (
    story_id INTEGER REFERENCES stories(id),
    sprint_id INTEGER REFERENCES sprints(id),
    PRIMARY KEY (story_id, sprint_id)
);

-- Workflow Executions
CREATE TABLE workflow_executions (
    id INTEGER PRIMARY KEY,
    workflow_name TEXT NOT NULL,
    story_id INTEGER REFERENCES stories(id),
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT CHECK(status IN ('running', 'completed', 'failed')),
    metadata JSON
);
```

#### 4.2 Markdown-SQLite Sync

**Requirements:**
- REQ-4.2.1: Sync story markdown files to database
- REQ-4.2.2: Sync database changes back to markdown
- REQ-4.2.3: Detect conflicts and resolve (last-write-wins)
- REQ-4.2.4: Sync on: file save, database update, manual trigger
- REQ-4.2.5: Preserve markdown formatting and comments

**Strategy:**
- Read story file → parse frontmatter → update database
- Update database → regenerate frontmatter → write file
- Hash-based change detection (content_hash field)
- Conflict resolution: database is source of truth for status, markdown for content

#### 4.3 Query API

**Requirements:**
- REQ-4.3.1: Python API for state queries
- REQ-4.3.2: CLI commands for common queries
- REQ-4.3.3: Query performance <50ms
- REQ-4.3.4: Support complex queries (joins, aggregations)
- REQ-4.3.5: Return results as models (not raw SQL)

**API:**
```python
# State query API
state = StateTracker(db_path)

# Story queries
state.get_story(epic=3, story=1)
state.get_stories_by_status("in_progress")
state.get_stories_by_epic(epic=3)
state.get_blocked_stories()

# Epic queries
state.get_epic(epic_num=3)
state.get_epic_progress(epic_num=3)  # {completed: 7, total: 9, percentage: 77.8}
state.get_active_epics()

# Sprint queries
state.get_current_sprint()
state.get_sprint_velocity(sprint_num=2)
state.get_sprint_stories(sprint_num=2)

# Workflow queries
state.get_workflow_execution(workflow_id=42)
state.get_story_workflow_history(story_id=15)
```

#### 4.4 Migration from Markdown/YAML

**Requirements:**
- REQ-4.4.1: Import existing sprint-status.yaml
- REQ-4.4.2: Import existing story files
- REQ-4.4.3: Import bmm-workflow-status.md
- REQ-4.4.4: Preserve all existing data
- REQ-4.4.5: Validate imported data

### Feature 5: Context Persistence Layer

#### 5.1 Context Cache

**Requirements:**
- REQ-5.1.1: In-memory cache of frequently accessed documents
- REQ-5.1.2: TTL-based expiration (default: 5 minutes)
- REQ-5.1.3: Invalidation on document update
- REQ-5.1.4: LRU eviction when cache full
- REQ-5.1.5: Thread-safe access

**API:**
```python
context_cache = ContextCache(ttl=300)  # 5 minutes

# Get cached or load
context_cache.get_or_load("epic_definition", loader_func)
context_cache.invalidate("epic_definition")
context_cache.clear()
```

#### 5.2 Workflow Context Object

**Requirements:**
- REQ-5.2.1: Context object passed through workflow steps
- REQ-5.2.2: Contains: epic, story, architecture, decisions, checklists
- REQ-5.2.3: Persisted to database between workflow executions
- REQ-5.2.4: Serializable to JSON
- REQ-5.2.5: Immutable (copy-on-write)

**Model:**
```python
@dataclass
class WorkflowContext:
    """Context passed through workflow execution."""
    workflow_id: str
    epic_num: int
    story_num: Optional[int]
    feature: str

    # Cached documents
    prd: Optional[str] = None
    architecture: Optional[str] = None
    epic_definition: Optional[str] = None
    story_definition: Optional[str] = None

    # State
    current_phase: str = "analysis"
    decisions: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
```

#### 5.3 Context API

**Requirements:**
- REQ-5.3.1: Simple API for agents to access context
- REQ-5.3.2: Lazy loading (only load when accessed)
- REQ-5.3.3: Automatic resolution from context object
- REQ-5.3.4: Fallback to document manager if not cached
- REQ-5.3.5: Track context access for audit

**API:**
```python
# In agent prompt
context = get_workflow_context()

# Access methods (lazy-loaded)
epic_def = context.get_epic_definition()
architecture = context.get_architecture()
coding_standards = context.get_coding_standards()
acceptance_criteria = context.get_acceptance_criteria()
```

#### 5.4 Context Lineage Tracking

**Requirements:**
- REQ-5.4.1: Track which context was used for which artifact
- REQ-5.4.2: Record context version (document hash)
- REQ-5.4.3: Query: "What architecture was used for Story 3.1?"
- REQ-5.4.4: Detect stale context usage
- REQ-5.4.5: Generate lineage reports

**Schema:**
```sql
CREATE TABLE context_usage (
    id INTEGER PRIMARY KEY,
    artifact_type TEXT NOT NULL,
    artifact_id TEXT NOT NULL,
    document_id INTEGER REFERENCES documents(id),
    document_version TEXT,  -- content hash
    accessed_at TEXT NOT NULL,
    workflow_id TEXT
);
```

---

## Success Criteria

### Epic 11: Document Lifecycle Management
- All documents tracked in lifecycle database (100% coverage)
- Document queries return results in <100ms
- Archival system moves obsolete documents automatically
- Lineage queries show document relationships correctly
- Zero manual document state management required

### Epic 12: Meta-Prompt System
- All reference types (@doc, @checklist, @query, @context) work correctly
- Context injection reduces prompt size by 50%+
- Reference resolution time <50ms per reference
- Works across all GAO domains (dev, ops, legal, research)
- Automatic context injection reduces manual context management by 90%

### Epic 13: Checklist Plugin System
- 20+ checklists defined in YAML (testing, quality, security, deployment, operations, legal)
- Checklist loading performance <10ms
- Plugin checklists override core checklists correctly
- Checklist execution tracking in database
- Compliance reports generated successfully

### Epic 14: State Tracking Database
- All story/epic status in SQLite database
- Markdown-SQLite sync maintains consistency (bidirectional)
- Query performance <50ms for all common queries
- Sprint tracking and velocity calculations working
- 100% backwards compatibility with existing workflows

### Epic 15: Context Persistence Layer
- Context cache reduces document reads by 80%+
- Workflow context persists across executions
- Context API reduces agent prompt complexity by 70%+
- Context lineage tracking shows correct usage
- Stale context detection prevents using outdated information

### Overall System
- <5% performance overhead from lifecycle management
- Zero breaking changes to existing workflows
- 90% reduction in manual context management
- Works seamlessly across dev, ops, legal, research domains
- Plugin developers can extend all systems

---

## Non-Functional Requirements

### Performance
- Document queries: <100ms
- Reference resolution: <50ms per reference
- Context cache hit rate: >80%
- Database sync: <200ms
- Overall system overhead: <5%

### Scalability
- Support 10,000+ documents in registry
- Support 1,000+ stories per epic
- Handle 100+ concurrent workflow executions
- Database size <500MB for typical project

### Reliability
- Zero data loss in state transitions
- Automatic recovery from sync failures
- Graceful degradation if database unavailable
- Backup and restore capability

### Maintainability
- Clear separation of concerns
- Comprehensive test coverage (>80%)
- Detailed logging and observability
- Migration guides for schema changes

### Security
- No secrets in document metadata
- Access control for sensitive documents (future)
- Audit trail for state changes
- Secure archival storage

---

## Dependencies

### Internal Dependencies
- Epic 10: Prompt & Agent Configuration Abstraction (COMPLETE)
- Existing PromptLoader and PromptRegistry
- Existing plugin system
- Existing SQLite infrastructure (metrics database)

### External Dependencies
- Python 3.11+
- SQLite 3.35+
- PyYAML for checklist parsing
- jsonschema for validation
- structlog for logging

---

## Constraints

### Technical Constraints
- Must work on Windows, macOS, Linux
- SQLite for state storage (no PostgreSQL/MySQL)
- File-based document storage (no S3/cloud)
- Synchronous API (async future enhancement)

### Business Constraints
- Zero breaking changes to existing workflows
- 100% backwards compatibility with Epic 10
- Must work across all GAO domains
- Plugin system must be extensible

### Timeline Constraints
- Epic 11: 2-3 weeks (foundational)
- Epic 12: 2 weeks (builds on Epic 11)
- Epic 13: 1-2 weeks (parallel with Epic 12)
- Epic 14: 2-3 weeks (critical path)
- Epic 15: 1-2 weeks (polish)
- **Total**: 8-12 weeks for complete system

---

## Risks & Mitigations

### Risk 1: Performance Degradation
**Severity**: High
**Mitigation**:
- Benchmark all queries and optimizations
- Implement caching aggressively
- Use indexes on all foreign keys
- Profile before/after

### Risk 2: Sync Conflicts (Markdown ↔ SQLite)
**Severity**: Medium
**Mitigation**:
- Database is source of truth for state
- Markdown is source of truth for content
- Hash-based conflict detection
- Clear conflict resolution rules

### Risk 3: Complexity Creep
**Severity**: Medium
**Mitigation**:
- Start with MVP for each epic
- Incremental feature additions
- Regular reviews of complexity
- Refactor aggressively

### Risk 4: Plugin Breaking Changes
**Severity**: Medium
**Mitigation**:
- Versioned plugin APIs
- Deprecation warnings
- Migration guides
- Test suite for plugins

### Risk 5: Database Schema Changes
**Severity**: Low
**Mitigation**:
- Schema versioning
- Migration scripts
- Automated migration testing
- Rollback capability

---

## Future Enhancements

### Phase 2 (Post-Epic 15)
- Full-text search in documents (SQLite FTS5)
- Document diff and version comparison
- Visual document lineage graph (mermaid/graphviz)
- Real-time document sync (file watchers)
- Document templates system

### Phase 3
- Access control and permissions
- Collaborative editing support
- Document approval workflows
- Integration with external systems (Jira, Notion)
- AI-powered document analysis

### Phase 4
- Cloud storage integration (S3, Azure)
- Real-time collaboration
- Document review and comments
- Automated document generation
- Multi-project support

---

## Appendix A: Document Types Inventory

Based on codebase analysis, these documents are currently created:

| Document Type | Path Pattern | Created By | Lifecycle |
|--------------|--------------|------------|-----------|
| PRD | `docs/PRD.md` | John | Manual → Active → Obsolete |
| Architecture | `docs/ARCHITECTURE.md` | Winston | Manual → Active → Obsolete |
| Tech Spec | `docs/tech-spec.md` | Winston | Manual → Active → Obsolete |
| Epics | `docs/epics.md` | John | Manual → Active → Archived |
| User Story | `docs/user-story.md` | Bob | Manual → Active → Obsolete |
| Story File | `docs/stories/epic-N/story-N.M.md` | Bob | Auto → Active → Archived |
| Workflow Status | `docs/bmm-workflow-status.md` | System | Auto → Active |
| Sprint Status | `docs/sprint-status.yaml` | System | Auto → Active |
| QA Report | `docs/features/*/QA_*.md` | Murat | Auto → Active → Archived |
| Test Report | `docs/features/*/TEST_REPORT_*.md` | Murat | Auto → Active → Archived |
| Final QA | `docs/features/*/FINAL_QA_REPORT_*.md` | Murat | Auto → Active → Archived |
| Benchmark Config | `sandbox/benchmarks/*.yaml` | Manual | Manual → Active |
| Metrics Database | `sandbox/projects/*/metrics.db` | System | Auto → Active |
| HTML Report | `sandbox/reports/*.html` | System | Auto → Active → Archived |

**Total Document Types**: 15
**Estimated Documents per Feature**: 50-100
**Lifecycle Management Need**: CRITICAL

---

## Appendix B: Reference Syntax Examples

```yaml
# Basic document reference
@doc:docs/PRD.md

# Section extraction
@doc:docs/ARCHITECTURE.md#component-design

# YAML field extraction
@doc:stories/epic-3/story-3.1.md@acceptance_criteria

# Glob pattern
@doc:glob:stories/epic-3/*.md

# Checklist reference
@checklist:testing/unit-test-standards

# Query reference
@query:stories.where(epic=3, status='done').format('markdown')

# Context reference
@context:epic_definition

# Config reference (existing)
@config:current_epic

# File reference (existing)
@file:common/responsibilities/developer.md

# Nested reference (resolved recursively)
@doc:templates/story-template.md  # Contains @checklist:testing/unit-test-standards
```

---

## Appendix C: Migration from Current State

### Migration Path

**Phase 1: Document Registry (Epic 11)**
1. Scan existing documents
2. Import metadata to database
3. Set initial states (all "active")
4. Build document relationships
5. Validate data integrity

**Phase 2: Meta-Prompts (Epic 12)**
1. Extend PromptLoader with new reference types
2. Update existing prompts to use references
3. Test with all workflows
4. Migrate hardcoded context to @doc: references
5. Performance optimization

**Phase 3: Checklists (Epic 13)**
1. Convert qa-comprehensive.md to YAML
2. Create category structure
3. Implement ChecklistLoader
4. Update workflows to use checklists
5. Add plugin support

**Phase 4: State Database (Epic 14)**
1. Create state database schema
2. Import sprint-status.yaml
3. Import story markdown files
4. Implement sync mechanism
5. Update workflows to use database

**Phase 5: Context Layer (Epic 15)**
1. Implement context cache
2. Create WorkflowContext object
3. Update orchestrators to pass context
4. Implement context API
5. Add lineage tracking

**Testing Strategy:**
- Unit tests for each component
- Integration tests for sync mechanisms
- End-to-end tests for complete workflows
- Performance benchmarks
- Backwards compatibility tests

---

*End of PRD*

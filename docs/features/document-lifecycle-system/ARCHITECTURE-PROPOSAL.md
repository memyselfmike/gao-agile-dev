# Architecture Proposal
## GAO-Dev Document Lifecycle & Context Management System
### Technical Design & Implementation Strategy

**Version:** 1.0.0
**Date:** 2025-11-04
**Author:** Winston (Technical Architect)
**Reviewers:** Mary (Engineering Manager), Brian (Engineering Manager)
**Status:** Proposal

---

## Executive Summary

This document proposes a comprehensive technical architecture for GAO-Dev's Document Lifecycle & Context Management System. The architecture addresses five critical gaps:

1. **Document Lifecycle Management** - Hybrid SQLite + Markdown approach with automatic archival/deletion
2. **Meta-Prompt System** - Dynamic context injection via @doc:, @prompt:, @checklist:, @query: references
3. **Checklist Management** - YAML-based checklists with automated validation
4. **Context Persistence** - SQLite for queryable state, markdown for human-readable content
5. **Domain Abstraction** - Configuration-driven domain support for ops, legal, research, etc.

**Key Design Decisions:**
- **Hybrid Storage:** SQLite for structured data + Markdown for content
- **Expansion Pipeline:** 8-stage prompt expansion with caching
- **State Machine:** Enforced lifecycle transitions with audit trail
- **Plugin Architecture:** First-class plugin support for domains, checklists, and agents

---

## Table of Contents

1. [Architecture Principles](#architecture-principles)
2. [System Architecture Overview](#system-architecture-overview)
3. [Hybrid Storage Design](#hybrid-storage-design)
4. [Meta-Prompt Expansion System](#meta-prompt-expansion-system)
5. [Checklist Validation Engine](#checklist-validation-engine)
6. [Context Persistence Layer](#context-persistence-layer)
7. [Domain Plugin System](#domain-plugin-system)
8. [Data Models & Schemas](#data-models--schemas)
9. [Service Layer Design](#service-layer-design)
10. [Integration Strategy](#integration-strategy)
11. [Performance Architecture](#performance-architecture)
12. [Migration Strategy](#migration-strategy)
13. [Security Considerations](#security-considerations)
14. [Deployment Architecture](#deployment-architecture)

---

## Architecture Principles

### 1. Separation of Concerns

**Principle:** Each component has a single, well-defined responsibility.

**Application:**
- DocumentManager handles lifecycle, not content
- PromptExpander handles expansion, not storage
- ChecklistManager handles validation, not execution
- StoryRepository handles persistence, not business logic

### 2. Hybrid Storage

**Principle:** Use the right tool for the job - SQLite for queries, Markdown for content.

**Rationale:**
- SQLite: Fast queries, relationships, indexes, transactions
- Markdown: Human-readable, git-friendly, easy to edit
- Together: Best of both worlds

### 3. Progressive Enhancement

**Principle:** Add features without breaking existing functionality.

**Application:**
- Dual-write mode during migration (both SQLite and YAML)
- Backward compatibility layer for old projects
- Graceful degradation when features unavailable

### 4. Plugin-First Design

**Principle:** Extensions should be first-class citizens, not afterthoughts.

**Application:**
- Domains as plugins
- Checklists as plugins
- Agents as plugins
- Clear plugin API and discovery

### 5. Caching by Default

**Principle:** Performance is a feature - cache aggressively.

**Application:**
- Prompt expansion results cached
- Document content cached
- Query results cached (with TTL)
- Checklist definitions cached

### 6. Fail-Fast with Clear Errors

**Principle:** Better to fail early with clear error than late with confusion.

**Application:**
- Invalid state transitions rejected immediately
- Missing @doc: references fail expansion
- Schema validation on all configs
- Type checking throughout

---

## System Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        GAO-Dev Core System                       │
│                                                                   │
│  ┌────────────────┐    ┌────────────────┐    ┌───────────────┐ │
│  │  Orchestrator  │───▶│ PromptExpander │───▶│  Agent Runner │ │
│  └────────────────┘    └────────────────┘    └───────────────┘ │
│           │                      │                     │         │
│           │                      ▼                     │         │
│           │            ┌──────────────────┐            │         │
│           │            │ Context Provider │            │         │
│           │            └──────────────────┘            │         │
│           │                      │                     │         │
│           ▼                      ▼                     ▼         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           Document Lifecycle & Context Layer            │    │
│  │                                                          │    │
│  │  ┌─────────────┐  ┌────────────┐  ┌────────────────┐  │    │
│  │  │  Document   │  │  Checklist │  │     Domain     │  │    │
│  │  │   Manager   │  │   Manager  │  │    Manager     │  │    │
│  │  └─────────────┘  └────────────┘  └────────────────┘  │    │
│  │                                                          │    │
│  │  ┌─────────────┐  ┌────────────┐  ┌────────────────┐  │    │
│  │  │    Story    │  │    Epic    │  │     Sprint     │  │    │
│  │  │ Repository  │  │ Repository │  │   Repository   │  │    │
│  │  └─────────────┘  └────────────┘  └────────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                               │                                  │
│                               ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Persistence Layer                      │    │
│  │                                                          │    │
│  │  ┌────────────────────┐      ┌─────────────────────┐   │    │
│  │  │  SQLite Database   │      │  Markdown Files     │   │    │
│  │  │  (State & Metadata)│      │  (Content & Docs)   │   │    │
│  │  └────────────────────┘      └─────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

1. **PromptExpander** - Expands meta-prompts with context injection
2. **DocumentManager** - Manages document lifecycle and relationships
3. **ChecklistManager** - Loads, validates, and tracks checklists
4. **StoryRepository** - CRUD and queries for stories
5. **EpicRepository** - CRUD and queries for epics
6. **SprintRepository** - Sprint tracking and velocity
7. **DomainManager** - Domain configuration loading and switching
8. **ContextProvider** - Aggregates context for prompt expansion

### Data Flow

```
User Prompt
    ↓
Brian Agent (Workflow Selection)
    ↓
Orchestrator.execute_workflow()
    ↓
Load Workflow Template
    ↓
PromptExpander.expand()
    │
    ├─→ Resolve @config: (from ConfigLoader)
    ├─→ Resolve @file: (from PromptLoader)
    ├─→ Resolve @doc: (from DocumentManager)
    ├─→ Resolve @prompt: (recursive expansion)
    ├─→ Resolve @checklist: (from ChecklistManager)
    ├─→ Resolve @query: (from StoryRepository)
    ├─→ Apply conditionals ({{#if}})
    └─→ Substitute {{variables}}
    ↓
Fully Expanded Prompt
    ↓
Agent Execution (Claude CLI)
    ↓
Artifacts Created
    ↓
DocumentManager.register_document()
    ↓
StoryRepository.update_status()
    ↓
Git Commit (atomic)
```

---

## Hybrid Storage Design

### Philosophy

**Problem:** Pure markdown is not queryable. Pure database loses git-friendliness.

**Solution:** Hybrid approach - SQLite for metadata/queries, Markdown for content.

### What Goes Where

**SQLite (Structured Data):**
```sql
-- Story metadata and state
{
  id: 61,
  epic_id: 6,
  story_number: 1,
  title: "Git Repository Integration",
  status: "completed",
  story_points: 5,
  owner: "Amelia",
  document_path: "docs/.../story-6.1.md",
  created_at: "2025-11-04T10:00:00Z",
  completed_at: "2025-11-04T16:30:00Z"
}
```

**Markdown (Human-Readable Content):**
```markdown
# Story 6.1: Git Repository Integration

**Epic**: Epic 6
**Status**: Done
**Owner**: Amelia

## User Story
As a GAO-Dev system...

## Acceptance Criteria
- AC1: Git repo initialized...
```

### Synchronization Strategy

**Phase 1: Dual Write (Weeks 1-26)**
```python
def update_story_status(story_id: int, status: StoryStatus):
    # Write to database (source of truth)
    db.execute("UPDATE stories SET status=? WHERE id=?", status, story_id)

    # Write to markdown (for human readability)
    update_markdown_frontmatter(story_path, {"Status": status})

    # Verify sync
    if not verify_sync(story_id, story_path):
        raise SyncError("Database and markdown out of sync")
```

**Phase 2: Database Primary (Weeks 27+)**
```python
def update_story_status(story_id: int, status: StoryStatus):
    # Write to database only
    db.execute("UPDATE stories SET status=? WHERE id=?", status, story_id)

    # Generate markdown on-demand
    if render_markdown_requested:
        generate_markdown_from_db(story_id)
```

### Directory Structure

```
docs/
  features/
    {feature-name}/
      current/                    # Current documents
        PRD.md                    # Content in markdown
        ARCHITECTURE.md
        epics.md
      versions/                   # Versioned documents
        PRD.v1.0.md
        PRD.v2.0.md
      active-stories/             # Current sprint stories
        epic-1/
          story-1.1.md
        epic-2/
          story-2.1.md
      archive/                    # Archived documents
        epic-1/
          stories/
            story-1.1.md
            story-1.2.md
          COMPLETION_SUMMARY.md

.gaodev/                          # Project-local data
  state.db                        # SQLite database
  cache/                          # Cache directory
    prompts/
    documents/
    queries/
  config.yaml                     # Project configuration
```

### Database Location

```python
# Default locations
DB_LOCATIONS = [
    Path(".gaodev/state.db"),           # Project-local (preferred)
    Path("~/.gaodev/global.db"),        # User global
    Path("/tmp/gaodev-{pid}.db")        # Fallback temporary
]
```

---

## Meta-Prompt Expansion System

### Expansion Pipeline

```python
class PromptExpander:
    """8-stage prompt expansion pipeline with caching."""

    def expand(
        self,
        template: PromptTemplate,
        variables: Dict[str, Any],
        context: ExecutionContext
    ) -> str:
        """
        Expand meta-prompt through 8 stages.

        Pipeline:
        1. Load template from cache or disk
        2. Resolve @config: references (e.g., @config:claude_model)
        3. Resolve @file: references (e.g., @file:common/header.md)
        4. Resolve @doc: references (e.g., @doc:PRD.md#goals)
        5. Resolve @prompt: references (e.g., @prompt:common/persona)
        6. Resolve @checklist: references (e.g., @checklist:code_quality)
        7. Resolve @query: references (e.g., @query:SELECT ...)
        8. Apply conditionals ({{#if}}) and substitute {{variables}}

        Each stage caches results for performance.
        """
```

### Reference Resolution Details

#### @doc: Resolution

```python
def resolve_doc_reference(reference: str, context: ExecutionContext) -> str:
    """
    Resolve @doc: reference to document content.

    Syntax:
    - @doc:PRD.md                  → Full document
    - @doc:ARCHITECTURE.md#services → Specific section
    - @doc:file.md#L10-20          → Line range
    - @doc:epics.md#epic-{{epic}}  → Variable in path

    Resolution:
    1. Expand variables in path ({{epic}}, {{story}})
    2. Resolve path (relative to docs/ or project root)
    3. Load document from DocumentManager (with caching)
    4. Extract section if specified (#heading or #L10-20)
    5. Return content

    Caching:
    - Cache key: (doc_path, section, context.version)
    - TTL: 5 minutes
    - Invalidate on document update
    """
```

#### @prompt: Resolution

```python
def resolve_prompt_reference(reference: str, context: ExecutionContext) -> str:
    """
    Resolve @prompt: reference recursively.

    Syntax:
    - @prompt:common/developer_persona
    - @prompt:tasks/implement_story_base

    Resolution:
    1. Load referenced prompt template
    2. Recursively expand (max depth: 10)
    3. Detect circular references
    4. Return expanded content

    Circular Reference Detection:
    - Track expansion stack
    - Error if same prompt appears twice in stack

    Example:
    @prompt:A includes @prompt:B
    @prompt:B includes @prompt:C
    @prompt:C includes @prompt:A  → ERROR: Circular reference
    """
```

#### @checklist: Resolution

```python
def resolve_checklist_reference(reference: str, context: ExecutionContext) -> str:
    """
    Resolve @checklist: reference to formatted checklist.

    Syntax:
    - @checklist:code_quality
    - @checklist:security_auth

    Resolution:
    1. Load checklist from ChecklistManager
    2. Format as markdown checkboxes
    3. Include metadata (version, severity)
    4. Show validation status if available

    Output Format:
    ## Code Quality Checklist (v1.0.0)

    - [ ] **[CRITICAL]** Type Safety - All functions have type hints
      - Automated: `mypy --strict .`
    - [ ] **[CRITICAL]** Test Coverage - Coverage >80%
      - Automated: `pytest --cov --cov-fail-under=80`
    - [ ] **[HIGH]** No Code Duplication - Follow DRY principle
      - Manual review required
    """
```

#### @query: Resolution

```python
def resolve_query_reference(reference: str, context: ExecutionContext) -> str:
    """
    Resolve @query: reference to database query results.

    Syntax:
    - @query:SELECT title FROM stories WHERE status='completed' LIMIT 5
    - @query:completed_stories  (named query)

    Security:
    - Only SELECT allowed
    - Parameterized queries only
    - Max 100 results
    - Timeout: 1 second

    Resolution:
    1. Parse SQL or lookup named query
    2. Execute via StoryRepository
    3. Format results as markdown table
    4. Cache results (TTL: 30 seconds)

    Output Format:
    | Story ID | Title                     | Status    |
    |----------|---------------------------|-----------|
    | 6.1      | Git Repository Integration| completed |
    | 6.2      | Story-Based Config        | completed |
    """
```

### Conditional Logic

```python
def apply_conditionals(template: str, context: ExecutionContext) -> str:
    """
    Apply {{#if}} conditionals using Mustache-like syntax.

    Syntax:
    {{#if condition}}
    Content if true
    {{/if}}

    {{#if condition}}
    Content if true
    {{else}}
    Content if false
    {{/if}}

    Conditions:
    - Variable existence: {{#if story.tags}}
    - Equality: {{#if project_type == "web_app"}}
    - Contains: {{#if story.tags.includes("authentication")}}
    - Boolean: {{#if automated}}

    Example:
    {{#if story.tags.includes("api")}}
    API Design Standards:
    @checklist:api_design
    {{/if}}
    """
```

### Caching Strategy

```python
class PromptCache:
    """Multi-level caching for prompt expansion."""

    def __init__(self):
        self.memory_cache = {}  # LRU cache, 100 entries
        self.disk_cache = Path(".gaodev/cache/prompts")

    def get_expanded_prompt(
        self,
        template_name: str,
        variables: Dict[str, Any],
        context: ExecutionContext
    ) -> Optional[str]:
        """
        Get expanded prompt from cache.

        Cache key: hash(template_name, variables, context.version)

        Levels:
        1. Memory cache (instant)
        2. Disk cache (fast)
        3. Miss → expand and cache

        Invalidation:
        - Template updated → invalidate all expansions
        - Document updated → invalidate expansions using that doc
        - Database updated → invalidate query expansions
        - TTL: 5 minutes
        """
```

---

## Checklist Validation Engine

### Architecture

```python
class ChecklistValidator:
    """Automated checklist validation engine."""

    def validate(
        self,
        story: Story,
        checklists: List[Checklist],
        parallel: bool = True
    ) -> ValidationResult:
        """
        Validate story against checklists.

        Process:
        1. Filter automated checks
        2. Execute checks in parallel (if enabled)
        3. Parse check output
        4. Mark items as pass/fail
        5. Store results in database
        6. Generate validation report

        Parallel Execution:
        - Use ThreadPoolExecutor
        - Max 5 concurrent checks
        - Timeout per check: 30 seconds
        """

    def execute_check(self, item: ChecklistItem) -> CheckResult:
        """
        Execute single automated check.

        Examples:
        - mypy --strict . → Type checking
        - pytest --cov --cov-fail-under=80 → Test coverage
        - ruff check . → Linting

        Output Parsing:
        - Extract pass/fail from exit code
        - Parse error messages
        - Count violations
        """
```

### Check Registration

```python
class CheckExecutor:
    """Registry of automated check executors."""

    def __init__(self):
        self.executors = {
            "mypy": MypyCheckExecutor(),
            "pytest": PytestCheckExecutor(),
            "ruff": RuffCheckExecutor(),
            "custom": CustomCheckExecutor()
        }

    def execute(self, command: str) -> CheckResult:
        """
        Execute check command.

        Parse command to determine executor:
        - "mypy --strict ." → MypyCheckExecutor
        - "pytest --cov" → PytestCheckExecutor
        - Custom script → CustomCheckExecutor
        """
```

---

## Context Persistence Layer

### Database Schema Design

```sql
-- Projects table (for multi-project support)
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    domain TEXT NOT NULL,  -- software_engineering, operations, legal, etc.
    methodology TEXT,      -- agile, kanban, waterfall
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'active',  -- active, completed, archived
    metadata JSON
);

-- Epics table
CREATE TABLE epics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    epic_number INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'planned',  -- planned, active, completed, cancelled
    start_date DATE,
    end_date DATE,
    estimated_end_date DATE,
    total_story_points INTEGER DEFAULT 0,
    completed_story_points INTEGER DEFAULT 0,
    owner TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    UNIQUE(project_id, epic_number)
);
CREATE INDEX idx_epics_status ON epics(status);
CREATE INDEX idx_epics_project ON epics(project_id);

-- Stories table
CREATE TABLE stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    epic_id INTEGER NOT NULL,
    story_number INTEGER NOT NULL,
    full_id TEXT NOT NULL,  -- "6.1", "6.2", computed from epic_num.story_num
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'draft',  -- draft, ready, in_progress, in_review, completed, blocked, skipped
    story_points INTEGER,
    priority TEXT DEFAULT 'P2',  -- P0, P1, P2, P3
    owner TEXT,
    document_path TEXT,  -- Path to story.md
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,
    FOREIGN KEY (epic_id) REFERENCES epics(id),
    UNIQUE(epic_id, story_number)
);
CREATE INDEX idx_stories_status ON stories(status);
CREATE INDEX idx_stories_epic ON stories(epic_id);
CREATE INDEX idx_stories_owner ON stories(owner);
CREATE INDEX idx_stories_full_id ON stories(full_id);

-- Story dependencies (blocks, requires, related)
CREATE TABLE story_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id INTEGER NOT NULL,
    depends_on_story_id INTEGER NOT NULL,
    dependency_type TEXT NOT NULL DEFAULT 'requires',  -- blocks, requires, related
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (story_id) REFERENCES stories(id),
    FOREIGN KEY (depends_on_story_id) REFERENCES stories(id),
    UNIQUE(story_id, depends_on_story_id)
);
CREATE INDEX idx_deps_story ON story_dependencies(story_id);
CREATE INDEX idx_deps_depends ON story_dependencies(depends_on_story_id);

-- Acceptance criteria
CREATE TABLE acceptance_criteria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id INTEGER NOT NULL,
    criteria_number INTEGER NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, passed, failed
    automated BOOLEAN DEFAULT FALSE,
    test_command TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (story_id) REFERENCES stories(id),
    UNIQUE(story_id, criteria_number)
);
CREATE INDEX idx_ac_story ON acceptance_criteria(story_id);
CREATE INDEX idx_ac_status ON acceptance_criteria(status);

-- Documents table
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL UNIQUE,
    document_type TEXT NOT NULL,  -- prd, architecture, story, epic, qa_report, etc.
    lifecycle_status TEXT NOT NULL DEFAULT 'draft',  -- draft, active, completed, archived, deleted
    version TEXT,
    epic_id INTEGER,
    story_id INTEGER,
    parent_document_id INTEGER,  -- For versioned documents
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archived_at TIMESTAMP,
    retention_days INTEGER,  -- Days before automatic deletion
    metadata JSON,
    FOREIGN KEY (epic_id) REFERENCES epics(id),
    FOREIGN KEY (story_id) REFERENCES stories(id),
    FOREIGN KEY (parent_document_id) REFERENCES documents(id)
);
CREATE INDEX idx_docs_type ON documents(document_type);
CREATE INDEX idx_docs_status ON documents(lifecycle_status);
CREATE INDEX idx_docs_epic ON documents(epic_id);
CREATE INDEX idx_docs_story ON documents(story_id);

-- Sprints table
CREATE TABLE sprints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    sprint_number INTEGER NOT NULL,
    name TEXT NOT NULL,
    goal TEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'planned',  -- planned, active, completed
    planned_story_points INTEGER DEFAULT 0,
    completed_story_points INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    UNIQUE(project_id, sprint_number)
);
CREATE INDEX idx_sprints_status ON sprints(status);
CREATE INDEX idx_sprints_project ON sprints(project_id);

-- Workflow executions
CREATE TABLE workflow_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_name TEXT NOT NULL,
    epic_id INTEGER,
    story_id INTEGER,
    status TEXT NOT NULL,  -- in_progress, completed, failed
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds REAL,
    artifacts_created JSON,  -- List of file paths
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,
    FOREIGN KEY (epic_id) REFERENCES epics(id),
    FOREIGN KEY (story_id) REFERENCES stories(id)
);
CREATE INDEX idx_workflows_status ON workflow_executions(status);
CREATE INDEX idx_workflows_story ON workflow_executions(story_id);

-- Audit log (state change history)
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,  -- epic, story, document, sprint
    entity_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,  -- status, owner, etc.
    old_value TEXT,
    new_value TEXT,
    changed_by TEXT NOT NULL,  -- Agent name or "system"
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    context JSON  -- Additional context
);
CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_changed_at ON audit_log(changed_at);
CREATE INDEX idx_audit_changed_by ON audit_log(changed_by);
```

### Common Queries (Optimized)

```sql
-- Q1: Get all in-progress stories (fast with index)
SELECT s.full_id, s.title, s.owner, e.name as epic_name
FROM stories s
JOIN epics e ON s.epic_id = e.id
WHERE s.status = 'in_progress'
ORDER BY e.epic_number, s.story_number;
-- Uses: idx_stories_status

-- Q2: Get all blocked stories with dependencies
SELECT s.full_id, s.title, GROUP_CONCAT(ds.full_id) as blocked_by
FROM stories s
JOIN story_dependencies sd ON s.id = sd.story_id
JOIN stories ds ON sd.depends_on_story_id = ds.id
WHERE s.status = 'blocked'
  AND sd.dependency_type = 'blocks'
GROUP BY s.id;
-- Uses: idx_stories_status, idx_deps_story

-- Q3: Get epic progress
SELECT
  e.epic_number,
  e.name,
  e.status,
  COUNT(s.id) as total_stories,
  SUM(CASE WHEN s.status = 'completed' THEN 1 ELSE 0 END) as completed_stories,
  SUM(s.story_points) as total_points,
  SUM(CASE WHEN s.status = 'completed' THEN s.story_points ELSE 0 END) as completed_points
FROM epics e
LEFT JOIN stories s ON e.id = s.epic_id
WHERE e.project_id = ?
GROUP BY e.id;
-- Uses: idx_stories_epic

-- Q4: Get story history (state changes)
SELECT
  changed_at,
  changed_by,
  field_name,
  old_value,
  new_value
FROM audit_log
WHERE entity_type = 'story'
  AND entity_id = ?
ORDER BY changed_at DESC;
-- Uses: idx_audit_entity

-- Q5: Get documents for story
SELECT path, document_type, lifecycle_status, updated_at
FROM documents
WHERE story_id = ?
  AND lifecycle_status != 'deleted'
ORDER BY updated_at DESC;
-- Uses: idx_docs_story
```

---

## Domain Plugin System

### Domain Configuration Format

```yaml
# domains/software_engineering.yaml
domain:
  metadata:
    name: software_engineering
    title: "Software Engineering"
    description: "Build software applications"
    version: 1.0.0
    author: "GAO-Dev Core Team"

  agents:
    - name: John
      role: Product Manager
      config: agents/john.yaml
    - name: Winston
      role: Technical Architect
      config: agents/winston.yaml
    - name: Amelia
      role: Software Developer
      config: agents/amelia.yaml
    - name: Bob
      role: Scrum Master
      config: agents/bob.yaml
    - name: Murat
      role: Test Architect
      config: agents/murat.yaml
    - name: Sally
      role: UX Designer
      config: agents/sally.yaml
    - name: Brian
      role: Engineering Manager
      config: agents/brian.yaml
    - name: Mary
      role: Engineering Manager
      config: agents/mary.yaml

  workflows:
    directories:
      - workflows/1-analysis
      - workflows/2-plan
      - workflows/3-solutioning
      - workflows/4-implementation

  document_types:
    - name: prd
      title: "Product Requirements Document"
      persistent: true
      versioned: true
    - name: architecture
      title: "System Architecture"
      persistent: true
      versioned: true
    - name: story
      title: "User Story"
      persistent: false
      archival_days: 90
    - name: qa_report
      title: "QA Validation Report"
      persistent: false
      retention_days: 30

  checklists:
    - code_quality
    - testing
    - security
    - api_design
    - database
    - git_workflow
    - deployment

  boilerplates:
    - name: python-fastapi
      repository: "https://github.com/tiangolo/full-stack-fastapi-template"
    - name: react-typescript
      repository: "https://github.com/vitejs/vite"

  scale_levels:
    config_file: scale_levels/software_engineering.yaml
```

### DomainManager Implementation

```python
class DomainManager:
    """Manages domain configurations and switching."""

    def __init__(
        self,
        domains_dir: Path,
        plugin_manager: PluginManager,
        config_loader: ConfigLoader
    ):
        self.domains_dir = domains_dir
        self.plugin_manager = plugin_manager
        self.config_loader = config_loader
        self._domains: Dict[str, DomainConfig] = {}
        self._active_domain: Optional[str] = None

    def load_domain(self, domain_name: str) -> DomainConfig:
        """
        Load domain configuration.

        Sources (in order):
        1. Built-in domains (domains/)
        2. Plugin domains
        3. User domains (~/.gaodev/domains/)
        4. Project domains (.gaodev/domains/)

        Caching: Domain configs cached after first load
        """

    def get_available_domains(self) -> List[DomainInfo]:
        """
        List all available domains.

        Returns:
        [
          DomainInfo(name="software_engineering", title="Software Engineering", source="built-in"),
          DomainInfo(name="operations", title="Operations & DevOps", source="plugin:gao-ops"),
          DomainInfo(name="legal", title="Legal", source="plugin:gao-legal")
        ]
        """

    def set_active_domain(self, domain_name: str) -> None:
        """
        Set active domain for current project.

        Updates:
        - .gaodev/config.yaml with domain selection
        - Reloads agents, workflows, checklists
        - Validates compatibility
        """

    def merge_domains(self, domain_names: List[str]) -> MergedDomainConfig:
        """
        Merge multiple domains for multi-domain projects.

        Merge Strategy:
        - Agents: Union of all agents
        - Workflows: Union with namespace prefixes
        - Document types: Union
        - Checklists: Union with namespace prefixes
        - Conflicts: Last domain wins (with warning)
        """
```

---

## Service Layer Design

### Repository Pattern

```python
class StoryRepository:
    """Data access layer for stories."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    # CRUD Operations
    def create(self, story: StoryCreate) -> Story:
        """Create new story with validation."""

    def get(self, story_id: int) -> Optional[Story]:
        """Get story by ID."""

    def get_by_full_id(self, full_id: str) -> Optional[Story]:
        """Get story by full_id (e.g., "6.1")."""

    def update(self, story_id: int, updates: StoryUpdate) -> Story:
        """Update story fields."""

    def delete(self, story_id: int) -> bool:
        """Soft delete story."""

    # Query Operations
    def find_by_status(self, status: StoryStatus) -> List[Story]:
        """Find all stories with given status."""

    def find_by_epic(self, epic_id: int) -> List[Story]:
        """Find all stories in epic."""

    def find_by_owner(self, owner: str) -> List[Story]:
        """Find all stories assigned to owner."""

    def find_blocked(self) -> List[Story]:
        """Find all blocked stories."""

    def find_in_progress(self) -> List[Story]:
        """Find all stories currently in progress."""

    # State Management
    def transition_status(
        self,
        story_id: int,
        to_status: StoryStatus,
        changed_by: str
    ) -> Story:
        """
        Transition story status with validation.

        Validates:
        - Transition is valid (via StateMachine)
        - Prerequisites met
        - Creates audit log entry
        """

    # Relationship Operations
    def get_dependencies(self, story_id: int) -> List[StoryDependency]:
        """Get all stories this story depends on."""

    def get_dependent_stories(self, story_id: int) -> List[Story]:
        """Get all stories that depend on this story."""

    def add_dependency(
        self,
        story_id: int,
        depends_on_id: int,
        dependency_type: DependencyType
    ) -> StoryDependency:
        """Add dependency between stories."""
```

### Service Layer

```python
class StoryService:
    """Business logic for story management."""

    def __init__(
        self,
        story_repo: StoryRepository,
        epic_repo: EpicRepository,
        document_manager: DocumentManager,
        event_bus: EventBus
    ):
        self.story_repo = story_repo
        self.epic_repo = epic_repo
        self.document_manager = document_manager
        self.event_bus = event_bus

    def create_story(
        self,
        epic_id: int,
        story_number: int,
        title: str,
        **kwargs
    ) -> Story:
        """
        Create new story with validation.

        Business Logic:
        - Validates epic exists
        - Validates story number unique
        - Creates story record
        - Generates full_id
        - Creates story document
        - Publishes StoryCreated event
        """

    def start_story(self, story_id: int, started_by: str) -> Story:
        """
        Start story implementation.

        Business Logic:
        - Validates story ready to start
        - Transitions status: ready → in_progress
        - Records started_at timestamp
        - Updates epic progress
        - Publishes StoryStarted event
        """

    def complete_story(
        self,
        story_id: int,
        completed_by: str,
        artifacts: List[str]
    ) -> Story:
        """
        Complete story.

        Business Logic:
        - Validates all acceptance criteria met
        - Transitions status: in_progress → completed
        - Records completed_at timestamp
        - Updates epic progress
        - Archives story documents (if configured)
        - Publishes StoryCompleted event
        """

    def block_story(
        self,
        story_id: int,
        blocked_by_story_id: int,
        reason: str
    ) -> Story:
        """
        Block story due to dependency.

        Business Logic:
        - Validates dependency story incomplete
        - Transitions status: in_progress → blocked
        - Creates dependency record
        - Notifies owner
        - Publishes StoryBlocked event
        """
```

---

## Integration Strategy

### Integration with Existing Orchestrator

```python
# Current: GAODevOrchestrator
class GAODevOrchestrator:
    def __init__(self, ...):
        # Existing components
        self.workflow_coordinator = ...
        self.story_lifecycle = ...
        self.process_executor = ...

        # NEW: Document & Context Layer
        self.document_manager = DocumentManager(...)
        self.checklist_manager = ChecklistManager(...)
        self.prompt_expander = PromptExpander(...)
        self.story_repository = StoryRepository(...)
        self.domain_manager = DomainManager(...)

    async def execute_workflow(self, ...):
        # ENHANCED: Load workflow with context expansion
        workflow_template = self.workflow_registry.get(workflow_name)

        # NEW: Expand with context
        context = self._build_context(epic_id, story_id)
        expanded_prompt = self.prompt_expander.expand(
            template=workflow_template,
            variables=variables,
            context=context
        )

        # Existing: Execute workflow
        result = await self.workflow_coordinator.execute(expanded_prompt)

        # NEW: Register artifacts
        for artifact in result.artifacts:
            self.document_manager.register_document(
                path=artifact,
                story_id=story_id
            )

        return result
```

### Migration Path

**Phase 1: Parallel Implementation (No Breaking Changes)**
```python
# Dual write: Both old and new systems
def update_story_status(story_id, status):
    # OLD: Update sprint-status.yaml
    update_yaml_file(story_id, status)

    # NEW: Update database
    story_repo.transition_status(story_id, status, "system")

    # Verify sync
    verify_consistency()
```

**Phase 2: New System Primary (Old System Read-Only)**
```python
# Database primary, YAML generated
def update_story_status(story_id, status):
    # NEW: Update database
    story_repo.transition_status(story_id, status, "system")

    # Generate YAML (read-only view)
    generate_sprint_status_yaml()
```

**Phase 3: Old System Deprecated**
```python
# Database only
def update_story_status(story_id, status):
    story_repo.transition_status(story_id, status, "system")
    # YAML removed or optional
```

---

## Performance Architecture

### Caching Strategy

```python
class MultiLevelCache:
    """3-level caching: Memory → Disk → Source"""

    def __init__(self):
        # L1: Memory cache (LRU, 100 entries, instant)
        self.memory = LRUCache(maxsize=100)

        # L2: Disk cache (10000 entries, fast)
        self.disk = DiskCache(Path(".gaodev/cache"))

        # L3: Source (database, filesystem, slow)
        self.source = None

    def get(self, key: str) -> Optional[Any]:
        # L1: Check memory
        if value := self.memory.get(key):
            return value

        # L2: Check disk
        if value := self.disk.get(key):
            self.memory.set(key, value)
            return value

        # L3: Load from source
        if value := self.source.load(key):
            self.memory.set(key, value)
            self.disk.set(key, value)
            return value

        return None
```

### Query Optimization

```python
# Use indexes for fast queries
CREATE INDEX idx_stories_status ON stories(status);
CREATE INDEX idx_stories_epic ON stories(epic_id);

# Avoid N+1 queries - use joins
def get_stories_with_epic(epic_id: int) -> List[StoryWithEpic]:
    return db.execute("""
        SELECT s.*, e.name as epic_name, e.status as epic_status
        FROM stories s
        JOIN epics e ON s.epic_id = e.id
        WHERE e.id = ?
    """, epic_id)

# Use connection pooling
class DatabaseManager:
    def __init__(self):
        self.pool = ConnectionPool(size=5)

    def get_connection(self):
        return self.pool.acquire()
```

### Lazy Loading

```python
class Story:
    """Story model with lazy loading."""

    def __init__(self, **data):
        self._data = data
        self._epic = None  # Lazy load
        self._dependencies = None  # Lazy load
        self._documents = None  # Lazy load

    @property
    def epic(self) -> Epic:
        if self._epic is None:
            self._epic = epic_repo.get(self._data['epic_id'])
        return self._epic

    @property
    def dependencies(self) -> List[Story]:
        if self._dependencies is None:
            self._dependencies = story_repo.get_dependencies(self.id)
        return self._dependencies
```

---

## Migration Strategy

### Step-by-Step Migration Plan

**Week 1-2: Database Setup**
1. Create SQLite database with schema
2. Create migration scripts
3. Test with sample data
4. Add to .gitignore (.gaodev/)

**Week 3-4: Dual Write Implementation**
1. Implement StoryRepository with CRUD
2. Update StoryLifecycleManager to write to both
3. Add verification (DB matches YAML)
4. Deploy with dual write enabled

**Week 5-8: Feature Development**
1. Implement query operations
2. Add CLI commands for queries
3. Test with real projects
4. Gather feedback

**Week 9-10: Data Migration**
1. Parse existing sprint-status.yaml
2. Populate database with historical data
3. Validate 100% data preserved
4. Create backup

**Week 11-12: Primary Switchover**
1. Make database primary source
2. Generate YAML from database (read-only)
3. Update all code to use database
4. Monitor for issues

**Week 13-14: Deprecation**
1. Mark YAML as deprecated
2. Add warnings when YAML modified
3. Document migration for users
4. Prepare for removal (2 releases later)

### Rollback Plan

```python
# If migration fails, rollback to YAML
def rollback_to_yaml():
    # 1. Disable database writes
    config.set("database.enabled", False)

    # 2. Regenerate YAML from last known good state
    generate_yaml_from_backup()

    # 3. Update all services to use YAML
    story_lifecycle.use_yaml_backend()

    # 4. Log rollback event
    logger.critical("ROLLBACK: Database migration failed, reverted to YAML")

    # 5. Notify team
    send_alert("Database rollback initiated")
```

---

## Security Considerations

### SQL Injection Prevention

```python
# ALWAYS use parameterized queries
# BAD:
query = f"SELECT * FROM stories WHERE id = {story_id}"  # VULNERABLE

# GOOD:
query = "SELECT * FROM stories WHERE id = ?"
result = db.execute(query, story_id)  # SAFE

# For @query: references, only allow SELECT
def validate_query(sql: str) -> bool:
    parsed = sqlparse.parse(sql)[0]
    if parsed.get_type() != "SELECT":
        raise SecurityError("Only SELECT queries allowed")
    return True
```

### File Path Validation

```python
def resolve_document_path(path: str) -> Path:
    """
    Resolve document path with security checks.

    Prevents:
    - Directory traversal: ../../etc/passwd
    - Absolute paths outside project: /etc/passwd
    - Symlink attacks
    """
    # 1. Normalize path
    normalized = Path(path).resolve()

    # 2. Ensure within project root
    if not normalized.is_relative_to(project_root):
        raise SecurityError(f"Path outside project: {path}")

    # 3. Check for symlinks
    if normalized.is_symlink():
        raise SecurityError(f"Symlinks not allowed: {path}")

    return normalized
```

### Audit Trail

```python
# Log all state changes with actor
def update_story_status(story_id: int, status: StoryStatus, changed_by: str):
    old_status = story_repo.get(story_id).status

    # Update database
    story_repo.update(story_id, {"status": status})

    # Create audit log entry
    audit_log.create(
        entity_type="story",
        entity_id=story_id,
        field_name="status",
        old_value=old_status,
        new_value=status,
        changed_by=changed_by,
        changed_at=datetime.now(),
        context={"source": "orchestrator"}
    )
```

---

## Deployment Architecture

### File Structure in Production

```
/opt/gao-dev/
  bin/
    gao-dev          # Main CLI executable
  lib/
    gao_dev/         # Python package
  config/
    domains/         # Built-in domains
    prompts/         # Built-in prompts
    checklists/      # Built-in checklists
  plugins/
    gao-ops/         # Example plugin
    gao-legal/

~/.gaodev/           # User-level data
  config.yaml        # User preferences
  domains/           # User domains
  prompts/           # User prompts
  checklists/        # User checklists
  cache/             # User-level cache

{project}/.gaodev/   # Project-level data
  state.db           # Project database (IMPORTANT: Add to .gitignore)
  config.yaml        # Project configuration
  cache/             # Project-level cache
  domains/           # Project-specific domains
  prompts/           # Project-specific prompts
```

### Environment Variables

```bash
# Database location (override default)
export GAODEV_DATABASE_PATH="/path/to/state.db"

# Cache directory
export GAODEV_CACHE_DIR="/tmp/gaodev-cache"

# Disable caching (for debugging)
export GAODEV_CACHE_ENABLED=false

# Plugin directory
export GAODEV_PLUGIN_DIR="/opt/gao-dev/plugins"
```

---

## Open Questions & Decisions Needed

### Question 1: Database per Project vs Global Database?

**Option A: Database per project** (.gaodev/state.db in each project)
- Pros: Isolation, easier backup, project-specific
- Cons: Harder to query across projects

**Option B: Global database** (~/.gaodev/global.db)
- Pros: Cross-project queries, centralized
- Cons: Larger database, potential conflicts

**Recommendation:** **Option A** (per-project), but support both. Default to .gaodev/state.db, allow override with env var.

### Question 2: Query Language for @query:?

**Option A: Raw SQL**
```yaml
@query:SELECT title FROM stories WHERE status='completed' LIMIT 5
```
- Pros: Powerful, flexible
- Cons: Security risk, complex

**Option B: Named queries**
```yaml
@query:completed_stories
```
- Pros: Safe, simple
- Cons: Less flexible

**Option C: DSL**
```yaml
@query:stories.where(status='completed').limit(5)
```
- Pros: Safe, readable
- Cons: Need to implement parser

**Recommendation:** **Option B + Option A**. Support named queries (safe), allow raw SQL for advanced users (with strict validation).

### Question 3: Markdown YAML Frontmatter or Separate Metadata?

**Option A: YAML frontmatter**
```markdown
---
story_id: 61
status: completed
owner: Amelia
---
# Story 6.1: Git Repository Integration
```
- Pros: Metadata with content
- Cons: Parsing required

**Option B: Separate .meta.yaml file**
```
story-6.1.md
story-6.1.meta.yaml
```
- Pros: Clean separation
- Cons: Two files per document

**Recommendation:** **Option A** (YAML frontmatter). More common pattern, easier to read.

---

## Appendix A: Technology Stack

**Core:**
- Python 3.11+
- SQLite 3.35+ (built-in)
- Jinja2 (templating)
- YAML (configuration)
- JSON Schema (validation)

**Database:**
- SQLAlchemy (ORM, optional)
- Alembic (migrations)

**Testing:**
- pytest
- pytest-cov
- mypy (type checking)

**CLI:**
- Click (command framework)
- Rich (terminal formatting)

**Caching:**
- functools.lru_cache (memory)
- diskcache (disk)

---

## Appendix B: Performance Targets

| Operation | Target | Baseline | Improvement |
|-----------|--------|----------|-------------|
| Document query | <100ms | 5-10s | 50-100x |
| Prompt expansion | <100ms | N/A | New feature |
| Story status update | <50ms | 1-2s | 20-40x |
| Checklist validation | <2min | N/A | New feature |
| Database migration | <5min | N/A | New feature |

---

**End of Architecture Proposal Document**

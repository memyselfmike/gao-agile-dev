# Epic Breakdown
## Document Lifecycle & Context Management System

**Feature:** Document Lifecycle & Context Management
**Total Epics:** 5
**Estimated Duration:** 8-12 weeks
**Priority:** High (Core Infrastructure)

---

## Epic 12: Document Lifecycle Management

**Goal:** Build comprehensive document tracking system that manages document states, relationships, archival, governance, and search capabilities with professional naming standards and templates.

**Owner:** Amelia (Developer) + Bob (Scrum Master for stories)
**Priority:** P0 (Critical - Foundation)
**Estimated Duration:** 3-4 weeks
**Story Points:** 44 points (Enhanced from 28 with research insights)

### Success Criteria
- All documents tracked in SQLite registry with standardized naming
- Document queries return results in <100ms
- Full-text search (FTS5) enables fast document discovery
- State machine enforces valid transitions
- Archival system with retention policies moves obsolete documents automatically
- Document templates reduce creation friction by 80%
- Governance framework ensures document ownership and review cycles
- Health KPIs track document system effectiveness
- Lineage queries show document relationships
- Zero data loss in state transitions
- 5S methodology principles applied throughout

### Stories

#### Story 12.1: Document Registry Database Schema + Naming Standards
**Points:** 5 | **Priority:** P0

**Description:** Create SQLite database schema for document registry with tables for documents, relationships, metadata, AND establish standardized naming convention and YAML frontmatter schema for all documents.

**Acceptance Criteria:**
- [ ] `documents` table with all required fields (id, path, type, state, dates, author, reviewer, owner, review_due_date, metadata)
- [ ] `document_relationships` table for parent-child relationships
- [ ] Indexes on frequently queried columns (type, state, feature, epic, owner, tags)
- [ ] FTS5 virtual table for full-text search (prepared for Story 12.9)
- [ ] Foreign key constraints enforced
- [ ] Schema migration support
- [ ] Naming convention standard: `{DocType}_{subject}_{date}_v{version}.{ext}`
- [ ] YAML frontmatter schema defined with all required/optional fields
- [ ] DocumentNamingConvention utility class for filename generation/parsing
- [ ] Unit tests for schema creation and naming utilities
- [ ] Performance: Create tables <100ms

**Technical Notes:**
- Use SQLite JSON1 extension for metadata storage
- Content hash field for sync conflict detection
- Composite indexes for common query patterns
- Naming pattern: `PRD_user-auth_2024-11-05_v1.0.md`
- Frontmatter includes: title, doc_type, status, owner, reviewer, tags, retention_policy
- Governance fields: created_date, last_updated, review_due_date, related_docs

**Dependencies:** None (foundational)

---

#### Story 12.2: DocumentRegistry Implementation
**Points:** 5 | **Priority:** P0

**Description:** Implement DocumentRegistry class for CRUD operations on documents in SQLite.

**Acceptance Criteria:**
- [ ] `register_document()` creates new document record
- [ ] `get_document()` retrieves by ID or path
- [ ] `update_document()` modifies metadata
- [ ] `delete_document()` removes (soft delete preferred)
- [ ] `query_documents()` with filters (type, state, feature, epic)
- [ ] Thread-safe operations
- [ ] Unit tests: >80% coverage
- [ ] Performance: Queries <50ms

**Technical Notes:**
- Use context managers for database connections
- Parameterized queries to prevent SQL injection
- Return Document dataclass instances

**Dependencies:** Story 12.1

---

#### Story 12.3: Document State Machine
**Points:** 3 | **Priority:** P0

**Description:** Implement state machine for document lifecycle with validation and transition logic.

**Acceptance Criteria:**
- [ ] `DocumentStateMachine` class defined
- [ ] Valid transitions: draft→active, active→obsolete, obsolete→archived
- [ ] `can_transition()` validates state changes
- [ ] `transition()` executes state change with validation
- [ ] Only one active document per type+feature enforced
- [ ] Hooks for custom transition logic
- [ ] Unit tests for all transitions
- [ ] Invalid transitions raise `InvalidStateTransition` exception

**Technical Notes:**
- State transitions atomic (database transaction)
- Audit log for all state changes
- Support for custom validators per document type

**Dependencies:** Story 12.2

---

#### Story 12.4: DocumentLifecycleManager
**Points:** 5 | **Priority:** P0

**Description:** Implement high-level DocumentLifecycleManager that orchestrates document lifecycle operations.

**Acceptance Criteria:**
- [ ] `register_document()` with metadata extraction
- [ ] `transition_state()` with validation
- [ ] `get_current_document()` returns active document
- [ ] `get_document_lineage()` returns ancestors + descendants
- [ ] `archive_document()` moves to archive directory
- [ ] `query_documents()` with multiple filters
- [ ] Integration tests with real documents
- [ ] Performance: Operations <100ms

**Technical Notes:**
- Coordinates DocumentRegistry and StateMachine
- Handles filesystem operations (move to archive)
- Preserves directory structure in archive

**Dependencies:** Story 12.3

---

#### Story 12.5: Document Scanning & Auto-Registration (with 5S Classification)
**Points:** 5 | **Priority:** P1

**Description:** Implement document scanning to automatically discover and register existing documents with 5S methodology classification (Sort: permanent, transient, temp).

**Acceptance Criteria:**
- [ ] `scan_directory()` discovers documents recursively
- [ ] Detects document type from path patterns
- [ ] Extracts metadata from frontmatter/YAML (including governance fields)
- [ ] Validates filenames against naming convention (warn on non-standard)
- [ ] Registers unregistered documents
- [ ] Updates metadata for registered documents
- [ ] 5S Classification: classify as permanent, transient, or temp
- [ ] Respects exclude patterns (.git, node_modules, .archive, .scratch, etc.)
- [ ] Progress reporting for large scans
- [ ] Performance: Scan 1000 docs <10 seconds

**Technical Notes:**
- Use glob patterns for type detection
- Parse markdown frontmatter for metadata
- Batch insert for performance
- 5S Sort: PRD/Architecture=permanent, QA reports=transient, drafts=temp
- Flag documents missing frontmatter or non-standard names

**Dependencies:** Story 12.4

---

#### Story 12.6: Archival System with Retention Policies
**Points:** 6 | **Priority:** P1 (Enhanced: +1 pt for retention framework)

**Description:** Implement automatic archival system that moves obsolete documents based on configurable rules with comprehensive retention policies for compliance (archive vs delete, retention periods).

**Acceptance Criteria:**
- [ ] Archival rules defined in YAML config
- [ ] Retention policy framework: archive_to_obsolete, obsolete_to_archive, archive_retention, delete_after_archive
- [ ] Rules support: document type, state, age in days, compliance tags
- [ ] `archive_obsolete_documents()` applies rules
- [ ] Moves files to `.archive/` with preserved structure (5S: Shine)
- [ ] Metadata preserved in database with archive timestamp
- [ ] Retention period enforcement (e.g., PRD: 2 years, QA: 5 years, postmortem: forever)
- [ ] Archive vs Delete distinction based on compliance requirements
- [ ] Dry-run mode for testing
- [ ] CLI commands: `gao-dev lifecycle archive`, `gao-dev lifecycle cleanup`
- [ ] Retention policy report: shows what will be archived/deleted
- [ ] Unit tests for rule evaluation and retention policies

**Technical Notes:**
- Configurable per document type with compliance tags
- Archive directory outside docs/ (.archive/)
- Support manual archival override
- Never delete documents tagged with compliance flags unless retention expired
- Example: postmortems never obsolete, QA reports retained 5 years for audits

**Dependencies:** Story 12.4

---

#### Story 12.7: Document Governance Framework
**Points:** 3 | **Priority:** P1

**Description:** Implement document governance framework with ownership, review cycles, and RACI matrix for document management (Research Insight: prevent document rot).

**Acceptance Criteria:**
- [ ] Governance configuration YAML with RACI matrix per document type
- [ ] Document ownership assignment (owner, reviewer, approver)
- [ ] Review cadence configuration per document type (e.g., PRD: 90 days, Architecture: 60 days)
- [ ] `check_review_due()` identifies documents needing review
- [ ] Auto-assignment of review due dates on document creation
- [ ] Governance rules: who can create, approve, archive each document type
- [ ] CLI command: `gao-dev lifecycle review-due`
- [ ] Email/notification support (optional, for future)
- [ ] Unit tests for governance rules

**Technical Notes:**
- RACI: Responsible (creator), Accountable (owner), Consulted (reviewer), Informed (stakeholders)
- John owns PRDs, Winston owns Architecture, Bob owns Stories
- Review cadence prevents stale documents (5S: Sustain)
- Integrates with document metadata (owner, reviewer, review_due_date)

**Dependencies:** Story 12.2

---

#### Story 12.8: Document Templates System
**Points:** 3 | **Priority:** P0

**Description:** Create document template system that generates documents from templates with proper frontmatter, naming convention, and governance metadata (Research Insight: reduce friction, ensure consistency).

**Acceptance Criteria:**
- [ ] `DocumentTemplateManager` class for template management
- [ ] `create_from_template()` generates document from template with variables
- [ ] Auto-generates filename using naming convention
- [ ] Auto-populates YAML frontmatter with governance fields
- [ ] Auto-registers document in lifecycle system
- [ ] Templates created: PRD, Architecture, Epic, Story, ADR, Postmortem, Runbook
- [ ] Template variables: subject, author, feature, epic, related_docs
- [ ] CLI command: `gao-dev lifecycle create <template> --subject "..." --author "..."`
- [ ] Unit tests for template rendering and document creation

**Technical Notes:**
- Templates in `gao_dev/config/templates/`
- Use Jinja2 for variable substitution
- Templates include @doc: references for context injection (prepares for Epic 13)
- Example: `gao-dev lifecycle create prd --subject "user-auth" --author "John"`
- Generated: `PRD_user-auth_2024-11-05_v1.0.md` with full frontmatter

**Dependencies:** Story 12.1, 12.2

---

#### Story 12.9: Full-Text Search (SQLite FTS5)
**Points:** 5 | **Priority:** P1

**Description:** Implement full-text search using SQLite FTS5 for fast document discovery and semantic search foundation (Research Insight: dramatically improves discovery, positions for Phase 3 vector search).

**Acceptance Criteria:**
- [ ] FTS5 virtual table `documents_fts` for full-text search
- [ ] Triggers to keep FTS in sync with documents table
- [ ] `DocumentSearch` class with search methods
- [ ] `search(query)` - full-text search across title, content, tags
- [ ] `search_by_tags(tags)` - tag-based search
- [ ] `get_related_documents(doc_id)` - find similar documents
- [ ] Query syntax: "authentication security", "api design"
- [ ] Filter by doc_type, state, feature, epic
- [ ] Result ranking by relevance
- [ ] CLI command: `gao-dev lifecycle search "query"`
- [ ] Performance: Search <200ms for 10,000 documents
- [ ] Unit tests with sample documents

**Technical Notes:**
- FTS5 MATCH syntax for queries
- Index title, content, tags, metadata fields
- Prepare for Phase 3 semantic search (vector embeddings)
- Can migrate to hybrid search (lexical + semantic) later
- Return Document objects with relevance score

**Dependencies:** Story 12.1, 12.2

---

#### Story 12.10: Document Health KPIs and Monitoring
**Points:** 3 | **Priority:** P2

**Description:** Implement KPI tracking and health monitoring for document lifecycle system (Research Insight: measure effectiveness, enable continuous improvement).

**Acceptance Criteria:**
- [ ] `DocumentHealthMetrics` class for metrics collection
- [ ] KPIs tracked: total docs, stale docs, docs needing review, orphaned docs
- [ ] KPIs tracked: avg document age, most/least accessed docs
- [ ] KPIs tracked: cache hit rate, avg query time, context injection rate
- [ ] `collect_metrics()` returns comprehensive metrics dict
- [ ] `generate_health_report()` produces markdown health report
- [ ] CLI commands: `gao-dev lifecycle health`, `gao-dev lifecycle health --json`
- [ ] Integration with logging for metric tracking
- [ ] Unit tests for metric calculation

**Technical Notes:**
- Metrics stored in existing metrics database
- Track document access patterns for "least accessed" detection
- Stale document: not updated in >review_cadence days
- Orphaned document: no relationships to other documents
- 5S: Sustain - KPIs ensure practices continue

**Dependencies:** Story 12.2, 12.7

---

### Epic Dependencies
- **Requires:** Epic 10 (Prompt Abstraction) - COMPLETE
- **Blocks:** Epic 13 (Meta-Prompts), Epic 15 (Context Layer)

---

## Epic 12: Meta-Prompt System & Context Injection

**Goal:** Extend prompt system with automatic context injection using @doc:, @checklist:, @query:, @context: references.

**Owner:** Amelia (Developer)
**Priority:** P0 (Critical - Core Functionality)
**Estimated Duration:** 2 weeks
**Story Points:** 26 points

### Success Criteria
- All reference types (@doc, @checklist, @query, @context) working
- Reference resolution time <50ms per reference
- Section extraction from markdown works correctly
- Automatic context injection reduces manual context by 90%
- Works across all GAO domains (dev, ops, legal, research)
- 100% backwards compatible with Epic 10

### Stories

#### Story 12.1: Reference Resolver Framework
**Points:** 5 | **Priority:** P0

**Description:** Create extensible framework for resolving different reference types in prompts.

**Acceptance Criteria:**
- [ ] `ReferenceResolver` base class defined
- [ ] Plugin architecture for adding new resolvers
- [ ] `parse_reference()` extracts type and value
- [ ] `resolve_reference()` dispatches to correct resolver
- [ ] Error handling for missing/invalid references
- [ ] Cache resolved references for performance
- [ ] Unit tests for framework
- [ ] Performance: Parse <1ms, resolve <50ms

**Technical Notes:**
- Strategy pattern for resolvers
- Each resolver implements resolve() method
- Support for nested references (reference in referenced file)

**Dependencies:** Epic 12 (Story 12.4)

---

#### Story 12.2: Document Reference Resolver (@doc:)
**Points:** 5 | **Priority:** P0

**Description:** Implement @doc: reference resolver for injecting document content.

**Acceptance Criteria:**
- [ ] `@doc:path/to/file.md` loads full document
- [ ] `@doc:path/to/file.md#section` extracts markdown section
- [ ] `@doc:path/to/file.md@yaml_key` extracts YAML field
- [ ] `@doc:glob:pattern/*.md` loads multiple documents
- [ ] Section extraction preserves formatting
- [ ] YAML field extraction handles nested keys
- [ ] Unit tests for all syntaxes
- [ ] Performance: Resolution <50ms

**Technical Notes:**
- Use DocumentLifecycleManager to load documents
- Markdown section extraction by heading hierarchy
- YAML parsing for field extraction
- Glob pattern expansion with max limit (100 files)

**Dependencies:** Story 12.1

---

#### Story 12.3: Query Reference Resolver (@query:)
**Points:** 4 | **Priority:** P1

**Description:** Implement @query: reference resolver for injecting database query results.

**Acceptance Criteria:**
- [ ] SQL-like query syntax: `@query:stories.where(epic=3, status='done')`
- [ ] Format options: markdown, json, csv
- [ ] Query result size limit (max 1000 chars)
- [ ] Query validation before execution
- [ ] Performance: Query <100ms
- [ ] Unit tests with mock database
- [ ] Error handling for invalid queries

**Technical Notes:**
- Query builder translates DSL to SQL
- Result formatting as markdown table
- Whitelist allowed tables and columns
- Prevent SQL injection

**Dependencies:** Story 12.1, Epic 14 (State Database)

---

#### Story 12.4: Context Reference Resolver (@context:)
**Points:** 3 | **Priority:** P1

**Description:** Implement @context: reference resolver for injecting cached context.

**Acceptance Criteria:**
- [ ] `@context:key` loads from ContextCache
- [ ] Fallback to DocumentLifecycleManager if not cached
- [ ] Common context keys: epic_definition, architecture, coding_standards
- [ ] Context tracking (what was used where)
- [ ] Unit tests with mock cache
- [ ] Performance: Cache hit <1ms, miss <100ms

**Technical Notes:**
- Integrates with ContextCache (Epic 15)
- Lazy loading if not in cache
- Track context usage for audit

**Dependencies:** Story 12.1, Epic 15 (Context Cache)

---

#### Story 12.5: MetaPromptEngine Implementation
**Points:** 5 | **Priority:** P0

**Description:** Implement MetaPromptEngine that extends PromptLoader with meta-prompt capabilities.

**Acceptance Criteria:**
- [ ] Extends Epic 10's PromptLoader
- [ ] `render_with_meta_prompts()` resolves all references
- [ ] Automatic context injection based on workflow
- [ ] Configuration for per-workflow auto-injection
- [ ] Support for nested references (up to 3 levels)
- [ ] Cycle detection prevents infinite loops
- [ ] Integration tests with real prompts
- [ ] Performance: Render <200ms for typical prompt

**Technical Notes:**
- Compose with PromptLoader (don't inherit)
- Reference resolution before template rendering
- Auto-injection config in YAML

**Dependencies:** Story 12.2, 12.3, 12.4

---

#### Story 12.6: Update Core Prompts to Use Meta-Prompts
**Points:** 4 | **Priority:** P1

**Description:** Update 10 core prompt templates to use meta-prompt references instead of hardcoded context.

**Acceptance Criteria:**
- [ ] `create_story.yaml` uses @doc: for epic context
- [ ] `implement_story.yaml` uses @doc: for story + architecture
- [ ] `validate_story.yaml` uses @checklist: references
- [ ] `create_prd.yaml` simplified with references
- [ ] `create_architecture.yaml` simplified with references
- [ ] All updated prompts tested with workflows
- [ ] Backwards compatibility maintained
- [ ] Documentation updated

**Technical Notes:**
- Gradual migration, not big bang
- Test each prompt individually
- Keep old prompts as fallback initially

**Dependencies:** Story 12.5

---

### Epic Dependencies
- **Requires:** Epic 12 (Document Lifecycle)
- **Blocks:** None (improves existing system)

---

## Epic 13: Checklist Plugin System

**Goal:** Create YAML-based checklist system that's reusable, plugin-extensible, and domain-agnostic.

**Owner:** Amelia (Developer)
**Priority:** P1 (High - Quality Gates)
**Estimated Duration:** 1-2 weeks
**Story Points:** 21 points

### Success Criteria
- 20+ checklists defined in YAML
- ChecklistLoader loads and validates checklists
- Checklist inheritance (extends) works correctly
- Plugin checklists discovered and loaded
- Checklist execution tracked in database
- Compliance reports generated

### Stories

#### Story 13.1: Checklist YAML Schema
**Points:** 3 | **Priority:** P0

**Description:** Define JSON schema for checklist YAML format with validation.

**Acceptance Criteria:**
- [ ] JSON schema for checklist format
- [ ] Required fields: name, category, version, items
- [ ] Optional fields: extends, description, metadata
- [ ] Item fields: id, text, severity, category, help_text
- [ ] Schema validation with jsonschema
- [ ] Example checklists as reference
- [ ] Documentation for checklist authors

**Technical Notes:**
- Similar format to prompt templates (Epic 10)
- Support for checklist inheritance
- Severity levels: high, medium, low

**Dependencies:** None (foundational)

---

#### Story 13.2: ChecklistLoader Implementation
**Points:** 5 | **Priority:** P0

**Description:** Implement ChecklistLoader that loads, validates, and resolves checklist inheritance.

**Acceptance Criteria:**
- [ ] `load_checklist()` loads from YAML file
- [ ] Validates against JSON schema
- [ ] Resolves `extends` inheritance
- [ ] Caches loaded checklists
- [ ] `render_checklist()` outputs markdown
- [ ] `list_checklists()` discovers available checklists
- [ ] Unit tests: >80% coverage
- [ ] Performance: Load <10ms (cached)

**Technical Notes:**
- Recursive inheritance resolution
- Override child items if same ID
- Plugin checklists override core checklists

**Dependencies:** Story 13.1

---

#### Story 13.3: Core Checklist Library
**Points:** 5 | **Priority:** P0

**Description:** Create 20+ core checklists for testing, quality, security, deployment, operations.

**Acceptance Criteria:**
- [ ] Testing: unit-test-standards, integration-test-standards, e2e-test-standards
- [ ] Code Quality: solid-principles, clean-code, python-standards
- [ ] Security: owasp-top-10, secure-coding
- [ ] Deployment: production-readiness, rollout-checklist
- [ ] Operations: incident-response, change-management
- [ ] All checklists validated against schema
- [ ] Documentation for each checklist
- [ ] Integration test loads all checklists

**Technical Notes:**
- Convert existing qa-comprehensive.md to YAML
- Create category structure
- Each checklist focused and reusable

**Dependencies:** Story 13.2

---

#### Story 13.4: Checklist Execution Tracking
**Points:** 5 | **Priority:** P1

**Description:** Track checklist executions in database with pass/fail results per item.

**Acceptance Criteria:**
- [ ] `checklist_executions` table in database
- [ ] `checklist_results` table for item results
- [ ] `track_execution()` records execution
- [ ] Query interface: get executions by artifact
- [ ] Status values: pass, fail, skip, na
- [ ] Overall status calculation
- [ ] Unit tests for tracking
- [ ] Performance: Track execution <50ms

**Technical Notes:**
- Link executions to stories/artifacts
- Store who executed and when
- Support partial completion (some items skipped)

**Dependencies:** Story 13.2, Epic 14 (State Database)

---

#### Story 13.5: Checklist Plugin Support
**Points:** 3 | **Priority:** P1

**Description:** Extend plugin system to support custom checklist loading from plugins.

**Acceptance Criteria:**
- [ ] `ChecklistPlugin` base class
- [ ] `get_checklists()` method for plugin checklists
- [ ] Plugin checklists discovered on startup
- [ ] Plugin checklists override core if same name
- [ ] Example plugin with custom checklist
- [ ] Documentation for plugin developers
- [ ] Integration test with plugin checklist

**Technical Notes:**
- Similar to prompt plugin system (Epic 10)
- Plugin checklists in plugin directory
- Validation same as core checklists

**Dependencies:** Story 13.2

---

### Epic Dependencies
- **Requires:** Epic 12 (Document Lifecycle)
- **Integrates With:** Epic 12 (Meta-Prompts for @checklist: references)

---

## Epic 14: State Tracking Database (SQLite)

**Goal:** Unify story, epic, sprint state tracking in queryable SQLite database with markdown sync.

**Owner:** Amelia (Developer)
**Priority:** P0 (Critical - Core Infrastructure)
**Estimated Duration:** 2-3 weeks
**Story Points:** 29 points

### Success Criteria
- All story/epic status in SQLite
- Markdown-SQLite bidirectional sync working
- Query performance <50ms
- Sprint tracking and velocity calculations
- 100% backwards compatibility with existing workflows
- Zero data loss during migration

### Stories

#### Story 14.1: State Database Schema
**Points:** 5 | **Priority:** P0

**Description:** Create SQLite schema for epics, stories, sprints, and workflow executions.

**Acceptance Criteria:**
- [ ] `epics` table with all metadata
- [ ] `stories` table with status, points, dates
- [ ] `sprints` table with sprint information
- [ ] `story_assignments` table (many-to-many)
- [ ] `workflow_executions` table
- [ ] Indexes on frequently queried columns
- [ ] Foreign key constraints enforced
- [ ] Unit tests for schema creation
- [ ] Performance: Create tables <100ms

**Technical Notes:**
- content_hash field for sync conflict detection
- JSON metadata field for extensibility
- Triggers for auto-updating timestamps

**Dependencies:** None (foundational)

---

#### Story 14.2: StateTracker Implementation
**Points:** 6 | **Priority:** P0

**Description:** Implement StateTracker class with CRUD operations for stories, epics, sprints.

**Acceptance Criteria:**
- [ ] Story operations: create, get, update, delete, query
- [ ] Epic operations: create, get, update, get_progress
- [ ] Sprint operations: create, get, assign_story, get_velocity
- [ ] Workflow execution tracking
- [ ] Thread-safe operations
- [ ] Unit tests: >80% coverage
- [ ] Performance: Queries <50ms

**Technical Notes:**
- Return dataclass instances (Story, Epic, Sprint)
- Prepared statements for performance
- Connection pooling if needed

**Dependencies:** Story 14.1

---

#### Story 14.3: Markdown-SQLite Syncer
**Points:** 6 | **Priority:** P0

**Description:** Implement bidirectional sync between markdown story files and SQLite database.

**Acceptance Criteria:**
- [ ] `sync_from_markdown()` parses markdown and updates database
- [ ] `sync_to_markdown()` writes database state to markdown
- [ ] Frontmatter parsing for metadata
- [ ] Content hash for conflict detection
- [ ] Conflict resolution strategy (configurable)
- [ ] Batch sync for performance
- [ ] Unit tests with example story files
- [ ] Performance: Sync 100 files <10 seconds

**Technical Notes:**
- Regex parsing for frontmatter
- Database is source of truth for status
- Markdown is source of truth for content
- Hash-based change detection

**Dependencies:** Story 14.2

---

#### Story 14.4: Query Builder & API
**Points:** 4 | **Priority:** P1

**Description:** Implement query builder for complex state queries with intuitive API.

**Acceptance Criteria:**
- [ ] `get_stories_by_status()` with filtering
- [ ] `get_epic_progress()` with percentage calculation
- [ ] `get_sprint_velocity()` with points sum
- [ ] `get_blocked_stories()` convenience method
- [ ] Query performance optimized (<50ms)
- [ ] Result pagination support
- [ ] Unit tests for all queries
- [ ] Documentation with examples

**Technical Notes:**
- Use indexes for all queries
- EXPLAIN QUERY PLAN for optimization
- Return typed results (not raw SQL rows)

**Dependencies:** Story 14.2

---

#### Story 14.5: Import Existing Data
**Points:** 5 | **Priority:** P0

**Description:** Import existing sprint-status.yaml and story markdown files into database.

**Acceptance Criteria:**
- [ ] Import sprint-status.yaml structure
- [ ] Import all story files from docs/stories/
- [ ] Import bmm-workflow-status.md
- [ ] Validation of imported data
- [ ] Migration script with dry-run mode
- [ ] CLI command: `gao-dev state import`
- [ ] Rollback capability
- [ ] Migration documentation

**Technical Notes:**
- One-time migration
- Preserve all existing data
- Backup before migration
- Idempotent (can run multiple times)

**Dependencies:** Story 14.3

---

#### Story 14.6: CLI Commands for State Management
**Points:** 3 | **Priority:** P1

**Description:** Create CLI commands for querying and managing state.

**Acceptance Criteria:**
- [ ] `gao-dev state story <epic> <story>` - Show story details
- [ ] `gao-dev state epic <epic>` - Show epic progress
- [ ] `gao-dev state sprint` - Show current sprint
- [ ] `gao-dev state sync` - Manual sync trigger
- [ ] `gao-dev state query "<query>"` - Custom queries
- [ ] Rich output formatting (tables, colors)
- [ ] Unit tests for CLI commands

**Technical Notes:**
- Use Click for CLI
- Rich library for formatting
- Support JSON output for scripting

**Dependencies:** Story 14.4

---

### Epic Dependencies
- **Requires:** Epic 12 (Document Lifecycle for document models)
- **Blocks:** Epic 12 (@query: references), Epic 15 (Context persistence)

---

## Epic 15: Context Persistence Layer

**Goal:** Build context caching and persistence system to reduce document reads and improve performance.

**Owner:** Amelia (Developer)
**Priority:** P1 (High - Performance)
**Estimated Duration:** 1-2 weeks
**Story Points:** 20 points

### Success Criteria
- Context cache reduces document reads by 80%+
- Workflow context persists across executions
- Context API simplifies agent prompts
- Context lineage tracking works
- Stale context detected automatically
- Performance overhead <5%

### Stories

#### Story 15.1: ContextCache Implementation
**Points:** 4 | **Priority:** P0

**Description:** Implement in-memory cache for frequently accessed documents with TTL and LRU eviction.

**Acceptance Criteria:**
- [ ] TTL-based expiration (default: 5 minutes)
- [ ] LRU eviction when cache full (max 100 entries)
- [ ] Thread-safe access with locks
- [ ] `get()`, `set()`, `invalidate()`, `clear()` methods
- [ ] Cache hit/miss metrics
- [ ] Unit tests: >80% coverage
- [ ] Performance: Get <1ms, set <1ms

**Technical Notes:**
- Use OrderedDict for LRU
- Threading.Lock for thread safety
- Configurable TTL per key

**Dependencies:** None (foundational)

---

#### Story 15.2: WorkflowContext Data Model
**Points:** 3 | **Priority:** P0

**Description:** Create WorkflowContext dataclass that holds context for workflow execution.

**Acceptance Criteria:**
- [ ] Fields: workflow_id, epic_num, story_num, feature
- [ ] Lazy-loaded document properties (prd, architecture, epic_definition, story)
- [ ] State fields: current_phase, decisions, artifacts
- [ ] Metadata: created_at, updated_at
- [ ] Serialization to JSON
- [ ] Deserialization from JSON
- [ ] Unit tests for all operations
- [ ] Immutable (copy-on-write)

**Technical Notes:**
- Use dataclass with property decorators
- Lazy loading loads from DocumentLifecycleManager
- Immutability prevents accidental mutations

**Dependencies:** Epic 12 (Document Lifecycle)

---

#### Story 15.3: Context Persistence to Database
**Points:** 5 | **Priority:** P1

**Description:** Implement ContextPersistence that saves/loads WorkflowContext to SQLite.

**Acceptance Criteria:**
- [ ] `context` table in database
- [ ] `save_context()` serializes and saves
- [ ] `load_context()` deserializes and loads
- [ ] JSON serialization for complex fields
- [ ] Context versioning support
- [ ] Query by workflow_id, epic, story
- [ ] Unit tests with mock database
- [ ] Performance: Save/load <50ms

**Technical Notes:**
- Store in separate database or state database
- JSON field for serialized context
- Index on workflow_id for fast lookups

**Dependencies:** Story 15.2, Epic 14 (State Database)

---

#### Story 15.4: Context Lineage Tracking
**Points:** 5 | **Priority:** P1

**Description:** Track which context (document versions) was used for which artifacts.

**Acceptance Criteria:**
- [ ] `context_usage` table in database
- [ ] Link artifacts to document versions (hash)
- [ ] `track_context_usage()` records usage
- [ ] `get_context_lineage()` queries lineage
- [ ] Detect stale context usage
- [ ] Query: "What architecture was used for Story 3.1?"
- [ ] Unit tests for tracking
- [ ] Performance: Track <50ms

**Technical Notes:**
- Store document hash at time of use
- Link to workflow_executions
- Enable compliance auditing

**Dependencies:** Story 15.3, Epic 12 (Document Lifecycle)

---

#### Story 15.5: Context API for Agents
**Points:** 3 | **Priority:** P1

**Description:** Create simple API for agents to access context without manual document loading.

**Acceptance Criteria:**
- [ ] `get_workflow_context()` returns current context
- [ ] Lazy-loading properties: get_epic_definition(), get_architecture(), etc.
- [ ] Automatic cache usage (transparent to caller)
- [ ] Fallback to document loading if not cached
- [ ] Usage tracking integrated
- [ ] Integration tests with real workflows
- [ ] Documentation with examples

**Technical Notes:**
- Context stored in thread-local or passed explicitly
- Integrates with ContextCache
- Simple API: context.get_epic_definition()

**Dependencies:** Story 15.1, 15.2

---

### Epic Dependencies
- **Requires:** Epic 12 (Document Lifecycle), Epic 14 (State Database)
- **Enhances:** Epic 12 (Meta-Prompts use context cache)

---

## Epic Sequencing & Dependencies

### Critical Path

```
Epic 12 (Document Lifecycle) → 2-3 weeks
    ↓
Epic 12 (Meta-Prompts) → 2 weeks
    ↓
Epic 14 (State Database) → 2-3 weeks
    ↓
Epic 15 (Context Persistence) → 1-2 weeks
```

### Parallel Work

```
Epic 12 (weeks 1-3)
    └─ Epic 13 (Checklists) can start after Epic 12 complete (weeks 4-5)

Epic 12 (weeks 4-5) ║ Epic 13 (weeks 4-5)
    ↓                    ↓
Epic 14 (weeks 6-8) ← needs both complete
    ↓
Epic 15 (weeks 9-10)
```

### Recommended Sprint Breakdown (UPDATED with Enhancements)

**Sprint 1 (Weeks 1-2): Foundation + Standards**
- Epic 12: Stories 12.1 (Enhanced), 12.2, 12.3, 12.4 (18 points)
- Epic 12: Story 12.8 - Document Templates (3 points)
- **Total: 21 points**
- Goal: Document lifecycle foundation with naming standards and templates

**Sprint 2 (Weeks 3-4): Scanning, Archival, Governance**
- Epic 12: Story 12.5 - Scanning with 5S (5 points)
- Epic 12: Story 12.6 - Archival + Retention (6 points)
- Epic 12: Story 12.7 - Governance Framework (3 points)
- Epic 12: Story 12.9 - Full-Text Search (5 points)
- **Total: 19 points**
- Goal: Complete document lifecycle with search and governance

**Sprint 3 (Weeks 5): Polish + Start Meta-Prompts**
- Epic 12: Story 12.10 - Health KPIs (3 points)
- Epic 13 (Meta-Prompts): Stories 13.1, 13.2 (10 points)
- **Total: 13 points**
- Goal: Epic 12 complete, meta-prompts started

**Sprint 4 (Weeks 6-7): Complete Meta-Prompts + Checklists**
- Epic 13: Stories 13.3, 13.4, 13.5, 13.6 (16 points)
- Epic 14 (Checklists): Stories 14.1, 14.2 (8 points)
- **Total: 24 points**
- Goal: Meta-prompts complete, checklist foundation

**Sprint 5 (Weeks 8-9): Complete Checklists + State Database**
- Epic 14: Stories 14.3, 14.4, 14.5 (13 points)
- Epic 15 (State): Stories 15.1, 15.2 (11 points)
- **Total: 24 points**
- Goal: Checklists complete, state database started

**Sprint 6 (Weeks 10-11): Complete State + Context Layer**
- Epic 15: Stories 15.3, 15.4, 15.5, 15.6 (18 points)
- Epic 16 (Context): Stories 16.1, 16.2 (7 points)
- **Total: 25 points**
- Goal: State database complete, context layer started

**Sprint 7 (Weeks 12-13): Complete Context Layer + Integration**
- Epic 16: Stories 16.3, 16.4, 16.5 (13 points)
- Integration testing and bug fixes
- **Total: 13+ points**
- Goal: All epics complete, system integrated

---

## Total Effort Summary (UPDATED with Research Enhancements)

| Epic | Story Points | Duration | Priority | Notes |
|------|--------------|----------|----------|-------|
| Epic 12: Document Lifecycle | **44** | 3-4 weeks | P0 | **+16 pts** from research insights |
| Epic 13: Meta-Prompts | 26 | 2 weeks | P0 | |
| Epic 14: Checklists | 21 | 1-2 weeks | P1 | |
| Epic 15: State Database | 29 | 2-3 weeks | P0 | |
| Epic 16: Context Persistence | 20 | 1-2 weeks | P1 | |
| **TOTAL** | **140 points** | **9-13 weeks** | - | Was 124 pts, 8-12 weeks |

### What Was Added (Research Team Insights)
- ✅ Naming Convention Standard (integrated into 12.1)
- ✅ YAML Frontmatter Schema (integrated into 12.1)
- ✅ Retention Policy Framework (+1 pt to 12.6)
- ✅ Document Governance Framework (Story 12.7: 3 pts)
- ✅ Document Templates System (Story 12.8: 3 pts)
- ✅ Full-Text Search FTS5 (Story 12.9: 5 pts)
- ✅ Document Health KPIs (Story 12.10: 3 pts)
- ✅ 5S Methodology (integrated throughout, 0 pts)

### Team Velocity Assumptions
- 1 developer full-time: ~20 points/week
- 2 developers full-time: ~35 points/week
- With testing/refactoring overhead: ~15-20 points/week/developer
- **Recommended:** 2 developers for optimal velocity (Amelia + rotating support)

### Risk Buffer
- Add 20% buffer for unknowns: 11-16 weeks
- Add 30% buffer for integration issues: 12-17 weeks
- **Conservative estimate:** 12-14 weeks (3-3.5 months)

---

## Implementation Order (UPDATED)

### Phase 1: Foundation with Excellence Standards (Epic 12 Enhanced)
**Duration:** 4-5 weeks (was 2-3 weeks)
**Deliverable:** Complete document lifecycle with governance, search, and templates

**Reason:** Epic 12 now includes research insights for production-grade system:
- Document tracking with standardized naming and frontmatter (12.1)
- Full lifecycle management (12.2-12.4)
- 5S-based scanning and retention policies (12.5-12.6)
- Governance framework prevents document rot (12.7)
- Templates reduce friction (12.8)
- FTS5 search enables discovery (12.9)
- KPIs measure effectiveness (12.10)

### Phase 2: Context Injection (Epics 13, 14)
**Duration:** 3-4 weeks
**Deliverable:** Meta-prompts + checklists

**Reason:** Build on solid document foundation:
- Meta-prompt engine with @doc:, @checklist:, @query: references (Epic 13)
- YAML-based reusable checklists (Epic 14)

### Phase 3: State & Context (Epics 15, 16)
**Duration:** 3-4 weeks
**Deliverable:** Queryable state + context persistence

**Reason:** Complete the integrated system:
- SQLite state tracking with markdown sync (Epic 15)
- Context caching and persistence (Epic 16)

### Phase 4: Integration & Polish
**Duration:** 1-2 weeks
**Deliverable:** Integration testing, bug fixes, performance tuning, documentation

**Reason:** Final polish before production use:
- End-to-end testing across all components
- Performance optimization based on benchmarks
- Documentation and migration guides
- Backwards compatibility verification

---

## Success Metrics (UPDATED with Research Enhancements)

### Phase 1 Success (Enhanced Document Lifecycle)
- [ ] All documents tracked in registry with standardized naming
- [ ] 100% of documents follow naming convention: `{DocType}_{subject}_{date}_v{version}.{ext}`
- [ ] YAML frontmatter present in 100% of new documents
- [ ] Full-text search returns results in <200ms for 10K documents
- [ ] Document templates reduce creation time by 80% (measured)
- [ ] Governance framework: 100% of documents have owner and review_due_date
- [ ] Retention policies prevent accumulation of stale documents
- [ ] 5S principles applied: no orphaned/temp files in production docs
- [ ] Health KPIs dashboard shows system effectiveness
- [ ] Zero breaking changes to existing workflows

### Phase 2 Success (Context Injection)
- [ ] @doc:, @checklist:, @query:, @context: references working in 10+ prompts
- [ ] Context injection reduces manual context by 90%
- [ ] 20+ checklists available in YAML format
- [ ] Agent prompt size reduced by 50%

### Phase 3 Success (State & Context)
- [ ] Story/epic status queryable in <50ms
- [ ] Markdown-SQLite bidirectional sync working with zero data loss
- [ ] Context cache hit rate >80%
- [ ] Document reads reduced by 80%

### Full System Success (After Phase 4)
- [ ] Works across dev, ops, legal, research domains
- [ ] Plugin developers can extend all systems
- [ ] Professional documentation appearance (naming, frontmatter, templates)
- [ ] Document discovery improved 10x (measured by time to find)
- [ ] Compliance-ready with retention policies and audit trails
- [ ] Zero stale documents (>review_cadence days without review)

### Performance Targets
- [ ] System overhead <5%
- [ ] Document queries <100ms
- [ ] Full-text search <200ms
- [ ] Reference resolution <50ms per reference
- [ ] Context cache hit <1ms
- [ ] State queries <50ms
- [ ] Template generation <1 second

---

## Risks & Mitigations

### Risk 1: Markdown-SQLite Sync Conflicts
**Likelihood:** Medium | **Impact:** High
**Mitigation:**
- Implement robust conflict detection (hash-based)
- Clear conflict resolution rules (database wins for status)
- Extensive testing with concurrent edits
- Manual conflict resolution UI if needed

### Risk 2: Performance Degradation
**Likelihood:** Medium | **Impact:** Medium
**Mitigation:**
- Benchmark early and often
- Aggressive caching at all layers
- Index all foreign keys
- Profile before/after changes

### Risk 3: Complexity Creep
**Likelihood:** High | **Impact:** Medium
**Mitigation:**
- Strict adherence to MVP scope
- Regular architecture reviews
- Refactor aggressively
- "Do less, better"

### Risk 4: Breaking Changes to Existing Workflows
**Likelihood:** Low | **Impact:** Critical
**Mitigation:**
- Comprehensive backwards compatibility tests
- Gradual rollout of new features
- Deprecation warnings before removal
- Feature flags for new functionality

### Risk 5: Plugin Ecosystem Breaking Changes
**Likelihood:** Medium | **Impact:** Medium
**Mitigation:**
- Versioned plugin APIs
- Migration guides with each release
- Test suite for plugin developers
- Stable API guarantee

---

## Epic 17: Context System Integration

**Goal:** Integrate Epic 16 Context Persistence Layer into the GAO-Dev ecosystem, making it functional and usable by agents, workflows, and users.

**Owner:** Amelia (Developer) + Bob (Scrum Master)
**Priority:** P0 (Critical - Makes Epic 16 Functional)
**Estimated Duration:** 2-3 weeks
**Story Points:** 34 points

### Success Criteria
- Documents load correctly from DocumentLifecycleManager (Epic 12)
- All context tables in single unified database with Epic 15
- Workflows automatically create and persist WorkflowContext
- Agents can access context via AgentContextAPI
- Users can query/manage context via CLI
- End-to-end tests verify full integration
- Migration system handles schema upgrades
- Performance validated (<50ms operations)
- Documentation updated with working examples

### Stories

#### Story 17.1: Document Loading Integration (Epic 12)
**Points:** 5 | **Priority:** P0

**Description:** Implement actual document loading via DocumentLifecycleManager to make WorkflowContext functional.

**Acceptance Criteria:**
- [ ] `context.get_prd()` returns actual PRD content from DocumentLifecycleManager
- [ ] `context.get_architecture()` returns actual architecture document
- [ ] `context.get_epic_definition()` returns actual epic definition
- [ ] `context.get_story_definition()` returns actual story content
- [ ] Document not found returns None gracefully (no errors)
- [ ] Integration tests with DocumentLifecycleManager pass
- [ ] AgentContextAPI default loader uses DocumentLifecycleManager
- [ ] Examples in documentation work with real documents

**Technical Notes:**
- Replace stub `_load_document()` in WorkflowContext
- Map doc_type to DocumentType enum from Epic 12
- Use feature/epic/story to construct document paths
- Cache loaded documents in WorkflowContext._document_cache

**Dependencies:** Epic 12 (DocumentLifecycleManager)

---

#### Story 17.2: Database Unification (Epic 15)
**Points:** 5 | **Priority:** P0

**Description:** Unify all context tables into single database with Epic 15 StateTracker to fix database fragmentation.

**Acceptance Criteria:**
- [ ] Single `gao_dev.db` contains all tables (state, context, documents)
- [ ] Foreign keys between context_usage and workflow_context validated
- [ ] Foreign keys between context_usage and documents table validated
- [ ] ContextPersistence uses same DB path as StateTracker
- [ ] ContextUsageTracker uses same DB path
- [ ] ContextLineageTracker uses same DB path
- [ ] Migration script moves data from old separate DBs
- [ ] Integration tests verify FK constraints work
- [ ] No orphaned data in separate databases

**Technical Notes:**
- Create `gao_dev.core.config.get_gao_db_path()` for unified DB path
- Update all context modules to use shared DB configuration
- Add migration script `003_unify_database.sql`
- Ensure workflow_context.workflow_id references workflow_executions.id

**Dependencies:** Epic 15 (StateTracker)

---

#### Story 17.3: Orchestrator Integration
**Points:** 8 | **Priority:** P0

**Description:** Wire WorkflowContext into GAODevOrchestrator lifecycle so workflows automatically create and persist context.

**Acceptance Criteria:**
- [ ] Orchestrator creates WorkflowContext at workflow start
- [ ] Context persisted to database at workflow initialization
- [ ] Context updated after each workflow phase transition
- [ ] Decisions recorded in context during execution
- [ ] Artifacts recorded in context as they're created
- [ ] Failed workflows mark context status as 'failed'
- [ ] Completed workflows mark context status as 'completed'
- [ ] WorkflowResult includes context_id field
- [ ] Integration tests verify full workflow with context tracking
- [ ] Benchmark workflows show context tracking in action

**Technical Notes:**
- Modify GAODevOrchestrator.__init__ to create ContextPersistence
- Add create_workflow_context() at workflow start
- Add update_workflow_context() after each phase
- Store context_id in WorkflowResult
- Use set_workflow_context() for thread-local access by agents

**Dependencies:** Story 17.1, Story 17.2

---

#### Story 17.4: Agent Prompt Integration
**Points:** 5 | **Priority:** P0

**Description:** Update agent prompts and configurations to use AgentContextAPI for accessing project context.

**Acceptance Criteria:**
- [ ] Story orchestrator sets WorkflowContext before agent execution
- [ ] Agents can call `get_workflow_context()` in prompt code
- [ ] Agents can access `context.get_epic_definition()` successfully
- [ ] Agents can access `context.get_architecture()` successfully
- [ ] Agents can access `context.get_coding_standards()` successfully
- [ ] Context usage automatically tracked for lineage
- [ ] Agent YAML configs include context API import examples
- [ ] Integration tests verify agents can access context
- [ ] Documentation shows complete agent usage examples
- [ ] Updated prompts work with real workflow executions

**Technical Notes:**
- Update `story_orchestrator/` prompts to set context
- Update `tasks/implement_story.yaml` to use AgentContextAPI
- Update `tasks/validate_story.yaml` to access context
- Add context API examples to agent YAML configs
- Document context access patterns for agent developers

**Dependencies:** Story 17.3

---

#### Story 17.5: CLI Commands for Context Management
**Points:** 5 | **Priority:** P1

**Description:** Add CLI commands for users to query and manage workflow context.

**Acceptance Criteria:**
- [ ] `gao-dev context show <workflow-id>` displays full context details
- [ ] `gao-dev context list` shows recent workflow contexts (last 20)
- [ ] `gao-dev context history <epic> <story>` shows all context versions
- [ ] `gao-dev context lineage <epic>` generates and displays lineage report
- [ ] `gao-dev context stats` shows cache hit rate and usage statistics
- [ ] `gao-dev context clear-cache` clears ContextCache
- [ ] All commands support `--json` output for scripting
- [ ] Rich formatting with tables and colors for terminal
- [ ] Help text and examples for all commands
- [ ] Unit tests for all CLI commands

**Technical Notes:**
- Create `gao_dev/cli/context_commands.py`
- Use Click for CLI framework
- Use Rich for table formatting and colors
- Register commands in `gao_dev/cli/commands.py`

**Dependencies:** Story 17.2, Story 17.3

---

#### Story 17.6: Migration System
**Points:** 3 | **Priority:** P1

**Description:** Implement database migration runner for schema upgrades and version tracking.

**Acceptance Criteria:**
- [ ] `schema_version` table tracks applied migrations with timestamps
- [ ] MigrationRunner detects pending migrations automatically
- [ ] Migrations applied in order on startup
- [ ] Rollback support for last N migrations
- [ ] `gao-dev db migrate` CLI command applies pending migrations
- [ ] `gao-dev db rollback [N]` CLI command rolls back migrations
- [ ] `gao-dev db status` shows migration status and version
- [ ] Migration logs show applied migrations with timestamps
- [ ] Integration tests verify migration up/down
- [ ] Existing databases migrated successfully without data loss

**Technical Notes:**
- Create `gao_dev/core/context/migrations/runner.py`
- Create `schema_version` table for tracking
- Support both .sql and Python migration files
- Add `003_unify_database.sql` migration
- Auto-run migrations on first DB access

**Dependencies:** Story 17.2

---

#### Story 17.7: End-to-End Integration Tests
**Points:** 3 | **Priority:** P0

**Description:** Comprehensive integration tests verifying the entire context system works end-to-end.

**Acceptance Criteria:**
- [ ] E2E test: Create PRD, workflow loads it via context
- [ ] E2E test: Implement story, context tracks document usage
- [ ] E2E test: Generate lineage report showing PRD → Architecture → Story flow
- [ ] E2E test: Cache hit rate >80% for repeated document access
- [ ] E2E test: Concurrent workflows don't interfere with each other
- [ ] E2E test: Missing documents handled gracefully (no errors)
- [ ] Performance test: Document load <50ms (p95)
- [ ] Performance test: Context save <50ms (p95)
- [ ] Performance test: Lineage query <100ms (p95)
- [ ] All E2E tests pass consistently (no flaky tests)

**Technical Notes:**
- Create `tests/integration/test_context_e2e.py`
- Create `tests/performance/test_context_performance.py`
- Use real DocumentLifecycleManager, not mocks
- Test full workflow execution end-to-end
- Validate performance claims from Epic 16

**Dependencies:** Story 17.1, 17.2, 17.3, 17.4

---

### Epic Dependencies
- **Requires:** Epic 12 (Document Lifecycle), Epic 15 (State Database), Epic 16 (Context Persistence Layer)
- **Blocks:** Meta-Prompt System, Advanced Context Features
- **Integrates With:** GAODevOrchestrator, Agent System, CLI

---

*End of Epic Breakdown*

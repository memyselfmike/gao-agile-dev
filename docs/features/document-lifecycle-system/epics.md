# Epic Breakdown
## Document Lifecycle & Context Management System

**Feature:** Document Lifecycle & Context Management
**Total Epics:** 5
**Estimated Duration:** 8-12 weeks
**Priority:** High (Core Infrastructure)

---

## Epic 11: Document Lifecycle Management

**Goal:** Build comprehensive document tracking system that manages document states, relationships, and archival.

**Owner:** Amelia (Developer) + Bob (Scrum Master for stories)
**Priority:** P0 (Critical - Foundation)
**Estimated Duration:** 2-3 weeks
**Story Points:** 28 points

### Success Criteria
- All documents tracked in SQLite registry
- Document queries return results in <100ms
- State machine enforces valid transitions
- Archival system moves obsolete documents automatically
- Lineage queries show document relationships
- Zero data loss in state transitions

### Stories

#### Story 11.1: Document Registry Database Schema
**Points:** 5 | **Priority:** P0

**Description:** Create SQLite database schema for document registry with tables for documents, relationships, and metadata.

**Acceptance Criteria:**
- [ ] `documents` table with all required fields (id, path, type, state, dates, author, metadata)
- [ ] `document_relationships` table for parent-child relationships
- [ ] Indexes on frequently queried columns (type, state, feature, epic)
- [ ] Foreign key constraints enforced
- [ ] Schema migration support
- [ ] Unit tests for schema creation
- [ ] Performance: Create tables <100ms

**Technical Notes:**
- Use SQLite JSON1 extension for metadata storage
- Content hash field for sync conflict detection
- Composite indexes for common query patterns

**Dependencies:** None (foundational)

---

#### Story 11.2: DocumentRegistry Implementation
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

**Dependencies:** Story 11.1

---

#### Story 11.3: Document State Machine
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

**Dependencies:** Story 11.2

---

#### Story 11.4: DocumentLifecycleManager
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

**Dependencies:** Story 11.3

---

#### Story 11.5: Document Scanning & Auto-Registration
**Points:** 5 | **Priority:** P1

**Description:** Implement document scanning to automatically discover and register existing documents.

**Acceptance Criteria:**
- [ ] `scan_directory()` discovers documents recursively
- [ ] Detects document type from path patterns
- [ ] Extracts metadata from frontmatter/YAML
- [ ] Registers unregistered documents
- [ ] Updates metadata for registered documents
- [ ] Respects exclude patterns (.git, node_modules, etc.)
- [ ] Progress reporting for large scans
- [ ] Performance: Scan 1000 docs <10 seconds

**Technical Notes:**
- Use glob patterns for type detection
- Parse markdown frontmatter for metadata
- Batch insert for performance

**Dependencies:** Story 11.4

---

#### Story 11.6: Archival System
**Points:** 5 | **Priority:** P1

**Description:** Implement automatic archival system that moves obsolete documents based on configurable rules.

**Acceptance Criteria:**
- [ ] Archival rules defined in YAML config
- [ ] Rules support: document type, state, age in days
- [ ] `archive_obsolete_documents()` applies rules
- [ ] Moves files to `.archive/` with preserved structure
- [ ] Metadata preserved in database
- [ ] Dry-run mode for testing
- [ ] CLI command: `gao-dev lifecycle archive`
- [ ] Unit tests for rule evaluation

**Technical Notes:**
- Configurable per document type
- Archive directory outside docs/
- Support manual archival override

**Dependencies:** Story 11.4

---

### Epic Dependencies
- **Requires:** Epic 10 (Prompt Abstraction) - COMPLETE
- **Blocks:** Epic 12 (Meta-Prompts), Epic 15 (Context Layer)

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

**Dependencies:** Epic 11 (Story 11.4)

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
- **Requires:** Epic 11 (Document Lifecycle)
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
- **Requires:** Epic 11 (Document Lifecycle)
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
- **Requires:** Epic 11 (Document Lifecycle for document models)
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

**Dependencies:** Epic 11 (Document Lifecycle)

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

**Dependencies:** Story 15.3, Epic 11 (Document Lifecycle)

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
- **Requires:** Epic 11 (Document Lifecycle), Epic 14 (State Database)
- **Enhances:** Epic 12 (Meta-Prompts use context cache)

---

## Epic Sequencing & Dependencies

### Critical Path

```
Epic 11 (Document Lifecycle) → 2-3 weeks
    ↓
Epic 12 (Meta-Prompts) → 2 weeks
    ↓
Epic 14 (State Database) → 2-3 weeks
    ↓
Epic 15 (Context Persistence) → 1-2 weeks
```

### Parallel Work

```
Epic 11 (weeks 1-3)
    └─ Epic 13 (Checklists) can start after Epic 11 complete (weeks 4-5)

Epic 12 (weeks 4-5) ║ Epic 13 (weeks 4-5)
    ↓                    ↓
Epic 14 (weeks 6-8) ← needs both complete
    ↓
Epic 15 (weeks 9-10)
```

### Recommended Sprint Breakdown

**Sprint 1 (Weeks 1-2): Foundation**
- Epic 11: Stories 11.1, 11.2, 11.3, 11.4 (18 points)
- Goal: Document lifecycle foundation working

**Sprint 2 (Weeks 3-4): Complete Document Lifecycle + Start Meta-Prompts**
- Epic 11: Stories 11.5, 11.6 (10 points)
- Epic 12: Stories 12.1, 12.2 (10 points)
- Goal: Document system complete, meta-prompts started

**Sprint 3 (Weeks 5-6): Meta-Prompts + Checklists**
- Epic 12: Stories 12.3, 12.4, 12.5, 12.6 (16 points)
- Epic 13: Stories 13.1, 13.2, 13.3 (13 points)
- Goal: Meta-prompts complete, checklist foundation

**Sprint 4 (Weeks 7-8): State Database**
- Epic 13: Stories 13.4, 13.5 (8 points)
- Epic 14: Stories 14.1, 14.2, 14.3 (17 points)
- Goal: Checklist system complete, state database started

**Sprint 5 (Weeks 9-10): Complete State + Context Layer**
- Epic 14: Stories 14.4, 14.5, 14.6 (12 points)
- Epic 15: Stories 15.1, 15.2, 15.3, 15.4, 15.5 (20 points)
- Goal: All epics complete, system integrated

---

## Total Effort Summary

| Epic | Story Points | Duration | Priority |
|------|--------------|----------|----------|
| Epic 11: Document Lifecycle | 28 | 2-3 weeks | P0 |
| Epic 12: Meta-Prompts | 26 | 2 weeks | P0 |
| Epic 13: Checklists | 21 | 1-2 weeks | P1 |
| Epic 14: State Database | 29 | 2-3 weeks | P0 |
| Epic 15: Context Persistence | 20 | 1-2 weeks | P1 |
| **TOTAL** | **124 points** | **8-12 weeks** | - |

### Team Velocity Assumptions
- 1 developer full-time: ~20 points/week
- 2 developers full-time: ~35 points/week
- With testing/refactoring overhead: ~15-20 points/week/developer

### Risk Buffer
- Add 20% buffer for unknowns: 10-14 weeks
- Add 30% buffer for integration issues: 10-16 weeks

---

## Implementation Order

### Phase 1: MVP (Epics 11, 12, 14)
**Duration:** 6-8 weeks
**Deliverable:** Core lifecycle + meta-prompts + state tracking

**Reason:** These three epics provide the minimum viable system:
- Document tracking (Epic 11)
- Context injection (Epic 12)
- Queryable state (Epic 14)

### Phase 2: Quality & Performance (Epics 13, 15)
**Duration:** 2-4 weeks
**Deliverable:** Checklists + context caching

**Reason:** These epics enhance the MVP:
- Reusable checklists (Epic 13)
- Performance optimization (Epic 15)

### Phase 3: Polish & Optimization
**Duration:** 1-2 weeks
**Deliverable:** Bug fixes, performance tuning, documentation

**Reason:** Final polish before production use

---

## Success Metrics

### MVP Success (After Phase 1)
- [ ] All documents tracked in registry
- [ ] @doc: and @query: references working in 10+ prompts
- [ ] Story/epic status queryable in <50ms
- [ ] Zero breaking changes to existing workflows
- [ ] Developer productivity: No increase in prompt complexity

### Full System Success (After Phase 2)
- [ ] 20+ checklists available
- [ ] Context cache hit rate >80%
- [ ] Document reads reduced by 80%
- [ ] Agent prompt size reduced by 50%
- [ ] Works across dev, ops, legal, research domains
- [ ] Plugin developers can extend all systems

### Performance Targets
- [ ] System overhead <5%
- [ ] Document queries <100ms
- [ ] Reference resolution <50ms per reference
- [ ] Context cache hit <1ms
- [ ] State queries <50ms

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

*End of Epic Breakdown*

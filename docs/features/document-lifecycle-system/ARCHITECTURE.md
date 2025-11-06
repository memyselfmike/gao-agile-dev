---
document:
  type: "architecture"
  state: "active"
  created: "2025-11-04"
  last_modified: "2025-11-06"
  author: "Winston"
  feature: "document-lifecycle-system"
  epic: null
  story: null
  related_documents:
    - "PRD.md"
    - "epics.md"
    - "ROADMAP.md"
  replaces: null
  replaced_by: null
---

# System Architecture
## GAO-Dev Document Lifecycle & Context Management System

**Version:** 1.0.0
**Date:** 2025-11-04
**Author:** Winston (Technical Architect)
**Status:** Draft

---

## Table of Contents
1. [System Context](#system-context)
2. [Architecture Overview](#architecture-overview)
3. [Component Design](#component-design)
4. [Data Models](#data-models)
5. [Integration Points](#integration-points)
6. [Technology Stack](#technology-stack)
7. [Directory Structure](#directory-structure)
8. [Performance Considerations](#performance-considerations)
9. [Security & Compliance](#security--compliance)
10. [Deployment & Operations](#deployment--operations)

---

## System Context

### Purpose
The Document Lifecycle & Context Management System provides comprehensive document tracking, meta-prompt context injection, reusable checklists, queryable state management, and context persistence across workflows.

### Key Goals
1. Track all document lifecycles (draft → active → obsolete → archived)
2. Automatically inject relevant context into agent prompts
3. Provide reusable, plugin-extensible checklists
4. Enable fast SQL queries for story/epic/sprint state
5. Persist context across workflow executions
6. Maintain domain-agnostic design for all GAO teams

### System Boundaries
**In Scope:**
- Document lifecycle management
- Meta-prompt context injection
- Checklist plugin system
- State tracking database
- Context persistence layer
- Integration with existing orchestrators

**Out of Scope:**
- Real-time collaboration (future)
- Access control (future)
- Cloud storage (future)
- Document editing UI (future)

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                       Application Layer                             │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐          │
│  │Orchestrators │  │   Agents     │  │ Workflow Engine  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────────┘          │
└─────────┼──────────────────┼──────────────────┼────────────────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼────────────────────┐
│                   Document Lifecycle Layer                          │
│                                                                      │
│  ┌────────────────────┐  ┌────────────────────┐                    │
│  │ DocumentLifecycle  │  │   MetaPromptEngine │                    │
│  │     Manager        │  │                    │                    │
│  └────────┬───────────┘  └─────────┬──────────┘                    │
│           │                        │                                │
│  ┌────────▼──────────┐   ┌────────▼──────────┐                    │
│  │ DocumentRegistry  │   │  PromptLoader+    │                    │
│  │    (SQLite)       │   │  (Extended)       │                    │
│  └───────────────────┘   └───────────────────┘                    │
└─────────────────────────────────────────────────────────────────────┘
          │                        │
┌─────────▼────────────────────────▼──────────────────────────────────┐
│                    State & Context Layer                            │
│                                                                      │
│  ┌────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │ StateTracker   │  │ ContextCache     │  │ ChecklistLoader  │   │
│  │   (SQLite)     │  │  (In-Memory)     │  │     (YAML)       │   │
│  └────────────────┘  └──────────────────┘  └──────────────────┘   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │              WorkflowContext (Persistence)                 │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
          │                        │                        │
┌─────────▼────────────────────────▼────────────────────────▼─────────┐
│                      Data Persistence Layer                          │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐          │
│  │  Documents   │  │  State DB    │  │  Metrics DB      │          │
│  │  (Markdown)  │  │  (SQLite)    │  │  (SQLite)        │          │
│  └──────────────┘  └──────────────┘  └──────────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
```

### Architectural Principles

**1. Separation of Concerns**
- Document lifecycle separate from state tracking
- Meta-prompt engine separate from prompt loader
- Context cache separate from workflow context

**2. Extensibility**
- Plugin-based checklist system
- Extensible reference syntax
- Custom document types via configuration

**3. Performance**
- Aggressive caching at all layers
- Indexed database queries
- Lazy loading of documents

**4. Reliability**
- Two-way sync (markdown ↔ SQLite)
- Graceful degradation
- Automatic recovery from failures

**5. Domain Agnostic**
- No hardcoded software engineering assumptions
- Configurable document types per domain
- Plugin-based domain extensions

---

## Component Design

### Component 1: DocumentLifecycleManager (ENHANCED)

**Purpose:** Manage document lifecycle from creation to archival with governance, templates, and search

**Responsibilities:**
- Track document metadata and states with governance fields (owner, reviewer, review_due_date)
- Enforce state machine transitions
- Archive obsolete documents with retention policies
- Manage document relationships and lineage
- Provide query interface with full-text search (FTS5)
- Generate documents from templates with standardized naming
- Track document health KPIs
- Support 5S methodology (Sort, Set in Order, Shine, Standardize, Sustain)

**Interface:**
```python
class DocumentLifecycleManager:
    """Manage document lifecycle and metadata."""

    def __init__(self, registry: DocumentRegistry, archive_dir: Path):
        """
        Initialize lifecycle manager.

        Args:
            registry: Document registry (SQLite)
            archive_dir: Directory for archived documents
        """
        self.registry = registry
        self.archive_dir = archive_dir
        self.state_machine = DocumentStateMachine()

    def register_document(
        self,
        path: Path,
        doc_type: str,
        author: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """
        Register a new document.

        Args:
            path: Path to document file
            doc_type: Type (prd, architecture, story, etc.)
            author: Document author
            metadata: Optional metadata

        Returns:
            Document object with assigned ID

        Raises:
            ValueError: If document already registered
        """

    def transition_state(
        self,
        doc_id: int,
        new_state: DocumentState,
        reason: Optional[str] = None
    ) -> bool:
        """
        Transition document to new state.

        Args:
            doc_id: Document ID
            new_state: Target state
            reason: Optional reason for transition

        Returns:
            True if transition successful

        Raises:
            InvalidStateTransition: If transition not allowed
        """

    def get_current_document(
        self,
        doc_type: str,
        feature: Optional[str] = None
    ) -> Optional[Document]:
        """
        Get current active document of specified type.

        Args:
            doc_type: Document type
            feature: Optional feature filter

        Returns:
            Active document or None
        """

    def get_document_lineage(
        self,
        doc_id: int
    ) -> Tuple[List[Document], List[Document]]:
        """
        Get document lineage (ancestors and descendants).

        Args:
            doc_id: Document ID

        Returns:
            Tuple of (ancestors, descendants)
        """

    def archive_document(self, doc_id: int) -> Path:
        """
        Archive document to archive directory.

        Args:
            doc_id: Document ID

        Returns:
            Path to archived file

        Raises:
            ValueError: If document not in archivable state
        """

    def query_documents(
        self,
        doc_type: Optional[str] = None,
        state: Optional[DocumentState] = None,
        feature: Optional[str] = None,
        epic: Optional[int] = None
    ) -> List[Document]:
        """
        Query documents with filters.

        Args:
            doc_type: Filter by type
            state: Filter by state
            feature: Filter by feature
            epic: Filter by epic

        Returns:
            List of matching documents
        """
```

**State Machine:**
```python
class DocumentStateMachine:
    """Enforce document state transitions."""

    TRANSITIONS = {
        DocumentState.DRAFT: [DocumentState.ACTIVE, DocumentState.ARCHIVED],
        DocumentState.ACTIVE: [DocumentState.OBSOLETE, DocumentState.ARCHIVED],
        DocumentState.OBSOLETE: [DocumentState.ARCHIVED],
        DocumentState.ARCHIVED: []  # Terminal state
    }

    def can_transition(self, from_state: DocumentState, to_state: DocumentState) -> bool:
        """Check if transition is allowed."""
        return to_state in self.TRANSITIONS.get(from_state, [])

    def transition(
        self,
        document: Document,
        to_state: DocumentState,
        reason: Optional[str] = None
    ) -> Document:
        """Execute state transition with validation."""
        if not self.can_transition(document.state, to_state):
            raise InvalidStateTransition(
                f"Cannot transition from {document.state} to {to_state}"
            )

        # Execute transition logic
        if to_state == DocumentState.ACTIVE:
            self._activate_document(document)
        elif to_state == DocumentState.OBSOLETE:
            self._mark_obsolete(document)
        elif to_state == DocumentState.ARCHIVED:
            self._archive_document(document)

        return document
```

### Component 2: MetaPromptEngine

**Purpose:** Extend PromptLoader with meta-prompt capabilities

**Responsibilities:**
- Resolve new reference types (@doc, @checklist, @query, @context)
- Extract document sections
- Automatic context injection
- Query execution and formatting

**Interface:**
```python
class MetaPromptEngine:
    """
    Extended prompt engine with meta-prompt capabilities.

    Builds on Epic 10's PromptLoader to add:
    - @doc: references for document injection
    - @checklist: references for checklist injection
    - @query: references for database queries
    - @context: references for cached context
    """

    def __init__(
        self,
        prompt_loader: PromptLoader,
        document_manager: DocumentLifecycleManager,
        checklist_loader: ChecklistLoader,
        state_tracker: StateTracker,
        context_cache: ContextCache
    ):
        """
        Initialize meta-prompt engine.

        Args:
            prompt_loader: Base prompt loader (Epic 10)
            document_manager: Document lifecycle manager
            checklist_loader: Checklist loader
            state_tracker: State tracker for queries
            context_cache: Context cache
        """
        self.prompt_loader = prompt_loader
        self.document_manager = document_manager
        self.checklist_loader = checklist_loader
        self.state_tracker = state_tracker
        self.context_cache = context_cache
        self._reference_resolvers = self._init_resolvers()

    def render_with_meta_prompts(
        self,
        template: PromptTemplate,
        variables: Dict[str, Any],
        auto_inject_context: bool = True
    ) -> str:
        """
        Render prompt with meta-prompt reference resolution.

        Args:
            template: Prompt template
            variables: Variables for substitution
            auto_inject_context: Whether to auto-inject context

        Returns:
            Rendered prompt with all references resolved
        """
        # Step 1: Auto-inject context if enabled
        if auto_inject_context:
            variables = self._inject_automatic_context(template, variables)

        # Step 2: Resolve all references
        resolved_vars = self._resolve_all_references(variables)

        # Step 3: Render using base prompt loader
        return self.prompt_loader.render_prompt(template, resolved_vars)

    def resolve_reference(self, reference: str) -> str:
        """
        Resolve a single reference.

        Args:
            reference: Reference string (e.g., "@doc:path/to/file.md")

        Returns:
            Resolved content

        Raises:
            ReferenceResolutionError: If reference cannot be resolved
        """
        ref_type, ref_value = self._parse_reference(reference)
        resolver = self._reference_resolvers.get(ref_type)

        if not resolver:
            raise ReferenceResolutionError(f"Unknown reference type: {ref_type}")

        return resolver(ref_value)

    def _resolve_doc_reference(self, ref: str) -> str:
        """
        Resolve @doc: reference.

        Supports:
        - @doc:path/to/file.md - Full document
        - @doc:path/to/file.md#section - Specific section
        - @doc:path/to/file.md@yaml_key - YAML field
        - @doc:glob:pattern/*.md - Multiple documents
        """
        # Parse reference
        if "#" in ref:
            path, section = ref.split("#", 1)
            return self._extract_section(path, section)
        elif "@" in ref:
            path, yaml_key = ref.split("@", 1)
            return self._extract_yaml_field(path, yaml_key)
        elif ref.startswith("glob:"):
            pattern = ref[5:]
            return self._resolve_glob_pattern(pattern)
        else:
            return self._load_document(ref)

    def _resolve_checklist_reference(self, ref: str) -> str:
        """
        Resolve @checklist: reference.

        Example: @checklist:testing/unit-test-standards
        """
        checklist = self.checklist_loader.load_checklist(ref)
        return self.checklist_loader.render_checklist(checklist)

    def _resolve_query_reference(self, ref: str) -> str:
        """
        Resolve @query: reference.

        Example: @query:stories.where(epic=3, status='done').format('markdown')
        """
        # Parse query
        query = self._parse_query(ref)

        # Execute query
        results = self.state_tracker.execute_query(query)

        # Format results
        return self._format_query_results(results, query.format)

    def _resolve_context_reference(self, ref: str) -> str:
        """
        Resolve @context: reference.

        Example: @context:epic_definition
        """
        # Try cache first
        cached = self.context_cache.get(ref)
        if cached:
            return cached

        # Fallback to document manager
        return self._load_context_from_documents(ref)

    def _inject_automatic_context(
        self,
        template: PromptTemplate,
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Inject context automatically based on workflow.

        Rules:
        - story workflows: inject epic context + architecture
        - implementation workflows: inject story + tech specs
        - validation workflows: inject checklists + acceptance criteria
        """
        workflow_name = template.metadata.get("workflow")

        if not workflow_name:
            return variables

        # Get auto-injection config for workflow
        auto_config = self._get_auto_injection_config(workflow_name)

        # Inject configured references
        for key, reference in auto_config.items():
            if key not in variables:  # Don't override explicit variables
                variables[key] = f"@{reference}"

        return variables
```

### Component 2A: DocumentNamingConvention (NEW - Research Insight)

**Purpose:** Enforce standardized document naming convention for professional, searchable filenames

**Responsibilities:**
- Generate standard filenames: `{DocType}_{subject}_{date}_v{version}.{ext}`
- Parse filenames into components
- Validate filenames against standard
- Provide CLI utilities for bulk renaming

**Interface:**
```python
class DocumentNamingConvention:
    """Enforce naming standards from research team."""

    PATTERN = re.compile(
        r"^(?P<doctype>[A-Z]+)_(?P<subject>[a-z0-9-]+)_(?P<date>\d{4}-\d{2}-\d{2})_v(?P<version>\d+\.\d+)\.(?P<ext>\w+)$"
    )

    @staticmethod
    def generate_filename(doc_type: str, subject: str, version: str = "1.0") -> str:
        """
        Generate standard filename.

        Example: generate_filename("PRD", "user authentication", "2.0")
        Returns: "PRD_user-authentication_2024-11-05_v2.0.md"
        """
        date = datetime.now().strftime("%Y-%m-%d")
        subject_slug = subject.lower().replace(" ", "-")
        return f"{doc_type.upper()}_{subject_slug}_{date}_v{version}.md"

    @staticmethod
    def parse_filename(filename: str) -> Dict[str, str]:
        """Parse filename into components."""
        match = DocumentNamingConvention.PATTERN.match(filename)
        if not match:
            raise ValueError(f"Filename does not match convention: {filename}")
        return match.groupdict()

    @staticmethod
    def validate_filename(filename: str) -> Tuple[bool, Optional[str]]:
        """Validate filename, return (is_valid, error_message)."""
        try:
            DocumentNamingConvention.parse_filename(filename)
            return (True, None)
        except ValueError as e:
            return (False, str(e))
```

**Technical Notes:**
- Pattern: `PRD_user-auth_2024-11-05_v1.0.md`
- ADRs use sequential numbering: `ADR-001_database-choice_2024-09-01.md`
- Postmortems use incident date: `Postmortem_2024-11-15_api-outage.md`

---

### Component 2B: DocumentTemplateManager (NEW - Research Insight)

**Purpose:** Generate documents from templates with proper frontmatter and naming

**Responsibilities:**
- Load and render document templates (Jinja2)
- Auto-generate filenames using naming convention
- Auto-populate YAML frontmatter with governance fields
- Auto-register documents in lifecycle system
- Provide CLI for document creation

**Interface:**
```python
class DocumentTemplateManager:
    """Manage document templates with proper frontmatter."""

    def __init__(
        self,
        templates_dir: Path,
        doc_manager: DocumentLifecycleManager,
        naming_convention: DocumentNamingConvention
    ):
        self.templates_dir = templates_dir
        self.doc_manager = doc_manager
        self.naming = naming_convention
        self.jinja_env = Environment(loader=FileSystemLoader(templates_dir))

    def create_from_template(
        self,
        template_name: str,
        variables: Dict[str, Any],
        output_dir: Path
    ) -> Path:
        """
        Create new document from template.

        Args:
            template_name: Template name (e.g., "prd", "architecture", "story")
            variables: Template variables (subject, author, feature, epic, etc.)
            output_dir: Where to create the document

        Returns:
            Path to created document
        """
        # Load template
        template = self.jinja_env.get_template(f"{template_name}.md.j2")

        # Generate filename using naming convention
        filename = self.naming.generate_filename(
            doc_type=variables.get('doc_type', template_name.upper()),
            subject=variables['subject'],
            version=variables.get('version', '1.0')
        )

        # Auto-populate governance fields
        frontmatter = self._generate_frontmatter(template_name, variables)

        # Render template with frontmatter
        rendered = self._render_with_frontmatter(template, variables, frontmatter)

        # Write file
        file_path = output_dir / filename
        file_path.write_text(rendered)

        # Auto-register in lifecycle system
        self.doc_manager.register_document(
            path=file_path,
            doc_type=variables.get('doc_type', template_name),
            author=variables.get('author'),
            metadata=frontmatter
        )

        return file_path

    def _generate_frontmatter(
        self,
        template_name: str,
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate YAML frontmatter with governance fields."""
        today = datetime.now().strftime("%Y-%m-%d")

        # Get governance config for document type
        governance = self._get_governance_config(template_name)

        review_cadence_days = governance.get('review_cadence', 90)
        review_due = (datetime.now() + timedelta(days=review_cadence_days)).strftime("%Y-%m-%d")

        return {
            "title": variables['subject'],
            "doc_type": variables.get('doc_type', template_name.upper()),
            "status": "draft",
            "owner": variables.get('author'),
            "reviewer": governance.get('reviewer'),
            "created_date": today,
            "last_updated": today,
            "version": variables.get('version', '1.0'),
            "review_due_date": review_due,
            "related_docs": variables.get('related_docs', []),
            "tags": variables.get('tags', []),
            "retention_policy": governance.get('retention_policy', 'archive_after_30_days_obsolete'),
            "feature": variables.get('feature'),
            "epic": variables.get('epic'),
        }
```

**Available Templates:**
- `prd.md.j2` - Product Requirements Document
- `architecture.md.j2` - System Architecture
- `epic.md.j2` - Epic Definition
- `story.md.j2` - User Story
- `adr.md.j2` - Architecture Decision Record
- `postmortem.md.j2` - Incident Postmortem
- `runbook.md.j2` - Operational Runbook

---

### Component 2C: DocumentSearch (NEW - Research Insight)

**Purpose:** Full-text search using SQLite FTS5 for fast document discovery

**Responsibilities:**
- Full-text search across documents
- Tag-based filtering
- Related document discovery
- Result ranking by relevance
- Position for Phase 3 semantic search (vector embeddings)

**Interface:**
```python
class DocumentSearch:
    """Full-text search for documents using FTS5."""

    def __init__(self, registry: DocumentRegistry):
        self.registry = registry

    def search(
        self,
        query: str,
        doc_type: Optional[str] = None,
        state: Optional[DocumentState] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[Tuple[Document, float]]:
        """
        Full-text search with filters.

        Args:
            query: Search query ("authentication security")
            doc_type: Filter by document type
            state: Filter by state
            tags: Filter by tags
            limit: Max results

        Returns:
            List of (Document, relevance_score) tuples

        Examples:
            search("authentication security")
            search("api design", doc_type="architecture")
            search("testing", tags=["epic-3"])
        """
        # Use FTS5 MATCH for full-text search
        sql = """
            SELECT d.*, fts.rank FROM documents d
            JOIN documents_fts fts ON d.id = fts.rowid
            WHERE fts MATCH ?
        """

        params = [query]

        # Add filters
        if doc_type:
            sql += " AND d.type = ?"
            params.append(doc_type)

        if state:
            sql += " AND d.state = ?"
            params.append(state.value)

        if tags:
            # Use JSON functions to query tags
            sql += " AND EXISTS (SELECT 1 FROM json_each(d.metadata, '$.tags') WHERE value IN ({})".format(
                ','.join('?' * len(tags))
            )
            sql += ")"
            params.extend(tags)

        sql += " ORDER BY fts.rank LIMIT ?"
        params.append(limit)

        return self.registry._execute_query(sql, params)

    def search_by_tags(self, tags: List[str]) -> List[Document]:
        """Tag-based search."""
        sql = """
            SELECT * FROM documents
            WHERE EXISTS (
                SELECT 1 FROM json_each(metadata, '$.tags')
                WHERE value IN ({})
            )
        """.format(','.join('?' * len(tags)))
        return self.registry._execute_query(sql, tags)

    def get_related_documents(
        self,
        doc_id: int,
        limit: int = 10
    ) -> List[Tuple[Document, float]]:
        """
        Find related documents by content similarity.

        Uses FTS5 for lexical similarity (Phase 1-2).
        Can be enhanced with vector embeddings for semantic similarity (Phase 3).
        """
        # Get document content
        doc = self.registry.get_document(doc_id)

        # Extract key terms for similarity search
        terms = self._extract_key_terms(doc.content)
        query = " ".join(terms[:10])  # Use top 10 terms

        # Search for similar documents
        results = self.search(query, limit=limit)

        # Filter out the original document
        return [(d, score) for d, score in results if d.id != doc_id]

    def _extract_key_terms(self, content: str) -> List[str]:
        """Extract key terms from content for similarity search."""
        # Simple term extraction (can be enhanced with TF-IDF, etc.)
        # Remove common words, extract nouns/technical terms
        # ...implementation...
        pass
```

**FTS5 Schema:**
```sql
-- FTS5 virtual table for full-text search
CREATE VIRTUAL TABLE documents_fts USING fts5(
    title,
    content,
    tags,
    content='documents',
    content_rowid='id'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER documents_fts_insert AFTER INSERT ON documents BEGIN
    INSERT INTO documents_fts(rowid, title, content, tags)
    VALUES (
        new.id,
        new.path,
        new.content,
        json_extract(new.metadata, '$.tags')
    );
END;

CREATE TRIGGER documents_fts_update AFTER UPDATE ON documents BEGIN
    UPDATE documents_fts
    SET title = new.path,
        content = new.content,
        tags = json_extract(new.metadata, '$.tags')
    WHERE rowid = new.id;
END;

CREATE TRIGGER documents_fts_delete AFTER DELETE ON documents BEGIN
    DELETE FROM documents_fts WHERE rowid = old.id;
END;
```

---

### Component 2D: DocumentHealthMetrics (NEW - Research Insight)

**Purpose:** Track KPIs and health monitoring for document lifecycle system

**Responsibilities:**
- Collect document health metrics
- Generate health reports
- Track document access patterns
- Identify stale/orphaned documents
- Monitor system effectiveness (5S: Sustain)

**Interface:**
```python
class DocumentHealthMetrics:
    """Track document health KPIs."""

    def __init__(
        self,
        registry: DocumentRegistry,
        governance: DocumentGovernance,
        metrics_db: Path
    ):
        self.registry = registry
        self.governance = governance
        self.metrics_db = metrics_db

    def collect_metrics(self) -> Dict[str, Any]:
        """Collect all document health metrics."""
        return {
            "total_documents": self.count_documents(),
            "documents_by_state": self.count_by_state(),
            "documents_by_type": self.count_by_type(),
            "stale_documents": self.count_stale_documents(),
            "documents_needing_review": self.count_review_due(),
            "orphaned_documents": self.count_orphaned(),
            "avg_document_age_days": self.avg_document_age(),
            "most_accessed_documents": self.get_top_accessed(limit=10),
            "least_accessed_documents": self.get_least_accessed(limit=10),
            "cache_hit_rate": self.get_cache_hit_rate(),
            "avg_query_time_ms": self.get_avg_query_time(),
            "context_injection_rate": self.get_auto_injection_rate(),
            "naming_compliance_rate": self.get_naming_compliance_rate(),
            "frontmatter_compliance_rate": self.get_frontmatter_compliance_rate(),
        }

    def count_stale_documents(self) -> int:
        """Count documents not updated in >review_cadence days."""
        sql = """
            SELECT COUNT(*) FROM documents d
            WHERE julianday('now') - julianday(d.modified_at) >
                  COALESCE(json_extract(d.metadata, '$.review_cadence_days'), 90)
        """
        return self.registry._execute_scalar(sql)

    def count_review_due(self) -> int:
        """Count documents with review_due_date in the past."""
        sql = """
            SELECT COUNT(*) FROM documents
            WHERE json_extract(metadata, '$.review_due_date') < date('now')
              AND state != 'archived'
        """
        return self.registry._execute_scalar(sql)

    def count_orphaned(self) -> int:
        """Count documents with no relationships to other documents."""
        sql = """
            SELECT COUNT(*) FROM documents d
            WHERE NOT EXISTS (
                SELECT 1 FROM document_relationships
                WHERE parent_id = d.id OR child_id = d.id
            )
            AND d.type NOT IN ('temp', 'draft')
        """
        return self.registry._execute_scalar(sql)

    def get_naming_compliance_rate(self) -> float:
        """Percentage of documents following naming convention."""
        total = self.count_documents()
        compliant = self._count_naming_compliant()
        return (compliant / total * 100) if total > 0 else 0.0

    def generate_health_report(self) -> str:
        """Generate markdown health report."""
        metrics = self.collect_metrics()

        report = f"""# Document Lifecycle Health Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary Metrics

| Metric | Value |
|--------|-------|
| Total Documents | {metrics['total_documents']} |
| Stale Documents | {metrics['stale_documents']} ({metrics['stale_documents']/metrics['total_documents']*100:.1f}%) |
| Needs Review | {metrics['documents_needing_review']} |
| Orphaned Documents | {metrics['orphaned_documents']} |
| Avg Document Age | {metrics['avg_document_age_days']:.1f} days |
| Cache Hit Rate | {metrics['cache_hit_rate']:.1f}% |
| Avg Query Time | {metrics['avg_query_time_ms']:.1f}ms |
| Naming Compliance | {metrics['naming_compliance_rate']:.1f}% |

## Documents by State

| State | Count |
|-------|-------|
"""
        for state, count in metrics['documents_by_state'].items():
            report += f"| {state} | {count} |\n"

        report += "\n## Action Items\n\n"

        if metrics['stale_documents'] > 0:
            report += f"- [ ] Review {metrics['stale_documents']} stale documents\n"

        if metrics['documents_needing_review'] > 0:
            report += f"- [ ] Review {metrics['documents_needing_review']} documents past due date\n"

        if metrics['orphaned_documents'] > 0:
            report += f"- [ ] Verify {metrics['orphaned_documents']} orphaned documents\n"

        if metrics['naming_compliance_rate'] < 100:
            non_compliant = metrics['total_documents'] * (100 - metrics['naming_compliance_rate']) / 100
            report += f"- [ ] Rename {non_compliant:.0f} non-compliant documents\n"

        return report
```

---

### Component 3: ChecklistLoader

**Purpose:** Load and manage YAML-based checklists

**Responsibilities:**
- Load checklist YAML files
- Resolve inheritance (extends)
- Render checklists as markdown
- Plugin discovery and loading
- Validation against schema

**Interface:**
```python
class ChecklistLoader:
    """Load and manage YAML-based checklists."""

    def __init__(
        self,
        checklists_dir: Path,
        plugin_manager: Optional[PluginManager] = None,
        validator: Optional[SchemaValidator] = None
    ):
        """
        Initialize checklist loader.

        Args:
            checklists_dir: Directory containing checklists
            plugin_manager: Optional plugin manager
            validator: Optional schema validator
        """
        self.checklists_dir = checklists_dir
        self.plugin_manager = plugin_manager
        self.validator = validator
        self._cache: Dict[str, Checklist] = {}

    def load_checklist(self, checklist_name: str) -> Checklist:
        """
        Load checklist by name.

        Args:
            checklist_name: Name (e.g., "testing/unit-test-standards")

        Returns:
            Checklist object

        Raises:
            ChecklistNotFoundError: If not found
            ChecklistValidationError: If invalid
        """

    def render_checklist(
        self,
        checklist: Checklist,
        format: str = "markdown"
    ) -> str:
        """
        Render checklist in specified format.

        Args:
            checklist: Checklist to render
            format: Output format (markdown, html, json)

        Returns:
            Rendered checklist
        """

    def list_checklists(
        self,
        category: Optional[str] = None,
        domain: Optional[str] = None
    ) -> List[str]:
        """
        List available checklists.

        Args:
            category: Filter by category
            domain: Filter by domain

        Returns:
            List of checklist names
        """

    def track_execution(
        self,
        checklist_name: str,
        artifact_type: str,
        artifact_id: str,
        results: Dict[str, str]
    ) -> int:
        """
        Track checklist execution.

        Args:
            checklist_name: Checklist name
            artifact_type: Type (story, pr, deployment, etc.)
            artifact_id: Artifact identifier
            results: Dict of item_id -> status (pass/fail/skip/na)

        Returns:
            Execution ID
        """
```

**Checklist Data Model:**
```python
@dataclass
class ChecklistItem:
    """Single checklist item."""
    id: str
    text: str
    severity: str  # high, medium, low
    category: Optional[str] = None
    help_text: Optional[str] = None

@dataclass
class Checklist:
    """Checklist definition."""
    name: str
    category: str
    version: str
    description: str
    extends: Optional[str] = None
    items: List[ChecklistItem] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def render_markdown(self) -> str:
        """Render as markdown checklist."""
        lines = [f"# {self.name}", "", self.description, ""]
        for item in self.items:
            severity_badge = f"[{item.severity.upper()}]" if item.severity != "medium" else ""
            lines.append(f"- [ ] {item.text} {severity_badge}")
            if item.help_text:
                lines.append(f"  > {item.help_text}")
        return "\n".join(lines)
```

### Component 4: StateTracker

**Purpose:** Unified SQLite-based state tracking

**Responsibilities:**
- Track story, epic, sprint state
- Sync with markdown files
- Provide query API
- Track workflow executions
- Generate reports

**Interface:**
```python
class StateTracker:
    """Unified state tracking with SQLite backend."""

    def __init__(self, db_path: Path, sync_enabled: bool = True):
        """
        Initialize state tracker.

        Args:
            db_path: Path to SQLite database
            sync_enabled: Whether to sync with markdown files
        """
        self.db_path = db_path
        self.sync_enabled = sync_enabled
        self._db = self._init_database()
        self._syncer = MarkdownSyncer(self) if sync_enabled else None

    # Story operations
    def create_story(
        self,
        epic_num: int,
        story_num: int,
        title: str,
        **kwargs
    ) -> Story:
        """Create new story."""

    def get_story(self, epic_num: int, story_num: int) -> Optional[Story]:
        """Get story by epic and story number."""

    def update_story_status(
        self,
        epic_num: int,
        story_num: int,
        status: StoryStatus
    ) -> bool:
        """Update story status."""

    def get_stories_by_status(
        self,
        status: StoryStatus
    ) -> List[Story]:
        """Get all stories with specified status."""

    # Epic operations
    def create_epic(
        self,
        epic_num: int,
        name: str,
        feature: str,
        goal: str
    ) -> Epic:
        """Create new epic."""

    def get_epic(self, epic_num: int) -> Optional[Epic]:
        """Get epic by number."""

    def get_epic_progress(
        self,
        epic_num: int
    ) -> Dict[str, Any]:
        """
        Get epic progress.

        Returns:
            {
                "completed": 7,
                "in_progress": 2,
                "total": 9,
                "percentage": 77.8
            }
        """

    # Sprint operations
    def create_sprint(
        self,
        sprint_num: int,
        name: str,
        start_date: str,
        end_date: str,
        goal: str
    ) -> Sprint:
        """Create new sprint."""

    def get_current_sprint(self) -> Optional[Sprint]:
        """Get currently active sprint."""

    def assign_story_to_sprint(
        self,
        story_id: int,
        sprint_id: int
    ) -> bool:
        """Assign story to sprint."""

    def get_sprint_velocity(
        self,
        sprint_num: int
    ) -> float:
        """Calculate sprint velocity (points completed)."""

    # Query operations
    def execute_query(self, query: Query) -> List[Dict[str, Any]]:
        """Execute custom query."""

    # Sync operations
    def sync_from_markdown(self, path: Path) -> None:
        """Sync database from markdown file."""

    def sync_to_markdown(self, path: Path) -> None:
        """Sync markdown file from database."""
```

**Database Schema:**
```sql
-- Core tables
CREATE TABLE epics (
    id INTEGER PRIMARY KEY,
    epic_num INTEGER UNIQUE NOT NULL,
    name TEXT NOT NULL,
    feature TEXT,
    goal TEXT,
    status TEXT CHECK(status IN ('planned', 'active', 'completed', 'cancelled')),
    created_at TEXT NOT NULL,
    completed_at TEXT
);

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
    content_hash TEXT,  -- For sync conflict detection
    UNIQUE(epic_num, story_num)
);

CREATE TABLE sprints (
    id INTEGER PRIMARY KEY,
    sprint_num INTEGER UNIQUE NOT NULL,
    name TEXT NOT NULL,
    goal TEXT,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT CHECK(status IN ('planned', 'active', 'completed'))
);

CREATE TABLE story_assignments (
    story_id INTEGER REFERENCES stories(id),
    sprint_id INTEGER REFERENCES sprints(id),
    PRIMARY KEY (story_id, sprint_id)
);

CREATE TABLE workflow_executions (
    id INTEGER PRIMARY KEY,
    workflow_name TEXT NOT NULL,
    story_id INTEGER REFERENCES stories(id),
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT CHECK(status IN ('running', 'completed', 'failed')),
    metadata JSON
);

-- Indexes for performance
CREATE INDEX idx_stories_epic ON stories(epic_num);
CREATE INDEX idx_stories_status ON stories(status);
CREATE INDEX idx_stories_owner ON stories(owner);
CREATE INDEX idx_workflow_story ON workflow_executions(story_id);
```

### Component 5: ContextCache & WorkflowContext

**Purpose:** Cache and persist context across workflows

**Responsibilities:**
- In-memory cache with TTL
- Workflow context object
- Context persistence
- Lineage tracking

**Interface:**
```python
class ContextCache:
    """In-memory cache for frequently accessed documents."""

    def __init__(self, ttl: int = 300, max_size: int = 100):
        """
        Initialize context cache.

        Args:
            ttl: Time-to-live in seconds (default: 5 minutes)
            max_size: Maximum cache size (LRU eviction)
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.ttl = ttl
        self.max_size = max_size
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[str]:
        """Get cached value if not expired."""

    def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """Set cache value with optional custom TTL."""

    def invalidate(self, key: str) -> None:
        """Invalidate cached value."""

    def clear(self) -> None:
        """Clear entire cache."""

@dataclass
class WorkflowContext:
    """Context passed through workflow execution."""
    workflow_id: str
    epic_num: int
    story_num: Optional[int]
    feature: str

    # Cached documents (lazy-loaded)
    _prd: Optional[str] = None
    _architecture: Optional[str] = None
    _epic_definition: Optional[str] = None
    _story_definition: Optional[str] = None

    # State
    current_phase: str = "analysis"
    decisions: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def get_epic_definition(self) -> str:
        """Lazy-load epic definition."""
        if not self._epic_definition:
            self._epic_definition = self._load_epic()
        return self._epic_definition

    def get_architecture(self) -> str:
        """Lazy-load architecture."""
        if not self._architecture:
            self._architecture = self._load_architecture()
        return self._architecture

    # Similar for other lazy-loaded properties

class ContextPersistence:
    """Persist workflow context to database."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_schema()

    def save_context(self, context: WorkflowContext) -> None:
        """Save context to database."""

    def load_context(self, workflow_id: str) -> Optional[WorkflowContext]:
        """Load context from database."""

    def track_context_usage(
        self,
        artifact_type: str,
        artifact_id: str,
        document_id: int,
        document_version: str
    ) -> None:
        """Track which context was used for which artifact."""

    def get_context_lineage(
        self,
        artifact_type: str,
        artifact_id: str
    ) -> List[Dict[str, Any]]:
        """Get context lineage for artifact."""
```

---

## Data Models

### Document Models

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

class DocumentState(Enum):
    """Document lifecycle states."""
    DRAFT = "draft"
    ACTIVE = "active"
    OBSOLETE = "obsolete"
    ARCHIVED = "archived"

class DocumentType(Enum):
    """Document types."""
    PRD = "prd"
    ARCHITECTURE = "architecture"
    TECH_SPEC = "tech_spec"
    EPIC = "epic"
    STORY = "story"
    USER_STORY = "user_story"
    QA_REPORT = "qa_report"
    TEST_REPORT = "test_report"
    CHECKLIST = "checklist"
    CODE = "code"
    CONFIG = "config"

@dataclass
class Document:
    """Document metadata model."""
    id: Optional[int] = None
    path: str = ""
    doc_type: DocumentType = DocumentType.STORY
    state: DocumentState = DocumentState.DRAFT
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_at: str = field(default_factory=lambda: datetime.now().isoformat())
    author: Optional[str] = None
    feature: Optional[str] = None
    epic: Optional[int] = None
    story: Optional[str] = None
    content_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Relationships
    parent_ids: List[int] = field(default_factory=list)
    child_ids: List[int] = field(default_factory=list)
    replaces_id: Optional[int] = None
    replaced_by_id: Optional[int] = None

@dataclass
class DocumentRelationship:
    """Document relationship model."""
    parent_id: int
    child_id: int
    relationship_type: str  # "derived_from", "implements", "tests", etc.
```

### State Models

```python
class StoryStatus(Enum):
    """Story status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

class EpicStatus(Enum):
    """Epic status values."""
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

@dataclass
class Story:
    """Story model."""
    id: Optional[int] = None
    epic_num: int = 0
    story_num: int = 0
    title: str = ""
    status: StoryStatus = StoryStatus.PENDING
    priority: str = "P2"
    points: int = 0
    owner: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    file_path: Optional[str] = None
    content_hash: Optional[str] = None

@dataclass
class Epic:
    """Epic model."""
    id: Optional[int] = None
    epic_num: int = 0
    name: str = ""
    feature: Optional[str] = None
    goal: str = ""
    status: EpicStatus = EpicStatus.PLANNED
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    total_points: int = 0
    completed_points: int = 0
```

### Checklist Models

```python
@dataclass
class ChecklistItem:
    """Single checklist item."""
    id: str
    text: str
    severity: str  # high, medium, low
    category: Optional[str] = None
    help_text: Optional[str] = None

@dataclass
class Checklist:
    """Checklist definition."""
    name: str
    category: str
    version: str
    description: str
    extends: Optional[str] = None
    items: List[ChecklistItem] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ChecklistExecution:
    """Checklist execution record."""
    id: Optional[int] = None
    checklist_name: str = ""
    artifact_type: str = ""
    artifact_id: str = ""
    executed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    executed_by: Optional[str] = None
    overall_status: str = "pass"  # pass, fail, partial
    results: Dict[str, str] = field(default_factory=dict)  # item_id -> status
```

---

## Integration Points

### Integration with Existing Systems

**1. Epic 10: Prompt & Agent Configuration Abstraction**
- MetaPromptEngine extends PromptLoader
- Reuse PromptTemplate and PromptRegistry
- Maintain backwards compatibility
- Add new reference resolvers

**2. Orchestrators (GAODevOrchestrator, BrianOrchestrator)**
- Pass WorkflowContext to all workflows
- Query StateTracker for story/epic status
- Use DocumentLifecycleManager for document queries
- Inject context automatically via MetaPromptEngine

**3. Sandbox & Benchmarking**
- Track benchmark artifacts in DocumentRegistry
- Link benchmark runs to stories
- Query context lineage for audit trails
- No changes to metrics database

**4. Plugin System**
- Load plugin checklists via ChecklistLoader
- Plugin documents registered in DocumentRegistry
- Plugin-specific document types supported
- Domain-specific context injection rules

### API Integration Points

```python
# Orchestrator integration
class GAODevOrchestrator:
    def __init__(self, ...):
        # Add new dependencies
        self.document_manager = DocumentLifecycleManager(...)
        self.meta_prompt_engine = MetaPromptEngine(...)
        self.state_tracker = StateTracker(...)
        self.context_cache = ContextCache()

    async def execute_workflow(self, workflow_name: str, **kwargs):
        # Create workflow context
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=kwargs.get('epic_num'),
            story_num=kwargs.get('story_num'),
            feature=kwargs.get('feature')
        )

        # Pass context to workflow
        result = await self._execute_with_context(workflow_name, context, **kwargs)

        # Persist context
        self.context_persistence.save_context(context)

        return result

# Agent integration
class ClaudeAgent:
    def execute_task(self, task: str, context: WorkflowContext):
        # Get prompt template
        template = self.meta_prompt_engine.load_prompt(task)

        # Render with context auto-injection
        prompt = self.meta_prompt_engine.render_with_meta_prompts(
            template,
            variables={'context': context},
            auto_inject_context=True
        )

        # Execute with Claude
        return self.claude_client.create_message(prompt)
```

---

## Technology Stack

### Core Technologies
- **Python**: 3.11+
- **SQLite**: 3.35+ (document registry, state tracking)
- **PyYAML**: 6.0+ (checklist parsing)
- **jsonschema**: 4.17+ (validation)
- **structlog**: 23.1+ (logging)

### Existing GAO-Dev Stack (Reused)
- **Click**: CLI framework
- **Jinja2**: Template rendering
- **pytest**: Testing
- **mypy**: Type checking
- **black/ruff**: Code quality

### Performance Libraries
- **cachetools**: LRU cache implementation
- **watchdog**: File system monitoring (optional)

### Database
```
SQLite Features Used:
- Foreign key constraints
- JSON1 extension (for metadata storage)
- FTS5 (full-text search - future)
- Indexes on foreign keys
- Transactions for consistency
```

---

## Directory Structure

```
gao_dev/
├── lifecycle/                        # NEW: Document lifecycle system
│   ├── __init__.py
│   ├── document_manager.py           # DocumentLifecycleManager
│   ├── document_registry.py          # SQLite registry
│   ├── document_state.py             # State machine
│   ├── archival.py                   # Archival logic
│   └── models.py                     # Document models
│
├── meta_prompts/                     # NEW: Meta-prompt system
│   ├── __init__.py
│   ├── meta_engine.py                # MetaPromptEngine
│   ├── reference_resolvers.py        # Reference resolution
│   ├── section_extractor.py          # Section extraction
│   ├── query_executor.py             # Query execution
│   └── auto_injector.py              # Automatic context injection
│
├── checklists/                       # NEW: Checklist system
│   ├── __init__.py
│   ├── loader.py                     # ChecklistLoader
│   ├── registry.py                   # ChecklistRegistry
│   ├── execution.py                  # Execution tracking
│   └── models.py                     # Checklist models
│
├── state/                            # NEW: State tracking
│   ├── __init__.py
│   ├── tracker.py                    # StateTracker
│   ├── syncer.py                     # Markdown-SQLite sync
│   ├── query_builder.py              # Query builder
│   └── models.py                     # State models
│
├── context/                          # NEW: Context management
│   ├── __init__.py
│   ├── cache.py                      # ContextCache
│   ├── workflow_context.py           # WorkflowContext
│   ├── persistence.py                # Context persistence
│   └── lineage.py                    # Lineage tracking
│
├── config/
│   ├── checklists/                   # NEW: Checklist YAML files
│   │   ├── testing/
│   │   │   ├── unit-test-standards.yaml
│   │   │   ├── integration-test-standards.yaml
│   │   │   └── e2e-test-standards.yaml
│   │   ├── code-quality/
│   │   │   ├── solid-principles.yaml
│   │   │   ├── clean-code.yaml
│   │   │   └── python-standards.yaml
│   │   ├── security/
│   │   │   ├── owasp-top-10.yaml
│   │   │   └── secure-coding.yaml
│   │   ├── deployment/
│   │   │   ├── production-readiness.yaml
│   │   │   └── rollout-checklist.yaml
│   │   ├── operations/
│   │   │   ├── incident-response.yaml
│   │   │   └── change-management.yaml
│   │   └── legal/
│   │       ├── contract-review.yaml
│   │       └── compliance-check.yaml
│   │
│   ├── schemas/
│   │   ├── checklist_schema.json     # NEW: Checklist schema
│   │   ├── document_schema.json      # NEW: Document schema
│   │   └── ... (existing schemas)
│   │
│   └── ... (existing config files)
│
├── core/
│   ├── prompt_loader.py              # MODIFIED: Extended for meta-prompts
│   └── ... (existing core files)
│
└── ... (existing modules)

docs/
└── .archive/                         # NEW: Archived documents
    ├── features/
    ├── stories/
    └── ... (archived structure mirrors docs/)

~/.gao-dev/
├── metrics.db                        # Existing: Benchmark metrics
├── state.db                          # NEW: Story/epic/sprint state
├── documents.db                      # NEW: Document registry
└── context.db                        # NEW: Context persistence
```

---

## Performance Considerations

### Caching Strategy

**1. Multi-Level Cache**
```
Level 1: In-Memory (ContextCache)
- TTL: 5 minutes
- Size: 100 entries (LRU)
- Hit rate target: >80%

Level 2: SQLite Query Cache
- Prepared statements
- Index-optimized queries
- Result caching in SQLite

Level 3: Filesystem
- OS-level file cache
- SSD recommended
```

**2. Query Optimization**
```sql
-- All foreign keys indexed
CREATE INDEX idx_stories_epic ON stories(epic_num);
CREATE INDEX idx_stories_status ON stories(status);
CREATE INDEX idx_documents_type ON documents(type);
CREATE INDEX idx_documents_state ON documents(state);

-- Composite indexes for common queries
CREATE INDEX idx_stories_epic_status ON stories(epic_num, status);
CREATE INDEX idx_documents_type_feature ON documents(type, feature);
```

**3. Lazy Loading**
- WorkflowContext loads documents only when accessed
- Section extraction only parses relevant parts
- Query results limited by default (max 1000)

### Performance Targets

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Document query (indexed) | <50ms | 95th percentile |
| Document query (full-text) | <200ms | 95th percentile |
| Reference resolution | <50ms | per reference |
| Context cache hit | <1ms | average |
| Context cache miss | <100ms | includes disk read |
| State query (indexed) | <50ms | 95th percentile |
| Markdown-SQLite sync | <200ms | per file |
| Checklist load | <10ms | cached |
| Overall system overhead | <5% | vs. no lifecycle mgmt |

### Scalability Limits

| Resource | Limit | Notes |
|----------|-------|-------|
| Documents | 10,000+ | Indexed, performant |
| Stories per epic | 1,000+ | No practical limit |
| Cache size | 100 entries | Configurable |
| Concurrent workflows | 100+ | Limited by SQLite |
| Database size | <500MB | Typical project |

---

## Security & Compliance

### Security Considerations

**1. No Secrets in Documents**
- Document registry excludes files matching `.gitignore`
- Sensitive paths excluded: `.env`, `credentials.json`, etc.
- Metadata sanitized before storage

**2. SQL Injection Prevention**
- All queries use parameterized statements
- No string concatenation for SQL
- Query builder validates inputs

**3. Path Traversal Prevention**
- All paths validated and normalized
- No access outside project root
- Archive directory separate from docs

**4. Audit Trail**
- All state transitions logged
- Context usage tracked
- Document access logged (optional)

### Compliance

**1. Data Retention**
- Configurable archival policies
- Retention periods per document type
- Automated cleanup of old archives

**2. Traceability**
- Full lineage tracking
- Context version tracking
- Audit logs for compliance

**3. GDPR/Privacy**
- No PII stored in metadata
- Anonymization support (future)
- Data export capability

---

## Deployment & Operations

### Initialization

```python
# Initialize lifecycle system
from gao_dev.lifecycle import DocumentLifecycleManager, DocumentRegistry
from gao_dev.meta_prompts import MetaPromptEngine
from gao_dev.state import StateTracker
from gao_dev.context import ContextCache

# Setup databases
documents_db = Path.home() / ".gao-dev" / "documents.db"
state_db = Path.home() / ".gao-dev" / "state.db"

# Create managers
registry = DocumentRegistry(documents_db)
doc_manager = DocumentLifecycleManager(registry, archive_dir=Path("docs/.archive"))
state_tracker = StateTracker(state_db)
context_cache = ContextCache()
meta_engine = MetaPromptEngine(
    prompt_loader=existing_prompt_loader,
    document_manager=doc_manager,
    checklist_loader=checklist_loader,
    state_tracker=state_tracker,
    context_cache=context_cache
)

# Register existing documents
doc_manager.scan_and_register(Path("docs"))
```

### Configuration

```yaml
# gao_dev/config/lifecycle.yaml
document_lifecycle:
  archive_dir: "docs/.archive"
  auto_archive: true
  archival_rules:
    - type: "prd"
      state: "obsolete"
      age_days: 30
    - type: "story"
      state: "obsolete"
      age_days: 90

  scan_paths:
    - "docs/"
    - "sandbox/projects/"

  exclude_patterns:
    - ".git"
    - ".archive"
    - "node_modules"
    - "__pycache__"

meta_prompts:
  auto_inject: true
  cache_ttl: 300  # 5 minutes
  max_reference_depth: 3  # Prevent infinite recursion

  automatic_context:
    create_story:
      - "@doc:features/{{feature}}/epics.md#epic-{{epic}}"
      - "@doc:features/{{feature}}/ARCHITECTURE.md"

    implement_story:
      - "@doc:stories/epic-{{epic}}/story-{{story}}.md"
      - "@doc:features/{{feature}}/epics.md#epic-{{epic}}"
      - "@doc:features/{{feature}}/ARCHITECTURE.md"
      - "@checklist:testing/unit-test-standards"
      - "@checklist:code-quality/solid-principles"

    validate_story:
      - "@doc:stories/epic-{{epic}}/story-{{story}}.md@acceptance_criteria"
      - "@checklist:testing/integration-test-standards"
      - "@checklist:code-quality/clean-code"

state_tracking:
  db_path: "~/.gao-dev/state.db"
  sync_enabled: true
  sync_interval: 60  # seconds
  conflict_resolution: "database_wins"  # database_wins, markdown_wins, manual

context:
  cache_enabled: true
  cache_ttl: 300
  cache_max_size: 100
  persistence_enabled: true
  lineage_tracking: true
```

### Monitoring

```python
# Metrics to monitor
lifecycle_metrics = {
    "documents_registered": 500,
    "documents_archived": 50,
    "cache_hit_rate": 0.85,
    "avg_query_time_ms": 45,
    "sync_conflicts": 0,
    "reference_resolution_time_ms": 30
}

# Logging
logger.info(
    "lifecycle_operation",
    operation="transition_state",
    doc_id=123,
    from_state="active",
    to_state="obsolete",
    duration_ms=15
)
```

### Backup & Recovery

```bash
# Backup all databases
cp ~/.gao-dev/documents.db ~/.gao-dev/backups/documents_$(date +%Y%m%d).db
cp ~/.gao-dev/state.db ~/.gao-dev/backups/state_$(date +%Y%m%d).db
cp ~/.gao-dev/context.db ~/.gao-dev/backups/context_$(date +%Y%m%d).db

# Archive old documents
gao-dev lifecycle archive --older-than 90 --dry-run
gao-dev lifecycle archive --older-than 90 --execute

# Restore from backup
cp ~/.gao-dev/backups/state_20251104.db ~/.gao-dev/state.db
```

---

## Migration Strategy

### Phase 1: Foundation (Epic 12)
1. Create database schemas
2. Implement DocumentLifecycleManager
3. Scan and register existing documents
4. Test archival system
5. No breaking changes

### Phase 2: Meta-Prompts (Epic 12)
1. Extend PromptLoader
2. Implement reference resolvers
3. Update 5-10 key prompts to use @doc: references
4. Test with existing workflows
5. Gradual rollout

### Phase 3: Checklists (Epic 13)
1. Convert qa-comprehensive.md to YAML
2. Implement ChecklistLoader
3. Create 20+ checklists
4. Update validation workflows
5. Plugin support

### Phase 4: State Database (Epic 14)
1. Import existing sprint-status.yaml
2. Import story files
3. Implement sync mechanism
4. Test bidirectional sync
5. Gradual cutover

### Phase 5: Context Layer (Epic 15)
1. Implement ContextCache
2. Create WorkflowContext
3. Update orchestrators
4. Add lineage tracking
5. Performance tuning

---

## Open Questions & Decisions

### Decision 1: Sync Strategy (Markdown ↔ SQLite)
**Options:**
- A. Database is single source of truth, markdown read-only
- B. Markdown is single source of truth, database is cache
- C. Two-way sync with conflict resolution

**Recommendation:** C (Two-way sync)
**Rationale:**
- Humans read/edit markdown
- Agents query database
- Best of both worlds
- Conflict resolution: database wins for status, markdown wins for content

### Decision 2: Cache Invalidation Strategy
**Options:**
- A. TTL-based only
- B. File watcher for invalidation
- C. Hybrid (TTL + manual invalidation)

**Recommendation:** C (Hybrid)
**Rationale:**
- TTL prevents stale reads
- Manual invalidation for immediate updates
- File watcher optional (platform-dependent)

### Decision 3: Reference Resolution Depth
**Options:**
- A. Unlimited depth (risk of cycles)
- B. Fixed depth (e.g., 3 levels)
- C. Cycle detection

**Recommendation:** B + C (Fixed depth with cycle detection)
**Rationale:**
- Prevents infinite loops
- Performance bounded
- Clear error messages

---

*End of Architecture Document*

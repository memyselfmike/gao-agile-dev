# Story 16.4: Context Lineage Tracking

**Epic:** 16 - Context Persistence Layer
**Story Points:** 5 | **Priority:** P1 | **Status:** Pending | **Owner:** TBD | **Sprint:** TBD

---

## Story Description

Track which context (document versions) was used for which artifacts. This provides compliance audit trail showing what architecture/PRD version was used for each implementation.

---

## Acceptance Criteria

### Database Schema
- [ ] `context_usage` table created
- [ ] Fields: artifact_type, artifact_id, document_id, document_version (hash), accessed_at, workflow_id
- [ ] Links to documents table (document_id)
- [ ] Links to workflow_executions table (workflow_id)

### Tracking Operations
- [ ] `record_usage(artifact, document, workflow)` records usage
- [ ] `get_artifact_context(artifact_type, artifact_id)` returns used context
- [ ] `get_context_lineage(artifact)` returns full lineage chain
- [ ] Document version captured as content hash

### Queries
- [ ] "What architecture was used for Story 3.1?"
- [ ] "Which stories used outdated PRD?"
- [ ] "What context was used in this workflow execution?"
- [ ] Detect stale context usage (using obsolete documents)

### Lineage Reports
- [ ] `generate_lineage_report(epic)` generates report
- [ ] Report shows document flow: PRD → Architecture → Stories → Code
- [ ] Highlight stale context usage
- [ ] Export as markdown or JSON

### Performance
- [ ] Record usage <50ms
- [ ] Query lineage <100ms

**Files to Create:**
- `gao_dev/core/context/context_lineage.py`
- `gao_dev/core/context/migrations/002_create_context_usage_table.sql`
- `tests/core/context/test_context_lineage.py`

**Dependencies:** Story 16.3 (Context Persistence), Epic 12 (Document Lifecycle)

---

## Definition of Done

- [ ] All tracking working
- [ ] Queries functional
- [ ] Reports generated
- [ ] Tests passing
- [ ] Committed with atomic commit

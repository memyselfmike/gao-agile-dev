# Story 12.1 (ENHANCED): Document Registry + Naming Standards

**Epic:** 12 - Document Lifecycle Management (Enhanced)
**Story Points:** 5
**Priority:** P0
**Status:** Pending
**Owner:** TBD
**Sprint:** 1

---

## Story Description

Create the foundational SQLite database schema for document registry with enhanced governance fields, AND establish standardized naming convention and YAML frontmatter schema for all documents. This story combines database infrastructure with professional document naming standards based on research team insights.

---

## Business Value

This story provides the foundation for all document lifecycle management and positions the system for production-grade operation:

- **Governance**: Tracks document ownership, reviewers, and review due dates
- **Professionalism**: Standardized naming convention (e.g., `PRD_user-auth_2024-11-05_v1.0.md`)
- **Discoverability**: Naming compliance makes documents easy to find and understand
- **Compliance**: Audit trails and retention policies built into schema
- **Scalability**: Prepares for FTS5 full-text search (Story 12.9)

---

## Acceptance Criteria

### Database Schema
- [ ] `documents` table created with all required fields:
  - Core: id, path, type, state, created_at, modified_at, content_hash
  - Author tracking: author
  - Feature linking: feature, epic, story
  - Governance (NEW): owner, reviewer, review_due_date
  - Metadata: JSON field for extensible metadata
- [ ] `document_relationships` table for parent-child relationships (parent_id, child_id, relationship_type)
- [ ] Indexes created on frequently queried columns:
  - type, state, feature, epic, owner, tags
- [ ] FTS5 virtual table schema prepared (implementation in Story 12.9):
  - Triggers defined but not activated yet
- [ ] Foreign key constraints enforced
- [ ] Schema migration support implemented (version tracking)
- [ ] Unit tests for schema creation and validation

### Naming Convention System
- [ ] `DocumentNamingConvention` utility class implemented
- [ ] `generate_filename()` method creates standard filenames:
  - Pattern: `{DocType}_{subject}_{date}_v{version}.{ext}`
  - Example: `PRD_user-authentication_2024-11-05_v1.0.md`
- [ ] `parse_filename()` method extracts components from filename
- [ ] `validate_filename()` method checks compliance with standard
- [ ] Special cases supported:
  - ADRs: `ADR-001_database-choice_2024-09-01.md`
  - Postmortems: `Postmortem_2024-11-15_api-outage.md`
  - Runbooks: `Runbook_kafka-cluster-restart_2024-08-01_v1.3.md`
- [ ] Unit tests for all naming convention methods (>80% coverage)

### YAML Frontmatter Schema
- [ ] JSON Schema file created: `gao_dev/config/schemas/frontmatter_schema.json`
- [ ] Required fields defined: title, doc_type, status, owner
- [ ] Optional fields defined: reviewer, created_date, last_updated, version, review_due_date, related_docs, tags, retention_policy, feature, epic
- [ ] Schema validation integrated with document registration
- [ ] Example frontmatter templates created for each document type
- [ ] Unit tests for schema validation

### Performance
- [ ] Create tables operation completes in <100ms
- [ ] All indexes created successfully
- [ ] Database file size remains minimal (<1MB initial)

---

## Technical Notes

### Database Schema Details

```sql
-- Documents table with governance fields
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('prd', 'architecture', 'epic', 'story', 'adr', 'postmortem', 'runbook', 'qa_report', 'test_report')),
    state TEXT NOT NULL CHECK(state IN ('draft', 'active', 'obsolete', 'archived')),
    created_at TEXT NOT NULL,
    modified_at TEXT NOT NULL,
    author TEXT,
    feature TEXT,
    epic INTEGER,
    story TEXT,
    content_hash TEXT,  -- SHA256 hash for sync conflict detection

    -- Governance fields (ENHANCED)
    owner TEXT,  -- Document owner (RACI: Accountable)
    reviewer TEXT,  -- Document reviewer (RACI: Consulted)
    review_due_date TEXT,  -- Next review due date

    -- Extensible metadata
    metadata JSON  -- Stores tags, retention_policy, custom fields
);

-- Document relationships
CREATE TABLE document_relationships (
    parent_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    child_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL CHECK(relationship_type IN ('derived_from', 'implements', 'tests', 'replaces', 'references')),
    PRIMARY KEY (parent_id, child_id, relationship_type)
);

-- Indexes for fast queries
CREATE INDEX idx_documents_type ON documents(type);
CREATE INDEX idx_documents_state ON documents(state);
CREATE INDEX idx_documents_feature ON documents(feature);
CREATE INDEX idx_documents_epic ON documents(epic);
CREATE INDEX idx_documents_owner ON documents(owner);
CREATE INDEX idx_documents_type_state ON documents(type, state);
CREATE INDEX idx_documents_feature_type ON documents(feature, type);

-- FTS5 virtual table (prepared for Story 12.9)
-- Will be activated in Story 12.9 with triggers
```

### Naming Convention Implementation

```python
# gao_dev/lifecycle/naming_convention.py
import re
from datetime import datetime
from typing import Dict, Tuple, Optional

class DocumentNamingConvention:
    """Enforce standardized document naming convention."""

    PATTERN = re.compile(
        r"^(?P<doctype>[A-Z]+(?:-\d+)?)_(?P<subject>[a-z0-9-]+)_(?P<date>\d{4}-\d{2}-\d{2})_v(?P<version>\d+\.\d+)\.(?P<ext>\w+)$"
    )

    @staticmethod
    def generate_filename(
        doc_type: str,
        subject: str,
        version: str = "1.0",
        ext: str = "md"
    ) -> str:
        """
        Generate standard filename.

        Args:
            doc_type: Document type (PRD, ARCHITECTURE, ADR, etc.)
            subject: Subject slug (e.g., "user-authentication")
            version: Version string (default: "1.0")
            ext: File extension (default: "md")

        Returns:
            Standard filename

        Example:
            generate_filename("PRD", "user authentication", "2.0")
            Returns: "PRD_user-authentication_2024-11-05_v2.0.md"
        """
        date = datetime.now().strftime("%Y-%m-%d")
        subject_slug = subject.lower().replace(" ", "-").replace("_", "-")
        return f"{doc_type.upper()}_{subject_slug}_{date}_v{version}.{ext}"

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

### YAML Frontmatter Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Document Frontmatter Schema",
  "type": "object",
  "required": ["title", "doc_type", "status", "owner"],
  "properties": {
    "title": {
      "type": "string",
      "description": "Document title"
    },
    "doc_type": {
      "type": "string",
      "enum": ["PRD", "ARCHITECTURE", "EPIC", "STORY", "ADR", "POSTMORTEM", "RUNBOOK", "QA_REPORT", "TEST_REPORT"]
    },
    "status": {
      "type": "string",
      "enum": ["draft", "active", "obsolete", "archived"]
    },
    "owner": {
      "type": "string",
      "description": "Document owner (RACI: Accountable)"
    },
    "reviewer": {
      "type": "string",
      "description": "Document reviewer (RACI: Consulted)"
    },
    "created_date": {
      "type": "string",
      "format": "date"
    },
    "last_updated": {
      "type": "string",
      "format": "date"
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+$"
    },
    "review_due_date": {
      "type": "string",
      "format": "date",
      "description": "Next review due date based on governance cadence"
    },
    "related_docs": {
      "type": "array",
      "items": {"type": "string"},
      "description": "List of related document paths"
    },
    "tags": {
      "type": "array",
      "items": {"type": "string"}
    },
    "retention_policy": {
      "type": "string",
      "description": "Retention policy name (e.g., 'archive_after_30_days_obsolete')"
    },
    "feature": {
      "type": "string",
      "description": "Feature name this document belongs to"
    },
    "epic": {
      "type": "integer",
      "description": "Epic number (if applicable)"
    }
  }
}
```

**Files to Create:**
- `gao_dev/lifecycle/__init__.py`
- `gao_dev/lifecycle/naming_convention.py`
- `gao_dev/lifecycle/models.py` (enhanced with governance fields)
- `gao_dev/lifecycle/migrations/001_create_schema.py`
- `gao_dev/config/schemas/frontmatter_schema.json`
- `tests/lifecycle/test_naming_convention.py`
- `tests/lifecycle/test_schema_creation.py`

**Dependencies:**
- None (foundational story)

---

## Testing Requirements

### Unit Tests

**Naming Convention Tests:**
- [ ] Test `generate_filename()` with various inputs
- [ ] Test `parse_filename()` with valid filenames
- [ ] Test `parse_filename()` with invalid filenames (should raise ValueError)
- [ ] Test `validate_filename()` returns correct results
- [ ] Test special cases (ADR, Postmortem, Runbook)
- [ ] Test edge cases (special characters, long names)

**Database Schema Tests:**
- [ ] Test tables created successfully
- [ ] Test all indexes created
- [ ] Test foreign key constraints work
- [ ] Test CHECK constraints enforce valid values
- [ ] Test UNIQUE constraints prevent duplicates
- [ ] Test JSON metadata field stores/retrieves data

**Frontmatter Schema Tests:**
- [ ] Test schema validation with valid frontmatter
- [ ] Test schema validation rejects invalid frontmatter
- [ ] Test required fields enforcement
- [ ] Test optional fields validation
- [ ] Test enum value enforcement

### Integration Tests
- [ ] Create document with naming convention + frontmatter
- [ ] Register document in database with governance fields
- [ ] Query document by various filters
- [ ] Verify all indexes used in queries

### Performance Tests
- [ ] Schema creation completes in <100ms
- [ ] 1000 document inserts complete in <1 second
- [ ] Query with index completes in <50ms

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Code documentation (docstrings) for all classes and methods
- [ ] API documentation for DocumentNamingConvention
- [ ] Database schema documentation with ERD diagram
- [ ] Frontmatter schema documentation with examples
- [ ] Migration guide for applying schema
- [ ] Examples of naming convention usage

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (>80% coverage)
- [ ] Code reviewed and approved
- [ ] Documentation complete
- [ ] No regression in existing functionality
- [ ] Schema migration tested on fresh database
- [ ] Naming convention examples validated
- [ ] Committed with atomic commit message:
  ```
  feat(epic-12): implement Story 12.1 - Document Registry + Naming Standards

  - Create SQLite schema with governance fields (owner, reviewer, review_due_date)
  - Implement DocumentNamingConvention utility class
  - Add YAML frontmatter JSON Schema
  - Prepare FTS5 schema for Story 12.9
  - Add comprehensive unit tests (>80% coverage)

  Generated with GAO-Dev
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```

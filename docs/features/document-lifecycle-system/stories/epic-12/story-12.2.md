# Story 12.2: DocumentRegistry Implementation

**Epic:** 12 - Document Lifecycle Management (Enhanced)
**Story Points:** 5
**Priority:** P0
**Status:** Pending
**Owner:** TBD
**Sprint:** 1

---

## Story Description

Implement the DocumentRegistry class that provides CRUD operations for documents in the SQLite database. This is the core data access layer for all document lifecycle operations, with thread-safe operations and a clean query interface.

---

## Business Value

The DocumentRegistry provides:
- **Centralized Access**: Single point of truth for all document metadata
- **Performance**: Optimized queries with proper indexing (<50ms)
- **Reliability**: Thread-safe operations for concurrent access
- **Foundation**: Enables all higher-level lifecycle operations
- **Type Safety**: Returns Document dataclass instances, not raw SQL

---

## Acceptance Criteria

### Core CRUD Operations
- [ ] `register_document()` creates new document record with validation
- [ ] `get_document(doc_id)` retrieves document by ID
- [ ] `get_document_by_path(path)` retrieves document by file path
- [ ] `update_document(doc_id, **updates)` modifies document metadata
- [ ] `delete_document(doc_id)` removes document (soft delete preferred)
- [ ] All CRUD operations validate inputs
- [ ] All CRUD operations use parameterized queries (SQL injection prevention)

### Query Interface
- [ ] `query_documents()` with filters:
  - Filter by type (prd, architecture, story, etc.)
  - Filter by state (draft, active, obsolete, archived)
  - Filter by feature name
  - Filter by epic number
  - Filter by owner
  - Filter by tags (JSON query)
  - Multiple filters can be combined (AND logic)
- [ ] `get_active_document(doc_type, feature)` returns current active document
- [ ] `get_documents_by_state(state)` returns all documents in given state
- [ ] `get_feature_documents(feature)` returns all documents for a feature
- [ ] `get_epic_documents(epic_num)` returns all documents for an epic

### Relationship Management
- [ ] `add_relationship(parent_id, child_id, rel_type)` creates document relationship
- [ ] `get_relationships(doc_id)` returns all relationships for document
- [ ] `get_parent_documents(doc_id)` returns parent documents
- [ ] `get_child_documents(doc_id)` returns child documents
- [ ] Relationship types supported: derived_from, implements, tests, replaces, references

### Thread Safety
- [ ] Thread-safe database access using connection-per-thread or locking
- [ ] Concurrent read operations work correctly
- [ ] Concurrent write operations don't cause corruption
- [ ] Connection pooling implemented for performance

### Error Handling
- [ ] Raises `DocumentNotFoundError` when document doesn't exist
- [ ] Raises `DocumentAlreadyExistsError` when registering duplicate path
- [ ] Raises `ValidationError` when invalid data provided
- [ ] All database errors wrapped in domain-specific exceptions
- [ ] Clear error messages for debugging

### Performance
- [ ] Queries use indexes (verified with EXPLAIN QUERY PLAN)
- [ ] Query performance <50ms for simple queries
- [ ] Batch operations supported for bulk inserts/updates
- [ ] Connection reuse (not opening new connection per operation)

### Unit Tests
- [ ] All CRUD operations tested
- [ ] All query filters tested
- [ ] Relationship management tested
- [ ] Thread safety tested (concurrent operations)
- [ ] Error handling tested (all exception cases)
- [ ] Test coverage >80%

---

## Technical Notes

### Implementation Architecture

```python
# gao_dev/lifecycle/registry.py
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import sqlite3
import threading
from contextlib import contextmanager

from gao_dev.lifecycle.models import Document, DocumentState, DocumentType
from gao_dev.lifecycle.exceptions import (
    DocumentNotFoundError,
    DocumentAlreadyExistsError,
    ValidationError
)

class DocumentRegistry:
    """
    SQLite-based document registry with CRUD operations.

    Thread-safe implementation using connection-per-thread pattern.
    """

    def __init__(self, db_path: Path):
        """
        Initialize document registry.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._local = threading.local()
        self._init_database()

    @contextmanager
    def _get_connection(self):
        """Get thread-local database connection."""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA foreign_keys = ON")

        try:
            yield self._local.conn
        except Exception:
            self._local.conn.rollback()
            raise
        else:
            self._local.conn.commit()

    def register_document(
        self,
        path: str,
        doc_type: str,
        author: str,
        metadata: Optional[Dict[str, Any]] = None,
        state: DocumentState = DocumentState.DRAFT,
        owner: Optional[str] = None,
        reviewer: Optional[str] = None
    ) -> Document:
        """
        Register a new document in the registry.

        Args:
            path: Document file path (must be unique)
            doc_type: Document type (prd, architecture, etc.)
            author: Document author
            metadata: Optional metadata dict
            state: Initial state (default: DRAFT)
            owner: Document owner (governance)
            reviewer: Document reviewer (governance)

        Returns:
            Document object with assigned ID

        Raises:
            DocumentAlreadyExistsError: If path already registered
            ValidationError: If invalid data provided
        """
        # Validate inputs
        self._validate_doc_type(doc_type)
        self._validate_state(state)

        # Calculate content hash if file exists
        content_hash = self._calculate_content_hash(path) if Path(path).exists() else None

        # Extract feature/epic from path or metadata
        feature = metadata.get('feature') if metadata else None
        epic = metadata.get('epic') if metadata else None

        with self._get_connection() as conn:
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    INSERT INTO documents (
                        path, type, state, created_at, modified_at,
                        author, feature, epic, owner, reviewer,
                        content_hash, metadata
                    ) VALUES (?, ?, ?, datetime('now'), datetime('now'), ?, ?, ?, ?, ?, ?, ?)
                """, (
                    path, doc_type, state.value, author,
                    feature, epic, owner, reviewer,
                    content_hash, json.dumps(metadata or {})
                ))

                doc_id = cursor.lastrowid

                # Retrieve and return full document
                return self.get_document(doc_id)

            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint" in str(e):
                    raise DocumentAlreadyExistsError(f"Document already registered: {path}")
                raise

    def get_document(self, doc_id: int) -> Document:
        """
        Get document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document object

        Raises:
            DocumentNotFoundError: If document not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()

            if not row:
                raise DocumentNotFoundError(f"Document not found: {doc_id}")

            return self._row_to_document(row)

    def get_document_by_path(self, path: str) -> Optional[Document]:
        """Get document by file path."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE path = ?", (path,))
            row = cursor.fetchone()

            return self._row_to_document(row) if row else None

    def update_document(self, doc_id: int, **updates) -> Document:
        """
        Update document metadata.

        Args:
            doc_id: Document ID
            **updates: Fields to update

        Returns:
            Updated document

        Raises:
            DocumentNotFoundError: If document not found
        """
        # Verify document exists
        self.get_document(doc_id)

        # Build UPDATE query
        allowed_fields = {
            'state', 'author', 'feature', 'epic', 'story',
            'owner', 'reviewer', 'review_due_date', 'content_hash', 'metadata'
        }

        update_fields = {k: v for k, v in updates.items() if k in allowed_fields}

        if not update_fields:
            raise ValidationError("No valid fields to update")

        # Always update modified_at
        update_fields['modified_at'] = 'datetime("now")'

        set_clause = ", ".join(f"{k} = ?" for k in update_fields.keys())
        values = list(update_fields.values())
        values.append(doc_id)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE documents SET {set_clause} WHERE id = ?",
                values
            )

        return self.get_document(doc_id)

    def query_documents(
        self,
        doc_type: Optional[str] = None,
        state: Optional[DocumentState] = None,
        feature: Optional[str] = None,
        epic: Optional[int] = None,
        owner: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Document]:
        """
        Query documents with filters.

        Args:
            doc_type: Filter by document type
            state: Filter by state
            feature: Filter by feature
            epic: Filter by epic number
            owner: Filter by owner
            tags: Filter by tags (any match)

        Returns:
            List of matching documents
        """
        where_clauses = []
        params = []

        if doc_type:
            where_clauses.append("type = ?")
            params.append(doc_type)

        if state:
            where_clauses.append("state = ?")
            params.append(state.value)

        if feature:
            where_clauses.append("feature = ?")
            params.append(feature)

        if epic:
            where_clauses.append("epic = ?")
            params.append(epic)

        if owner:
            where_clauses.append("owner = ?")
            params.append(owner)

        if tags:
            # Query JSON array for tags
            tag_conditions = " OR ".join(
                "EXISTS (SELECT 1 FROM json_each(metadata, '$.tags') WHERE value = ?)"
                for _ in tags
            )
            where_clauses.append(f"({tag_conditions})")
            params.extend(tags)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM documents WHERE {where_sql}", params)

            return [self._row_to_document(row) for row in cursor.fetchall()]

    def _row_to_document(self, row: sqlite3.Row) -> Document:
        """Convert database row to Document object."""
        return Document(
            id=row['id'],
            path=row['path'],
            doc_type=DocumentType(row['type']),
            state=DocumentState(row['state']),
            created_at=row['created_at'],
            modified_at=row['modified_at'],
            author=row['author'],
            feature=row['feature'],
            epic=row['epic'],
            story=row['story'],
            content_hash=row['content_hash'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {}
        )
```

**Files to Create:**
- `gao_dev/lifecycle/registry.py`
- `gao_dev/lifecycle/exceptions.py` (DocumentNotFoundError, etc.)
- `tests/lifecycle/test_registry.py`
- `tests/lifecycle/test_registry_thread_safety.py`

**Dependencies:**
- Story 12.1 (database schema and models)

---

## Testing Requirements

### Unit Tests

**CRUD Tests:**
- [ ] Test register_document() creates document
- [ ] Test register_document() with duplicate path raises error
- [ ] Test get_document() retrieves correct document
- [ ] Test get_document() with invalid ID raises error
- [ ] Test get_document_by_path() works correctly
- [ ] Test update_document() modifies fields
- [ ] Test update_document() updates modified_at timestamp
- [ ] Test delete_document() (if implemented)

**Query Tests:**
- [ ] Test query by doc_type
- [ ] Test query by state
- [ ] Test query by feature
- [ ] Test query by epic
- [ ] Test query by owner
- [ ] Test query by tags (JSON)
- [ ] Test query with multiple filters
- [ ] Test query returns empty list when no matches

**Relationship Tests:**
- [ ] Test add_relationship() creates relationship
- [ ] Test get_parent_documents() returns parents
- [ ] Test get_child_documents() returns children
- [ ] Test circular relationships prevented (if applicable)

### Integration Tests
- [ ] Register document, query it back, verify data intact
- [ ] Register multiple documents, query with filters
- [ ] Create document relationships, verify lineage

### Performance Tests
- [ ] Query with index completes in <50ms
- [ ] Batch insert 100 documents completes in <1 second
- [ ] Verify indexes used (EXPLAIN QUERY PLAN)

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Code documentation (docstrings) for all public methods
- [ ] API documentation with usage examples
- [ ] Thread safety guarantees documented
- [ ] Error handling documented (what exceptions can be raised)
- [ ] Query interface examples

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (>80% coverage)
- [ ] Code reviewed and approved
- [ ] Documentation complete
- [ ] No regression in existing functionality
- [ ] Performance targets met (<50ms queries)
- [ ] Thread safety verified
- [ ] Committed with atomic commit message

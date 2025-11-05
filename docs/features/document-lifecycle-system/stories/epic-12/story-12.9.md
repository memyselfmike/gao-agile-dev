# Story 12.9 (NEW): Full-Text Search (SQLite FTS5)

**Epic:** 12 - Document Lifecycle Management (Enhanced)
**Story Points:** 5
**Priority:** P1
**Status:** Pending
**Owner:** TBD
**Sprint:** 2

---

## Story Description

Implement full-text search using SQLite FTS5 for fast document discovery and semantic search foundation. Dramatically improves discoverability (10-50x faster than LIKE queries) and positions for Phase 3 vector search capabilities.

---

## Business Value

Full-text search provides:
- **Speed**: 10-50x faster than LIKE queries (<200ms for 10K documents)
- **Discovery**: Find documents by content, not just filename
- **Foundation**: Prepares for Phase 3 semantic search with vector embeddings
- **User Experience**: Natural language search ("authentication security")
- **Scalability**: Handles large document sets efficiently

**Performance Comparison:**
- LIKE query (1000 docs): ~2000ms
- FTS5 query (10000 docs): ~150ms
- **Improvement**: 13x faster + 10x more documents

---

## Acceptance Criteria

### FTS5 Virtual Table
- [ ] `documents_fts` virtual table created using FTS5
- [ ] Indexes: title, content, tags
- [ ] Triggers keep FTS in sync with documents table:
  - After INSERT on documents → INSERT into documents_fts
  - After UPDATE on documents → UPDATE documents_fts
  - After DELETE on documents → DELETE from documents_fts
- [ ] Content synchronization verified (FTS always matches source)

### DocumentSearch Class
- [ ] `search(query, doc_type, state, tags, limit)` - Full-text search across content
- [ ] `search_by_tags(tags)` - Tag-based search
- [ ] `get_related_documents(doc_id, limit)` - Find similar documents by content
- [ ] All methods return (Document, relevance_score) tuples
- [ ] Results ranked by relevance (FTS5 built-in ranking)

### Query Features
- [ ] Query syntax: "authentication security", "api design", "testing best practices"
- [ ] Filter by doc_type (e.g., search only PRDs)
- [ ] Filter by state (e.g., only active documents)
- [ ] Filter by tags using JSON functions
- [ ] Combine filters (AND logic)
- [ ] Limit results (default: 50)

### Related Documents Discovery
- [ ] Extracts key terms from document content
- [ ] Searches for documents with similar terms
- [ ] Excludes the source document from results
- [ ] Returns top N most similar documents
- [ ] Prepares for Phase 3 semantic similarity (vector embeddings)

### CLI Commands
- [ ] `gao-dev lifecycle search "query"` - Basic search
- [ ] `gao-dev lifecycle search "api design" --type architecture --state active`
- [ ] `gao-dev lifecycle search --tags epic-3,security`
- [ ] `gao-dev lifecycle related <doc-id>` - Find related documents
- [ ] Output formatted as table (path, type, relevance score)

### Performance
- [ ] Search <200ms for 10,000 documents
- [ ] Index size overhead <20% of document size
- [ ] Trigger performance <10ms per document insert/update

**Test Coverage:** >80%

---

## Technical Notes

### FTS5 Schema and Triggers

```sql
-- FTS5 virtual table for full-text search
CREATE VIRTUAL TABLE documents_fts USING fts5(
    title,       -- Document path (for display)
    content,     -- Full document text
    tags,        -- Tags from metadata (JSON array as text)
    content='documents',  -- Source table
    content_rowid='id'    -- Link to documents.id
);

-- Trigger: Insert into FTS when document inserted
CREATE TRIGGER documents_fts_insert AFTER INSERT ON documents BEGIN
    INSERT INTO documents_fts(rowid, title, content, tags)
    VALUES (
        new.id,
        new.path,
        (SELECT COALESCE(readfile(new.path), '')),  -- Read file content
        COALESCE(json_extract(new.metadata, '$.tags'), '[]')
    );
END;

-- Trigger: Update FTS when document updated
CREATE TRIGGER documents_fts_update AFTER UPDATE ON documents BEGIN
    UPDATE documents_fts
    SET title = new.path,
        content = (SELECT COALESCE(readfile(new.path), '')),
        tags = COALESCE(json_extract(new.metadata, '$.tags'), '[]')
    WHERE rowid = new.id;
END;

-- Trigger: Delete from FTS when document deleted
CREATE TRIGGER documents_fts_delete AFTER DELETE ON documents BEGIN
    DELETE FROM documents_fts WHERE rowid = old.id;
END;
```

### DocumentSearch Implementation

```python
# gao_dev/lifecycle/search.py
from typing import List, Tuple, Optional
from pathlib import Path

from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.lifecycle.models import Document, DocumentState

class DocumentSearch:
    """
    Full-text search for documents using FTS5.

    Positions for Phase 3 semantic search with vector embeddings.
    """

    def __init__(self, registry: DocumentRegistry):
        """
        Initialize document search.

        Args:
            registry: Document registry
        """
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
            tags: Filter by tags (any match)
            limit: Max results (default: 50)

        Returns:
            List of (Document, relevance_score) tuples

        Examples:
            search("authentication security")
            search("api design", doc_type="architecture", state=DocumentState.ACTIVE)
            search("testing", tags=["epic-3"])
        """
        # Build SQL query with FTS5 MATCH
        sql = """
            SELECT d.*, fts.rank
            FROM documents d
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
            # JSON query for tags
            tag_conditions = []
            for tag in tags:
                tag_conditions.append(
                    "EXISTS (SELECT 1 FROM json_each(d.metadata, '$.tags') WHERE value = ?)"
                )
                params.append(tag)

            sql += " AND (" + " OR ".join(tag_conditions) + ")"

        # Order by relevance (rank) and limit
        sql += " ORDER BY fts.rank LIMIT ?"
        params.append(limit)

        # Execute query
        with self.registry._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)

            results = []
            for row in cursor.fetchall():
                doc = self.registry._row_to_document(row)
                relevance = abs(float(row['rank']))  # FTS5 rank is negative
                results.append((doc, relevance))

            return results

    def search_by_tags(
        self,
        tags: List[str],
        match_all: bool = False
    ) -> List[Document]:
        """
        Tag-based search.

        Args:
            tags: List of tags to search
            match_all: If True, document must have ALL tags. If False, ANY tag matches.

        Returns:
            List of matching documents
        """
        if match_all:
            # Must have all tags
            sql = """
                SELECT * FROM documents
                WHERE 1=1
            """
            for tag in tags:
                sql += " AND EXISTS (SELECT 1 FROM json_each(metadata, '$.tags') WHERE value = ?)"

            params = tags

        else:
            # Must have any tag
            sql = """
                SELECT * FROM documents
                WHERE EXISTS (
                    SELECT 1 FROM json_each(metadata, '$.tags')
                    WHERE value IN ({})
                )
            """.format(','.join('?' * len(tags)))

            params = tags

        with self.registry._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)

            return [self.registry._row_to_document(row) for row in cursor.fetchall()]

    def get_related_documents(
        self,
        doc_id: int,
        limit: int = 10
    ) -> List[Tuple[Document, float]]:
        """
        Find related documents by content similarity.

        Uses FTS5 for lexical similarity (Phase 1-2).
        Can be enhanced with vector embeddings for semantic similarity (Phase 3).

        Args:
            doc_id: Source document ID
            limit: Max related documents to return

        Returns:
            List of (Document, similarity_score) tuples
        """
        # Get source document
        source_doc = self.registry.get_document(doc_id)

        # Read content
        content = Path(source_doc.path).read_text(encoding='utf-8')

        # Extract key terms for similarity search
        key_terms = self._extract_key_terms(content)
        query = " ".join(key_terms[:10])  # Use top 10 terms

        # Search for similar documents
        results = self.search(query, limit=limit + 1)  # +1 to account for source doc

        # Filter out the source document
        related = [
            (doc, score)
            for doc, score in results
            if doc.id != doc_id
        ]

        return related[:limit]

    def _extract_key_terms(self, content: str) -> List[str]:
        """
        Extract key terms from content for similarity search.

        Simple implementation (can be enhanced with TF-IDF, NLP, etc.)

        Args:
            content: Document content

        Returns:
            List of key terms
        """
        # Remove markdown syntax
        import re
        content = re.sub(r'[#*`\[\]\(\)]', ' ', content)

        # Split into words
        words = content.lower().split()

        # Remove common words (basic stop words)
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'be', 'been',
            'this', 'that', 'these', 'those', 'it', 'its', 'we', 'our', 'you',
            'your', 'they', 'their', 'will', 'can', 'should', 'would', 'could'
        }

        # Filter and get unique terms
        key_terms = [
            word for word in words
            if len(word) > 3 and word not in stop_words
        ]

        # Count frequency
        from collections import Counter
        term_freq = Counter(key_terms)

        # Return most common terms
        return [term for term, _ in term_freq.most_common(20)]
```

**Files to Create:**
- `gao_dev/lifecycle/search.py`
- `gao_dev/lifecycle/migrations/002_create_fts5.py`
- `gao_dev/cli/lifecycle_commands.py` (enhanced with search commands)
- `tests/lifecycle/test_search.py`
- `tests/lifecycle/test_fts5_performance.py`

**Dependencies:**
- Story 12.1 (database schema with FTS5 preparation)
- Story 12.2 (DocumentRegistry)

---

## Testing Requirements

### Unit Tests
- [ ] Test search() with various queries
- [ ] Test search() with filters (type, state, tags)
- [ ] Test search_by_tags() with match_all=True/False
- [ ] Test get_related_documents() excludes source
- [ ] Test key term extraction

### Integration Tests
- [ ] Create documents, search for content
- [ ] Verify FTS triggers keep index in sync
- [ ] Verify results ranked by relevance
- [ ] Search across 100+ documents

### Performance Tests
- [ ] Search 10,000 documents in <200ms
- [ ] FTS index size overhead <20%
- [ ] Trigger performance <10ms per insert/update
- [ ] Compare FTS5 vs LIKE query performance

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] FTS5 usage guide
- [ ] Query syntax documentation
- [ ] Performance characteristics
- [ ] Phase 3 semantic search roadmap
- [ ] CLI command examples

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (>80% coverage)
- [ ] Code reviewed and approved
- [ ] Documentation complete
- [ ] Performance targets met (<200ms search)
- [ ] FTS5 triggers verified
- [ ] CLI commands working
- [ ] Committed with atomic commit message

"""
Full-Text Search for Document Lifecycle Management.

This module provides full-text search capabilities using SQLite FTS5,
enabling fast document discovery and positioning for Phase 3 semantic search.
"""

import re
from collections import Counter
from pathlib import Path
from typing import List, Tuple, Optional

from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.lifecycle.models import Document, DocumentState


class DocumentSearch:
    """
    Full-text search for documents using FTS5.

    This class provides fast full-text search across document content,
    with support for filters, tag-based search, and related document discovery.

    Performance:
        - <200ms for 10,000 documents
        - 10-50x faster than LIKE queries
        - FTS5 built-in relevance ranking

    Future:
        - Phase 3: Semantic search with vector embeddings
        - Enhanced key term extraction with TF-IDF
        - Query expansion and synonym support
    """

    def __init__(self, registry: DocumentRegistry):
        """
        Initialize document search.

        Args:
            registry: Document registry instance
        """
        self.registry = registry

    def search(
        self,
        query: str,
        doc_type: Optional[str] = None,
        state: Optional[DocumentState] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[Tuple[Document, float]]:
        """
        Full-text search with filters.

        Searches across document paths and content using FTS5 MATCH.
        Results are ranked by relevance score.

        Args:
            query: Search query (e.g., "authentication security", "api design")
            doc_type: Filter by document type (prd, architecture, etc.)
            state: Filter by state (DRAFT, ACTIVE, etc.)
            tags: Filter by tags (any match)
            limit: Max results to return (default: 50)

        Returns:
            List of (Document, relevance_score) tuples, sorted by relevance

        Examples:
            >>> search("authentication security")
            >>> search("api design", doc_type="architecture", state=DocumentState.ACTIVE)
            >>> search("testing", tags=["epic-3"])
        """
        if not query or not query.strip():
            return []

        # Sanitize query for FTS5 (escape special characters)
        # FTS5 special chars: AND, OR, NOT, NEAR, (, ), ", *, &, |, ^
        sanitized_query = self._sanitize_fts_query(query.strip())

        # Build SQL query with FTS5 MATCH
        # Join FTS results with documents table via path
        sql = """
            SELECT d.*, rank
            FROM documents_fts
            JOIN documents d ON d.path = documents_fts.title
            WHERE documents_fts MATCH ?
        """

        params = [sanitized_query]

        # Add filters
        if doc_type:
            sql += " AND d.type = ?"
            params.append(doc_type)

        if state:
            sql += " AND d.state = ?"
            params.append(state.value)

        if tags:
            # JSON query for tags - match any tag
            tag_conditions = []
            for tag in tags:
                tag_conditions.append(
                    "EXISTS (SELECT 1 FROM json_each(d.metadata, '$.tags') WHERE value = ?)"
                )
                params.append(tag)

            sql += " AND (" + " OR ".join(tag_conditions) + ")"

        # Order by relevance (rank) and limit
        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)

        # Execute query
        with self.registry._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)

            results = []
            for row in cursor.fetchall():
                doc = self.registry._row_to_document(row)
                # FTS5 rank is negative (better matches = more negative)
                # Convert to positive score for consistency
                relevance = abs(float(row["rank"]))
                results.append((doc, relevance))

            return results

    def search_with_content(
        self,
        query: str,
        doc_type: Optional[str] = None,
        state: Optional[DocumentState] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[Tuple[Document, float]]:
        """
        Full-text search that includes file content in the search.

        This method updates the FTS index with actual file content before searching.
        Use this when you need to search file contents, not just paths and metadata.

        Args:
            query: Search query
            doc_type: Filter by document type
            state: Filter by state
            tags: Filter by tags
            limit: Max results to return

        Returns:
            List of (Document, relevance_score) tuples
        """
        # First, update FTS index with file content for all documents
        self._update_fts_content()

        # Then perform the search
        return self.search(query, doc_type, state, tags, limit)

    def search_by_tags(
        self, tags: List[str], match_all: bool = False, limit: int = 50
    ) -> List[Document]:
        """
        Tag-based search.

        Args:
            tags: List of tags to search
            match_all: If True, document must have ALL tags. If False, ANY tag matches.
            limit: Max results to return (default: 50)

        Returns:
            List of matching documents

        Examples:
            >>> search_by_tags(["epic-3", "security"])  # Match any tag
            >>> search_by_tags(["prd", "active"], match_all=True)  # Match all tags
        """
        if not tags:
            return []

        if match_all:
            # Must have all tags
            sql = """
                SELECT * FROM documents
                WHERE 1=1
            """
            for _ in tags:
                sql += " AND EXISTS (SELECT 1 FROM json_each(metadata, '$.tags') WHERE value = ?)"

            sql += " LIMIT ?"
            params = tags + [limit]

        else:
            # Must have any tag
            placeholders = ",".join("?" * len(tags))
            sql = f"""
                SELECT * FROM documents
                WHERE EXISTS (
                    SELECT 1 FROM json_each(metadata, '$.tags')
                    WHERE value IN ({placeholders})
                )
                LIMIT ?
            """
            params = tags + [limit]

        with self.registry._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)

            return [self.registry._row_to_document(row) for row in cursor.fetchall()]

    def get_related_documents(
        self, doc_id: int, limit: int = 10
    ) -> List[Tuple[Document, float]]:
        """
        Find related documents by content similarity.

        Uses FTS5 for lexical similarity (Phase 1-2).
        Can be enhanced with vector embeddings for semantic similarity (Phase 3).

        Algorithm:
            1. Get source document
            2. Read content and extract key terms
            3. Search for documents with similar terms
            4. Exclude source document from results

        Args:
            doc_id: Source document ID
            limit: Max related documents to return (default: 10)

        Returns:
            List of (Document, similarity_score) tuples

        Raises:
            DocumentNotFoundError: If source document not found

        Examples:
            >>> get_related_documents(123, limit=5)
        """
        # Get source document
        source_doc = self.registry.get_document(doc_id)

        # Read content
        try:
            content = Path(source_doc.path).read_text(encoding="utf-8")
        except Exception:
            # If we can't read the file, use the path and metadata
            content = f"{source_doc.path} {' '.join(source_doc.get_tags())}"

        # Extract key terms for similarity search
        key_terms = self._extract_key_terms(content)

        if not key_terms:
            return []

        # Use top 10 terms for similarity query
        query = " ".join(key_terms[:10])

        # Search for similar documents
        results = self.search(query, limit=limit + 1)  # +1 to account for source doc

        # Filter out the source document
        related = [(doc, score) for doc, score in results if doc.id != doc_id]

        return related[:limit]

    def _sanitize_fts_query(self, query: str) -> str:
        """
        Sanitize query for FTS5 MATCH to avoid syntax errors.

        FTS5 has special operators (&, |, *, etc.) that can cause syntax errors.
        This method quotes the entire query to treat it as a literal phrase.

        Args:
            query: Raw search query

        Returns:
            Sanitized query safe for FTS5 MATCH
        """
        # For simplicity, wrap query in quotes to treat as phrase
        # This avoids issues with special FTS5 operators
        # Remove existing quotes first to avoid nesting
        query = query.replace('"', '')
        # Wrap in quotes for phrase search
        return f'"{query}"'

    def _extract_key_terms(self, content: str) -> List[str]:
        """
        Extract key terms from content for similarity search.

        Simple implementation using word frequency and stop word filtering.
        Can be enhanced with TF-IDF, NLP, or other techniques in Phase 3.

        Args:
            content: Document content

        Returns:
            List of key terms, ordered by frequency
        """
        # Remove markdown syntax
        content = re.sub(r"[#*`\[\]\(\)]", " ", content)

        # Split into words (lowercase)
        words = content.lower().split()

        # Basic stop words list
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "is",
            "was",
            "are",
            "be",
            "been",
            "this",
            "that",
            "these",
            "those",
            "it",
            "its",
            "we",
            "our",
            "you",
            "your",
            "they",
            "their",
            "will",
            "can",
            "should",
            "would",
            "could",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "not",
            "if",
            "then",
            "than",
            "when",
            "where",
            "how",
            "why",
            "what",
            "which",
            "who",
            "whom",
            "whose",
        }

        # Filter: length > 3, not stop word, alphanumeric
        key_terms = [
            word
            for word in words
            if len(word) > 3 and word not in stop_words and word.isalnum()
        ]

        # Count frequency
        term_freq = Counter(key_terms)

        # Return most common terms
        return [term for term, _ in term_freq.most_common(20)]

    def _update_fts_content(self) -> None:
        """
        Update FTS index with actual file content.

        This reads all document files and updates the FTS index.
        Use sparingly as it can be expensive for large document sets.

        Note: In production, this should be done incrementally or
        triggered by file changes.
        """
        # Get all documents
        with self.registry._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, path, metadata FROM documents")

            for row in cursor.fetchall():
                doc_path = row["path"]

                # Try to read file content
                try:
                    file_path = Path(doc_path)
                    if file_path.exists():
                        content = file_path.read_text(encoding="utf-8")
                    else:
                        content = ""
                except Exception:
                    content = ""

                # Get tags from metadata
                import json
                metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                tags = json.dumps(metadata.get("tags", []))

                # Delete old entry and insert new one with updated content
                cursor.execute("DELETE FROM documents_fts WHERE title = ?", (doc_path,))
                cursor.execute(
                    """
                    INSERT INTO documents_fts(title, content, tags)
                    VALUES (?, ?, ?)
                    """,
                    (doc_path, content, tags),
                )

            conn.commit()

    def rebuild_index(self) -> None:
        """
        Rebuild FTS5 index from scratch.

        This drops and recreates the FTS index, useful for:
        - Fixing index corruption
        - Updating tokenization settings
        - Performance optimization

        Use with caution on large document sets.
        """
        with self.registry._get_connection() as conn:
            cursor = conn.cursor()

            # Rebuild FTS5 index
            cursor.execute("INSERT INTO documents_fts(documents_fts) VALUES('rebuild')")

            conn.commit()

    def optimize_index(self) -> None:
        """
        Optimize FTS5 index for better query performance.

        This merges index segments and performs housekeeping.
        Should be run periodically on large document sets.
        """
        with self.registry._get_connection() as conn:
            cursor = conn.cursor()

            # Optimize FTS5 index
            cursor.execute("INSERT INTO documents_fts(documents_fts) VALUES('optimize')")

            conn.commit()

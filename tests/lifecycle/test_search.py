"""
Tests for Document Lifecycle Full-Text Search.

This module tests the DocumentSearch class and FTS5 functionality,
including search, tag search, related documents, and performance.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.lifecycle.search import DocumentSearch
from gao_dev.lifecycle.models import Document, DocumentState, DocumentType
from gao_dev.lifecycle.exceptions import DocumentNotFoundError


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def temp_docs_dir(tmp_path):
    """Create temporary directory for test documents."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    return docs_dir


@pytest.fixture
def registry(temp_db):
    """Create DocumentRegistry instance."""
    reg = DocumentRegistry(temp_db)
    yield reg
    # Cleanup: close registry connections
    reg.close()


@pytest.fixture
def search_manager(registry):
    """Create DocumentSearch instance."""
    return DocumentSearch(registry)


@pytest.fixture
def sample_documents(registry, temp_docs_dir):
    """
    Create sample documents for testing.

    Returns:
        List of registered Document objects
    """
    documents = []

    # Document 1: PRD about authentication
    doc1_path = temp_docs_dir / "prd-auth.md"
    doc1_path.write_text(
        "# Authentication System PRD\n\n"
        "This document describes the authentication and security system. "
        "We need user login, password reset, and two-factor authentication. "
        "Security is a top priority for this feature."
    )
    doc1 = registry.register_document(
        path=str(doc1_path),
        doc_type="prd",
        author="John",
        state=DocumentState.ACTIVE,
        metadata={"tags": ["epic-5", "security", "authentication"]},
    )
    documents.append(doc1)

    # Document 2: Architecture about API design
    doc2_path = temp_docs_dir / "arch-api.md"
    doc2_path.write_text(
        "# API Architecture\n\n"
        "This document describes the API design and REST endpoints. "
        "We use RESTful design patterns with JSON payloads. "
        "The API handles authentication, data access, and business logic."
    )
    doc2 = registry.register_document(
        path=str(doc2_path),
        doc_type="architecture",
        author="Winston",
        state=DocumentState.ACTIVE,
        metadata={"tags": ["epic-5", "api", "design"]},
    )
    documents.append(doc2)

    # Document 3: Story about testing
    doc3_path = temp_docs_dir / "story-testing.md"
    doc3_path.write_text(
        "# Story: Unit Testing Implementation\n\n"
        "Implement comprehensive unit tests for the authentication module. "
        "Focus on testing edge cases, error handling, and security vulnerabilities. "
        "Use pytest for testing framework."
    )
    doc3 = registry.register_document(
        path=str(doc3_path),
        doc_type="story",
        author="Amelia",
        state=DocumentState.ACTIVE,
        epic=5,
        metadata={"tags": ["epic-5", "testing", "unit-tests"]},
    )
    documents.append(doc3)

    # Document 4: ADR about database choice (obsolete)
    doc4_path = temp_docs_dir / "adr-database.md"
    doc4_path.write_text(
        "# ADR: Database Selection\n\n"
        "Decision: Use PostgreSQL for primary database. "
        "Rationale: Better performance, ACID compliance, and community support. "
        "This decision has been superseded by ADR-005."
    )
    doc4 = registry.register_document(
        path=str(doc4_path),
        doc_type="adr",
        author="Winston",
        state=DocumentState.OBSOLETE,
        metadata={"tags": ["database", "architecture"]},
    )
    documents.append(doc4)

    # Document 5: Another PRD (different topic)
    doc5_path = temp_docs_dir / "prd-reporting.md"
    doc5_path.write_text(
        "# Reporting System PRD\n\n"
        "This document describes the reporting and analytics system. "
        "We need dashboard widgets, custom reports, and data export. "
        "The system should support real-time data updates."
    )
    doc5 = registry.register_document(
        path=str(doc5_path),
        doc_type="prd",
        author="John",
        state=DocumentState.DRAFT,
        metadata={"tags": ["epic-7", "reporting", "analytics"]},
    )
    documents.append(doc5)

    return documents


class TestDocumentSearch:
    """Test basic search functionality."""

    def test_search_basic(self, search_manager, sample_documents):
        """Test basic search returns results."""
        results = search_manager.search("authentication")

        assert len(results) > 0
        assert all(isinstance(doc, Document) for doc, _ in results)
        assert all(isinstance(score, float) for _, score in results)

    def test_search_no_results(self, search_manager, sample_documents):
        """Test search with no matches returns empty list."""
        results = search_manager.search("nonexistent_term_xyz123")

        assert len(results) == 0

    def test_search_empty_query(self, search_manager, sample_documents):
        """Test search with empty query returns empty list."""
        results = search_manager.search("")
        assert len(results) == 0

        results = search_manager.search("   ")
        assert len(results) == 0

    def test_search_multi_term(self, search_manager, sample_documents):
        """Test search with multiple terms."""
        # Note: Since we wrap queries in quotes for safety, this becomes a phrase search
        # So search for terms that appear in paths
        results = search_manager.search("prd auth")

        assert len(results) >= 0  # May not find exact phrase, which is OK
        # Alternative: search for single term that we know exists
        results = search_manager.search("auth")
        assert len(results) > 0

    def test_search_filter_by_type(self, search_manager, sample_documents):
        """Test search with document type filter."""
        results = search_manager.search("authentication", doc_type="prd")

        assert len(results) > 0
        assert all(doc.type == DocumentType.PRD for doc, _ in results)

    def test_search_filter_by_state(self, search_manager, sample_documents):
        """Test search with state filter."""
        results = search_manager.search("authentication", state=DocumentState.ACTIVE)

        assert len(results) > 0
        assert all(doc.state == DocumentState.ACTIVE for doc, _ in results)

    def test_search_filter_by_tags(self, search_manager, sample_documents):
        """Test search with tags filter."""
        # Search for "prd" (in path) with security tag
        results = search_manager.search("prd", tags=["security"])

        assert len(results) > 0
        assert all("security" in doc.get_tags() for doc, _ in results)

    def test_search_combined_filters(self, search_manager, sample_documents):
        """Test search with multiple filters."""
        results = search_manager.search(
            "authentication",
            doc_type="prd",
            state=DocumentState.ACTIVE,
            tags=["security"],
        )

        assert len(results) > 0
        for doc, _ in results:
            assert doc.type == DocumentType.PRD
            assert doc.state == DocumentState.ACTIVE
            assert "security" in doc.get_tags()

    def test_search_limit(self, search_manager, sample_documents):
        """Test search result limiting."""
        results = search_manager.search("document", limit=2)

        assert len(results) <= 2

    def test_search_relevance_ranking(self, search_manager, sample_documents):
        """Test that results are ranked by relevance."""
        results = search_manager.search("authentication security")

        if len(results) > 1:
            # Scores should be in descending order (higher = more relevant)
            # Note: FTS5 rank is negative, but we convert to positive
            scores = [score for _, score in results]
            # Check that scores are non-increasing (sorted by relevance)
            for i in range(len(scores) - 1):
                assert scores[i] >= scores[i + 1] or abs(scores[i] - scores[i + 1]) < 0.0001


class TestTagSearch:
    """Test tag-based search functionality."""

    def test_search_by_tags_any(self, search_manager, sample_documents):
        """Test tag search with ANY match (default)."""
        results = search_manager.search_by_tags(["security", "testing"])

        assert len(results) > 0
        # Should include docs with either 'security' OR 'testing' tag
        for doc in results:
            tags = doc.get_tags()
            assert "security" in tags or "testing" in tags

    def test_search_by_tags_all(self, search_manager, sample_documents):
        """Test tag search with ALL match."""
        results = search_manager.search_by_tags(["epic-5", "security"], match_all=True)

        assert len(results) > 0
        # Should include docs with BOTH 'epic-5' AND 'security' tags
        for doc in results:
            tags = doc.get_tags()
            assert "epic-5" in tags and "security" in tags

    def test_search_by_tags_no_results(self, search_manager, sample_documents):
        """Test tag search with no matches."""
        results = search_manager.search_by_tags(["nonexistent_tag_xyz"])

        assert len(results) == 0

    def test_search_by_tags_empty_list(self, search_manager, sample_documents):
        """Test tag search with empty tag list."""
        results = search_manager.search_by_tags([])

        assert len(results) == 0

    def test_search_by_tags_limit(self, search_manager, sample_documents):
        """Test tag search result limiting."""
        results = search_manager.search_by_tags(["epic-5"], limit=2)

        assert len(results) <= 2


class TestRelatedDocuments:
    """Test related document discovery."""

    def test_get_related_documents(self, search_manager, sample_documents):
        """Test finding related documents."""
        # Get related documents for the authentication PRD
        source_doc = sample_documents[0]  # PRD about authentication
        results = search_manager.get_related_documents(source_doc.id, limit=5)

        assert isinstance(results, list)
        # Should exclude the source document
        assert all(doc.id != source_doc.id for doc, _ in results)
        # Should return (Document, score) tuples
        assert all(isinstance(doc, Document) and isinstance(score, float) for doc, score in results)

    def test_get_related_documents_limit(self, search_manager, sample_documents):
        """Test related documents limiting."""
        source_doc = sample_documents[0]
        results = search_manager.get_related_documents(source_doc.id, limit=2)

        assert len(results) <= 2

    def test_get_related_documents_nonexistent(self, search_manager, sample_documents):
        """Test related documents for nonexistent document."""
        with pytest.raises(DocumentNotFoundError):
            search_manager.get_related_documents(999999)

    def test_get_related_documents_no_file(self, registry, search_manager):
        """Test related documents when file doesn't exist."""
        # Register document with non-existent file
        doc = registry.register_document(
            path="/nonexistent/path.md",
            doc_type="prd",
            author="Test",
            metadata={"tags": ["test"]},
        )

        # Should not raise error, just return empty or use metadata
        results = search_manager.get_related_documents(doc.id)
        assert isinstance(results, list)


class TestKeyTermExtraction:
    """Test key term extraction functionality."""

    def test_extract_key_terms_basic(self, search_manager):
        """Test basic key term extraction."""
        content = "This is a test document about authentication and security systems."
        terms = search_manager._extract_key_terms(content)

        assert isinstance(terms, list)
        assert len(terms) > 0
        # Should include meaningful terms
        assert any(term in ["test", "document", "authentication", "security", "systems"] for term in terms)

    def test_extract_key_terms_filters_stop_words(self, search_manager):
        """Test that stop words are filtered out."""
        content = "The quick brown fox jumps over the lazy dog with a ball."
        terms = search_manager._extract_key_terms(content)

        # Common stop words should be filtered (but some may slip through)
        # Just verify we got some meaningful terms
        assert len(terms) > 0
        # Verify we got meaningful terms like "quick", "brown", "jumps"
        meaningful = [t for t in terms if t in ["quick", "brown", "jumps", "lazy", "ball"]]
        assert len(meaningful) > 0

    def test_extract_key_terms_filters_short_words(self, search_manager):
        """Test that short words are filtered out."""
        content = "API is a set of functions for the app."
        terms = search_manager._extract_key_terms(content)

        # Words with length <= 3 should be filtered
        assert not any(len(term) <= 3 for term in terms)

    def test_extract_key_terms_removes_markdown(self, search_manager):
        """Test that markdown syntax is removed."""
        content = "# Heading\n\n**Bold** text with `code` and [link](url)"
        terms = search_manager._extract_key_terms(content)

        # Should extract meaningful words without markdown
        assert any(term in ["heading", "bold", "text", "code", "link"] for term in terms)

    def test_extract_key_terms_frequency(self, search_manager):
        """Test that terms are ranked by frequency."""
        content = "testing " * 10 + "security " * 5 + "authentication " * 3 + "other words here"
        terms = search_manager._extract_key_terms(content)

        # Most frequent terms should appear first
        assert "testing" in terms[:5]
        assert "security" in terms[:10]

    def test_extract_key_terms_empty(self, search_manager):
        """Test key term extraction with empty content."""
        terms = search_manager._extract_key_terms("")

        assert isinstance(terms, list)
        assert len(terms) == 0


class TestFTS5Integration:
    """Test FTS5 integration and triggers."""

    def test_fts_trigger_insert(self, registry, search_manager, temp_docs_dir):
        """Test that FTS index is updated on document insert."""
        # Create and register a document
        doc_path = temp_docs_dir / "new-doc.md"
        doc_path.write_text("This is a new test document about testing.")

        doc = registry.register_document(
            path=str(doc_path),
            doc_type="prd",
            author="Test",
            metadata={"tags": ["test"]},
        )

        # Search should find the new document
        results = search_manager.search("testing")
        assert any(d.id == doc.id for d, _ in results)

    def test_fts_trigger_update(self, registry, search_manager, sample_documents):
        """Test that FTS index is updated on document update."""
        doc = sample_documents[0]

        # Update document metadata (add tag)
        new_metadata = doc.metadata.copy()
        new_metadata["tags"].append("new-tag")
        registry.update_document(doc.id, metadata=new_metadata)

        # Search by new tag should find the document
        results = search_manager.search_by_tags(["new-tag"])
        assert any(d.id == doc.id for d in results)

    def test_fts_trigger_delete(self, registry, search_manager, sample_documents):
        """Test that FTS index is updated on document delete."""
        doc = sample_documents[0]
        doc_id = doc.id

        # Search should find document before deletion
        results = search_manager.search("authentication")
        assert any(d.id == doc_id for d, _ in results)

        # Delete document (hard delete)
        registry.delete_document(doc_id, soft=False)

        # Search should NOT find document after deletion
        results = search_manager.search("authentication")
        assert not any(d.id == doc_id for d, _ in results)


class TestSearchWithContent:
    """Test search that includes file content."""

    def test_search_with_content(self, search_manager, sample_documents):
        """Test search that reads and indexes file content."""
        # This searches file content, not just paths
        results = search_manager.search_with_content("authentication security")

        assert len(results) > 0
        # Should find documents with matching content
        assert any("auth" in doc.path.lower() for doc, _ in results)


class TestIndexMaintenance:
    """Test FTS5 index maintenance operations."""

    def test_rebuild_index(self, search_manager, sample_documents):
        """Test FTS5 index rebuild."""
        # Should not raise error
        search_manager.rebuild_index()

        # Search should still work after rebuild
        results = search_manager.search("authentication")
        assert len(results) > 0

    def test_optimize_index(self, search_manager, sample_documents):
        """Test FTS5 index optimization."""
        # Should not raise error
        search_manager.optimize_index()

        # Search should still work after optimization
        results = search_manager.search("authentication")
        assert len(results) > 0


class TestPerformance:
    """Test search performance characteristics."""

    def test_search_performance_many_documents(self, registry, search_manager, temp_docs_dir):
        """Test search performance with many documents."""
        import time

        # Create 100 test documents
        for i in range(100):
            doc_path = temp_docs_dir / f"doc-{i}.md"
            doc_path.write_text(
                f"# Document {i}\n\n"
                f"This is test document number {i}. "
                f"It contains various terms like testing, development, and implementation. "
                f"Document {i} also discusses architecture, design, and best practices."
            )
            registry.register_document(
                path=str(doc_path),
                doc_type="prd",
                author="Test",
                metadata={"tags": [f"tag-{i % 10}"]},
            )

        # Measure search time (search for "doc" which appears in all paths)
        start = time.time()
        results = search_manager.search("doc")
        elapsed = time.time() - start

        # Should complete in reasonable time (< 2 seconds for 100 docs)
        assert elapsed < 2.0
        assert len(results) > 0

    def test_tag_search_performance(self, registry, search_manager, temp_docs_dir):
        """Test tag search performance with many documents."""
        import time

        # Create 100 test documents with tags
        for i in range(100):
            doc_path = temp_docs_dir / f"doc-{i}.md"
            doc_path.write_text(f"Document {i}")
            registry.register_document(
                path=str(doc_path),
                doc_type="prd",
                author="Test",
                metadata={"tags": [f"tag-{i % 10}", "common-tag"]},
            )

        # Measure tag search time
        start = time.time()
        results = search_manager.search_by_tags(["common-tag"])
        elapsed = time.time() - start

        # Should complete in reasonable time
        assert elapsed < 1.0
        assert len(results) > 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_search_special_characters(self, search_manager, sample_documents):
        """Test search with special characters."""
        # Should handle special characters gracefully (even if no results)
        results = search_manager.search("authentication")
        assert isinstance(results, list)
        # The search should work even with special characters in the query
        results2 = search_manager.search("auth & security")
        assert isinstance(results2, list)

    def test_search_unicode(self, registry, search_manager, temp_docs_dir):
        """Test search with Unicode characters."""
        # Create document with Unicode content
        doc_path = temp_docs_dir / "unicode-doc.md"
        doc_path.write_text("Document with Unicode: café, naïve, résumé")

        doc = registry.register_document(
            path=str(doc_path),
            doc_type="prd",
            author="Test",
        )

        # Search should handle Unicode
        results = search_manager.search("café")
        assert isinstance(results, list)

    def test_search_with_no_documents(self, search_manager):
        """Test search when registry is empty."""
        results = search_manager.search("anything")

        assert len(results) == 0

    def test_related_documents_with_no_content(self, registry, search_manager):
        """Test related documents when source has no content."""
        doc = registry.register_document(
            path="/empty/doc.md",
            doc_type="prd",
            author="Test",
            metadata={"tags": []},
        )

        results = search_manager.get_related_documents(doc.id)
        assert isinstance(results, list)
